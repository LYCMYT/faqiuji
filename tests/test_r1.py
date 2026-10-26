import unittest,sys,math,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))

class RevisionContracts(unittest.TestCase):
    def safe(self):
        return dict(start=False,head_home=True,slide_home=True,slide_clear=False,aim_reached=False,gate_closed=True,gate_open=False,cover_closed=True,estop_ok=True,cassette_locked=True,exit=False,capture_detected=False,guide_up=True,guide_down=False,clamp_open=True,clamp_closed=False,wheels_ready=True,upper_held=True,ball_present=True)
    def test_upper_retained_until_gate_closed(self):
        from control.feed_cycle import FeedCycle
        c=FeedCycle();c.state='GATE_CLOSE'
        r=c.step({**self.safe(),'guide_up':False,'guide_down':True,'gate_closed':False,'gate_open':True},.1)
        self.assertEqual(r['upper_target'],'hold')
        c=FeedCycle();c.state='DROP'
        self.assertEqual(c.step({**self.safe(),'upper_held':False,'gate_open':True,'gate_closed':False,'guide_up':False,'guide_down':True},.1)['state'],'FAULT')
    def test_missing_exit_is_not_a_falling_edge(self):
        from control.feed_cycle import FeedCycle
        c=FeedCycle();c.state='WAIT_EXIT';c.step({**self.safe(),'exit':True},.1)
        obs=self.safe();obs.pop('exit')
        self.assertEqual(c.step(obs,.1)['state'],'FAULT')
    def test_old_position_feedback_cannot_skip_return(self):
        from control.feed_cycle import FeedCycle
        c=FeedCycle();c.state='RETREAT'
        obs={**self.safe(),'slide_clear':True,'head_home':True}
        for _ in range(3):self.assertEqual(c.step(obs,.1)['state'],'RETREAT')
        c.step({**obs,'slide_clear':False},.1)
        self.assertEqual(c.step(obs,.1)['state'],'RETREAT')
        cmd=c.outputs()['command']
        ack=dict(cycle_id=cmd['cycle_id'],accepted_id=cmd['command_id'],completed_id=None,actual_position=cmd['target'],in_tolerance=True,sample_id=1)
        c.step(obs,.1,ack=ack)
        self.assertEqual(c.step(obs,.1,ack={**ack,'completed_id':cmd['command_id'],'sample_id':2})['state'],'HOME')
        self.assertEqual(c.step(obs,.1,ack={**ack,'completed_id':cmd['command_id'],'sample_id':3})['state'],'HOME')
    def test_feedback_loss_stops_active_cycle(self):
        from control.feed_cycle import FeedCycle
        for state in ['APPROACH','WAIT_EXIT']:
            for value in [False,None]:
                c=FeedCycle();c.state=state
                self.assertEqual(c.step({**self.safe(),'wheels_ready':value},.1)['state'],'FAULT')
        c=FeedCycle();c.state='CLEAR'
        self.assertEqual(c.step({**self.safe(),'ball_present':False,'clamp_closed':True,'clamp_open':False},.1)['fault'],'held_ball_feedback_lost')
    def test_nonphysical_supports_rejected(self):
        from engineering.evaluate import evaluate
        rows=[dict(instance_id='x',mass_kg=40,com_world_mm=[0,0,1000],evidence_status='measured_or_supplier_verified')]
        for stiffness in [-100,0,float('nan')]:
            supports=[dict(x_mm=x,y_mm=y,vertical_stiffness_N_mm=stiffness) for x in [-400,400] for y in [-400,400]]
            with self.assertRaises(ValueError):evaluate(rows,supports)
    def test_uncapturable_geometry_is_explicit(self):
        from unittest.mock import patch
        from control.feed_cycle import FeedCycle
        with patch('control.feed_cycle.capture_stroke',return_value=None):
            c=FeedCycle();self.assertEqual(c.step({**self.safe(),'start':True,'head_home':True,'slide_home':True},.1)['state'],'FAULT')
        from tools.check_collisions import annotate_capture_states
        result=annotate_capture_states([dict(slide=185)],None)
        self.assertFalse(result[0]['capture_geometry_supported'])
    def test_service_dynamic_wire_uses_requested_height(self):
        import cadquery as cq
        from cad.assemblies.posing import pose_shape
        item=dict(parent='WORLD_STATIC',dynamic_height=True)
        recipe=dict(op='box',size=[2,2,2],at=[0,0,'head_axis_height-355'])
        sh=pose_shape(item,cq.Workplane().box(2,2,2).val(),dict(height=1400),recipe)
        self.assertAlmostEqual(sh.Center().z,1045)
    def test_loaded_overrun_and_empty_travel(self):
        from cad.assemblies.kinematics import permitted,capture_stroke
        self.assertFalse(permitted(dict(guide=115,slide=185,clamp=14,loaded=True)))
        self.assertTrue(permitted(dict(guide=115,slide=185,clamp=14,loaded=False)))
        self.assertAlmostEqual(capture_stroke(),178.85044843902224,places=4)
    def test_capture_requires_fresh_exit_pulse(self):
        from control.feed_cycle import FeedCycle
        c=FeedCycle();c.state='WAIT_EXIT';c.last_exit=False
        safe=self.safe()
        self.assertEqual(c.step(safe,.1)['state'],'WAIT_EXIT')
        c.step({**safe,'exit':True},.1)
        self.assertEqual(c.state,'WAIT_EXIT')
        self.assertEqual(c.step(safe,.1)['state'],'RETREAT')
    def test_fault_is_latched(self):
        from control.feed_cycle import FeedCycle
        c=FeedCycle();r=c.step(dict(cover_closed=False,estop_ok=True,cassette_locked=True),.1)
        self.assertEqual(r['state'],'FAULT');self.assertFalse(r['enable_motion']);self.assertFalse(r['enable_wheels'])
        self.assertEqual(c.step(dict(cover_closed=True,estop_ok=True,cassette_locked=True),.1)['state'],'FAULT')
    def test_timeout_and_stuck_exit_do_not_reset(self):
        from control.feed_cycle import FeedCycle
        safe=dict(cover_closed=True,estop_ok=True,cassette_locked=True,exit=True)
        c=FeedCycle();self.assertEqual(c.step(safe,.1)['state'],'FAULT')
        c=FeedCycle();c.state='WAIT_EXIT';c.step({**safe,'exit':False},100)
        self.assertEqual(c.state,'FAULT')
    def test_capture_stuck_high_is_rejected(self):
        from control.feed_cycle import FeedCycle
        c=FeedCycle()
        r=c.step({**self.safe(),'capture_detected':True},.1)
        self.assertEqual(r['fault'],'capture_sensor_high_before_approach')
    def test_evidence_gate_and_symmetric_support(self):
        from engineering.evaluate import evaluate
        supports=[dict(x_mm=x,y_mm=y,vertical_stiffness_N_mm=100) for x in [-400,400] for y in [-400,400]]
        self.assertEqual(evaluate([dict(instance_id='x',mass_kg=None)],supports)['status'],'BLOCKED_MISSING_EVIDENCE')
        r=evaluate([dict(instance_id='x',mass_kg=40,com_world_mm=[0,0,1000],evidence_status='measured_or_supplier_verified')],supports,allow_partial=True)
        for f in r['support_reactions_N']:self.assertAlmostEqual(f,98.0665)
    def test_loop_length_invariant(self):
        from cad.parts.cable import return_loop_points,return_loop_length
        lengths=[]
        for q in [0,105,178.85045,185]:
            pts=return_loop_points(-235,-245+q,-95,-52,-65,360,96)
            self.assertAlmostEqual(pts[-1][0],-245+q)
            lengths.append(return_loop_length(-235,-245+q,-95,-52,360))
        for n in lengths:self.assertAlmostEqual(n,360,places=8)

if __name__=='__main__':unittest.main()
