# BM1 R4 首件与低速准备包

状态 PREPARATION_ONLY；未加工/未试验/未放行。先读 USER_INPUTS.md 和 WORKSHOP_CARDS.md；PDF 可现场打印，templates 为未填写记录。reference 是冻结R4的原文件，不可编辑。

三类候选与左右/半径参考共10个部件STEP，另附总装STEP/索引/爆炸图；3张原首件图及7张新增夹块评审图。STEP 为毫米单位。现场填写请复制模板另存原始证据；build.py 只生成新目录。CSV 使用 UTF-8 BOM，字段单位写在表头；空表不是已完成试验。

低速数值、扭矩、关键配合、采购量和成功率阈值均未新增。所有审批需真实责任人和附件，不能由生成器自动放行。I/O表包含观测、执行器意图、停止保持意图和协议字段；协议字段不是接线端子，缺失轮组/机头相关项目明确标记不适用或未运行。

来源见 source_binding.json；包文件校验见 manifest.json；随包 build.py 与 jaw_drawings.py 必须放回完整项目 preparation/r4_first_article/ 后从项目运行。其 PDF/CSV/新增评审图只受本包独立验收，不属于历史 R4 数字验证范围。
