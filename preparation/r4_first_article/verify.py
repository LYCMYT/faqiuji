"""Read-only bundle validation plus real CLI overwrite-regression checks."""
import csv,hashlib,json,subprocess,sys,tempfile,zipfile
from pathlib import Path
import pymupdf

R=Path(__file__).resolve().parents[2]
P=Path(__file__).resolve().parent
O=P/'kit_20261027_final'
def require(value,message):
    if not value:raise RuntimeError(message)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(name):return json.loads((O/name).read_text(encoding='utf-8'))
def rows(name):
    with (O/'templates'/(name+'.csv')).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def main():
    manifest=read('manifest.json');source=read('source_binding.json')
    for field in ['manufacturing_release','first_article_release','automatic_operation_release','physical_trials_performed']:require(source[field] is False,field)
    for name,expected in source['source_files'].items():
        require(digest(R/name)==expected,'Source drift: '+name)
        require(digest(O/'reference'/name)==expected,'Copy drift: '+name)
    require(digest(P/'build.py')==source['generator_sha256'],'Generator changed')
    require(digest(P/'jaw_drawings.py')==source['helper_sha256'],'Helper changed')
    for item in manifest['files']:
        p=O/item['path'];require(p.stat().st_size==item['bytes'] and digest(p)==item['sha256'],'Manifest mismatch '+item['path'])
    sys.path.insert(0,str(R))
    from tools.build_context import verify_content_context
    proof=json.loads((R/'reports/r4_review_bundle.json').read_text(encoding='utf-8'));verify_content_context(R,proof)
    require(source['base_run_id']==proof['run_id'],'Base run mismatch')
    expected={f'PRT-0603-R3-R{r}-{s}' for r in [23,26,29,32] for s in ['L','R']}|{'PRT-0701-R4-A','PRT-0602-R3-BASE'}
    require({row['family'] for row in rows('quote_reply')}==expected,'Part coverage')
    require({row['family'] for row in rows('supplier_reply')}==expected,'DFM coverage')
    for row in rows('quote_reply'):
        for key in ['quantity','unit_price_CNY','lead_days','supplier']:require(row[key]=='','Invented procurement field')
        require(row['approval']=='OPEN','Quote approval')
    for row in rows('axis_parameters'):
        for key in ['speed','force_or_current_limit','arrival_tolerance','stop_distance_limit']:require(row[key]=='','Invented hardware limit')
    require(all(row['decision']=='BLOCKED' for row in rows('gate_signoff')),'Gate pre-approved')
    require(len(rows('input_return'))==12,'Input list incomplete')
    io={row['signal']:row for row in rows('io_review')}
    for signal in ['slide_target_mm','guide_target_mm','clamp_target','gate_target','upper_target','safe_intent.slide','safe_intent.catch_clamp','command_id','cycle_id','accepted_id','completed_id','sample_id']:
        require(signal in io,'Missing interface '+signal)
    require(io['enable_wheels']['applicability']=='NOT_APPLICABLE_NO_WHEELS','Wheel scope')
    require(io['capture_detected']['applicability'].startswith('NOT_RUN'),'Capture scope')
    additional=read('additional_jaw_features.json');require(len(additional)==7,'Additional jaw count')
    for row in additional:
        require(row['critical_fit_tolerance'] is None and row['first_article_release'] is False,'Jaw release')
        require(len(row['holes_local_mm'])==2,'Jaw hole count')
    require(len(list((O/'reference/output/fixture_r4/step/parts').glob('*.step')))==10,'STEP count')
    raw_names=['ball_measurements','stack_force','inspection','manual_checks','cycle_log','stop_tests','nonconformance','evidence_index','run_summary']
    require(all(not rows(name) for name in raw_names),'Fabricated actual records')
    zip_path=O.with_suffix('.zip')
    with tempfile.TemporaryDirectory(prefix='bm1-prep-unpack-') as td,zipfile.ZipFile(zip_path) as z:
        target=Path(td).resolve();require(z.testzip() is None,'ZIP CRC')
        for name in z.namelist():require((target/name).resolve().is_relative_to(target),'Unsafe zip member')
        z.extractall(target)
        for item in manifest['files']:
            p=target/O.name/item['path'];require(p.stat().st_size==item['bytes'] and digest(p)==item['sha256'],'Unpack mismatch')
        with pymupdf.open(target/O.name/'BM1_R4_First_Article_Low_Speed_Preparation.pdf') as pdf:
            pages=len(pdf);require(pages==23,'Unexpected pagination')
            overflow=[]
            for i,page in enumerate(pdf):
                for b in page.get_text('blocks'):
                    if b[0]<30 or b[1]<20 or b[2]>page.rect.width-25 or b[3]>page.rect.height-15:overflow.append(i+1)
            require(not overflow,'PDF text overflow')
    cases=[]
    with tempfile.TemporaryDirectory(prefix='overwrite-regression-',dir=P) as td:
        base=Path(td)
        for suffix in ['.zip','.zip.sha256']:
            dest=base/('existing_zip' if suffix=='.zip' else 'existing_checksum');sentinel=dest.with_suffix(suffix);sentinel.write_bytes(b'KEEP ORIGINAL DELIVERY')
            before=digest(sentinel)
            p=subprocess.run([sys.executable,'-O',str(P/'build.py'),'--out',str(dest)],capture_output=True,text=True)
            require(p.returncode!=0 and 'Refusing existing ZIP or checksum' in p.stderr,'Overwrite not rejected')
            require(digest(sentinel)==before and not dest.exists(),'Overwrite damaged delivery');cases.append(suffix+' rejected under -O')
        p=subprocess.run([sys.executable,'-O',str(P/'build.py'),'--out',str(O)],capture_output=True,text=True)
        require(p.returncode!=0 and 'Refusing existing output' in p.stderr,'Existing output not rejected');cases.append('existing output rejected under -O')
    result=dict(status='PASS_PREPARATION_ONLY',base_run_id=source['base_run_id'],source_copies=len(source['source_files']),manifest_files=len(manifest['files']),zip_sha256=digest(zip_path),zip_crc=True,independent_unpack_hashes=True,pdf_pages=pages,pdf_overflow=overflow,additional_jaw_sheets=7,part_step_files=10,assembly_step_files=1,templates=16,io_rows=len(io),input_requests=12,overwrite_regressions=cases,raw_records_blank=True,R4_source_unchanged=True,physical_testing='NOT_RUN',manufacturing_release=False,first_article_release=False,automatic_operation_release=False)
    (P/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
