"""Build analytic B-reps, unfused STEP assemblies and CAD-derived tessellations."""
import json,sys,csv,time,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import cadquery as cq
from cad.parts.recipe import build
from cad.assemblies.kinematics import parameters,matrix
import numpy as np

def exact_bbox(s):
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    b=Bnd_Box();BRepBndLib.AddOptimal_s(s.wrapped,b,False,False);return cq.BoundBox(b)

def load_model(data_dir=None):
    data_dir=Path(data_dir) if data_dir else R/'data'
    env={k:v['value'] for k,v in json.loads((data_dir/'design.json').read_text(encoding='utf-8'))['parameters'].items()};env['wheel_center_y']=(env['wheel_diameter']+env['wheel_gap_visual'])/2;env['slide']=0
    for p in json.loads((data_dir/'parts.json').read_text(encoding='utf-8')):
        for axis,value in zip('xyz',p['bbox_mm']):env[p['part_id'].replace('PRT-','P')+'_'+axis]=value
    data=json.loads((data_dir/'geometry.json').read_text(encoding='utf-8'))['instances']
    model=[]
    for item in data:
        try:s=build(item['shape'],env)
        except Exception as e:raise RuntimeError(item['instance_id']) from e
        if not s.isValid() or s.Volume()<=0:raise ValueError('Invalid native solid '+item['instance_id'])
        model.append((item,s))
    return model

def locate(s,parent,state=None):
    from OCP.gp import gp_Trsf
    m=matrix(parent,state);t=gp_Trsf();t.SetValues(*[float(v) for v in m[:3,:].flatten()]);return s.located(cq.Location(t))

def run():
    for d in ['step/parts','step/assemblies','mesh','stl','render','drawings','animation','blend','glb','calibration']:(R/'output'/d).mkdir(parents=True,exist_ok=True)
    model=load_model(); assembly=cq.Assembly(name='BM1_V0_assembly'); groups={}; mains={}; deriv={}; mesh=[]; records=[]
    expl=json.loads((R/'data/exploded.json').read_text(encoding='utf-8')); ev={x['assembly_id']:x['translation_mm'] for x in expl['modules']}
    t0=time.time()
    for index,(i,s) in enumerate(model):
        name=i['instance_id']; placed=locate(s,i['parent']); rgb=tuple(int(i['color'][j:j+2],16)/255 for j in (1,3,5))
        if not i.get('reference'):
            assembly.add(placed,name=name,color=cq.Color(*rgb))
            groups.setdefault(i['assembly_id'],cq.Assembly(name=i['assembly_id'])).add(placed,name=name,color=cq.Color(*rgb))
            mains.setdefault(i['part_id'],[]).append(placed)
            deriv.setdefault(i['derived_id'],[]).append(placed)
        verts,tris=s.tessellate(.18,.15)
        bb=exact_bbox(placed); localbb=exact_bbox(s)
        v=[list(v.toTuple()) for v in verts]
        mesh.append({**{k:val for k,val in i.items() if k!='shape'},'vertices':v,'triangles':tris,'matrix':matrix(i['parent']).tolist(),'explode':ev.get(i['assembly_id'],[0,0,0]),'bounds_mm':[bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax]})
        records.append({**{k:val for k,val in i.items() if k!='shape'},'volume_mm3':s.Volume(),'solid_count':len(s.Solids()),'valid':s.isValid(),'bounds_mm':[bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax],'local_bounds_mm':[localbb.xmin,localbb.ymin,localbb.zmin,localbb.xmax,localbb.ymax,localbb.zmax]})
        # BREP cache speeds exact intersection checks without rebuilding.
        s.exportBrep(str(R/'output/mesh'/f'{name}.brep'))
    assembly.export(str(R/'output/step/BM1_V0_assembly.step'))
    for aid,assy in groups.items():assy.export(str(R/'output/step/assemblies'/f'{aid}.step'))
    for pid,shapes in {**deriv,**mains}.items():
        # Part family STEP preserves all instances at their installation coordinates.
        cq.exporters.export(cq.Compound.makeCompound(shapes),str(R/'output/step/parts'/f'{pid}.step'))
    for pid in ['PRT-0603','PRT-0604','PRT-0701','PRT-0702','PRT-1003']:
        cq.exporters.export(cq.Compound.makeCompound(mains[pid]),str(R/'output/stl'/f'{pid}_FIT_ONLY.stl'),tolerance=.1,angularTolerance=.1)
    (R/'output/mesh/model.json').write_text(json.dumps(mesh,ensure_ascii=False),encoding='utf-8')
    (R/'data/instances.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    (R/'reports/solid_validation.json').write_text(json.dumps(dict(instances=len(records),main_items=len(mains),all_valid=all(x['valid'] for x in records),solids=sum(x['solid_count'] for x in records),native_brep=True,build_seconds=time.time()-t0),indent=2),encoding='utf-8')
    print('Built',len(records),'instances;',len(mains),'main items;',sum(x['solid_count'] for x in records),'solids',flush=True)

if __name__=='__main__':run()
