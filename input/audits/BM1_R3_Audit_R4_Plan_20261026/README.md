# BM1 R3 项目审查与下一阶段执行包

日期：2026-10-26（Asia/Shanghai）。

审查仓库：https://github.com/LYCMYT/faqiuji

审查基准：`main` / `c8c52514a80f52c364950852ed2fde2a1d926e62`，发布标签 `v0.2-r3`。

本包是独立审查与执行规划，不是产品代码修复，也不包含重新复制的 Git 仓库。原仓库已跟踪文件保持未改。本轮没有采购、加工、接入设备或做实物试验。

## 建议阅读顺序

1. [AUDIT_REPORT.md](AUDIT_REPORT.md)：当前完成度、独立验证结果、新发现、已知未决问题及研发路线。
2. [2026-10-26-bm1-r4-plan.md](docs/superpowers/plans/2026-10-26-bm1-r4-plan.md)：下一轮可交给 Codex 的分任务实施计划，含依赖、文件、接口和验收条件。
3. [CODEX_NEXT_PROMPT.md](CODEX_NEXT_PROMPT.md)：可直接复制的下一条指令。
4. [evidence/README.md](evidence/README.md)：本次验证与反例的结果；[cradle_support_review.png](figures/cradle_support_review.png) 解释接球支撑问题。

**下一版本目标：保留现有 R1–R3 成果，先修正数据、构建与控制合同，完成可审查的低速供球台架机械闭环；随后取得真实球样与接口证据。高速发射与语音分阶段继续。**

## 证据的含义

- `r3_geometry_full_rerun.json`：在独立副本复跑原 R3 检查器，235 个指定状态通过；只对应报告声明的离散检查范围。
- `r3_geometry_static_rerun.json`：原检查器 `--static` 的单点 PASS；用于证明静态结果能够覆盖完整结果文件这一门禁缺口。
- `export_reopen_audit.json`：80 份 STEP 回读、29 份 DXF 闭合轮廓回读及4本PDF页数检查。不是全量重新建模，也不是制造图审核。
- `manifest_check.json`：1,806 项交付清单大小与 SHA-256 全部匹配。
- `control_findings.json`：7组控制/测试问题的复现结果。`reproduced=true` 表示问题被复现，不是问题已经修复。
- `existing_tests.log`：原有18项测试通过的实际输出。
- `support_evidence.json`：名义接球几何的接触与小角度扰动探针；不能替代真实球受力和落球试验。
- 其余 JSON：来源指纹、门禁谓词、输入覆写、质量与支承算法反例。

本机使用 CadQuery 2.7.0 / OCCT 7.8.1.1.post1，仓库记录的是 CadQuery 2.8.0 / OCCT 7.9.3.1。没有在本机完整重跑仓库声明的 Windows + Blender + Chrome 构建链。环境差异已在报告中保留。

## 复核控制问题

用包含 NumPy、CadQuery 的项目环境运行：

```bash
python evidence/reproduce_control_findings.py --repo /absolute/path/to/faqiuji --output /tmp/bm1-control-results.json --mass-output /tmp/bm1-mass-results.json
```

该脚本只读取项目并把结果写到仓库外。对更新后的提交运行时，旧问题可能不再复现，这是预期；不能把本包旧结果自动当作新版本的验收结论。

接球探针 `evidence/reproduce_support_findings.py` 同样是审查脚本，使用方法见文件头。它不是产品 CAD 生成器。
