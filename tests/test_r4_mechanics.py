"""Regression counterexamples, not load/physical qualification."""
import unittest,json
from pathlib import Path
import cadquery as cq
from cad.assemblies.r4_fixture import model,posed
from cad.assemblies.kinematics import parameters
from cad.parts.recipe import build
from tools.r4_mechanical_checks import retention_acceptance,ball_sequence_checks,endpoint_pin_acceptance,service_removal_checks
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
    def test_modified_tongue_has_r4_provenance(self):
        a=self.by['PRT-0607-B'];self.assertIn('R4',a['family']);self.assertIn('lock bore',a['r4_revision'])
    def test_nominal_native_retention_and_both_end_stops(self):
        state=dict(height=0,guide=0,slide=0,clamp=14,upper=0,gate=0)
        for axis in ['upper','gate','guide','slide','clamp']:
            result=retention_acceptance(self.rows,self.s,self.p,axis,state)
            self.assertEqual(result['status'],'PASS',result)
    def test_disconnected_upper_guide_is_rejected(self):
        changed=[dict(a) for a in self.rows]
        for a in changed:
            if a['instance_id']=='PRT-0603-R3-CARRIER-L':a['shape']=a['shape'].translate((200,0,0))
        result=retention_acceptance(changed,self.s,self.p,'upper',dict(height=0,upper=0),False)
        self.assertEqual(result['status'],'FAIL')
    def test_detached_fixed_bush_is_rejected(self):
        changed=[dict(a) for a in self.rows]
        for a in changed:
            if a['instance_id'] in ['PRT-0602-C__L410','PRT-0603-R4-BUSHCAP-L']:a['shape']=a['shape'].translate((200,0,0))
        self.assertEqual(retention_acceptance(changed,self.s,self.p,'upper',dict(height=0,upper=0),False)['status'],'FAIL')
    def test_detached_sleeve_tongue_is_rejected(self):
        changed=[dict(a) for a in self.rows]
        for a in changed:
            if a['instance_id']=='PRT-0607-B':a['shape']=a['shape'].translate((200,0,0))
        self.assertEqual(retention_acceptance(changed,self.s,self.p,'guide',dict(height=0,guide=0),False)['status'],'FAIL')
    def test_upper_overtravel_is_rejected(self):
        self.assertEqual(retention_acceptance(self.rows,self.s,self.p,'upper',dict(height=0,upper=25),False)['status'],'FAIL')
    def test_nonengaging_positive_pin_is_rejected(self):
        pin=dict(self.by['PRT-0603-R4-HOLDPIN-L']);pin['installed_shape']=pin['installed_shape'].translate((200,0,0));placed={a['instance_id']:sh for a,sh in posed(self.rows,dict(height=0,upper=0))}
        self.assertEqual(endpoint_pin_acceptance(pin,0,placed,self.s,self.p)['status'],'FAIL')
    def test_nominal_removal_and_proposed_new_tool_channels(self):
        state=dict(height=0,guide=self.p['guide_stroke'],slide=0,clamp=14,upper=self.s['service']['upper_work_open_mm'],gate=0);result=service_removal_checks(self.rows,self.s,self.p,state)
        self.assertEqual(result['status'],'PASS',[(v.get('phase',v.get('tool')),v['instance'],v['intersections']) for v in result['paths']+result['candidate_tool_channels'] if v['status']=='FAIL'])
    def test_ball_sequence_explicitly_releases_ownership(self):
        originals=json.loads((R/'data/geometry.json').read_text(encoding='utf-8'))['instances'];refs=[(a['instance_id'],build(a['shape'],self.p)) for a in originals if a['instance_id'] in ['PRT-REF-CORK','PRT-REF-SKIRT']]
        demo=json.loads((R/'data/implementation.json').read_text(encoding='utf-8'))['demo'];result=ball_sequence_checks(self.rows,refs,self.s,self.p,demo['clamp_open_mm'],demo)
        self.assertEqual(result['status'],'PASS',result)
        released=False
        for stage in result['stages']:
            if stage['name']=='RELEASE':released=True;continue
            if released:self.assertFalse(stage['ball_present']);self.assertIsNone(stage['reference_translation_mm'])
if __name__=='__main__':unittest.main()
