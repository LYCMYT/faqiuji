import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'data/geometry.json';g=json.loads(p.read_text(encoding='utf-8'));d={i['instance_id']:i for i in g['instances']}
def B(s,at):return dict(op='box',size=s,at=at)
def cut(a,b):return dict(op='cut',children=[a,b])
def hole(at):return dict(op='cylinder',radius=4.5,height=100,at=at,rotate=([0,1,0],90))
d['PRT-0905__SEN-04']['shape']=B([30,20,20],['load_x-75',-65,-60])
wire=d['PRT-0903-WIRE_A'];wire['dynamic_height']=True;wire['shape']['points']=[[75,0,300],[75,20,400],[0,20,400],[0,20,'head_axis_height-355'],[80,20,'head_axis_height-355']];wire['dynamic_path']=wire['shape']['points']
d['PRT-0201']['shape']=cut(d['PRT-0201']['shape'],hole([0,20,400]));d['PRT-0202']['shape']=cut(d['PRT-0202']['shape'],hole([0,20,-355]));d['PRT-0803-A']['shape']=cut(d['PRT-0803-A']['shape'],B([10,30,12],[75,10,369]))
wire=d['PRT-0704-WIRE_A'];wire['dynamic_slide']=True;wire['shape']['points']=[[-235,-95,-60],[-280,-95,-70],['load_x-70+slide',-95,-80],['load_x-55+slide',-65,-50]];wire['dynamic_path']=wire['shape']['points']
p.write_text(json.dumps(g,ensure_ascii=False,indent=2),encoding='utf-8')
with (R/'reports/design_changes.md').open('a',encoding='utf-8') as f:f.write('\n路径修正：将释放反馈候选体移到执行器后下侧；升降线束改为立柱内通道并开进出线孔，端点随H重建；滑台线束端点随J05变化重建。线束采用分段扫掠包络，未保持恒定弧长，弯曲半径、拖链和实际余量仍待定，不能据此判定线束耐久性。\n')
