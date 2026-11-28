#!/usr/bin/env python3
"""Render Markdown class diagrams as a portable offline HTML viewer (Python 3.9+)."""
import argparse
import html
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import quote

SKILL_ROOT = Path(__file__).resolve().parents[1]
ASSETS = SKILL_ROOT / 'assets'
RUNTIME_FILES = ('mermaid-12.3.0.min.js', 'class-diagram-layout.js', 'class-diagram-source-links.js', 'mermaid-LICENSE', 'diagram-navigation.js')


def extract_diagrams(markdown):
    diagrams = []
    for match in re.finditer(r'^```mermaid[^\S\n]*\n(.*?)\n```[ \t]*$', markdown, re.M | re.S):
        source = match[1]
        if not re.match(r'\s*classDiagram\b', source):
            continue
        headings = re.findall(r'^#{1,6}[ \t]+(.+?)\s*$', markdown[:match.start()], re.M)
        title = headings[-1] if headings else f'类图 {len(diagrams) + 1}'
        for line in source.splitlines():
            if re.match(r'^\s*[\w$]+\s+(?:<\|--|<\|\.\.|\.\.>|-->|o--|\*--|--\*|--o)', line):
                if not re.search(r':\s*\S', line):
                    raise ValueError(f'{title}: relationship needs a label: {line.strip()}')
        diagrams.append({'title': title, 'source': source})
    if not diagrams:
        raise ValueError('No fenced Mermaid classDiagram blocks found.')
    return diagrams


def replace_once(pattern, replacement, content):
    result, count = re.subn(pattern, lambda _: replacement, content, count=1, flags=re.S)
    if count != 1:
        raise ValueError(f'Template structure changed; expected pattern: {pattern}')
    return result


def missing_source_links(diagrams, mapping):
    def normalize(signature):
        return re.sub(r'\s+', '', signature).lstrip('+-#~').rstrip('$*')

    displayed = {}
    for diagram in diagrams:
        current = None
        for line in diagram['source'].splitlines():
            line = line.strip()
            declaration = re.match(r'class\s+([\w$]+)(?:~[^~]+~)?(?:\s*\["[^"]*"\])?\s*(\{)?', line)
            inline_member = re.match(r'([\w$]+)(?:~[^~]+~)?\s*:\s*(.+)', line)
            if declaration:
                name = declaration[1]
                displayed.setdefault(name, set())
                current = name if declaration[2] else None
                continue
            if line == '}':
                current = None
                continue
            name, member = inline_member.groups() if inline_member else (current, line)
            if name:
                methods = displayed.setdefault(name, set())
                signature = re.match(r'[+\-#~]?\s*([\w$]+\s*\([^)]*\))', member)
                if signature:
                    methods.add(normalize(signature[1]))

    missing = []
    for name, methods in displayed.items():
        if name not in mapping:
            missing.append(name)
        mapped = {normalize(key) for key in mapping.get(name, {}).get('methods', {})}
        missing.extend(f'{name}.{signature}' for signature in sorted(methods - mapped))
    return missing


def publish(output, resource_dir, staged_output, staged_resources, overwrite):
    # HTML files are siblings even when different skills generate them.
    lock = output.parent / f'.{output.stem}.assets.lock'
    try:
        lock.mkdir()
    except FileExistsError as error:
        raise ValueError(f'Another generation is using {output}; retry after it finishes.') from error
    previous = lock / 'previous'
    try:
        if resource_dir.is_symlink() or (resource_dir.exists() and not resource_dir.is_dir()):
            raise ValueError(f'Expected a regular generated resources directory: {resource_dir}')
        if not overwrite and (output.exists() or resource_dir.exists()):
            raise ValueError(f'Output or resources already exist: {output}; use --overwrite.')
        if resource_dir.exists():
            resource_dir.rename(previous)
        installed = False
        try:
            staged_resources.rename(resource_dir)
            installed = True
            staged_output.replace(output)
        except BaseException:
            if installed:
                resource_dir.rename(staged_resources)
            if previous.exists():
                previous.rename(resource_dir)
            raise
        if previous.exists():
            shutil.rmtree(previous)
    finally:
        # Preserve the backup if a filesystem failure also prevented rollback.
        if not previous.exists():
            lock.rmdir()


