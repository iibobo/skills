#!/usr/bin/env python3
"""Exercise the ZIPs used for offline transfer and, optionally, host installation."""
import argparse
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Timer
from urllib.parse import unquote, urlsplit
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]


class LocalLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attributes):
        self.links.extend(value for key, value in attributes if key in ('href', 'src') and value)


def run(*command, cwd, env=None):
    if command[0] == sys.executable:
        # Match the pipe decoder even when Windows defaults to a legacy code page.
        env = dict(os.environ if env is None else env, PYTHONIOENCODING='utf-8')
    process = subprocess.run(command, cwd=cwd, env=env, timeout=90,
                             capture_output=True, text=True, encoding='utf-8')
    if process.returncode:
        raise RuntimeError(f'{command[0]} exited {process.returncode}\n{process.stdout}{process.stderr}')
    return process.stdout


def check_standalone(archive_path, skill, directory):
    unpacked = directory / 'standalone'
    with ZipFile(archive_path) as archive:
        assert all(name.startswith(f'{skill}/') for name in archive.namelist())
        archive.extractall(unpacked)
    skill_root = unpacked / skill
    source = skill_root / 'assets/example.md'
    expected = source.read_bytes()
    output = directory / 'output' / '示例 图.html'
    run(sys.executable, str(skill_root / 'scripts/render_diagrams.py'), str(source), '--output', str(output), cwd=directory)
    shutil.rmtree(unpacked)
    relocated = directory / 'relocated'
    output.parent.rename(relocated)
    content = (relocated / output.name).read_text(encoding='utf-8')
    data = re.search(r'<script id="diagram-data" type="application/json">(.*?)</script>', content, re.S)
    assert data and len(json.loads(data[1])) == 2, skill
    snapshot, = relocated.glob('*/*.assets/source.md')
    assert snapshot.read_bytes().replace(b'\r\n', b'\n') == expected.replace(b'\r\n', b'\n'), skill
    links = LocalLinks()
    links.feed(content)
    assert links.links, skill
    for link in links.links:
        url = urlsplit(link)
        target = relocated / unquote(url.path)
        assert not url.scheme and not url.netloc and target.resolve().is_relative_to(relocated) and target.is_file(), link
    print(f'{skill}: standalone generation and relocated resources passed', flush=True)


def codex_skill_names(cwd, env):
    with subprocess.Popen(['codex', 'app-server', '--listen', 'stdio://'], cwd=cwd, env=env,
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                          text=True, encoding='utf-8') as process:
        timer = Timer(30, process.kill)
        timer.start()
        try:
            def send(method, params=None, request_id=None):
                message = {'method': method}
                if request_id is not None:
                    message.update(id=request_id, params=params)
                process.stdin.write(json.dumps(message) + '\n')
                process.stdin.flush()
                if request_id is not None:
                    for line in process.stdout:
                        response = json.loads(line)
                        if response.get('id') == request_id:
                            return response['result']
                    raise RuntimeError(f'Codex app-server stopped before replying to {method}')

            send('initialize', {'clientInfo': {'name': 'skills-release-check', 'version': '1.0.0'}}, 1)
            send('initialized')
            result = send('skills/list', {'cwds': [str(cwd)], 'forceReload': True}, 2)
            workspace, = result['data']
            assert not workspace['errors'], workspace['errors']
            return {skill['name'] for skill in workspace['skills'] if skill['enabled']}
        finally:
            process.kill()
            timer.cancel()


def check_installation(unpacked, work, plugin, marketplace, skills):
    name = plugin['name']
    plugin_id = f'{name}@{marketplace["name"]}'
    for host in ('codex', 'claude'):
        profile, project = work / f'{host}-profile', work / f'{host}-project'
        profile.mkdir()
        project.mkdir()
        env = os.environ.copy()
        if host == 'codex':
            env['CODEX_HOME'] = str(profile)
            run(host, 'plugin', 'marketplace', 'add', str(unpacked), cwd=project, env=env)
            run(host, 'plugin', 'add', plugin_id, cwd=project, env=env)
            status = json.loads(run(host, 'plugin', 'list', '--json', cwd=project, env=env))
            assert any(item['pluginId'] == plugin_id and item['version'] == plugin['version']
                       and item['installed'] and item['enabled'] for item in status['installed']), status
            discovered = codex_skill_names(project, env)
            assert {skill for skill in discovered if skill.startswith(f'{name}:')} == {f'{name}:{skill}' for skill in skills}, discovered
        else:
            env.update(CLAUDE_CONFIG_DIR=str(profile), CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1')
            run(host, 'plugin', 'validate', str(unpacked), '--strict', cwd=project, env=env)
            run(host, 'plugin', 'validate', str(unpacked / '.claude-plugin/plugin.json'), '--strict', cwd=project, env=env)
            run(host, 'plugin', 'marketplace', 'add', str(unpacked), '--scope', 'project', cwd=project, env=env)
            run(host, 'plugin', 'install', plugin_id, '--scope', 'project', cwd=project, env=env)
            details = run(host, 'plugin', 'details', name, cwd=project, env=env)
            assert f'Skills ({len(skills)})' in details and all(skill in details for skill in skills), details
        print(f'{host}: installation and skill inventory passed', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true', help='Also install in isolated Codex and Claude Code profiles.')
    args = parser.parse_args()
    with TemporaryDirectory(prefix='iibobo-release-') as temporary:
        work = Path(temporary).resolve()
        archives = work / 'archives'
        run(sys.executable, str(ROOT / 'scripts/package_plugin.py'), '--output', str(archives), cwd=work)
        plugin = json.loads((ROOT / '.claude-plugin/plugin.json').read_text(encoding='utf-8'))
        marketplace = json.loads((ROOT / '.claude-plugin/marketplace.json').read_text(encoding='utf-8'))
        skills = {Path(path).name for path in plugin['skills']}
        version = plugin['version']
        unpacked = work / 'market'
        with ZipFile(archives / f'{plugin["name"]}-{version}.zip') as archive:
            files = archive.namelist()
            assert set(Path(file).parts[0] for file in files) <= {'plugin.json', '.claude-plugin', 'skills', 'LICENSE', 'NOTICE'}
            assert {file for file in files if file.endswith('/SKILL.md')} == {f'skills/{skill}/SKILL.md' for skill in skills}
            portable = json.loads(archive.read('plugin.json'))
            assert portable['name'] == plugin['name'] and portable['version'] == version
            assert 'skills' not in portable
            archive.extractall(unpacked)
        for skill in sorted(skills):
            check_standalone(archives / f'{skill}-{version}.zip', skill, work / skill)
        if args.install:
            check_installation(unpacked, work, plugin, marketplace, skills)


if __name__ == '__main__':
    main()
