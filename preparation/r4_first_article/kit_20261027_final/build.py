"""Create a separate, non-releasing workshop preparation bundle from frozen R4 evidence.
Run from repository: python preparation/r4_first_article/build.py --out <NEW_DIRECTORY>
Existing output directories are rejected; never target evidence or original output.
"""
import argparse, csv, hashlib, json, shutil, sys, zipfile
from pathlib import Path
from xml.sax.saxutils import escape

R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R))
from tools.build_context import verify_content_context

INPUTS=[
('U01','预算和办理范围','询价前','PROCUREMENT','你','首轮预算上限、交付城市、期望日期、是否已有加工联系人；未知写“未定”。数量由分组/报价确认，不默认下单。','文字回复；联系人可只给公司/能力，不必给个人隐私'),
('U02','球样实收','首件尺寸冻结前','BALL-SAMPLES','你/现场','已有球的型号、速度标识、批次、实收数、新旧/损伤；没有实物则写“尚未购买”。72 只仅是既有计划。','包装与逐球照片、采购凭据或批次说明'),
('U03','逐球与堆叠测量','首件尺寸冻结前','BALL-SAMPLES','测量人员','逐球球头多方向直径/高度、裙径、全长、质量；同组 1/3/6 只堆高、分离力、卡滞；量具编号/分辨率/校核和原始视频。','填写 ball_measurements、stack_force、instruments；原始附件'),
('U04','加工能力及图纸反馈','首件下单前','PROCUREMENT','加工方','可加工材料和装夹方案、薄壁/曲面/沉孔/孔边风险、可检验基准、毛刺边缘处理、缺失关键公差；逐条回复不能只写“可做”。','supplier_reply；原厂/加工方标注图'),
('U05','报价及首件约定','首件下单前','PROCUREMENT','你/加工方','按料号版本报数量、单价、编程/工装/检验费、材料、运税、交期；约定报告/不合格返修/禁止擅改。','quote_reply；正式报价附件'),
('U06','真实导向和执行器','相关零件冻结前','R3-O01/R3-O02','机械人员/供应商','现有或拟选导轨、滑块、执行器型号和原始图纸版本；安装孔/夹持区、行程、负载/力矩、失电保持和手动操作方法。未选型写未选型。','PDF/STEP原厂文件、铭牌照片、规格来源'),
('U07','工作台及锚固','底板加工与试装前','R3-O04','你/现场','台面材质/厚度/外形/支承跨度、底部照片、可用夹持/钻孔区、背板/锚固方案；是否允许加工台面。','带尺照片/草图、现场尺寸表'),
('U08','材料紧固与装配评审','手动试验前','R3-O03/R3-O05','机械人员/加工方','材料批次、紧固件等级、夹紧/预紧与防松方案；限位、保持、反力路径、装拆工具及球头/羽裙接触评审。扭矩不得凭模型指定。','材质/紧固件证明、签署的装配和首件检验记录'),
('U09','试验资源与人员','手动试验前','R3-O05','你/现场','现场负责人、机械审核人、测量人；量具/力测量/相机与时间同步条件、隔离区域；缺少的器材写无。','人员角色表、仪器清单、台架全景'),
('U10','电气接口及停机链','通电低速前','ELECTRICAL','电控人员','真实驱动器/电源/执行器电气图、I/O极性/接线/掉线行为、独立停机链、失电保持策略、位置反馈与限位；各轴审批的速度/力/电流/行程和到位容差。','签署I/O表、接线图、参数单、风险处置评审'),
('U11','首件与无能源试验记录','通电低速前','R3-O01/R3-O02/R3-O03/R3-O04/R3-O05','现场/审核人','实收尺寸与偏差、成套装配记录、逐轴空行程、单球接球/夹持/释放及3/6只分球结果；所有失败和人为介入保留。','inspection、manual_checks、cycle_log、nonconformance与原始录像'),
('U12','通电阶段实测及单独轮组资料','逐级试验；轮组另案','ELECTRICAL/WHEELS','电控/机械人员','在已批准方案下测量实际停止时间/距离及故障行为；轮/轴/毂原图、额定限制、转速反馈和防护资料留待独立轮组试验。','stop_tests和原始波形/视频；轮组资料另存，缺失不阻止询价准备')]

