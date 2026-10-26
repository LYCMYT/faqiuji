from pathlib import Path
import json,csv,math,html
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Image,PageBreak,Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
R=Path(__file__).resolve().parents[1];O=R/'output/fixture_r3'
def read(p):return json.loads((R/p).read_text(encoding='utf-8'))
s=read('data/r3_fixture.json');work=read('data/r3_work_instructions.json');v=read('reports/r3_geometry_validation.json');e=read('reports/r3_export_validation.json');drawings=read('output/fixture_r3/drawing_index.json');parts=read('output/fixture_r3/parts_index.json')
with (O/'hole_table.csv').open(encoding='utf-8-sig',newline='') as f:holes=list(csv.DictReader(f))
pdfmetrics.registerFont(TTFont('CN','C:/Windows/Fonts/msyh.ttc',subfontIndex=0))
body=ParagraphStyle('body',fontName='CN',fontSize=10.5,leading=17,textColor=HexColor('#183a4d'),wordWrap='CJK',spaceAfter=8)
head=ParagraphStyle('head',parent=body,fontSize=21,leading=29,spaceAfter=14);small=ParagraphStyle('small',parent=body,fontSize=8.5,leading=13)
story=[];planned_pages=0
def para(t,sty=body):return Paragraph(html.escape(str(t)),sty)
def page(title,paras=()):
    global planned_pages
    if story:story.append(PageBreak())
    planned_pages+=1;story.append(para(title,head));story.extend(para(p) for p in paras)
def fig(path,width=700,height=400):
    a,b=PILImage.open(path).size;f=min(width/a,height/b);story.append(Image(str(path),a*f,b*f))
