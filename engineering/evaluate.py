"""Evidence-gated mass/COM and unilateral vertical-spring calculation."""
import json,math,argparse,itertools
from pathlib import Path
import numpy as np
from engineering.evidence_schema import finite_number,validate_numeric_rows,validate_components

def evaluate(rows,supports,gravity=9.80665,*,expected_instances=None,evidence_index=None,allow_partial=False):
    try:
        with np.errstate(over='raise',invalid='raise',divide='raise'):
            return _evaluate(rows,supports,gravity,expected_instances=expected_instances,evidence_index=evidence_index,allow_partial=allow_partial)
    except (OverflowError,FloatingPointError,np.linalg.LinAlgError) as exc:
        raise ValueError('Numerically unsupported mass/support input') from exc

def _evaluate(rows,supports,gravity,*,expected_instances,evidence_index,allow_partial):
    if not finite_number(gravity) or gravity<=0:raise ValueError('gravity must be finite positive')
    if not 3<=len(supports)<=12:raise ValueError('Verified enumeration supports 3..12 supports only')
    for s in supports:
        if not all(finite_number(s.get(k)) for k in ['x_mm','y_mm']):raise ValueError('Invalid support coordinates')
        k=s.get('vertical_stiffness_N_mm')
        if k is not None and (not finite_number(k) or k<=0):raise ValueError('Support stiffness must be finite positive')
    validate_numeric_rows(rows,allow_missing=True)
    missing=[r['instance_id'] for r in rows if r.get('mass_kg') is None or r.get('com_world_mm') is None]
    blocked=dict(status='BLOCKED_MISSING_EVIDENCE',missing_instances=missing,actual_mass_kg=None,actual_com_mm=None,stability_pass=None,support_solution_valid=False)
    if missing or not rows:return blocked
    validate_numeric_rows(rows)
    if expected_instances is not None and evidence_index is not None:
        validate_components(rows,set(expected_instances),evidence_index)
        status='INPUT_EVIDENCE_LINKED'
    elif allow_partial:
        status='PARTIAL_UNVERIFIED_CALCULATION'
    else:
        return {**blocked,'reason':'Expected instance manifest and evidence records required; verified string is insufficient'}
    masses=np.array([r['mass_kg'] for r in rows]);com=np.average([r['com_world_mm'] for r in rows],axis=0,weights=masses)
    result=dict(status=status,actual_mass_kg=float(masses.sum()) if status=='INPUT_EVIDENCE_LINKED' else None,actual_com_mm=com.tolist() if status=='INPUT_EVIDENCE_LINKED' else None,calculated_mass_kg=float(masses.sum()),calculated_com_mm=com.tolist(),stability_pass=None,support_solution_valid=False,notice='Rigid base, static gravity, coplanar unilateral linear springs only; no physical stability acceptance')
    if any(s.get('vertical_stiffness_N_mm') is None for s in supports):result['support_reactions_status']='BLOCKED_MISSING_SUPPORT_STIFFNESS';return result
    A=np.array([[1,s['x_mm'],s['y_mm']] for s in supports],float);K=np.array([s['vertical_stiffness_N_mm'] for s in supports]);W=masses.sum()*gravity
    # Scale coordinates before condition and equilibrium tests, to avoid unit-driven conditioning.
    scale=max(1.,float(np.max(np.abs(A[:,1:]))));B=A.copy();B[:,1:]/=scale
    load=np.array([W,W*com[0]/scale,W*com[1]/scale])
    for size in range(3,len(supports)+1):
        for active in itertools.combinations(range(len(supports)),size):
            active=list(active);M=B[active].T@(K[active,None]*B[active]);condition=np.linalg.cond(M)
            if not np.isfinite(condition) or condition>1e12:continue
            displacement=np.linalg.solve(M,load);deflections=B@displacement
            if not np.all(np.isfinite(displacement)) or not np.all(np.isfinite(deflections)):raise ValueError('Nonfinite support solution')
            forces=np.zeros(len(supports));forces[active]=K[active]*deflections[active]
            inactive=[i for i in range(len(supports)) if i not in active]
            if np.min(forces)<-1e-8 or any(deflections[i]>1e-8 for i in inactive):continue
            forces=np.maximum(forces,0)
            residual=B.T@forces-load
            spring=forces-K*np.maximum(deflections,0)
            complementarity=float(np.max(np.abs(spring)))
            if not np.all(np.isfinite(forces)) or not np.all(np.isfinite(residual)) or not math.isfinite(complementarity):raise ValueError('Nonfinite support residual')
            if np.max(np.abs(residual))>1e-7*max(1.,W) or complementarity>1e-7:continue
            result.update(support_reactions_N=forces.tolist(),support_reactions_status='RIGID_BASE_LINEAR_SPRING_ASSUMPTION',support_solution_valid=True,active_indices=active,all_support_deflections_mm=deflections.tolist(),condition_number=float(condition),complementarity_residual=complementarity,equilibrium_residual_N_Nmm=(A.T@forces-[W,W*com[0],W*com[1]]).tolist())
            return result
    result['support_reactions_status']='NO_VALID_UNILATERAL_SUPPORT_SOLUTION';return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('input');ap.add_argument('--output',default='evaluation.json');ap.add_argument('--allow-partial',action='store_true');args=ap.parse_args()
    spec=json.loads(Path(args.input).read_text(encoding='utf-8'));out=evaluate(spec['components'],spec['supports'],expected_instances=spec.get('expected_instances'),evidence_index=spec.get('evidence_index'),allow_partial=args.allow_partial);Path(args.output).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(out['status'])
