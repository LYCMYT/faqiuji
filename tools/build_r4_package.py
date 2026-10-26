"""Export reviewable R4 native candidate; BLOCKED geometry is never upgraded by export."""
from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import cadquery as cq
from cad.assemblies.r4_fixture import model,posed
from cad.export_all import exact_bbox
from tools.build_context import active_context,atomic_json,file_hash
from tools.render_cad_preview import render

def run():
    ctx=active_context(R,'r4_exports','full');out=R/'output/fixture_r4'
    for d in ['step/parts','step/sections','drawings']:(out/d).mkdir(parents=True,exist_ok=True)
    rows,variants,s,b=model();state={**b['state'],'height':s['local_height_mm'],'guide':0,'slide':0,'upper':0,'gate':0};placed=posed(rows,state)
    groups={}
    for a in rows+variants:groups.setdefault(a['family'],a)
    section_names=[q['name'] for q in s['sections']]
    expected=['step/BM1_R4_fixture_assembly.step',*[f'step/parts/{name}.step' for name in groups],*[f'step/sections/{name}.step' for name in section_names]]
    # Only retire prior generated R4 index entries, never source/history files.
    previous=out/'parts_index.json'
    if previous.exists():
        for old in json.loads(previous.read_text(encoding='utf-8')):
            relative=old['step']
            if relative not in expected:
                obsolete=(out/relative).resolve()
                if obsolete.parent!=(out/'step/parts').resolve():raise RuntimeError('Unsafe obsolete artifact path')
                if obsolete.exists():obsolete.unlink()
    atomic_json(R/'reports/r4_export_validation.json',ctx.report('RUNNING',expected_step_set=expected))
    assy=cq.Assembly(name='BM1_R4_MANUAL_GUIDE_SUPPORT_CANDIDATE');meshes=[];metrics={expected[0]:{'volume':sum(sh.Volume() for _,sh in placed),'solids':sum(len(sh.Solids()) for _,sh in placed)}}
    for a,sh in placed:
        colors={'context':'#8CA4AF','custom':'#E28362','revised_context':'#7DA99F','hardware':'#B8BEC4'};color=colors[a['kind']];assy.add(sh,name=a['instance_id'],color=cq.Color(*[int(color[j:j+2],16)/255 for j in (1,3,5)]))
        vv,tt=sh.tessellate(.2,.2);bb=exact_bbox(sh)
        meshes.append(dict(instance_id=a['instance_id'],family=a['family'],part_id=a['part_id'],assembly_id=a['assembly_id'],kind=a['kind'],parent=a['parent'],color=color,vertices=[list(v.toTuple()) for v in vv],triangles=tt,bounds_mm=[bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax]))
    assy.export(str(out/expected[0]));atomic_json(out/'mesh.json',meshes)
    index=[]
    for family,a in groups.items():
        sh=a['shape'];bb=exact_bbox(sh);origin=[bb.xmin,bb.ymin,bb.zmin];local=sh.translate(tuple(-v for v in origin));file=f'step/parts/{family}.step';cq.exporters.export(local,str(out/file))
        metrics[file]={'volume':local.Volume(),'solids':len(local.Solids())}
        instances=[q['instance_id'] for q in rows if q['family']==family]
        index.append(dict(family=family,part_id=a['part_id'],source_revision=a.get('r4_revision',a.get('source_revision','R3 retained')),quantity_in_assembly=len(instances),instance_ids=instances,material=a['material'],kind=a['kind'],step=file,local_origin_H_mm=origin,holes=a.get('holes',[]),dimensions_mm=[bb.xlen,bb.ylen,bb.zlen],manufacturing_release=False))
    atomic_json(out/'parts_index.json',index)
    compound=cq.Compound.makeCompound([sh for _,sh in placed]);bb=exact_bbox(compound)
    for section in s['sections']:
        name,axis,value=section['name'],section['axis'],section['position_mm']
        lo=[bb.xmin-1,bb.ymin-1,bb.zmin-1];hi=[bb.xmax+1,bb.ymax+1,bb.zmax+1];hi[axis]=value;cutter=cq.Solid.makeBox(*[q-p for p,q in zip(lo,hi)],cq.Vector(*lo));cut=[]
        for a,sh in placed:
            q=sh.cut(cutter)
            if q.Volume()>.001:cut.append((a['instance_id'],q))
        section_shape=cq.Compound.makeCompound([sh for _,sh in cut]);relative=f'step/sections/{name}.step';metrics[relative]={'volume':section_shape.Volume(),'solids':len(section_shape.Solids())};cq.exporters.export(section_shape,str(out/relative));render(cut,out/'drawings'/name,'R4 / native boolean section / candidate only')
    render([(a['instance_id'],sh) for a,sh in placed],out/'drawings/assembly','R4 / manual guide + cork seat candidate / NOT RELEASED')
    render([(a['instance_id'],sh) for a,sh in placed if a['part_id'].startswith('PRT-07')],out/'drawings/receiving_support','R4 / receiving seat, captive slide and clamp / nominal')
    checks=[]
    for relative in expected:
        sh=cq.importers.importStep(str(out/relative)).val();source=metrics[relative];error=abs(sh.Volume()-source['volume']);valid=sh.isValid() and sh.Volume()>0 and len(sh.Solids())==source['solids'] and error<=max(1e-5,source['volume']*1e-8)
        if not valid:raise RuntimeError('Invalid STEP roundtrip '+relative)
        checks.append(dict(file=(out/relative).relative_to(R).as_posix(),valid=valid,solids=len(sh.Solids()),volume_mm3=sh.Volume(),source_volume_mm3=source['volume'],volume_error_mm3=error,source_solids=source['solids']))
    actual=sorted(q.relative_to(out).as_posix() for q in (out/'step').rglob('*.step'))
    if actual!=sorted(expected):raise RuntimeError('Unexpected/stale STEP file set')
    hashes={q.relative_to(R).as_posix():file_hash(q) for q in [*[out/v for v in expected],out/'parts_index.json',out/'mesh.json']}
    atomic_json(R/'reports/r4_export_validation.json',ctx.report('PASS',['expected_step_set','step_roundtrip'],hashes,expected_step_set=expected,step_reopened=checks,instances=len(rows),families=len(groups),sections=section_names,geometry_approval='Separate geometry report; exports do not imply mechanical PASS',manufacturing_release=False))
    print('R4 EXPORT',len(rows),'instances;',len(checks),'STEP roundtrips')
if __name__=='__main__':run()
