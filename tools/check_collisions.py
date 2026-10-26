"""Broad phase AABB -> exact OCCT common volume. No implicit pair exemptions.
Static assembly and selected kinematic state grid; numerical results explicitly
do not claim continuous motion or manufacturing tolerance certification.
"""
import sys,json,itertools,time,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import cadquery as cq
import numpy as np
from cad.export_all import locate
from cad.assemblies.kinematics import parameters,matrix,capture_stroke
from cad.parts.recipe import build

def bbox(s):
    b=s.BoundingBox();return (b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax)
def overlaps(a,b):return all(min(a[k+3],b[k+3])-max(a[k],b[k])>.001 for k in range(3))
def annotate_capture_states(states,capture):
    for state in states:
        state['capture_geometry_supported']=capture is not None
        state['loaded']=capture is None or state.get('slide',0)<=capture+1e-6
    return states
def run(mode='static'):
    items=json.loads((R/'data/instances.json').read_text(encoding='utf-8'))
    model=[(i,cq.Shape.importBrep(str(R/'output/mesh'/(i['instance_id']+'.brep')))) for i in items]
    recipes={i['instance_id']:i['shape'] for i in json.loads((R/'data/geometry.json').read_text(encoding='utf-8'))['instances']}
    allowed=json.loads((R/'data/contact_pairs.json').read_text(encoding='utf-8')) if (R/'data/contact_pairs.json').exists() else []
    whitelist={tuple(sorted(x['pair'])):x for x in allowed if x.get('type') in ['mounting_overlap_concept','elastic_contact','shaft_fit','guide_fit']}
    if mode=='static':states=[dict(height=h,guide=115,slide=0,clamp=0) for h in [1400,1500,1800]]
    elif mode=='motion':
        states=[dict(height=1500,yaw=y,pitch=p,guide=115,slide=105,clamp=0) for y in range(-45,46,5) for p in range(-10,61,5)]
        states += [dict(height=1500,yaw=0,pitch=0,guide=g,slide=0,clamp=0) for g in list(range(0,116,2))+[115]]
        states += [dict(height=1500,yaw=0,pitch=0,guide=115,slide=q,clamp=14 if q>=165 else 0) for q in list(range(0,186,2))+[185]]
        states += [dict(height=h,yaw=y,pitch=p,guide=115,slide=105,clamp=0) for h in [1400,1800] for y in [-45,-35,35,45] for p in [-10,0,55,60]]
        # Feeding after aiming, including the actual demo pose and combined extrema.
        states += [dict(height=1500,yaw=y,pitch=p,guide=115,slide=q,clamp=min(14,max(0,(q-145)*14/20))) for y,p in [(25,35),(-35,55),(35,55),(-45,60),(45,60)] for q in list(range(105,186,2))+[185]]
        # Separator motion and the full falling reference envelope, zero head angles.
        states += [dict(height=1500,guide=0,slide=0,clamp=14,fall=300,upper=0,gate=q) for q in list(range(0,86,2))+[85]]
        states += [dict(height=1500,guide=0,slide=0,clamp=14,fall=300,upper=q,gate=0) for q in range(0,25,2)]
        states += [dict(height=1500,guide=0,slide=0,clamp=14,fall=q,upper=0,gate=85) for q in range(0,301,2)]
    else:raise ValueError(mode)
    capture=capture_stroke()
    annotate_capture_states(states,capture)
    if mode=='motion' and capture is not None:
        # Refine the contact approach. Above-boundary travel is empty carriage only.
        states += [dict(height=1500,guide=115,slide=float(q),yaw=25,pitch=35,clamp=14,loaded=True) for q in np.arange(165,capture,.25)]
        frozen=dict(height=1500,guide=115,slide=capture,yaw=25,pitch=35,clamp=14)
        states += [dict(height=1500,guide=115,slide=float(q),yaw=25,pitch=35,clamp=14,loaded=True,reference_frozen_at=frozen) for q in np.linspace(capture,105,39)]
    hits={};tests=0;start=time.time();errors=[];wire_cache={};intersection_cache={}
    rigid_groups={'WHEEL_LEFT':'MOVING_HEAD','WHEEL_RIGHT':'MOVING_HEAD'}
    for si,state in enumerate(states):
        transforms={i['parent']:matrix(i['parent'],state) for i,s in model};relative_keys={}
        posed=[]
        for i,s in model:
            if i.get('reference') and state.get('loaded') is False:continue
            if i.get('dynamic_height') or i.get('dynamic_slide'):
                key=(i['instance_id'],state['height'] if i.get('dynamic_height') else 0,state.get('slide',0) if i.get('dynamic_slide') else 0)
                if key not in wire_cache:
                    env={**parameters(),'head_axis_height':state['height'],'slide':state.get('slide',0)};wire_cache[key]=build(recipes[i['instance_id']],env)
                s=wire_cache[key]
            if i.get('reference'):
                s=s.translate((0,0,state.get('fall',0)))
            pose=state.get('reference_frozen_at',state) if i.get('reference') else state
            posed.append((i,locate(s,i['parent'],pose)))
        bbs=[bbox(s) for i,s in posed]
        for a in range(len(posed)):
            i,s=posed[a]
            for b in range(a):
                j,t=posed[b]
                if mode=='motion' and rigid_groups.get(i['parent'],i['parent'])==rigid_groups.get(j['parent'],j['parent']) and not any(x.get('dynamic_height') or x.get('dynamic_slide') or x.get('reference') for x in [i,j]):continue # rigidly invariant pairs checked statically
                if not overlaps(bbs[a],bbs[b]):continue
                # Elastic cork/wheel contact only in capture window, never blanket exemption.
                pair=tuple(sorted([i['instance_id'],j['instance_id']]))
                tests+=1
                frames=(i['parent'],j['parent'])
                if frames not in relative_keys:relative_keys[frames]=tuple(np.round((np.linalg.inv(transforms[frames[0]])@transforms[frames[1]]).flatten(),6))
                extra=tuple((state.get('slide',0) if x.get('dynamic_slide') or x.get('reference') else 0,state.get('height',1500) if x.get('dynamic_height') else 0,state.get('fall',0) if x.get('reference') else 0) for x in [i,j])
                reference_state=repr(sorted(state.items())) if i.get('reference') or j.get('reference') else None
                cache_key=(pair,relative_keys[frames],extra,reference_state)
                try:
                    if cache_key not in intersection_cache:intersection_cache[cache_key]=s.intersect(t).Volume()
                    vol=intersection_cache[cache_key]
                except Exception as e:errors.append(dict(pair=pair,state=state,error=str(e)));continue
                if vol>.01:
                    classification=whitelist.get(pair,{}).get('type','unresolved_hard_intersection')
                    if set([i['part_id'],j['part_id']])==set(['PRT-0505','PRT-REF-CORK']) and state.get('slide',0)>=178:
                        classification='elastic_contact_pending_test'
                    if pair not in hits:hits[pair]=dict(pair=pair,max_volume_mm3=vol,first_state=state,samples=1,classification=classification)
                    else:hits[pair]['max_volume_mm3']=max(vol,hits[pair]['max_volume_mm3']);hits[pair]['samples']+=1
        if si%20==0:print(mode,si,'/',len(states),'pairs',len(hits),'elapsed',round(time.time()-start),flush=True)
    result=dict(mode=mode,geometry_sha256=hashlib.sha256((R/'data/geometry.json').read_bytes()).hexdigest(),states=len(states),pair_evaluations=tests,exact_intersections=len(intersection_cache),errors=errors,linear_step_mm=2,capture_step_mm=.25,angular_step_deg=5,volume_threshold_mm3=.01,tolerance_mm=.001,continuous_proof=False,post_capture_dynamic_validated=False,capture_stroke_mm=capture,empty_travel_states=sum(s.get('loaded') is False for s in states),frozen_marker_retreat_states=sum('reference_frozen_at' in s for s in states),scope='R1: loaded stops at first ideal contact; full 185mm travel checked empty; conservative frozen world marker during retreat; no flight simulation',results=list(hits.values()),unresolved_pairs=sum(x['classification']=='unresolved_hard_intersection' for x in hits.values()),indeterminate_pairs=sum('UNVALIDATED' in x['classification'] for x in hits.values()),seconds=time.time()-start)
    (R/'reports'/f'collisions_{mode}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print('RESULT',mode,result['unresolved_pairs'],'unresolved pairs')
if __name__=='__main__':run(sys.argv[1] if len(sys.argv)>1 else 'static')
