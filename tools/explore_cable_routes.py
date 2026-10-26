from pathlib import Path
import sys,json,itertools
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import cadquery as cq
from cad.parts.cable import solid
from cad.export_all import locate
from tools.check_collisions import bbox,overlaps
items=json.loads((R/'data/instances.json').read_text(encoding='utf-8'))
model=[(i,cq.Shape.importBrep(str(R/'output/mesh'/(i['instance_id']+'.brep')))) for i in items if not i.get('reference') and i['instance_id']!='PRT-0704-WIRE_A']
states=[dict(height=h,yaw=y,pitch=p,slide=q,guide=115,clamp=14 if q>=165 else 0) for h,y,p,q in itertools.product([1400,1800],[-45,-25,0,25,45],[-10,0,35,55,60],[105,185])]
posed=[[(i,locate(s,i['parent'],st)) for i,s in model] for st in states]
results=[]
for direction,length,y in itertools.product([1,-1],[280,300],[-130,-145,-165,-190]):
    hits=[];wires={}
    try:
        for si,st in enumerate(states):
            q=st['slide']
            if q not in wires:wires[q]=solid(-235,-245+q,-95,-52,y,length,2,direction)
            w=locate(wires[q],'MOVING_HEAD',st);bb=bbox(w)
            for i,s in posed[si]:
                if overlaps(bb,bbox(s)) and w.intersect(s).Volume()>.01:hits.append(i['instance_id']);break
            if hits:break
        result=dict(direction=direction,length=length,y=y,first_hit=hits,coarse_clear=not hits);results.append(result);print(result,flush=True)
    except Exception as e:print(str(e),flush=True)
(R/'reports/cable_route_exploration.json').write_text(json.dumps(results,indent=2))
