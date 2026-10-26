import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'data/geometry.json';g=json.loads(p.read_text(encoding='utf-8'));d={x['instance_id']:x for x in g['instances']}
def B(s,at):return dict(op='box',size=s,at=at)
frame=dict(op='union',children=[B([60,110,8],[-280,0,275]),B([60,110,8],[-285,0,310]),B([8,8,27],[-305,45,292.5]),B([8,8,27],[-305,-45,292.5])])
d['PRT-0607-C']['shape']=dict(op='cut',children=[frame,d['PRT-0607-A']['shape'],d['PRT-0602-G']['shape'],d['PRT-0605__1']['shape'],d['PRT-0605__2']['shape']])
p.write_text(json.dumps(g,ensure_ascii=False,indent=2),encoding='utf-8')
with (R/'reports/design_changes.md').open('a',encoding='utf-8') as f:f.write('\n闸板全行程修正：导轨顶部连接桥改为上下横梁与侧立柱组成的门形件。下梁顶279、闸板281…287、上梁底306；侧柱Y±45避开闸板Y±32.5，从真实实体中打开撤闸通道。\n')
