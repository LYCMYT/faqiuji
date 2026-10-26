"""One-time auditable concept-detail authoring. Normal rebuild NEVER runs this.
It preserves input data and writes all additional dimensions to data/geometry.json.
No supplier hole patterns or performance values are asserted.
"""
import json, math, importlib.util
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(n):return json.loads((R/'data'/n).read_text(encoding='utf-8'))
def write(n,o):(R/'data'/n).write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
parts={p['part_id']:p for p in read('parts.json')}; recipes=[]
def box(s,at=(0,0,0)):return dict(op='box',size=s,at=at)
def cyl(r,h,at=(0,0,0),axis=None):
    a=dict(op='cylinder',radius=r,height=h,at=at)
    if axis:a['rotate']=([1,0,0],90) if axis=='y' else ([0,1,0],90)
    return a
def ring(r,ri,h,at=(0,0,0),axis=None):
    a=cyl(r,h,at,axis);a.update(op='ring',inner=ri);return a
def cut(*children):return dict(op='cut',children=children)
def union(*children):return dict(op='union',children=children)
def tube(s,t,at):return cut(box(s,at),box([s[0]-2*t,s[1]-2*t,s[2]+2],at))
def add(pid,suffix,name,shape,parent='WORLD_STATIC',**kwargs):
    base='PRT-'+pid; main=parts.get(base); derived=base+('-'+suffix.split('__')[0] if suffix and not suffix.startswith('__') else '')
    iid=base+('-'+suffix if suffix and not suffix.startswith('__') else suffix)
    recipes.append({**dict(instance_id=iid,part_id=base,derived_id=derived,assembly_id=main['assembly_id'] if main else 'REFERENCE',name=name,parent=parent,shape=shape,color=main['color'] if main else '#E8D8A9',status='concept'),**kwargs})
W='MOVING_HEAD'; F='FIXED_HEAD_CARRIER'; Y='YAW_CARRIER'; C='CARRIAGE'

# A: measured invariants and explicitly separate presentation controls.
write('implementation.json',dict(status='concept',geometry_authority='geometry.json; arithmetic references design.json and parts.json',
    demo=dict(release_begin_x=-45,release_complete_x=-25,clamp_open_mm=14,upper_open_mm=24,gate_open_mm=85,fps=24,duration_seconds=22,rotation_rpm=18,notice='仅顺序演示；时间、转速、释放位置和出球轨迹未验证'),
    validation=dict(linear_step_mm=2,angular_step_deg=5,geometry_tolerance_mm=0.001,intersection_volume_threshold_mm3=0.01),
    coordinate_adapter='CAD mm Z-up -> mesh JSON mm Z-up -> Blender divide by 1000 only -> Blender GLB exporter Y-up; no other rotation',
    material_density_kg_m3=dict(aluminium_candidate=2700,steel_candidate=7850,polymer_candidate=1200)))

# B: stepped structural load path, distinct bearing housings and shafts.
add('0501','A','前宽承载板',box(['head_wide_x_max-head_wide_x_min',340,12],['(head_wide_x_max+head_wide_x_min)/2',0,-175]),W)
add('0501','B','后窄抬高尾板',box([145,'head_tail_y_half*2',12],[-162.5,0,'head_tail_support_z_H']),W)
for side,sg in [('L',1),('R',-1)]:
    add('0501','C__'+side,'阶梯过渡筋',box([12,12,137],[-90,sg*39,-112.5]),W)
    add('0501','D__'+side,'侧立筋',box([60,12,146],[30,sg*164,-96]),W)
    add('0501','E__'+side,'耳轴外伸连接板',box([60,42,12],[0,sg*182,-29]),W)
    add('0501','F__'+side,'短耳轴承力耳板',cut(box([60,12,60],[0,sg*200,-12]),cyl(9.1,16,[0,sg*200,0],'y')),W)
