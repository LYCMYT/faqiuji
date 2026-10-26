"""Strict observation and continuous offline interlock contracts."""
import math
from numbers import Real

class ObservationError(ValueError):
    """A sample cannot safely participate in this control tick."""

ARRIVALS={'CLEAR':'slide_clear','AIM':'aim_reached','RETREAT':'slide_clear','HOME':'head_home','LOAD':'slide_home'}
GUIDE_UP={'CLEAR','AIM','RELEASE','APPROACH','WAIT_EXIT','RETREAT','HOME','LOAD'}
GUIDE_DOWN={'RETAIN','DROP','GATE_CLOSE','GRIP'}
GATE_CLOSED={'GRIP','GUIDE_UP',*GUIDE_UP,'DONE'}
KNOWN=set('start cover_closed estop_ok cassette_locked exit capture_detected head_home slide_home slide_clear aim_reached guide_up guide_down gate_closed gate_open clamp_closed clamp_open upper_held ball_present wheels_ready'.split())

def validate_interval(dt: object) -> float:
    if isinstance(dt,bool) or not isinstance(dt,Real) or not math.isfinite(dt) or dt<=0:
        raise ObservationError('invalid_sample_interval')
    return float(dt)

def validate_observation(payload: dict, state: str) -> dict:
    if not isinstance(payload,dict):raise ObservationError('observation_not_mapping')
    required=set('cover_closed estop_ok cassette_locked exit'.split())
    fields={'IDLE':'start head_home slide_home capture_detected','GUIDE_DOWN':'guide_up guide_down','RETAIN':'upper_held gate_closed','DROP':'ball_present gate_open upper_held','GATE_CLOSE':'gate_closed upper_held','GRIP':'clamp_closed ball_present','GUIDE_UP':'guide_up clamp_closed ball_present','AIM':'wheels_ready','RELEASE':'clamp_open capture_detected','APPROACH':'capture_detected clamp_open'}
    required.update(fields.get(state,'').split())
    if state in GUIDE_DOWN:required.add('guide_down')
    if state in GUIDE_UP:required.add('guide_up')
    if state in GATE_CLOSED:required.add('gate_closed')
    if state in {'GUIDE_UP','CLEAR','AIM'}:required.update(['clamp_closed','ball_present'])
    if state in {'APPROACH','WAIT_EXIT','RETREAT'}:required.add('clamp_open')
    if state in {'RELEASE','APPROACH','WAIT_EXIT'}:required.add('wheels_ready')
    if state in ARRIVALS:required.add(ARRIVALS[state])
    for key in sorted(required | (KNOWN & payload.keys())):
        if type(payload.get(key)) is not bool:raise ObservationError(key+'_feedback_missing_or_invalid')
    return dict(payload)

def check_invariants(state: str, observation: dict) -> str | None:
    s=observation
    if not all(s[k] for k in ['cover_closed','estop_ok','cassette_locked']):return 'protective_chain_not_confirmed'
    for a,b in [('guide_up','guide_down'),('gate_open','gate_closed'),('clamp_open','clamp_closed')]:
        if s.get(a) is True and s.get(b) is True:return 'contradictory_'+a
    if state=='IDLE' and s['exit']:return 'exit_sensor_high_before_cycle'
    if state in {'IDLE','RELEASE'} and s['capture_detected']:return 'capture_sensor_high_before_approach'
    checks=[(state in GUIDE_DOWN,'guide_down','guide_down_lost'),(state in GATE_CLOSED,'gate_closed','gate_closed_lost'),(state in GUIDE_UP,'guide_up','guide_up_lost'),(state in {'APPROACH','WAIT_EXIT','RETREAT'},'clamp_open','release_feedback_lost'),(state in {'RELEASE','APPROACH','WAIT_EXIT'},'wheels_ready','wheel_ready_feedback_lost'),(state in {'GUIDE_UP','CLEAR','AIM'},'clamp_closed','held_ball_feedback_lost'),(state in {'GUIDE_UP','CLEAR','AIM'},'ball_present','held_ball_feedback_lost'),(state in {'DROP','GATE_CLOSE'},'upper_held','upper_retention_feedback_lost')]
    for active,key,fault in checks:
        if active and s[key] is not True:return fault
    return None
