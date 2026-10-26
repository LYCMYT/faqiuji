"""Actual-model orthographic projections, editable SVG and Chinese A4 atlas.
Uses the exact CAD tessellation, not the input design-book drawing generator.
"""
from pathlib import Path
import sys,json,math,html,csv
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import sys; sys.path.insert(0,str(R))
from tools.input_manifest import generated_path, metadata_path
from cad.assemblies.kinematics import matrix,capture_stroke
OUT=R/'output';DRAW=OUT/'drawings';PAGES=DRAW/'pages';PAGES.mkdir(parents=True,exist_ok=True)
DATA=json.loads((OUT/'mesh/model.json').read_text(encoding='utf-8'))
PARTS=json.loads((R/'data/parts.json').read_text(encoding='utf-8')); ASMS=json.loads((R/'data/assemblies.json').read_text(encoding='utf-8'))
P={k:v['value'] for k,v in json.loads((R/'data/design.json').read_text(encoding='utf-8'))['parameters'].items()}
FONT='C:/Windows/Fonts/msyh.ttc';pdfmetrics.registerFont(TTFont('CN',FONT,subfontIndex=0));pf=ImageFont.truetype(FONT,22)

def project(items,name,view='iso',world=True,exploded=False,state=None,section=False,save_svg=True):
    width,height=1200,820
    axes={'front':([0,1,0],[0,0,1],[1,0,0]),'rear':([0,-1,0],[0,0,1],[-1,0,0]),'left':([-1,0,0],[0,0,1],[0,1,0]),'right':([1,0,0],[0,0,1],[0,-1,0]),'top':([0,1,0],[-1,0,0],[0,0,1])}
    if view=='iso':
        z=np.array([1.3,-1.8,1.05]);z/=np.linalg.norm(z);x=np.cross([0,0,1],z);x/=np.linalg.norm(x);y=np.cross(z,x);B=np.array([x,y,z])
    else:B=np.array(axes[view],float)
    bundles=[];allv=[]
    for idx,item in enumerate(items):
        if state and item.get('dynamic_loop'):
            from cad.parts.recipe import build
            sh=build(item['dynamic_loop'],dict(P,slide=state.get('slide',0)))
            vertices,triangles=sh.tessellate(.18,.15)
            item=dict(item,vertices=[list(v.toTuple()) for v in vertices],triangles=triangles)
        v=np.array(item['vertices'],float);M=matrix(item['parent'],state) if world else np.eye(4)
        v=v@M[:3,:3].T+M[:3,3]
        if exploded:
            delta=np.array(item['explode']) if exploded=='modules' else np.array(item.get('part_explode',[0,0,idx*35]))
            v=v+delta
        pr=v@B.T;allv.append(pr);bundles.append((item,v,pr))
    combined=np.concatenate(allv);lo=combined[:,:2].min(0);hi=combined[:,:2].max(0);center=(lo+hi)/2;scale=min((width-100)/max(hi[0]-lo[0],1),(height-100)/max(hi[1]-lo[1],1))
    polygons=[]
    for item,v,pr in bundles:
        tris=np.array(item['triangles']);tri=v[tris];norm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);lens=np.linalg.norm(norm,axis=1);norm/=np.maximum(lens[:,None],1e-9)
        # All faces are depth sorted; no geometry removed for interference analysis.
        colors=np.array([int(item['color'][j:j+2],16) for j in [1,3,5]])
        shade=.62+.30*np.abs(norm@np.array([.3,-.5,.81]))
        pp=pr[tris];screen=(pp[:,:,:2]-center)*[scale,-scale]+[width/2,height/2]
        if section:
            keep=tri.mean(1)[:,1]<=0
        else:keep=np.ones(len(tri),bool)
        for k in np.flatnonzero(keep):
            color=tuple(np.minimum(255,colors*shade[k]+18).astype(int));polygons.append((float(pp[k,:,2].mean()),screen[k],color))
    polygons.sort(key=lambda a:a[0]);im=Image.new('RGB',(width,height),'#F4F7F9');dr=ImageDraw.Draw(im)
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><rect width="1200" height="820" fill="#f4f7f9"/>']
    for depth,pts,c in polygons:
        points=[tuple(x) for x in pts];dr.polygon(points,fill=c)
        if save_svg:svg.append('<polygon points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in points)+'" fill="rgb('+','.join(map(str,c))+')"/>')
    if view!='iso':
        xmin,xmax=width/2-(hi[0]-lo[0])*scale/2,width/2+(hi[0]-lo[0])*scale/2
        ymin,ymax=height/2-(hi[1]-lo[1])*scale/2,height/2+(hi[1]-lo[1])*scale/2
        label=f'{hi[0]-lo[0]:.1f} mm';dr.line([(xmin,790),(xmax,790)],fill='#275568',width=2)
        for xx in [xmin,xmax]:dr.line([(xx,780),(xx,800)],fill='#275568',width=2)
        dr.text((width/2-55,760),label,font=pf,fill='#275568')
        dr.text((15,80),f'{hi[1]-lo[1]:.1f} mm',font=pf,fill='#275568')
        if save_svg:svg.append(f'<path d="M{xmin:.2f} 790 H{xmax:.2f}" fill="none" stroke="#275568"/><text x="540" y="778" font-size="22" fill="#275568">{label}</text><text x="15" y="85" font-size="22">{hi[1]-lo[1]:.1f} mm</text>')
    # model coordinate triad, labelled for unambiguous projection
    origin=np.array([75,height-65])
    for idx,color,label in [(0,'#d14949','+X'),(1,'#208e74','+Y'),(2,'#467cbd','+Z')]:
        end=origin+B[:2,idx]*[40,-40];dr.line([tuple(origin),tuple(end)],fill=color,width=3);dr.text(tuple(end),label,font=pf,fill=color)
    path=DRAW/(name+'.png');im.save(path)
    if save_svg:
        svg.append('<text x="30" y="35" font-family="Microsoft YaHei" font-size="20" fill="#294454">'+html.escape(name+' · CAD正投影 / 概念尺寸 mm')+'</text></svg>');(DRAW/(name+'.svg')).write_text(''.join(svg),encoding='utf-8')
    return path

W,H=841.8898,595.2756
c=canvas.Canvas(str(OUT/'BM1_V0_design_book.pdf'),pagesize=(W,H));c.setTitle('BM1 V0.2 参数实体与模型图册');c.setAuthor('BM1 engineering implementation')
page=0;index=[]
def text(x,y,s,size=10,color='#314756'):
    c.setFillColor(color);c.setFont('CN',size);c.drawString(x,y,str(s))
def wrapped(s,x,y,w,size=9,leading=15,maxlines=40):
    line='';count=0
    for ch in str(s):
        if ch=='\n' or pdfmetrics.stringWidth(line+ch,'CN',size)>w:
            text(x,y,line,size);y-=leading;line='';count+=1
            if count>=maxlines:return y
        if ch!='\n':line+=ch
    if line:text(x,y,line,size);y-=leading
    return y
def start(title,subtitle='概念工程实体 / 尺寸未冻结 / 不是加工图'):
    global page;page+=1;index.append({'page':page,'title':title});c.setFillColorRGB(.965,.975,.98);c.rect(0,0,W,H,fill=1,stroke=0);c.setFillColor('#173E50');c.rect(0,H-83,W,83,fill=1,stroke=0);text(24,H-35,title,20,'#FFFFFF');text(24,H-60,subtitle,9,'#D6E5EA');text(24,18,'BM1  |  V0.2  |  原生实体重建 · 全部模型图来自本次 CAD',8);text(W-85,18,f'{page:03d}',9);c.bookmarkPage(str(page));c.addOutlineEntry(title,str(page),level=0)
def img(path,x,y,w,h):c.drawImage(str(path),x,y,width=w,height=h,preserveAspectRatio=True,anchor='c',mask='auto')
def done():c.showPage()

solid=[i for i in DATA if not i.get('reference')]
start('BM1 / V0.2  羽毛球发球机','参数实体 · 机构与部件页 · 本次实际模型交付')
overall=OUT/'render/overall.png'
if not overall.exists():overall=project(solid,'01_overall')
img(overall,25,65,480,430)
y=465
for s in ['44 个主项 / 10 个功能模块','H = '+str(P['head_axis_height'])+' mm','双轮仅接触球头，羽毛裙在轮面上方。','先缩导套，再脱筒，再转头。','球在捕获后解除托架绑定。','本册展示真实 CAD 派生模型；采购接口与样机性能未验证。','干涉与重导入结果见 reports/；未决项 U01-U10 不自动关闭。']:
    y=wrapped(s,535,y,270,12,20)-14
done()
start('数据状态与交付边界')
y=465
for s in ['已建模：44 个主项及展开的结构分件、候选采购外形和传感功能位置。','数字检查：必须以 reports/validation.json 和碰撞明细的实际结果为准。有效实体与成功导出并不代表无干涉。','采购待确认：孔型、配合、材料牌号、扭矩、驱动电压和接口。所有新增孔、槽、连接细节均属概念试验几何。','样机待验证：单球率、释放窗口、有效轮压缩、离轮翻转、实际容量、真实节拍、落点标定和防护能力。','固定供球机构与机头基座共用手动升降；功能 ASM 分组与运动层级独立。','原设计包完整保留 input/。重建仅读取根目录 data/；不调用原示意图脚本。']:
    y=wrapped(s,35,y,770,13,22)-20
done()

views=[('02_cutaway','去罩结构','iso',False),('03_front','前正投影','front',False),('04_rear','后正投影','rear',False),('05_left','左正投影','left',False),('06_right','右正投影','right',False),('07_top','顶正投影','top',False),('08_exploded','总装功能模块爆炸','iso','modules'),('09_section','机头 Y=0 剖开观察','right',False)]
for name,title,view,ex in views:
    items=[i for i in solid if not i.get('cover')] if name in ('02_cutaway','09_section') else solid
    if name=='09_section':items=json.loads((OUT/'mesh/section.json').read_text(encoding='utf-8'))
    path=project(items,name,view,exploded=ex,section=False);start(title,'实际模型投影；各视图独立缩放，数值单位 mm；爆炸位移仅展示')
    img(path,25,65,620,440)
    y=460
    for s in ['默认 H：'+str(P['head_axis_height']),'筒长：'+str(P['tube_length']),'筒顶：'+str(P['head_axis_height']+P['tube_bottom_z_H']+P['tube_length']),'筒帽顶：'+str(P['head_axis_height']+P['tube_bottom_z_H']+P['tube_length']+P['tube_cap_allowance']),'支撑点中心：850 × 800','轮心距：(D + gap) = '+str(P['wheel_diameter']+P['wheel_gap_visual']),'剖面按真实 CAD 布尔剖切生成，剖切 STEP 单独提供。']:
        y=wrapped(s,660,y,155,10,18)-12
    done()

# Distinct assembled and exploded views for all ten functional modules.
for a in ASMS:
    items=[i for i in solid if i['assembly_id']==a['id']]
    for n,i in enumerate(items):
        b=i['bounds_mm'];center=np.array([(b[k]+b[k+3])/2 for k in range(3)]);i['part_explode']=[(n%3-1)*70,((n//3)%3-1)*70,n*23]
    path=project(items,a['id']+'_exploded',exploded='parts');start(a['id']+'  '+a['name']+' / 子总成拆解')
    img(path,20,80,580,425);y=480
    for pid in dict.fromkeys(i['part_id'] for i in items):
        p=next(p for p in PARTS if p['part_id']==pid);y=wrapped(pid+' '+p['name'],615,y,200,11,18)-8
    wrapped('分解位置用于展示；拆卸方向和工具可达性需另外检查。'+a['role'],615,180,195,10,17)
    done()

# Seven meaningful sequence snapshots and endpoint combinations from the same transforms.
seq=[('装载低位',dict(guide=0,slide=0,clamp=14)),('定位持球',dict(guide=0,slide=0,clamp=0)),('导套回缩',dict(guide=115,slide=0)),('前移脱筒',dict(guide=115,slide=105)),('共同偏航俯仰',dict(guide=115,slide=105,yaw=35,pitch=55)),('捕获前实体开夹',dict(guide=115,slide=165,clamp=14)),('接触边界停推 / 等待新出球脉冲',dict(guide=115,slide=capture_stroke(),clamp=14))]
head=[i for i in DATA if i['parent']!='WORLD_STATIC' and not i.get('cover') and i['part_id'] not in ['PRT-0202']]
for n,(label,state) in enumerate(seq):
    path=project(head,'sequence_'+str(n),state=state);start(label,'供球顺序示意；时间、释放阈值、转速与轨迹未验证')
    img(path,25,65,620,440);wrapped(json.dumps(state,ensure_ascii=False),665,460,150,10,18)
    wrapped('捕获边界按刚性圆截面估算；ST09 之后球不再属于滑台。真实动态必须试验。',665,260,150,11,19);done()
for h,yaw,pitch in [(1400,-45,-10),(1400,45,60),(1800,-45,60),(1800,45,-10)]:
    state=dict(height=h,yaw=yaw,pitch=pitch,slide=105,guide=115)
    path=project(solid,f'limit_{h}_{yaw}_{pitch}',state=state);start(f'组合极限 H{h} / 偏航{yaw}° / 俯仰{pitch}°')
    img(path,30,55,625,445);wrapped('姿态由统一变换树计算。端点截图不能替代完整运动路径检测；离散分辨率与未通过项见验收报告。',675,450,140,11,20);done()

coverages=[]
start('高度链 / H 基准与三位置行程','全部数值读取 data/，候选尺寸 mm；正角俯仰绕局部 -Y')
img(DRAW/'06_right.png',20,65,450,440)
chain=[('H 默认 / 范围',f"{P['head_axis_height']} / {P['head_height_min']} - {P['head_height_max']}"),('外立柱顶',str(P['base_top_z']+P['outer_mast_length'])),('内柱顶',f"H {P['inner_mast_top_z_H']:+}"),('固定板 / 回转支承','12 / 30（设计初值）'),('U架下缘',f"H {P['yaw_platform_z_H']:+}"),('筒顶',f"H + {P['tube_bottom_z_H']+P['tube_length']}"),('筒帽顶',f"H + {P['tube_bottom_z_H']+P['tube_length']+P['tube_cap_allowance']}"),('装载 / 等待 / 喂入',f"X {P['load_x']} / {P['clear_x']} / {P['feed_x']}"),('滑台行程',f"0 / {P['clear_stroke']} / {P['carriage_total_stroke']}"),('导套行程',str(P['guide_stroke']))]
y=480
for k,v in chain:text(490,y,k,11,'#087F82');text(655,y,v,10);y-=35
wrapped('最高轴高的内外柱重叠：232 mm，仅几何结果；刚度、销孔强度和最高位稳定性尚未验证。',490,100,320,11,18);done()
for service,pids,label in [('tube',['PRT-0601','PRT-0602','PRT-0603','PRT-0604','PRT-0605','PRT-0606','PRT-0607'],'球筒后拆与分球检修'),('wheel',['PRT-0501','PRT-0502','PRT-0503','PRT-0504','PRT-0505','PRT-0506'],'轮组上提与换轮'),('electrical',['PRT-0507','PRT-0901','PRT-0902','PRT-0903','PRT-0803'],'电气舱布局与后侧检修')]:
    sub=[i for i in solid if i['part_id'] in pids and not i.get('cover')];path=project(sub,'service_'+service);start(label,'基于实际模型的检修图；路径结果详见 service_validation.json')
    img(path,20,60,605,440)
    notes={'tube':['R1整套供球器沿-X抽出350mm。','空筒、最低轴高、隔离能源、托车承重、断开接线；两销向外退出55mm。','保留筒、分球器与导套为一体。见r1_service_validation.json；锁销承重、复装对中和实际工具操作待验证。'], 'wheel':['拆出方向：+Z，沿独立轮轴。','先停机确认停转，拆上罩，解除轴向固定。','轮毂、锁紧方式与真实高速轴承仍需选型；图示不证明高速安全。'], 'electrical':['拆出方向：-X，经后舱门。','电源、驱动和本地控制分区；插拔、散热及保险/切断方案未选型。','先隔离电源并解除连接，再移出模块；工具头与插头型号未冻结。']}
    y=460
    for n in notes[service]:y=wrapped(n,650,y,165,11,20)-25
    done()
def partpage(p,items,code,title,derived=False):
    iso=project(items,code+'_iso',world=True);a=project(items,code+'_front','front',world=True);b=project(items,code+'_side','right',world=True)
    locitems=[dict(i,color='#D4DEE4') for i in solid if not i.get('cover')]
    ids={i['instance_id'] for i in items}
    for i in locitems:
        if i['instance_id'] in ids:i['color']='#DB7D39'
    thumb=project(locitems,code+'_location',save_svg=False)
    start(code+'  '+title,p['assembly_id']+' / V0.2 / '+('概念派生件' if derived else p['kind'])+' / 型号、配合与加工尺寸未冻结')
    img(iso,20,235,435,270);img(thumb,455,325,120,180)
    text(30,220,'独立等轴测 · 原生实体派生',9)
    img(a,20,50,265,155);img(b,305,50,265,155)
    allv=np.concatenate([np.array(i['vertices'])@matrix(i['parent'])[:3,:3].T+matrix(i['parent'])[:3,3] for i in items]);dims=allv.max(0)-allv.min(0)
    text(25,42,'前视 / Y-Z 投影',8);text(310,42,'侧视 / X-Z 投影',8)
    y=490
    unresolved=json.loads((R/'data/unresolved.json').read_text(encoding='utf-8'));uids=[u['id'] for u in unresolved if p['part_id'][4:] in u['affected'] or ('采购' in p['kind'] and u['id']=='U09')]
    lines=[('几何包络',' × '.join(f'{d:.1f}' for d in dims)+' mm（含所示实例）'),('功能',p['function']),('连接 / 基准',p['interfaces']),('材料 / 工艺',p['material_candidate']),('拆装',p['removal']),('待验证',p['validation']+' 关联：'+('/'.join(uids) or 'U07/U09')),('实例',', '.join(i['instance_id'] for i in items))]
    for key,value in lines:
        text(590,y,key,10,'#087F82');y-=17;y=wrapped(value,590,y,225,8.5,13)-12
    done();coverages.append(dict(code=code,part_id=p['part_id'],page=page,instances=len(items),derived=derived))
    desc=''.join('<h3>'+k+'</h3><p>'+html.escape(v)+'</p>' for k,v in lines)
    body=f'''<!doctype html><html lang="zh"><meta charset="utf-8"><title>{code} {title}</title><style>body{{font:15px/1.7 system-ui,"Microsoft YaHei";max-width:1200px;margin:32px auto;color:#233f4d;background:#f5f8fa}}h1{{color:#146e73}}.grid{{display:grid;grid-template-columns:2fr 1fr;gap:25px}}img{{max-width:100%}}.orth{{display:flex}}.orth img{{width:49%}}h3{{margin-bottom:0}}p{{margin-top:3px}}small{{color:#8d5a15}}</style><a href="../../../viewer/">← 返回三维查看器</a><h1>{code} · {title}</h1><small>概念工程版 / 型号与配合未冻结 / 非加工图</small><div class="grid"><div><img src="../{code}_iso.png"><div class="orth"><img src="../{code}_front.png"><img src="../{code}_side.png"></div><img width="220" src="../{code}_location.png"></div><div>{desc}</div></div></html>'''
    (PAGES/(code+'.html')).write_text(body,encoding='utf-8')
for p in PARTS:
    items=[i for i in solid if i['part_id']==p['part_id']];partpage(p,items,p['part_id'],p['name'])
    print('page',page,p['part_id'],flush=True)
# Key independent manufacturing pieces, one page per unique derived ID.
for did in dict.fromkeys(i['derived_id'] for i in solid if i['derived_id']!=i['part_id']):
    items=[i for i in solid if i['derived_id']==did];p=next(p for p in PARTS if p['part_id']==items[0]['part_id']);partpage(p,items,did,items[0]['name'],True)
start('U01-U10 / 样机与采购关闭条件')
y=480
for u in json.loads((R/'data/unresolved.json').read_text(encoding='utf-8')):
    y=wrapped(u['id']+' '+u['title']+'：'+u['close_condition'],30,y,775,10,16)-12
done();c.save()
generated_path(R,'page_index_engineering.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
(R/'reports/page_coverage.json').write_text(json.dumps(dict(pdf_pages=page,main_pages=sum(not x['derived'] for x in coverages),derived_pages=sum(x['derived'] for x in coverages),pages=coverages),ensure_ascii=False,indent=2),encoding='utf-8')
with (OUT/'BOM.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['part_id','name','assembly_id','design_quantity','modeled_instances','status','page','supplier_model'])
    for p in PARTS:w.writerow([p['part_id'],p['name'],p['assembly_id'],p['quantity'] if p['quantity'] is not None else '未定（传感器族）',len([i for i in solid if i['part_id']==p['part_id']]),p['status'],next(x['page'] for x in coverages if x['code']==p['part_id']),'未选型' if '采购' in p['kind'] else '不适用/待确定'])
print('BOOK',page,'pages')
