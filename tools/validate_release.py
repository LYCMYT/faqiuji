"""Fail-closed stage execution and same-run release validation."""
from pathlib import Path
import json
import os
import subprocess
import sys
from tools.build_context import atomic_json, file_hash, BuildContext
from tools.input_manifest import snapshot_inputs, require_unchanged


def require_report(report, ctx, required_checks=(), root=None):
    if isinstance(report, (str, Path)):
        report = json.loads(Path(report).read_text(encoding='utf-8'))
    for field in ('run_id','input_sha256','code_sha256','tool_versions','scope'):
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
        if result.returncode: raise RuntimeError('Stage exit code '+str(result.returncode))
        artifacts={}
        for name in (*expected_reports,*expected_files):
            path=root/name
            if not path.is_file() or not path.stat().st_size: raise RuntimeError('Missing expected artifact: '+name)
            artifacts[name]=file_hash(path)
        # Stage-specific status checks are mandatory, not inferred from empty errors.
        for name in expected_reports:
            report=json.loads((root/name).read_text(encoding='utf-8'))
            if report.get('status') in ('FAIL','BLOCKED','NOT_RUN') or report.get('errors') or report.get('unresolved_pairs',0):
                raise RuntimeError('Unsuccessful result: '+name)
            required_true = {
                'reports/r3_blender_validation.json': ['blend_reopened','glb_reopened','ids_preserved'],
                'reports/solid_validation.json': ['all_valid'],
                'reports/r1_service_validation.json': ['all_paths_passed'],
                'reports/r1_contract_validation.json': ['full_cycle_passed'],
            }.get(name, [])
            if any(report.get(key) is not True for key in required_true):
                raise RuntimeError('Required check false/missing: '+name)
        value=ctx.report('PASS',completed_checks,artifacts,command=list(cmd),returncode=0,log=str(log.relative_to(root)))
        atomic_json(dest,value)
        return value
    except Exception as exc:
        atomic_json(dest,ctx.report('FAIL',error=str(exc),command=list(cmd),log=str(log.relative_to(root))))
        raise


def validate_release(root, ctx, requirements, expected_files):
    root=Path(root)
    if ctx.scope!='full': raise RuntimeError('Release requires full scope')
    ctx.assert_current(root)
    for name, checks in requirements.items():
        require_report(root/'reports/builds'/ctx.run_id/(name+'.json'),ctx.for_stage(name),checks,root)
    for name in expected_files:
        if not (root/name).is_file() or not (root/name).stat().st_size: raise RuntimeError('Missing expected artifact: '+name)
    return ctx.report('PASS',['release_gate'],{p:file_hash(root/p) for p in expected_files},manufacturing_release=False)
