"""Generate the executable, blank-evidence engineering and prototype work pack."""
from pathlib import Path
import sys,json,csv,html,copy
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import cadquery as cq
from cad.parts.recipe import build
from cad.export_all import locate
from engineering.evaluate import evaluate
from tools.check_collisions import bbox,overlaps
from tools.render_cad_preview import render
O=R/'output/engineering';O.mkdir(exist_ok=True)
def read(p):return json.loads((R/p).read_text(encoding='utf-8'))
def dump(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def csvfile(name,header,rows):
    with (O/name).open('w',encoding='utf-8-sig',newline='') as f:w=csv.writer(f);w.writerow(header);w.writerows(rows)
parts=read('data/parts.json');items=read('data/instances.json');spec=read('data/r1_engineering.json');service=read('data/r1_service.json');p={k:v['value'] for k,v in read('data/design.json')['parameters'].items()}
components=[dict(instance_id=i['instance_id'],mass_kg=None,com_world_mm=None,evidence_status='not_measured',source=None) for i in items if not i.get('reference')]
mass=dict(pose=dict(height=1800,yaw=45,pitch=60),components=components,supports=[dict(x_mm=x,y_mm=y,vertical_stiffness_N_mm=None) for x in [-p['support_x']/2,p['support_x']/2] for y in [-p['support_y']/2,p['support_y']/2]],notes='必须按指定姿态填写世界坐标质心。此表不把采购件包络体积当真实质量。')
dump(O/'mass_inputs_BLANK.json',mass);dump(O/'mass_evaluation.json',evaluate(components,mass['supports']))
csvfile('shuttle_measurements_BLANK.csv',['sample_id','brand_model','batch','new_or_used','cork_diameter_mm','cork_height_mm','skirt_max_diameter_mm','overall_height_mm','mass_g','stack_count','stack_height_mm','incremental_pitch_mm','force_N','damage_notes','instrument','operator','date','evidence_file'],[[f'PLAN-{n:02}',*['']*17] for n in range(1,31)])
csvfile('prototype_runs_BLANK.csv',['run_id','test_id','hardware_revision','ball_sample_id','wheel_gap_mm','rpm_left_measured','rpm_right_measured','guide_up_confirmed','release_x_measured_mm','capture_x_measured_mm','one_ball','jam','damage','exit_pulse','stop_time_s','landing_x_m','landing_y_m','video_path','operator','date','result'],[])
csvfile('supplier_interface_RFQ.csv',['part_id','name','envelope_candidate_mm','required_data','supplier','model','mass_kg','drawing_revision','hole_pattern_source','ratings_source','verified','notes'],[[a['part_id'],a['name'],str(a['bbox_mm']),'外形图/孔型/轴径/配合/载荷或扭矩/惯量/转速或行程/供电/停止要求/质量',*['']*6,'NO','仅候选包络，未经采购冻结'] for a in parts])
csvfile('interface_signoff.csv',['interface','requirement','evidence_required','value','unit','source','approved_by','status'],[
 ['轮毂-轴','孔轴配合与轴向防松','供应商图/强度与拆装验证','','','','','OPEN'],['电机-轮组','额定/峰值扭矩与惯量、轮胎最高转速','选型计算/厂家书面数据/动平衡与轮试验','','','','','OPEN'],['滑台','行程185、负载/侧向力矩、停止距离','厂家曲线与负载试验','','','','','OPEN'],['导套','行程115、上位反馈与同心','装配测量/循环记录','','','','','OPEN'],['抽出组件','承重、两销锁止、插接线束','结构计算/承载与误操作试验','','','','','OPEN'],['电缆','循环弯曲半径与寿命','电缆型号/厂家允许值/实机轨迹','','','','','OPEN'],['支撑脚','质量分布、垂向刚度、地面条件','称重/质心/挠度测量','','','','','OPEN']])
protocols=[
 ('T01','球型与套叠测量','U03/U04/U05','每只球编号；测球头、羽裙、质量，再逐只叠加测高度。记录仪器、重复值和照片。','形成原始数据与范围，不能用平均值代替极限；目标球型由实际样品确定。'),
 ('T02','低速分球台','U03/U04','轮组不安装在分球验证台；依次试R23/R26/R29/R32嵌件，人工低速动作后再逐步自动循环。记录双球、卡球、损伤与球型。','未出现异常的次数如实记录；项目可靠性目标待确定，不预填合格。'),
 ('T03','松夹和捕获窗口','U02/U05','先用无动力轮组检查开夹与位置，再在专用防护试验环境记录同步位置、推力和高速视频。','确认释放完成早于牵引；接触几何位置不等于可靠捕获位置。'),
 ('T04','反馈与故障注入','U06/U08','逐项断开或模拟导套上位、夹开、出球、罩门及双销确认；记录停机反应。','不得自动继续或自动复位；硬件停止时间及诊断覆盖需另测。'),
 ('T05','抽出组件维护','U06/U09','空筒、最低轴高、隔离能源、托车承重；拔销并断线，再整套后抽。','测实际操作力、插拔空间、复装对中和误锁止；几何通路不等于便捷/强度合格。'),
 ('T06','电缆循环','U06/U08','核对供应商最小动态弯曲半径后检查全行程，记录拉力、扭转、磨擦和端部应力释放。','恒长滑台曲线仅为中心线设计；升降与旋转线路仍需完成实物布线。'),
 ('T07','质量/刚度/稳定','U07','逐件称重或取得厂家质量质心，在最低/最高、满筒和组合姿态测支脚反力及位移。','用测量输入evaluate.py；额外覆盖动态停止和地面条件，不由静态结果推安全等级。'),
 ('T08','轮组、防护与停止','U02/U08','选定实际轮/轴/驱动后，由具备条件的试验场验证连接、动平衡、停转、温升及防护能力。','限速与防护能力需厂家资料和试验依据，不从材料名称推定。'),
 ('T09','球路与节拍标定','U01/U10','在完成前述检查后，按球型、高度、角度、两轮实测转速采集落点、最高点、过网高度和节拍。','保留逐球数据和视频；用独立数据检验拟合，未采集前无精度成绩。'),
 ('T10','持续循环与复检','U03/U07/U08/U09','按项目确定的循环数量记录磨耗、松动、线束、轮胎和夹块状态。','次数、环境和失效必须可追溯；没有记录就保持未验证。')]
dump(O/'test_protocols.json',[dict(test_id=a,title=b,issues=c,procedure=d,acceptance_basis=e,result=None) for a,b,c,d,e in protocols])
dump(O/'evidence_register.json',dict(physical_measurements=[],supplier_confirmations=[],prototype_test_results=[],model_revision=spec['revision']))
bench=read('data/r1_testbench.json');assy=cq.Assembly(name='BM1_R1_LOW_SPEED_SEPARATOR_BENCH');model=[]
for i in items:
    if i['part_id'] not in bench['include_parts'] or i.get('reference'):continue
    sh=cq.Shape.importBrep(str(R/'output/mesh'/(i['instance_id']+'.brep')));sh=locate(sh,i['parent'],bench['state']);assy.add(sh,name=i['instance_id']);model.append((i['instance_id'],sh))
for i in bench['fixture_instances']:
    sh=build(i['shape'],p);assy.add(sh,name=i['instance_id']);model.append((i['instance_id'],sh));cq.exporters.export(sh,str(O/(i['instance_id']+'.step')))
assy.export(str(O/'BM1_R1_separator_bench.step'))
bench_hits=[]
for a,(name,s) in enumerate(model):
    for other,t in model[:a]:
        if overlaps(bbox(s),bbox(t)):
            volume=s.intersect(t).Volume()
            if volume>.01:bench_hits.append(dict(pair=[name,other],volume_mm3=volume))
render(model,O/'separator_bench','BM1 R1 / 独立低速分球与接球验证台')
# Independent fit inserts; not silently substituted into the assembly.
base=read('data/geometry.json')['instances'];jaws=[i for i in base if i['part_id']=='PRT-0603']
for radius in spec['separator']['pad_radius_candidates_mm']:
    shapes=[]
    for i in jaws:
        recipe=copy.deepcopy(i['shape']);recipe['children'][1]['radius']=radius;shapes.append(build(recipe,p))
    shape=cq.Compound.makeCompound(shapes)
    cq.exporters.export(shape,str(O/f'PRT-0603_FIT_R{radius}.step'));cq.exporters.export(shape,str(O/f'PRT-0603_FIT_R{radius}.stl'))
reopened=[]
for path in O.glob('*.step'):
    s=cq.importers.importStep(str(path)).val();assert s.isValid() and s.Volume()>0;reopened.append(dict(file=path.name,solids=len(s.Solids()),valid=True))
dump(R/'reports/r1_bench_validation.json',dict(step_reopened=reopened,static_intersections=bench_hits,low_speed_fixture_only=True,structural_strength_verified=False,physical_testing_performed=False))
stack=[]
for pitch in spec['separator']['synthetic_pitch_cases_mm']:
    top_radius=p['cork_diameter_visual']/2+(p['skirt_diameter_max']/2-p['cork_diameter_visual']/2)*(spec['separator']['hold_z_H']+6-300-pitch-p['feather_z_min'])/(p['feather_z_max']-p['feather_z_min'])
    for radius in spec['separator']['pad_radius_candidates_mm']:
        stack.append(dict(synthetic_pitch_mm=pitch,pad_radius_mm=radius,lower_ball_to_pad_axial_gap_mm=spec['separator']['hold_z_H']-6-300-p['feather_z_max'],ideal_second_skirt_radius_at_pad_top_mm=top_radius,nominal_radial_overlap_mm=top_radius-radius,interpretation='正值仅表示理想包络接触，负值表示间隙；不是实际夹持力或可靠性',physical_measurement=False))
dump(O/'synthetic_stack_sensitivity.json',dict(status='SYNTHETIC_ENVELOPE_ONLY',actual_stack_pitch_mm=None,feather_compression_verified=False,cases=stack))
md=['# BM1 V0.2 R1 样机工程工作包','', '本包已生成可执行计算、原生实体试验台和空白记录；没有进行实物测量、采购确认或硬件试验。','', '## 使用顺序','先阅读机构修订和验收报告 → T01测球 → T02低速分球 → 确定供应商接口 → T03/T04 → T05/T06/T07/T08 → T09/T10。','', '## 试验台与嵌件','BM1_R1_separator_bench.step含固定供球组件、接球滑台和独立台架，不含高速轮组；仅供低速机构试装评审。R23/R26/R29/R32是弧面候选半径，不是球型实测值；没有预判哪一种可靠。','', '## 测量与采购','shuttle_measurements_BLANK.csv中PLAN编号仅为计划行；所有测量格空白。supplier_interface_RFQ.csv逐主项列出候选包络和应索取资料，可由采购发送；本次未联系供应商或下单。interface_signoff.csv保留接口签核。','', '## 质量与支脚计算','mass_inputs_BLANK.json逐实例质量及世界质心待填；可运行：python engineering/evaluate.py output/engineering/mass_inputs_BLANK.json --output output/engineering/mass_evaluation.json。缺少证据时返回BLOCKED；不会用包络体积生成虚假的质量。支脚反力采用刚性底盘/线性垂向弹簧假设，需要实测支脚刚度。当前姿态为H1800/偏航45/俯仰60，其他姿态需独立输入。','', '## 控制逻辑边界','control/feed_cycle.py是无硬件连接的反馈合同模拟器；上位先确认、脱筒后转向、夹开后接近，接触后停推，必须有新的出球高→低脉冲才允许撤回；故障锁定。不是安全PLC或可直接接电机的固件。simulation_state_timeout_s只是测试配置；真实硬件超时尚未设定。','', '## 功能接线图','output/engineering/control_functional.svg区分停止链、运动控制与传感反馈。电压、端子、熔断器、导线截面积、驱动与安全等级均待选型，不能据此直接接线。','', '## 试验规程']
for a,b,c,d,e in protocols:md+=['',f'### {a} {b}（{c}）',d,'判据与边界：'+e,'结果：未执行；原始数据、操作者、日期、视频与器件版本待填写。']
md+=['','## 来源','依据官方选型资料整理资料需求；不构成型号推荐或供应商确认。']+[f"- [{s['id']}] {s['url']} — {s['purpose']}" for s in spec['sources']]
(O/'README_工程与试验.md').write_text('\n'.join(md),encoding='utf-8')
body=''.join('<h2>'+html.escape(x[3:])+'</h2>' if x.startswith('## ') else '<h3>'+html.escape(x[4:])+'</h3>' if x.startswith('### ') else '<p>'+html.escape(x)+'</p>' for x in md)
(O/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>BM1 R1 工程工作包</title><style>body{max-width:1000px;margin:40px auto;font:16px/1.8 system-ui;background:#f4f7f9;color:#173c4c}h2{color:#087b80}</style><a href="../../viewer/">三维查看器</a><p><a href="BM1_R1_separator_bench.step">低速验证台STEP</a> · <a href="shuttle_measurements_BLANK.csv">测量记录</a> · <a href="supplier_interface_RFQ.csv">采购接口表</a> · <a href="prototype_runs_BLANK.csv">试验记录</a></p>'+body,encoding='utf-8')
svg='''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="660" viewBox="0 0 1200 660"><rect width="1200" height="660" fill="#f4f7f9"/><style>text{font:20px "Microsoft YaHei",sans-serif;fill:#183a4d}.small{font-size:16px}.box{fill:white;stroke:#087b80;stroke-width:2}.wire{fill:none;stroke:#183a4d;stroke-width:3}</style><text x="30" y="45">BM1 R1 / 功能接线与停止关系（概念，非端子接线图）</text><rect class="box" x="40" y="100" width="220" height="100"/><text x="60" y="140">隔离与保护 / 电源</text><text class="small" x="60" y="175">额定值、型号均待确认</text><rect class="box" x="360" y="100" width="240" height="100"/><text x="380" y="140">独立停止链与驱动使能</text><text class="small" x="380" y="175">架构/制动/停转能力待验证</text><rect class="box" x="760" y="100" width="370" height="100"/><text x="780" y="140">轮组驱动、滑台与执行器</text><text class="small" x="780" y="175">任何软件模拟不能代替硬件停止</text><path class="wire" d="M260 150 H360 M600 150 H760"/><rect class="box" x="40" y="300" width="220" height="100"/><text x="60" y="340">急停、罩门、锁销确认</text><text class="small" x="60" y="375">信号实现与诊断待选型</text><path class="wire" d="M260 350 H320 V180 H360"/><rect class="box" x="360" y="300" width="240" height="100"/><text x="380" y="340">顺序控制与故障锁定</text><text class="small" x="380" y="375">真实超时、去抖、看门狗待定</text><path class="wire" d="M600 350 H700 V180 H760"/><rect class="box" x="760" y="300" width="370" height="100"/><text x="780" y="340">导套 / 滑台 / 夹开 / 出球反馈</text><text class="small" x="780" y="375">出球必须是捕获后的新高→低脉冲</text><path class="wire" d="M760 350 H600"/><text x="40" y="485">互锁顺序：导套上位 → 前移脱筒 → 转头 → 夹开 → 捕获边界停推 → 出球确认 → 撤回</text><text x="40" y="535">禁止：以固定延时替代反馈；出球传感器常高仍继续；故障解除后自动重启。</text><text class="small" x="40" y="595">本图不规定供电电压、引脚、线径、熔断器、制动参数或安全等级。采购与实机验证后另出冻结电气图。</text></svg>'''
(O/'control_functional.svg').write_text(svg,encoding='utf-8')
print('ENGINEERING PACK',len(components),'blank mass entries;',len(reopened),'STEP files reopened;',len(protocols),'unexecuted protocols')
