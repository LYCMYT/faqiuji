from pathlib import Path
import sys,json,math,html
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Image,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
pdfmetrics.registerFont(TTFont('CN','C:/Windows/Fonts/msyh.ttc',subfontIndex=0))
O=R/'output/engineering'
def read(p):return json.loads((R/p).read_text(encoding='utf-8'))
spec=read('data/r1_engineering.json');motion=read('reports/collisions_motion.json');contract=read('reports/r1_contract_validation.json');service=read('reports/r1_service_validation.json');protocols=read('output/engineering/test_protocols.json');stack=read('output/engineering/synthetic_stack_sensitivity.json')
style=ParagraphStyle('body',fontName='CN',fontSize=11,leading=18,textColor=HexColor('#183a4d'),wordWrap='CJK',spaceAfter=9)
head=ParagraphStyle('head',parent=style,fontSize=22,leading=31,spaceAfter=16)
small=ParagraphStyle('small',parent=style,fontSize=9.5,leading=15)
story=[]
def p(s,sty=style):return Paragraph(html.escape(str(s)),sty)
def page(title,paras=()):
    if story:story.append(PageBreak())
    story.append(p(title,head));story.extend(p(s) for s in paras)
def figure(path,w=720,h=350):
    a,b=PILImage.open(path).size;scale=min(w/a,h/b);story.append(Image(str(path),a*scale,b*scale));story.append(Spacer(1,8))
def table(rows,widths):
    data=[[p(c,small) for c in row] for row in rows];t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#dce9ec')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.4,HexColor('#b7cbd2')),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.append(t)
