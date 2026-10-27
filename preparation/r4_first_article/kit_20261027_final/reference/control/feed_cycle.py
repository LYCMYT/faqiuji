"""Offline feedback-contract simulator. No GPIO, network, motor or safety outputs.

Boolean inputs represent observations, not time-based assumptions. Hardware
debounce, wiring categories, stopping time and watchdog integration are NOT certified.
"""
from pathlib import Path
import json,math
from uuid import uuid4
from control.commands import Command,CommandLifecycle
from control.contracts import ObservationError,validate_interval,validate_observation,check_invariants
from cad.assemblies.kinematics import capture_stroke,parameters
R=Path(__file__).resolve().parents[1]

class FeedCycle:
    def __init__(self):
        self.state='IDLE';self.elapsed=0.;self.last_exit=False;self.exit_seen=False;self.fault=None
        self.arrival_low_seen=False
        self.cycle_id=uuid4().hex;self.command_counter=0;self.clock=0.;self.commands=CommandLifecycle();self.armed=False
        self.spec=json.loads((R/'data/r1_engineering.json').read_text(encoding='utf-8'))['controller']
    def trip(self,reason):
        self.state='FAULT';self.fault=reason;self.armed=False;self.commands=CommandLifecycle()
    def pause(self):
        if self.state!='FAULT':self.state='PAUSED';self.armed=False;self.commands=CommandLifecycle()
        return self.outputs()
    def reset(self):
        if self.state not in {'FAULT','PAUSED','DONE'}:raise ValueError('reset_requires_stopped_state')
        self.state='IDLE';self.fault=None;self.elapsed=0.;self.armed=False;self.last_exit=False;self.exit_seen=False;self.commands=CommandLifecycle()
        return self.outputs()
    def restart(self):
        if self.state!='IDLE':raise ValueError('restart_requires_idle_reset')
        self.cycle_id=uuid4().hex;self.commands=CommandLifecycle();self.armed=True
        return self.outputs()
    def _issue(self):
        targets={'CLEAR':('slide',parameters()['clear_stroke']),'AIM':('head',0.),'RETREAT':('slide',parameters()['clear_stroke']),'HOME':('head',0.),'LOAD':('slide',0.)}
        if self.state in targets:
            action,target=targets[self.state];self.command_counter+=1
            self.commands.issue(Command(self.cycle_id+':'+str(self.command_counter),self.cycle_id,action,target,self.clock))
    def step(self,s,dt,*,ack=None):
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
        if self.state=='PAUSED':return self.outputs()
        next_clock=self.clock+dt
        next_elapsed=self.elapsed+dt
        if not math.isfinite(next_clock) or not math.isfinite(next_elapsed):
            self.trip('simulation_clock_overflow');return self.outputs()
        self.clock=next_clock
        self.elapsed=next_elapsed
        if self.elapsed>self.spec['simulation_state_timeout_s'] and self.state not in ['IDLE','DONE']:
            self.trip('state_timeout');return self.outputs()
        old=self.state
        arrival_fields={'CLEAR':'slide_clear','AIM':'aim_reached','RETREAT':'slide_clear','HOME':'head_home','LOAD':'slide_home'}
        field=arrival_fields.get(self.state)
        if field and self.commands.command is None:self._issue()
        completed=self.commands.observe(ack) if field else False
        arrived=bool(field and s[field] is True and completed)
        transitions={
            'IDLE':('GUIDE_DOWN',self.armed and s.get('start') and s.get('head_home') and s.get('slide_home')),
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
            if condition:
                # RELEASE opens the clamp immediately: validate its entry sample
                # before committing the transition or exposing its action targets.
                if target=='RELEASE':
                    try:
                        validate_observation(s,target)
                    except ObservationError as error:
                        self.trip(str(error));return self.outputs()
                    fault=check_invariants(target,s)
                    if fault:self.trip(fault);return self.outputs()
                self.state=target
        if old=='APPROACH' and self.state=='WAIT_EXIT':
            self.exit_seen=False
            if s.get('exit'):self.trip('exit_high_at_capture')
        if self.state!=old:
            self.elapsed=0
            self.commands=CommandLifecycle()
            self._issue()
            if self.state=='DONE':self.armed=False
        self.last_exit=bool(s.get('exit',False))
        return self.outputs()
    def outputs(self):
        p=parameters();enabled=self.state not in ['IDLE','DONE','FAULT','PAUSED']
        targets={'CLEAR':p['clear_stroke'],'AIM':p['clear_stroke'],'RELEASE':p['clear_stroke'],
                 'APPROACH':capture_stroke(),'WAIT_EXIT':capture_stroke(),'RETREAT':p['clear_stroke'],'HOME':p['clear_stroke'],'LOAD':0}
        guide_down=self.state in ['GUIDE_DOWN','RETAIN','DROP','GATE_CLOSE','GRIP']
        clamp_closed=self.state in ['GRIP','GUIDE_UP','CLEAR','AIM']
        return dict(state=self.state,fault=self.fault,command=self.commands.output(),cycle_id=self.cycle_id,
            safe_intent=({'upper':'hold_remaining_stack','gate':'controlled_close','guide':'hold_position','slide':'controlled_stop_then_hold','catch_clamp':'hold_current_state','future_wheels':'controlled_deceleration'} if not enabled else None),
            safe_intent_status='BLOCKED_hardware_capability_unconfirmed',enable_motion=enabled,
            enable_wheels=enabled and self.state in ['AIM','RELEASE','APPROACH','WAIT_EXIT'],
            slide_target_mm=targets.get(self.state) if enabled else None,
            guide_target_mm=(0 if guide_down else p['guide_stroke']) if enabled else None,
            clamp_target=('closed' if clamp_closed else 'open') if enabled else None,gate_target=('open' if self.state=='DROP' else 'closed') if enabled else None,
            upper_target=('hold' if self.state in ['RETAIN','DROP','GATE_CLOSE'] else 'open') if enabled else None,hardware_connected=False,
            notice='离线合同测试；捕获位置仅理想接触边界，牵引窗口及停止能力待实测')