for x in [-215,-115]:add('0501','G__'+str(abs(x)),'轨道垫座',box([20,32,4],[x,0,-42]),W)
for side,sg in [('L',1),('R',-1)]:
    cy='wheel_center_y' if sg==1 else '-wheel_center_y'; wheel='WHEEL_LEFT' if sg==1 else 'WHEEL_RIGHT'
    plate=box([95,75,12],[0,cy,-163])
    slots=[box([7,16,16],[x,f'{cy}+({dy})',-163]) for x in [-36,36] for dy in [-24,24]]
    add('0502','__'+side,'可调轮距滑座',cut(plate,*slots),W)
    # Standoffs deliberately carry bearing from base instead of floating in space.
    for x in [-35,35]:add('0502','A__'+side+str(x),'轴承托架立柱',box([10,60,102],[x,cy,-106]),W)
    add('0502','B__'+side,'轴承托台',cut(box([80,60,8],[0,cy,-51]),cyl(12,12,[0,cy,-51])),W)
    add('0503','A__'+side,'轴承固定座包络',ring(22.5,7,29,[0,cy,-32.5]),W)
    add('0503','B__'+side,'主轴候选',cyl(7,55,[0,cy,-27.5]),wheel)
    add('0504','__'+side,'轮毂候选实体',ring('P0504_x/2',7,'wheel_width',[0,cy,0]),wheel)
    add('0505','__'+side,'弹性轮缘',ring('wheel_diameter/2','P0504_x/2','wheel_width',[0,cy,0]),wheel,color='#30353E')
    add('0506','A__'+side,'电机定子候选',cyl('motor_diameter_visual/2','motor_length_visual',[0,cy,'(motor_z_min_H+motor_z_max_H)/2']),W)
    add('0506','B__'+side,'电机可调压环',ring(39,'motor_diameter_visual/2',8,[0,cy,-151]),W)
    add('0506','C__'+side,'接线出口候选',box([12,12,16],[0,f'{cy}+({sg*40})',-120]),W)

# Real rail/slider and physical open-clamp translations; wide body stays below wheel plane.
add('0703','A','固定轨',box(['P0703_x','linear_rail_y_width_max',12],[-115,0,-34]),W)
add('0703','B','导向凸轨',box(['P0703_x',12,8],[-115,0,-24]),W)
add('0703','C','移动滑块',cut(box([36,30,8],['load_x',0,-24]),box([38,12.4,8.4],['load_x',0,-24])),C)
add('0701','A','低位托体',box([60,32,7],['load_x-15',0,-16.5]),C)
add('0701','B','窄推头',box([3,10,12],['load_x-15',0,-7]),C)
add('0701','C','释放机构侧悬臂',box([10,70,8],['load_x-40',-30,-16]),C)
for side,sg in [('L',1),('R',-1)]:
    add('0702','__'+side,'低位夹指',box([35,10,8],['load_x-12',sg*18.25,-12]),'CLAMP_'+side)
    add('0702','A__'+side,'夹指导向连杆',box([8,36.5,4],['load_x-26',sg*18.25,-18]),'CLAMP_'+side)
add('0704','','释放执行器候选',box(['P0704_x','P0704_y','P0704_z'],['load_x-55',-65,-35]),C)
add('0704','A','执行器连接支板',box([30,16,4],['load_x-55',-65,-18]),C)

# C: tube slots for radial mechanism, rear-open quick-release collars, independent sleeve guide.
tube_shape=ring('tube_od/2','tube_id/2','tube_length',['load_x',0,'tube_bottom_z_H+tube_length/2'])
tube_shape=cut(tube_shape,box([90,66,8],['load_x',0,284]),box([20,100,14],['load_x',0,330]))
add('0601','','带分球窗口储球筒',tube_shape,F,color='#A7C3D1',alpha=0.32)
add('0601','A','可拆筒帽',ring(43,38,'tube_cap_allowance',['load_x',0,'tube_bottom_z_H+tube_length+tube_cap_allowance/2']),F)
for side,sg in [('L',1),('R',-1)]:
    add('0602','A__'+side,'后侧固定立杆',tube([20,20,950],3,[-310,sg*85,125]),F)
    add('0602','B__'+side,'底部悬臂连接梁',box([310,20,20],[-155,sg*85,-352]),F)
    for z in [410,600]:
        add('0602','C__'+side+str(z),'筒架侧向托臂',box([120,20,12],[-250,sg*60,z]),F)