page('BM1 V0.2 R1 / 修订与样机工程手册',['原生参数模型、可执行检查、试验夹具与证据记录入口。没有进行实物试验或采购确认。'])
figure(R/'output/render/R1_cassette_service.png',720,350)
story.append(p('187个物理实例 / 44主项 / 983个离散运动状态 / 制造批准：否',small))
page('01 / 本轮实际改动')
table([['项目','R0问题','R1产物与边界'],['捕获后动作','继续前推与冻结参考球相交','带球停于首次理想接触；新出球脉冲后撤回；牵引动态仍未实测'],['后侧维护','单独球筒需先拆分球及导套','整套抽出组件、承接槽和双横销；205个维护位置检查；负载及实际操作未验证'],['上夹接口','平面夹块与球堆接口未知','弧面R29装机候选，R23/R26/R32替换试件；真实套叠节距待测'],['滑台线缆','名义折线路径长度变化','圆弧恒长357.272mm；中心线半径21.5mm；厂家允许值待确认'],['试验工作','只有未决问题清单','低速验证台、10项规程、测量空表、采购接口表、质量计算入口'],['控制合同','只有动画及简单允许条件','反馈状态机与故障注入、18项回归；无硬件输出，不是安全PLC']],[90,230,420])
page('02 / 释放、接触与捕获不能混为一谈',['球头D26.5、轮D140、间隙25来自当前概念数据。首次刚性圆截面接触X约-11.149552，滑台行程约178.850448；这个位置不保证已经具备可靠牵引力。','实体夹指必须在该边界前张开。X=-5／行程185保留为机械空行程检查，带球状态禁止继续推至该位置。','捕获后参考球保持独立世界变换，仅用来检查保守停留情况下的退让；没有假设实际球停住或生成虚假的飞行轨迹。'])
table([['量','当前设计/数字值','仍需证据'],['开夹示意区间','X=-45开始，X=-25完成','实际执行器延迟、夹力、球型极限'],['接触边界行程',f"{contract['capture_first_tangency_stroke_mm']:.6f} mm",'压缩与牵引建立位置、停止距离'],['复位许可','捕获后新出球高→低脉冲','传感器、去抖、断线诊断、硬件停止'],['间隙30参数变体','球头26.5时无几何捕获','控制器阻止带球周期；结构重建成功不代表可发球']],[160,270,310])
page('03 / 反馈合同与离线周期')
table([['离线样本','状态','滑台目标mm']] + [[t['sample'],t['output']['state'],'' if t['output']['slide_target_mm'] is None else round(t['output']['slide_target_mm'],6)] for t in contract['cycle_trace']],[100,320,320])
story.append(p('17个输入样本是逻辑测试，不是实测时间。位置反馈必须先观测离位，再观测新到位；缺失出球输入不能充当下降沿。真实超时仍未设定。',small))
page('04 / 整套供球组件后抽',['动作前提：空筒、隔离能源并确认停转、最低轴高锁定、托车承重、线束断开。先把左右横销各向外退出55mm，再沿-X将完整供球器后抽350mm。','两销路径29个位置、整套后抽176个位置；维护状态H1400，升降线束按该高度重新构建。导套和分球器保持在组件内，不用先拆掉它们避让。'])
figure(R/'output/render/R1_cassette_service.png',720,315)
story.append(p('承接槽强度、横销防误退出、满载搬运、接头操作和复装同心尚待验证。演示中没有用托车承重模型冒充已设计托车。',small))
page('05 / 滑台恒长回线',['回线由两段直线、180°回环、90°出线与末端直线组成。平移时回环中心移动半个滑台位移；两直线长度增减抵消。','186个位移状态解析长度相同：357.272121mm；中心线弯曲半径21.5mm，线缆外径候选4mm，对应内侧半径19.5mm。以上不是厂商允许弯曲半径或耐久成绩。'])
figure(R/'output/drawings/PRT-0704-WIRE_A_iso.png',700,280)
story.append(p('全姿态实体检查包含此回线。固定端夹持、端部应力释放、升降及旋转轴完整线束仍需选型与现场布线验证。',small))
page('06 / 球堆敏感性：假设与测量分开',['下球最高包络H383，上夹最低面H386，当前轴向几何间隔3mm。上夹的弧面与下一只球羽裙接触程度取决于真实套叠节距。下表的节距是试验准备假设，不是实测。'])
table([['假设节距mm','夹块半径mm','理想包络径向重叠mm','意义']] + [[a['synthetic_pitch_mm'],a['pad_radius_mm'],f"{a['nominal_radial_overlap_mm']:.3f}",'正值仅包络接触；负值为间隙'] for a in stack['cases']],[120,130,190,300])
story.append(p('不能把正重叠判作可靠夹持。真实羽片稀疏、变形、磨耗和夹力必须用实物夹块试验确认。',small))
page('07 / 独立低速分球与接球验证台')
figure(O/'separator_bench.png',720,380)
story.append(p('STEP中含供球器、接球滑台和7件台架候选，未安装高速轮。原生实体回读及静态相交检查完成；紧固、锚固、刚度和操作防护尚未批准。',small))
page('08 / 采购资料与接口签核',['supplier_interface_RFQ.csv覆盖44主项；interface_signoff.csv记录关键接口。可作为询价资料准备，本次未发送给供应商、未订货。'])
table([['器件族','须取得的真实数据'],['轮/轮毂/轴/轴承','材料与制造批次、孔轴配合、轴向锁紧、允许载荷/转速、动平衡与质量惯量'],['电机与驱动','扭矩-转速曲线、额定/峰值电流、转子惯量、控制接口、停止与制动方式'],['滑台与导套执行器','行程、安装孔图、导轨载荷/力矩、运行速度与停止距离、限位形式'],['偏航/俯仰支承','实际外形、孔型、回转/俯仰力矩、间隙、锁止能力'],['电源与保护','供电制式、额定功率、保护配置、散热、连接器、导线和停止链架构'],['线缆与传感器','实际型号、动态弯曲允许值、寿命条件、安装尺寸、响应和诊断特性']],[170,570])
page('09 / 如何填入真实证据',['先复制BLANK模板并重命名；不要在重建会生成的模板中保存唯一实测记录。','shuttle_measurements_BLANK.csv：记录球型号、批次、新旧程度、球头/羽裙/全长、质量、逐只套叠高度、力、仪器、操作者、日期及照片。PLAN编号是计划行，不代表已测30只。','prototype_runs_BLANK.csv：每次动作关联球样本、硬件版本、轮距、两轮实测转速、释放和捕获位置、单双球、卡球、损伤、出球反馈与视频。','evidence_register.json当前测量、供应商确认及样机结果数组均为空。没有证据时保留空值，不用0代替未知。'])
for start in range(0,len(protocols),2):
    page('10 / 样机规程 '+protocols[start]['test_id']+'—'+protocols[start+1]['test_id'])
    for t in protocols[start:start+2]:
        story.append(p(t['test_id']+' '+t['title']+' / '+t['issues'],ParagraphStyle('sub',parent=style,fontSize=15,leading=23,spaceBefore=13)))
        story.append(p('步骤：'+t['procedure']));story.append(p('判据与边界：'+t['acceptance_basis']));story.append(p('当前结果：未执行。实际样机版本、操作者、仪器、原始记录与视频待填。',small))
