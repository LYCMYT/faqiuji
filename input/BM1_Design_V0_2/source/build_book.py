"""Build the illustrated design brief and concept SVG assets. No production CAD is generated."""
import sys, json, csv, math, re
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, Color, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import fitz
from design_data import ROOT, META, PARAMS as P, ASSEMBLIES, ASM, PARTS, JOINTS, SOURCES, UNRESOLVED, export_data
from drawings import draw_mesh, part_mesh, world_scene, subassembly_mesh, exploded_subassembly, svg, box, cylinder, tube, shuttle, Mesh, mul

FONT_PATH=Path('/tmp/bm1_cjk.ttf')
FONT_PATH.write_bytes(fitz.Font('china-s').buffer)
pdfmetrics.registerFont(TTFont('CJK',str(FONT_PATH)))
pdfmetrics.registerFont(TTFont('Sans','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('SansBold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))

W,H=841.89,595.28
BG='#F4F7F7'; INK='#203747'; MUTED='#617480'; TEAL='#127F76'; LINE='#D7E1E4'; GOLD='#D7932D'; CORAL='#C76A50'
OUT=ROOT/'BM1_Design_Book_V0_2.pdf'
PAGE_INDEX=[]; TEXT_BOXES=[]

def txt(c,s,x,y,size=10,color=INK,font='CJK'):
    c.setFont(font,size);c.setFillColor(HexColor(color));c.drawString(x,y,str(s))

def para(c,s,x,y,w,size=10.2,leading=15.5,color=INK,font='CJK',maxlines=None):
    lines=[]
    for block in str(s).split('\n'):
        line=''
        for ch in block:
            if pdfmetrics.stringWidth(line+ch,font,size)>w and line:
                lines.append(line);line=ch
            else:line+=ch
        lines.append(line)
    if maxlines is not None and len(lines)>maxlines:raise ValueError(f'Text overflow {len(lines)}>{maxlines}: {s[:30]}')
    for line in lines:txt(c,line,x,y,size,color,font);y-=leading
    TEXT_BOXES.append((c.getPageNumber(),x,y+leading,w,len(lines)*leading,s[:40]))
    return y

def pill(c,s,x,y,color=TEAL):
    tw=pdfmetrics.stringWidth(s,'CJK',8.7)
    c.setFillColor(HexColor(color));c.roundRect(x,y-4,tw+16,18,6,fill=1,stroke=0)
    txt(c,s,x+8,y+1,8.7,'#FFFFFF')

def panel(c,x,y,w,h,color='#FFFFFF'):
    c.setFillColor(HexColor(color));c.roundRect(x,y,w,h,10,fill=1,stroke=0)

def line(c,x1,y1,x2,y2,color=LINE,width=.8,dash=None):
    c.setStrokeColor(HexColor(color));c.setLineWidth(width)
    c.setDash(dash or []);c.line(x1,y1,x2,y2);c.setDash([])

def arrow(c,a,b,color=TEAL,width=1.4):
    line(c,*a,*b,color,width)
    dx,dy=b[0]-a[0],b[1]-a[1];l=math.hypot(dx,dy) or 1;ux,uy=dx/l,dy/l
    p=c.beginPath();p.moveTo(*b);p.lineTo(b[0]-7*ux+3*uy,b[1]-7*uy-3*ux);p.lineTo(b[0]-7*ux-3*uy,b[1]-7*uy+3*ux);p.close()
    c.setFillColor(HexColor(color));c.drawPath(p,fill=1,stroke=0)

def dim(c,a,b,s,offset=0):
    # horizontal or vertical dimension line in drawing space
    if abs(a[1]-b[1])<.01:
        y=a[1]+offset;line(c,a[0],a[1],a[0],y,MUTED,.5);line(c,b[0],b[1],b[0],y,MUTED,.5)
        line(c,a[0],y,b[0],y,MUTED,.7)
        for x in [a[0],b[0]]:line(c,x-3,y-3,x+3,y+3,MUTED,.7)
        tw=pdfmetrics.stringWidth(s,'CJK',8.5);panel(c,(a[0]+b[0]-tw)/2-4,y-1,tw+8,13,BG);txt(c,s,(a[0]+b[0]-tw)/2,y+2,8.5,MUTED)
    else:
        x=a[0]+offset;line(c,a[0],a[1],x,a[1],MUTED,.5);line(c,b[0],b[1],x,b[1],MUTED,.5)
        line(c,x,a[1],x,b[1],MUTED,.7)
        for y in [a[1],b[1]]:line(c,x-3,y-3,x+3,y+3,MUTED,.7)
        txt(c,s,x+5,(a[1]+b[1])/2,8.5,MUTED)

