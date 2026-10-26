"""Generate machine-readable handoff metadata and self-contained component introduction pages."""
import json, html, csv
from pathlib import Path
from design_data import ROOT, META, PARAMS as P, PARTS, ASM, SOURCES, UNRESOLVED

def writejson(name,data):
    (ROOT/'data'/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

INTERFACES=[
 ('IF01','底盘与外立柱','WORLD',[0,0,160],[0,0,1],['PRT-0101','PRT-0201'],'外柱底部安装面；连接板和加强筋纳入0101派生件','安装板及螺栓规格需载荷校核'),
 ('IF02','内柱与偏航固定板','H',[0,0,-342],[0,0,1],['PRT-0202','PRT-0301'],'内柱顶/基座板底面','固定板厚12；连接法兰派生件随实际管材定义'),
 ('IF03','固定板与回转支承','H',[0,0,-330],[0,0,1],['PRT-0301','PRT-0302'],'基座上面/轴承底面','供应商固定圈孔位待核对'),
 ('IF04','回转支承与U架','H',[0,0,-300],[0,0,1],['PRT-0302','PRT-0401'],'支承顶面/U架底面','供应商转动圈孔位待核对'),
 ('IF05','左俯仰耳轴','H',[0,210,0],[0,1,0],['PRT-0401','PRT-0402','PRT-0501'],'左短轴中心；禁止贯通至球道','孔轴配合与轴承尺寸待校核'),
 ('IF06','右俯仰耳轴','H',[0,-210,0],[0,1,0],['PRT-0401','PRT-0402','PRT-0501'],'右短轴中心；与左侧同轴','与俯仰传动连接待选型'),
 ('IF07','左轮轴','H',[0,82.5,0],[0,0,1],['PRT-0503','PRT-0504','PRT-0505','PRT-0506'],'轮中面与主轴中心','轴承座实体保持轮面下方，上部仅轴伸；传动联接待选型'),
 ('IF08','右轮轴','H',[0,-82.5,0],[0,0,1],['PRT-0503','PRT-0504','PRT-0505','PRT-0506'],'轮中面与主轴中心','中心距须由轮D与概念轮缝计算，不写成第二套独立常数'),
 ('IF09','储球管轴线','H',[-190,0,110],[0,0,1],['PRT-0601','PRT-0602'],'固定管下缘中心；与零位托球中心同轴','球筒跟随手动升降但不跟yaw/pitch'),
 ('IF10','分球作用区','H',[-190,0,300],[0,0,1],['PRT-0602','PRT-0603','PRT-0604','PRT-0605'],'运动件最低Z必须≥280','留球/闸门几何尚未验证；真实夹爪窗口按球堆试验确定'),
 ('IF11','导套上位','H',[-190,0,110],[0,0,1],['PRT-0601','PRT-0606','PRT-0607'],'套下缘110、套上缘260','套在管外：ID82>OD80；外导轨负责定位'),
 ('IF12','导套装载位','H',[-190,0,-5],[0,0,1],['PRT-0606','PRT-0701','PRT-0702'],'套下缘-5、套上缘145','低位夹爪与套口逐件检查，不允许用固定漏斗挡住转头路径'),
 ('IF13','托球装载位','H',[-190,0,0],[1,0,0],['PRT-0701','PRT-0703'],'球头中心基准；滑台行程0','θ=0，ψ=0；夹持形面按真实球头形状修正'),
 ('IF14','托球避让位','H',[-85,0,0],[1,0,0],['PRT-0701','PRT-0703'],'滑台行程105；转向前等待位','完整球裙已脱离固定导套后才允许yaw/pitch'),
 ('IF15','喂入示意终点','H',[-5,0,0],[1,0,0],['PRT-0701','PRT-0702','PRT-0505'],'滑台示意行程185，不代表球实际仍随台运动','真实捕获可能在约-11.15即开始；仅刚性截面估算，必须试验'),
 ('IF16','轮下中央滑轨','H',[-115,0,-30],[1,0,0],['PRT-0501','PRT-0703'],'导轨总体宽≤40、Z=-40…-20','避开轮轴座、传动及线缆；托架结构顶≤-12'),
 ('IF17','固定球筒支架','H',[-310,0,0],[0,0,1],['PRT-0202','PRT-0301','PRT-0602'],'与固定侧升降载架连接；后柱参考X=-310','横支撑与分球件最低Z≥280；后窄尾全yaw/pitch扫掠检查'),
 ('IF18','发射护罩','H',[0,0,0],[1,0,0],['PRT-0501','PRT-0801','PRT-0802'],'前罩宽、后尾窄；中央全羽球路径留空','轮上翻转空间与防护强度待验证'),
 ('IF19','底舱电气托盘','WORLD',[0,0,210],[0,0,1],['PRT-0101','PRT-0803','PRT-0901','PRT-0902','PRT-0903','PRT-0507'],'功率与控制模块布置面','线束插拔、散热、保险/切断及应力释放必须留实空间'),
 ('IF20','手动升降基准链','WORLD',[0,0,0],[0,0,1],['PRT-0201','PRT-0202','PRT-0203','PRT-0602'],'所有H坐标在升降时共同移动','外柱顶1040，内柱顶H-342，内柱650；H1800时重叠232'),
]

SENSORS=[
 ('SEN-01','导套上位','FIXED_FEEDER','允许滑台前移的必要输入'),
 ('SEN-02','导套下位','FIXED_FEEDER','落球前确认导向位置'),
 ('SEN-03','滑台回零','MOVING_HEAD','定义装载位基准；连续位置由模组编码反馈提供'),
 ('SEN-04','夹持/释放反馈','SLIDER','不能仅用固定延时假设已松夹'),
 ('SEN-05','托架有球','SLIDER','不能单独证明恰好一球'),
 ('SEN-06','出球通过','MOVING_HEAD','结合计数和喂入状态判定一次出球'),
 ('SEN-07','偏航回零','LIFT_CARRIAGE','定义ψ=0装载方向'),
 ('SEN-08','偏航左/右限位族','YAW_FRAME','需左右独立保护信号或等效已验证实现'),
 ('SEN-09','俯仰回零','YAW_FRAME','定义θ=0装载姿态'),
 ('SEN-10','俯仰上/下限位族','MOVING_HEAD','需上下限位或等效已验证实现'),
 ('SEN-11','发射罩开合','MOVING_HEAD','打开保护罩停危险驱动/禁止供球'),
 ('SEN-12','分球留球/闸门反馈','FIXED_FEEDER','每个关键分球动作应有状态证据'),
 ('SEN-13','左轮转速','MOVING_HEAD','若电机内置反馈已满足，则不重复采购'),
 ('SEN-14','右轮转速','MOVING_HEAD','独立于左轮反馈')
]

def create_metadata():
    rows=[dict(interface_id=a,name=b,reference_frame=c,origin_mm=d,axis=e,parts=f,geometry_rule=g,
               unresolved=h,hole_pattern=None,fasteners=None,status='concept') for a,b,c,d,e,f,g,h in INTERFACES]
    writejson('interfaces.json',rows)
    writejson('sensor_schedule.json',[dict(instance_id=a,function=b,parent=c,requirement=d,selected_model=None,quantity_exact=None) for a,b,c,d in SENSORS])
    writejson('derived_constraints.json',[
      dict(id='C01',expression='wheel_center_y=(wheel_diameter+wheel_gap_visual)/2',expected_mm=82.5),
      dict(id='C02',expression='tube_top_z_H=tube_bottom_z_H+tube_length',expected_mm=650),
      dict(id='C03',expression='overall_height=head_axis_height+tube_top_z_H+tube_cap_allowance',expected_default_mm=2170,range_mm=[2070,2470]),
      dict(id='C04',expression='guide_top_clear_z_H=guide_bottom_clear_z_H+guide_length',expected_mm=260),
      dict(id='C05',expression='separator_motion_z_min_H-guide_top_clear_z_H>=20',expected_min_mm=20),
      dict(id='C06',expression='carriage_total_stroke=feed_x-load_x',expected_mm=185),
      dict(id='C07',expression='clear_stroke=clear_x-load_x',expected_mm=105),
      dict(id='C08',expression='base_plate_bottom_H=-342;base_plate_thickness=12;bearing_height=30;U_frame_bottom_H=-300'),
      dict(id='C09',expression='outer_mast_top=160+880=1040;inner_bottom=H-342-650;overlap_at_H1800=232',status='geometric_only_not_strength_proof'),
      dict(id='C10',expression='pitch_rotation=R_y(-theta);yaw_rotation=R_z(psi)',note='抬头为正θ，左转为正ψ'),
      dict(id='C11',expression='first_contact_x=-sqrt((Rwheel+Rcork)^2-center_y^2)',display_value_mm=-11.14955,note='仅刚性圆截面估算，不作为释放位置定稿')])
    tree={
      'WORLD':{'BASE_FIXED':['ASM-01','PRT-0201','PRT-0204','PRT-0803','PRT-0507','PRT-0901','PRT-0902','PRT-0903','PRT-0904','PRT-1003'],
        'LIFT_CARRIAGE':{'reference':'J01 manual height','fixed':['PRT-0202','PRT-0301','PRT-0303'],
          'FIXED_FEEDER':{'fixed':['PRT-0601','PRT-0602','PRT-0605','PRT-0607'],
                         'GATES':['PRT-0603','PRT-0604'],'GUIDE_Z':['PRT-0606']},
          'YAW_FRAME':{'reference':'J02 +Z','fixed':['PRT-0401','PRT-0403'],
            'MOVING_HEAD':{'reference':'J03 -Y','fixed':['PRT-0501','PRT-0502','PRT-0503','PRT-0506','PRT-0703','PRT-0801','PRT-0802'],
             'WHEEL_LEFT':['PRT-0504-L','PRT-0505-L'],'WHEEL_RIGHT':['PRT-0504-R','PRT-0505-R'],
             'SLIDER':{'reference':'J05 +X','fixed':['PRT-0701','PRT-0704'],'CLAMP':['PRT-0702-L','PRT-0702-R']}}}},
        'EXTERNAL':['PRT-1001','PRT-1002']},
      'notes':['功能总成编号与运动父节点是两套信息；0507驱动属于发射功能但实际固定在底舱。',
               '0302回转支承需拆分固定圈与转动圈；0403执行器需区分壳体与输出。',
               '0203高度销、0402耳轴及0905传感器实例由具体安装接口归属，不能省略。',
               '校核羽球是TEST_SHUTTLE对象；轮捕获后解除SLIDER绑定，不属于真实BOM。']}
    writejson('assembly_tree.json',tree)
    writejson('expected_contacts.json',[
      dict(pair=['PRT-0505-L','TEST_SHUTTLE.cork'],type='elastic_friction',status='requires_test'),
      dict(pair=['PRT-0505-R','TEST_SHUTTLE.cork'],type='elastic_friction',status='requires_test'),
      dict(pair=['PRT-0702','TEST_SHUTTLE.cork_lower'],type='controlled_clamping',condition='closed states only'),
      dict(pair=['PRT-0503.shaft','PRT-0504.bore'],type='shaft_hub_fit',status='supplier_and_fit_pending'),
      dict(pair=['PRT-0202','PRT-0204.guide_inserts'],type='sliding_guide',status='fit_pending')])
    writejson('viewshots.json',[
      dict(id='VIEW-01',name='整体外观',yaw=-12,pitch=18,H=1500,cover=True,output='render/overall.png'),
      dict(id='VIEW-02',name='去罩总装',yaw=0,pitch=0,H=1500,cover=False,output='render/cutaway.png'),
      dict(id='VIEW-03',name='正投影',views=['front','rear','left','right','top'],projection='orthographic'),
      dict(id='VIEW-04',name='总装与10总成爆炸',explosion='display_copy_only'),
      dict(id='VIEW-05',name='每主项与派生件单页',layout='isometric+necessary_orthographic+dimensions+interfaces'),
      dict(id='VIEW-06',name='供球剖视序列',states='S00-S08'),
      dict(id='VIEW-07',name='极限与检修',yaw=[-45,0,45],pitch=[-10,0,35,60],H=[1400,1800])])
    writejson('exploded.json',dict(note='仅为Codex展示分解方向建议。位移可为排版调整，不改变真实装配。',
      modules=[dict(assembly_id=aid,reference_frame='WORLD',translation_mm=tr,rotation_deg=[0,0,0]) for aid,tr in [
       ('ASM-01',[0,0,-80]),('ASM-02',[0,0,50]),('ASM-03',[360,0,100]),('ASM-04',[0,0,450]),
       ('ASM-05',[450,0,700]),('ASM-06',[-650,0,430]),('ASM-07',[700,-200,300]),
       ('ASM-08',[600,300,450]),('ASM-09',[650,-300,30]),('ASM-10',[-500,-200,250])]]))
    writejson('measured_calibration.json',dict(status='not_measured',shots=[],note='不可填入推测或渲染数据冒充实测。'))
    with (ROOT/'data'/'standard_hardware.csv').open('w',encoding='utf-8-sig',newline='') as f:
      w=csv.writer(f);w.writerow(['family','use','quantity','size_status','gate_before_manufacture'])
      w.writerows([
       ['FAST-M3','控制板与低速附件','TBD','候选族','按板卡孔型、柱高和咬合长度确认'],
       ['FAST-M4','传感器/小型机构','TBD','候选族','按实际安装接口确认'],
       ['FAST-M5M6','机头、罩壳、支架','TBD','候选族','校核载荷、防松与工具可达'],
       ['FAST-M8','底盘/立柱候选','TBD','候选族','载荷和连接板确定后选择，不直接下单'],
       ['BEARING','轮轴、俯仰和偏航','TBD','未选型','校核载荷、速度和配合'],
       ['CONNECTOR','动力/传感/外部停发','TBD','未选型','电流等级、锁紧、插拔与应力释放'],
       ['WIRE','动力与信号线束','TBD','未选型','电流、线径、弯曲半径和保护路径']])

CSS='''
:root{--ink:#203747;--muted:#617480;--line:#d7e1e4;--bg:#f4f7f7;--teal:#127f76}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.7 -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK SC","Microsoft YaHei",sans-serif}a{color:var(--teal)}main{max-width:1180px;margin:36px auto;padding:0 24px}h1{font-size:34px;line-height:1.3;margin:14px 0}h2{font-size:22px;margin-top:32px}.eyebrow{font-size:13px;color:var(--teal);letter-spacing:1px}.note{color:var(--muted);font-size:14px}.hero{display:grid;grid-template-columns:1.1fr 1fr;gap:24px}.visual,.card{background:white;border-radius:16px;padding:24px}.visual svg{width:100%;height:auto;display:block}.card h3{font-size:15px;color:var(--teal);margin-bottom:4px}.card p{margin:0 0 20px}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}.thumb{display:block;background:white;border-radius:12px;padding:14px;text-decoration:none}.thumb img{width:100%;aspect-ratio:1.4;object-fit:contain}.thumb strong{display:block;color:var(--ink)}.chip{display:inline-block;background:#e2efeb;color:var(--teal);padding:4px 10px;border-radius:20px;font-size:13px;margin:2px 5px 2px 0}.nav{display:flex;justify-content:space-between;margin:26px 0}footer{margin:30px 0;color:var(--muted);font-size:13px}@media(max-width:850px){.hero{grid-template-columns:1fr}.grid{grid-template-columns:repeat(2,1fr)}}@media print{body{background:white}main{margin:0}.nav{display:none}.hero{grid-template-columns:1.1fr 1fr}.card,.visual{border:1px solid var(--line)}}
'''

def create_html():
    parts=json.loads((ROOT/'data'/'parts.json').read_text())
    for i,p in enumerate(parts):
        svgtext=(ROOT/'figures'/f'{p["part_id"]}.svg').read_text()
        q='按传感位置展开' if p['quantity'] is None else str(p['quantity'])
        info=''.join(f'<h3>{a}</h3><p>{html.escape(b)}</p>' for a,b in [
           ('功能',p['function']),('建模尺寸与形状',p['features']),('安装接口',p['interfaces']),
           ('候选材料与工艺',p['material_candidate']),('仍需验证',p['validation']),('拆装方向',p['removal'])])
        prev=f'<a href="{parts[i-1]["part_id"]}.html">← 上一部件</a>' if i else '<span></span>'
        nxt=f'<a href="{parts[i+1]["part_id"]}.html">下一部件 →</a>' if i+1<len(parts) else '<span></span>'
        body=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{p['part_id']} {p['name']}</title><style>{CSS}</style><main><a href="../index.html">返回部件目录</a><div class="eyebrow">BM1 / V0.2 / {p['assembly_id']}</div><h1>{p['part_id']} {p['name']}</h1><p class="note">独立部件介绍页 · 图册第 {p['page']} 页 · 概念外形，非加工图</p><p><span class="chip">{p['kind']}</span><span class="chip">数量 {q}</span><span class="chip">包络 {' × '.join(map(str,p['bbox_mm']))} mm</span></p><div class="hero"><div class="visual">{svgtext}<p class="note">显示的是部件外形和功能层次。供应商接口、运动接触面及公差需在工程模型中确认。</p></div><div class="card">{info}</div></div><div class="nav">{prev}{nxt}</div><footer>2026-10-26 · 以 data/design.json 和部件清单为准。物理性能与强度未实测。</footer></main></html>'''
        (ROOT/'pages'/f'{p["part_id"]}.html').write_text(body,encoding='utf-8')
    blocks=[]
    for aid,a in ASM.items():
        cards=[]
        for p in parts:
            if p['assembly_id']!=aid:continue
            cards.append(f'<a class="thumb" href="pages/{p["part_id"]}.html"><img src="figures/{p["part_id"]}.svg" alt="{p["name"]}概念图"><span class="eyebrow">{p["part_id"]}</span><strong>{p["name"]}</strong><span class="note">{p["kind"]} · PDF {p["page"]}页</span></a>')
        blocks.append(f'<h2 id="{aid}">{aid} {a["name"]}</h2><p class="note">{a["role"]}</p><div class="grid">'+''.join(cards)+'</div>')
    body=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BM1 羽毛球发球机设计目录</title><style>{CSS}</style><main><div class="eyebrow">BM1 / V0.2 / 2026.10.26</div><h1>羽毛球发球机三维建模设计方案</h1><p>10 个功能总成，44 类关键部件。选择部件查看独立介绍页；整个目录可以离线阅读。</p><p><a href="BM1_Design_Book_V0_2.pdf">打开 71 页设计图册</a> · <a href="docs/CODEX_TASK.md">Codex 建模任务书</a> · <a href="README.md">使用说明</a></p><p class="note">当前是完整的概念设计与建模任务书。尚未生成生产 CAD、加工图或完成实物验证。</p><nav>{''.join(f'<a class="chip" href="#{aid}">{a["name"]}</a>' for aid,a in ASM.items())}</nav>{''.join(blocks)}<footer>图形为本设计的结构示意。所有数字初值均有状态标记；不得将供应商占位件或动画当作已验证的工程结果。</footer></main></html>'''
    (ROOT/'index.html').write_text(body,encoding='utf-8')

def create_readme():
    text='''# BM1 羽毛球发球机三维建模设计包

版本 V0.2，日期 2026-10-26。这里是交给 Codex 执行的设计方案，当前未生成生产 CAD 或加工图。

## 先打开哪些文件

1. `BM1_Design_Book_V0_2.pdf`：71 页图册，包含整机总装、三视图、爆炸关系、供球时序、10 总成与 44 类关键部件独立介绍页。
2. `index.html`：离线部件目录。`pages/` 内有 44 个独立 HTML 介绍页，每页内嵌图形。
3. `docs/CODEX_TASK.md`：完整的 Codex 执行任务书，包含可直接复制的总提示词。
4. `data/`：统一参数、BOM、接口、关节、运动层级、传感位置、未决问题及参考资料。
5. `figures/`：SVG 结构图与单件示意。它们说明建模意图，不是由已验证工程 CAD 导出的加工图。

## 怎么交给 Codex

解压完整文件夹，让 Codex 能读取它。把 `docs/CODEX_TASK.md` 的最后总提示词发给 Codex，并要求先读取本目录的 README、任务书和全部 data 文件。

可以这样说：

> 请读取这个设计包，按照 docs/CODEX_TASK.md 开始实际建模。以 data/ 为唯一参数来源，先完成球路、装载和运动避让，再完成整机、外壳、工程导出、图页和展示。请持续执行并提交可重建源代码及实际模型文件；未完成或未验证的部分明确列出。

## 设计的主线

- 双水平轮盘只接触球头。球头朝下、羽毛向上，侧向喂入后需要验证出轮翻转。
- 同一升降载架同时携带固定供球器和运动机头。固定指不参与左右/俯仰，不是固定在地面高度。
- 先收回导套，再把托球中心从 X=-190 前移到 -85，之后才能转头。最终喂入展示终点 X=-5 不是已确定的解夹点。
- 默认出球轴高 1500，手动范围 1400–1800；储球管长 540；整机总高默认约 2170，范围约 2070–2470，含20顶盖预留。
- 机头后部收窄并抬高，避免完整低位长板在俯仰/偏航时撞 U 架和固定筒柱。
- 语音只请求训练设置，本地控制器校验与执行。实体停止和故障恢复不依赖对话模型。

## 数字的含义

`concept` 表示用于建立 V0 几何的初值。`supplier_verified` 表示真实供应商图纸已核对。`prototype_verified` 表示样机测过。`frozen` 才可进入冻结加工流程。当前大部分值为 concept。

`null` 不是 0。它表示没有选型、没有测量或尚待拆分。尤其不能为 wheel RPM、落点标定、有效轮压缩、实际容量、强度和安全等级编造数值。

44 是关键主项数，不是最终物理零件数量。自制总成的板件、导向块、法兰与紧固件需以派生料号展开；0903 是配电功能模组，0905 是传感器族，不能各当成一个已确认 SKU。

## 本轮生成与下一轮待生成

本轮已有：PDF、HTML介绍页、SVG示意、JSON/CSV规格、Codex任务书与图册生成源文件。

下一轮应生成：参数化 CAD 源、总装/逐件 STEP、BLEND、GLB、真实模型导出的工程视图、爆炸和供球动画、数字检查报告以及完善后的部件册。不得把前一段列出的设计文件当作后一段的已完成物。

## 复现本设计图册

`source/design_data.py` 保存本册文字与概念值；`source/drawings.py` 和 `source/build_book.py` 生成矢量结构示意和PDF；`source/build_handoff.py` 生成接口数据和HTML目录。这些是设计文档的生成工具，不是可用于加工的 CAD 建模源。

依赖 Python、ReportLab、PyMuPDF，以及可用的字体。运行：

```bash
python source/build_book.py
python source/build_handoff.py
```

修改设计时，应同步维护 data 与图册源，并重新核对。实际 CAD 阶段以 data 为输入建立独立工程源，不用这些简单图形函数替代实体建模。

## 参考与许可

一手来源列在 data/sources.json 和图册末页。当前示意图没有导入第三方 CAD 文件。未来复用 BadmintonAce、ThongPaDisp 等项目时，需按被复用文件的实际许可保留作者、许可和修改记录。
'''
    (ROOT/'README.md').write_text(text,encoding='utf-8')

if __name__=='__main__':
    create_metadata();create_html();create_readme()
    print('metadata and 44 HTML introduction pages generated')
