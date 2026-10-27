"""Machine-readable test evidence from this invocation only."""
from pathlib import Path
import sys
import unittest
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from tools.build_context import active_context, atomic_json

if __name__=='__main__':
    ctx=active_context(R,'unit_tests')
    suite=unittest.defaultTestLoader.discover(str(R/'tests'))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    atomic_json(R/'reports/unit_tests.json',ctx.report('PASS' if result.wasSuccessful() else 'FAIL',
        ['unit_tests'], tests_run=result.testsRun, failures=len(result.failures), errors=len(result.errors),
        skipped=len(result.skipped)))
    raise SystemExit(0 if result.wasSuccessful() else 1)