def header(c,title,kicker='BM1  /  V0.2  /  CONCEPT DESIGN',subtitle=None):
    c.setFillColor(HexColor(BG));c.rect(0,0,W,H,fill=1,stroke=0)
    txt(c,kicker,34,H-32,8.5,TEAL,'Sans')
    txt(c,title,34,H-69,24,INK)
    if subtitle:txt(c,subtitle,35,H-92,9.5,MUTED)
    PAGE_INDEX.append({'page':c.getPageNumber(),'title':title})

def footer(c):
    txt(c,'概念尺寸与功能示意  |  需经 CAD 校核、采购接口确认与样机试验后升级',34,20,8,MUTED)
    txt(c,f'{c.getPageNumber():02d}',W-57,19,10,TEAL,'SansBold')
    c.showPage()

def textblock(c,title,body,x,y,w=300,color=TEAL):
    txt(c,title,x,y,10.3,color)
    return para(c,body,x,y-18,w,10,15)-14

def table(c,rows,widths,x,y,row_h=27,headerrow=None,size=9):
    if headerrow:
        c.setFillColor(HexColor(TEAL));c.roundRect(x,y-row_h,sum(widths),row_h,5,fill=1,stroke=0)
        xx=x
        for t,w in zip(headerrow,widths):txt(c,t,xx+8,y-row_h+9,size,'#FFFFFF');xx+=w
        y-=row_h
    for i,row in enumerate(rows):
        c.setFillColor(HexColor('#FFFFFF' if i%2==0 else '#EDF3F3'));c.rect(x,y-row_h,sum(widths),row_h,fill=1,stroke=0)
        xx=x
        for t,w in zip(row,widths):para(c,str(t),xx+8,y-17,w-14,size,12,maxlines=max(1,int((row_h-6)/12)));xx+=w
        y-=row_h
    return y

def callout(c,proj,p,text,x,y,color=TEAL):
    a=proj(p);mid=(x-9,y+4)
    line(c,*a,*mid,color,.8)
    c.setFillColor(HexColor(color));c.circle(*a,2.4,fill=1,stroke=0)
    txt(c,text,x,y,9,color)

def draw_cover(c):
    c.setFillColor(HexColor(BG));c.rect(0,0,W,H,fill=1,stroke=0)
    txt(c,'BM1',42,526,42,TEAL,'SansBold')
    txt(c,'羽毛球发球机',42,471,30)
    txt(c,'三维建模设计方案',42,429,26)
    para(c,'面向 Codex 的结构方案、图形目录、部件说明与参数化建模任务书。',44,377,285,13,21)
    for i,(num,label) in enumerate([('10','功能总成'),('44','关键部件独立页'),('V0.2','概念设计版本')]):
        x=44+i*108
        txt(c,num,x,271,26,TEAL,'SansBold');txt(c,label,x,247,9.5,MUTED)
    para(c,'后场与前场训练  /  高度与距离标定  /  实时语音调整',44,192,300,10.5,18)
    pill(c,'2026.10.26',44,118)
    para(c,'本册已经完成设计规划与示意图。实际工程实体、加工孔位和性能仍由后续建模与样机阶段完成。',44,91,305,9.2,14)
    panel(c,395,57,411,489,'#E9F0EF')
    draw_mesh(c,world_scene(True,head_pitch=18,head_yaw=-12),(424,83,354,432))
    txt(c,'整机结构示意  /  颜色区分功能部件',421,68,9,MUTED)
    PAGE_INDEX.append({'page':1,'title':META['title']});footer(c)

def draw_readguide(c):
    header(c,'先看清楚本轮交付与建模边界',subtitle='本轮交付的是完整设计任务书；下一轮 Codex 按此建立并检查真实 CAD。')
    y=453
    for title,body in [
      ('本轮已经完成','整机结构方案、统一坐标与主要尺寸、动作顺序、10 总成和 44 主项介绍页、Codex 执行规范、BOM/关节/接口数据、可追踪的待验证清单。'),
      ('下一轮 Codex 应完成','可重建的参数化实体、总装与逐件 STEP、Blender 场景、GLB 浏览模型、从真实模型生成的尺寸/爆炸图、运动检查和最终图文册。'),
      ('进入制造前必须补齐','采购件实尺寸、安装孔与配合、公差与载荷、防护/停止电气设计，以及单球分离、出轮翻转和落点实测。')]:
        panel(c,34,y-98,370,111);y=textblock(c,title,body,49,y-13,338)-20
    panel(c,430,94,377,390)
    txt(c,'如何阅读本册',450,456,17)
    y=423
    for n,t,b in [('01','总体图与动作图','先确认球如何从固定筒到运动机头。'),('02','总成与 44 部件页','按稳定编号查功能、接口、材料和未定项。'),('03','机器可读参数与任务书','把整个压缩包交给 Codex，禁止另建一套尺寸。'),('04','分阶段验收','先做核心避让和装配，再做外观、渲染及动画。')]:
        pill(c,n,450,y,TEAL);txt(c,t,493,y+1,12);para(c,b,493,y-18,280,10,15);y-=83
    footer(c)

