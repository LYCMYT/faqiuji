# BM1 R4 实际检查与剩余输入

构建 4ba7c7d18a63449c8b34bc7e64190085；Git f8939e9df17eb2115a17d98e8b904e4879a6f74e。输入 9f27b70c17e373d812b0c6671ea67f0db1d84699076a082c0bf026564397d1b3；源码 b707320283dd906a50ba53de4b25e6ad440d5a9927de7544dadc55a1f2fc4472。

实际运行：83 项单元测试，失败 0、错误 0；8 类故意失败注入通过。R4 几何状态 BLOCKED；逐件 STEP、BLEND/GLB、中文 PDF（69 页）、动画完整解码、本地查看器交互分别经过本次检查。详情为 reports/builds/4ba7c7d18a63449c8b34bc7e64190085/ 的日志和来源报告。

机械门禁 BLOCKED：当前包仅供评审，完整发布门禁未通过。连接、保持和工具操作的具体失败/开放项逐条见 r4_geometry_validation.json；不得把导出和图页通过理解为机械通过。

{
  "connections": [
    {
      "axis_id": "upper",
      "endpoints": [
        {
          "value_mm": 0,
          "distance_mm": 0.0,
          "overlap_mm3": 0.0
        },
        {
          "value_mm": 24,
          "distance_mm": 0.0,
          "overlap_mm3": 0.0
        }
      ],
      "status": "PASS",
      "retention_and_stop_acceptance": {
        "axis": "upper",
        "value_mm": 0,
        "status": "PASS",
        "checks": [
          {
            "check": "L:shaft_engaged",
            "material_fraction": 0.903046792447475,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "L:bush_retaining_material",
            "material_fraction": 0.9766322069160429,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "L:shaft_engaged",
            "material_fraction": 1.0,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "L:bush_retaining_material",
            "material_fraction": 1.0000000000000027,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "R:shaft_engaged",
            "material_fraction": 0.9030467921940329,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "R:bush_retaining_material",
            "material_fraction": 0.976632206873996,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "R:shaft_engaged",
            "material_fraction": 1.0,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "R:bush_retaining_material",
            "material_fraction": 1.0000000000000027,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "within_nominal_stops",
            "value_mm": 0,
            "limits_mm": [
              0,
              24
            ],
            "status": "PASS"
          },
          {
            "check": "hard_stop_blocks_overtravel",
            "moving": "PRT-0603-R3-CARRIER-L",
            "endpoint_mm": 0,
            "probe_mm": -0.5,
            "blocked_volume_mm3": 13.069025438933611,
            "status": "PASS"
          },
          {
            "check": "hard_stop_blocks_overtravel",
            "moving": "PRT-0603-R3-CARRIER-R",
            "endpoint_mm": 0,
            "probe_mm": -0.5,
            "blocked_volume_mm3": 13.0690254389336,
            "status": "PASS"
          },
          {
            "check": "hard_stop_blocks_overtravel",
            "moving": "PRT-0603-R3-CARRIER-L",
            "endpoint_mm": 24,
            "probe_mm": 0.5,
            "blocked_volume_mm3": 13.069025438933611,
            "status": "PASS"
          },
          {
            "check": "hard_stop_blocks_overtravel",
            "moving": "PRT-0603-R3-CARRIER-R",
            "endpoint_mm": 24,
            "probe_mm": 0.5,
            "blocked_volume_mm3": 13.0690254389336,
            "status": "PASS"
          }
        ],
        "load_and_material_rating": "OPEN"
      },
      "reason": "Paired integral Y shafts in two bored bushes constrain lateral/vertical and rotation; collars bound24mm",
      "reaction_path": {
        "status": "NATIVE_CANDIDATE_LOAD_OPEN",
        "candidate": "carrier -> paired shafts -> bush -> integral bridge -> side410 bracket -> uprights -> base"
      }
    },
    {
      "axis_id": "gate",
      "endpoints": [
        {
          "value_mm": 0,
          "distance_mm": 0.0,
          "overlap_mm3": 0.0
        },
        {
          "value_mm": 85,
          "distance_mm": 0.0,
          "overlap_mm3": 0.0
        }
      ],
      "status": "PASS",
      "retention_and_stop_acceptance": {
        "axis": "gate",
        "value_mm": 0,
        "status": "PASS",
        "checks": [
          {
            "check": "-1:shaft_engaged",
            "material_fraction": 1.0,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "-1:bush_retaining_material",
            "material_fraction": 0.9452259253727894,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "1:shaft_engaged",
            "material_fraction": 0.9030471471239733,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "1:bush_retaining_material",
            "material_fraction": 0.921857943831803,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "within_nominal_stops",
            "value_mm": 0,
            "limits_mm": [
              0,
              85
            ],
            "status": "PASS"
          },
          {
            "check": "hard_stop_blocks_overtravel",
            "moving": "PRT-0604",
            "endpoint_mm": 0,
            "probe_mm": -0.5,
            "blocked_volume_mm3": 9.80176907920017,
            "status": "PASS"
          },
          {
            "check": "hard_stop_blocks_overtravel",
            "moving": "PRT-0604",
            "endpoint_mm": 0,
            "probe_mm": -0.5,
            "blocked_volume_mm3": 9.801769079200163,
            "status": "PASS"
          },
          {
            "check": "hard_stop_blocks_overtravel",
            "moving": "PRT-0604",
            "endpoint_mm": 85,
            "probe_mm": 0.5,
            "blocked_volume_mm3": 26.91913022755319,
            "status": "PASS"
          },
          {
            "check": "hard_stop_blocks_overtravel",
            "moving": "PRT-0604",
            "endpoint_mm": 85,
            "probe_mm": 0.5,
            "blocked_volume_mm3": 26.919130227553186,
            "status": "PASS"
          }
        ],
        "load_and_material_rating": "OPEN"
      },
      "reason": "Paired X shafts at y±60 in wall-supported outboard bushes; collars bound85mm; rear ribs remain inside original tube slot",
      "reaction_path": {
        "status": "NATIVE_CANDIDATE_LOAD_OPEN",
        "candidate": "gate -> rear ribs/ears -> paired shafts -> bushes -> reaction bridge -> rear wall -> frame -> base"
      }
    },
    {
      "axis_id": "guide",
      "endpoints": [
        {
          "value_mm": 0,
          "distance_mm": 0.0,
          "overlap_mm3": 0.0
        },
        {
          "value_mm": 115,
          "distance_mm": 0.19999999999998863,
          "overlap_mm3": 0.0
        }
      ],
      "status": "PASS",
      "retention_and_stop_acceptance": {
        "axis": "guide",
        "value_mm": 0,
        "status": "PASS",
        "checks": [
          {
            "check": "tongue_axial_engagement",
            "engaged_mm": 30.0,
            "total_mm": 30.0,
            "status": "PASS"
          },
          {
            "check": "tongue_present",
            "material_fraction": 1.0,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "-1:front_lip_retains_tongue",
            "material_fraction": 1.0,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "1:front_lip_retains_tongue",
            "material_fraction": 1.0,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "back_web_present",
            "material_fraction": 1.0,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "within_nominal_stops",
            "value_mm": 0,
            "limits_mm": [
              0,
              115
            ],
            "status": "PASS"
          },
          {
            "check": "hard_stop_blocks_overtravel",
            "moving": "PRT-0607-B",
            "endpoint_mm": 0,
            "probe_mm": -0.5,
            "blocked_volume_mm3": 42.0,
            "status": "PASS"
          },
          {
            "check": "hard_stop_blocks_overtravel",
            "moving": "PRT-0607-B",
            "endpoint_mm": 115,
            "probe_mm": 0.5,
            "blocked_volume_mm3": 42.0,
            "status": "PASS"
          }
        ],
        "load_and_material_rating": "OPEN"
      },
      "reason": "Rectangular captive Z tongue with front lips, back web and sidewalls; stops113/258 bound115mm",
      "reaction_path": {
        "status": "NATIVE_CANDIDATE_LOAD_OPEN",
        "candidate": "sleeve -> revised neck -> existing tongue -> custom captive way -> bracket at z271 -> rear frame -> base"
      }
    },
    {
      "axis_id": "slide",
      "endpoints": [
        {
          "value_mm": 0,
          "distance_mm": 0.0,
          "overlap_mm3": 0.0
        },
        {
          "value_mm": 185,
          "distance_mm": 0.0,
          "overlap_mm3": 0.0
        }
      ],
      "status": "PASS",
      "retention_and_stop_acceptance": {
        "axis": "slide",
        "value_mm": 0,
        "status": "PASS",
        "checks": [
          {
            "check": "-1:flange_engaged",
            "material_fraction": 1.0,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "-1:channel_upper_lip",
            "material_fraction": 1.0,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "-1:channel_lower_lip",
            "material_fraction": 1.0,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "1:flange_engaged",
            "material_fraction": 1.0,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "1:channel_upper_lip",
            "material_fraction": 1.0,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "1:channel_lower_lip",
            "material_fraction": 1.0,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "within_nominal_stops",
            "value_mm": 0,
            "limits_mm": [
              0,
              185
            ],
            "status": "PASS"
          },
          {
            "check": "hard_stop_blocks_overtravel",
            "moving": "PRT-0703-C",
            "endpoint_mm": 0,
            "probe_mm": -0.5,
            "blocked_volume_mm3": 23.599999999999998,
            "status": "PASS"
          },
          {
            "check": "hard_stop_blocks_overtravel",
            "moving": "PRT-0703-C",
            "endpoint_mm": 185,
            "probe_mm": 0.5,
            "blocked_volume_mm3": 23.4766419469047,
            "status": "PASS"
          }
        ],
        "load_and_material_rating": "OPEN"
      },
      "reason": "Paired integral side flanges in captive C-ways; rear/front stops bound185mm",
      "reaction_path": {
        "status": "NATIVE_CANDIDATE_LOAD_OPEN",
        "candidate": "cradle -> carriage -> captive flanges -> rail -> revised shoes/posts -> base"
      }
    },
    {
      "axis_id": "clamp",
      "endpoints": [
        {
          "value_mm": 0,
          "distance_mm": 0.0,
          "overlap_mm3": 0.0
        },
        {
          "value_mm": 14,
          "distance_mm": 0.0,
          "overlap_mm3": 0.0
        }
      ],
      "status": "PASS",
      "retention_and_stop_acceptance": {
        "axis": "clamp",
        "value_mm": 14,
        "status": "PASS",
        "checks": [
          {
            "check": "L:arm_engaged_in_portal",
            "material_fraction": 1.0,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "L:lower_lip",
            "material_fraction": 1.0,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "L:upper_lip",
            "material_fraction": 1.0,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "L:rear_wall",
            "material_fraction": 1.0,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "R:arm_engaged_in_portal",
            "material_fraction": 1.0,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "R:lower_lip",
            "material_fraction": 1.0,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "R:upper_lip",
            "material_fraction": 1.0,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "R:rear_wall",
            "material_fraction": 1.0,
            "minimum_fraction": 0.6,
            "status": "PASS"
          },
          {
            "check": "within_nominal_stops",
            "value_mm": 14,
            "limits_mm": [
              0,
              14
            ],
            "status": "PASS"
          },
          {
            "check": "hard_stop_blocks_overtravel",
            "moving": "PRT-0702-A__L",
            "endpoint_mm": 0,
            "probe_mm": -0.5,
            "blocked_volume_mm3": 3.7882367343226435,
            "status": "PASS"
          },
          {
            "check": "hard_stop_blocks_overtravel",
            "moving": "PRT-0702-A__R",
            "endpoint_mm": 0,
            "probe_mm": -0.5,
            "blocked_volume_mm3": 3.7882367343226426,
            "status": "PASS"
          },
          {
            "check": "hard_stop_blocks_overtravel",
            "moving": "PRT-0702-A__L",
            "endpoint_mm": 14,
            "probe_mm": 0.5,
            "blocked_volume_mm3": 3.7882367343226444,
            "status": "PASS"
          },
          {
            "check": "hard_stop_blocks_overtravel",
            "moving": "PRT-0702-A__R",
            "endpoint_mm": 14,
            "probe_mm": 0.5,
            "blocked_volume_mm3": 3.7882367343226453,
            "status": "PASS"
          }
        ],
        "load_and_material_rating": "OPEN"
      },
      "reason": "Rear channel back/top/bottom constrain arm; fixed stepped pin in14mm slot constrains forward X and nominal Y travel; running clearance0.2mm",
      "reaction_path": {
        "status": "NATIVE_CANDIDATE_LOAD_OPEN",
        "candidate": "finger -> arm -> slot/pin and channel -> symmetric crossbeam -> cradle -> carriage -> rail -> base"
      }
    }
  ],
  "tool_status": "PASS_SPECIFIED_ENVELOPES",
  "tool_intersections": [],
  "assumptions": [
    "R3 local height=0, no wheel solids in fixture; no full-machine wheel clearance claim",
    "No ball attached to animation parent during perturbation",
    "Five native captive guide candidates examined; holding, cap assembly, weld/fastener and strength remain OPEN",
    "Upper M4 service, ordered cap/fastener removal and declared candidate M3/M2 tool envelopes checked separately; actual tools/human handling remain OPEN"
  ]
}

