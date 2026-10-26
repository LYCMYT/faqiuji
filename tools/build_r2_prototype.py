"""Rebuild R2 preparation artifacts from data/. No fabricated physical evidence."""
from pathlib import Path
import sys,json,csv,copy,html,math,hashlib
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import cadquery as cq
from cad.parts.recipe import build
from tools.render_cad_preview import render
from PIL import Image as PILImage,ImageDraw,ImageFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Image,PageBreak,Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def read(p):return json.loads((R/p).read_text(encoding='utf-8'))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
S=read('data/r2_prototype.json');routes=read('data/r2_process_routes.json')['routes'];parts=read('data/parts.json')
P={k:v['value'] for k,v in read('data/design.json')['parameters'].items()}
E=read('data/r1_engineering.json');G=read('data/geometry.json')['instances']
O=R/'output/prototype_r2';O.mkdir(exist_ok=True)
for d in ['step','dxf','drawings']:(O/d).mkdir(exist_ok=True)
assert set(routes)=={p['part_id'] for p in parts}
def csvout(name,keys,rows):
    with (O/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)

samples=[]
for group in S['samples']:
    for n in range(1,group['planned_count']+1):
        samples.append(dict(sample_id=f"{group['group']}-{n:03d}",model=group['model'],tube_plan=(n-1)//group['published_per_tube']+1,role='封存复核' if n>group['planned_count']-group['holdout_count'] else group['role'],wear_remeasure_planned=n<=group['wear_remeasure_count'],status='PLANNED_NOT_RECEIVED',actual_batch=None,actual_speed_label=None,received_date=None,photo=None))
csvout('sample_register_PLAN.csv',list(samples[0]),samples)
measure=[]
for a in samples:
    for rep in range(1,S['measurement']['repeats']+1):
        measure.append(dict(sample_id=a['sample_id'],repeat=rep,status='NOT_MEASURED',actual_condition=None,cork_diameter_x_mm=None,cork_diameter_y_mm=None,cork_height_mm=None,skirt_max_diameter_mm=None,overall_height_mm=None,mass_g=None,temperature_C=None,humidity_percent=None,instrument_id=None,calibration_record=None,operator=None,date=None,photo=None))
csvout('measurements_PLAN.csv',list(measure[0]),measure)
csvout('stack_measurements_BLANK.csv',['stack_id','sequence_index','added_sample_id','rotation_deg','height_mm','incremental_pitch_mm','force_N','temperature_C','humidity_percent','operator','date','evidence'],[])
trials=[]
for radius in E['separator']['pad_radius_candidates_mm']:
    for group in [*S['trial_plan']['feather_groups'],'M350']:
        for count in S['trial_plan']['stack_counts']:
            trials.append(dict(trial_id=f'R{radius}-{group}-N{count}',stage='NYLON_EXPLORATORY' if group=='M350' else 'FEATHER_SCREEN',radius_mm=radius,group=group,planned_stack_count=count,planned_cycles=S['trial_plan']['nylon_cycles_per_cell'] if group=='M350' else S['trial_plan']['screening_cycles_per_cell'],status='NOT_RUN',actual_sample_ids=None,actual_cycles=None,single_feed_count=None,double_feed_count=None,jam_count=None,damage_count=None,force_trace=None,hardware_revision=None,video=None,result=None))
csvout('screening_trials_PLAN.csv',list(trials[0]),trials)
csvout('holdout_confirmation_PLAN.csv',['stage','group','sample_ids','radius_mm','planned_cycles','actual_cycles','status','result'],[dict(stage='AFTER_SELECTION',group='AS30',sample_ids=';'.join(a['sample_id'] for a in samples if a['role']=='封存复核'),radius_mm=None,planned_cycles=S['trial_plan']['holdout_cycles'],actual_cycles=None,status='BLOCKED_UNTIL_SELECTION_AND_FIXTURE_VERIFIED',result=None)])
rfq=[]
for p in parts:
    route,gate=routes[p['part_id']]
    rfq.append(dict(part_id=p['part_id'],assembly_id=p['assembly_id'],name=p['name'],main_item_quantity=p['quantity'],route_choice=route,unresolved_gate=gate,status='RFQ_ONLY',supplier=None,material_lot=None,quote_CNY=None,lead_time_days=None,drawing_revision=None,interface_confirmed=False,manufacture_released=False))
csvout('manufacturing_routes_44_RFQ.csv',list(rfq[0]),rfq)
csvout('supplier_response_BLANK.csv',['rfq_id','part_id','supplier','model','material_grade','material_lot','drawing_file','drawing_revision','unit_price_CNY','tax_included','lead_time_days','actual_hole_drawing','mass_kg','ratings_file','inspection_report','proposed_changes','review_status'],[])
dump(O/'evidence_status.json',{k:S[k] for k in ['revision','physical_measurements','supplier_confirmations','orders','prototype_results','manufacturing_release']})

# True CAD curve profiles; dimension values measured from generated solids.
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',23)
smallfont=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19)
checks=[];coupons=[]
for radius in E['separator']['pad_radius_candidates_mm']:
    for original in [a for a in G if a['part_id']=='PRT-0603']:
        side=original['instance_id'].split('__')[-1];name=f'PRT-0603-R2-R{radius}-{side}'
        rec=copy.deepcopy(original['shape']);rec['children'][1]['radius']=radius
        world=build(rec,P);b=world.BoundingBox();offset=[b.xmin,b.ymin,b.zmin]
        sh=world.translate(tuple(-v for v in offset));box=sh.BoundingBox()
        sp=O/'step'/f'{name}.step';cq.exporters.export(sh,str(sp))
        # Top-face wires are projected to XY at Z=0 for 1:1 millimetre DXF.
        top=cq.Workplane('XY').add(sh).faces('>Z').val()
        profile=top.outerWire().translate((0,0,-box.zmax))
        cq.exporters.exportDXF(profile,str(O/'dxf'/f'{name}.dxf'))
        re=cq.importers.importStep(str(sp)).val()
        assert sh.isValid() and re.isValid() and len(re.Solids())==1 and re.Volume()>0
        assert abs(re.Volume()-sh.Volume())<.001
        checks.append(dict(file=sp.relative_to(R).as_posix(),valid=True,solids=1,volume_mm3=re.Volume(),volume_roundtrip_error_mm3=abs(re.Volume()-sh.Volume())))
        render([(name,sh)],O/'drawings'/f'{name}_iso',name+' / POM-C 试配毛件')
        im=PILImage.new('RGB',(1200,780),'#f4f7f9');d=ImageDraw.Draw(im)
        d.text((30,20),name+'  |  曲面试配 / 无装机孔位',font=font,fill='#183a4d')
        verts=[]
        for edge in sh.Edges():
            points,_=edge.sample(45 if edge.geomType()!='LINE' else 2)
            verts.append([p.toTuple() for p in points])
        for axes,origin,label in [((0,1),(210,340),'俯视 XY'),((0,2),(540,340),'正视 XZ'),((1,2),(920,340),'侧视 YZ')]:
            lengths=[box.xlen,box.ylen,box.zlen];scale=min(250/lengths[axes[0]],230/lengths[axes[1]])
            for pts in verts:
                xy=[(origin[0]+(p[axes[0]]-lengths[axes[0]]/2)*scale,origin[1]-(p[axes[1]]-lengths[axes[1]]/2)*scale) for p in pts]
                d.line(xy,fill='#183a4d',width=2)
            d.text((origin[0]-100,120),label,font=font,fill='#087b80')
        lines=[f'单位 mm；局部原点为实体包围盒最小角；原机头坐标偏移 {offset[0]:.3f}, {offset[1]:.3f}, {offset[2]:.3f}',f'实际实体外包络：X {box.xlen:.3f} / Y {box.ylen:.3f} / Z {box.zlen:.3f}；接触圆弧 R{radius}',f'试配询价要求：曲面轮廓 ±{S["manufacturing"]["coupon_profile_tolerance_mm"]}；厚度 ±{S["manufacturing"]["coupon_thickness_tolerance_mm"]}；未经加工厂确认。','STEP为精确曲面；DXF为1:1毫米顶面外轮廓；本PNG为缩放视图，不得量图下料。','去毛刺、接触面平滑；固定方式待冻结。本件仅为试配毛件，不是可直接安装的夹块。']
        for n,t in enumerate(lines):d.text((30,510+n*43),t,font=smallfont,fill='#183a4d')
        im.save(O/'drawings'/f'{name}_sheet.png')
        coupons.append(dict(part_id=name,parent_id='PRT-0603',assembly_id='ASM-06',source_instance=original['instance_id'],radius_mm=radius,side=side,quantity=S['manufacturing']['coupon_quantity_each'],material='POM-C 未填充本色',bbox_x_mm=box.xlen,bbox_y_mm=box.ylen,bbox_z_mm=box.zlen,local_origin_in_source_mm=offset,shape_recipe=rec,source_parameters='data/design.json',status='FIT_BLANK_NO_MOUNTING_INTERFACE'))
dump(O/'coupon_index.json',coupons)
csvout('coupon_RFQ.csv',['part_id','radius_mm','side','quantity','material','bbox_x_mm','bbox_y_mm','bbox_z_mm','status'],[{k:a[k] for k in ['part_id','radius_mm','side','quantity','material','bbox_x_mm','bbox_y_mm','bbox_z_mm','status']} for a in coupons])
csvout('coupon_inspection_BLANK.csv',['part_id','material_certificate','actual_x_mm','actual_y_mm','actual_thickness_mm','profile_deviation_mm','burr_check','surface_check','instrument','operator','date','evidence_file','result'],[dict(part_id=a['part_id'],**{k:None for k in ['material_certificate','actual_x_mm','actual_y_mm','actual_thickness_mm','profile_deviation_mm','burr_check','surface_check','instrument','operator','date','evidence_file','result']}) for a in coupons])

# Chinese manual, tables and individual native-solid views.
pdfmetrics.registerFont(TTFont('CN','C:/Windows/Fonts/msyh.ttc',subfontIndex=0))
style=ParagraphStyle('body',fontName='CN',fontSize=10.5,leading=17,textColor=HexColor('#183a4d'),wordWrap='CJK',spaceAfter=8)
head=ParagraphStyle('head',parent=style,fontSize=22,leading=30,spaceAfter=15)
small=ParagraphStyle('small',parent=style,fontSize=9,leading=14)
story=[]
def para(t,sty=style):return Paragraph(html.escape(str(t)),sty)
def page(title,lines=()):
    if story:story.append(PageBreak())
    story.append(para(title,head));story.extend(para(t) for t in lines)
def table(rows,widths):
    t=Table([[para(x,small) for x in row] for row in rows],colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#dce9ec')),('GRID',(0,0),(-1,-1),.4,HexColor('#b7cbd2')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]));story.append(t)
page('BM1 / R2 球样与加工工作包',['版本 '+S['revision']+' / '+S['decision_date'],'已确定首轮球样组合和加工路线；本包供采购准备、加工询价和低速试配。','R1总装、44主项及已有STEP/BLEND/GLB/动画继续作为设计参考。R2新增8个独立夹块试配毛件，保留PRT-0603与ASM-06编号关系。','当前：未采购、未收货、未加工、未测球、未进行硬件试验。整机制造未放行。','所有公开规格与项目候选均有单独状态；空白记录须复制后填写，避免重建覆盖真实证据。'])
story.append(Image(str(R/'output/engineering/separator_bench.png'),300,225))
page('01 / 首轮样本：72只，3个型号')
table([['型号 / 用途','包装与计划','速度选择','复核安排']]+[[g['model']+' / '+g['role'],f"{g['tubes']}筒 × {g['published_per_tube']}只 = {g['planned_count']}只",g['speed_choice'],f"封存{g['holdout_count']}只；同球磨损复测{g['wear_remeasure_count']}只"] for g in S['samples']],[200,130,260,150])
story.extend(para(t) for t in S['sampling_rules'])
m=S['measurement']
page('02 / 测量条件与方法',[S['environment']['note'],m['instrument_status'],f"量具采购目标：卡尺{m['caliper_range_mm']}mm、分辨率{m['caliper_resolution_mm']}mm；秤分辨率{m['balance_resolution_g']}g；高度测量{m['height_range_mm']}mm；测力仪候选{m['force_gauge_range_N']}N。",'此处仪器量程和分辨率是采购目标，不是已校准精度。']+m['procedure'])
page('03 / 低速筛选与复核',S['trial_plan']['gates'])
table([['阶段','计划条件','计划动作次数','当前结果'],['天然羽毛球筛选','各候选半径、天然球型号及堆叠数量分别筛选',str(sum(a['planned_cycles'] for a in trials if a['stage']=='FEATHER_SCREEN')),'未执行'],['尼龙探索','候选半径和堆叠数量独立探索',str(sum(a['planned_cycles'] for a in trials if a['stage']=='NYLON_EXPLORATORY')),'前置试配未执行'],['封存样本复核','筛选后选定半径；封存AS30重复循环',str(S['trial_plan']['holdout_cycles']),'半径未选定，尚未执行']],[145,350,110,135])
page('04 / 加工条件与材料选择',[S['manufacturing'][k] for k in ['preferred_shop','aluminum','polymer','clear_parts','covers','printed_parts','finish']])
page('05 / 加工询价边界与首件检查',[S['manufacturing']['tolerance_status'],S['manufacturing']['coupon_interface_status'],'R1台架的紧固孔、支撑连接、锚固和刚度仍未冻结；加工方须先返回DFM和安装方案。不能把实体无相交当作结构承载或紧固合格。','球筒/导套按现有尺寸询价；若无合适管料或薄壁加工变形，应提出有记录的尺寸与结构变更，再重建和检查，不能自行缩小模型部件。','供应商需返回：'+'；'.join(S['manufacturing']['required_supplier_returns']),'高速轮组先完成额定资料、驱动计算、轴系连接和专用防护验证；本轮低速试配结果不提供转速上限、落点精度或安全等级。'])
for start in range(0,len(rfq),8):
    page(f'06 / 44主项工艺路线 {start+1}-{min(start+8,len(rfq))}')
    table([['编号 / 名称','选定询价路线','开工前待确认']]+[[a['part_id']+' '+a['name'],a['route_choice'],a['unresolved_gate']] for a in rfq[start:start+8]],[175,270,295])
for a in coupons:
    page(a['part_id']+' / 独立试配毛件')
    story.append(Image(str(O/'drawings'/f'{a["part_id"]}_sheet.png'),700,455))
page('07 / 文件使用与证据状态',['sample_register_PLAN.csv：72个计划编号，收货、批号、照片空白；measurements_PLAN.csv：216行重复测量占位，所有实际尺寸空白。','screening_trials_PLAN.csv：36组筛选条件；holdout_confirmation_PLAN.csv：复核计划。stack_measurements_BLANK.csv保留逐只堆叠原始记录。','manufacturing_routes_44_RFQ.csv：44个主项工艺选择；coupon_RFQ.csv：8个无安装孔毛件；supplier_response_BLANK.csv：报价和实际接口回填。','重建：在工程根目录使用 .venv/Scripts/python.exe tools/build_r2_prototype.py。生成器只读取data参数，不读取或覆盖用户另存的实测记录。','已建模：四种弧面左右毛件。数字检查：每件原生实体与STEP回读。采购接口待确认：固定方式、供应商孔图、执行器与材料供货。样机试验：实际尺寸、套叠、夹持、分球力及损伤均未执行。'])
page('08 / 官方资料与选择依据',['来源查阅日：2026-10-26。官方产品信息用于样本/材料类别选择；具体样本尺寸与本机适配情况须测量。'])
for s in S['sources']:
    story.append(para(s['id']+'：'+s['fact']+' 用途：'+s['use']))
    story.append(Paragraph(f'<link href="{html.escape(s["url"],quote=True)}" color="#087b80">{html.escape(s["url"])}</link>',small))
def footer(c,doc):
    c.setFont('CN',8);c.setFillColor(HexColor('#526677'));c.drawString(36,20,'BM1 R2 / 询价与低速试配准备 / 实物验证未执行');c.drawRightString(805,20,str(doc.page))
pdf=O/'BM1_R2_sample_manufacturing_manual.pdf'
SimpleDocTemplate(str(pdf),pagesize=landscape(A4),leftMargin=42,rightMargin=42,topMargin=32,bottomMargin=36).build(story,onFirstPage=footer,onLaterPages=footer)

intro=['R2已选择AS-30 36只、AS-10 24只、MAVIS350 12只；实际未采购收货。','优先6061-T651机加工板件、POM-C可换试配毛件、透明PC管件询价。','本目录是R1的补充；8个STEP和DXF只含夹块试配毛件，固定接口待冻结。','运行 tools/build_r2_prototype.py 重建本包。运行 tools/check_r2_prototype.py 校验。','所有PLAN/BLANK记录重建时会覆盖，请复制到单独实测目录后填写。']
links=[('BM1_R2_sample_manufacturing_manual.pdf','中文说明与8件图页'),('sample_register_PLAN.csv','72只球样编号'),('measurements_PLAN.csv','216行测量模板'),('manufacturing_routes_44_RFQ.csv','44主项加工路线'),('coupon_RFQ.csv','8件试配毛件询价'),('screening_trials_PLAN.csv','低速筛选矩阵'),('../../viewer/','R1总装查看器')]
body='<h1>BM1 R2 · 球样与加工工作包</h1>'+''.join('<p>'+html.escape(t)+'</p>' for t in intro)+'<ul>'+''.join(f'<li><a href="{u}">{t}</a></li>' for u,t in links)+'</ul>'
for a in coupons:body+=f'<h2>{a["part_id"]}</h2><a href="step/{a["part_id"]}.step">STEP</a> · <a href="dxf/{a["part_id"]}.dxf">DXF</a><img style="width:100%" src="drawings/{a["part_id"]}_sheet.png">'
(O/'index.html').write_text('<!doctype html><html lang="zh"><meta charset="utf-8"><title>BM1 R2</title><style>body{max-width:1100px;margin:40px auto;background:#f4f7f9;color:#183a4d;font:16px/1.8 system-ui}a{color:#087b80}</style>'+body+'</html>',encoding='utf-8')
(O/'README.txt').write_text('\n'.join(intro),encoding='utf-8')
dump(R/'reports/r2_build_validation.json',dict(revision=S['revision'],step_checks=checks,sample_plan_count=len(samples),measurement_plan_rows=len(measure),screening_cells=len(trials),main_item_routes=len(rfq),physical_evidence_count=0,manufacturing_release=False))
print('R2 BUILT',len(coupons),'native STEP/DXF coupons;',len(samples),'planned samples;',len(rfq),'routes')