def draw_overview(c):
    header(c,'总装结构与功能分区',subtitle='固定供球器与运动机头共用升降基准；只有轮组、托架和推送机构参与俯仰。')
    panel(c,34,66,468,421);panel(c,520,66,286,421)
    proj=draw_mesh(c,world_scene(False),(64,85,391,375))
    y=455
    for aid,name,col,role in ASSEMBLIES:
        c.setFillColor(HexColor(col));c.circle(537,y+3,4,fill=1,stroke=0)
        txt(c,f'{aid}  {name}',549,y,10.3)
        para(c,role,549,y-15,237,8.8,12)
        y-=38
    txt(c,'去罩结构示意',57,462,10,TEAL)
    footer(c)

def draw_orthos(c):
    header(c,'整体包络与正投影视图',subtitle='所有尺寸为 mm；H 表示球头中心/两轮最窄口中心的离地高度。')
    scene=world_scene(False)
    panel(c,34,111,244,375);panel(c,290,111,244,375);panel(c,546,111,261,375)
    p1=draw_mesh(c,scene,(55,147,199,310),'front')
    p2=draw_mesh(c,scene,(310,147,202,310),'side')
    p3=draw_mesh(c,scene,(567,232,219,219),'top')
    txt(c,'前视  从 +X 看向机器',53,465,10,TEAL)
    txt(c,'侧视  从 -Y 看向机器',309,465,10,TEAL)
    txt(c,'顶视  +X 为图中右方',565,465,10,TEAL)
    dim(c,p1((0,-400,0)),p1((0,400,0)),'支撑宽 800',-15)
    dim(c,p2((-425,0,0)),p2((425,0,0)),'支撑深 850',-15)
    para(c,'底架 650×600\n展开接地范围 850×800\n轴高 H=1500，手调 1400–1800\n总高 H+670，约 2070–2470\n默认轴高时总高约 2170',564,209,220,10.2,18)
    para(c,'总高包含约 20 顶盖。快拆球筒采用侧向移除，避免再额外要求向上抽出整根 540 管长。尺寸并非防倾覆结论。',39,85,760,10,15)
    footer(c)

def draw_exploded(c):
    header(c,'总装拆解关系与展示爆炸方向',subtitle='图中分离位移仅用于说明结构层次；真实拆卸路径另见维修页。')
    scene=world_scene(True)
    offsets={'ASM-01':(0,0,-80),'ASM-02':(0,0,50),'ASM-03':(360,0,100),
     'ASM-04':(0,0,450),'ASM-05':(450,0,700),'ASM-06':(-650,0,430),
     'ASM-07':(700,-200,300),'ASM-08':(600,300,450),'ASM-09':(650,-300,30),'ASM-10':(-500,-200,250)}
    exp=[]
    for m in scene:
        aid='ASM-'+m.pid[4:6] if m.pid.startswith('PRT-') else 'ASM-07'
        exp.append(m.transformed(offsets.get(aid,(0,0,0))))
    panel(c,34,68,529,419);draw_mesh(c,exp,(49,86,498,378))
    y=456
    for a,t,col,role in ASSEMBLIES:
        txt(c,a,586,y,10,col,'SansBold');txt(c,t,655,y,10.5)
        y-=35
    para(c,'先按总成拆解，再在总成页定位各主项。紧固件、线束和采购模组内部件在 V1 工程 BOM 中继续展开。',585,110,218,9.7,15)
    svg(exp,ROOT/'figures'/'F05_exploded.svg',title='BM1 exploded concept')
    footer(c)