for z in [410,600]:
    collar=cut(ring(55,40.5,12,['load_x',0,z]),box([70,82,16],['load_x-35',0,z]))
    add('0602','D__'+str(z),'后开口快拆卡环',collar,F)
    add('0602','E__'+str(z),'可拆后压带',cut(ring(55,40.5,12,['load_x',0,z]),box([110,110,16],['load_x+42',0,z])),F)
# open-sided experimental box, avoids filled bounding cuboid
for sg in [-1,1]:add('0602','F__'+str(sg),'分球盒侧壁',box([170,6,100],[-225,sg*72,330]),F)
add('0602','G','分球机构背板',box([6,150,100],[-313,0,330]),F)
for side,sg in [('L',1),('R',-1)]:
    add('0603','__'+side,'留球夹试验嵌件',box([18,45,12],['load_x',sg*35.5,330]),'UPPER_'+side)
add('0604','','可抽出托球闸',box(['P0604_x','P0604_y','P0604_z'],['load_x',0,284]),'LOWER_GATE')
for i,z in enumerate([303,356]):
    add('0605','__'+str(i+1),'分球执行器候选',box(['P0605_x','P0605_y','P0605_z'],[-270,44,z]),F)
    add('0605','A__'+str(i+1),'可调连杆',box([60,6,6],[-245,30,z]),F)
add('0606','','外导球套',ring('guide_od/2','guide_id/2','guide_length',['load_x',0,'guide_bottom_load_z_H+guide_length/2']),'GUIDE_SLEEVE',color='#B8D5DC',alpha=.45)
add('0606','A','导套滑座连接叉',cut(box([68,26,10],[-231,0,128]),cyl(43,14,['load_x',0,128])),'GUIDE_SLEEVE')
add('0607','A','独立线性导套轨',box(['P0607_x','P0607_y','P0607_z'],[-275,0,170]),F)
add('0607','B','导套移动滑块',box([12,25,30],[-249,0,128]),'GUIDE_SLEEVE')
add('0607','C','导轨顶部固定桥',box([55,110,8],[-285,0,284]),F)

# D: base and height chain.
for sg in [-1,1]:
    add('0101','A__'+str(sg),'纵向底架梁',box(['base_x',40,80],[0,f'{sg}*(base_y/2-20)','base_top_z-40']))
    add('0101','B__'+str(sg),'横向底架梁',box([40,'base_y-80',80],[f'{sg}*(base_x/2-20)',0,'base_top_z-40']))
add('0101','C','立柱连接桥板',box([200,'base_y-80',8],[0,0,'base_top_z-4']))
add('0101','D','配重承托梁',box([420,40,8],[0,0,100]))
add('0102','','配重板',box(['P0102_x','P0102_y','P0102_z'],[0,0,110]))
for sx in [-1,1]:
    for sy in [-1,1]:
        end=[sx*425,sy*400]; mid=[sx*(425-220/2/math.sqrt(2)),sy*(400-220/2/math.sqrt(2))]
        leg=box(['P0103_x','P0103_y','P0103_z']);leg['rotate']=([0,0,1],math.degrees(math.atan2(sy,sx)));leg['at']=[*mid,100]
        leg=cut(leg,cyl(6.5,44,[*end,100]))
        suffix='__'+str(sx)+'_'+str(sy)
        add('0103',suffix,'展开支腿',leg)
        add('0103','A'+suffix,'概念支腿锁销',cyl(4,48,[sx*300,sy*275,100]))
        add('0104',suffix,'调平脚候选',union(cyl(25,10,[*end,5]),cyl(6,80,[*end,50])))
