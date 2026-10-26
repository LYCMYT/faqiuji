import unittest
from control.feed_cycle import FeedCycle
from tests.test_control_input_contract import baseline

class ContinuousInterlocks(unittest.TestCase):
    def advance(self,changes):
        c=FeedCycle();s=baseline()
        for change in changes:
            s.update(change);o=c.step(s,.1)
            self.assertNotEqual(o['state'],'FAULT',o)
        return c,s
    def test_guide_down_lost_before_drop(self):
        c,s=self.advance([dict(start=True),dict(guide_up=False,guide_down=True)])
        o=c.step({**s,'guide_down':False,'upper_held':True},.1)
        self.assertEqual(o['fault'],'guide_down_lost');self.assertNotEqual(o['gate_target'],'open');self.assertFalse(o['enable_motion'])
    def test_gate_reopens_after_handover(self):
        c,s=self.advance([dict(start=True),dict(guide_up=False,guide_down=True),dict(upper_held=True),dict(ball_present=True,gate_open=True,gate_closed=False),dict(gate_closed=True,gate_open=False)])
        o=c.step({**s,'gate_closed':False,'gate_open':True,'clamp_closed':True,'clamp_open':False},.1)
        self.assertEqual(o['fault'],'gate_closed_lost');self.assertFalse(o['enable_motion'])
    def test_all_state_required_fields_are_strict(self):
        from control.contracts import validate_observation,ObservationError
        states=['IDLE','GUIDE_DOWN','RETAIN','DROP','GATE_CLOSE','GRIP','GUIDE_UP','CLEAR','AIM','RELEASE','APPROACH','WAIT_EXIT','RETREAT','HOME','LOAD','DONE']
        for state in states:
            s=baseline();validate_observation(s,state)
            for field in s:
                for value in ['false',0,1,None]:
                    with self.subTest(state=state,field=field,value=value):
                        with self.assertRaises(ObservationError):validate_observation({**s,field:value},state)
    def test_lost_interlocks_never_issue_active_targets(self):
        cases=[('DROP','guide_down','guide_down_lost'),('GATE_CLOSE','upper_held','upper_retention_feedback_lost'),('CLEAR','guide_up','guide_up_lost'),('AIM','ball_present','held_ball_feedback_lost'),('APPROACH','clamp_open','release_feedback_lost'),('WAIT_EXIT','wheels_ready','wheel_ready_feedback_lost')]
        for state,field,fault in cases:
            s={**baseline(),'guide_down':state in ['DROP','GATE_CLOSE'],'guide_up':state not in ['DROP','GATE_CLOSE'],'upper_held':True,'ball_present':True,'clamp_closed':state in ['CLEAR','AIM'],'clamp_open':state not in ['CLEAR','AIM'],'wheels_ready':True}
            s[field]=False;c=FeedCycle();c.state=state;o=c.step(s,.1)
            self.assertEqual(o['fault'],fault);self.assertIsNone(o['slide_target_mm']);self.assertIsNone(o['guide_target_mm']);self.assertFalse(o['enable_wheels'])
    def test_release_entry_rejects_high_or_missing_capture_before_output(self):
        path=[dict(start=True),dict(guide_up=False,guide_down=True),dict(upper_held=True),dict(ball_present=True,gate_open=True,gate_closed=False),dict(gate_closed=True,gate_open=False),dict(clamp_closed=True,clamp_open=False),dict(guide_up=True,guide_down=False),dict(slide_clear=True,slide_home=False)]
        for missing in [False,True]:
            c,s=self.advance(path)
            self.assertEqual(c.state,'AIM')
            s.update(aim_reached=True,wheels_ready=True,capture_detected=True)
            if missing:del s['capture_detected']
            o=c.step(s,.1)
            self.assertEqual(o['fault'],'capture_detected_feedback_missing_or_invalid' if missing else 'capture_sensor_high_before_approach')
            for key in ['slide_target_mm','guide_target_mm','clamp_target','gate_target','upper_target']:self.assertIsNone(o[key])
            self.assertFalse(o['enable_motion']);self.assertFalse(o['enable_wheels'])
