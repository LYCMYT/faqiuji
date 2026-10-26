"""Rebuild the R4 candidate from source, with fixed fail-closed release gates."""
from pathlib import Path
import csv
import json
import os
import shutil
import sys
import argparse
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from tools.build_context import BuildContext,atomic_json,file_hash
from tools.input_manifest import snapshot_inputs,require_unchanged
from tools.validate_release import run_stage,validate_release,validate_review_bundle
from tools.release_contract import REQUIRED_STAGES
from tools.doctor import probe

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--review-draft',action='store_true',help='Keep BLOCKED nominal geometry visible; does not produce release proof');args=parser.parse_args()
    if sys.flags.optimize:raise RuntimeError('Optimized Python unsupported')
    environment=probe()
    for name in ('blender','ffmpeg','ffprobe','chrome'):
        if environment['tools'][name]['status']!='AVAILABLE':raise RuntimeError('Required tool unavailable: '+name)
        os.environ['BM1_'+name.upper()+'_EXE']=environment['tools'][name]['path']
    if environment['chinese_font']['status']!='AVAILABLE':raise RuntimeError('Chinese font unavailable')
    before=snapshot_inputs(R);ctx=BuildContext.create(R,scope='full');run_dir=R/'reports/builds'/ctx.run_id
    environment['packages']=ctx.tool_versions
    atomic_json(run_dir/'context.json',ctx.to_dict());atomic_json(run_dir/'environment.json',environment)
    atomic_json(R/'reports/release_proof.json',ctx.report('RUNNING'))
    (R/'reports/r4_readiness.md').write_text('# BM1 R4\n\nRUNNING — current build has not passed release gates.\n',encoding='utf-8')
    O=R/'output/fixture_r4'
    if O.exists():
        archive=R/'output/history'/('fixture_r4_before_'+ctx.run_id);archive.parent.mkdir(parents=True,exist_ok=True)
        if not O.resolve().is_relative_to((R/'output').resolve()):raise RuntimeError('Invalid output archive path')
        O.rename(archive)
    O.mkdir(parents=True,exist_ok=True)
    print('R4 RUN',ctx.run_id,flush=True)
    def stage(name,script,report,files=(),blender=False):
        print('STAGE',name,flush=True)
        command=[sys.executable,str(R/script)]
        if blender:command=[environment['tools']['blender']['path'],'--background','--python-exit-code','1','--python',str(R/script)]
        return run_stage(command,ctx.for_stage(name),R,expected_reports=[report],expected_files=files,completed_checks=REQUIRED_STAGES[name])
    try:
        stage('unit_tests','tools/run_tests.py','reports/unit_tests.json')
        stage('failure_modes','tools/check_failure_modes.py','reports/r4_failure_modes.json')
        blocked=False
        try:stage('r4_geometry','tools/check_r4_geometry.py','reports/r4_geometry_validation.json')
        except RuntimeError:
            diagnostic=json.loads((R/'reports/r4_geometry_validation.json').read_text(encoding='utf-8'))
            if not args.review_draft or diagnostic.get('status')!='BLOCKED' or diagnostic.get('clearances',{}).get('intersections')!=[] or diagnostic.get('all_native_single_solids') is not True or diagnostic.get('support_projection',{}).get('status')!='PASS_NOMINAL':raise
            blocked=True
            atomic_json(run_dir/'r4_geometry.json',ctx.for_stage('r4_geometry').report('BLOCKED',diagnostic.get('completed_checks',[]),{'reports/r4_geometry_validation.json':file_hash(R/'reports/r4_geometry_validation.json')},reason='Nominal full diagnostic retains unresolved mechanical/service requirements'))
        stage('r4_exports','tools/build_r4_package.py','reports/r4_export_validation.json',
              ['output/fixture_r4/parts_index.json','output/fixture_r4/mesh.json','output/fixture_r4/step/BM1_R4_fixture_assembly.step'])
        stage('r4_blender','blender/build_r4_scene.py','reports/r4_blender_validation.json',
              ['output/fixture_r4/BM1_R4_fixture.blend','output/fixture_r4/BM1_R4_fixture.glb','output/fixture_r4/R4_assembly.png','output/fixture_r4/R4_exploded.png'],blender=True)
        stage('r4_media','tools/finish_r4_media.py','reports/r4_media_validation.json')
        shutil.copyfile(R/'viewer/r4_template.html',O/'viewer.html')
        stage('r4_viewer','tools/check_r4_viewer.py','reports/r4_viewer_validation.json')
        stage('r4_documents','tools/build_r4_manual.py','reports/r4_document_validation.json')
        index=json.loads((O/'parts_index.json').read_text(encoding='utf-8'))
        with (O/'first_article_RFQ.csv').open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(['family','revision','STEP','material_candidate','datums_and_holes','drawing_review','supplier','quantity','quote_CNY','lead_days','first_article_released'])
            for item in index:
                if 'R4' in item.get('family',''):
                    writer.writerow([item['family'],'R4',item['step'],item.get('material','OPEN'),json.dumps(item.get('holes',[]),ensure_ascii=False),'OPEN','','','','',False])
        with (O/'physical_measurements_BLANK.csv').open('w',encoding='utf-8-sig',newline='') as stream:
            csv.writer(stream).writerow(['record_id','sample_id','hardware_revision','pose','instrument','operator','date','quantity','value','unit','raw_evidence_path','sha256','review_status'])
        links=[('BM1_R4_review_book.pdf','中文 R4 图册'),('step/BM1_R4_fixture_assembly.step','总装 STEP'),('BM1_R4_fixture.blend','BLEND'),('BM1_R4_fixture.glb','GLB'),('BM1_R4_connections_explode.mp4','分解动画'),('viewer.html','本地三维查看器'),('first_article_RFQ.csv','首件询价范围'),('../../reports/r4_readiness.md','实际检查与开放项')]
        body='<h1>BM1 R4 · 工程评审候选</h1><p>数字检查仅覆盖报告声明范围；制造、采购接口和实物试验另行确认。</p><ul>'+''.join(f'<li><a href="{path}">{label}</a></li>' for path,label in links)+'</ul><img src="R4_assembly.png"><img src="R4_exploded.png">'
        (O/'index.html').write_text('<!doctype html><html lang="zh"><meta charset="utf-8"><title>BM1 R4</title><style>body{max-width:1100px;margin:40px auto;font:16px/1.8 system-ui;color:#183a4d;background:#f4f7f9}img{width:100%}a{color:#087b80}</style>'+body+'</html>',encoding='utf-8')
        def read(name):return json.loads((R/'reports'/name).read_text(encoding='utf-8'))
        geo=read('r4_geometry_validation.json');exports=read('r4_export_validation.json');pdf=read('r4_document_validation.json');tests=read('unit_tests.json')
        scope=json.loads((R/'data/r4_release_scope.json').read_text(encoding='utf-8'))
        text='# BM1 R4 实际检查与剩余输入\n\n'
        text+=f'构建 {ctx.run_id}；Git {ctx.commit_sha}。输入 {ctx.input_sha256}；源码 {ctx.code_sha256}。\n\n'
        text+=f"实际运行：{tests['tests_run']} 项单元测试，失败 {tests['failures']}、错误 {tests['errors']}；8 类故意失败注入通过。R4 几何状态 {geo['status']}；逐件 STEP、BLEND/GLB、中文 PDF（{pdf['pages']} 页）、动画完整解码、本地查看器交互分别经过本次检查。详情为 reports/builds/{ctx.run_id}/ 的日志和来源报告。\n\n"
        if blocked:text+='机械门禁 BLOCKED：当前包仅供评审，完整发布门禁未通过。连接、保持和工具操作的具体失败/开放项逐条见 r4_geometry_validation.json；不得把导出和图页通过理解为机械通过。\n\n'+json.dumps({'connections':geo.get('connections'),'tool_status':geo.get('tool_status'),'tool_intersections':geo.get('tool_intersections'),'assumptions':geo.get('assumptions')},ensure_ascii=False,indent=2)+'\n\n'
        text+='数字通过只限报告中的离散状态、名义接触和工具包络；不是连续扫掠、刚度、预紧、公差叠加或实物性能证明。\n\n'
        text+='未运行：真实供应商接口核验、球样测量、夹力/轮速/停止距离、报价、加工、低速硬件循环、高速发射、落点标定及安全等级验证。人工签核 NOT_RUN，不能由自动渲染继承。保留的 R1–R3 历史动画/图册没有在本次 R4 构建中全部重渲染，不作为本次 R4 检查证明。\n\n'
        text+='首件和低速试验需要：\n\n'
        text+='\n'.join('- '+item['id']+' ['+item['status']+']：'+item['required'] for item in scope['open_inputs'])
        text+='\n\n整机 manufacturing_release=false；首件和自动运行尚未放行。具体顺序见 docs/test_protocol_r4.md；数字候选交付不关闭任何实物开放项。\n'
        (R/'reports/r4_readiness.md').write_text(text,encoding='utf-8')
        summary_files=[O/'first_article_RFQ.csv',O/'physical_measurements_BLANK.csv',O/'index.html',R/'reports/r4_readiness.md']
        atomic_json(run_dir/'r4_metadata.json',ctx.for_stage('r4_metadata').report('PASS',['scope_summary'],{path.relative_to(R).as_posix():file_hash(path) for path in summary_files},manufacturing_release=False))
        require_unchanged(R,before)
        proof=validate_review_bundle(R,ctx) if blocked else validate_release(R,ctx)
        atomic_json(run_dir/('review_bundle.json' if blocked else 'release.json'),proof)
        atomic_json(R/'reports'/('r4_review_bundle.json' if blocked else 'release_proof.json'),proof)
        if blocked:atomic_json(R/'reports/release_proof.json',ctx.for_stage('release').report('BLOCKED',reason='Mechanical/service findings remain OPEN; review bundle is not a release'))
        atomic_json(run_dir/'build.json',ctx.report('REVIEW_ONLY' if blocked else 'PASS',list(REQUIRED_STAGES),manufacturing_release=False))
        # Immutable run snapshot excludes raw frames; final files remain directly browsable.
        snapshot=R/'output/builds'/ctx.run_id/'fixture_r4'
        shutil.copytree(O,snapshot,ignore=shutil.ignore_patterns('frames','*.log'))
        print('R4 CANDIDATE','REVIEW_ONLY' if blocked else 'PASS',ctx.run_id,'manufacturing_release=false',flush=True)
    except Exception as exc:
        atomic_json(run_dir/'build.json',ctx.report('FAIL',error=str(exc),manufacturing_release=False))
        atomic_json(R/'reports/release_proof.json',ctx.report('FAIL',error=str(exc)))
        (R/'reports/r4_readiness.md').write_text('# BM1 R4\n\n构建未通过；不得发布为已通过候选。\n\n'+str(exc)+'\n\n实物/制造放行保持 false。详见 reports/builds/'+ctx.run_id+'/。\n',encoding='utf-8')
        raise

if __name__=='__main__':main()