for sy in [-1,1]:
    add('0105','A__'+str(sy),'搬运轮胎',ring(40,6,28,[-280,sy*240,46],'y'))
    add('0105','B__'+str(sy),'脚轮支架',union(box([50,40,6],[-280,sy*240,77]),box([50,6,40],[-280,sy*240+17,54]),box([50,6,40],[-280,sy*240-17,54])))
outer=tube([90,90,880],4,[0,0,600]);outer=cut(outer,cyl(6.2,100,[0,0,950],'x'))
add('0201','','外立柱',outer)
inner=tube([80,80,650],4,[0,0,-667])
for z in [-850,-750,-650,-550,-450]:inner=cut(inner,cyl(6.2,90,[0,0,z],'x'))
add('0202','','内滑柱',inner,F)
add('0203','','高度定位销候选',cyl(6,100,[0,0,950],'x'))
for z in [860,1022.5]:add('0204','__'+str(z),'分体导向夹紧座',cut(box([130,130,35],[0,0,z]),box([90.2,90.2,40],[0,0,z])))
add('0301','','偏航固定基座',box(['P0301_x','P0301_y','P0301_z'],[0,0,'inner_mast_top_z_H+P0301_z/2']),F)
add('0302','A','回转固定圈',ring(80,64,30,[0,0,-315]),F)
add('0302','B','回转运动圈',ring(63.5,45,30,[0,0,-315]),Y)
add('0303','','偏航闭环执行器候选',box(['P0303_x','P0303_y','P0303_z'],[-165,0,-390]),F)
add('0303','A','偏航输出候选连接轴',cyl(10,70,[-165,0,-315]),F)
add('0303','B','偏航传动概念连臂',box([165,18,10],[-82.5,0,-335]),F)
add('0401','A','U架下横梁',box([220,460,10],[0,0,-295]),Y)
for sg in [-1,1]:
    add('0401','B__'+str(sg),'U架侧板',cut(box([100,10,300],[0,sg*225,-140]),cyl(9.2,14,[0,sg*225,0],'y')),Y)
    add('0402','__'+str(sg),'独立短耳轴',cyl(9,60,[0,sg*210,0],'y'),W)
add('0403','','俯仰执行器候选',box(['P0403_x','P0403_y','P0403_z'],[0,-280,-32.5]),Y)
add('0403','A','俯仰联轴器候选',ring(16,9,12,[0,-241,0],'y'),Y)

# E: sectional covers. Side plates stop below trunnion bridge, roof has full shuttle corridor.
for side,sg in [('L',1),('R',-1)]:
    add('0801','A__'+side,'轮组侧护板',box([240,3,140],[30,sg*183.5,-102]),W,cover=True)
    add('0801','B__'+side,'轮组上护板',box([240,132,3],[30,sg*119,92]),W,cover=True)
    add('0801','C__'+side,'后窄尾护板',box([145,3,75],[-162.5,sg*53.5,-12.5]),W,cover=True)
    add('0801','D__'+side,'上罩连接柱',box([6,6,122],[145,sg*180,29]),W,cover=True)
