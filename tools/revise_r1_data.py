"""One-time R1 data authoring from preserved R0. Not a rebuild step."""
from pathlib import Path
import json,copy,math
R=Path(__file__).resolve().parents[1];D=R/'data';B=R/'revisions/r0/data'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(name,x):(D/name).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
spec=dict(revision='V0.2-R1',status='concept_not_prototype_verified',
 controller=dict(simulation_state_timeout_s=10,hardware_timeout_s=None,capture_feedback_device=None,exit_requires_fresh_pulse=True,hardware_connected=False),
 cassette=dict(extraction_mm=350,pin_withdraw_mm=55,sample_step_mm=2,receiver_clearance_mm=1,lock_pin_diameter_mm=8,lock_bore_diameter_mm=9,load_rating_N=None,retention_verified=False,method='整套固定供球器后抽；双销退出、线束断开、支撑托车就位；不拆导套或分球器'),
 separator=dict(pad_radius_candidates_mm=[23,26,29,32],selected_concept_radius_mm=29,measured_stack_pitch_mm=None,synthetic_pitch_cases_mm=[30,40,50],synthetic_ball_count=3,hold_z_H=392,single_ball_reliability=None),
 cable=dict(slide_loop_length_mm=280,slide_exit_y_mm=-65,slide_plane_y_mm=-130,slide_centerline_radius_mm=21.5,cable_diameter_mm=4,supplier_min_bend_radius_mm=None,dynamic_life_cycles=None,mast_and_rotary_routes_validated=False),
 hardware_evidence=dict(measurements=[],supplier_quotes=[],prototype_runs=[],manufacturing_release=False),
 sources=[dict(id='R1-S01',url='https://www.thk.com/us/en/products/lm_guide_actuator/selection/',purpose='直线模组选择须核对载荷、力矩、寿命与精度，不代表已选型'),dict(id='R1-S02',url='https://www.igus.com/company/energy-chains-caring-for-cables-ca',purpose='线缆选择须核对弯曲半径、运动和应力释放，几何半径不代表电缆已合格'),dict(id='R1-S03',url='https://www.orientalmotor.com/motor-sizing/index.html',purpose='电机需要扭矩、速度、惯量和停止要求，未据外形确定型号')])
write('r1_engineering.json',spec)
g=read(B/'geometry.json');g['note']+=' R1:整套供球器抽出接口、弧面夹块与恒长滑台回线；全部新增结构均为待验证设计候选。'
def box(size,at):return dict(op='box',size=size,at=at)
def cyl(rad,h,at):return dict(op='cylinder',radius=rad,height=h,at=at,rotate=[[1,0,0],90])
for i in g['instances']:
    if i['part_id']=='PRT-0603':
        i['shape']=dict(op='cut',children=[i['shape'],dict(op='cylinder',radius=29,height=16,at=['load_x',0,392])]);i['name']='可更换弧面留球试验夹块 R29'
    if i['instance_id'].startswith('PRT-0602-B__'):
        sg=1 if i['instance_id'].endswith('L') else -1
        i['shape']=dict(op='cut',children=[i['shape'],cyl(4.5,42,[-20,sg*85,-352])])
    if i['instance_id']=='PRT-0704-WIRE_A':
        i['shape']=dict(op='return_loop',fixed_x=-235,moving_x='load_x-55+slide',lower_z=-95,upper_z=-52,y=-130,length=280,radius=2,direction=1,exit_y=-65)
        i['dynamic_loop']=copy.deepcopy(i['shape']);i.pop('dynamic_path',None);i['name']='恒长回环及圆弧出线候选'
for sg,label in [(1,'L'),(-1,'R')]:
    at=[-20,sg*85,-354.5]
    # Receiver upper lands meet the existing yaw-base underside at H-342.
    # A lower inward flange would foul the outer-mast collar at H=1400.
    receiver=dict(op='cut',children=[box([40,30,25],at),box([42,22,23],[-20,sg*85,-352.5])])
    receiver=dict(op='cut',children=[receiver,cyl(4.5,60,[-20,sg*85,-352])])
    pin=dict(op='union',children=[cyl(4,50,[-20,sg*85,-352]),cyl(7,5,[-20,sg*112.5,-352])])
    for suffix,name,shape,parent in [('RECEIVER','供球抽出组件固定承接槽',receiver,'FIXED_HEAD_CARRIER'),('PIN','供球抽出组件横向解锁销候选',pin,'CASSETTE_PIN_'+label)]:
        pid='PRT-0202-R1_'+suffix
        g['instances'].append(dict(instance_id=pid+'__'+label,part_id='PRT-0202',derived_id=pid,assembly_id='ASM-02',name=name,parent=parent,shape=shape,color='#526677',status='concept'))
write('geometry.json',g)
design=read(D/'design.json');design['revision']='V0.2-R1';design['notice']='R1数字工程修订；无实测或采购冻结。';write('design.json',design)
p={k:v['value'] for k,v in design['parameters'].items()};capture=-math.sqrt(((p['wheel_diameter']+p['cork_diameter_visual'])/2)**2-((p['wheel_diameter']+p['wheel_gap_visual'])/2)**2)-p['load_x']
states=read(B/'animation_keyframes.json')
for row in states:
    if row[0] in [390,420]:row[3]=capture
    if row[0]==420:row[1]='ST09 停推等待出球反馈'
    if row[0]==450:row[1]='ST10 条件撤回·需新出球脉冲'
write('animation_keyframes.json',states)
services=read(B/'service_validation.json') if (B/'service_validation.json').exists() else []
write('r1_service.json',dict(cassette_parts=['PRT-0601','PRT-0602','PRT-0603','PRT-0604','PRT-0605','PRT-0606','PRT-0607'],cassette_instances=['PRT-0905__SEN-01','PRT-0905__SEN-02','PRT-0905__SEN-12','PRT-0905__SEN-12_HOLD'],pin_instances=['PRT-0202-R1_PIN__L','PRT-0202-R1_PIN__R'],service_state=dict(guide=115,slide=0,clamp=14,yaw=0,pitch=0,height=1400),pin_withdraw_mm=55,extract_mm=350,step_mm=2,prerequisites=['电源隔离且轮组确认停转','轴高降至1400并锁定','供球器为空；落球与导套收妥','供球组件由独立托车承重','插接线束断开','两只横销沿外侧退出55mm','整套供球器沿-X抽出350mm'],verified_load_rating=None))
print('R1 DATA',len(g['instances']),'capture',capture)
