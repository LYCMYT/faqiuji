"""Delivery membership: immutable inputs/evidence override derived-cache filters."""
from pathlib import Path
from tools.build_context import code_paths
from tools.input_manifest import classify_paths

def collect_delivery_files(root,run_id):
    root=Path(root);files=[]
    excluded={'__pycache__','pdf_review','feed','explode','service','frames'}
    for folder in ('cad','blender','control','engineering','data','docs','licenses','viewer','reports','output','input','evidence'):
        for path in (root/folder).rglob('*'):
            relative=path.relative_to(root)
            if not path.is_file() or any(v in excluded for v in relative.parts):continue
            if path.suffix in ('.blend1','.brep'):continue
            if path.suffix=='.log' and path.name not in ('r1_review_red.log','r1_review_green.log') and run_id not in path.parts and 'cold_core' not in path.parts:continue
            if any(relative.as_posix().startswith(prefix) for prefix in ('output/mesh/','output/builds/','output/history/')):continue
            if path.name in ('feed_preview_131.png','feed_preview_66.png'):continue
            files.append(path)
    files += [root/name for name in code_paths(root)]
    # Original .log/.brep files are evidence, regardless of generated-cache suffixes.
    inputs=classify_paths(root)
    files += [root/name for group in ('authoritative','evidence_index') for name in inputs[group]]
    return sorted(set(files))
