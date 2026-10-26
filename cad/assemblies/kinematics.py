"""The single mm/Z-up kinematic transform implementation.

Functional ASM groups do not dictate movement. Geometry lives in H coordinates
except WORLD_STATIC. Pitch is about local -Y, then yaw about +Z, then height.
"""
import json, math
from pathlib import Path
import numpy as np
from functools import lru_cache
ROOT=Path(__file__).resolve().parents[2]

@lru_cache(maxsize=1)
def parameters():
    p={k:v['value'] for k,v in json.loads((ROOT/'data/design.json').read_text(encoding='utf-8'))['parameters'].items()}
    p['wheel_center_y']=(p['wheel_diameter']+p['wheel_gap_visual'])/2
    return p

def matrix(parent,state=None):
    p=parameters(); s={'height':p['head_axis_height'],'pitch':0,'yaw':0,'slide':0,'guide':p['guide_stroke'],'clamp':0,'gate':0,'upper':0,**(state or {})}
    M=np.eye(4)
    if parent=='WORLD_STATIC': return M
    M[2,3]=s['height']
    if parent in ('YAW_CARRIER','MOVING_HEAD','CARRIAGE','CLAMP_L','CLAMP_R','WHEEL_LEFT','WHEEL_RIGHT'):
        a=math.radians(s['yaw']); R=np.eye(4); R[:2,:2]=[[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]]; M=M@R
    if parent in ('MOVING_HEAD','CARRIAGE','CLAMP_L','CLAMP_R','WHEEL_LEFT','WHEEL_RIGHT'):
        a=-math.radians(s['pitch']); R=np.eye(4); R[0,0]=R[2,2]=math.cos(a); R[0,2]=math.sin(a); R[2,0]=-math.sin(a); M=M@R
    T=np.eye(4)
    if parent in ('CARRIAGE','CLAMP_L','CLAMP_R'): T[0,3]=s['slide']
    if parent in ('CLAMP_L','CLAMP_R'): T[1,3]=s['clamp']*(1 if parent=='CLAMP_L' else -1)
    if parent=='GUIDE_SLEEVE': T[2,3]=s['guide']
    if parent=='LOWER_GATE': T[0,3]=-s['gate']
    if parent in ('UPPER_L','UPPER_R'): T[1,3]=s['upper']*(1 if parent=='UPPER_L' else -1)
    if parent in ('CASSETTE_PIN_L','CASSETTE_PIN_R'):T[1,3]=s.get('pin_withdraw',0)*(1 if parent.endswith('_L') else -1)
    return M@T

def point(xyz,parent,state=None): return (matrix(parent,state)@np.r_[xyz,1])[:3]

def capture_stroke(p=None):
    """First ideal rigid cork/rim tangency, NOT a proven traction position."""
    p=p or parameters();radius=(p['wheel_diameter']+p['cork_diameter_visual'])/2
    half=(p['wheel_diameter']+p['wheel_gap_visual'])/2
    if radius<=half: return None # this geometry cannot capture the cork
    return -math.sqrt(radius*radius-half*half)-p['load_x']

def motion_limits(mode='work'):
    """Concept design bounds; service angles require explicit selection."""
    if mode not in ('work','service'):raise ValueError('unknown motion mode')
    p=parameters(); suffix='work' if mode=='work' else 'check'
    d=json.loads((ROOT/'data/implementation.json').read_text(encoding='utf-8'))['demo']
    return dict(height=(p['head_height_min'],p['head_height_max']),pitch=(p['pitch_min_'+suffix],p['pitch_max_'+suffix]),yaw=(p['yaw_min_'+suffix],p['yaw_max_'+suffix]),slide=(0,p['carriage_total_stroke']),guide=(0,p['guide_stroke']),clamp=(0,d['clamp_open_mm']),gate=(0,d['gate_open_mm']),upper=(0,d['upper_open_mm']))


def validate_motion_state(state: dict, limits: dict) -> list[str]:
    """Layered data, absolute limits, ideal reachability and relative checks."""
    from numbers import Real
    if not isinstance(state,dict):return ['data:state_not_mapping']
    p=parameters();s=dict(height=p['head_axis_height'],pitch=0,yaw=0,slide=0,guide=p['guide_stroke'],clamp=0,gate=0,upper=0,loaded=True);s.update(state)
    errors=[]
    for axis in limits:
        value=s.get(axis)
        if isinstance(value,bool) or not isinstance(value,Real) or not math.isfinite(value):errors.append('data:'+axis+'_not_finite_real')
    if type(s['loaded']) is not bool:errors.append('data:loaded_not_bool')
    if errors:return errors
    for axis,(lo,hi) in limits.items():
        if not lo<=s[axis]<=hi:errors.append('limit:'+axis+'_out_of_range')
    boundary=capture_stroke(p)
    if boundary is None or not math.isfinite(boundary) or not limits['slide'][0]<=boundary<=limits['slide'][1]:errors.append('reachability:capture_outside_slide_range')
    elif s['loaded'] and s['slide']>boundary+1e-6:errors.append('reachability:loaded_capture_overrun')
    aimed=abs(s['yaw'])+abs(s['pitch'])>1e-8
    if s['guide']<p['guide_stroke']-1e-8 and (s['slide']>0 or aimed):errors.append('interlock:guide_not_retracted')
    if aimed and s['slide']<p['clear_stroke']:errors.append('interlock:head_not_clear')
    d=json.loads((ROOT/'data/implementation.json').read_text(encoding='utf-8'))['demo']
    if s['slide']+p['load_x']>=d['release_complete_x'] and s['clamp']<d['clamp_open_mm']-1e-8:errors.append('interlock:clamp_not_released')
    return errors


def permitted(s, mode='work'):
    return not validate_motion_state(s,motion_limits(mode))
