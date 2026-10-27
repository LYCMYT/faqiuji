import tempfile,unittest
from pathlib import Path
from tools.delivery_files import collect_delivery_files

class DeliveryFiles(unittest.TestCase):
    def test_original_evidence_survives_cache_and_log_filters(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            required=['input/audits/evidence/existing_tests.log','evidence/service/raw.brep','data/frames/parameters.json','tools/generator.py','.github/workflows/check.yml','README.md']
            excluded=['output/fixture_r4/frames/0001.png','output/mesh/cache.brep','output/history/prior.step','reports/old.log']
            for name in required+excluded:
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('original')
            actual={path.relative_to(root).as_posix() for path in collect_delivery_files(root,'current-run')}
            self.assertTrue(set(required)<=actual)
            self.assertFalse(set(excluded)&actual)

if __name__=='__main__':unittest.main()
