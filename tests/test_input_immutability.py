import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class InputImmutability(unittest.TestCase):
    def test_enrichment_preserves_nonempty_authority_and_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shutil.copytree(ROOT / 'data', root / 'data')
            shutil.copytree(ROOT / 'tools', root / 'tools', ignore=shutil.ignore_patterns('__pycache__', 'blender'))
            materials = json.loads((root / 'data/materials.json').read_text(encoding='utf-8'))
            materials[0].update(density_kg_m3=1234, supplier_model='TEST-NONEMPTY', status='evidence_provided')
            (root / 'data/materials.json').write_text(json.dumps(materials), encoding='utf-8')
            contacts = json.loads((root / 'data/contact_pairs.json').read_text(encoding='utf-8'))
            contacts[0]['condition'] = 'TEST-CONTACT-DO-NOT-RESET'
            (root / 'data/contact_pairs.json').write_text(json.dumps(contacts), encoding='utf-8')
            (root / 'evidence').mkdir()
            (root / 'evidence/index.json').write_text('{"records":[{"id":"TEST"}]}')
            before = {str(p.relative_to(root)): p.read_bytes() for folder in ('data', 'evidence') for p in (root / folder).rglob('*') if p.is_file()}
            subprocess.run([sys.executable, str(root / 'tools/enrich_metadata.py')], check=True, capture_output=True)
            self.assertEqual(before, {p: (root / p).read_bytes() for p in before})

    def test_snapshot_detects_added_changed_and_removed_inputs(self):
        from tools.input_manifest import snapshot_inputs, require_unchanged
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / 'data').mkdir()
            (root / 'data/design.json').write_text('{}')
            before = snapshot_inputs(root)
            (root / 'data/new.json').write_text('{}')
            with self.assertRaisesRegex(RuntimeError, 'new.json'):
                require_unchanged(root, before)

if __name__ == '__main__':
    unittest.main()
