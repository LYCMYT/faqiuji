"""Actual OCCT half-space section, including capped cut faces."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import cadquery as cq
from cad.export_all import locate
items=json.loads((R/'data/instances.json').read_text(encoding='utf-8'));out=[];assy=cq.Assembly(name='BM1_Y0_section')
half=cq.Workplane().box(2000,1000,3000).translate((0,-500,1500)).val()
for i in items:
    if i['parent']=='WORLD_STATIC' or i.get('cover') or i['part_id']=='PRT-0202':continue
    s=cq.Shape.importBrep(str(R/'output/mesh'/(i['instance_id']+'.brep')));s=locate(s,i['parent']).intersect(half)
    if s.Volume()<.001:continue
    assy.add(s,name=i['instance_id']);v,t=s.tessellate(.18,.15)
    out.append({**i,'vertices':[list(a.toTuple()) for a in v],'triangles':t,'parent':'WORLD_STATIC','explode':[0,0,0]})
assy.export(str(R/'output/step/BM1_Y0_section.step'))
(R/'output/mesh/section.json').write_text(json.dumps(out,ensure_ascii=False),encoding='utf-8')
print('True section',len(out),'objects')
