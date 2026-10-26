"""Regression counterexamples, not load/physical qualification."""
import unittest,json
from pathlib import Path
import cadquery as cq
from cad.assemblies.r4_fixture import model,posed
from cad.assemblies.kinematics import parameters
from cad.parts.recipe import build
R=Path(__file__).resolve().parents[1]
class R4MechanicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows,cls.variants,cls.s,cls.b=model();cls.by={a['instance_id']:a for a in cls.rows};cls.p=parameters()
        refs=json.loads((R/'data/geometry.json').read_text(encoding='utf-8'))['instances'];cls.cork=build(next(a['shape'] for a in refs if a['instance_id']=='PRT-REF-CORK'),cls.p)
    def test_every_export_body_single_native_solid(self):
        self.assertTrue(all(a['shape'].isValid() and len(a['shape'].Solids())==1 for a in self.rows+self.variants))
    def test_seat_blocks_original_descending_tipping_counterexample(self):
        x=self.p['load_x']+5.5;pivot=(x,0,-13)
        moved=self.cork.rotate(pivot,(x,1,-13),1)
        self.assertGreater(moved.intersect(self.by['PRT-0701-A']['shape']).Volume(),.01)
    def test_seat_blocks_free_downward_drop(self):
        self.assertGreater(self.cork.translate((0,0,-.1)).intersect(self.by['PRT-0701-A']['shape']).Volume(),.01)
    def test_slide_endpoint_matches_authoritative_stroke(self):
        self.assertEqual(self.s['manual_guides']['slide']['stroke_mm'],self.p['carriage_total_stroke'])
    def test_fixed_guides_are_not_five_moving_translation_parents(self):
        for name in ['PRT-0602-C__L410','PRT-0602-G','PRT-0607-A']:
            self.assertEqual(self.by[name]['parent'],'FIXED_HEAD_CARRIER')
        self.assertEqual(self.by['PRT-0703-A']['parent'],'MOVING_HEAD')
        self.assertEqual(self.by['PRT-0701-C']['parent'],'CARRIAGE')
    def test_guide_assembly_has_removable_caps_and_stops(self):
        for token in ['BUSHCAP','ENDSTOP','UPSTOP','TRAVELNUT']:
            self.assertTrue(any(token in k for k in self.by),token)
    def test_no_invented_physical_result_or_manufacturing_release(self):
        self.assertEqual(self.s['real_ball_samples'],[]);self.assertIsNone(self.s['manual_force_N']);self.assertFalse(self.s['manufacturing_release'])
if __name__=='__main__':unittest.main()
