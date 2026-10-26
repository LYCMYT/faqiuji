import json,sys,shutil,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import cadquery as cq
from cad.export_all import load_model,locate
before=hashlib.sha256((R/'data/design.json').read_bytes()).hexdigest();baseline=load_model();results=[]
for name,value in [('wheel_gap_visual',30),('tube_cap_allowance',24)]:
    folder=R/'output/verification_variants'/name;dd=folder/'data';dd.mkdir(parents=True,exist_ok=True)
    for fn in ['design.json','parts.json','geometry.json']:shutil.copyfile(R/'data'/fn,dd/fn)
    p=json.loads((dd/'design.json').read_text(encoding='utf-8'));old=p['parameters'][name]['value'];p['parameters'][name]['value']=value;(dd/'design.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
    variant=load_model(dd);assy=cq.Assembly(name='BM1_parameter_rebuild_'+name);count=0
    for i,s in variant:
        assert s.isValid() and s.Volume()>0
        if i.get('reference'):continue
        assy.add(locate(s,i['parent']),name=i['instance_id']);count+=len(s.Solids())
    f=folder/'assembly.step';assy.export(str(f));back=cq.importers.importStep(str(f)).val();assert back.isValid() and len(back.Solids())==count
    results.append(dict(parameter=name,from_value=old,to_value=value,all_instances_rebuilt=len(variant),step_reopened_solids=count,passed=True,source_data=str(dd.relative_to(R))))
restored=load_model();assert len(restored)==len(baseline)
for (i,a),(j,b) in zip(restored,baseline):assert i['instance_id']==j['instance_id'] and abs(a.Volume()-b.Volume())<1e-6 and (a.Center()-b.Center()).Length<1e-6
assert hashlib.sha256((R/'data/design.json').read_bytes()).hexdigest()==before
(R/'reports/parameter_full_rebuild.json').write_text(json.dumps(dict(variants=results,baseline_regenerated_and_identical=True,baseline_data_untouched=True),ensure_ascii=False,indent=2),encoding='utf-8');print('FULL PARAMETER REBUILD PASSED',len(restored),'instances x 3')