def generate(source, output, title=None, subtitle='类与接口关系图 · 主要职责与核心方法', overwrite=False, source_map=None, require_source_links=False):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.is_relative_to(SKILL_ROOT):
        raise ValueError('Output must be outside the skill directory.')
    if output == source:
        raise ValueError('HTML output must differ from Markdown source.')
    module_dir = output.parent / 'class-diagrams'
    resource_dir = module_dir / (output.stem + '.assets')
    resource_location = resource_dir.resolve()
    source_map = Path(source_map).resolve() if source_map else None
    if source.is_relative_to(resource_location) or (source_map and source_map.is_relative_to(resource_location)):
        raise ValueError('Markdown and source map inputs must be outside the generated resources directory.')
    if not overwrite and (output.exists() or resource_dir.exists()):
        raise ValueError(f'Output or resources already exist: {output}; use --overwrite.')
    required = ('viewer.html',) + RUNTIME_FILES
    for name in required:
        if not (ASSETS / name).is_file():
            raise ValueError(f'Skill package is incomplete: missing assets/{name}')
    markdown = source.read_text(encoding='utf-8')
    diagrams = extract_diagrams(markdown)
    if not title:
        match = re.search(r'^#[ \t]+(.+?)\s*$', markdown, re.M)
        title = match[1] if match else source.stem
    content = (ASSETS / 'viewer.html').read_text(encoding='utf-8')
    content = replace_once(r'<title>.*?</title>', '<title>' + html.escape(title) + '</title>', content)
    resource_url = quote(resource_dir.relative_to(output.parent).as_posix(), safe='/')
    source_url = quote(source.relative_to(output.parent).as_posix(), safe='/') if source.parent == module_dir else resource_url + '/source.md'
    link = html.escape(source_url, quote=True)
    header = f'<div class="header-copy"><h1>{html.escape(title)}</h1><p>{html.escape(subtitle)} <a href="{link}">阅读完整指南</a></p></div>'
    content = replace_once(r'<div class="header-copy">.*?</div>', header, content)
    data = json.dumps(diagrams, ensure_ascii=False).replace('<', '\\u003c')
    content = replace_once(r'<script id="diagram-data" type="application/json">.*?</script>',
                           '<script id="diagram-data" type="application/json">' + data + '</script>', content)
    for name in (name for name in RUNTIME_FILES if name.endswith('.js')):
        original = f'src="{name}"'
        if content.count(original) != 1:
            raise ValueError(f'Template must reference {name} exactly once.')
        content = content.replace(original, 'src="' + resource_url + '/' + name + '"')
    source_files = {}
    mapping = json.loads(source_map.read_text(encoding='utf-8')) if source_map else {}
    if not isinstance(mapping, dict):
        raise ValueError('Source map must be a JSON object keyed by class name.')
    def validate_location(value, owner=None, method=False):
        if not isinstance(value, dict):
            raise ValueError('Each source location must be an object.')
        class_name = value.get('className', (owner or {}).get('className'))
        symbolic = bool(class_name)
        if symbolic and not re.fullmatch(r'[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*', class_name):
            raise ValueError(f'Invalid Java className: {class_name}')
        if symbolic and method:
            if not re.fullmatch(r'[A-Za-z_$][\w$]*', value.get('methodName', '')):
                raise ValueError('Symbolic methods require methodName.')
            types = value.get('parameterTypes')
            if not isinstance(types, list) or any(not isinstance(t, str) or not t or '...' in t for t in types):
                raise ValueError('Symbolic methods require erased parameterTypes; use [] for no arguments.')
        if 'file' in value:
            if not isinstance(value.get('line'), int) or isinstance(value['line'], bool) or value['line'] < 1:
                raise ValueError('Source locations require a positive integer line.')
            origin = (source_map.parent / value['file']).resolve()
            if origin.is_relative_to(resource_location):
                raise ValueError('Source files must be outside the generated resources directory.')
            if value['line'] > len(origin.read_text(encoding='utf-8').splitlines()):
                raise ValueError(f'Source line exceeds file length: {origin}')
            name = hashlib.sha256(str(origin).encode()).hexdigest()[:12] + '-' + origin.name
            source_files[name] = origin
            value['file'] = resource_dir.relative_to(output.parent).as_posix() + '/sources/' + name
        elif not symbolic:
            raise ValueError('Source locations require className or file/line.')
    for key, entry in mapping.items():
        validate_location(entry)
        methods = entry.get('methods', {})
        if not isinstance(methods, dict):
            raise ValueError(f'{key}: methods must be an object.')
        for value in methods.values():
            validate_location(value, entry, method=True)
    if require_source_links:
        missing = missing_source_links(diagrams, mapping)
        if missing:
            raise ValueError('Missing source links: ' + ', '.join(missing))
    mapping_json = json.dumps(mapping, ensure_ascii=False).replace('<', '\\u003c')
    content = replace_once(r'<script id="source-map" type="application/json">.*?</script>',
                          '<script id="source-map" type="application/json">' + mapping_json + '</script>', content)
    files = list(RUNTIME_FILES)
    if (ASSETS / 'mermaid-third-party-LICENSE.txt').is_file():
        files.append('mermaid-third-party-LICENSE.txt')
    module_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.class-diagram-', dir=module_dir) as directory:
        staged_output = Path(directory) / 'page.html'
        staged_resources = Path(directory) / 'resources'
        staged_resources.mkdir()
        for name in files:
            shutil.copyfile(ASSETS / name, staged_resources / name)
        if source_files:
            (staged_resources / 'sources').mkdir()
            for name, origin in source_files.items():
                shutil.copyfile(origin, staged_resources / 'sources' / name)
        (staged_resources / 'source.md').write_text(markdown, encoding='utf-8')
        staged_output.write_text(content, encoding='utf-8')
        publish(output, resource_dir, staged_output, staged_resources, overwrite)
    return len(diagrams)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Markdown containing Mermaid class diagrams')
    parser.add_argument('--output', type=Path, help='Default: top-level HTML in the diagram output directory')
    parser.add_argument('--title', help='Default: Markdown H1')
    parser.add_argument('--subtitle', default='类与接口关系图 · 主要职责与核心方法')
    parser.add_argument('--source-map', type=Path, help='JSON symbolic class/method targets or optional local file/line locations')
    parser.add_argument('--require-source-links', action='store_true', help='Fail unless every declared class and displayed method has a mapping')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    try:
        source = args.source.resolve()
        output_root = source.parent.parent if source.parent.name == 'class-diagrams' else source.parent
        output = (args.output or output_root / source.with_suffix('.html').name).resolve()
        count = generate(source, output, args.title, args.subtitle, args.overwrite, args.source_map, args.require_source_links)
    except (ValueError, OSError, TypeError) as error:
        parser.exit(1, f'Error: {error}\n')
    print(f'Generated {output} ({count} class diagrams).')
    print(f'Offline resources: class-diagrams/{output.stem}.assets/; keep the relative layout.')


if __name__ == '__main__':
    main()
