"""Current-source rebuild. Immutable inputs and same-run stage evidence."""
import os,sys,shutil,argparse
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from tools.build_context import BuildContext,atomic_json
from tools.validate_release import run_stage
from tools.input_manifest import snapshot_inputs,require_unchanged

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--scope',choices=['core','full'],default='full');args=ap.parse_args()
    if sys.flags.optimize:raise RuntimeError('Optimized Python unsupported')
    before=snapshot_inputs(R);ctx=BuildContext.create(R,scope=args.scope)
    atomic_json(R/'reports/builds'/ctx.run_id/'context.json',ctx.to_dict())
    print('BUILD',ctx.run_id,args.scope,flush=True)
    count=0
    def py(script,*extra,reports=(),files=(),checks=()):
        nonlocal count
        count+=1
        stage=f'{count:02d}_'+Path(script).stem+('_'+str(extra[0]) if extra else '')
        print(stage,flush=True)
        return run_stage([sys.executable,str(R/script),*extra],ctx.for_stage(stage),R,expected_reports=reports,expected_files=files,completed_checks=checks)
    blender=os.environ.get('BM1_BLENDER_EXE') or shutil.which('blender')
    if not blender:
        blender=next((str(p) for p in (R/'tools/blender').glob('*/blender.exe')),None)
    def bl(script,reports=(),files=()):
        nonlocal count
        if not blender:raise RuntimeError('Set BM1_BLENDER_EXE; Blender is NOT_RUN')
        count+=1;stage=f'{count:02d}_'+Path(script).stem
        print(stage,flush=True)
        return run_stage([blender,'--background','--python-exit-code','1','--python',str(R/script)],ctx.for_stage(stage),R,expected_reports=reports,expected_files=files,completed_checks=['script_completed'])
    try:
        py('tools/run_tests.py',reports=['reports/unit_tests.json'],checks=['unit_tests'])
        py('cad/export_all.py',reports=['reports/solid_validation.json'],files=['output/generated_metadata/cache_provenance.json','output/step/BM1_V0_assembly.step'],checks=['native_solids'])
        py('tools/check_dimensions.py',reports=['reports/dimension_validation.json'])
        py('tools/check_collisions.py','static',reports=['reports/collisions_static.json'],checks=['static_collisions'])
        py('tools/check_collisions.py','motion',reports=['reports/collisions_motion.json'],checks=['sampled_motion'])
        py('tools/check_service.py',reports=['reports/service_validation.json'])
        py('tools/check_r1_service.py',reports=['reports/r1_service_validation.json'])
        py('tools/check_r1_contracts.py',reports=['reports/r1_contract_validation.json'])
        py('tools/enrich_metadata.py')
        py('tools/check_r3_geometry.py',reports=['reports/r3_geometry_validation.json'],checks=['motion_endpoints','connections','tool_channels'])
        if args.scope=='full':
            py('tools/calibration.py');bl('blender/check_calibration.py')
            py('tools/make_section.py')
            bl('blender/build_scene.py');bl('blender/reopen_check.py',reports=['reports/blender_roundtrip.json'])
            bl('blender/render_animation.py');py('tools/encode_animations.py')
            py('tools/build_book.py');py('tools/check_pdf.py');py('tools/validate_outputs.py');py('tools/check_parameter_rebuild.py')
            py('tools/build_r1_engineering_package.py');py('tools/build_r1_manual.py');py('tools/check_viewer_isolated.py')
            py('tools/final_report.py');py('tools/check_r1_delivery.py')
            py('tools/build_r2_prototype.py');py('tools/check_r2_prototype.py')
            py('tools/build_r3_package.py');bl('blender/build_r3_scene.py',reports=['reports/r3_blender_validation.json'])
            py('tools/build_r3_manual.py');py('tools/finish_r3_delivery.py');py('tools/check_r3_viewer.py')
        require_unchanged(R,before)
        atomic_json(R/'reports/builds'/ctx.run_id/'build.json',ctx.report('PASS',['core_pipeline']+(['render_pipeline'] if args.scope=='full' else []),stages=count,manufacturing_release=False))
    except Exception as exc:
        atomic_json(R/'reports/builds'/ctx.run_id/'build.json',ctx.report('FAIL',error=str(exc),stages=count));raise
    print('BUILD COMPLETE',ctx.run_id,'manufacturing_release=false')
if __name__=='__main__':main()
