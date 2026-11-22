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
RUNTIME_FILES = ('mermaid-12.3.0.min.js', 'mermaid-LICENSE')


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


def generate(source, output, title=None, overwrite=False):
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
    replacements = {
        '@@TITLE@@': html.escape(title),
        '@@ASSETS@@': html.escape(quote(resources.name, safe=''), quote=True),
        '@@DIAGRAMS@@': json.dumps(diagrams, ensure_ascii=False).replace('<', '\\u003c'),
    }
    # One substitution pass prevents user text from being treated as template tokens.
    content = re.sub(r'@@(?:TITLE|ASSETS|DIAGRAMS)@@', lambda m: replacements[m[0]], content)
    output.parent.mkdir(parents=True, exist_ok=True)
    resources.mkdir(exist_ok=True)
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
        output = args.output or args.source.with_suffix('.html')
        count = generate(args.source, output, args.title, args.overwrite)
    except (ValueError, OSError) as error:
        parser.exit(1, f'Error: {error}\n')
    print(f'Generated {output.resolve()} ({count} flowcharts).')
    print(f'Keep {output.stem}.assets/ beside the HTML for offline viewing.')


if __name__ == '__main__':
    main()