add('0802','','透明检查窗',box(['P0802_x','P0802_z','P0802_y'],[25,185,32.5]),W,cover=True,alpha=.3)
# electrical shell with actual mast aperture and removable rear panel
shell=cut(box(['P0803_x','P0803_y','P0803_z'],[0,0,265]),box(['P0803_x-6','P0803_y-6','P0803_z-6'],[0,0,265]),box([98,98,220],[0,0,265]),box([8,400,198],[-248,0,265]))
for yy in [-130,-100,-70,70,100,130]:shell=cut(shell,box([60,14,8],[130,yy,369]))
add('0803','A','带通风孔电气舱',shell,cover=True)
add('0803','B','可拆后舱门',box([3,400,198],[-248.5,0,265]),cover=True)
add('0803','C','分区电气托盘',cut(box([480,400,3],[0,0,211.5]),box([98,98,6],[0,0,211.5])))
for idx,x in enumerate([-110,110]):add('0507','__'+str(idx+1),'双轮驱动器候选',box(['P0507_x','P0507_y','P0507_z'],[x,-125,322.5]))
add('0901','','本地控制板候选',box(['P0901_x','P0901_y','P0901_z'],[150,110,225.5]))
add('0902','','电源模块候选',box(['P0902_x','P0902_y','P0902_z'],[85,-120,238]))
add('0903','','配电联锁功能模块候选',box(['P0903_x','P0903_y','P0903_z'],[-140,100,248]))
add('0904','','自锁急停候选',union(cyl(20,14,[-100,-85,940],'y'),cyl(10,46,[-100,-55,940],'y')),color='#CE3938')
add('0904','A','急停固定安装面板',cut(box([100,4,90],[-100,-75,940]),cyl(10.5,8,[-100,-75,940],'y')))
add('0904','B','面板立柱连接臂',box([80,30,6],[-85,-30,900]))
add('1001','','终端候选包络',box([12,85,170],[-120,0,780]))
add('1002','','有线停发手柄',box([30,50,100],[-130,95,770]))
add('1003','','终端夹持架',union(box([6,90,110],[-110,0,780]),box([60,90,6],[-83,0,728]),box([30,6,110],[-122,42,780]),box([30,6,110],[-122,-42,780])))

# Sensor function locations - quantities remain unset in the supplier BOM.
locations=[(F,[-275,29,270]),(F,[-275,29,80]),(W,[-235,32,-30]),(C,[-225,44,-32]),(C,[-195,42,-60]),(W,[120,50,30]),(F,[90,0,-325]),(Y,[65,100,-278]),(Y,[0,245,-60]),(W,[0,200,-60]),(W,[125,164,50]),(F,[-265,-45,350]),(W,[35,125,-90]),(W,[35,-125,-90])]
schedule=read('sensor_schedule.json')
for sen,(parent,pos) in zip(schedule,locations):
    add('0905','__'+sen['instance_id'],sen['function']+'功能占位',box(['P0905_x','P0905_y','P0905_z'],pos),parent,sensor_function=sen['instance_id'])
    sen['model_instance']='PRT-0905__'+sen['instance_id'];sen['geometry_status']='功能位置占位，非器件数量定稿'
write('sensor_schedule.json',schedule)

# Reference geometry is exported separately, never counted as a purchasable part.
add('REF-CORK','','校核球头',cyl('cork_diameter_visual/2','cork_z_max-cork_z_min',['load_x',0,'(cork_z_max+cork_z_min)/2']),C,color='#D7B482',reference=True)
add('REF-SKIRT','','完整羽毛裙包络',dict(op='cone',radius='cork_diameter_visual/2',radius2='skirt_diameter_max/2',height='feather_z_max-feather_z_min',at=['load_x',0,'(feather_z_max+feather_z_min)/2']),C,color='#F0ECE1',alpha=.5,reference=True)
write('geometry.json',dict(status='concept',note='新增概念细节；全部尺寸是当前data权威。采购孔型保持空，不是制造图。',instances=recipes))

# Comparison is read-only; the old design-book generator is never used to make CAD.
spec=importlib.util.spec_from_file_location('old',R/'input/BM1_Design_V0_2/source/design_data.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
p=read('design.json')['parameters'];diff={k:[v,p.get(k)] for k,v in old.PARAMS.items() if p.get(k,{}).get('value')!=v}
(R/'reports/input_audit.json').write_text(json.dumps(dict(main_items=len(parts),source_parameter_differences=diff,external_task_matches_packaged=True,data_files_read=[f.name for f in (R/'input/BM1_Design_V0_2/data').iterdir()]),ensure_ascii=False,indent=2),encoding='utf-8')
print('Authored',len(recipes),'CAD instances;',len(parts),'main IDs; source differences:',diff)
