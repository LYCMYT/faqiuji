# R4 质量与支承数据录入

默认空记录保持 BLOCKED_MISSING_EVIDENCE。完整评价必须传入当前对象的 expected_instances 清单：整机来自本次物理实例清单，台架来自其自身清单；不要套用固定 187/155 数量。

每个 components 记录含唯一 instance_id、有限正 mass_kg、三个有限非布尔 com_world_mm、source 证据编号、非空 hardware_revision 和非空数值 pose（必须包含 height/yaw/pitch，以 mm/deg）。质心坐标必须是指定姿态的世界坐标。禁止以采购包络体积估算值充当已测质量。

evidence_index 需要 root、hardware_revision、pose 和 records 字典。records 按 source 编号索引，每条有 path、bytes、sha256、instance_id、hardware_revision、pose；文件必须实际存在且非空，大小和 SHA-256 匹配。修订和姿态必须与本次评价一致。source 和 verified 标签本身不构成证据；文件来源、测量器具、人员和原始数据的可信性仍需工程审核。

supports 每项填写 x_mm、y_mm 和真实来源的 vertical_stiffness_N_mm；缺刚度则只报告质量/质心，不解支反力。当前算法限定 3–12 个同平面单向线性竖向弹簧、刚性底盘、静态重力，枚举可重新接触的活动集并检查平衡、非负反力、非活动点不压入、弹簧关系与条件数。数值溢出或病态输入拒绝计算。

无真实证据的数学实验只能显式 allow_partial=True 或命令行 --allow-partial；输出 PARTIAL_UNVERIFIED_CALCULATION，实际质量/质心为空，仅提供 calculated_*。任何模式均不自动将 stability_pass 置为 true；实际冲击、地面倾斜、风、连接柔度、停止载荷与抗倾覆仍需另外分析及实测。

最小结构示例（仅说明格式；不是实测数据，实际数值及散列必须来自文件）：

```json
{
  "expected_instances": ["实际实例编号"],
  "components": [{"instance_id":"实际实例编号","mass_kg":null,"com_world_mm":null,"source":"记录编号","hardware_revision":"实际修订","pose":{"height":0,"yaw":0,"pitch":0}}],
  "evidence_index": {"root":"证据所在目录","hardware_revision":"实际修订","pose":{"height":0,"yaw":0,"pitch":0},"records":{"记录编号":{"path":"原始记录.csv","bytes":null,"sha256":null,"instance_id":"实际实例编号","hardware_revision":"实际修订","pose":{"height":0,"yaw":0,"pitch":0}}}},
  "supports": []
}
```

示例的 0 姿态仅表示台架局部零位写法；必须换成本次真实姿态。null 和空 supports 会阻断计算，不可为了通过门禁随意填数字。
