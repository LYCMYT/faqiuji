import json,copy
from pathlib import Path
R=Path(__file__).resolve().parents[1];path=R/'data/geometry.json';g=json.loads(path.read_text(encoding='utf-8'));d={i['instance_id']:i for i in g['instances']}
def B(size,at):return dict(op='box',size=size,at=at)
def C(r,h,at):return dict(op='cylinder',radius=r,height=h,at=at)
def cut(a,*b):return dict(op='cut',children=[a,*b])
def un(*s):return dict(op='union',children=list(s))
for side,sg in [('L',1),('R',-1)]:
    d['PRT-0702-A__'+side]['shape']=cut(un(B([8,36.5,4],['load_x-35',sg*18.25,-10]),B([10,8,4],['load_x-30',sg*18.25,-10])),d['PRT-0702__'+side]['shape'])
    for z in [410,600]:
        key='PRT-0602-C__'+side+str(z);d[key]['shape']=cut(d[key]['shape'],B([20,20,970],[-310,sg*85,125]))
    cy='wheel_center_y' if sg>0 else '-wheel_center_y'
    for x in [-36,36]:
      for yy in [-24,24]:
        val=28 if yy>0 else -28;newy=f'{cy}+({val})'
        bolt='PRT-0502-FAST__'+side+'_'+str(x)+'_'+str(yy);nut=bolt.replace('FAST','NUT')
        for ch in d[bolt]['shape']['children']:ch['at'][1]=newy
        d[nut]['shape']['at'][1]=newy
        d['PRT-0501-A']['shape']=cut(d['PRT-0501-A']['shape'],C(3.5,30,[x,newy,-169]))
        tower='PRT-0502-A__'+side+str(35 if x>0 else -35)
        d[tower]['shape']=cut(d[tower]['shape'],C(6,12,[x,newy,-153]))
    key='PRT-0303-H__'+str(sg);mate='PRT-0602-B__'+side;d[key]['shape']=cut(d[key]['shape'],d[mate]['shape'])
d['PRT-0801-C__R']['shape']=un(cut(B([154,3,75],[-167,-53.5,-12.5]),B([280,12,14],[-115,-53.5,-16])),B([6,3,75],[-241,-53.5,-12.5]))
d['PRT-0905__SEN-07']['shape']=B([30,20,20],[90,45,-360])
path.write_text(json.dumps(g,ensure_ascii=False,indent=2),encoding='utf-8')
with (R/'reports/design_changes.md').open('a',encoding='utf-8') as f:f.write('\n第三轮：夹指连接改为后端L形连杆；后罩检修槽的闭合边后移9mm到全行程外；M6候选锁紧位置调整到槽内Y±28，并增加工具凹口；筒架接合去除管内孤立材料；消除线束与传感候选体相交。\n')
print('Round 3 corrections recorded')
