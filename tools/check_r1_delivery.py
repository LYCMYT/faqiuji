"""Final artifact/evidence audit; does not upgrade physical acceptance."""
from pathlib import Path
import json,hashlib,subprocess,sys
import pymupdf
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text(encoding='utf-8'))
v=read('reports/validation.json');g=hashlib.sha256((R/'data/geometry.json').read_bytes()).hexdigest()
assert v['revision']=='V0.2-R1'
assert v['geometry_sha256']==v['static']['geometry_sha256']==v['motion']['geometry_sha256']==g
assert v['all_native_solids_valid'] and v['step_pass'] and v['all_main_steps_complete']
assert v['main_items']==44 and v['physical_instances']==187 and v['cad_instances']==189
assert v['static']['unresolved_pairs']==v['motion']['unresolved_pairs']==0
assert not v['static']['errors'] and not v['motion']['errors']
assert v['r1_service']['all_paths_passed'] and v['r1_service']['geometry_sha256']==g
assert not v['r1_bench']['static_intersections']
assert v['engineering_production_acceptance'] is False and v['prototype_tests_performed'] is False
assert len(v['unresolved_ids'])==10 and not v['missing_required_files']
assert v['mass_evaluation']['status']=='BLOCKED_MISSING_EVIDENCE'
e=read('output/engineering/evidence_register.json');assert not e['physical_measurements'] and not e['supplier_confirmations'] and not e['prototype_test_results']
required=['output/engineering/BM1_R1_separator_bench.step','output/engineering/BM1_R1_engineering_manual.pdf','output/engineering/shuttle_measurements_BLANK.csv','output/engineering/supplier_interface_RFQ.csv','output/engineering/prototype_runs_BLANK.csv','output/engineering/control_functional.svg','output/animation/BM1_R1_cassette_service.mp4','control/feed_cycle.py','engineering/evaluate.py']
for p in required:assert (R/p).is_file() and (R/p).stat().st_size>0,p
pdfs=[]
for rel,expected in [('output/BM1_V0_design_book.pdf',152),('output/engineering/BM1_R1_engineering_manual.pdf',18)]:
    f=R/rel;d=pymupdf.open(f);assert len(d)==expected;issues=[]
    for n,page in enumerate(d):
        pix=page.get_pixmap(matrix=pymupdf.Matrix(.3,.3));assert pix.width and pix.height
        for b in page.get_text('blocks'):
            if b[0]<0 or b[1]<0 or b[2]>page.rect.width or b[3]>page.rect.height:issues.append(n+1)
    assert not issues;pdfs.append(dict(file=rel,pages=len(d),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),out_of_page_text=issues))
media=[]
for f in sorted((R/'output/animation').glob('*.mp4')):
    metadata=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name,width,height,nb_frames','-show_entries','format=duration','-of','json',str(f)]))
    subprocess.run(['ffmpeg','-v','error','-i',str(f),'-f','null','-'],capture_output=True,check=True)
    media.append(dict(file=f.name,metadata=metadata,all_frames_decoded=True))
assert len(media)==3
viewer=read('reports/viewer_validation.json');assert viewer['loaded'] and viewer['meshes']==187 and not viewer['js_errors']
result=dict(revision='V0.2-R1',geometry_sha256=g,required_artifacts_present=True,pdfs=pdfs,media=media,viewer=viewer,all_native_geometry_and_roundtrips_passed=True,physical_acceptance=False,scope='File integrity and listed discrete digital checks only; physical inputs remain missing.')
(R/'reports/r1_delivery_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(R/'reports/media_validation.json').write_text(json.dumps(dict(decode_all_frames_passed=True,files=media),ensure_ascii=False,indent=2),encoding='utf-8')
(R/'reports/visual_review.json').write_text(json.dumps(dict(revision='V0.2-R1',pdfs=pdfs,model_contacts_reviewed=['001','021','041','061','081','101','121','141'],manual_contacts_reviewed=['01','09','17'],scope='All contact sheets visually reviewed; selected full-size figures checked. Layout review, not engineering approval.',findings='No evident missing illustrations or clipping; all pages also rendered and text bounds checked.'),ensure_ascii=False,indent=2),encoding='utf-8')
print('R1 DELIVERY CHECK PASS: 152+18 PDF pages; 3 complete MP4 decodes; native/roundtrip/motion/service reports current; physical acceptance FALSE.')
