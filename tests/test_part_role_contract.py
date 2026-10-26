import csv
import json
import unittest
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORRECTIONS = {
    'PRT-0402': ('短耳轴', '扇形板'),
    'PRT-0702': ('定位夹', '限位块'),
    'PRT-0704': ('夹持释放', '滑台执行器'),
    'PRT-0903': ('配电', '辅助电机驱动'),
}


class PartRoleContractTests(unittest.TestCase):
    def test_r4_rfq_includes_declared_retained_candidates_and_actual_revisions(self):
        from tools.r4_rfq import first_article_rfq_rows
        declared=json.loads((ROOT/'data/r4_first_article.json').read_text(encoding='utf-8'));families=[v['family'] for v in declared['items']]+['PRT-0607-B-R4']
        index=[dict(family=f,step='step/parts/'+f+'.step',source_revision='descriptive inherited source',quantity_in_assembly=99,material='candidate',holes=[]) for f in families];rows=first_article_rfq_rows(index,declared);by={v['family']:v for v in rows}
        self.assertEqual(set(families),set(by));self.assertEqual('R3',by['PRT-0603-R3-R29-L']['revision']);self.assertEqual('R3',by['PRT-0602-R3-BASE']['revision']);self.assertEqual('R4',by['PRT-0701-R4-A']['revision'])
        for row in rows:
            for field in ['supplier','quantity','quote_CNY','lead_days']:self.assertIsNone(row[field])
            self.assertFalse(row['supplier_confirmed']);self.assertFalse(row['first_article_released']);self.assertFalse(row['manufacturing_release'])
        from tools.r4_rfq import write_first_article_rfq
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'RFQ.csv';write_first_article_rfq(path,index,declared)
            with path.open(encoding='utf-8-sig',newline='') as stream:exported=list(csv.DictReader(stream))
        self.assertEqual({v['family'] for v in exported},set(families))
        for row in exported:
            for field in ['supplier','quantity','quote_CNY','lead_days']:self.assertEqual(row[field],'')
            for field in ['supplier_confirmed','first_article_released','manufacturing_release']:self.assertEqual(row[field],'False')
    def test_r4_rfq_fails_if_declared_candidate_missing(self):
        from tools.r4_rfq import first_article_rfq_rows
        with self.assertRaises(ValueError):first_article_rfq_rows([],{'items':[{'family':'PRT-0602-R3-BASE'}]})
    def test_native_r4_hardware_default_provenance_is_not_r3_retained(self):
        from tools.r4_rfq import native_source_revision
        self.assertEqual(native_source_revision({'family':'PRT-0603-R4-CAP-M3-SCREW'}),'R4 self-designed candidate');self.assertEqual(native_source_revision({'family':'PRT-0602-R3-BASE'}),'R3 retained');self.assertEqual(native_source_revision({'family':'PRT-0701-R4-A','source_revision':'R3 cradle + explicit R4 land'}),'R3 cradle + explicit R4 land')
    def test_d01_routes_match_actual_functions(self):
        routes = json.loads((ROOT / 'data/r2_process_routes.json').read_text(encoding='utf-8'))['routes']
        for part_id, (required, forbidden) in CORRECTIONS.items():
            with self.subTest(part_id=part_id):
                self.assertIn(required, routes[part_id][0])
                self.assertNotIn(forbidden, ' '.join(routes[part_id]))

    def test_d01_errors_do_not_propagate_to_generated_rfq(self):
        from tools.part_role_contract import write_rfq
        read=lambda name:json.loads((ROOT/'data'/name).read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'RFQ.csv'
            write_rfq(path,read('parts.json'),read('part_roles.json'),read('r2_process_routes.json'))
            with path.open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.DictReader(stream))
        self.assertEqual(44, len(rows))
        indexed = {row['part_id']: row for row in rows}
        for part_id, (required, forbidden) in CORRECTIONS.items():
            with self.subTest(part_id=part_id):
                self.assertIn(required, indexed[part_id]['route_choice'])
                self.assertNotIn(forbidden, indexed[part_id]['route_choice'])
        for row in rows:
            self.assertEqual('False', row['manufacture_released'])
            for field in ('supplier', 'material_lot', 'quote_CNY', 'lead_time_days'):
                self.assertEqual('', row[field])

    def test_all_roles_are_explicit_and_source_traced(self):
        role_path = ROOT / 'data/part_roles.json'
        self.assertTrue(role_path.exists(), 'Explicit reviewed 44-item role contract is missing')
        if not role_path.exists():
            return
        from tools.part_role_contract import validate_part_roles
        parts = json.loads((ROOT / 'data/parts.json').read_text(encoding='utf-8'))
        roles = json.loads(role_path.read_text(encoding='utf-8'))
        routes = json.loads((ROOT / 'data/r2_process_routes.json').read_text(encoding='utf-8'))
        validate_part_roles(parts, roles, routes)
        self.assertEqual({p['part_id'] for p in parts}, set(roles['parts']))
        self.assertFalse(roles['manufacturing_release'])

    def test_incompatible_route_and_stale_function_are_rejected(self):
        self.assertTrue((ROOT / 'data/part_roles.json').exists(), 'Role contract required')
        if not (ROOT / 'data/part_roles.json').exists():
            return
        from tools.part_role_contract import validate_part_roles
        parts = json.loads((ROOT / 'data/parts.json').read_text(encoding='utf-8'))
        roles = json.loads((ROOT / 'data/part_roles.json').read_text(encoding='utf-8'))
        routes = json.loads((ROOT / 'data/r2_process_routes.json').read_text(encoding='utf-8'))
        routes['route_categories']['PRT-0704'] = 'linear_motion_module'
        with self.assertRaises(ValueError):
            validate_part_roles(parts, roles, routes)
        routes['route_categories']['PRT-0704'] = roles['parts']['PRT-0704']['route_category']
        parts[0]['function'] = 'changed without engineering review'
        with self.assertRaises(ValueError):
            validate_part_roles(parts, roles, routes)

    def test_role_cannot_be_relabelled_as_unrelated_function(self):
        from tools.part_role_contract import validate_part_roles
        parts = json.loads((ROOT / 'data/parts.json').read_text(encoding='utf-8'))
        roles = json.loads((ROOT / 'data/part_roles.json').read_text(encoding='utf-8'))
        routes = json.loads((ROOT / 'data/r2_process_routes.json').read_text(encoding='utf-8'))
        roles['parts']['PRT-0704']['role'] = roles['parts']['PRT-0703']['role']
        with self.assertRaises(ValueError):
            validate_part_roles(parts, roles, routes)


if __name__ == '__main__':
    unittest.main()
