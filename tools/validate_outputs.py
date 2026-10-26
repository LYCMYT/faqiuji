import json,sys,time,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
if sys.flags.optimize: raise RuntimeError('Optimized Python unsupported for assertion-based CAD validation')
import sys; sys.path.insert(0,str(R))
from tools.input_manifest import generated_path, metadata_path
import cadquery as cq
from cad.export_all import load_model
from cad.parts.recipe import build
from cad.assemblies.kinematics import parameters

def run():
    start=time.time();files=[];fail=[]
    source=json.loads((R/'data/geometry.json').read_text(encoding='utf-8'))['instances']
    physical=[x for x in source if not x.get('reference')]
    expected={'output/step/BM1_V0_assembly.step','output/step/BM1_Y0_section.step'}
    expected|={'output/step/parts/'+x[key]+'.step' for x in physical for key in ['part_id','derived_id']}
    expected|={'output/step/assemblies/'+x['assembly_id']+'.step' for x in physical}
    missing=sorted(name for name in expected if not (R/name).is_file())
    if missing:raise RuntimeError('Missing expected STEP set: '+str(missing))
    for f in sorted((R/'output/step').rglob('*.step')):
        try:
            s=cq.importers.importStep(str(f)).val();solids=s.Solids();ok=s.isValid() and len(solids)>0 and all(t.Volume()>0 for t in solids)
            files.append(dict(path=str(f.relative_to(R)),valid=ok,solids=len(solids),volume_mm3=s.Volume()))
            if not ok:fail.append(str(f))
        except Exception as e:fail.append([str(f),str(e)])
    p=parameters();env=dict(p,slide=0)
    for item in json.loads((R/'data/parts.json').read_text(encoding='utf-8')):
        for a,v in zip('xyz',item['bbox_mm']):env[item['part_id'].replace('PRT-','P')+'_'+a]=v
    g=json.loads((R/'data/geometry.json').read_text(encoding='utf-8'))['instances'];d={i['instance_id']:i for i in g}
    # No edit to baseline files: alternate parameter environments exercise the same functions.
    original=build(d['PRT-0505__L']['shape'],env);variant=dict(env,wheel_gap_visual=30,wheel_center_y=(p['wheel_diameter']+30)/2);changed=build(d['PRT-0505__L']['shape'],variant)
    gap_shift=changed.Center().y-original.Center().y;assert abs(gap_shift-2.5)<1e-6
    cap0=build(d['PRT-0601-A']['shape'],env);cap1=build(d['PRT-0601-A']['shape'],dict(env,tube_cap_allowance=24));capshift=cap1.BoundingBox().zmax-cap0.BoundingBox().zmax;assert abs(capshift-4)<1e-6
    restored=build(d['PRT-0505__L']['shape'],env);assert abs(restored.Center().y-original.Center().y)<1e-8
    result=dict(step_files_reopened=len(files),step_files=files,failures=fail,all_step_valid=not fail,parameter_rebuild_tests=[dict(parameter='wheel_gap_visual',old=25,new=30,observed_left_center_shift_mm=gap_shift,passed=True),dict(parameter='tube_cap_allowance',old=20,new=24,observed_top_shift_mm=capshift,passed=True)],baseline_restored=True,seconds=time.time()-start)
    rec=json.loads(metadata_path(R,'instances.json').read_text(encoding='utf-8'));counts=[]
    for main in json.loads((R/'data/parts.json').read_text(encoding='utf-8')):
        pid=main['part_id'];expected=sum(x['solid_count'] for x in rec if x['part_id']==pid);actual=next(x['solids'] for x in files if x['path'].replace('\\','/')=='output/step/parts/'+pid+'.step')
        counts.append(dict(part_id=pid,expected=expected,actual=actual,passed=actual==expected));assert expected==actual,(pid,expected,actual)
    result['main_item_completeness']=counts
    if fail:raise RuntimeError('Invalid STEP files: '+str(fail))
    (R/'reports/step_roundtrip.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print('STEP',len(files),'reopened;',len(fail),'failed; parameter rebuild passed')
if __name__=='__main__':run()