数字通过只限报告中的离散状态、名义接触和工具包络；不是连续扫掠、刚度、预紧、公差叠加或实物性能证明。

无历史 output/reports 的隔离重建：PASS，源提交 45cdb8e，10 个核心阶段；范围为 R1–R3 核心工程。R4 当前实体与展示由本次构建单独检查。详见 reports/r4_cold_core_validation.json。

未运行：真实供应商接口核验、球样测量、夹力/轮速/停止距离、报价、加工、低速硬件循环、高速发射、落点标定及安全等级验证。人工签核 NOT_RUN，不能由自动渲染继承。保留的 R1–R3 历史动画/图册没有在本次 R4 构建中全部重渲染，不作为本次 R4 检查证明。

首件和低速试验需要：

- R3-O01 [OPEN]：upper guide mounting, travel/retention, manual force measurement; motor adapter only after original supplier drawing
- R3-O02 [OPEN]：actual slide model, drawing revision, allowed clamp zone, stroke, block envelope, load and moment limits
- R3-O03 [OPEN]：material lots, fastener grade, load/preload analysis, torque method, POM compression and recheck record
- R3-O04 [OPEN]：table material/thickness/support spacing, underside access, anchor/backplate assembly and rigidity record
- R3-O05 [OPEN]：five-function mechanism review, stops/retention, fixture assembly and operating envelope inspection
- BALL-SAMPLES [BLOCKED]：received batch/speed mark/count, individual ball ID, cork/skirt dimensions, mass, stacking pitch, separation force, damage baseline
- ELECTRICAL [BLOCKED]：actual actuators/drivers, I/O truth table, holding on loss of power, independent stop chain, measured stop travel/time
- WHEELS [BLOCKED]：real wheel/shaft/hub drawings and ratings, verified speed feedback, guarded test fixture; no wheel speed limit inferred
- PROCUREMENT [OPEN]：reviewed drawing revision and material/tolerances, supplier quote, lead time/tax/freight, first article report and rework terms

整机 manufacturing_release=false；首件和自动运行尚未放行。具体顺序见 docs/test_protocol_r4.md；数字候选交付不关闭任何实物开放项。
