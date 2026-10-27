# 审查证据索引

对应仓库 `LYCMYT/faqiuji`，提交 `c8c52514a80f52c364950852ed2fde2a1d926e62`。本目录保存审查结果和诊断脚本；**不是产品补丁，也不是实物验收记录**。

| 文件 | 方法与结果含义 |
|---|---|
| audit_scope.json | 审查环境、范围和远端提交复查 |
| manifest_check.json | 对仓库清单中的 1,806 项文件复算大小与 SHA-256 |
| existing_tests.log | 现有 18 项单元测试的实际输出 |
| export_reopen_audit.json | 80 份 STEP、29 份 DXF 和 4 本 PDF 的指定回读检查 |
| r3_geometry_full_rerun.json | 在隔离副本执行原 R3 检查器：235 个状态、793 次精确配对计算 |
| r3_geometry_static_rerun.json | 原 R3 检查器的 static 模式：1 个状态、179 次精确配对计算；用于验证同名报告覆盖问题 |
| support_evidence.json | 155 个台架实例下的名义球头接触、小角度扰动；未包含真实质量/摩擦/冲击 |
| reproduce_support_findings.py | 可在指定仓库重新执行接球诊断；固定审查边缘参数不适用于任意新设计 |
| control_findings.json | 7 组离线控制、运动输入和测试判据问题的采样轨迹；reproduced=true 表示问题存在 |
| reproduce_control_findings.py | 使用 --repo 指定仓库，结果必须写到该仓库之外 |
| mass_solver_counterexample.json | 质量证据输入缺口，以及五支点算法的独立枚举反例；不是默认四脚整机试验 |
| input_dependency_probe.json | 内存改变设计轮距后实体变化，但原单文件几何哈希判断仍匹配 |
| source_rewrite_probe.json | 临时副本中加入标记，再运行原 enrich_metadata，确认输入会被默认值覆盖 |
| gate_predicate_probes.json | 执行源码原 AST 门禁表达式；不等同完整 Blender/发布流程运行 |
| standalone_collision_failure_probe.json | 临时两立方体碰撞场景；单独检查器退出行为的证据。完整 R1 重建另有后续碰撞兜底 |

证据 JSON 中的绝对路径保留了原执行位置，下载后通过本表同名文件定位，不要求重建那些临时路径。`control_findings.json` 分发副本仅省略与结论无关的本地未跟踪文件列表；全部问题轨迹和已跟踪文件未改证据保留。两个诊断脚本已改为要求显式 `--repo`，便于在其他机器复核。

## 复核命令

在项目依赖环境中，从本包根目录执行：

```bash
python evidence/reproduce_support_findings.py --repo /absolute/path/to/faqiuji --output /tmp/bm1-support-results.json
python evidence/reproduce_control_findings.py --repo /absolute/path/to/faqiuji --output /tmp/bm1-control-results.json --mass-output /tmp/bm1-mass-results.json
```

更新后的提交应生成新结果；若问题已经修复，旧缺陷不再复现是正确结果。不能把本包的旧 PASS 或问题结果自动套用到新提交。

本轮运行环境与仓库声明的完整 Windows 环境不同。特别是 Blender/Chrome 完整构建、实物测量、实际停止时间和发球落点均未在本轮执行。
