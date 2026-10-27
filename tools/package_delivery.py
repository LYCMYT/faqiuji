from pathlib import Path
import zipfile,json,hashlib,argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.build_context import BuildContext
from tools.validate_release import require_report,validate_release,validate_review_bundle
R=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--revision',choices=['R4'],default='R4')
group=parser.add_mutually_exclusive_group(required=True);group.add_argument('--release-proof',type=Path);group.add_argument('--review-proof',type=Path);args=parser.parse_args()
review=bool(args.review_proof);proof=json.loads((args.review_proof or args.release_proof).read_text(encoding='utf-8'))
ctx=BuildContext(**{k:proof[k] for k in BuildContext.__dataclass_fields__})
if review:
    if ctx.scope!='review' or proof.get('status')!='REVIEW_ONLY' or proof.get('full_release_allowed') is not False:raise RuntimeError('Not a review-only proof')
    validated=validate_review_bundle(R,ctx.for_stage('build','full'))
else:
    if ctx.scope!='full':raise RuntimeError('Cannot publish static/core diagnostics')
    require_report(proof,ctx.for_stage('release'),['release_gate'],R)
    validated=validate_release(R,ctx)
if proof.get('contract_id')!=validated['contract_id'] or proof.get('artifact_hashes')!=validated['artifact_hashes']:raise RuntimeError('Proof does not match fixed contract/current artifacts')
if not proof.get('artifact_hashes'):raise RuntimeError('Empty artifact contract')
from tools.delivery_files import collect_delivery_files
files=collect_delivery_files(R,ctx.run_id);manifest=[]
for p in files:manifest.append(dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(R/'delivery_manifest.json').write_text(json.dumps(dict(files=manifest,excluded='installed runtimes, caches, raw animation frames and PDF review contact sheets; final artifacts retained'),ensure_ascii=False,indent=2),encoding='utf-8')
files.append(R/'delivery_manifest.json')
dest=R.parent/(f'BM1_V02_{args.revision}_Review_Candidate_BLOCKED.zip' if review else f'BM1_V02_{args.revision}_Engineering_Delivery.zip')
with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files:z.write(p,Path('BM1_V02_Engineering')/p.relative_to(R))
with zipfile.ZipFile(dest) as z:
    err=z.testzip()
    if err is not None:raise RuntimeError('ZIP CRC failure: '+err)
    for entry in manifest:
        raw=z.read('BM1_V02_Engineering/'+entry['path'])
        if len(raw)!=entry['bytes'] or hashlib.sha256(raw).hexdigest()!=entry['sha256']:raise RuntimeError('ZIP manifest hash mismatch: '+entry['path'])
print('ZIP VERIFIED',dest,len(files),'files',round(dest.stat().st_size/1024/1024,2),'MiB')

dest.with_suffix(dest.suffix+'.sha256').write_text(hashlib.sha256(dest.read_bytes()).hexdigest()+'  '+dest.name+'\n',encoding='utf-8')
