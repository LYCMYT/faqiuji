import unittest
from control.feed_cycle import FeedCycle
from tests.test_control_input_contract import baseline

class CommandLifecycle(unittest.TestCase):
    def test_home_already_true_can_complete_after_fresh_acceptance(self):
        c=FeedCycle();c.state='HOME'
        s=baseline();s['head_home']=True
        c.step(s,.1)
        self.assertIsNotNone(c.outputs().get('command'))
        cmd=c.outputs()['command']
        ack=dict(cycle_id=cmd['cycle_id'],accepted_id=cmd['command_id'],completed_id=None,actual_position=0.,in_tolerance=True,sample_id=1)
        self.assertEqual(c.step(s,.1,ack=ack)['state'],'HOME')
        ack.update(completed_id=cmd['command_id'],sample_id=2)
        self.assertEqual(c.step(s,.1,ack=ack)['state'],'LOAD')

    def test_pause_reset_require_explicit_restart(self):
        c=FeedCycle();c.pause();self.assertEqual(c.state,'PAUSED')
        c.reset();self.assertEqual(c.state,'IDLE')
        self.assertEqual(c.step({**baseline(),'start':True},.1)['state'],'IDLE')
        c.restart();self.assertEqual(c.step({**baseline(),'start':True},.1)['state'],'GUIDE_DOWN')

    def test_old_cross_cycle_repeated_and_wrong_target_ack_do_not_advance(self):
        c=FeedCycle();c.state='HOME';s=baseline();c.step(s,.1)
        cmd=c.outputs()['command']
        good=dict(cycle_id=cmd['cycle_id'],accepted_id=cmd['command_id'],completed_id=cmd['command_id'],actual_position=0.,in_tolerance=True,sample_id=1)
        for bad in [dict(cycle_id='old'),dict(accepted_id='old'),dict(completed_id='old'),dict(actual_position=1.),dict(in_tolerance=1),dict(sample_id=True)]:
            self.assertEqual(c.step(s,.1,ack={**good,**bad})['state'],'HOME')
        # Current command was accepted at sample 1, but replaying that sample
        # cannot acknowledge completion, even when physical home stays true.
        self.assertEqual(c.step(s,.1,ack=good)['state'],'HOME')
        self.assertEqual(c.step(s,.1,ack={**good,'sample_id':2})['state'],'LOAD')
        self.assertEqual(c.step(s,.1,ack={**good,'sample_id':3})['state'],'LOAD')

    def test_fault_latches_and_unknown_operations_rejected(self):
        c=FeedCycle();c.trip('test');c.pause();self.assertEqual(c.state,'FAULT')
        with self.assertRaises(ValueError):c.restart()
        c.reset();self.assertIsNone(c.outputs()['command'])
        with self.assertRaises(TypeError):c.step(baseline(),.1,stop=True)
        self.assertIn('BLOCKED',c.outputs()['safe_intent_status'])

    def test_duplicate_command_is_rejected(self):
        from control.commands import Command,CommandLifecycle
        lifecycle=CommandLifecycle();cmd=Command('id','cycle','head',0.,0.)
        lifecycle.issue(cmd)
        with self.assertRaises(ValueError):lifecycle.issue(cmd)
        lifecycle.issue(Command('next','cycle','head',0.,1.))
        with self.assertRaises(ValueError):lifecycle.issue(cmd)

    def test_zero_angle_full_single_cycle_and_done_does_not_repeat(self):
        c=FeedCycle();c.restart();s=baseline()
        path=[{},dict(start=True),dict(guide_up=False,guide_down=True),dict(upper_held=True),dict(gate_open=True,gate_closed=False,ball_present=True),dict(gate_closed=True,gate_open=False),dict(clamp_closed=True,clamp_open=False),dict(guide_up=True,guide_down=False),dict(slide_clear=True,slide_home=False),dict(aim_reached=True,wheels_ready=True),dict(clamp_open=True,clamp_closed=False),dict(capture_detected=True,slide_clear=False),dict(exit=True),dict(exit=False),dict(slide_clear=True),{},dict(slide_home=True)]
        for change in path:
            s.update(change);self.assertTrue(s['head_home'])
            cmd=c.outputs()['command']
            if cmd:
                ack=dict(cycle_id=cmd['cycle_id'],accepted_id=cmd['command_id'],completed_id=None,actual_position=cmd['target'],in_tolerance=True,sample_id=1)
                c.step(s,.1,ack=ack)
                out=c.step(s,.1,ack={**ack,'completed_id':cmd['command_id'],'sample_id':2})
            else:out=c.step(s,.1)
            self.assertNotEqual(out['state'],'FAULT',out)
        self.assertEqual(c.state,'DONE')
        for _ in range(3):self.assertEqual(c.step(s,.1)['state'],'DONE')

    def test_acceptance_while_moving_counts_before_in_tolerance_completion(self):
        c=FeedCycle();c.state='LOAD';s=baseline();s['slide_home']=False;c.step(s,.1)
        cmd=c.outputs()['command']
        ack=dict(cycle_id=cmd['cycle_id'],accepted_id=cmd['command_id'],completed_id=None,actual_position=10.,in_tolerance=False,sample_id=1)
        self.assertEqual(c.step(s,.1,ack=ack)['state'],'LOAD')
        s['slide_home']=True
        self.assertEqual(c.step(s,.1,ack={**ack,'completed_id':cmd['command_id'],'actual_position':0.,'in_tolerance':True,'sample_id':2})['state'],'DONE')

    def test_recreated_controller_does_not_replay_persistent_start(self):
        for _ in range(2):
            c=FeedCycle()
            self.assertFalse(c.armed)
            for _ in range(3):self.assertEqual(c.step({**baseline(),'start':True},.1)['state'],'IDLE')
            c.restart()
            self.assertEqual(c.state,'IDLE')
            self.assertEqual(c.step({**baseline(),'start':True},.1)['state'],'GUIDE_DOWN')
