import tempfile
import unittest
from pathlib import Path
from tools.build_context import BuildContext, fingerprint_inputs


class Provenance(unittest.TestCase):
    def test_all_declared_input_and_generator_changes_invalidate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            files = ['data/design.json','data/parts.json','data/contact_pairs.json','data/r3_fixture.json',
                     'cad/assemblies/kinematics.py','cad/parts/recipe.py']
            for name in files:
                p=root/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text('25')
            ctx=BuildContext.create(root)
            self.assertNotEqual(ctx.run_id, BuildContext.create(root).run_id)
            for name in files:
                (root/name).write_text('30')
                with self.assertRaisesRegex(RuntimeError,'Stale build source'): ctx.assert_current(root)
                (root/name).write_text('25')
            ctx.assert_current(root)
            self.assertEqual(fingerprint_inputs(root,files),fingerprint_inputs(root,list(reversed(files))))

if __name__ == '__main__': unittest.main()
