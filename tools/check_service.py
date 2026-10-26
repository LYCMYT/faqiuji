import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
if sys.flags.optimize: raise RuntimeError('Optimized Python unsupported for assertion-based CAD validation')
import sys; sys.path.insert(0,str(R))
from tools.input_manifest import generated_path, metadata_path
import cadquery as cq
from cad.export_all import locate
from tools.check_collisions import bbox,overlaps
rows=json.loads(metadata_path(R,'instances.json').read_text(encoding='utf-8'))
model=[(i,locate(cq.Shape.importBrep(str(R/'output/mesh'/(i['instance_id']+'.brep'))),i['parent'])) for i in rows if not i.get('reference')]
cases=[dict(id='SERVICE_TUBE',targets=['PRT-0601'],removed_parts=['PRT-0603','PRT-0604','PRT-0605','PRT-0606','PRT-0607'],removed_instances=['PRT-0602-E__410','PRT-0602-E__600','PRT-0602-G'],delta=[-240,0,0],prerequisite='先卸分球动作模块与导套/导轨，再卸后压带和后板；这不是已验证的快速补球操作。'),dict(id='SERVICE_WHEEL',targets=['PRT-0504','PRT-0505'],removed_parts=['PRT-0801','PRT-0802'],removed_instances=[],delta=[0,0,130],prerequisite='停机并确认停转，拆开上罩，解除轴向锁紧后上提轮组。'),dict(id='SERVICE_ELECTRICAL',targets=['PRT-0902'],removed_parts=[],removed_instances=['PRT-0803-B'],delta=[-500,0,0],prerequisite='先隔离电源、解除接线、拆后门，再移出电源候选包络。')]
for case in cases:
    if case['id']=='SERVICE_TUBE':case['removed_instances'] += ['PRT-0905__SEN-01','PRT-0905__SEN-12','PRT-0905__SEN-12_HOLD'];case['prerequisite']+='同时解除随模块的上位/分球反馈传感头。'
    moving=[(i,s) for i,s in model if i['part_id'] in case['targets']];rest=[(i,s,bbox(s)) for i,s in model if i['part_id'] not in case['targets']+case['removed_parts'] and i['instance_id'] not in case['removed_instances']];hits={}
    for q in range(0,101,2):
        for i,s in moving:
            sh=s.translate(tuple(q/100*v for v in case['delta']));bb=bbox(sh)
            for j,t,b in rest:
                if overlaps(bb,b):
                    v=sh.intersect(t).Volume()
                    if v>.01:hits[(i['instance_id'],j['instance_id'])]=max(v,hits.get((i['instance_id'],j['instance_id']),0))
    case['checks']=51;case['max_step_mm']=max(abs(x) for x in case['delta'])/50;case['collisions']=[dict(pair=k,volume_mm3=v) for k,v in hits.items()];case['geometric_path_passed']=not hits
    print(case['id'],case['geometric_path_passed'],case['collisions'],flush=True)
(R/'reports/service_validation.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf-8')
