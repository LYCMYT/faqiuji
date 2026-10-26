"""Offline feedback-contract simulator. No GPIO, network, motor or safety outputs.

Boolean inputs represent observations, not time-based assumptions. Hardware
debounce, wiring categories, stopping time and watchdog integration are NOT certified.
"""
from pathlib import Path
import json,math
from control.contracts import ObservationError,validate_interval,validate_observation,check_invariants
from cad.assemblies.kinematics import capture_stroke,parameters
R=Path(__file__).resolve().parents[1]

class FeedCycle:
    def __init__(self):
        self.state='IDLE';self.elapsed=0.;self.last_exit=False;self.exit_seen=False;self.fault=None
        self.arrival_low_seen=False
        self.spec=json.loads((R/'data/r1_engineering.json').read_text(encoding='utf-8'))['controller']
    def trip(self,reason):self.state='FAULT';self.fault=reason
    def step(self,s,dt):
        if self.state=='FAULT':return self.outputs()
        try:
            dt=validate_interval(dt)
            s=validate_observation(s,self.state)
        except ObservationError as error:
            self.trip(str(error));return self.outputs()
        fault=check_invariants(self.state,s)
        if fault:self.trip(fault);return self.outputs()
        boundary=capture_stroke()
        if (boundary is None or not math.isfinite(boundary) or not 0<=boundary<=parameters()['carriage_total_stroke']) and (self.state!='IDLE' or s['start']):
            self.trip('geometry_cannot_capture');return self.outputs()
        self.elapsed+=dt
        if self.elapsed>self.spec['simulation_state_timeout_s'] and self.state not in ['IDLE','DONE']:
            self.trip('state_timeout');return self.outputs()
        old=self.state
        arrival_fields={'CLEAR':'slide_clear','AIM':'aim_reached','RETREAT':'slide_clear','HOME':'head_home','LOAD':'slide_home'}
        field=arrival_fields.get(self.state)
        if field:
            if type(s.get(field)) is not bool:self.trip('arrival_feedback_missing_'+field);return self.outputs()
            if s[field] is False:self.arrival_low_seen=True
        arrived=bool(field and self.arrival_low_seen and s[field] is True)
        transitions={
            'IDLE':('GUIDE_DOWN',s.get('start') and s.get('head_home') and s.get('slide_home')),
            'GUIDE_DOWN':('RETAIN',s.get('guide_down')),
            'RETAIN':('DROP',s.get('upper_held') and s.get('gate_closed')),
            'DROP':('GATE_CLOSE',s.get('ball_present') and s.get('gate_open')),
            'GATE_CLOSE':('GRIP',s.get('gate_closed')),
            'GRIP':('GUIDE_UP',s.get('clamp_closed') and s.get('ball_present')),
            'GUIDE_UP':('CLEAR',s.get('guide_up')),
            'CLEAR':('AIM',arrived and s.get('guide_up')),
            'AIM':('RELEASE',arrived and s.get('wheels_ready')),
            'RELEASE':('APPROACH',s.get('clamp_open')),
            'APPROACH':('WAIT_EXIT',s.get('capture_detected') and s.get('clamp_open')),
            'RETREAT':('HOME',arrived and s.get('clamp_open')),
            'HOME':('LOAD',arrived),
            'LOAD':('DONE',arrived),
        }
        if self.state=='WAIT_EXIT':
            if s.get('exit') and not self.last_exit:self.exit_seen=True
            if self.exit_seen and self.last_exit and s['exit'] is False:self.state='RETREAT'
        elif self.state in transitions:
            target,condition=transitions[self.state]
            if condition:self.state=target
        if old=='APPROACH' and self.state=='WAIT_EXIT':
            self.exit_seen=False
            if s.get('exit'):self.trip('exit_high_at_capture')
        if self.state!=old:
            self.elapsed=0
            field=arrival_fields.get(self.state);self.arrival_low_seen=bool(field and s.get(field) is False)
        self.last_exit=bool(s.get('exit',False))
        return self.outputs()
    def outputs(self):
        p=parameters();enabled=self.state not in ['IDLE','DONE','FAULT']
        targets={'CLEAR':p['clear_stroke'],'AIM':p['clear_stroke'],'RELEASE':p['clear_stroke'],
                 'APPROACH':capture_stroke(),'WAIT_EXIT':capture_stroke(),'RETREAT':p['clear_stroke'],'HOME':p['clear_stroke'],'LOAD':0}
        guide_down=self.state in ['GUIDE_DOWN','RETAIN','DROP','GATE_CLOSE','GRIP']
        clamp_closed=self.state in ['GRIP','GUIDE_UP','CLEAR','AIM']
        return dict(state=self.state,fault=self.fault,enable_motion=enabled,
            enable_wheels=enabled and self.state in ['AIM','RELEASE','APPROACH','WAIT_EXIT'],
            slide_target_mm=targets.get(self.state) if enabled else None,
            guide_target_mm=(0 if guide_down else p['guide_stroke']) if enabled else None,
            clamp_target=('closed' if clamp_closed else 'open') if enabled else None,gate_target=('open' if self.state=='DROP' else 'closed') if enabled else None,
            upper_target=('hold' if self.state in ['RETAIN','DROP','GATE_CLOSE'] else 'open') if enabled else None,hardware_connected=False,
            notice='离线合同测试；捕获位置仅理想接触边界，牵引窗口及停止能力待实测')
