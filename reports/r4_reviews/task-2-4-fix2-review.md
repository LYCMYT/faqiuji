# Tasks 2–4 fix2 re-review

Scope: commit 45cdb8e, task-2-4-fix2.diff, updated implementation report and the four fix1 findings. Read-only source review; no tests rerun, implementation changes, subagents or commits. Mechanical/model correctness remains outside this review.

Verdict: **PASS for this scoped fix review**. All four fix1 findings are addressed in the reviewed integration. This is not final end-to-end acceptance; the frozen-source full build and real same-run negative/render acceptance remain pending.

## Four findings disposition

1. **Transitive artifact integrity — addressed.** run_stage validates producer artifact hashes and merges them into its immutable stage wrapper. Release and review validation verify those wrappers against current files and require delivery artifacts to have a validated producer; source data/docs remain bound by the source fingerprint. The added r4_metadata wrapper binds the generated readiness, index and RFQ outputs. The supplied regression exercises replacement of a producer PDF after its successful stage and subsequent rejection.

2. **R4 result schemas — addressed for the reviewed cases.** R4 validation now requires actual reopen/render/media/viewer booleans, positive typed result counts, empty applicable defect arrays and stage-specific required artifact keys. STEP results must match the expected file set and provide valid solid counts, finite volumes, agreement with source volumes and hashes. A PASS status plus completed-check strings no longer suffices for the previously identified missing/False reopen cases. The supplied tests cover missing/False/string reopen fields and incomplete artifacts. Geometry algorithm/acceptance correctness is separately reviewed, not inferred here.

3. **Selected executable identity — addressed in the production R4 path.** Doctor-selected Blender/ffmpeg/ffprobe/Chrome paths are exported before BuildContext creation and inherited by child stages, aligning portable-tool selection, recorded identity and execution. The browser uses executable_path when BM1_CHROME_EXE is set. Actual portable-tool and browser execution remains part of the pending full acceptance run; this review does not claim it ran.

4. **Direct encoder frame provenance — addressed.** Blender records the exact rendered-frame hash set and distinguishes export_only from full render scope. The encoder requires same-run r4_blender provenance, the frames_rendered check and flag, an exact expected frame set, and matching frame bytes before encoding. Its new PASS report explicitly records video_fully_decoded. The supplied regression covers changed-frame and old-run rejection.

## Minor observation

The unrelated scene-name edit in blender/build_r4_scene.py changes readable `R4装配与连接件分解` to mojibake (`R4瑁呴厤涓庤繛鎺ヤ欢鍒嗚В`). Restore the readable label when convenient; this does not undermine the four gate/provenance fixes and is not a blocker for this scoped verdict.

## Evidence and remaining acceptance

The updated report supplies six targeted release-gate tests PASS. They were inspected as supplied evidence, not independently rerun. No new important integration defect was identified in this fix diff. Complete the already planned frozen-source pipeline and real same-run fault/render checks before claiming final task 2–4 acceptance or a full release. REVIEW_ONLY/BLOCKED remains distinct from full release, and neither establishes manufacturing or hardware approval.
