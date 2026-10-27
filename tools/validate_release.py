"""Fail-closed stage execution and same-run release validation."""
from pathlib import Path
import json
import os
import subprocess
import sys
import math
from tools.build_context import atomic_json, file_hash, BuildContext
from tools.input_manifest import snapshot_inputs, require_unchanged

def require_unreleased_physical_scope(root):
    for filename in ('r1_engineering.json','r2_prototype.json','r3_fixture.json','r4_fixture.json','r4_release_scope.json'):
        path=Path(root)/'data'/filename
        if path.is_file():
            data=json.loads(path.read_text(encoding='utf-8'))
            boundary=data.get('hardware_evidence',{}).get('manufacturing_release') if filename=='r1_engineering.json' else data.get('manufacturing_release')
            if boundary is not False:raise RuntimeError('Physical manufacturing boundary must remain false: '+filename)


def require_report(report, ctx, required_checks=(), root=None):
    if isinstance(report, (str, Path)):
        report = json.loads(Path(report).read_text(encoding='utf-8'))
    for field in ('run_id','input_sha256','code_sha256','tool_versions','scope','stage'):
        if report.get(field) != getattr(ctx, field): raise RuntimeError('Report mismatch: '+field)
    if report.get('status') != 'PASS': raise RuntimeError('Report did not PASS')
    missing = set(required_checks)-set(report.get('completed_checks', []))
    if missing: raise RuntimeError('Missing completed checks: '+str(sorted(missing)))
    if root:
        ctx.assert_current(root)
        for path,digest in report.get('artifact_hashes', {}).items():
            if not (Path(root)/path).is_file() or file_hash(Path(root)/path)!=digest:
                raise RuntimeError('Artifact missing/changed: '+path)
    return report


