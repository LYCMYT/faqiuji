from pathlib import Path
import zipfile,json,hashlib,argparse
R=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--revision',choices=['R1','R2','R3'],default='R3');args=parser.parse_args()
include=['cad','blender','control','engineering','data','docs','licenses','viewer','reports','output','input']
excluded_dirs={'__pycache__','pdf_review','feed','explode','service','frames'}
files=[]
for folder in include:
    for p in (R/folder).rglob('*'):
        if not p.is_file() or any(v in excluded_dirs for v in p.relative_to(R).parts):continue
        if p.suffix in ['.blend1','.brep']:continue
        if p.suffix=='.log' and p.name not in ['r1_review_red.log','r1_review_green.log']:continue
        if 'output/mesh/' in p.as_posix():continue # rebuild creates caches from data; not needed for viewer
        if p.name in ['feed_preview_131.png','feed_preview_66.png']:continue
        files.append(p)
files += [p for p in (R/'tools').glob('*.py') if not p.name.startswith('debug_')]
files += [p for p in (R/'tests').glob('*.py')]
files += [R/'README_DELIVERY.md',R/'requirements-lock.txt',R/'启动查看器.cmd',R/'重建模型.cmd']
files=sorted(set(files));manifest=[]
for p in files:manifest.append(dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(R/'delivery_manifest.json').write_text(json.dumps(dict(files=manifest,excluded='installed runtimes, caches, raw animation frames and PDF review contact sheets; final artifacts retained'),ensure_ascii=False,indent=2),encoding='utf-8')
files.append(R/'delivery_manifest.json')
dest=R.parent/f'BM1_V02_{args.revision}_Engineering_Delivery.zip'
with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in files:z.write(p,Path('BM1_V02_Engineering')/p.relative_to(R))
with zipfile.ZipFile(dest) as z:
    err=z.testzip();assert err is None,err
print('ZIP VERIFIED',dest,len(files),'files',round(dest.stat().st_size/1024/1024,2),'MiB')
