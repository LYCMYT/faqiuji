"""Actual pin withdrawal then full-cassette rear extraction; no hidden obstructions."""
from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
if sys.flags.optimize: raise RuntimeError('Optimized Python unsupported for assertion-based CAD validation')
import sys; sys.path.insert(0,str(R))
from tools.input_manifest import generated_path, metadata_path
import cadquery as cq
from cad.export_all import locate
from cad.assemblies.posing import pose_shape
from tools.check_collisions import bbox,overlaps
spec=json.loads((R/'data/r1_service.json').read_text(encoding='utf-8'))
rows=json.loads(metadata_path(R,'instances.json').read_text(encoding='utf-8'))
model=[(i,cq.Shape.importBrep(str(R/'output/mesh'/(i['instance_id']+'.brep')))) for i in rows if not i.get('reference')]
recipes={i['instance_id']:i['shape'] for i in json.loads((R/'data/geometry.json').read_text(encoding='utf-8'))['instances']}
state=spec['service_state'];pins=set(spec['pin_instances']);parts=set(spec['cassette_parts']);ids=set(spec['cassette_instances'])
static_shapes={i['instance_id']:pose_shape(i,s,state,recipes[i['instance_id']]) for i,s in model if i['instance_id'] not in pins}
def is_cassette(i):return i['part_id'] in parts or i['instance_id'] in ids
cases=[]
for name,travel in [('PIN_WITHDRAW',spec['pin_withdraw_mm']),('CASSETTE_EXTRACT',spec['extract_mm'])]:
    hits={};samples=list(range(0,travel+1,spec['step_mm']))
    if samples[-1]!=travel:samples.append(travel)
    for q in samples:
        posed=[]
        for i,s in model:
            st={**state,'pin_withdraw':q if name=='PIN_WITHDRAW' else spec['pin_withdraw_mm']}
            sh=locate(s,i['parent'],st) if i['instance_id'] in pins else static_shapes[i['instance_id']]
            moving=i['instance_id'] in pins if name=='PIN_WITHDRAW' else is_cassette(i)
            if name=='CASSETTE_EXTRACT' and moving:sh=sh.translate((-q,0,0))
            posed.append((i,sh,bbox(sh),moving))
        for i,s,bb,moving in posed:
            if not moving:continue
            for j,t,b,other_moving in posed:
                if other_moving or not overlaps(bb,b):continue
                v=s.intersect(t).Volume()
                if v>.01:
                    pair=(i['instance_id'],j['instance_id'])
                    if pair not in hits:hits[pair]=dict(pair=pair,first_travel_mm=q,max_volume_mm3=v)
                    else:hits[pair]['max_volume_mm3']=max(v,hits[pair]['max_volume_mm3'])
    result=dict(id=name,samples=len(samples),travel_mm=travel,step_mm=spec['step_mm'],collisions=list(hits.values()),geometric_path_passed=not hits)
    cases.append(result);print(name,result,flush=True)
(R/'reports/r1_service_validation.json').write_text(json.dumps(dict(geometry_sha256=hashlib.sha256((R/'data/geometry.json').read_bytes()).hexdigest(),cases=cases,prerequisites=spec['prerequisites'],all_paths_passed=all(c['geometric_path_passed'] for c in cases),tool_operation_and_load_rating_verified=False),ensure_ascii=False,indent=2),encoding='utf-8')