def validate_stage_result(name, report, ctx, root=None):
    """Explicit adapters for legacy producers; no missing-field success defaults."""
    if name=='reports/service_validation.json':
        if not isinstance(report,list) or not report or any(not isinstance(x,dict) or x.get('geometric_path_passed') is not True or x.get('collisions')!=[] for x in report):
            raise RuntimeError('Invalid service cases')
        return
    if not isinstance(report,dict) or not report:raise RuntimeError('Malformed/empty report: '+name)
    if name.startswith('reports/r4_'):
        from tools.release_contract import REQUIRED_STAGES
        if ctx.stage not in REQUIRED_STAGES:raise RuntimeError('Unknown R4 report stage')
        require_report(report,ctx,REQUIRED_STAGES[ctx.stage],root)
        required_artifacts={
            'r4_blender':['BM1_R4_fixture.blend','BM1_R4_fixture.glb','R4_assembly.png','R4_exploded.png'],
            'r4_media':['BM1_R4_connections_explode.mp4'],
            'r4_documents':['BM1_R4_review_book.pdf'],
            'r4_exports':['parts_index.json','mesh.json','step/BM1_R4_fixture_assembly.step'],
            'r4_viewer':['viewer.html','viewer_preview.png'],
        }.get(ctx.stage,[])
        hashes=report.get('artifact_hashes')
        if not isinstance(hashes,dict) or any('output/fixture_r4/'+name not in hashes for name in required_artifacts):raise RuntimeError('Incomplete producer artifact set: '+ctx.stage)
        if ctx.stage=='failure_modes':
            results=report.get('results',{})
            for name in ('blender_nonzero','collision_nonzero','boolean_error_nonzero','corrupt_step_nonzero'):
                rc=results.get(name,{}).get('returncode')
                if type(rc) is not int or rc==0:raise RuntimeError('Missing failure-injection exit evidence: '+name)
        true_fields={
            'r4_blender':['blend_reopened','glb_reopened','ids_preserved','frames_rendered'],
            'r4_media':['video_fully_decoded'],
            'r4_viewer':['loaded','part_isolation','restore_all','asm_prt_metadata'],
            'r4_geometry':['all_native_single_solids'],
        }.get(ctx.stage,[])
        if any(report.get(key) is not True for key in true_fields):raise RuntimeError('Required R4 result missing/false: '+ctx.stage)
        for key in {'r4_blender':['meshes'],'r4_media':['frames'],'r4_documents':['pages'],'r4_exports':['instances','families']}.get(ctx.stage,[]):
            if type(report.get(key)) is not int or report[key]<=0:raise RuntimeError('Invalid R4 result count: '+key)
        for key in {'r4_documents':['text_overflow'],'r4_viewer':['js_errors']}.get(ctx.stage,[]):
            if report.get(key)!=[]:raise RuntimeError('R4 result defects/missing: '+key)
        if ctx.stage=='r4_exports':
            rows=report.get('step_reopened');expected=report.get('expected_step_set')
            if not isinstance(rows,list) or not rows or not isinstance(expected,list) or len(rows)!=len(expected):raise RuntimeError('Incomplete expected STEP evidence')
            if {x.get('file') for x in rows}!={'output/fixture_r4/'+x for x in expected}:raise RuntimeError('STEP result set mismatch')
            for row in rows:
                if row.get('valid') is not True or type(row.get('solids')) is not int or row['solids']<=0 or row.get('source_solids')!=row['solids']:raise RuntimeError('Invalid STEP result')
                for key in ('volume_mm3','source_volume_mm3','volume_error_mm3'):
                    value=row.get(key)
                    if type(value) not in (int,float) or not math.isfinite(value):raise RuntimeError('Invalid STEP volume evidence')
                if row['volume_mm3']<=0 or row['source_volume_mm3']<=0 or abs(row['volume_mm3']-row['source_volume_mm3'])>max(1e-5,abs(row['source_volume_mm3'])*1e-8):raise RuntimeError('STEP volume mismatch')
                if row['file'] not in report.get('artifact_hashes',{}):raise RuntimeError('Unbound STEP result')
        if ctx.stage=='r4_geometry' and (report.get('clearances',{}).get('intersections')!=[] or report.get('support_projection',{}).get('status')!='PASS_NOMINAL' or report.get('tool_intersections')!=[]):raise RuntimeError('Nominal geometry/tool failure')
        return
    if 'run_id' in report:
        for key in ('run_id','input_sha256','code_sha256','tool_versions'):
            if report.get(key)!=getattr(ctx,key):raise RuntimeError('Report mismatch: '+key)
        if report.get('status')!='PASS':raise RuntimeError('Report did not PASS: '+name)
    if name.startswith('reports/collisions_'):
        mode=Path(name).stem.removeprefix('collisions_')
        require_report(report,ctx.for_stage('collisions_'+mode,mode),[mode+'_collisions'])
        if report.get('scope')!=mode or report.get('mode')!=mode:raise RuntimeError('Collision scope mismatch')
        for key in ('states','pair_evaluations','exact_intersections'):
            if type(report.get(key)) is not int or report[key]<=0:raise RuntimeError('Missing collision count: '+key)
        if report.get('errors')!=[] or type(report.get('unresolved_pairs')) is not int or report['unresolved_pairs']!=0 or report.get('indeterminate_pairs')!=0:raise RuntimeError('Collision check failed')
        return
    required={
        'reports/unit_tests.json':['status','tests_run','failures','errors','skipped'],
        'reports/solid_validation.json':['instances','main_items','all_valid','solids'],
        'reports/r3_geometry_validation.json':['status','mode','scope','states','all_native_single_solids','completed_checks'],
        'reports/r3_blender_validation.json':['blend_reopened','glb_reopened','ids_preserved','meshes'],
        'reports/blender_roundtrip.json':['blend_reopened','glb_reopened','glb_ids_preserved','reference_shuttle_independent'],
        'reports/r1_service_validation.json':['all_paths_passed','cases'],
        'reports/r1_contract_validation.json':['full_cycle_passed','cycle_trace','fault_cases'],
        'reports/dimension_validation.json':['wheel_skirt_min_sampled_mm','open_finger_cork_gap_mm','guide_clear_bottom_H'],
        'reports/step_roundtrip.json':['all_step_valid','step_files_reopened','main_item_completeness','failures'],
        'reports/pdf_validation.json':['pages','out_of_page_text','rendered_every_page'],
        'reports/parameter_full_rebuild.json':['baseline_regenerated_and_identical','baseline_data_untouched','variants'],
        'reports/r1_bench_validation.json':['step_reopened','static_intersections'],
        'reports/viewer_validation.json':['loaded','meshes','js_errors','part_information'],
        'reports/r2_delivery_validation.json':['status','step_dxf_roundtrips','pdf_text_overflow','manufacturing_release'],
        'reports/r3_export_validation.json':['instances','step_files','step_reopened','manufacturing_release'],
        'reports/r3_delivery_validation.json':['status','blend_glb_reopened','video_fully_decoded','step_reopened','pdf_text_overflow'],
        'reports/r3_viewer_validation.json':['loaded','part_isolation','restore_all','asm_prt_metadata','js_errors'],
    }.get(name)
    if required is None:raise RuntimeError('No explicit result schema: '+name)
    if any(k not in report for k in required):raise RuntimeError('Missing report fields: '+name)
    for key in ('all_valid','all_paths_passed','full_cycle_passed','all_native_single_solids','blend_reopened','glb_reopened','ids_preserved','glb_ids_preserved','reference_shuttle_independent','all_step_valid','rendered_every_page','baseline_regenerated_and_identical','baseline_data_untouched','loaded','part_information','blend_glb_reopened','video_fully_decoded','part_isolation','restore_all','asm_prt_metadata'):
        if key in required and report[key] is not True:raise RuntimeError('Required true: '+key)
    if 'status' in required and report['status']!='PASS':raise RuntimeError('Report not PASS')
    for key in ('failures','out_of_page_text','static_intersections','js_errors','pdf_text_overflow'):
        if key in required and report[key]!=[] and not (name=='reports/unit_tests.json' and report[key]==0):raise RuntimeError('Reported defects: '+key)
    if 'manufacturing_release' in required and report['manufacturing_release'] is not False:raise RuntimeError('Manufacturing release must stay false')
    if name=='reports/step_roundtrip.json' and (not report['main_item_completeness'] or any(x.get('passed') is not True for x in report['main_item_completeness']) or type(report['step_files_reopened']) is not int or report['step_files_reopened']<=0):raise RuntimeError('STEP checks incomplete')
    if name=='reports/unit_tests.json' and (type(report['tests_run']) is not int or report['tests_run']<=0 or report['failures']!=0 or report['errors']!=0):raise RuntimeError('Tests failed/incomplete')
    if name=='reports/r3_geometry_validation.json' and (report['mode']!='full' or report['scope']!='full' or 'motion_endpoints' not in report['completed_checks']):raise RuntimeError('Full R3 motion required')
    if name=='reports/r3_geometry_validation.json':require_report(report,ctx.for_stage('r3_geometry','full'),['native_solids','motion_endpoints','connections','tool_channels'])