def draw_core(c):
    header(c,'双轮与羽毛球的正确空间关系',subtitle='轮轴沿局部 Z。羽毛球初始轴线也沿 Z，球头朝下；侧向加速后需验证自然翻转。')
    panel(c,34,82,473,404);panel(c,523,82,284,404)
    ox,oy,s=345,291,1.0
    for sy in [-1,1]:
        c.setFillColor(HexColor('#DFA746'));c.setStrokeColor(HexColor('#B47D22'));c.setLineWidth(1)
        c.circle(ox,oy+sy*82.5,70,fill=1,stroke=1)
        c.setFillColor(HexColor('#F4F7F7'));c.circle(ox,oy+sy*82.5,9,fill=1,stroke=0)
        txt(c,'Ø140',ox-20,oy+sy*82.5-4,10,'#71521E','SansBold')
    for xpos,name,co in [(-190,'装载 -190',TEAL),(-85,'脱筒 -85',CORAL),(-5,'喂入 -5',GOLD)]:
        xx=ox+xpos*s
        c.setStrokeColor(HexColor(co));c.setDash([3,3]);c.circle(xx,oy,34,fill=0,stroke=1);c.setDash([])
        c.setFillColor(HexColor(co));c.circle(xx,oy,13.25,fill=1,stroke=0)
        if xpos==-5:
            txt(c,'喂入 -5',421,oy-21,8.9,GOLD)
            line(c,xx+15,oy-4,416,oy-16,GOLD,.7)
        else:txt(c,name,xx-30,oy-55,8.9,co)
    arrow(c,(155,130),(260,130),TEAL);txt(c,'前移脱筒 105',154,113,9,TEAL)
    arrow(c,(270,130),(340,130),CORAL);txt(c,'后续喂入约 80',271,113,9,CORAL)
    arrow(c,(414,oy),(482,oy),TEAL);txt(c,'+X 出球',424,oy+12,9,TEAL)
    line(c,ox-80,oy,ox+70,oy,MUTED,.5,[4,3])
    txt(c,'俯视示意  虚线圆表示羽毛裙最大外径',52,459,10,TEAL)
    txt(c,'双轮中心距 165 = 140 + 25',82,92,9.2,MUTED)
    y=456
    for t,b in [('只接触球头','轮面 Z=-8…8；球头示意 Z=-13…13；羽毛从 Z=13 延伸到 Z=83。'),
      ('羽毛留空','羽毛裙最大直径按 68 建模，静态再放大 3。该余量不能代替动态验证。'),
      ('轮向必须一致','左轮沿 +Z 正向、右轮沿 -Z 正向，使内侧接触点切向速度都朝 +X。'),
      ('不能承诺球路','捕获后球不再绑定滑台。翻转距离、前场稳定性、转速与落点均等待实测。')]:
        y=textblock(c,t,b,541,y,247)
    footer(c)

def draw_sequence(c):
    header(c,'一次发球的动作顺序与互锁',subtitle='下列时间只表达先后顺序。真实节拍、释放时刻和喂入速度由试验决定。')
    states=[
     ('01','归零待装','机头角度归零，滑台在 -190；检查无球、导套上位。'),
     ('02','导向落单球','导套下降到 H-5；留住上部球堆，释放最低一球。'),
     ('03','夹持与收套','确认球入托与夹持；导套升到 H+110 并得到上位信号。'),
     ('04','前移脱筒','滑台从 -190 到 -85；整只羽毛球离开固定筒投影。'),
     ('05','瞄准与稳速','保持夹持，调整俯仰/偏航；等待实际位置和转速满足条件。'),
     ('06','释放并喂入','按验证窗口松夹并侧推；轮捕获后解除球与托架绑定。'),
     ('07','确认出球','出球检测与计数；空托先退到 -85；异常即停供球。'),
     ('08','返回装载','空头回俯仰/偏航零位，再将空托从 -85 退回 -190。')]
    for i,(n,t,b) in enumerate(states):
        col=i%4;row=i//4;x=34+col*196;y=287-row*201
        panel(c,x,y,184,184)
        pill(c,n,x+12,y+150,TEAL if i<4 else CORAL);txt(c,t,x+47,y+154,11.8)
        # Small sequence symbol with fixed tube, tray and direction.
        line(c,x+25,y+111,x+152,y+111,LINE,5)
        for yy in [-11,11]:
            c.setFillColor(HexColor('#DFA746'));c.circle(x+146,y+111+yy,9,fill=1,stroke=0)
        xx=x+(40 if i<3 or i==7 else 89 if i in [3,4,6] else 135)
        c.setFillColor(HexColor(TEAL));c.circle(xx,y+111,5,fill=1,stroke=0)
        if i in [1,2]:line(c,x+40,y+126,x+40,y+143,TEAL,4)
        if i in [3,5]:arrow(c,(x+44,y+91),(x+126,y+91),CORAL,1)
        para(c,b,x+12,y+71,160,9.2,14)
    footer(c)

