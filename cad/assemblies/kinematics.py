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

def permitted(s):
    p=parameters(); guide=s.get('guide',p['guide_stroke']); slide=s.get('slide',0)
    aimed=abs(s.get('yaw',0))+abs(s.get('pitch',0))>1e-8
    if guide < p['guide_stroke']-1e-8 and (slide>0 or aimed): return False
    if aimed and slide < p['clear_stroke']: return False
    boundary=capture_stroke(p)
    if s.get('loaded',True) and (boundary is None or slide>boundary+1e-6):return False
    d=json.loads((ROOT/'data/implementation.json').read_text(encoding='utf-8')) if (ROOT/'data/implementation.json').exists() else {'demo':{'release_complete_x':-25}}
    if slide+p['load_x']>=d['demo']['release_complete_x'] and s.get('clamp',0)<d['demo'].get('clamp_open_mm',14)-1e-8: return False
    return True