CHAPTERS=[
('01 工作范围与顺序',[
'本包是 R4 之后的加工和现场准备资料，状态 PREPARATION_ONLY。没有下单、发消息给供应商、连接硬件或执行实物试验。整机、首件和自动运行放行均为 false。',
'路径：资料收集/供应商工艺评审 → 球样及接口冻结 → 三类首件逐项审批 → 来料尺寸检验 → 无能源逐轴试装 → 单球 → 3/6只堆叠 → 经电控确认的低速供球。阶段之间均需要真实记录和责任人签署。',
'不要将“低速”理解为某个默认转速。此包不指定轮速、轴速度、力、电流、扭矩、循环成功率阈值或安全等级；实际限值须由选定硬件和测量确定。轮组发射属于后续独立台架，本包不提供运行程序。',
'三类首件只覆盖承托、夹块与底板候选，不构成完整试验台 BOM。既有 R4 全部附属导向/限位/保持/连接仍需逐项装配审查，不能仅购买三件就进入通电。']),
('02 加工方交接说明',[
'本包可用于询价和 DFM 工艺评审，不能作为直接加工指令。请按料号、实际 R3/R4 版本和所附文件 SHA-256 回复；未经书面变更不得缩小部件、删孔或改变连接来解决冲突。',
'询价表数量、单价、交期和供应商均保持空白。报价必须区分材料、加工、装夹/编程、检验、运税及备选件；确认承托/夹块是否分别报价，左右夹块是否成对。当前 R29 只是候选，不能把四种半径全部视作采购数量。',
'STEP 单位 mm。首件图采用局部 STEP 原点，A=底面、B=最小Y侧、C=最小X侧是待加工方确认的候选基准；原装配 H 坐标不可混用。局部坐标必须依 first_article_features.json 的 local_origin_H_mm 转换。',
'既有一般线性 ±0.2 mm、孔坐标 ±0.1 mm 为项目询价候选，不是供应商能力证明；关键配合公差仍未确定。尺寸未定义、配合/平面度/轮廓/表面状态未约定时，先提问再加工。',
'需返回：逐项 DFM 答复、标注缺失信息的图、材料候选及批次证明方式、拟定工艺/检验方法、报价、交期、首件检验报告样式和返修约定。文稿在 supplier_message_DRAFT.md，尚未发送。']),
('03 三类首件工艺与检验关注点',[
'PRT-0701-R4-A：沿用一体机加工承托方案。中心承托面须从同一母体保留，不能改为浮动垫片。核对加工装夹、承托面相对底面高度、槽/指爪空间、毛刺和接触损伤。未声明新安装孔，连接/导向反力需另核对。真实球样适配前不可冻结关键配合。',
'PRT-0603-R3-R29-L：保留的 R3 左夹块，候选 POM-C。M4 为间隙通孔和顶面沉孔，不在 POM 间隙孔中加工螺纹。检验轮廓、孔轴/沉孔深度、剩余孔边、螺钉头落座、夹球压痕和释放。夹块装夹变形及材料批次由加工方确认。',
'夹块参考：R23/R26/R29/R32 的 L/R STEP 全部附作筛选资料；除三个原首件图页外，其余七件补充了原生 STEP 投影评审图和特征索引。若采购成对或其他半径，仍须为所选每件确认对应图纸/关键公差/版本。禁止把镜像或左右配对当作已放行。',
'PRT-0602-R3-BASE：候选 6061-T651 底板。先确认真实台面、支承和锚固，再评审装夹基准、孔坐标、板件变形和平面度。模型中的台面锚固预留孔不是实际工作台孔位，未经现场确认不得照图钻台面。',
'三张原首件图及 STEP 是冻结 R4 候选的原文件副本，另七张夹块图由冻结 STEP 新生成；原始尺寸来源保存在 reference/，新增图的派生特征见 additional_jaw_features.json。本准备包没有新增工程尺寸或供应商接口。']),
('04 首件接收与尺寸检验卡',[
'收到零件先隔离待检，记录供应商、图纸版本/哈希、料号、左右、数量、材料批次、到货日期和运输损伤。核对供应商报告与实物编号，未知材料或版本不明不得按合格入库。',
'按三张首件图和特征 JSON 检查外形、孔/沉孔、承托高度、轮廓与底板基准。量具必须有编号、分辨率与校核记录；软材料测量方法要一致。测量结果填写实际数值和单位，未知用空白/OPEN，不填0代替。',
'既有 inspection 表只提供特征提示，不是完整检验规程。每项先填最终批准名义值、公差/方法及来源，再判定；未定义关键验收要求时保持 OPEN。判定不能由一般公差自动扩展到所有配合。',
'偏差需记录 NCR 编号、实际值/照片、影响和处置意见。返修必须有修订图或批准指令及复检；不允许“先用着”代替记录。填写副本另存 evidence/runs/；模板和原始 R4 文件不修改。']),
('05 无能源试装卡 M0/M1',[
'M0 入场：机械负责人确认能源隔离方式、重力/弹性储能及保持方法、台架锚固、操作隔离、工具和部件清点。不能把拔电源等同于所有轴安全保持；未知保持能力先停止。通过记录与签名为空，必须现场填写。',
'M1 空载逐轴：上夹、下闸、导套、接球滑台、接球夹分别操作。记录起止位置/实际方向、阻力、侧隙、上下限位、锁销/保持件、返程及可能夹点。固定件不可跟随移动；限位不得靠碰撞别的零件实现。',
'按 R4 指定拆装次序核对锁销从安装位到停放位、工具接近和零件移出。图中的 64 段路径和 44 个工具包络是名义数字检查，不是现场工具/手部可达证明。',
'停止条件：导向脱出、连接松动、保持无效、工具干涉、台面变形或异常阻力。先记录失败，隔离并评审，整改后重做受影响阶段。不要为完成表格强行拉动。']),
('06 单球与堆叠人工卡 M2/M3',[
'M2：使用已编号实测球，导套在装载下位、滑台在装载位，观察开夹接球的真实承托接触、倾斜、回弹和羽裙。记录球号/批次、夹块左右/半径、版本、照片和视频时间点。',
'闭夹并记录夹持/释放力及球头损伤。导套必须先回缩到位，托架才能前移脱筒，之后才可讨论机头转向；本 R4 夹具没有轮组，不能验证轮捕获或发射。',
'上夹保持 → 下闸开启 → 单球接收 → 下闸闭合 → 上夹释放的交接逐项观察。若上夹不能承载球堆或下闸不能保持，停止，不继续增加球数。夹块半径一次只变一个条件。',
'M3：单球阶段批准后再用同组 3/6 只堆叠。保留每次请求，包括双球、无球、卡滞、损伤和人为干预。重复使用同一球不算新的独立样本。',
'双球、回弹脱位、羽裙/球头损伤、卡滞或人为介入均暂停升级；先保存原始记录。成功阈值要在首轮尺寸/力证据后冻结，不根据已发生结果反向改阈值。']),
('07 通电低速准入卡 E0',[
'E0 仅是准备卡，当前 BLOCKED。要求 M0-M3 对应证据已审核，真实电气图/接线/I/O/掉线行为/失电保持明确，独立停止链和操作者隔离方案经负责人员审查；批准的各轴参数及验收限值已记录。',
'低速阶段仅限供球机构，轮组不得因本卡获授权。速度、力/电流、行程、到位容差、超时、采样/去抖/监视周期和停止距离上限必须来自硬件方案及评审，空白时不执行。',
'control/feed_cycle.py 是离线合同模拟器，没有真实驱动、安全输出或硬件看门狗；不能把 estop_ok、wheels_ready 或 capture_detected 强制为 true 以运行台架。应另行完成硬件适配与独立验证，再进入试验。',
'对每个轴记录失电后的实际行为和受控停止办法。保持未知时不提供“一律断电”操作指令；急停/掉电测试只能由负责人员在已评审的固定/隔离条件下实施。',
'E0 批准不等于后续试验成功。先逐轴空载，再经审查做单球/堆叠；每一级都需要新结果。硬件不具备的测试记录 NOT_RUN，并保持其后阶段 BLOCKED。']),
('08 低速功能与故障试验卡 E1/E2',[
'E1 计划项目：逐轴方向、位置反馈、行程限位、保持；到位时再发新命令应有新的接受/完成确认；延迟到位、旧周期/旧命令、重复采样不得被当作新完成。具体激励方法由硬件工程师填写后审核。',
'连续联锁项目：导套下位约束装载；回缩确认先于滑台脱筒；下闸闭合后才能释放上夹；脱筒先于转向；捕获前/后球体所有权需真实传感证据。R4 无轮捕获，相关项 NOT_RUN，不得伪造反馈跑通。',
'故障项目：防护/锁止反馈丢失、通信中断、位置反馈异常、停机/暂停/复位/重连。确认停止意图与实际轴行为一致，复位或重连回到待命，需要独立新启动，不能自动续跑。软件测试通过不替代硬件记录。',
'停止测量：记录轴/载荷/姿态、命令与物理触发定义、时基同步方法、初始速度、停止位置/时间、原始波形或逐帧视频及测量不确定度。审批限值空白时不得判 PASS。',
'E2：E1 经审核后才做单球、再做同组球堆。冻结夹块/球样/参数和验收规则后，才执行原计划封存 12 只及 300 次复核；300 次不是300个独立球，也不是量产可靠性结论。']),
('09 记录、统计与证据交接',[
'每次请求单独一行：request_id、run_id、球号/球堆号、硬件修订、姿态、阶段、实际位移/力/时间、结果、缺陷标签、人工干预、录像时间点。结果只选 valid_single/double/empty/jam/aborted/other 之一；损伤另列，不能与主结果混合导致重复计数。',
'有效单球率=valid_single/全部请求；另报损伤、人工干预和中止次数。全部请求含失败/中止；无请求时比例未定义。原始表不可删行，修正需保留更改前文件和原因。未执行表不参与统计。',
'每次运行保存设置快照、零件/图纸/程序版本、人员、环境、仪器、球样和原始附件。证据索引记录文件相对路径、字节数、SHA-256、来源、日期、硬件版本和姿态，填写“已验证”不等于真实附件存在。',
'templates/ 全部是 PLAN/BLANK；复制到独立 evidence/samples 或 evidence/runs 后填写。不要运行生成器覆盖实测；生成器拒绝已存在的输出目录。该包记录表是采集模板，不冒充现有质量/支承求解器的数据接口。',
'任何尺寸、接口或控制修改须更改正式 data/源码，重新执行受影响的 R4 数字检查并换用新修订；本准备包与原包哈希会帮助识别旧版，不能以新签名覆盖旧文件。']),
('10 一次性资料回传说明',[
'先回答你知道的事实，未知写“未选型/未购买/未测/没有”。你不需要现在独自完成专业测量、电气设计或批准扭矩；这些列为加工方/机械/电控/现场人员的交付责任。',
'现在最先需要：预算/城市/日期/加工渠道；已有球样和器材；实际工作台资料；是否有机械、电控和测量人员。没有加工渠道也请明确写无。',
'下单前：球样几何/力测量、候选材料与关键公差、选定左右夹块、真实接口和台面、DFM 答复、数量报价与首件检验约定。无能源试验前：来料尺寸、装配保持、台架锚固及人员/仪器准备。',
'通电前：真实驱动器/执行器/I/O/失电与停止链资料，各轴限值/到位判断、无能源试验记录、硬件适配程序和审核。轮组资料是后续独立试验输入，不阻塞当前纸面询价与手动准备。',
'详细一次性清单在 USER_INPUTS.md 与 templates/input_return.csv，共 U01-U12。可分阶段补齐，但无需反复回答同一个问题；收到资料后按原ID追踪，不把缺项默认为完成。'])]

