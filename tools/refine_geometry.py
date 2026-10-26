"""Explicit corrections from first exact-solid collision run.
Run once after seeding. Normal rebuild reads corrected geometry.json directly.
"""
import json,copy
from pathlib import Path
R=Path(__file__).resolve().parents[1];p=R/'data/geometry.json';data=json.loads(p.read_text(encoding='utf-8'));items=data['instances'];d={i['instance_id']:i for i in items};changes=[]
def B(s,at):return dict(op='box',size=s,at=at)
def CY(r,h,at,axis=None):
    s=dict(op='cylinder',radius=r,height=h,at=at)
    if axis:s['rotate']=([0,1,0],90) if axis=='x' else ([1,0,0],90)
    return s
def cut(a,*b):return dict(op='cut',children=[a,*b])
def un(*s):return dict(op='union',children=list(s))
def change(id,shape,reason):d[id]['shape']=shape;changes.append((id,reason))
def trim(a,b,reason):change(a,cut(d[a]['shape'],copy.deepcopy(d[b]['shape'])),reason)
def new(base,suffix,name,shape,parent):
    original=next(i for i in items if i['part_id']==base);x={**original,'instance_id':base+'-'+suffix,'derived_id':base+'-'+suffix,'name':name,'shape':shape,'parent':parent};items.append(x);d[x['instance_id']]=x

# Miter/seat the structural joints; this removes material only at explicit mating interfaces.
for side in ['L','R']:
    trim('PRT-0501-C__'+side,'PRT-0501-A','过渡筋端面按前板接合面修剪')
    trim('PRT-0501-C__'+side,'PRT-0501-B','过渡筋端面按尾板接合面修剪')
    trim('PRT-0501-D__'+side,'PRT-0501-E__'+side,'侧筋改为端面对接')
    trim('PRT-0501-E__'+side,'PRT-0501-F__'+side,'耳板接口改为台阶接合')
    cy='wheel_center_y' if side=='L' else '-wheel_center_y'
    for x in [-35,35]:change('PRT-0502-A__'+side+str(x),B([10,60,102],[45 if x>0 else -45,cy,-106]),'轴承托架外移，避开D70电机与D78压环；未缩小电机')
    trim('PRT-0506-C__'+side,'PRT-0506-A__'+side,'接线出口从定子外表面起')

trim('PRT-0701-C','PRT-0701-A','侧悬臂与托体端面对接')
change('PRT-0701-A',cut(d['PRT-0701-A']['shape'],B([35,70,8],['load_x-12',0,-12]),B([8.4,110,4.4],['load_x-26',0,-18])),'给实际开夹的夹指和连杆留完整滑动槽；宽体仍在轮面下')
trim('PRT-0704-A','PRT-0701-C','执行器安装板端面接合')
for side,sg in [('L',1),('R',-1)]:
    trim('PRT-0602-B__'+side,'PRT-0602-A__'+side,'固定筒架下梁端面对接立杆')
for z in [410,600]:
    ring=dict(op='ring',radius=55,inner=40.5,height=12,at=['load_x',0,z])
    change('PRT-0602-D__'+str(z),cut(ring,B([110,120,16],['load_x-55',0,z])),'快拆环分为前半固定和后半压带，两半不重叠')
    change('PRT-0602-E__'+str(z),cut(ring,B([110,120,16],['load_x+55',0,z])),'后半压带可先向后移除')
    for side,sg in [('L',1),('R',-1)]:
        ident='PRT-0602-C__'+side+str(z);change(ident,B([130,50,12],[-255,sg*60,z]),'托臂延伸到后杆并接触半环，建立连续连接')
        for mate in ['PRT-0602-A__'+side,'PRT-0602-D__'+str(z),'PRT-0602-E__'+str(z)]:trim(ident,mate,'明确接口止口切口')
for n in [1,2]:change('PRT-0605-A__'+str(n),B([60,6,6],[-245,46,303 if n==1 else 356]),'连杆改走管外，避免穿透未开窗筒壁')
change('PRT-0606-A',cut(B([58,26,10],[-226,0,128]),CY(43,14,['load_x',0,128]),d['PRT-0607-B']['shape']),'导套连接叉从移动滑块端面起，避开固定导轨')
trim('PRT-0607-C','PRT-0602-G','顶部桥板背板接口修剪')
trim('PRT-0607-C','PRT-0605__1','为分球执行器留实际接口缺口')

