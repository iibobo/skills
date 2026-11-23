#!/usr/bin/env python3
"""Meaningful generator contract checks; independent of the calling repository."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('render_diagrams', Path(__file__).with_name('render_diagrams.py'))
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class SourceLinksTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'diagram.md'
        self.source.write_text('# Example\n\n```mermaid\nclassDiagram\n class Worker {\n +call(request) Result\n }\n```\n')
        self.mapping = self.root / 'symbols.json'
        self.data = {'Worker': {'className': 'example.Worker', 'methods': {'call(request)': {
            'methodName': 'call', 'parameterTypes': ['example.Request']}}}}

    def tearDown(self):
        self.temp.cleanup()

    def generate(self):
        self.mapping.write_text(json.dumps(self.data))
        return renderer.generate(self.source, self.root / 'out.html', source_map=self.mapping, require_source_links=True)

    def test_symbols_need_no_sources_and_preserve_exact_targets(self):
        self.assertEqual(self.generate(), 1)
        page = (self.root / 'out.html').read_text()
        self.assertIn('example.Request', page)
        self.assertFalse((self.root / 'class-diagrams/out.assets/sources').exists())
        self.assertEqual((self.root / 'class-diagrams/out.assets/source.md').read_text(), self.source.read_text())

    def test_missing_method_fails_before_creating_output(self):
        self.data['Worker']['methods'] = {}
        with self.assertRaisesRegex(ValueError, 'Missing source links'):
            self.generate()
        self.assertFalse((self.root / 'out.html').exists())

    def test_inline_method_requires_the_same_mapping_as_a_block_member(self):
        self.source.write_text('```mermaid\nclassDiagram\n class Worker\n Worker : +call(request) Result\n```\n')
        target = self.data['Worker']['methods'].pop('call(request)')
        with self.assertRaisesRegex(ValueError, r'Missing source links: Worker\.call\(request\)'):
            self.generate()
        self.assertFalse((self.root / 'out.html').exists())

        self.data['Worker']['methods']['call(request)'] = target
        self.assertEqual(self.generate(), 1)
        self.assertIn('example.Request', (self.root / 'out.html').read_text())

    def test_shortened_parameters_rejected(self):
        self.data['Worker']['methods']['call(request)']['parameterTypes'] = ['...']
        with self.assertRaisesRegex(ValueError, 'parameterTypes'):
            self.generate()

    def test_legacy_missing_file_is_not_a_valid_fallback(self):
        self.data = {'Worker': {'file': 'missing.java', 'line': 2}}
        with self.assertRaises(OSError):
            self.generate()

    def test_declaring_class_override_preserved(self):
        self.data['Worker']['methods']['call(request)']['className'] = 'example.Contract'
        self.generate()
        self.assertIn('example.Contract', (self.root / 'out.html').read_text())

    def test_overwriting_with_a_plain_diagram_removes_copied_source(self):
        self.source.write_text('```mermaid\nclassDiagram\n class Worker\n```\n')
        java = self.root / 'Worker.java'
        java.write_text('class Worker {}\n')
        self.data = {'Worker': {'file': java.name, 'line': 1}}
        self.generate()
        assets = self.root / 'class-diagrams/out.assets'
        self.assertEqual(len(list((assets / 'sources').glob('*Worker.java'))), 1)
        notes = assets.parent / 'notes.md'
        notes.write_text('Keep this file.\n')

        renderer.generate(self.source, self.root / 'out.html', overwrite=True)

        self.assertFalse((assets / 'sources').exists())
        self.assertNotIn('Worker.java', (self.root / 'out.html').read_text())
        self.assertEqual((assets / 'source.md').read_text(), self.source.read_text())
        self.assertEqual(notes.read_text(), 'Keep this file.\n')

    def test_failed_overwrite_preserves_previous_resources(self):
        self.generate()
        assets = self.root / 'class-diagrams/out.assets'
        before = (assets / 'source.md').read_bytes()
        output = self.root / 'out.html'
        output.unlink()
        output.mkdir()
        self.source.write_text(self.source.read_text().replace('Example', 'Changed'))

        with self.assertRaises(OSError):
            renderer.generate(self.source, output, overwrite=True)

        self.assertEqual((assets / 'source.md').read_bytes(), before)
        self.assertTrue(output.is_dir())
        self.assertEqual(list(assets.parent.iterdir()), [assets])


def load_tests(loader, tests, pattern):
    tests.addTests(loader.discover(str(Path(__file__).resolve().parents[1] / 'tests')))
    return tests


if __name__ == '__main__':
    unittest.main()