page('11 / 质量、质心与支脚计算',['mass_inputs_BLANK.json为187个物理实例保留质量、指定姿态世界质心与来源状态。采购件包络不能按实心体积直接当真实质量。','engineering/evaluate.py在质量/质心证据缺失时返回BLOCKED_MISSING_EVIDENCE；当前实际质量、质心和稳定性结果均为空。','支脚反力采用刚性底盘及线性垂向弹簧模型，需要有限正的实测刚度；支脚离地时重新求有效接触集。负刚度、零刚度、非有限值和不足支点被拒绝。','只在明确姿态与地面假设下作静态计算。最高位满筒、头姿态变化、动态停止、倾斜地面、变形和疲劳均需另外验证，不能由静态重力平衡推定安全等级。'])
page('12 / 功能接线与停止关系',['control_functional.svg是可编辑的功能关系图：电源与隔离 → 独立停止链与驱动使能 → 执行器；顺序控制接收导套、滑台、夹开、出球等反馈。','具体电压、端子、导线截面积、保护、制动、诊断和控制器型号均未确定。本图不能用于直接接电机。','离线模拟器没有GPIO或电机连接；保护输入异常、轮速/持球反馈丢失、信号缺失、超时和常高异常会锁定FAULT，不自动恢复运行。'])
table([['当前产物','仍未生成/验证'],['反馈状态机与18项回归','真实PLC/固件、驱动参数、去抖与看门狗硬件集成'],['概念功能接线SVG','供应商冻结端子图、电气额定值及保护协调'],['联锁输入合同','安全控制等级、诊断覆盖与真实停转时间'],['三段机械顺序动画','真实出球动态、可靠性、长期耐久和安全认证']],[280,460])
page('13 / 验收边界与资料来源',[f"主模型检查：{motion['states']}个离散状态，无未解释硬相交。205个维护位置检查通过；试验台有效实体和静态几何检查通过。",'U01—U10全部保持开放；采购、实测球堆、牵引动态、完整电气/线束、稳定性与防护没有因为导出成功而关闭。','以下资料只用于整理选型所需输入，不代表选定型号或厂家认可本机构。'])
for s in spec['sources']:
    story.append(Paragraph(f'<link href="{html.escape(s["url"],quote=True)}" color="#087b80">{s["id"]} 官方选型资料</link> — '+html.escape(s['purpose']),style))
story.append(p('配套：acceptance_report.html、validation.json、r1_code_review.md、r1_service_validation.json、r1_contract_validation.json。所有原始实测数据当前为空。'))
def footer(c,doc):
    c.setFont('CN',8);c.setFillColor(HexColor('#526677'));c.drawString(36,20,'BM1 / V0.2 R1 / 概念工程与试验准备 · 非制造批准');c.drawRightString(805,20,str(doc.page))
doc=SimpleDocTemplate(str(O/'BM1_R1_engineering_manual.pdf'),pagesize=landscape(A4),rightMargin=36,leftMargin=36,topMargin=32,bottomMargin=34)
planned_pages=1+sum(isinstance(item,PageBreak) for item in story)
doc.build(story,onFirstPage=footer,onLaterPages=footer)
(R/'reports/r1_manual_expected.json').write_text(json.dumps({'planned_pages':planned_pages}),encoding='utf-8')
print('R1 MANUAL CREATED')