def draw_motion(c):
    header(c,'导套避让与运动范围',subtitle='正仰角绕局部 -Y；固定球筒不跟随俯仰或偏航，但跟随整机的手动升降。')
    panel(c,34,82,353,404);panel(c,403,82,404,404)
    txt(c,'导套先收回，再允许托架前移',51,457,12,TEAL)
    for n,up in enumerate([False,True]):
        cx=119+n*164;base=169;s=.36
        # Side elevation using H-relative heights.
        c.setFillColor(HexColor('#D2E3DC'));c.setStrokeColor(HexColor(TEAL));c.rect(cx-14,base+110*s,28,540*s,fill=1,stroke=1)
        zb=110 if up else -5
        c.setFillColor(HexColor('#A5C8BD'));c.rect(cx-17,base+zb*s,34,150*s,fill=1,stroke=1)
        c.setFillColor(HexColor('#6F9F91'));c.rect(cx-38,base+280*s,76,70*s,fill=1,stroke=0)
        c.setFillColor(HexColor(GOLD));c.circle(cx,base,5,fill=1,stroke=0)
        c.setFillColor(HexColor('#DCE5DD'));p=c.beginPath();p.moveTo(cx-5,base+5);p.lineTo(cx-12,base+30);p.lineTo(cx+12,base+30);p.lineTo(cx+5,base+5);p.close();c.drawPath(p,fill=1,stroke=0)
        line(c,cx-50,base,cx+48,base,MUTED,.5,[3,3]);txt(c,'H',cx+51,base-3,9,MUTED,'Sans')
        txt(c,'上位' if up else '装载位',cx-17,135,10,TEAL)
        txt(c,'下缘 +110' if up else '下缘 -5',cx-26,118,9,MUTED)
    para(c,'固定管 ID76/OD80；外滑套 ID82/OD86。分球运动件最低处 ≥H+280，导套上位最高处 H+260，名义避让 20。',51,100,318,8.4,12)
    y=457
    for title,body in [
      ('工作角与校核角分开','工作仰角 0–55°、偏航 ±35°；数字校核扩大到俯仰 -10–60°、偏航 ±45°。组合姿态必须一起检查。'),
      ('固定与运动的真实层级','底盘 → 升降载架；其下并列固定供球器和偏航总成；偏航总成 → U 架 → 俯仰机头。球筒不可挂在俯仰层。'),
      ('头部采用阶梯窄尾','前部 X=-90…150 保持宽轮架；后部 X=-235…-90 收窄至 Y±45 并抬高底板，降低与 U 架/后支柱的干涉。'),
      ('检查仍未代替试验','约 280 的落球高度可能产生回弹；羽毛裙翻转、轮胎形变与振动不能由静态留空证明。')]:
        y=textblock(c,title,body,422,y,365)
    footer(c)

def draw_architecture(c):
    header(c,'语音控制与实际动作的连接',subtitle='本页定义功能和空间布置，不替代电气原理图或最终安全电路。')
    boxes=[(45,381,205,83,'手机与近讲耳麦','离线口令 / 云端自然对话',TEAL),
           (315,381,207,83,'白名单训练指令','目标、距离、高度、间隔',TEAL),
           (587,381,207,83,'本地状态机','限位 / 互锁 / 执行回执',TEAL),
           (45,213,205,100,'物理停止入口','机器急停 + 独立停发手柄',CORAL),
           (315,213,207,100,'驱动与供球机构','轮、偏航、俯仰、导套、夹持',GOLD),
           (587,213,207,100,'实际状态反馈','位置、转速、球检测、开盖',TEAL)]
    for x,y,w,h,t,b,col in boxes:
        panel(c,x,y,w,h);pill(c,t,x+14,y+h-30,col);para(c,b,x+14,y+27,w-28,10,15)
    arrow(c,(250,420),(309,420));arrow(c,(522,420),(580,420));arrow(c,(690,319),(690,378))
    arrow(c,(530,260),(584,260));arrow(c,(630,378),(485,319));arrow(c,(250,259),(307,259),CORAL)
    panel(c,34,72,774,110)
    para(c,'语音回复只在机器确认“已生效”后说完成。参数在供球安全间隔应用；启动、故障恢复和急停释放需要明确动作。本机通信失联暂停供球；仅互联网中断可回落到已验证的本地模式。',51,156,740,11,18)
    para(c,'机器舱内保留功率线、低电平信号线、应力释放、风道和维修区。不要在未选电压/电流前伪造精确端子接线。',51,99,740,10,15)
    footer(c)

