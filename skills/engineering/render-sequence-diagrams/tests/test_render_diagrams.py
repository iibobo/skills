import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('render', ROOT / 'scripts/render_diagrams.py')
render = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render)

class RendererTests(unittest.TestCase):
    def test_regeneration_preserves_navigation_and_scale(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = 'sequenceDiagram\n participant A as nowrap: Demo\n A->>A: call()'
            mapping = {'symbols': {'Demo': {'className': 'demo.Demo', 'methods': {'call()': {'methodName': 'call', 'parameterTypes': []}}}}, 'diagrams': [{'sourceHash': hashlib.sha256(source.encode()).hexdigest(), 'participants': {'A': {'label': 'Demo', 'links': [{'text': 'Demo', 'symbol': 'Demo'}]}}, 'messages': [{'from': 'A', 'to': 'A', 'label': 'call()', 'links': [{'text': 'call', 'symbol': 'Demo', 'method': 'call()'}]}]}]}
            (root / 'map.json').write_text(json.dumps(mapping))
            md = root / 'demo.md'
            md.write_text('# Demo\n<!-- sequence-viewer: {"initialZoom":0.71,"sourceMap":"map.json"} -->\n```mermaid\n' + source + '\n```\n')
            output = root / 'demo.html'
            render.generate(md, output)
            first = output.read_bytes()
            render.generate(md, output, overwrite=True)
            self.assertEqual(first, output.read_bytes())
            self.assertEqual(md.read_bytes(), (root / 'sequence-diagrams/demo.assets/source.md').read_bytes())
            self.assertEqual(mapping, json.loads((root / 'sequence-diagrams/demo.assets/map.json').read_text()))
            self.assertIn('zoom=0.71', output.read_text())
            # A changed call cannot silently reuse the previous target.
            md.write_text(md.read_text().replace('A->>A: call()', 'A->>A: other()'))
            with self.assertRaisesRegex(ValueError, 'Stale'):
                render.generate(md, output, overwrite=True)
            self.assertEqual(first, output.read_bytes())

    def test_missing_mapping_rejected(self):
        with self.assertRaises(ValueError):
            render.validate_mapping([{'source': 'sequenceDiagram'}], {}, True)

    def test_invalid_method_reference_rejected(self):
        source = 'sequenceDiagram\n participant A as Demo'
        mapping = {'symbols': {'Demo': {'className': 'demo.Demo'}}, 'diagrams': [{'sourceHash': hashlib.sha256(source.encode()).hexdigest(), 'participants': {'A': {'label': 'Demo', 'links': [{'text': 'Demo', 'symbol': 'Demo', 'method': 'missing()'}]}}, 'messages': []}]}
        with self.assertRaisesRegex(ValueError, 'Unresolved'):
            render.validate_mapping([{'source': source, 'title': 'Demo'}], mapping, True)

    def test_strict_mapping_requires_unaliased_participants(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = 'sequenceDiagram\n actor Requester\n participant Worker as Service\n Requester->>Worker: call()'
            markdown = root / 'demo.md'
            markdown.write_text(f'```mermaid\n{source}\n```\n')
            output = root / 'demo.html'
            mapping_file = root / 'map.json'
            scene = {
                'sourceHash': hashlib.sha256(source.encode()).hexdigest(),
                'participants': {'Worker': {'label': 'Service', 'reason': 'External service'}},
                'messages': [{'from': 'Requester', 'to': 'Worker', 'label': 'call()', 'reason': 'External call'}],
            }
            mapping_file.write_text(json.dumps({'diagrams': [scene]}))
            with self.assertRaisesRegex(ValueError, 'Missing participants: Requester'):
                render.generate(markdown, output, source_map=mapping_file, require_source_links=True)
            self.assertFalse(output.exists())

            scene['participants']['Requester'] = {'label': 'Requester', 'reason': 'Human actor'}
            mapping_file.write_text(json.dumps({'diagrams': [scene]}))
            self.assertEqual(render.generate(markdown, output, source_map=mapping_file), 1)

    def test_strict_mapping_checks_activation_arrows_and_implicit_participants(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = 'sequenceDiagram\n A->>+B: call()\n B-->>-A: result'
            markdown = root / 'activation.md'
            markdown.write_text(f'```mermaid\n{source}\n```\n')
            output = root / 'activation.html'
            mapping_file = root / 'map.json'
            scene = {
                'sourceHash': hashlib.sha256(source.encode()).hexdigest(),
                'participants': {name: {'label': name, 'reason': 'External participant'} for name in ('A', 'B')},
                'messages': [{'from': 'A', 'to': 'B', 'label': 'call()', 'reason': 'External call'}],
            }
            mapping_file.write_text(json.dumps({'diagrams': [scene]}))
            with self.assertRaisesRegex(ValueError, 'Mapping coverage differs from source'):
                render.generate(markdown, output, source_map=mapping_file)
            scene['messages'].append({'from': 'B', 'to': 'A', 'label': 'result', 'reason': 'Return value'})
            mapping_file.write_text(json.dumps({'diagrams': [scene]}))
            self.assertEqual(render.generate(markdown, output, source_map=mapping_file), 1)

if __name__ == '__main__':
    unittest.main()
