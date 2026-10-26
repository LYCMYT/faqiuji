import json,copy
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'data/geometry.json';g=json.loads(p.read_text(encoding='utf-8'));items=g['instances'];d={x['instance_id']:x for x in items}
def B(s,at):return dict(op='box',size=s,at=at)
def C(r,h,at):return dict(op='cylinder',radius=r,height=h,at=at)
def ring(ro,ri,h,at):return dict(op='ring',radius=ro,inner=ri,height=h,at=at)
def cut(s,*others):return dict(op='cut',children=[s,*others])
def un(*s):return dict(op='union',children=list(s))
def setshape(id,s):d[id]['shape']=s
def add(base,suf,name,shape,parent):
 x={**next(i for i in items if i['part_id']==base),'instance_id':base+'-'+suf,'derived_id':base+'-'+suf.split('__')[0],'name':name,'shape':shape,'parent':parent};items.append(x);d[x['instance_id']]=x
for side,sg in [('L',1),('R',-1)]:
 for z in [410,600]:
    # A fork side arm ends against its collar. It is ONE connected solid and does not cross the tube bore.
    ident='PRT-0602-C__'+side+str(z)
    s=un(B([130,20,12],[-255,sg*60,z]),B([20,35,12],[-300,sg*72.5,z]))
    s=cut(s,C(55,16,['load_x',0,z]),d['PRT-0602-A__'+side]['shape'])
    setshape(ident,s)
for n in [1,2]:setshape('PRT-0605-A__'+str(n),cut(d['PRT-0605-A__'+str(n)]['shape'],d['PRT-0605__'+str(n)]['shape']))
for sx in [-1,1]:
 for sy in [-1,1]:
    id='PRT-0103__'+str(sx)+'_'+str(sy);setshape(id,cut(d[id]['shape'],C(6.5,100,[sx*425,sy*400,60])))
setshape('PRT-0905__SEN-03',B([30,20,20],[-245,-35,-88]))

# Put yaw belt ABOVE the support plate, so it cannot wrap through the square inner mast.
setshape('PRT-0303',B(['P0303_x','P0303_y','P0303_z'],[-250,0,-350]))
setshape('PRT-0303-A',C(10,30,[-250,0,-295]))
setshape('PRT-0303-B',cut(un(C(88,8,[0,0,-284]),C(88,8,[-250,0,-284]),B([250,176,8],[-125,0,-284])),un(C(86,12,[0,0,-284]),C(86,12,[-250,0,-284]),B([250,172,12],[-125,0,-284]))))
setshape('PRT-0303-C',ring(63.5,45,12,[0,0,-294]))
setshape('PRT-0303-D',ring(86,64,2,[0,0,-289]))
setshape('PRT-0303-E',ring(86,10,8,[-250,0,-284]))
setshape('PRT-0303-F',ring(86,45,8,[0,0,-284]))
setshape('PRT-0401-A',cut(d['PRT-0401-A']['shape'],C(64,14,[0,0,-295])))
add('PRT-0303','G','偏航电机支座',B([100,170,8],[-250,0,-394]),'FIXED_HEAD_CARRIER')
for sy in [-1,1]:add('PRT-0303','H__'+str(sy),'电机支座侧连接',B([100,8,34],[-250,sy*81,-373]),'FIXED_HEAD_CARRIER')

# Replace split slider with a connected U-profile and keep the carriage plate continuous.
setshape('PRT-0703-C',un(B([36,8,8],['load_x',11,-24]),B([36,8,8],['load_x',-11,-24]),B([36,30,2],['load_x',0,-19])),)
# Jaw rods are guided above the low plate; ball head doesn't reach their rear x-position.
for side,sg in [('L',1),('R',-1)]:setshape('PRT-0702-A__'+side,B([8,36.5,4],['load_x-26',sg*18.25,-10]))
setshape('PRT-0701-A',cut(B([60,32,5],['load_x-15',0,-15.5]),B([35,70,8],['load_x-12',0,-12])))
# Tall strips alongside the tail movement slot remain connected by rear upright.
setshape('PRT-0801-C__R',un(d['PRT-0801-C__R']['shape'],B([6,3,75],[-232,-53.5,-12.5])))

# Real candidate fasteners through designed slots and front-plate holes (not supplier patterns).
for side,sg in [('L',1),('R',-1)]:
 cy='wheel_center_y' if sg>0 else '-wheel_center_y'
 for x in [-36,36]:
  for yy in [-24,24]:
    at=[x,f'{cy}+({yy})',-169]
    setshape('PRT-0501-A',cut(d['PRT-0501-A']['shape'],C(3.5,30,at)))
    shape=un(C(3,28,at),C(5,4,[x,at[1],-155]))
    add('PRT-0502',f'FAST__{side}_{x}_{yy}','轮距滑座紧固候选M6',shape,'MOVING_HEAD')
    add('PRT-0502',f'NUT__{side}_{x}_{yy}','滑座螺母候选',ring(5,3,5,[x,at[1],-183.5]),'MOVING_HEAD')

# Nominal wiring paths and explicit maintenance-volume data; dynamic bend validation remains open.
add('PRT-0903','WIRE_A','固定立柱线束概念路径',dict(op='wire',radius=3,points=[[75,0,300],[75,0,1000],[120,0,1050],[155,0,1050],[155,0,1120],[110,0,1130]]),'WORLD_STATIC')
setshape('PRT-0803-A',cut(d['PRT-0803-A']['shape'],C(5,12,[75,0,369])))
add('PRT-0704','WIRE_A','滑台柔性回路概念路径',dict(op='wire',radius=2,points=[[-240,-75,-65],[-200,-95,-100],[-140,-95,-100],[-100,-75,-65],[-150,-65,-50]]),'MOVING_HEAD')
services=[dict(id='SERVICE_TUBE',part_id='PRT-0601',direction_mm=[-240,0,0],status='后压带拆除后再后移；路径须检测'),dict(id='SERVICE_WHEEL',part_id='PRT-0505',direction_mm=[0,0,130],status='先拆上罩'),dict(id='SERVICE_ELECTRICAL',part_id='PRT-0902',direction_mm=[-500,0,0],status='先拆后门并解除接线'),dict(id='SERVICE_JAM',part_id='PRT-0701',direction_mm=[-150,0,0],status='停转、拆后罩；需工具可达验证')]
(R/'data/service_spaces.json').write_text(json.dumps(services,ensure_ascii=False,indent=2),encoding='utf-8')
p.write_text(json.dumps(g,ensure_ascii=False,indent=2),encoding='utf-8')
with (R/'reports/design_changes.md').open('a',encoding='utf-8') as f:f.write('\n第二轮：将偏航带传动上置并给U架中心开孔，避免绕过/穿过内立柱；修正脚端孔深和分球连杆；托臂改为连接叉；增加滑座紧固候选、真实孔与名义线束路径。线束柔性、传动张紧、连接细节仍需采购和样机验证。\n')
print('Round 2 geometry authored',len(items))
