"""Portable generation and source preservation contracts."""
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('sequence_renderer', Path(__file__).with_name('render_diagrams.py'))
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)


class SequenceRendererTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'flows.md'
        self.source.write_text((renderer.ASSETS / 'example.md').read_text())
        self.output = self.root / 'output space' / 'flows.html'

    def test_multiple_diagrams_preserve_source_and_ignore_other_types(self):
        markdown = self.source.read_text() + '\n```mermaid\nclassDiagram\n class A\n```\n'
        self.source.write_text(markdown)
        self.assertEqual(renderer.generate(self.source, self.output), 2)
        page = self.output.read_text()
        data = json.loads(re.search(r'id="diagram-data" type="application/json">(.*?)</script>', page, re.S)[1])
        self.assertEqual(data, renderer.extract_diagrams(markdown))
        self.assertEqual((self.output.parent / 'sequence-diagrams/flows.assets/source.md').read_text(), markdown)

    def test_no_diagrams_rejects_before_writing(self):
        self.source.write_text('# Not a sequence\n```mermaid\nclassDiagram\n class A\n```\n')
        with self.assertRaisesRegex(ValueError, 'No fenced'):
            renderer.generate(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_overwrite_is_explicit(self):
        renderer.generate(self.source, self.output)
        before = self.output.read_bytes()
        with self.assertRaisesRegex(ValueError, 'overwrite'):
            renderer.generate(self.source, self.output, title='Changed')
        self.assertEqual(self.output.read_bytes(), before)
        renderer.generate(self.source, self.output, title='Changed', overwrite=True)
        self.assertIn('<title>Changed</title>', self.output.read_text())

    def test_source_map_template_round_trips_and_protects_an_existing_map(self):
        self.source.write_text(
            '```mermaid\nsequenceDiagram\n participant A as nowrap: Worker\n'
            ' A->>B: call()\n B-->>A: done\n```\n',
            encoding='utf-8',
        )
        mapping_path = self.root / 'symbols.json'
        command = [sys.executable, str(SPEC.origin), str(self.source), '--init-source-map', str(mapping_path)]
        subprocess.run(command, check=True, capture_output=True)
        mapping = json.loads(mapping_path.read_text(encoding='utf-8'))
        scene, = mapping['diagrams']
        self.assertEqual(mapping['symbols'], {})
        self.assertEqual(scene['participants'], {
            'A': {'label': 'Worker', 'links': []},
            'B': {'label': 'B', 'links': []},
        })
        self.assertEqual(scene['messages'], [
            {'from': 'A', 'to': 'B', 'label': 'call()', 'links': []},
            {'from': 'B', 'to': 'A', 'label': 'done', 'links': []},
        ])
        with self.assertRaisesRegex(ValueError, 'links or an explicit exclusion reason'):
            renderer.generate(self.source, self.output, source_map=mapping_path)
        self.assertFalse(self.output.exists())

        mapping['symbols']['Worker'] = {'className': 'example.Worker'}
        scene['participants']['A']['links'].append({'symbol': 'Worker', 'text': 'Worker'})
        for item in [scene['participants']['B'], *scene['messages']]:
            item['reason'] = 'External boundary or data'
        mapping_path.write_text(json.dumps(mapping), encoding='utf-8')
        filled = mapping_path.read_bytes()
        self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
        self.assertEqual(mapping_path.read_bytes(), filled)
        self.assertEqual(renderer.generate(self.source, self.output, source_map=mapping_path), 1)

    def test_user_text_cannot_escape_json_or_trigger_template_replacement(self):
        self.source.write_text('# <标题> @@ASSETS@@\n```mermaid\nsequenceDiagram\n A->>B: </script><script>alert(1)</script>\n```\n')
        renderer.generate(self.source, self.output)
        page = self.output.read_text()
        self.assertIn('&lt;标题&gt; @@ASSETS@@', page)
        self.assertNotIn('</script><script>alert(1)</script>', page)
        data = json.loads(re.search(r'id="diagram-data" type="application/json">(.*?)</script>', page, re.S)[1])
        self.assertIn('</script>', data[0]['source'])

    def test_standalone_skill_and_relocated_output(self):
        isolated = self.root / 'standalone'
        shutil.copytree(renderer.SKILL_ROOT, isolated)
        spec = importlib.util.spec_from_file_location('standalone_renderer', isolated / 'scripts/render_diagrams.py')
        standalone = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(standalone)
        standalone.generate(self.source, self.output)
        shutil.rmtree(isolated)
        moved = self.root / 'moved'
        shutil.move(str(self.output.parent), moved)
        self.source.unlink()
        page = (moved / 'flows.html').read_text()
        for link in re.findall(r'(?:src|href)="(sequence-diagrams/flows.assets/[^"]+)"', page):
            self.assertTrue((moved / link).is_file(), link)
        self.assertNotIn(str(renderer.SKILL_ROOT), page)
        self.assertEqual((moved / 'sequence-diagrams/flows.assets/mermaid-12.3.0.min.js').read_bytes(), (renderer.ASSETS / 'mermaid-12.3.0.min.js').read_bytes())


def load_tests(loader, tests, pattern):
    tests.addTests(loader.discover(str(Path(__file__).resolve().parents[1] / 'tests')))
    return tests


if __name__ == '__main__':
    unittest.main()
