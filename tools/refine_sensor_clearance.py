import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'data/geometry.json';g=json.loads(p.read_text(encoding='utf-8'));d={i['instance_id']:i for i in g['instances']}
d['PRT-0905__SEN-01']['shape']['at'][2]=250
d['PRT-0905__SEN-08_R']['shape']['at'][2]=-260
p.write_text(json.dumps(g,ensure_ascii=False,indent=2),encoding='utf-8')
with (R/'reports/design_changes.md').open('a',encoding='utf-8') as f:f.write('\n探头最终净空修正：导套上位探头移至H+250，避免新门形桥；新增右偏航限位候选头抬至H-260，避开偏航带环扫掠。所有探头仍为功能位置候选，真实安装方式待选型。尺寸验收改用不依赖三角网格的OCCT解析包围盒，避免显示网格偏差被误计入工程尺寸。\n')