# Legs below frame, explicit pin bores; casters shifted inside rear frame, fork above tyre.
for sx in [-1,1]:
 for sy in [-1,1]:
    suf=str(sx)+'_'+str(sy);i=d['PRT-0103__'+suf];i['shape']['children'][0]['at'][2]=60
    hole=CY(4.2,200,[sx*300,sy*275,80]);i['shape']=cut(i['shape'],hole)
    change('PRT-0103-A__'+suf,CY(4,48,[sx*300,sy*275,80]),'正向销移动到上下梁接合区；两件均开销孔')
    for beam in ['PRT-0101-A__'+str(sy),'PRT-0101-B__'+str(sx)]:change(beam,cut(d[beam]['shape'],hole),'在支腿锁销处开真实孔')
for sy in [-1,1]:
    tire=d['PRT-0105-A__'+str(sy)]['shape'];tire['at']=[-235,sy*220,46]
    fork=un(B([50,40,6],[-235,sy*220,97]),B([50,6,48],[-235,sy*220+17,70]),B([50,6,48],[-235,sy*220-17,70]))
    change('PRT-0105-B__'+str(sy),cut(fork,CY(6.2,50,[-235,sy*220,46],'y')),'轮叉顶板抬高到轮胎上方，侧板有真实轴孔')
    new('PRT-0105','C__'+str(sy),'脚轮安装桥',cut(B([50,65,6],[-235,sy*250,97]),d['PRT-0101-A__'+str(sy)]['shape'],d['PRT-0105-B__'+str(sy)]['shape']),'WORLD_STATIC')

change('PRT-0301',cut(d['PRT-0301']['shape'],CY(11,20,[0,0,-336])),'为下置偏航传动轴开中心孔；供应商法兰孔仍未定义')
change('PRT-0303-B',cut(un(CY(42,10,[0,0,-355]),CY(42,10,[-165,0,-355]),B([165,84,10],[-82.5,0,-355])),un(CY(39,14,[0,0,-355]),CY(39,14,[-165,0,-355]),B([165,78,14],[-82.5,0,-355]))),'偏航驱动改为板下概念带环，避免刚性杆穿基座')
change('PRT-0303-A',CY(10,60,[-165,0,-320]),'输入轴从电机顶面起，不穿入带环')
new('PRT-0303','C','偏航输出轴候选',CY(10,50,[0,0,-330]),'YAW_CARRIER')
new('PRT-0303','D','偏航输出连接臂',cut(B([110,20,10],[0,0,-305]),CY(10,14,[0,0,-305])),'YAW_CARRIER')
for x,n in [(-165,'E'),(0,'F')]:new('PRT-0303',n,'偏航带轮候选',dict(op='ring',radius=39,inner=10,height=10,at=[x,0,-355]),'FIXED_HEAD_CARRIER' if x else 'YAW_CARRIER')
trim('PRT-0303-D','PRT-0302-B','输出连臂端面接合转圈')
trim('PRT-0403-A','PRT-0403','俯仰联轴器从执行器外表面起')
for side in ['L','R']:trim('PRT-0801-A__'+side,'PRT-0501-E__'+side,'侧罩为耳板连接留缺口')
# Tail shell slot lets carriage side release linkage pass through its full stroke.
change('PRT-0801-C__R',cut(d['PRT-0801-C__R']['shape'],B([280,12,14],[-115,-53.5,-16])),'后罩为滑台侧置释放连杆开连续运动槽；防伸入能力待验证')
change('PRT-0802',cut(d['PRT-0802']['shape'],CY(12,10,[0,185,0],'y')),'检查窗为短耳轴留孔；孔处需要防护盖验证')
change('PRT-1003',cut(d['PRT-1003']['shape'],B([13,86,172],[-120,0,780])),'终端夹架开真实设备容纳腔，保留夹宽概念')
sensor=[('SEN-03',[-235,32,-72]),('SEN-04',[-225,43,-72]),('SEN-05',[-195,0,-88]),('SEN-07',[90,0,-360])]
for n,pos in sensor:change('PRT-0905__'+n,B([30,20,20],pos),'功能探头移到结构之外；检测光路/型号待选型')
p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
(R/'reports/design_changes.md').write_text('# 几何修正记录\n\n全部新增尺寸为 concept。保留原尺寸、未缩小电机/羽毛裙、未以隐藏部件消除干涉。\n\n首次精确实体检查发现77组静态相交，以下为逐项处理：\n\n'+'\n'.join('- '+a+'：'+b for a,b in changes)+'\n\n后续状态以最终碰撞报告为准；接口修剪不等于加工/强度验证。\n',encoding='utf-8')
print('Applied',len(changes),'explicit corrections')
