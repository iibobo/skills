#!/usr/bin/env python3
"""Verify symbolic Java mappings against actual JVM class/method descriptors using javap."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess


def parameter_types(descriptor):
    rest = descriptor[1:descriptor.index(')')]
    primitives = dict(zip('BCDFIJSZ', ['byte', 'char', 'double', 'float', 'int', 'long', 'short', 'boolean']))
    result = []
    while rest:
        suffix = ''
        while rest.startswith('['):
            suffix += '[]'
            rest = rest[1:]
        if rest.startswith('L'):
            end = rest.index(';')
            value, rest = rest[1:end].replace('/', '.').replace('$', '.'), rest[end + 1:]
        else:
            value, rest = primitives[rest[0]], rest[1:]
        result.append(value + suffix)
    return result


def declarations(text):
    classes, methods = set(), set()
    owner, method = None, None
    for line in text.splitlines():
        match = re.search(r'(?:class|interface) ([\w.$]+)', line)
        if match and not line.startswith(' '):
            owner = match[1].replace('$', '.')
            classes.add(owner)
        if '(' in line and not line.strip().startswith('descriptor:'):
            match = re.search(r'([\w$]+)\(', line)
            method = match[1] if match else None
        if 'descriptor: (' in line and owner and method:
            methods.add((owner, method, tuple(parameter_types(line.split('descriptor: ', 1)[1]))))
    return classes, methods


def audit(mapping, classpath, javap):
    targets = []
    for name, entry in mapping.items():
        targets.append((name, entry, False))
        for label, value in entry.get('methods', {}).items():
            targets.append((name + '.' + label, {'className': entry['className'], **value}, True))
    names = sorted({target['className'] for _, target, _ in targets})
    # javap accepts binary names for nested classes. Discover them incrementally by replacing
    # rightmost type separators; package separators remain untouched until a real class is found.
    pending, output = list(names), ''
    for _ in range(8):
        if not pending:
            break
        command = [javap, '-s', '-p'] + (['-classpath', classpath] if classpath else []) + pending
        run = subprocess.run(command, text=True, capture_output=True, timeout=120)
        output += '\n' + run.stdout
        found, _ = declarations(output)
        next_names = []
        for binary in pending:
            if binary.replace('$', '.') in found:
                continue
            if '.' in binary:
                prefix, leaf = binary.rsplit('.', 1)
                next_names.append(prefix + '$' + leaf)
        pending = next_names
    classes, methods = declarations(output)
    result = []
    for label, target, is_method in targets:
        normalized = {**target, 'className': target['className'].replace('$', '.')}
        valid = normalized['className'] in classes
        if is_method:
            valid = valid and (normalized['className'], normalized['methodName'],
                tuple(value.replace('$', '.').replace('...', '[]') for value in normalized['parameterTypes'])) in methods
        result.append({'label': label, 'target': normalized, 'status': 'verified' if valid else 'missing'})
    return {'verification': 'JVM declarations only; does not establish IDEA indexing or actual navigation',
            'total': len(result), 'verified': sum(row['status'] == 'verified' for row in result), 'results': result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_map', type=Path)
    parser.add_argument('--classpath-file', type=Path, help='UTF-8 file containing the platform-separated dependency classpath')
    parser.add_argument('--javap', default=shutil.which('javap'), help='Path to a compatible JDK javap executable')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if not args.javap:
        parser.error('javap is unavailable; supply --javap')
    try:
        report = audit(json.loads(args.source_map.read_text(encoding='utf-8')),
                       args.classpath_file.read_text(encoding='utf-8').strip() if args.classpath_file else '', args.javap)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    except (KeyError, ValueError, OSError, subprocess.TimeoutExpired) as error:
        parser.exit(1, str(error) + '\n')
    print(f"Verified {report['verified']}/{report['total']} JVM declarations; report: {args.report}")
    if report['verified'] != report['total']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