def write_csv(path,fields,rows=()):
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    out=args.out.resolve()
    if out.exists():raise SystemExit('Refusing existing output directory; preserve records and select a new folder')
    if not out.is_relative_to(R/'preparation/r4_first_article'):raise SystemExit('Output must be within preparation/r4_first_article/')
    zpath=out.with_suffix('.zip')
    if zpath.exists() or zpath.with_suffix('.zip.sha256').exists():raise SystemExit('Refusing existing ZIP or checksum; preserve earlier deliveries')
    proof=json.loads((R/'reports/r4_review_bundle.json').read_text(encoding='utf-8'))
    verify_content_context(R,proof)
    if proof['status']!='REVIEW_ONLY' or proof['manufacturing_release'] is not False:raise RuntimeError('Expected frozen review-only R4 proof')
    out.mkdir(parents=True);(out/'templates').mkdir();(out/'reference').mkdir()
    refs=['data/r4_first_article.json','data/r4_release_scope.json','data/r4_fixture.json','data/r3_fixture.json','docs/test_protocol_r4.md','reports/r4_review_bundle.json','reports/r4_package_check.json','control/contracts.py','control/commands.py','control/feed_cycle.py']
    refs += ['output/fixture_r4/'+n for n in ['first_article_features.json','first_article_RFQ.csv','first_article_inspection_BLANK.csv']]
    refs += ['output/fixture_r4/'+n for n in ['parts_index.json','R4_assembly.png','R4_exploded.png','step/BM1_R4_fixture_assembly.step']]
    features=json.loads((R/'output/fixture_r4/first_article_features.json').read_text(encoding='utf-8'))
    families=[x['family'] for x in features]
    selected=set(families)|{f'PRT-0603-R3-R{rad}-{side}' for rad in (23,26,29,32) for side in ('L','R')}
    refs += [f'output/fixture_r4/step/parts/{family}.step' for family in sorted(selected)]
    refs += [f'output/fixture_r4/drawings/{family}_first_article.png' for family in families]
    for name in refs:
        dest=out/'reference'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/name,dest)
    from preparation.r4_first_article.jaw_drawings import generate
    additional=generate(R,out,selected-set(families))
    h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    source=dict(status='PREPARATION_ONLY',base_run_id=proof['run_id'],base_source_commit=proof['commit_sha'],base_input_sha256=proof['input_sha256'],base_code_sha256=proof['code_sha256'],manufacturing_release=False,first_article_release=False,automatic_operation_release=False,physical_trials_performed=False,source_files={name:h(R/name) for name in refs},generator_sha256=h(Path(__file__)),helper_sha256=h(Path(__file__).with_name('jaw_drawings.py')))
    (out/'source_binding.json').write_text(json.dumps(source,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'WORKSHOP_CARDS.md').write_text('# BM1 R4 首件与低速试验准备\n\n'+'\n\n'.join('## '+title+'\n\n'+'\n\n'.join(lines) for title,lines in CHAPTERS),encoding='utf-8')
    (out/'USER_INPUTS.md').write_text('# 请一次回复的资料清单\n\n未知项写未选型/未购买/未测/没有，不需编造答案。可交给对应负责人填写。\n\n'+'\n\n'.join(f'## {i} {name}\n\n期限：{stage}；关联：{gate}；负责：{who}。\n\n{need}\n\n附件形式：{fmt}' for i,name,stage,gate,who,need,fmt in INPUTS),encoding='utf-8')
    (out/'supplier_message_DRAFT.md').write_text('# 加工方询价文稿 - 未发送\n\n请对附件 BM1 R4 候选做工艺评审和分项报价，当前仅询价、未放行加工。请核对每件实际料号/版本/哈希，并回复 supplier_reply 与 quote_reply 表。\n\n承托为一体保留加工；夹块包含左右和半径备选资料，采购组合/数量未定，其他半径尚缺独立批准图；底板锚固依真实工作台确认。不得用通用公差替代未定义关键配合，也不得自行改变孔位/尺寸。\n\n请列出材料/装夹/孔边/沉孔/轮廓/变形风险、所需补充尺寸、公差和检验方法，报价分离材料、编程工装、加工、检验、运税与交期，并说明首件报告和不合格返修办法。任何不明确项请先标注，审批后再加工。联系人、数量、日期、价格留待真实确认。\n',encoding='utf-8')
    templates={
      'input_return':(['id','item','needed_before','gate','responsible_role','required','attachment_format','reply','attachment_paths','status'],[dict(zip(['id','item','needed_before','gate','responsible_role','required','attachment_format'],r),status='OPEN') for r in INPUTS]),
      'supplier_reply':(['family','revision','topic','supplier_response','drawing_revision','attachment','reviewer','review_date','disposition'],[dict(family=f,revision=('R4' if '-R4-' in f else 'R3'),topic=q,disposition='OPEN') for f in sorted(selected) for q in ['材料批次/工艺装夹','基准/孔边/沉孔/轮廓','关键公差/配合/平面度','去毛刺与接触表面','检验方法与报告','成套连接/锚固与未定义项']]),
      'quote_reply':(['family','revision','scope','supplier','quantity','unit_price_CNY','material_cost_CNY','setup_cost_CNY','inspection_cost_CNY','tax_CNY','freight_CNY','lead_days','quote_attachment','valid_until','approval'],[dict(family=f,revision=('R4' if '-R4-' in f else 'R3'),scope=('三类首件候选' if f in families else '左右/半径筛选候选评审图，未放行'),approval='OPEN') for f in sorted(selected)]),
      'instruments':(['instrument_id','purpose','make_model','range','resolution','unit','calibration_or_check_method','check_date','certificate_path','operator','status'],[]),
      'ball_measurements':(['ball_id','group_id','brand_model','speed_mark','lot','condition','date','operator','instrument_id','orientation','repeat_id','cork_diameter_mm','cork_height_mm','skirt_diameter_mm','overall_height_mm','mass_g','lean_observation','damage_baseline','raw_evidence'],[]),
      'stack_force':(['stack_id','ball_ids','group_id','count','repeat_id','stack_height_mm','increment_pitch_mm','separation_force_N','force_direction','displacement_mm','method','instrument_id','operator','date','jam_observation','raw_evidence'],[]),
      'inspection':(['part_serial','family','drawing_revision_hash','material_lot','feature','nominal','unit','approved_tolerance','tolerance_source','method','instrument_id','actual','deviation','raw_evidence','inspector','date','result','ncr_id'],[]),
      'manual_checks':(['run_id','stage','axis','hardware_revision','pose','part_ids','check','actual_start','actual_end','unit','force_N','retention_observation','tool_id','raw_evidence','operator','reviewer','date','result'],[]),
      'io_review':(['signal','category','applicability','source_contract','physical_sensor_or_output','terminal','polarity','truth_definition','fault_detection','loss_of_power_behavior','approved_timing_tolerance','attachment','engineer','approval'],[]),
      'axis_parameters':(['axis','actuator_driver_model','drawing_revision','travel_min','travel_max','position_unit','speed','speed_unit','force_or_current_limit','limit_unit','arrival_tolerance','timeout_s','stop_distance_limit','stop_time_limit_s','holding_strategy','source_evidence','approver','date','status'],[dict(axis=a,status='OPEN') for a in ['upper','gate','guide','slide','clamp']]),
      'gate_signoff':(['stage','entry_evidence','test_plan_revision','parameter_sheet','acceptance_rule','actual_result','unresolved_ncr','mechanical_reviewer','electrical_reviewer','operator','date','decision'],[dict(stage=s,decision='BLOCKED') for s in ['P0_DFM','P1_ORDER','M0_ASSEMBLY','M1_EMPTY','M2_SINGLE','M3_STACK','E0_ENERGIZE','E1_EMPTY_FAULTS','E2_SINGLE_STACK','V0_FROZEN_CONFIRMATION']]),
      'cycle_log':(['request_id','run_id','stage','ball_ids','stack_id','group_id','jaw_family_left','jaw_family_right','hardware_revision','pose','settings_attachment','started_at','ended_at','primary_result','damage','intervention','force_N','displacement_mm','time_s','raw_video','video_timecode','operator','notes'],[]),
      'stop_tests':(['test_id','run_id','axis','load_pose','initial_speed','speed_unit','trigger_definition','trigger_timestamp','stop_timestamp','stop_time_s','start_position','stop_position','position_unit','stop_distance','clock_sync_method','measurement_uncertainty','approved_limit_source','raw_evidence','operator','engineer','result'],[]),
      'nonconformance':(['ncr_id','run_id','request_id','part_serial','description','raw_evidence','containment','impact','proposed_action','approved_revision','approver','retest_evidence','status'],[]),
      'evidence_index':(['record_id','run_id','ball_or_part_id','relative_path','bytes','sha256','source','captured_at','operator','hardware_revision','pose','supersedes_record','reason'],[]),
      'run_summary':(['run_id','stage','settings_hash','independent_ball_count','all_requests','valid_single','double','empty','jam','aborted','other','damaged_requests','intervention_requests','valid_single_rate','frozen_acceptance_source','reviewer','decision'],[])
    }
    # Import only the pure contract module; never create hardware outputs.
    from control.contracts import KNOWN
    outside={'wheels_ready','capture_detected','exit','aim_reached','head_home'}
    io=[dict(signal=s,category='observation_contract',applicability='NOT_RUN_NO_WHEELS_OR_HEAD' if s in outside else 'HARDWARE_MAPPING_OPEN',source_contract='control/contracts.py:KNOWN',approval='OPEN') for s in sorted(KNOWN)]
    for s in ['enable_motion','slide_target_mm','guide_target_mm','clamp_target','gate_target','upper_target','enable_wheels']:
        io.append(dict(signal=s,category='actuator_output_intent',applicability='NOT_APPLICABLE_NO_WHEELS' if s=='enable_wheels' else 'HARDWARE_MAPPING_OPEN',source_contract='control/feed_cycle.py:outputs',approval='OPEN'))
    for s in ['upper','gate','guide','slide','catch_clamp','future_wheels']:
        io.append(dict(signal='safe_intent.'+s,category='stop_hold_intent_NOT_implemented',applicability='NOT_APPLICABLE_NO_WHEELS' if s=='future_wheels' else 'HARDWARE_CAPABILITY_OPEN',source_contract='control/feed_cycle.py:outputs.safe_intent',approval='OPEN'))
    for s in ['command_id','cycle_id','action','target','issued_at','accepted_id','completed_id','actual_position','in_tolerance','sample_id']:
        io.append(dict(signal=s,category='protocol_field_NOT_terminal',applicability='ADAPTER_OPEN',source_contract='control/commands.py:Command/CommandLifecycle',approval='OPEN'))
    templates['io_review']=(templates['io_review'][0],io)
    for name,(fields,rows) in templates.items():write_csv(out/'templates'/(name+'.csv'),fields,rows)
    allrfq=list(csv.DictReader((R/'output/fixture_r4/first_article_RFQ.csv').open(encoding='utf-8-sig')))
    filtered=[r for r in allrfq if r['family'] in families]
    if {r['family'] for r in filtered}!=set(families):raise RuntimeError('Missing source RFQ family')
    write_csv(out/'FIRST_ARTICLE_RFQ_SOURCE.csv',list(filtered[0]),filtered)
    (out/'README.md').write_text('# BM1 R4 首件与低速准备包\n\n状态 PREPARATION_ONLY；未加工/未试验/未放行。先读 USER_INPUTS.md 和 WORKSHOP_CARDS.md；PDF 可现场打印，templates 为未填写记录。reference 是冻结R4的原文件，不可编辑。\n\n三类候选与左右/半径参考共10个部件STEP，另附总装STEP/索引/爆炸图；3张原首件图及7张新增夹块评审图。STEP 为毫米单位。现场填写请复制模板另存原始证据；build.py 只生成新目录。CSV 使用 UTF-8 BOM，字段单位写在表头；空表不是已完成试验。\n\n低速数值、扭矩、关键配合、采购量和成功率阈值均未新增。所有审批需真实责任人和附件，不能由生成器自动放行。I/O表包含观测、执行器意图、停止保持意图和协议字段；协议字段不是接线端子，缺失轮组/机头相关项目明确标记不适用或未运行。\n\n来源见 source_binding.json；包文件校验见 manifest.json；随包 build.py 与 jaw_drawings.py 必须放回完整项目 preparation/r4_first_article/ 后从项目运行。其 PDF/CSV/新增评审图只受本包独立验收，不属于历史 R4 数字验证范围。\n',encoding='utf-8')
    shutil.copyfile(Path(__file__),out/'build.py')
    shutil.copyfile(Path(__file__).with_name('jaw_drawings.py'),out/'jaw_drawings.py')
    from reportlab.pdfgen import canvas
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Image
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.colors import HexColor
    from reportlab.lib.utils import ImageReader
    font=Path('C:/Windows/Fonts/msyh.ttc');pdfmetrics.registerFont(TTFont('ZH',str(font)))
    body=ParagraphStyle('body',fontName='ZH',fontSize=10.5,leading=17,spaceAfter=13,wordWrap='CJK',textColor=HexColor('#253647'))
    title=ParagraphStyle('title',parent=body,fontSize=19,leading=26,spaceAfter=21,textColor=HexColor('#126c78'))
    story=[]
    for n,(head,paragraphs) in enumerate(CHAPTERS):
        if n:story.append(PageBreak())
        story.append(Paragraph(escape(head),title))
        for para in paragraphs:story.append(Paragraph(escape(para),body))
    for row in INPUTS:
        i,name,stage,gate,who,need,fmt=row
        if i in ('U01','U05','U09'):story.append(PageBreak());story.append(Paragraph('一次性资料清单 '+i+' 起',title))
        story.append(Paragraph(escape(i+' '+name+' | '+stage),body))
        story.append(Paragraph(escape('负责：'+who+'；'+need+' 附件：'+fmt),body))
    for family in families+sorted(additional):
        story.append(PageBreak());story.append(Paragraph(escape('首件候选图 / '+family),title))
        img=(out/'candidate_drawings'/f'{family}_review.png') if family in additional else (out/'reference/output/fixture_r4/drawings'/f'{family}_first_article.png')
        iw,ih=ImageReader(str(img)).getSize();story.append(Image(str(img),width=480,height=480*ih/iw))
        caption='由冻结 STEP 生成的新增评审图' if family in additional else '冻结原图副本'
        story.append(Spacer(1,12));story.append(Paragraph(caption+'，仅供工艺/尺寸评审。关键公差、真实接口及材料批次待确认；未放行加工。',body))
    def footer(c,doc):
        c.setFont('ZH',8);c.setFillColor(HexColor('#516572'));c.drawString(42,25,'BM1 R4 / PREPARATION_ONLY / 2026-10-27');c.drawRightString(553,25,str(doc.page))
        if doc.page<=10:
            for y,label in [(190,'现场补充记录 / 原始证据编号：'),(140,'责任人 / 日期：'),(90,'审核结论 / 待办：')]:
                c.drawString(48,y,label);c.setStrokeColor(HexColor('#ccd5da'));c.line(48,y-22,547,y-22)
    pdf=out/'BM1_R4_First_Article_Low_Speed_Preparation.pdf'
    SimpleDocTemplate(str(pdf),pagesize=(595.28,841.89),rightMargin=48,leftMargin=48,topMargin=46,bottomMargin=48).build(story,onFirstPage=footer,onLaterPages=footer)
    files=[p for p in out.rglob('*') if p.is_file()]
    manifest={'status':'PREPARATION_ONLY','files':[dict(path=p.relative_to(out).as_posix(),bytes=p.stat().st_size,sha256=h(p)) for p in sorted(files)]}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    with zipfile.ZipFile(zpath,'x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file():z.write(p,Path(out.name)/p.relative_to(out))
    with zipfile.ZipFile(zpath) as z:
        if z.testzip() is not None:raise RuntimeError('ZIP CRC failure')
        for row in manifest['files']:
            raw=z.read(out.name+'/'+row['path'])
            if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise RuntimeError('ZIP hash failure: '+row['path'])
    with zpath.with_suffix('.zip.sha256').open('x',encoding='utf-8') as f:f.write(h(zpath)+'  '+zpath.name+'\n')
    print(json.dumps(dict(output=str(out),files=len(manifest['files']),zip=str(zpath),zip_sha256=h(zpath)),ensure_ascii=False))

if __name__=='__main__':main()
