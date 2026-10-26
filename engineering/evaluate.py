"""Evidence-gated mass/COM and rigid-base vertical-spring support calculation."""
import json,math,argparse
from pathlib import Path
import numpy as np

def evaluate(rows,supports,gravity=9.80665):
    if not isinstance(gravity,(float,int)) or isinstance(gravity,bool) or not math.isfinite(gravity) or gravity<=0:raise ValueError('gravity must be finite and positive')
    if len(supports)<3:raise ValueError('At least three support points required')
    for s in supports:
        if not all(isinstance(s.get(k),(float,int)) and not isinstance(s[k],bool) and math.isfinite(s[k]) for k in ['x_mm','y_mm']):raise ValueError('Invalid support coordinates')
        k=s.get('vertical_stiffness_N_mm')
        if k is not None and (not isinstance(k,(float,int)) or isinstance(k,bool) or not math.isfinite(k) or k<=0):raise ValueError('Support stiffness must be finite and positive')
    missing=[r['instance_id'] for r in rows if r.get('mass_kg') is None or r.get('com_world_mm') is None or r.get('evidence_status')!='measured_or_supplier_verified']
    if missing:return dict(status='BLOCKED_MISSING_EVIDENCE',missing_instances=missing,actual_mass_kg=None,actual_com_mm=None,stability_pass=None)
    if not rows or any(r['mass_kg']<=0 or len(r['com_world_mm'])!=3 or not all(math.isfinite(v) for v in [r['mass_kg'],*r['com_world_mm']]) for r in rows):raise ValueError('Invalid mass/COM data')
    masses=np.array([r['mass_kg'] for r in rows]);com=np.average([r['com_world_mm'] for r in rows],axis=0,weights=masses)
    result=dict(status='INPUT_EVIDENCE_PRESENT',actual_mass_kg=float(masses.sum()),actual_com_mm=com.tolist(),stability_pass=None,notice='仅指定姿态静态重力；未包含冲击、风、地面倾斜、结构变形或动态停止')
    if any(s.get('vertical_stiffness_N_mm') is None for s in supports):result['support_reactions_status']='BLOCKED_MISSING_SUPPORT_STIFFNESS';return result
    active=list(range(len(supports)));forces=np.zeros(len(supports));W=masses.sum()*gravity
    for _ in supports:
        A=np.array([[1,supports[i]['x_mm'],supports[i]['y_mm']] for i in active],float);K=np.diag([supports[i]['vertical_stiffness_N_mm'] for i in active])
        if len(active)<3 or np.linalg.matrix_rank(A)<3:result['support_reactions_status']='NO_STABLE_ACTIVE_SUPPORT_SET';return result
        displacement=np.linalg.solve(A.T@K@A,[W,W*com[0],W*com[1]]);f=K@A@displacement
        if np.all(f>=-1e-8):forces[active]=f;break
        active.pop(int(np.argmin(f)))
    result['support_reactions_N']=forces.tolist();result['support_reactions_status']='RIGID_BASE_LINEAR_SPRING_ASSUMPTION';result['equilibrium_residual_N_Nmm']=(np.array([[1,s['x_mm'],s['y_mm']] for s in supports]).T@forces-[W,W*com[0],W*com[1]]).tolist()
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('--output',default='evaluation.json');args=ap.parse_args()
    spec=json.loads(Path(args.input).read_text(encoding='utf-8'));out=evaluate(spec['components'],spec['supports']);Path(args.output).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(out['status'])
