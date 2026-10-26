import sys
import tempfile
import unittest
import json
from pathlib import Path
from tools.build_context import BuildContext
from tools.validate_release import require_report, run_stage, validate_release, validate_stage_result


class ReleaseGates(unittest.TestCase):
    def test_scope_identity_and_failed_stage(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); ctx=BuildContext.create(root,'negative','full')
            for change in ({'scope':'static'},{'run_id':'old'},{'status':'FAIL'},{'completed_checks':[]}):
                report=ctx.report('PASS',['motion']); report.update(change)
                with self.assertRaises(RuntimeError): require_report(report,ctx,['motion'])
            with self.assertRaises(RuntimeError): run_stage([sys.executable,'-c','raise RuntimeError("injected")'],ctx,root)
            report=root/'reports/builds'/ctx.run_id/'negative.json'
            self.assertIn('"FAIL"',report.read_text())
            with self.assertRaises(RuntimeError): run_stage([sys.executable,'-c','pass'],ctx,root,expected_files=['missing.step'])

    def test_missing_expected_file_and_source_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); (root/'data').mkdir(); (root/'data/design.json').write_text('{}')
            ctx=BuildContext.create(root)
            with self.assertRaises(RuntimeError): validate_release(root,ctx,{},['missing.step'])
            (root/'data/design.json').write_text('{"gap":30}')
            with self.assertRaises(RuntimeError): require_report(ctx.report('PASS'),ctx,root=root)

    def test_legacy_service_adapter_and_malformed_reports(self):
        with tempfile.TemporaryDirectory() as td:
            ctx=BuildContext.create(Path(td),'check_service')
            validate_stage_result('reports/service_validation.json',[{'geometric_path_passed':True,'collisions':[]}],ctx)
            for value in ({},[],[{'geometric_path_passed':True}],[{'geometric_path_passed':'true','collisions':[]}]):
                with self.assertRaises(RuntimeError):validate_stage_result('reports/service_validation.json',value,ctx)
            for value in ({},{'status':'RUNNING'},{'errors':[],'unresolved_pairs':0}):
                with self.assertRaises(RuntimeError):validate_stage_result('reports/collisions_motion.json',value,ctx)
            report=ctx.report('PASS',['motion']);report['run_id']='old'
            with self.assertRaises(RuntimeError):validate_stage_result('reports/r3_geometry_validation.json',report,ctx)
            report=ctx.report('PASS',['motion']);report['stage']='wrong'
            with self.assertRaises(RuntimeError):require_report(report,ctx)

    def test_r4_reopen_flags_are_not_inferred_from_status(self):
        with tempfile.TemporaryDirectory() as td:
            ctx=BuildContext.create(Path(td),'r4_blender')
            from tools.release_contract import REQUIRED_STAGES
            report=ctx.report('PASS',REQUIRED_STAGES['r4_blender'],blend_reopened=True,glb_reopened=True,ids_preserved=True,frames_rendered=True,meshes=1)
            report['artifact_hashes']={'output/fixture_r4/'+name:'0'*64 for name in ('BM1_R4_fixture.blend','BM1_R4_fixture.glb','R4_assembly.png','R4_exploded.png')}
            validate_stage_result('reports/r4_blender_validation.json',report,ctx)
            for key in ('blend_reopened','glb_reopened','ids_preserved','frames_rendered'):
                for value in (False,None,'true'):
                    with self.assertRaises(RuntimeError):validate_stage_result('reports/r4_blender_validation.json',{**report,key:value},ctx)
            with self.assertRaisesRegex(RuntimeError,'Incomplete producer artifact set'):validate_stage_result('reports/r4_blender_validation.json',{**report,'artifact_hashes':{}},ctx)

    def test_direct_encoder_rejects_stale_or_changed_frames(self):
        from tools.finish_r4_media import require_rendered_frames
        from tools.build_context import atomic_json,file_hash
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);frame=root/'output/fixture_r4/frames/0001.png';frame.parent.mkdir(parents=True);frame.write_bytes(b'original')
            ctx=BuildContext.create(root,'r4_media')
            report=ctx.for_stage('r4_blender').report('PASS',['frames_rendered'],frames_rendered=True,frame_hashes={frame.relative_to(root).as_posix():file_hash(frame)})
            target=root/'reports/r4_blender_validation.json';atomic_json(target,report)
            require_rendered_frames(root,ctx,[frame])
            frame.write_bytes(b'changed')
            with self.assertRaisesRegex(RuntimeError,'Stale/changed frame'):require_rendered_frames(root,ctx,[frame])
            frame.write_bytes(b'original');atomic_json(target,{**report,'run_id':'old'})
            with self.assertRaisesRegex(RuntimeError,'Report mismatch'):require_rendered_frames(root,ctx,[frame])

    def test_producer_hashes_survive_stage_wrapper(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);ctx=BuildContext.create(root,'r4_documents')
            payload=ctx.report('PASS',['pdf_rendered','pdf_text_bounds'],pages=1,text_overflow=[],manual_signoff='NOT_RUN')
            code="import sys,json,hashlib;from pathlib import Path;r=json.loads(sys.argv[1]);p=Path('output/fixture_r4/BM1_R4_review_book.pdf');p.parent.mkdir(parents=True);p.write_bytes(b'first');r['artifact_hashes']={'output/fixture_r4/BM1_R4_review_book.pdf':hashlib.sha256(p.read_bytes()).hexdigest()};Path('reports/r4_document_validation.json').write_text(json.dumps(r))"
            report=run_stage([sys.executable,'-c',code,json.dumps(payload)],ctx,root,expected_reports=['reports/r4_document_validation.json'],completed_checks=['pdf_rendered','pdf_text_bounds'])
            self.assertIn('output/fixture_r4/BM1_R4_review_book.pdf',report['artifact_hashes'])
            (root/'output/fixture_r4/BM1_R4_review_book.pdf').write_bytes(b'replaced')
            with self.assertRaisesRegex(RuntimeError,'Artifact missing/changed'):require_report(report,ctx,root=root)

if __name__=='__main__': unittest.main()
