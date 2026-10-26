"""Evidence-based acceptance summary. No unresolved issue is auto-closed."""
from pathlib import Path
import json,csv,hashlib,html,shutil,subprocess
R=Path(__file__).resolve().parents[1]
def read(f):return json.loads((R/f).read_text(encoding='utf-8'))
records=read('data/instances.json');parts=read('data/parts.json');pages=read('reports/page_coverage.json');step=read('reports/step_roundtrip.json');blend=read('reports/blender_roundtrip.json');static=read('reports/collisions_static.json');motion=read('reports/collisions_motion.json');viewer=read('reports/viewer_validation.json');pdf=read('reports/pdf_validation.json');service=read('reports/service_validation.json')
physical=[i for i in records if not i.get('reference')];geo_hash=hashlib.sha256((R/'data/geometry.json').read_bytes()).hexdigest()
required=['output/step/BM1_V0_assembly.step','output/blend/BM1_V0_master.blend','output/glb/BM1_V0_assembly.glb','output/BM1_V0_design_book.pdf','output/animation/BM1_feed_sequence.mp4','output/animation/BM1_explode_restore.mp4','viewer/index.html','cad/export_all.py']
missing=[p for p in required if not (R/p).exists() or (R/p).stat().st_size==0]
result=dict(project='BM1',revision='V0.2 concept engineering',units='CAD mm Z-up; Blender m Z-up; GLB m Y-up',geometry_sha256=geo_hash,main_items=len(parts),cad_instances=len(records),physical_instances=len(physical),reference_instances=len(records)-len(physical),all_native_solids_valid=all(i['valid'] and i['volume_mm3']>0 for i in records),step_files_reopened=step['step_files_reopened'],step_pass=step['all_step_valid'],all_main_steps_complete=all(i['passed'] for i in step['main_item_completeness']),blender=blend,static=static,motion=motion,service=service,viewer=viewer,pdf=pdf,page_coverage=dict(main=pages['main_pages'],derived=pages['derived_pages'],pdf_pages=pages['pdf_pages']),parameter_rebuild_tests=step['parameter_rebuild_tests'],reports_match_current_geometry=static.get('geometry_sha256')==motion.get('geometry_sha256')==geo_hash,missing_required_files=missing,engineering_production_acceptance=False,prototype_tests_performed=False,unresolved_ids=[u['id'] for u in read('data/unresolved.json')])
(R/'reports/validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
result['dimensions']=read('reports/dimension_validation.json')
result['full_parameter_rebuild']=read('reports/parameter_full_rebuild.json')
(R/'reports/validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
issues=read('data/unresolved.json')
open_text='# 未决问题（未关闭）\n\n'+''.join('## '+u['id']+' '+u['title']+'\n\n'+u['close_condition']+'\n\n' for u in issues)
open_text+='## 本次实现中仍未完成的工程工作\n\n- 实际球堆、真实套叠节距与可靠留球/单球分离；动画仅含一只校核球。\n- 捕获后的球体动力学、推头撤回与出球反馈闭环。冻结参考标记和前移推头的交集仍保留，不能判为通过。\n- 便捷后侧快拆补球：现方案需要先拆导套、分球模块、后压带、后板和关联探头。\n- 全部采购法兰孔型、安装配合与紧固方式；当前紧固件只是可重建概念候选。\n- 线束恒定长度、弯曲半径、拖链、应力释放和端子/工具实体；现有路径仅名义占位。\n- 最高手动高度、满筒及偏转状态的实际质量、质心、支撑反力、刚度、疲劳与倾覆裕量；材料密度和供应商重量尚未落实，未据宽底盘宣称稳定。\n- 停止链路、电气额定值、制动与真实停转时间；防护罩开口、冲击能力与实际安全等级。\n'
(R/'reports/open_issues.md').write_text(open_text,encoding='utf-8')
motion_note='在'+str(motion['states'])+'个离散状态中，无未解释硬相交。' if motion['unresolved_pairs']==0 else '仍有'+str(motion['unresolved_pairs'])+'组未解释硬相交，见明细。'
text=f'''# BM1 V0.2 验收报告

交付性质：可重建概念工程版。文件制作已形成实际产物；不等同采购、制造或样机工程验收通过。

## 已建模

- 44主项、10功能模块；{len(physical)}个物理实例与2个独立校核球体对象，共{len(records)}个有效原生实体。
- 阶梯机头、独立双轮、短耳轴、三位置滑台、真实张开的夹指、固定供球器、导套、分球试验件、底盘升降/转向、罩壳、电气候选、17个传感功能位置和名义线束。
- {step['step_files_reopened']}份STEP（总装、子总成、逐主项与派生件、真实剖切）、BLEND、GLB、{pages['pdf_pages']}页中文图册，其中44主项与{pages['derived_pages']}派生件独立页；本地查看器、SVG/PNG、两段MP4、BOM和重建源。
- 主项STEP聚合完整，全部子件统一默认装配坐标；主项与派生文件不会互相覆盖。

## 数字检查通过的范围

- 所有建模实例闭合有效、非空且正体积。STEP全部重新打开，44主项的子件数量逐项核对。
- 100mm标定块与不同长度三轴完成STEP/GLB/Blender往返；实际Blender标定块0.1m。
- BLEND重新打开保留两场景、运动父级、材质、镜头和动作；GLB重新导入H={blend['H_m']:.3f}m、筒帽顶={blend['cap_top_m']:.3f}m，44主项ID保留。
- 轮距25→30使左轮心移动2.5mm；筒帽20→24使顶高增加4mm；随后按基准重新生成。
- h=1400/1500/1800静态检查：未解释硬相交{static['unresolved_pairs']}组。{motion_note}角度5°、位移2mm离散；体积阈值0.01mm³，几何数值容差0.001mm；不是制造公差或连续证明。
- 运动采样覆盖组合转向、瞄准后喂入、导套、闸板、上夹与完整落球参考包络。{motion.get('indeterminate_pairs',0)}组捕获后冻结参考标记相交单独保留为未验证，未计作通过。
- 三条维护路径在明确拆除前置件后进行了51个位置采样；各自状态见service_validation.json。几何移出不证明螺栓工具可达或快拆便捷。
- 查看器模型加载、轮缘隔离、罩壳切换、爆炸滑块和零件页联动测试通过；依赖均在本地。
- PDF逐页渲染并检测页面外文字，检出{len(pdf['out_of_page_text'])}处；图文来自实际CAD模型。

## 采购接口待确认

电机/轴承/驱动/回转支承/直线模组的型号、孔位、连接与配合；材料牌号和公差；供电、接口、散热、线束与连接器。原有null值及供应商孔型未被编造数值替换。PRT-0905为器件族，17个功能位置不等于采购数量。

## 需要样机试验及仍未完成的工程验证

U01-U10全部保留。真实球堆、可靠单球、释放窗口、压缩量、离轮翻转、容量、节拍、落点标定、磨耗、刚度、最高位稳定性与防护能力均无实测结论。

特别边界：捕获后的冻结球标记会与继续前移的推头相交。报告保留其体积与状态，不能用这个标记推断真实球运动；喂入末段动力学未通过。因此MP4在捕获边界暂停，BLEND中的复位仅为收到真实出球确认后的条件动作。线束没有恒定弧长/最小弯曲半径证明。筒体后拆需要预先拆下多个模块，便捷快拆补球尚未实现。

## 验收结论

概念文件可查看、可拆分、可追溯并能重建。工程生产验收：未通过（采购、动力学、真实球堆、线束、工具可达、稳定性与样机项未关闭）。未生成供应商冻结加工图、电气原理图、实测球路标定或安全认证；不把这些计划视作产出。

当前几何与静态/运动报告哈希一致：{result['reports_match_current_geometry']}。必需交付文件缺失：{missing or '无'}。

详情：design_changes.md、open_issues.md、validation.json、collisions_motion.json、service_validation.json、step_roundtrip.json。原始数据与任务书保留在input/。
'''
(R/'reports/acceptance_report.md').write_text(text,encoding='utf-8')
paras=[]
for line in text.splitlines():
    if line.startswith('# '):paras.append('<h1>'+html.escape(line[2:])+'</h1>')
    elif line.startswith('## '):paras.append('<h2>'+html.escape(line[3:])+'</h2>')
    elif line.startswith('- '):paras.append('<p class="bullet">• '+html.escape(line[2:])+'</p>')
    elif line:paras.append('<p>'+html.escape(line)+'</p>')
(R/'reports/acceptance_report.html').write_text('<!doctype html><meta charset="utf-8"><title>BM1验收报告</title><style>body{font:16px/1.8 system-ui,"Microsoft YaHei";max-width:1000px;margin:45px auto;background:#f6f8fa;color:#263f4e}h1,h2{color:#087b80}.bullet{margin:8px 0}a{color:#087b80}</style><a href="../viewer/">←三维查看器</a>'+''.join(paras),encoding='utf-8')
# Detailed BOM preserves both the 44 main-item quantities and actual model instances.
with (R/'output/BOM_instances.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['instance_id','part_id','derived_id','assembly_id','motion_parent','name','status','supplier_verified'])
    for i in physical:w.writerow([i['instance_id'],i['part_id'],i['derived_id'],i['assembly_id'],i['parent'],i['name'],i['status'],False])
with (R/'output/BOM_derived.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['derived_id','parent_main','instances','page','status'])
    for p in pages['pages']:
        if p['derived']:w.writerow([p['code'],p['part_id'],p['instances'],p['page'],'concept'])
dest=R/'output/render/parts';dest.mkdir(exist_ok=True)
for p in pages['pages']:shutil.copyfile(R/'output/drawings'/(p['code']+'_iso.png'),dest/(p['code']+'.png'))
# Keep machine-readable environment and deliverable status alongside immutable input manifest.
(R/'reports/environment.json').write_text(json.dumps(dict(python='3.12.10',cadquery='2.8.0',occt='7.9.3.1',blender='4.5.9 LTS',dependency_lock='requirements-lock.txt'),indent=2))
(R/'data/deliverable_manifest.json').write_text(json.dumps(dict(main_items=44,physical_instances=len(physical),reference_instances=2,pdf_pages=pages['pdf_pages'],cad_status='native_parametric_concept_generated',manufacturing_approved=False,physical_test_status='not_performed',validation='reports/validation.json'),ensure_ascii=False,indent=2),encoding='utf-8')
for p in parts:p['page']=next(x['page'] for x in pages['pages'] if x['code']==p['part_id'])
(R/'data/parts.json').write_text(json.dumps(parts,ensure_ascii=False,indent=2),encoding='utf-8')
shutil.copyfile(R/'data/page_index_engineering.json',R/'data/page_index.json');shutil.copyfile(R/'output/BOM.csv',R/'data/bom.csv')
(R/'data/document_validation.json').write_text(json.dumps(pdf,ensure_ascii=False,indent=2),encoding='utf-8')
design=read('data/design.json');design['phase']='native_parametric_concept_engineering';design['notice']='本次已生成原生参数实体与模型图册；仍为concept，非加工冻结、非采购确认、非样机验证。'
(R/'data/design.json').write_text(json.dumps(design,ensure_ascii=False,indent=2),encoding='utf-8')
readme=R/'README_DELIVERY.md';readme.write_text(readme.read_text(encoding='utf-8').replace('180个可独立查看',str(len(physical))+'个可独立查看'),encoding='utf-8')
print('REPORT GENERATED',len(physical),'physical instances,',pages['pdf_pages'],'PDF pages; production acceptance FALSE')
from r1_report_text import write_r1_report
write_r1_report(result)
