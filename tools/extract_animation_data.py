import ast,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'blender/build_scene.py';s=p.read_text(encoding='utf-8');t=ast.parse(s)
import sys; sys.path.insert(0,str(R))
from tools.input_manifest import generated_path, metadata_path
n=next(n for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='states' for x in n.targets))
a=ast.literal_eval(n.value);generated_path(R,'animation_keyframes.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf-8')
lines=s.splitlines();lines[n.lineno-1:n.end_lineno]=["states=json.loads((R/'data/animation_keyframes.json').read_text(encoding='utf-8'))"]
p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
