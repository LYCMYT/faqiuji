import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'data/geometry.json';g=json.loads(p.read_text(encoding='utf-8'));d={i['instance_id']:i for i in g['instances']}
def B(s,at):return dict(op='box',size=s,at=at)
def cut(a,*b):return dict(op='cut',children=[a,*b])
for side,sg in [('L',1),('R',-1)]:
    d['PRT-0603__'+side]['shape']['at'][2]=392
    d['PRT-0602-F__'+str(sg)]['shape']=cut(B([170,6,170],[-225,sg*72,365]),B([22,12,16],['load_x',sg*72,392]),B([150,14,14],[-250,sg*72,410]))
d['PRT-0601']['shape']=cut(dict(op='ring',radius='tube_od/2',inner='tube_id/2',height='tube_length',at=['load_x',0,'tube_bottom_z_H+tube_length/2']),B([90,66,8],['load_x',0,284]),B([20,100,14],['load_x',0,392]))
d['PRT-0602-G']['shape']=cut(d['PRT-0602-G']['shape'],B([12,68,10],[-313,0,284]))
d['PRT-0605__2']['shape']['at'][2]=369.5
d['PRT-0605-A__2']['shape']=cut(B([60,6,6],[-245,46,392]),d['PRT-0605__2']['shape'])
d['PRT-0905__SEN-04']['shape']=B([30,20,20],['load_x-100',-65,-35])
# Lead terminates on the release actuator surface without penetrating its candidate envelope.
wire=d['PRT-0704-WIRE_A'];wire['shape']['points'][-1]=['load_x-55+slide',-65,-52];wire['dynamic_path']=wire['shape']['points']
p.write_text(json.dumps(g,ensure_ascii=False,indent=2),encoding='utf-8')
with (R/'reports/design_changes.md').open('a',encoding='utf-8') as f:f.write('\n分球路径补检修正：上留球夹由H+330移至H+392，其最低点386高于待释放单球（球头中心H+300、裙顶383）3mm；扩展试验盒并重新开管窗/侧壁行程槽，后板开闸板撤出槽。此举仅保证所示单球下落路径不被上夹横挡；上球堆实际套叠与夹持界面尚未知，U03不关闭，不宣称实现可靠单球分离。\n')