def run_stage(cmd, ctx, cwd, *, expected_reports=(), expected_files=(), completed_checks=()):
    root=Path(cwd)
    if sys.flags.optimize: raise RuntimeError('PYTHONOPTIMIZE unsupported: legacy checkers contain assertions')
    ctx.assert_current(root)
    before=snapshot_inputs(root)
    dest=root/'reports/builds'/ctx.run_id/(ctx.stage+'.json')
    atomic_json(dest, ctx.report('RUNNING'))
    # Remove only declared result files, never inputs or evidence.
    for name in expected_reports:
        path=(root/name).resolve()
        if not path.is_relative_to((root/'reports').resolve()): raise RuntimeError('Report outside reports/: '+name)
        path.unlink(missing_ok=True)
    context_file=root/'reports/builds'/ctx.run_id/'context.json'
    atomic_json(context_file,ctx.to_dict())
    env=dict(os.environ, BM1_BUILD_CONTEXT=str(context_file), PYTHONIOENCODING='utf-8')
    if env.get('PYTHONOPTIMIZE'): raise RuntimeError('PYTHONOPTIMIZE unsupported')
    log=dest.with_suffix('.log')
    try:
        with log.open('w',encoding='utf-8') as stream:
            result=subprocess.run(cmd,cwd=root,env=env,stdout=stream,stderr=subprocess.STDOUT)
        require_unchanged(root,before)
        ctx.assert_current(root)
        if result.returncode: raise RuntimeError('Stage exit code '+str(result.returncode))
        artifacts={}
        for name in (*expected_reports,*expected_files):
            path=root/name
            if not path.is_file() or not path.stat().st_size: raise RuntimeError('Missing expected artifact: '+name)
            artifacts[name]=file_hash(path)
        # Stage-specific status checks are mandatory, not inferred from empty errors.
        for name in expected_reports:
            report=json.loads((root/name).read_text(encoding='utf-8'))
            validate_stage_result(name,report,ctx,root)
            if isinstance(report,dict):
                for artifact,digest in report.get('artifact_hashes',{}).items():
                    if not (root/artifact).is_file() or file_hash(root/artifact)!=digest:raise RuntimeError('Changed producer artifact: '+artifact)
                    artifacts[artifact]=digest
        value=ctx.report('PASS',completed_checks,artifacts,command=list(cmd),returncode=0,log=str(log.relative_to(root)))
        atomic_json(dest,value)
        return value
    except Exception as exc:
        atomic_json(dest,ctx.report('FAIL',error=str(exc),command=list(cmd),log=str(log.relative_to(root))))
        raise


