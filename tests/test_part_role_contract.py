import csv
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORRECTIONS = {
    'PRT-0402': ('短耳轴', '扇形板'),
    'PRT-0702': ('定位夹', '限位块'),
    'PRT-0704': ('夹持释放', '滑台执行器'),
    'PRT-0903': ('配电', '辅助电机驱动'),
}


class PartRoleContractTests(unittest.TestCase):
    def test_d01_routes_match_actual_functions(self):
        routes = json.loads((ROOT / 'data/r2_process_routes.json').read_text(encoding='utf-8'))['routes']
        for part_id, (required, forbidden) in CORRECTIONS.items():
            with self.subTest(part_id=part_id):
                self.assertIn(required, routes[part_id][0])
                self.assertNotIn(forbidden, ' '.join(routes[part_id]))

    def test_d01_errors_do_not_propagate_to_generated_rfq(self):
        with (ROOT / 'output/prototype_r2/manufacturing_routes_44_RFQ.csv').open(encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.DictReader(stream))
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
