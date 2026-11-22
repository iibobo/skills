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

if __name__ == '__main__':
    unittest.main()
