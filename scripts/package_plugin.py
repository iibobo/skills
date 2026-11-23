#!/usr/bin/env python3
"""Build the plugin and standalone skill ZIPs from tracked release files."""
import argparse
import json
from pathlib import Path
import re
import subprocess
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json'
PORTABLE_FIELDS = ('name', 'version', 'description', 'author', 'homepage', 'repository', 'license', 'keywords')


def tracked_files(path):
    paths = subprocess.check_output(['git', 'ls-files', '-z', '--', path.as_posix()], cwd=ROOT)
    for value in paths.decode('utf-8').split('\0'):
        if value:
            yield Path(value)


def write_zip(path, entries):
    with ZipFile(path, 'x') as archive:
        for name, content in sorted(entries.items()):
            info = ZipInfo(name)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content, compress_type=ZIP_DEFLATED)


def manifest_json(data):
    return (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def build(output):
    manifests = ROOT / '.claude-plugin'
    plugin = json.loads((manifests / 'plugin.json').read_text(encoding='utf-8'))
    marketplace = (manifests / 'marketplace.json').read_bytes()
    package = json.loads((ROOT / 'package.json').read_text(encoding='utf-8'))
    name, version = plugin['name'], plugin['version']
    if version != package['version'] or not re.fullmatch(r'[0-9A-Za-z][0-9A-Za-z.+-]*', version):
        raise ValueError('Plugin version must match package.json and be safe for archive names.')
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name):
        raise ValueError('Invalid plugin name for archive.')

    notices = {path.as_posix(): (ROOT / path).read_bytes()
               for filename in ('LICENSE', 'NOTICE') for path in tracked_files(Path(filename))}
    portable = {'$schema': SCHEMA, **{key: plugin[key] for key in PORTABLE_FIELDS if key in plugin}}
    combined = {**notices, 'plugin.json': manifest_json(portable), '.claude-plugin/marketplace.json': marketplace}
    archives = {}
    packaged_skills = []
    for directory in map(Path, plugin['skills']):
        if directory.parts[:1] != ('skills',) or '..' in directory.parts or directory.name in packaged_skills:
            raise ValueError(f'Invalid or duplicate packaged skill: {directory}')
        if not (ROOT / directory).is_dir() or (ROOT / directory).resolve() != ROOT / directory:
            raise ValueError(f'Package only regular skill directories: {directory}')
        entries = {}
        for file in tracked_files(directory):
            source = ROOT / file
            if source.resolve() != source or not source.is_file():
                raise ValueError(f'Package only regular skill files: {file}')
            relative = file.relative_to(directory).as_posix()
            entries[relative] = source.read_bytes()
        if 'SKILL.md' not in entries:
            raise ValueError(f'Missing tracked SKILL.md: {directory}')
        skill = directory.name
        packaged_skills.append(skill)
        combined.update({f'skills/{skill}/{file}': data for file, data in entries.items()})
        archives[f'{skill}-{version}.zip'] = {f'{skill}/{file}': data for file, data in (notices | entries).items()}

    plugin['skills'] = [f'./skills/{skill}' for skill in packaged_skills]
    combined['.claude-plugin/plugin.json'] = manifest_json(plugin)
    archives[f'{name}-{version}.zip'] = combined
    output.mkdir(parents=True, exist_ok=True)
    paths = [output / filename for filename in archives]
    if any(path.exists() or path.is_symlink() for path in paths):
        raise FileExistsError(f'An archive for {version} already exists in {output}; use an empty output directory.')
    for path, entries in zip(paths, archives.values()):
        write_zip(path, entries)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        for path in build(args.output.resolve()):
            print(path)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