def draw_maintenance(c):
    header(c,'拆装路径与服务空间',subtitle='维修路径以真正能取出零件为准；爆炸图中把零件移开不等于可维修。')
    scene=world_scene(False);panel(c,34,72,406,415);p=draw_mesh(c,scene,(55,92,350,361))
    for a,b in [((-190,0,2050),(-390,0,2050)),((0,-82,1500),(0,-280,1500)),((0,0,280),(-350,0,280))]:arrow(c,p(a),p(b),CORAL)
    y=455
    for t,b in [('球筒侧向拆','540 长球筒设计后侧快拆；补球前下降到可达高度或拆下地面装填。不得要求站高处给筒顶持续加球。'),
      ('发射轮与轮缘','侧罩打开、确认飞轮完全停转后拆轮；轴端、锁紧件和拉出方向必须可达。'),
      ('卡球与导套','通过检查窗定位，停机后拆分球盒侧盖或托架嵌件。手不能从出球口接近仍转动的轮。'),
      ('底舱与线束','电源、驱动和 IO 从后门维护；接插件拔出长度、工具直径及线缆最小弯曲半径由选型录入。'),
      ('稳定性与搬运','训练时支腿锁定、调平脚落地；停机并收好电缆再搬运，机头高位和满筒状态单独核验。')]:
        y=textblock(c,t,b,458,y,331)
    footer(c)

def draw_module(c,aid):
    a=ASM[aid];ps=[p for p in PARTS if p['assembly_id']==aid]
    header(c,f'{aid}  {a["name"]}',subtitle=a['role'])
    panel(c,34,76,443,409);panel(c,493,76,314,409)
    scene=exploded_subassembly(aid)
    draw_mesh(c,scene,(54,286,402,154))
    txt(c,'分总成拆解示意',52,456,11,a['color'])
    txt(c,'部件索引  /  各件分别缩放，非安装比例',52,266,8.7,MUTED)
    for i,p in enumerate(ps):
        col=i%3;row=i//3;xx=55+col*135;yy=211-row*52
        draw_mesh(c,part_mesh(p),(xx+4,yy+9,116,34))
        txt(c,p['part_id'],xx+29,yy-1,7.5,a['color'],'Sans')
    para(c,'上图位移仅用于拆解展示。安装尺寸、真实孔位及拆卸路径由工程模型核验。',52,92,402,8.7,12)
    y=455
    for p in ps:
        txt(c,p['part_id'],510,y,9.2,a['color'],'SansBold');txt(c,p['name'],596,y,10.2)
        y=para(c,p['function'],510,y-17,278,9.3,14)-16
    if y>120:
        para(c,'下一节每个主项各有独立图页。相同件多个实例共页；模组内部和标准件继续细分 BOM。',510,min(y-5,138),278,9.3,14,MUTED)
    svg(subassembly_mesh(aid),ROOT/'figures'/f'{aid}_parts.svg',title=f'{aid} part breakdown; each item independently scaled')
    svg(scene,ROOT/'figures'/f'{aid}_exploded.svg',title=f'{aid} exploded concept; display offsets only')
    footer(c)

def draw_part(c,p):
    aid=p['assembly_id'];page=c.getPageNumber();p['page']=page
    header(c,f'{p["part_id"]}  {p["name"]}',kicker=f'BM1  /  {aid}  /  PART SPECIFICATION',subtitle=f'{p["kind"]}  |  {ASM[aid]["name"]}  |  尺寸状态：概念初值')
    panel(c,34,76,421,410);panel(c,472,76,335,410)
    mesh=part_mesh(p)
    draw_mesh(c,mesh,(57,236,374,220))
    txt(c,'等轴测结构示意',51,466,9.5,p['color'])
    count='按传感位置展开' if p['quantity'] is None else str(p['quantity'])
    txt(c,f'主项数量 {count}',319,466,9,MUTED)
    line(c,51,219,438,219,LINE,.7)
    draw_mesh(c,mesh,(65,126,155,75),'top',wire=True)
    draw_mesh(c,mesh,(255,126,155,75),'front',wire=True)
    txt(c,'顶视示意',104,108,8.8,MUTED);txt(c,'正视示意',298,108,8.8,MUTED)
    dims=' × '.join(str(i) for i in p['bbox_mm'])
    txt(c,f'外形参考包络  {dims} mm',55,86,9.2,p['color'])
    y=457
    for t,b in [('功能',p['function']),('建模尺寸与形状',p['features']),('安装接口',p['interfaces']),('候选材料与工艺',p['material_candidate']),('仍需验证',p['validation']),('拆装方向',p['removal'])]:
        y=textblock(c,t,b,488,y,302,p['color'])
    if y<74:raise ValueError(f'Part page overflow {p["part_id"]}: {y}')
    svg(mesh,ROOT/'figures'/f'{p["part_id"]}.svg',title=p['part_id']+' concept envelope '+dims+' mm')
    footer(c)

def draw_bom(c,chunk,number):
    header(c,f'部件索引与数量表 {number}',subtitle='44 是本册的关键主项数；采购模组、传感器族和自制总成不等于已冻结的物理零件数量。')
    rows=[]
    for p in chunk:
        q='待展开' if p['quantity'] is None else p['quantity']
        rows.append([p['part_id'],p['name'],p['kind'],q,p.get('page','-')])
    table(c,rows,[106,245,180,85,158],34,482,17.5,['编号','中文名称','类型','数量','独立页'],8.2)
    para(c,'标准件另表列出：M3/M4/M5/M6 等仅为尺寸族候选。长度、等级、垫圈、螺纹咬合和防松方法依接口与载荷选定，不生成虚假的采购数量。',36,63,765,9.5,14)
    footer(c)

