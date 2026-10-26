from pathlib import Path
import json,html
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text(encoding='utf-8'))

def write_r1_report(result):
    contract=read('reports/r1_contract_validation.json');service=read('reports/r1_service_validation.json');bench=read('reports/r1_bench_validation.json');mass=read('output/engineering/mass_evaluation.json')
    result.update(revision='V0.2-R1',r1_contract=contract,r1_service=service,r1_bench=bench,mass_evaluation=mass)
    (R/'reports/validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    motion=result['motion'];length=contract['cable']['analytic_length_min_mm']
    text=f'''# BM1 V0.2 R1 验收报告

交付性质：可重建概念工程修订与样机工作包。没有进行实物测量、供应商确认、采购或硬件试验；制造批准仍为否。上一版交付 ZIP 保留。

## 已建模与已制作

- 44主项、10模块、{result['physical_instances']}个物理实例、2个独立参考对象；全部{result['cad_instances']}个原生实体有效且正体积。
- {result['step_files_reopened']}份总装/逐件/子总成/剖切STEP回读；另有{len(bench['step_reopened'])}份低速试验台、夹具和弧面嵌件STEP回读。BLEND含装配、爆炸、供球组件后抽3个场景；GLB保留44主项。
- {result['page_coverage']['pdf_pages']}页中文模型图册，其中44主项和{result['page_coverage']['derived']}派生件独立页；修订与试验手册、三段MP4、本地查看器、BOM和源代码。
- 供球器作为完整抽出组件，新增两只承接槽和两只横销；原编号保留并用PRT-0202派生编号记录。
- 上夹弧面R29为装机候选，另给R23/R26/R32试装件。独立低速试验台不含高速轮，静态未解释硬相交{len(bench.get('static_intersections',[]))}组。
- 离线反馈合同模拟器、逐件质量/质心计算入口、44主项采购接口表、测球和试验空表、10项试验规程、概念功能接线图均已生成。

## 数字检查通过的范围

- h1400/1500/1800静态检查未解释硬相交{result['static']['unresolved_pairs']}组；{motion['states']}个离散运动状态未解释硬相交{motion['unresolved_pairs']}组。角度5°、普通路径2mm、接近捕获0.25mm；交集阈值0.01mm³，数值容差0.001mm。不是连续证明或制造公差。
- R1带球前进停于理想首次接触行程{contract['capture_first_tangency_stroke_mm']:.6f}mm；X=-5对应185mm仅在空滑台检查中允许。轮组捕获可靠位置、制动距离和牵引力仍待试验。
- 捕获后独立世界参考球保留，撤回路径检查没有原版的继续前推相交；没有预设真实飞行轨迹。缺少新出球高→低脉冲时，控制合同不允许撤回。
- 供球组件维护：两销外退55mm检查29个位置，整套后抽350mm检查176个位置；路径通过={service['all_paths_passed']}。维护高度H1400，动态高度线束按该高度重建。前提：空筒、隔离电源、轮组停转、托车承重和接线断开；未证明销锁承载或真实插拔操作。
- 滑台回线解析总长{length:.6f}mm，含180°回环和90°出线；186个位移状态恒长。中心线半径21.5mm、线缆半径2mm、内侧半径19.5mm；均为设计候选。实际电缆允许弯曲半径及耐久仍待厂家数据和试验。
- 两组全总装参数变更重建并恢复基准；STEP、BLEND、GLB回读和标定检查通过。查看器加载、隔离、罩壳、爆炸与介绍页检查见viewer_validation.json。
- 18项回归测试通过；独立审查的7项问题已补失败测试并修复。完整周期17个输入样本和故障注入仅证明离线逻辑，不代表真实硬件或功能安全等级。

## 采购接口待确认

supplier_interface_RFQ.csv与interface_signoff.csv已列出外形、孔型、轴径、配合、扭矩/载荷、惯量、行程、供电、停止和质量资料要求。没有依据包络选择实际型号，没有联系供应商或下单。官方THK、igus、Oriental Motor资料作为核对要求来源，链接见工程工作包；不代表厂家认可本设计。

## 需要实物输入和样机验证

U01-U10全部保留。球型和套叠节距、夹力/损伤、可靠单球率、捕获释放窗口、轮胎压缩/转速、停止时间、防护、真实容量、节拍与落点标定均未实测。

三组套叠节距30/40/50mm只是敏感性假设；弧面半径不是测量结果。没有用理想包络相交推断夹持可靠性。

质量工具当前返回{mass['status']}，缺少{len(mass.get('missing_instances',[]))}个实例的质量/质心证据；实际支脚反力与稳定性未得到结论。负/零/非有限刚度或重力被拒绝。升降及偏航/俯仰线束、应力释放和完整端子实体仍未完成工程验证。

样机工作包把上述工作组织为可填写记录和可执行计算；空表、试验规程和功能接线示意均不计作实测、冻结加工图或电气接线批准。

## 结论

数字修订与文件交付已形成实际产物；制造及样机验收未通过。剩余事项需要实际样品、采购图纸、现场装配与测试条件，不能通过继续生成文件代替。

几何/静态/运动报告哈希一致：{result['reports_match_current_geometry']}。所列基础交付缺失：{result['missing_required_files'] or '无'}。详细结果见validation.json、r1_service_validation.json、r1_contract_validation.json、r1_bench_validation.json和r1_code_review.md。
'''
    (R/'reports/acceptance_report.md').write_text(text,encoding='utf-8')
    body=[]
    for line in text.splitlines():
        tag='h1' if line.startswith('# ') else 'h2' if line.startswith('## ') else 'p';value=line[2:] if tag=='h1' else line[3:] if tag=='h2' else line
        if value:body.append(f'<{tag}>'+html.escape(value)+f'</{tag}>')
    (R/'reports/acceptance_report.html').write_text('<!doctype html><meta charset="utf-8"><title>BM1 R1验收报告</title><style>body{font:16px/1.8 system-ui;max-width:1050px;margin:40px auto;color:#183a4d;background:#f4f7f9}h1,h2{color:#087b80}</style><a href="../viewer/">三维查看器</a> · <a href="../output/engineering/index.html">工程工作包</a>'+''.join(body),encoding='utf-8')
    unresolved=read('data/unresolved.json');pending='# 未决问题 / R1\n\n'+''.join('## '+u['id']+' '+u['title']+'\n\n'+u['close_condition']+'\n\n' for u in unresolved)
    pending+='## R1新增边界\n\n抽出组件负载与防误解锁、复装对中、线束插接和托车操作待实测。滑台回线恒长通过解析检查，但电缆规格/耐久未确认，其他运动线束仍待完善。低速试验台未做强度或锚固批准。离线控制器没有硬件连接，不是安全控制器。见output/engineering/test_protocols.json。\n'
    (R/'reports/open_issues.md').write_text(pending,encoding='utf-8')
