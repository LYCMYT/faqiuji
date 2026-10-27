# R4 当前工作入口

R4 基于 c8c52514a80f52c364950852ed2fde2a1d926e62 的独立审查实施。保留 R1–R3 历史来源与44主项编号；R4修订台架见 `output/fixture_r4/index.html`，实际状态见 `reports/r4_readiness.md`。已有 R1–R3 报告不自动成为 R4 的通过证明。

完整数字候选构建：`python tools/rebuild.py`。Windows 设置 `BM1_BLENDER_EXE` 为实际 Blender 可执行文件路径；`python tools/doctor.py` 检查当前工具和中文字体。需要时用 `BM1_CHINESE_FONT` 指定字体。核心原环境复核单独运行 `python tools/rebuild.py --legacy --scope core`；它不发布 R4。

若机械服务/保持路径仍 BLOCKED，只有显式 `python tools/rebuild.py --review-draft` 才能继续制作**评审专用**文件；它保持几何 BLOCKED 和完整发布门禁 BLOCKED，不会生成通过的发布证明。该模式也拒绝名义实体无效、接球支撑失效或未解决的全装配体积相交。

通过的完整候选用 `python tools/package_delivery.py --release-proof reports/release_proof.json` 打包。评审专用候选另用 `--review-proof reports/r4_review_bundle.json`，ZIP名称明确包含 `Review_Candidate_BLOCKED`。两种门禁和产物散列分别检查，不能把评审包当作通过包。构建及打包均不授权制造、采购或硬件运行。

权威 `data/`、原始 `input/` 与 `evidence/` 构建前后必须字节不变；派生结果写 `output/`。旧实例和页面快照是只读兼容输入，新元数据在 `output/generated_metadata/`。供应商图、球样、夹力、轮速、报价、停止与低速试验没有真实记录时继续 OPEN/BLOCKED。首件输入、测量协议见 `data/r4_release_scope.json`、`docs/test_protocol_r4.md`；离线控制与质量证据格式见 `docs/control_contract_r4.md`、`docs/engineering_evidence_r4.md`。

当前查看器：双击 `启动查看器.cmd`，或运行 `python tools/serve_viewer.py --open --revision R4`；入口为 `/output/fixture_r4/viewer.html`。

---

以下是审查基准提交 c8c52514 的历史 R1–R3 交付说明。历史打包命令、统计和“最新”称谓仅适用于当时版本；当前命令和状态以上方 R4 入口及当前报告为准。

# BM1 V0.2 R1 总装 + R2 球样 + R3 连接细化交付

最新R3入口：`output/fixture_r3/index.html`；三维查看器：`output/fixture_r3/viewer.html`；43页中文连接图集：`output/fixture_r3/BM1_R3_connection_drawing_book.pdf`。新增155实例低速台架变体、71份STEP、21份顶面DXF及零件图、53行孔表、BLEND/GLB和分解动画。R1整机和R2准备资料继续保留。

R3已补基板、压板、支柱、支脚和夹块穿透连接。上夹驱动适配及导向、实际滑台接口、原供球组件其余连接、紧固载荷和台面锚固仍开放，不能直接接电运行或将整机视为制造批准。详见`reports/r3_acceptance_report.md`。

只重建R3：依次运行`tools/check_r3_geometry.py`、`tools/build_r3_package.py`，用Blender后台运行`blender/build_r3_scene.py`，再运行`tools/build_r3_manual.py`、`tools/finish_r3_delivery.py`及`tools/check_r3_viewer.py`。均使用本工程Python环境；全部尺寸来自data目录。打包最新交付：`.venv/Scripts/python.exe tools/package_delivery.py --revision R3`。

R2新增入口：`output/prototype_r2/index.html`；中文说明及8件试配毛件图页：`output/prototype_r2/BM1_R2_sample_manufacturing_manual.pdf`。
已选择AS-30 36只、AS-10 24只、MAVIS350 12只作为首轮计划样本，生成44主项加工路线及8个POM-C毛件STEP/DXF。所有实测、采购、收货、加工和试验记录仍为空。R2尚未冻结夹块安装与台架紧固接口，整机制造未放行。

只重建R2：`.venv/Scripts/python.exe tools/build_r2_prototype.py`，随后运行`.venv/Scripts/python.exe tools/check_r2_prototype.py`。完整重建也包含R2。打包最新完整交付：`.venv/Scripts/python.exe tools/package_delivery.py --revision R2`。实际测量请另存副本，不要填入会被重建覆盖的PLAN/BLANK文件。

本目录为本次实际生成的参数实体、交换模型、展示文件和模型图册。原设计包保留在 `input/`；不是将原示意图改名交付。

先双击 **启动查看器.cmd**。浏览器访问 `http://127.0.0.1:8765/viewer/`。页面提供44主项/10模块选择、隔离、罩壳开关、爆炸滑块、预设镜头及独立介绍页。全部网页依赖已本地化。不要用 `file://` 打开。

主要交付：

