#!/usr/bin/env python3
"""Render fenced Mermaid flowcharts into a portable offline viewer."""
import argparse
import html
import json
from pathlib import Path
import re
import shutil
from urllib.parse import quote

SKILL_ROOT = Path(__file__).resolve().parents[1]
ASSETS = SKILL_ROOT / 'assets'
RUNTIME_FILES = ('mermaid-12.3.0.min.js', 'mermaid-LICENSE', 'diagram-navigation.js', 'flowchart-edges.js')


def extract_diagrams(markdown):
    diagrams = []
    for match in re.finditer(r'^```mermaid[^\S\n]*\n(.*?)\n```[ \t]*$', markdown, re.M | re.S):
        if not re.match(r'\s*(?:flowchart|graph)\s+(?:TB|TD|BT|RL|LR)\b', match[1]):
            continue
        headings = re.findall(r'^#{1,6}[ \t]+(.+?)\s*$', markdown[:match.start()], re.M)
        diagrams.append({'title': headings[-1] if headings else f'流程图 {len(diagrams) + 1}',
                         'source': match[1]})
    if not diagrams:
        raise ValueError('No fenced Mermaid flowchart/graph blocks with a direction found.')
    return diagrams


def extract_source_map(diagrams):
    source_map = {}
    for index, diagram in enumerate(diagrams, start=1):
        directives = re.findall(r'^[ \t]*%%[ \t]+source-map:[ \t]*(.*)$', diagram['source'], re.M)
        if not directives:
            continue
        context = f"source-map in diagram {index} ({diagram['title']})"
        if len(directives) != 1:
            raise ValueError(f'{context}: expected one directive per diagram')
        try:
            entries = json.loads(directives[0])
        except ValueError as error:
            raise ValueError(f'{context}: {error}') from error
        if not isinstance(entries, dict):
            raise ValueError(f'{context}: expected an object keyed by Mermaid node ID')
        for node_id, target in entries.items():
            if not node_id or not isinstance(target, dict) or set(target) != {'className', 'line'}:
                raise ValueError(f'{context}: {node_id!r} needs className and line')
            class_name, line = target['className'], target['line']
            if (not isinstance(class_name, str) or len(class_name) > 500
                    or not all(part.replace('$', '_').isidentifier() for part in class_name.split('.'))):
                raise ValueError(f'{context}: invalid className for {node_id!r}')
            if type(line) is not int or not 1 <= line <= 2147483647:
                raise ValueError(f'{context}: line for {node_id!r} must be a positive 32-bit integer')
            source_map[f'{index}:{node_id}'] = target
    return source_map


def generate(source, output, title=None, overwrite=False):
    source, output = Path(source).resolve(), Path(output).resolve()
    module_dir = output.parent / 'flowcharts'
    resources = module_dir / (output.stem + '.assets')
    if output == source or output.is_relative_to(SKILL_ROOT) or output.suffix.lower() != '.html':
        raise ValueError('Use an .html output outside the skill directory, distinct from the source.')
    if source.is_relative_to(resources):
        raise ValueError('Markdown input must be outside the generated resources directory.')
    if not overwrite and (output.exists() or resources.exists()):
        raise ValueError('Output or resources already exist; use --overwrite.')
    for name in ('viewer.html',) + RUNTIME_FILES:
        if not (ASSETS / name).is_file():
            raise ValueError(f'Skill package is incomplete: missing assets/{name}')
    markdown = source.read_text(encoding='utf-8')
    diagrams = extract_diagrams(markdown)
    source_map = extract_source_map(diagrams)
    heading = re.search(r'^#[ \t]+(.+?)\s*$', markdown, re.M)
    title = title or (heading[1] if heading else source.stem)
    content = (ASSETS / 'viewer.html').read_text(encoding='utf-8')
    source_link = source if source.parent == module_dir else resources / 'source.md'
    replacements = {
        '@@SOURCE@@': html.escape(quote(source_link.relative_to(output.parent).as_posix(), safe='/'), quote=True),
        '@@TITLE@@': html.escape(title),
        '@@ASSETS@@': html.escape(quote(resources.relative_to(output.parent).as_posix(), safe='/'), quote=True),
        '@@DIAGRAMS@@': json.dumps(diagrams, ensure_ascii=False).replace('<', '\\u003c'),
        '@@SOURCE_MAP@@': json.dumps(source_map, ensure_ascii=False).replace('<', '\\u003c'),
    }
    # One substitution pass prevents user text from being treated as template tokens.
    content = re.sub(r'@@(?:TITLE|ASSETS|SOURCE|DIAGRAMS|SOURCE_MAP)@@', lambda m: replacements[m[0]], content)
    output.parent.mkdir(parents=True, exist_ok=True)
    resources.mkdir(parents=True, exist_ok=True)
    for name in RUNTIME_FILES:
        shutil.copyfile(ASSETS / name, resources / name)
    (resources / 'source.md').write_text(markdown, encoding='utf-8')
    output.write_text(content, encoding='utf-8')
    return len(diagrams)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--title')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    try:
        source = args.source.resolve()
        output_root = source.parent.parent if source.parent.name == 'flowcharts' else source.parent
        output = (args.output or output_root / source.with_suffix('.html').name).resolve()
        count = generate(args.source, output, args.title, args.overwrite)
    except (ValueError, OSError) as error:
        parser.exit(1, f'Error: {error}\n')
    print(f'Generated {output.resolve()} ({count} flowcharts).')
    print(f'Offline resources: flowcharts/{output.stem}.assets/; keep the relative layout.')


if __name__ == '__main__':
    main()