def draw_cad(c,second=False):
    if not second:
        header(c,'Codex 建模路线与唯一数据源',subtitle='工程实体、展示模型和图纸从同一套参数与部件清单生成。')
        steps=[('01','数据与基准','读取 design/parts/interfaces/joints；先做 100 mm 标定块和三轴检验。'),
          ('02','机械核心','建立真实球体包络、轮组、夹持滑台、导套和分球盒，解决装载与释放通路。'),
          ('03','整机装配','接入升降、偏航、俯仰和底盘；核查阶梯窄尾、线束及检修空间。'),
          ('04','展示与文件','由实体导出 STEP 与 GLB；Blender 生成材质、相机、爆炸、动画及图文册。')]
        y=458
        for n,t,b in steps:
            panel(c,34,y-76,418,89);pill(c,n,50,y-19);txt(c,t,91,y-15,13);para(c,b,91,y-36,342,10,15);y-=100
        panel(c,474,83,333,404)
        y=456
        for t,b in [('CadQuery 为参数实体主源','Python 与 JSON 保存可重建逻辑。STEP 是实体交换结果，不包含完整参数历史。[S05]'),
          ('Blender 为展示层','保留 ID 与实例层级。材质、灯光和镜头可以改变，工程尺寸与安装面不可另改。'),
          ('跨格式必须验证','glTF 用米与 Y-up；库可能已转换坐标。100 mm 标定块导入应为 0.1 m，不能重复缩放/旋转。[S06–S08]'),
          ('缺失依赖时透明降级','可用 FreeCAD Python 实体路线替代。仅做出展示网格时明确未完成工程模型，不能改后缀冒充 STEP。')]:
            y=textblock(c,t,b,491,y,299)
    else:
        header(c,'Codex 应生成的文件与图形',subtitle='本页是下一阶段交付目录；本设计包中不伪装包含尚未完成的 STEP 或 Blender 工程。')
        rows=[
          ('参数源','Python + JSON','可一键重建，记录实际工具版本'),
          ('工程实体','总装与逐件 STEP','零件独立、实体有效、命名/实例可追溯'),
          ('展示模型','BLEND + GLB','带真实装配层级，单件可选、可隔离'),
          ('整体图形','PNG + SVG/PDF','外观、去罩、正投影、总装爆炸、运动极限'),
          ('每件图页','PDF + SVG','每主项和派生零件有视图、尺寸、接口和说明'),
          ('演示动画','MP4','爆炸复原、完整供球周期；不冒充动力学'),
          ('本地查看器','HTML + 本地依赖','旋转、隔离、爆炸滑块、单件页联动'),
          ('验收报告','MD/JSON/CSV','BOM、干涉、单位、导入、未闭合问题')]
        table(c,rows,[125,185,464],34,483,36,['类别','格式','要求'],10)
        para(c,'固定零件 ID 不随页面顺序改变。同料号的两个实例分别命名 -L/-R 或 -01/-02。普通螺纹可简化，但螺栓头、有效长度、安装孔和工具空间不可全省。',38,123,762,10.5,17)
        para(c,'工程数据与爆炸展示分开。爆炸位移不得回写实际装配。模型检查始终在 explosion=0 的真实装配中执行。',38,76,762,10,16)
    footer(c)

def draw_acceptance(c):
    header(c,'验收与制造准备度',subtitle='文件能打开、渲染好看、静态无碰撞，分别证明不同的事情。')
    panel(c,34,85,375,402);panel(c,425,85,382,402)
    y=456
    for t,b in [('V0 概念模型','整体形态、总成层级、初始包络和运动逻辑一致。可以讨论与继续建模，不能直接采购加工。'),
      ('V1 样机工程模型','换入真实采购件，补齐孔位/配合/连接件；解决已识别干涉，完成轮、分球、夹持和停止方案试验。'),
      ('V2 加工与装配资料','冻结材料、公差、紧固、装配顺序和检验项目；关键设计通过负责人复核，形成可追溯制造版。')]:
        y=textblock(c,t,b,51,y,340)
    txt(c,'Codex 数字验收必须给出证据',443,456,14,TEAL)
    checks=['44 主项及新增派生料号均有对象、源代码与图页。','所有 STEP 为非空有效实体，重新导入尺寸一致。','100 mm 块、整机轴高和坐标方向跨格式一致。','所有关节极限、装载/脱筒/喂入位置及组合角度检查。','羽毛裙完整包络、轮下夹持、固定筒与线束留空可查。','孔/轴和弹性轮接触等豁免成对记录；不全局忽略相交。','每页尺寸来自 JSON；BOM、对象和页码一一对应。','未关闭问题列编号、影响件和所需实测，不能隐藏。']
    y=420
    for i,t in enumerate(checks):
        txt(c,f'{i+1:02d}',445,y,9.5,TEAL,'SansBold');y=para(c,t,473,y,313,10,15)-13
    footer(c)

