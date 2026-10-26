"""R4 ownership: historical snapshots and real evidence are read-only."""
from pathlib import Path
import hashlib, json, warnings
LEGACY_DERIVED = frozenset({'instances.json','demo_states.json','animation_keyframes.json','page_index.json','page_index_engineering.json','deliverable_manifest.json','document_validation.json','bom.csv'})
def classify_paths(root: Path) -> dict[str,list[str]]:
    root=Path(root)
    def files(folder):
        return sorted(p.relative_to(root).as_posix() for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    return {'authoritative':files('data'),'derived':files('output'),'evidence_index':files('evidence')}
def snapshot_inputs(root):
    c=classify_paths(root)
    return {p:hashlib.sha256((Path(root)/p).read_bytes()).hexdigest() for p in c['authoritative']+c['evidence_index']}
def require_unchanged(root,before):
    after=snapshot_inputs(root)
    changed=sorted(p for p in set(before)|set(after) if before.get(p)!=after.get(p))
    if changed: raise RuntimeError('Authoritative/evidence files changed: '+', '.join(changed))
def generated_path(root,name):
    p=Path(root)/'output/generated_metadata'/name;p.parent.mkdir(parents=True,exist_ok=True);return p
def metadata_path(root,name,*,allow_legacy=True):
    p=Path(root)/'output/generated_metadata'/name
    if p.is_file():return p
    if allow_legacy and (Path(root)/'data'/name).is_file():
        warnings.warn('Read-only legacy R1-R3 metadata fallback: data/'+name,RuntimeWarning)
        return Path(root)/'data'/name
    raise FileNotFoundError('Regenerate metadata: '+str(p))
def initialize_input(path,value):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
