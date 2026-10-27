"""Executable fault injection in temporary copies. Never modifies project inputs."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from tools.build_context import active_context, BuildContext, atomic_json, file_hash
from tools.validate_release import require_report, run_stage, validate_stage_result

def main():
    import cadquery as cq
    ctx=active_context(R,'failure_modes')
    checks=[];results={}
    def rejected(label, action):
        try:action()
        except (RuntimeError,ValueError,FileNotFoundError):checks.append(label);return
        raise RuntimeError('Fault injection incorrectly accepted: '+label)
    rejected('stale_rejected',lambda:require_report({**ctx.report('PASS'),'run_id':'old'},ctx))
    rejected('static_rejected',lambda:require_report({**ctx.report('PASS'),'scope':'static'},ctx))
    rejected('malformed_report_rejected',lambda:validate_stage_result('reports/collisions_static.json',{},ctx))
    blender=os.environ.get('BM1_BLENDER_EXE') or shutil.which('blender')
    if not blender:raise RuntimeError('Blender fault injection NOT_RUN: configure BM1_BLENDER_EXE')
    with tempfile.TemporaryDirectory(prefix='bm1-r4-faults-') as td:
        root=Path(td)
        for directory in ('tools','cad','data'):
            shutil.copytree(R/directory,root/directory,ignore=shutil.ignore_patterns('__pycache__','blender'))
        (root/'reports').mkdir();(root/'output/mesh').mkdir(parents=True);(root/'output/generated_metadata').mkdir()
        shape=cq.Workplane('XY').box(10,10,10).val()
        entries=[]
        for name in ('PROBE-A','PROBE-B'):
            entries.append(dict(instance_id=name,part_id=name,parent='WORLD_STATIC',reference=False,shape={'type':'box','size':[10,10,10],'at':[0,0,0]}))
            shape.exportBrep(str(root/'output/mesh'/f'{name}.brep'))
        atomic_json(root/'data/geometry.json',{'instances':entries})
        atomic_json(root/'data/contact_pairs.json',[])
        atomic_json(root/'output/generated_metadata/instances.json',entries)
        fake=BuildContext.create(root,'cad_export')
        artifacts={p.relative_to(root).as_posix():file_hash(p) for p in (root/'output/mesh').glob('*.brep')}
        artifacts['output/generated_metadata/instances.json']=file_hash(root/'output/generated_metadata/instances.json')
        atomic_json(root/'output/generated_metadata/cache_provenance.json',fake.report('PASS',['native_solids'],artifacts))
        env=os.environ.copy();env.pop('BM1_BUILD_CONTEXT',None)
        for label,command in [
            ('collision_nonzero',[sys.executable,str(root/'tools/check_collisions.py'),'static']),
            ('boolean_error_nonzero',[sys.executable,'-c',"from tools import check_collisions as c\ndef fail(*a,**k):raise RuntimeError('injected boolean failure')\nc.cq.Shape.intersect=fail\nraise SystemExit(0 if c.run('static') else 1)"]),
            ('blender_nonzero',[blender,'--background','--python-exit-code','1','--python-expr',"raise RuntimeError('R4 deliberate exception')"]),
        ]:
            p=subprocess.run(command,cwd=root,env=env,capture_output=True,text=True)
            results[label]={'returncode':p.returncode,'tail':(p.stdout+p.stderr)[-1500:]}
            if p.returncode==0:raise RuntimeError(label+' failed to propagate failure')
            if label in ('collision_nonzero','boolean_error_nonzero'):
                report=json.loads((root/'reports/collisions_static.json').read_text(encoding='utf-8'))
                if label=='collision_nonzero' and report.get('unresolved_pairs')!=1:raise RuntimeError('Collision probe did not reach intersection')
                if label=='boolean_error_nonzero' and not report.get('errors'):raise RuntimeError('Boolean probe did not reach injected exception')
            checks.append(label)
        bad=root/'corrupt.step';bad.write_text('deliberately invalid STEP')
        p=subprocess.run([sys.executable,'-c','import cadquery as cq; cq.importers.importStep("corrupt.step")'],cwd=root,env=env,capture_output=True,text=True)
        if p.returncode==0:raise RuntimeError('Corrupt STEP accepted')
        checks.append('corrupt_step_nonzero');results['corrupt_step_nonzero']={'returncode':p.returncode,'tail':p.stderr[-1000:]}
        missing=BuildContext.create(root,'missing_file')
        rejected('missing_artifact_rejected',lambda:run_stage([sys.executable,'-c','pass'],missing,root,expected_files=['missing.step']))
    report=ctx.report('PASS',checks,results=results,scope_notice='Synthetic native geometry, deliberate software errors; no hardware test')
    atomic_json(R/'reports/r4_failure_modes.json',report)
    print('Failure modes:',len(checks),'PASS')

if __name__=='__main__':main()