def validate_release(root, ctx, requirements=None, expected_files=None):
    from tools.release_contract import REQUIRED_STAGES, REQUIRED_FILES, CONTRACT_ID
    root=Path(root)
    require_unreleased_physical_scope(root)
    if requirements is not None and requirements!=REQUIRED_STAGES:raise RuntimeError('Incomplete/noncanonical release contract')
    if expected_files is not None and expected_files!=REQUIRED_FILES:raise RuntimeError('Incomplete/noncanonical artifact contract')
    requirements=REQUIRED_STAGES;expected_files=list(REQUIRED_FILES)
    if ctx.scope!='full': raise RuntimeError('Release requires full scope')
    ctx.assert_current(root)
    bound={}
    for name, checks in requirements.items():
        report=require_report(root/'reports/builds'/ctx.run_id/(name+'.json'),ctx.for_stage(name),checks,root)
        bound.update(report['artifact_hashes'])
    index_path=root/'output/fixture_r4/parts_index.json'
    if not index_path.is_file():raise RuntimeError('Missing expected parts index')
    index=json.loads(index_path.read_text(encoding='utf-8'))
    if not isinstance(index,list) or not index:raise RuntimeError('Empty expected parts index')
    # The index itself is bound by same-run export proof; every declared part must exist.
    expected_files += ['output/fixture_r4/'+x['step'] for x in index]
    for name in expected_files:
        if not (root/name).is_file() or not (root/name).stat().st_size: raise RuntimeError('Missing expected artifact: '+name)
        if not name.startswith(('data/','docs/')) and name not in bound:raise RuntimeError('Required artifact lacks validated producer: '+name)
    return ctx.for_stage('release').report('PASS',['release_gate'],{p:file_hash(root/p) for p in expected_files},contract_id=CONTRACT_ID,manufacturing_release=False)


def validate_review_bundle(root,ctx):
    """Separate diagnostic bundle contract. Never satisfies the full release gate."""
    from tools.release_contract import REQUIRED_STAGES,REQUIRED_FILES,CONTRACT_ID
    root=Path(root);ctx.assert_current(root)
    require_unreleased_physical_scope(root)
    bound={}
    for name,checks in REQUIRED_STAGES.items():
        if name=='r4_geometry':continue
        result=require_report(root/'reports/builds'/ctx.run_id/(name+'.json'),ctx.for_stage(name),checks,root)
        bound.update(result['artifact_hashes'])
    path=root/'reports/r4_geometry_validation.json';geo=json.loads(path.read_text(encoding='utf-8'))
    for key in ('run_id','input_sha256','code_sha256','tool_versions'):
        if geo.get(key)!=getattr(ctx,key):raise RuntimeError('Review geometry source mismatch: '+key)
    if geo.get('scope')!='full' or geo.get('status')!='BLOCKED':raise RuntimeError('Review-only contract requires explicitly BLOCKED full diagnostic')
    if geo.get('digital_status')!='PASS' or geo.get('digital_failures')!=[]:raise RuntimeError('Review bundle requires completed nominal digital checks')
    if geo.get('all_native_single_solids') is not True or geo.get('clearances',{}).get('intersections')!=[] or geo.get('support_projection',{}).get('status')!='PASS_NOMINAL':
        raise RuntimeError('Unresolved nominal solid/contact/collision defects; review bundle not eligible')
    if 'sampled_motion' not in geo.get('completed_checks',[]):raise RuntimeError('Motion diagnostic NOT_RUN')
    files=list(REQUIRED_FILES)+['reports/r4_geometry_validation.json']
    bound['reports/r4_geometry_validation.json']=file_hash(path)
    index=json.loads((root/'output/fixture_r4/parts_index.json').read_text(encoding='utf-8'))
    if not index:raise RuntimeError('Empty part manifest')
    files+=['output/fixture_r4/'+item['step'] for item in index]
    for name in files:
        if not (root/name).is_file() or not (root/name).stat().st_size:raise RuntimeError('Missing review artifact: '+name)
        if not name.startswith(('data/','docs/')) and name not in bound:raise RuntimeError('Review artifact lacks validated producer: '+name)
    return ctx.for_stage('review_bundle','review').report('REVIEW_ONLY',['review_bundle_integrity'],
        {name:file_hash(root/name) for name in files},contract_id=CONTRACT_ID+'-blocked-review',
        full_release_allowed=False,manufacturing_release=False,geometry_status='BLOCKED')
