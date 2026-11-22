#!/usr/bin/env python3
"""Render fenced Mermaid sequence diagrams into a portable offline viewer."""
import argparse
import html
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
from urllib.parse import quote

SKILL_ROOT = Path(__file__).resolve().parents[1]
ASSETS = SKILL_ROOT / 'assets'
RUNTIME_FILES = ('mermaid-12.3.0.min.js', 'mermaid-LICENSE', 'sequence-source-links.js', 'sequence-navigation.js')


def extract_diagrams(markdown):
    diagrams = []
    for match in re.finditer(r'^```mermaid[^\S\n]*\n(.*?)\n```[ \t]*$', markdown, re.M | re.S):
        if not re.match(r'\s*sequenceDiagram\b', match[1]):
            continue
        headings = re.findall(r'^#{1,6}[ \t]+(.+?)\s*$', markdown[:match.start()], re.M)
        diagrams.append({'title': headings[-1] if headings else f'时序图 {len(diagrams) + 1}',
                         'source': match[1]})
    if not diagrams:
        raise ValueError('No fenced Mermaid sequenceDiagram blocks found.')
    return diagrams


def validate_mapping(diagrams, mapping, required):
    symbols = mapping.get('symbols', {})
    scenes = mapping.get('diagrams', [])
    if required and len(scenes) != len(diagrams):
        raise ValueError('Every diagram requires a source mapping.')
    for name, entry in symbols.items():
        if not re.fullmatch(r'[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*', entry.get('className', '')):
            raise ValueError('Invalid Java class: ' + name)
        for method in entry.get('methods', {}).values():
            if not re.fullmatch(r'[A-Za-z_$][\w$]*', method.get('methodName', '')) or not isinstance(method.get('parameterTypes'), list) or any(not isinstance(t, str) or not t or '...' in t for t in method['parameterTypes']):
                raise ValueError('Methods require verified erased parameterTypes.')
    for diagram, scene in zip(diagrams, scenes):
        if scene['sourceHash'] != hashlib.sha256(diagram['source'].encode()).hexdigest():
            raise ValueError('Stale source mapping: ' + diagram['title'])
        actors = dict(re.findall(r'^\s*(?:participant|actor) (\w+) as (?:nowrap: )?(.+)$', diagram['source'], re.M))
        messages = re.findall(r'^\s*(\w+)\s*([<\-\.>=()]+)\s*(\w+):\s*(.+)$', diagram['source'], re.M)
        if set(scene['participants']) != set(actors) or len(scene['messages']) != len(messages):
            raise ValueError('Mapping coverage differs from source.')
        items = []
        for actor, label in actors.items():
            item = scene['participants'][actor]
            if item['label'] != label: raise ValueError('Stale participant label')
            items.append(item)
        for item, (sender, arrow, receiver, label) in zip(scene['messages'], messages):
            if (item['from'], item['to'], item['label']) != (sender, receiver, label): raise ValueError('Stale message label')
            items.append(item)
        for item in items:
            if not item.get('links') and not item.get('reason'):
                raise ValueError('Each item requires links or an explicit exclusion reason.')
            for link in item.get('links', []):
                owner = symbols.get(link['symbol'])
                if not owner or link['text'] not in item['label'] or ('method' in link and link['method'] not in owner.get('methods', {})):
                    raise ValueError('Unresolved source link: ' + str(link))
    return symbols, scenes


def generate(source, output, title=None, overwrite=False, source_map=None, require_source_links=False):
    source, output = Path(source).resolve(), Path(output).resolve()
    resources = output.with_name(output.stem + '.assets')
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
    heading = re.search(r'^#[ \t]+(.+?)\s*$', markdown, re.M)
    title = title or (heading[1] if heading else source.stem)
    content = (ASSETS / 'viewer.html').read_text(encoding='utf-8')
    settings_match = re.search(r'<!--\s*sequence-viewer:\s*(\{.*?\})\s*-->', markdown, re.S)
    settings = json.loads(settings_match[1]) if settings_match else {}
    initial_zoom = settings.get('initialZoom', 1)
    if isinstance(initial_zoom, bool) or not isinstance(initial_zoom, (int, float)) or not math.isfinite(initial_zoom) or not .1 <= initial_zoom <= 3:
        raise ValueError('initialZoom must be a number between 0.1 and 3.')
    if source_map is None and settings.get('sourceMap'):
        source_map = source.parent / settings['sourceMap']
    require_source_links = require_source_links or source_map is not None
    mapping = json.loads(Path(source_map).read_text(encoding='utf-8')) if source_map else {}
    symbols, scenes = validate_mapping(diagrams, mapping, require_source_links)
    encode = lambda value: json.dumps(value, ensure_ascii=False).replace('<', chr(92) + 'u003c')
    replacements = {
        '@@SOURCE_MAP@@': encode(symbols),
        '@@SEQUENCE_LINKS@@': encode(scenes),
        '@@INITIAL_ZOOM@@': str(initial_zoom),
        '@@TITLE@@': html.escape(title),
        '@@ASSETS@@': html.escape(quote(resources.name, safe=''), quote=True),
        '@@DIAGRAMS@@': json.dumps(diagrams, ensure_ascii=False).replace('<', chr(92) + 'u003c'),
    }
    # One substitution pass prevents user text from being treated as template tokens.
    content = re.sub(r'@@(?:TITLE|ASSETS|DIAGRAMS|INITIAL_ZOOM|SOURCE_MAP|SEQUENCE_LINKS)@@', lambda m: replacements[m[0]], content)
    output.parent.mkdir(parents=True, exist_ok=True)
    resources.mkdir(exist_ok=True)
    for name in RUNTIME_FILES:
        shutil.copyfile(ASSETS / name, resources / name)
    if source_map:
        (resources / Path(source_map).name).write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding='utf-8')
    (resources / 'source.md').write_text(markdown, encoding='utf-8')
    output.write_text(content, encoding='utf-8')
    return len(diagrams)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--title')
    parser.add_argument('--source-map', type=Path)
    parser.add_argument('--require-source-links', action='store_true')
    parser.add_argument('--overwrite', action='store_true')
    args = parser.parse_args()
    try:
        output = args.output or args.source.with_suffix('.html')
        count = generate(args.source, output, args.title, args.overwrite, args.source_map, args.require_source_links)
    except (ValueError, OSError) as error:
        parser.exit(1, f'Error: {error}\n')
    print(f'Generated {output.resolve()} ({count} sequence diagrams).')
    print(f'Keep {output.stem}.assets/ beside the HTML for offline viewing.')


if __name__ == '__main__':
    main()
