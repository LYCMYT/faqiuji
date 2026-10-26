import json,copy
from pathlib import Path
R=Path(__file__).resolve().parents[1];path=R/'data/geometry.json';g=json.loads(path.read_text(encoding='utf-8'));d={i['instance_id']:i for i in g['instances']}
for base,suffix,name,pos in [('SEN-08','R','偏航右限位功能占位',[-65,100,-278]),('SEN-10','DOWN','俯仰下限位功能占位',[-45,200,-75]),('SEN-12','HOLD','留球夹反馈功能占位',[-270,-45,450])]:
    iid='PRT-0905__'+base+'_'+suffix
    if iid not in d:
        i=copy.deepcopy(d['PRT-0905__'+base]);i.update(instance_id=iid,name=name);i['shape']['at']=pos;g['instances'].append(i)
d['PRT-0905__SEN-08']['name']='偏航左限位功能占位';d['PRT-0905__SEN-10']['name']='俯仰上限位功能占位';d['PRT-0905__SEN-12']['name']='下闸反馈功能占位'
path.write_text(json.dumps(g,ensure_ascii=False,indent=2),encoding='utf-8')
p=R/'data/sensor_schedule.json';schedule=json.loads(p.read_text(encoding='utf-8'))
for s in schedule:s['model_instances']=[i['instance_id'] for i in g['instances'] if i.get('sensor_function')==s['instance_id']]
p.write_text(json.dumps(schedule,ensure_ascii=False,indent=2),encoding='utf-8')
with (R/'reports/design_changes.md').open('a',encoding='utf-8') as f:f.write('\n传感功能位置补齐：偏航左右限位、俯仰上下限位、留球夹/下闸反馈分别展开，合计17个功能探头候选位置；PRT-0905采购数量仍为null，不把位置数视为最终器件数。\n')
