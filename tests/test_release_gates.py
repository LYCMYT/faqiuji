import sys
import tempfile
import unittest
from pathlib import Path
from tools.build_context import BuildContext
from tools.validate_release import require_report, run_stage, validate_release


class ReleaseGates(unittest.TestCase):
    def test_scope_identity_and_failed_stage(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); ctx=BuildContext.create(root,'negative','full')
            for change in ({'scope':'static'},{'run_id':'old'},{'status':'FAIL'},{'completed_checks':[]}):
                report=ctx.report('PASS',['motion']); report.update(change)
                with self.assertRaises(RuntimeError): require_report(report,ctx,['motion'])
            with self.assertRaises(RuntimeError): run_stage([sys.executable,'-c','raise RuntimeError("injected")'],ctx,root)
            report=root/'reports/builds'/ctx.run_id/'negative.json'
            self.assertIn('"FAIL"',report.read_text())
            with self.assertRaises(RuntimeError): run_stage([sys.executable,'-c','pass'],ctx,root,expected_files=['missing.step'])

    def test_missing_expected_file_and_source_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/'data').mkdir(); (root/'data/design.json').write_text('{}')
            ctx=BuildContext.create(root)
            with self.assertRaises(RuntimeError): validate_release(root,ctx,{},['missing.step'])
            (root/'data/design.json').write_text('{"gap":30}')
            with self.assertRaises(RuntimeError): require_report(ctx.report('PASS'),ctx,root=root)

if __name__=='__main__': unittest.main()