- `output/step/BM1_V0_assembly.step`：未融合的总装，mm。
- `output/step/parts/`：44主项与派生件。主项文件包含其所有子件，统一默认装配坐标；派生文件用于进一步拆分。
- `output/step/assemblies/`：10个功能子总成；功能分组不代表运动父级。
- `output/step/BM1_Y0_section.step`：真实布尔剖切。
- `output/blend/BM1_V0_master.blend`：装配/供球、爆炸和供球组件维护三个场景；m、Z-up，含关节空节点、材质、镜头和可编辑动作。
- `output/glb/BM1_V0_assembly.glb`：187个可独立查看的物理实例网格，m、Y-up。
- `output/BM1_V0_design_book.pdf` 与 `output/drawings/`：中文模型图册、SVG投影、PNG、独立HTML页。
- `output/animation/BM1_feed_sequence.mp4`：顺序演示停在捕获边界，后续动态待实测。
- `output/animation/BM1_explode_restore.mp4`：爆炸/复原。
- `output/animation/BM1_R1_cassette_service.mp4`：双销退出与完整供球器后抽；对应BLEND第三场景。
- `output/engineering/index.html`：R1修订与试验工作包，含手册PDF、低速验证台STEP、4组弧面试件、测量/采购/试验空表、概念功能接线SVG和质量计算入口。
- `output/BOM.csv`：原主项数量和建模实例数分别列出。传感器族采购数量保持未定。
- `reports/acceptance_report.html` / `.md`、`validation.json`：验收结果与边界。请先阅读，不把导出成功当作制造批准。
- `output/verification_variants/`：轮距与筒帽参数分别变更后的完整总装 STEP、对应输入数据；验证后已恢复基准。`reports/parameter_full_rebuild.json` 记录实际重建结果。

## 重建

本机已经安装项目独立环境，直接运行 **重建模型.cmd**。它只读取当前 `data/`，不会执行最初创建/修正数据的脚本。

在另一台Windows电脑上：安装Python 3.12，创建 `.venv`，用 `requirements-lock.txt` 安装依赖；准备Blender 4.5.9 LTS、FFmpeg及Chrome（自动查看器检查使用）。将 `BM1_BLENDER_EXE` 设置为Blender程序的绝对路径，或把Blender加入PATH，然后运行重建脚本。核心版本为Python 3.12.10、CadQuery 2.8.0、OCCT 7.9.3.1、Blender 4.5.9 LTS。环境与大型工具程序不放入便携交付ZIP。

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
$env:BM1_BLENDER_EXE = 'C:/path/to/blender.exe'
.\.venv\Scripts\python.exe tools/rebuild.py
```

参数入口为 `data/design.json`，补充形状与接口细节在 `data/geometry.json`。表达式可引用基础参数和原主项包络（如 `P0504_x`）。工程生成器为 `cad/parts/recipe.py`，使用原生OpenCascade盒、圆柱、环、布尔和扫掠实体；没有网格包装STEP。运动树在 `cad/assemblies/kinematics.py`。动画关键帧在 `data/animation_keyframes.json`，演示速度与真实额定值分开。

`tools/seed_engineering_data.py`、`refine_*.py` 和 `extract_animation_data.py` 是此次实施历史记录，不是日常重建入口；重复运行可能重置或重复修正当前数据。

## 必须保留的边界

全部新增结构、孔、槽、材料与接口仍属concept。采购型号、供应商孔型、配合、公差、转速上限、电气额定值、实际容量、单球率、落点标定和安全等级未冻结；实测档案仍为空。

R1带球前推停于首次理想接触边界，取消原版继续前推引起的参考球相交；X=-5仅允许空滑台检查。冻结参考球不属于托架，保守撤回路径已查；实际捕获动力学仍未验证。视频停在接触边界，ST10须真实新出球脉冲后才允许复位。

R1采用完整供球组件后抽：导套和分球器保留在组件内。空筒、最低轴高、隔离能源、托车承重并断线后，两销向外退出55mm，组件后抽350mm；路径通过不等于销锁承重和真实快拆操作合格。滑台回线解析恒长357.272121mm、中心线半径21.5mm，实际电缆允许值和耐久未确认；升降与旋转轴完整线束仍待完善。分球夹为可更换弧面试件，实际球堆接口与可靠性仍需实测。

`control/feed_cycle.py`是无硬件连接的离线合同模拟器，不是可直接驱动设备的固件。`engineering/evaluate.py`在质量/质心缺失时明确返回BLOCKED，不用采购包络冒充质量。复制BLANK模板后重命名再填实测记录；勿将唯一实测数据保存在重建模板中。

上一版交付ZIP保留；R1完整包名为`BM1_V02_R1_Engineering_Delivery.zip`。`tools/revise_r1_data.py`只供本次修订历史审计，依赖本机保留的R0快照，不在日常重建中执行。日常重建只使用当前data/。

STL仅提供低速试装用途；不提供高速轮直接打印使用版本。
