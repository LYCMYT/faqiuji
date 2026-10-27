import unittest, math
from control.feed_cycle import FeedCycle
from cad.assemblies.kinematics import permitted

def baseline():
    return dict(start=False,cover_closed=True,estop_ok=True,cassette_locked=True,exit=False,capture_detected=False,head_home=True,slide_home=True,slide_clear=False,aim_reached=False,guide_up=True,guide_down=False,gate_closed=True,gate_open=False,clamp_closed=False,clamp_open=True,upper_held=False,ball_present=False,wheels_ready=False)

class InputContract(unittest.TestCase):
    def test_interval_types(self):
        for dt in [True,False,'0.1',None,float('nan'),float('inf'),0,-1]:
            with self.subTest(dt=dt):
                c=FeedCycle(); c.state='RETAIN'
                o=c.step({**baseline(),'guide_up':False,'guide_down':True,'upper_held':True},dt)
                self.assertEqual(o['fault'],'invalid_sample_interval');self.assertIsNone(o['slide_target_mm']);self.assertFalse(o['enable_motion'])
    def test_required_bool(self):
        for field in ['start','head_home','slide_home','cover_closed','exit','capture_detected']:
            for value in ['false',0,1,None]:
                with self.subTest(field=field,value=value):
                    s=baseline();s[field]=value
                    self.assertEqual(FeedCycle().step(s,.1)['state'],'FAULT')
            s=baseline();del s[field]
            self.assertEqual(FeedCycle().step(s,.1)['state'],'FAULT')
    def test_motion_invalid(self):
        for s in [dict(slide=math.nan),dict(guide=math.inf),dict(yaw=True),dict(slide=-1),dict(slide=1000,loaded=False),dict(yaw=180,pitch=80)]:
            self.assertFalse(permitted(s),s)
    def test_service_ranges_and_per_side_clamp(self):
        from cad.assemblies.kinematics import motion_limits,validate_motion_state
        s=dict(slide=105,yaw=40,pitch=58)
        self.assertIn('limit:yaw_out_of_range',validate_motion_state(s,motion_limits()))
        self.assertEqual(validate_motion_state(s,motion_limits('service')),[])
        self.assertIn('limit:clamp_out_of_range',validate_motion_state(dict(clamp=28),motion_limits()))
    def test_capture_must_be_reachable(self):
        from unittest.mock import patch
        from cad.assemblies.kinematics import motion_limits,validate_motion_state
        for boundary in [None,-1,186,float('nan')]:
            with self.subTest(boundary=boundary),patch('control.feed_cycle.capture_stroke',return_value=boundary):
                self.assertEqual(FeedCycle().step({**baseline(),'start':True},.1)['fault'],'geometry_cannot_capture')
            with patch('cad.assemblies.kinematics.capture_stroke',return_value=boundary):
                self.assertIn('reachability:capture_outside_slide_range',validate_motion_state({},motion_limits()))
    def test_public_validation_and_invalid_mapping(self):
        from control.contracts import validate_observation,validate_interval,ObservationError
        for payload in [None,[],False]:
            with self.assertRaises(ObservationError):validate_observation(payload,'IDLE')
            self.assertEqual(FeedCycle().step(payload,.1)['state'],'FAULT')
        self.assertEqual(validate_interval(.1),.1)
    def test_unrepresentable_real_values_are_contract_failures(self):
        from cad.assemblies.kinematics import validate_motion_state,motion_limits
        c=FeedCycle();c.state='RETAIN'
        o=c.step({**baseline(),'guide_up':False,'guide_down':True,'upper_held':True},10**1000)
        self.assertEqual(o['fault'],'invalid_sample_interval');self.assertFalse(o['enable_motion'])
        for key in ['slide_target_mm','guide_target_mm','clamp_target','gate_target','upper_target']:self.assertIsNone(o[key])
        self.assertIn('data:slide_not_finite_real',validate_motion_state({'slide':10**1000},motion_limits()))