def draw_sources(c,which):
    if which==1:
        header(c,'待验证项目与关闭条件',subtitle='这些项目是后续工程工作的输入；在完成之前不报告训练精度、安全等级或量产成熟度。')
        y=459
        for u,t,affected,method in UNRESOLVED:
            txt(c,u,38,y,10,TEAL,'SansBold');txt(c,t,82,y,11)
            para(c,method,330,y,468,9.5,14)
            txt(c,affected,82,y-15,8.2,MUTED,'Sans')
            y-=39
        footer(c)
    else:
        header(c,'设计依据与公开参考',subtitle='资料核对日期 2026-10-26。尺寸与部件方案为本项目建议；来源不构成本机性能证明。')
        y=459
        for sid,t,url in SOURCES:
            txt(c,sid,38,y,9.2,TEAL,'SansBold');txt(c,t,80,y,10)
            y=para(c,url,80,y-16,710,8,11,MUTED,'Sans')-14
        para(c,'引用和复用分开处理：本册未导入第三方 CAD 几何。下一阶段若复用开源零件，应保留原作者、许可文本和修改说明；不能只因公开下载就当作无条件商用。',39,75,760,9.5,15)
        footer(c)

def export_book():
    export_data()
    c=canvas.Canvas(str(OUT),pagesize=(W,H),pageCompression=1)
    c.setTitle(META['title']);c.setAuthor('BM1 Design Planning');c.setSubject(META['notice'])
    draw_cover(c);draw_readguide(c);draw_overview(c);draw_orthos(c);draw_exploded(c)
    draw_core(c);draw_sequence(c);draw_motion(c);draw_architecture(c);draw_maintenance(c)
    for a in ASM:draw_module(c,a)
    for p in PARTS:draw_part(c,p)
    draw_bom(c,PARTS[:22],1);draw_bom(c,PARTS[22:],2)
    draw_cad(c);draw_cad(c,True);draw_acceptance(c);draw_sources(c,1);draw_sources(c,2)
    c.save()
    # Make the long drawing book navigable without adding blank divider pages.
    doc=fitz.open(OUT);toc=[]
    for title,start,end in [('总体方案与动作图',1,10),('十个功能总成',11,20),('四十四类关键部件',21,64),('索引与执行验收',65,71)]:
        toc.append([1,title,start])
        toc.extend([2,row['title'],row['page']] for row in PAGE_INDEX if start<=row['page']<=end)
    doc.set_toc(toc)
    temp=OUT.with_suffix('.tmp.pdf');doc.save(temp,garbage=4,deflate=True);doc.close();temp.replace(OUT)
    (ROOT/'data'/'page_index.json').write_text(json.dumps(PAGE_INDEX,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'data'/'parts.json').write_text(json.dumps(PARTS,ensure_ascii=False,indent=2),encoding='utf-8')
    with (ROOT/'data'/'bom.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['part_id','name_zh','assembly_id','kind','quantity','quantity_unit','bbox_mm','status','page'])
        for p in PARTS:writer.writerow([p['part_id'],p['name'],p['assembly_id'],p['kind'],p['quantity'] if p['quantity'] is not None else '', '器件族_待逐位置展开' if p['quantity'] is None else '主项', 'x'.join(map(str,p['bbox_mm'])),'concept',p['page']])
    svg(world_scene(True,head_pitch=18,head_yaw=-12),ROOT/'figures'/'F01_overview.svg',width=1400,height=1400,title='BM1 overall concept; H=1500 mm')
    svg(world_scene(False),ROOT/'figures'/'F02_cutaway.svg',width=1400,height=1400,title='BM1 internal layout concept')
    for v in ['front','side','top']:svg(world_scene(False),ROOT/'figures'/f'F03_{v}.svg',view=v,title=f'BM1 {v} orthographic concept')
    info={'page_count':len(PAGE_INDEX),'part_count':len(PARTS),'svg_count':len(list((ROOT/'figures').glob('*.svg'))),
          'pdf':str(OUT),'no_engineering_cad_generated':True}
    (ROOT/'data'/'deliverable_manifest.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(info,ensure_ascii=False))

if __name__=='__main__':export_book()
