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
from tempfile import TemporaryDirectory
from urllib.parse import quote

SKILL_ROOT = Path(__file__).resolve().parents[1]
ASSETS = SKILL_ROOT / 'assets'
RUNTIME_FILES = ('mermaid-12.3.0.min.js', 'mermaid-LICENSE', 'sequence-source-links.js', 'sequence-navigation.js')
ACTOR_ID = r'[\w$][\w$.-]*'
ACTOR = re.compile(rf'(?:create\s+)?(?:participant|actor)\s+({ACTOR_ID})(?:\s+as\s+(?:(?:no)?wrap:\s*)?(.+))?')
ARROW = r'(?:<<--?>>|--?(?:>>?|[x)]|\|[\\/]|//|\\\\)|(?:/\||//|\\\\)--?|\.\.>)'
MESSAGE = re.compile(rf'({ACTOR_ID}?)\s*(?:\(\))?{ARROW}(?:\(\))?\s*[+-]?\s*({ACTOR_ID})\s*:\s*(.*)')


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


def navigation_items(source):
    actors = {}
    messages = []
    for line in source.splitlines():
        line = line.strip()
        if line.startswith('%%'):
            continue
        actor = ACTOR.fullmatch(line)
        if actor:
            name, label = actor.groups()
            actors[name] = label or name
        elif re.match(r'(?:create\s+)?(?:participant|actor)\s', line):
            raise ValueError(f'Unsupported participant declaration for source mapping: {line}')
        message = MESSAGE.fullmatch(line)
        if message:
            messages.append(message.groups())
    for sender, receiver, _ in messages:
        actors.setdefault(sender, sender)
        actors.setdefault(receiver, receiver)
    return actors, messages


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
        actors, messages = navigation_items(diagram['source'])
        missing = actors.keys() - scene['participants'].keys()
        if missing:
            raise ValueError('Missing participants: ' + ', '.join(sorted(missing)))
        if set(scene['participants']) != set(actors) or len(scene['messages']) != len(messages):
            raise ValueError('Mapping coverage differs from source.')
        items = []
        for actor, label in actors.items():
            item = scene['participants'][actor]
            if item['label'] != label: raise ValueError('Stale participant label')
            items.append(item)
        for item, (sender, receiver, label) in zip(scene['messages'], messages):
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


def generate(source, output, title=None, overwrite=False, source_map=None, require_source_links=False):
    source, output = Path(source).resolve(), Path(output).resolve()
    module_dir = output.parent / 'sequence-diagrams'
    resources = module_dir / (output.stem + '.assets')
    resource_location = resources.resolve()
    if output == source or output.is_relative_to(SKILL_ROOT) or output.suffix.lower() != '.html':
        raise ValueError('Use an .html output outside the skill directory, distinct from the source.')
    if source.is_relative_to(resource_location):
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
    if source_map is not None:
        source_map = Path(source_map)
        map_location = source_map.resolve()
        if map_location == output:
            raise ValueError('HTML output must differ from the source map.')
        if map_location.is_relative_to(resource_location):
            raise ValueError('Source map input must be outside the generated resources directory.')
        if source_map.name.casefold() in {name.casefold() for name in (*RUNTIME_FILES, 'source.md')}:
            raise ValueError(f'Source map name conflicts with a generated resource: {source_map.name}')
    mapping = json.loads(source_map.read_text(encoding='utf-8')) if source_map else {}
    symbols, scenes = validate_mapping(diagrams, mapping, require_source_links)
    encode = lambda value: json.dumps(value, ensure_ascii=False).replace('<', chr(92) + 'u003c')
    source_link = source if source.parent == module_dir else resources / 'source.md'
    replacements = {
        '@@SOURCE@@': html.escape(quote(source_link.relative_to(output.parent).as_posix(), safe='/'), quote=True),
        '@@SOURCE_MAP@@': encode(symbols),
        '@@SEQUENCE_LINKS@@': encode(scenes),
        '@@INITIAL_ZOOM@@': str(initial_zoom),
        '@@TITLE@@': html.escape(title),
        '@@ASSETS@@': html.escape(quote(resources.relative_to(output.parent).as_posix(), safe='/'), quote=True),
        '@@DIAGRAMS@@': json.dumps(diagrams, ensure_ascii=False).replace('<', chr(92) + 'u003c'),
    }
    # One substitution pass prevents user text from being treated as template tokens.
    content = re.sub(r'@@(?:TITLE|ASSETS|SOURCE|DIAGRAMS|INITIAL_ZOOM|SOURCE_MAP|SEQUENCE_LINKS)@@', lambda m: replacements[m[0]], content)
    module_dir.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='.render-', dir=module_dir) as directory:
        staged_output = Path(directory) / 'page.html'
        staged_resources = Path(directory) / 'resources'
        staged_resources.mkdir()
        for name in RUNTIME_FILES:
            shutil.copyfile(ASSETS / name, staged_resources / name)
        if source_map:
            (staged_resources / source_map.name).write_text(
                json.dumps(mapping, ensure_ascii=False, indent=2), encoding='utf-8')
        (staged_resources / 'source.md').write_text(markdown, encoding='utf-8')
        staged_output.write_text(content, encoding='utf-8')
        publish(output, resources, staged_output, staged_resources, overwrite)
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
        source = args.source.resolve()
        output_root = source.parent.parent if source.parent.name == 'sequence-diagrams' else source.parent
        output = (args.output or output_root / source.with_suffix('.html').name).resolve()
        count = generate(args.source, output, args.title, args.overwrite, args.source_map, args.require_source_links)
    except (ValueError, OSError) as error:
        parser.exit(1, f'Error: {error}\n')
    print(f'Generated {output.resolve()} ({count} sequence diagrams).')
    print(f'Offline resources: sequence-diagrams/{output.stem}.assets/; keep the relative layout.')


if __name__ == '__main__':
    main()