def table(rows,widths):
    t=Table([[para(c,small) for c in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#dce9ec')),('GRID',(0,0),(-1,-1),.4,HexColor('#b7cbd2')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.append(t)
page('BM1 R3 / 低速台架连接与加工图集',[s['date']+' / '+s['revision'],'本轮补齐基板孔位、筒架压板、滑台支柱、支脚与可换夹块连接。所有自定义孔位来自data/r3_fixture.json，沿用ASM/PRT编号。','当前是首件加工评审候选。上夹托板到执行器的适配与导向、原供球机构其余连接、实际滑台兼容、预紧载荷和台面锚固仍开放，整机制造未放行。',f"共{v['instances']}个实体实例、{e['step_files']}份STEP回读、{len(drawings)}张独立零件图、{len(holes)}行孔表。"])
fig(O/'drawings/assembly.png',400,260)
page('01 / 台架总装与自定义连接',['灰色为原R1概念部件；新件为本轮连接设计。总装没有高速轮组，不能用于高速发射。原R1整机与动画仍单独保留。'])
fig(O/'drawings/assembly.png',650,390)
page('02 / 基板、压板、支柱和支脚',['筒架下臂由穿透拉杆与压板固定；滑台轨底由带凹台侧压爪固定。此页单独显示连接件，完整装配及干涉检查包含所有原供球组件。'])
fig(O/'drawings/base_connections.png',650,390)
page('03 / 可更换夹块连接',['保留R23/26/29/32四种候选接触弧。孔中心移至筒外，POM后端加长4mm；托板有R41避筒弧面。R29仅为总装展示位。','两颗M4x25从上方沉孔连接托板；托板外端3.2mm销孔为本机候选接口，实际驱动适配件及导向未冻结。'])
fig(O/'drawings/jaw_connections.png',650,340)
for name,label in [('SECTION_POST_Y','滑台拉杆中心平面剖切'),('SECTION_JAW_X','夹块螺钉中心平面剖切')]:
    page('04 / '+label,['STEP剖切由原生实体布尔运算生成。保留截后实体，未用透明效果冒充剖切；紧固件牙型仍按下页简化约定。']);fig(O/'drawings'/f'{name}.png',650,390)
page('05 / 螺纹、孔位和基准约定',[s['hardware']['thread_representation'],'零件STEP使用局部包围盒最小角作为坐标原点；parts_index.json同时记录该原点在H坐标系的位置。A为底面，B为Y最小侧，C为X最小侧。对于中空、弧面件，坐标原点可位于实体之外。','孔表给出局部X/Y/Z、钻入轴向、孔径与沉孔。Z向孔默认贯穿，从Z+侧加工沉孔；X向托板销孔贯穿。DXF是顶面可见轮廓，不能替代有深度信息的孔表。',f"首件询价要求：一般线性尺寸±{s['inspection']['linear_general_tolerance_mm']}mm；孔坐标±{s['inspection']['hole_position_coordinate_tolerance_mm']}mm；POM厚度±{s['inspection']['jaw_thickness_tolerance_mm']}mm。这些是项目要求，尚无加工能力或实测证据。",'M6拉杆按长度切制后修端、去毛刺并核验完整牙型；实际等级、防松、预紧与支承面压均待载荷数据。长拉杆、空心管端面和侧压爪不能凭模型有效判定承载合格。'])
page('06 / 干涉修正记录',['初版夹块托板及内侧螺钉与固定球筒有6处体积交叠：孔移至筒外、POM后端加长、托板增加真实避筒弧面，固定球筒尺寸未改变。','初版滑台拉杆在末段行程与张开夹指相交：拉杆横移至Y±42mm，侧压爪设置直径20mm、深3mm的开边螺母工具凹台。','支柱曾采用加宽方案，造成释放执行器与顶盖/压爪相交；最终采用50×100×4mm空心柱候选外形，保留执行器包络并重做内部杆位与凹台。','修改历史原始冲突报告保留在reports/r3_*_conflicts.json。没有隐藏原部件、缩小球筒或执行器来消除冲突。',f"最终检查：{v['states']}个离散位置，{v['exact_pair_intersections']}次精确实体相交运算，无未解释相交；{v['tool_channels']}个指定工具通道通过。离散几何通过不等于连续运动、公差、刚度和实物装配全部通过。"])
page('07 / 装配顺序 1-5',work['assembly_steps'][:5])
page('08 / 装配顺序 6-10',work['assembly_steps'][5:])
page('09 / 夹块检修与工具通道',s['service']['prerequisites']+[f"检查姿态：{s['service']['tool_pose']}。M4直杆工具包络半径{s['inspection']['tool_M4_radius']}mm、长{s['inspection']['tool_M4_length']}mm；M6上部工具包络半径{s['inspection']['tool_M6_radius']}mm、长{s['inspection']['tool_M6_length']}mm。",'M4工具不能在原上夹位置直接向上穿过筒卡环。必须先断开实际连接并支撑，侧向退出40mm后操作。此路径只证明当前几何可达，实际连接拆卸和导向仍未冻结。','本轮检查包含每个结构螺母被拉杆覆盖及杆端伸出。螺纹牙型、牙数承载、防松寿命和操作力不在数字证明范围。'])
page('10 / 首件与样机检查',work['inspection_items'])
story.append(para('数字范围：'+v['motion_scope']+'。工具范围：'+v['tool_scope']+'。',small))
custom=[a for a in parts if a['kind']!='context']
for start in range(0,len(custom),10):
    page(f'11 / 连接件BOM {start+1}-{min(start+10,len(custom))}')
    table([['编号','装配数 / 备选数','材料与状态']]+[[a['family'],str(a['quantity_in_assembly'])+' / '+str(a['quantity_for_optional_pair']),a['material']] for a in custom[start:start+10]],[270,110,360])
for family in drawings:
    page(family+' / 独立零件图');fig(O/'drawings'/f'{family}.png',700,467)
for start in range(0,len(holes),12):
    page(f'12 / 孔表 {start+1}-{min(start+12,len(holes))}')
    table([['零件 / 孔号','轴','X / Y / Z mm','孔径','沉孔直径 / 深度','用途']]+[[a['family']+' / '+a['hole'],a['axis'],' / '.join(f"{float(a[k]):.3f}" for k in ['x_local_mm','y_local_mm','z_local_mm']),a['diameter_mm'],a['counterbore_diameter_mm']+' / '+a['counterbore_depth_mm'],a['purpose']] for a in holes[start:start+12]],[210,30,150,45,100,205])
page('13 / 尚未冻结的接口')
table([['编号 / 项目','需要的证据','状态']]+[[a['id']+' '+a['topic'],a['required'],a['status']] for a in work['open_interfaces']],[210,450,80])
story.extend(para(t) for t in ['实测球型、采购、加工、紧固载荷和样机试验仍未执行；所有真实结果保持空白。','R2的72只样本、216行测量模板和筛选计划继续适用。本轮没有改变轮缝、球头捕获、导套先回缩、先脱筒后转头等原机械关系。'])
page('14 / 官方外形资料与重建',['以下资料仅支持通用紧固件外形建模，不代表已采购型号、连接等级或载荷合格。'])
for source in s['sources']:
    story.append(para(source['fact']));story.append(Paragraph(f'<link href="{html.escape(source["url"],quote=True)}" color="#087b80">{html.escape(source["url"])}</link>',small))
story.append(para('重建顺序：tools/check_r3_geometry.py → tools/build_r3_package.py → blender/build_r3_scene.py → tools/build_r3_manual.py → tools/finish_r3_delivery.py。真实记录须另存；BLANK模板重建会覆盖。',small))
def footer(c,doc):
    c.setFont('CN',8);c.setFillColor(HexColor('#526677'));c.drawString(38,19,'BM1 R3 / 低速连接细化 / 采购与样机试验未完成');c.drawRightString(804,19,str(doc.page))
SimpleDocTemplate(str(O/'BM1_R3_connection_drawing_book.pdf'),pagesize=landscape(A4),leftMargin=42,rightMargin=42,topMargin=30,bottomMargin=35).build(story,onFirstPage=footer,onLaterPages=footer)
(R/'reports/r3_pdf_expected.json').write_text(json.dumps(dict(planned_pages=planned_pages),indent=2),encoding='utf-8');print('R3 PDF',planned_pages,'planned pages')
