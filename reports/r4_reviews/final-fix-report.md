# Final source review fix wave — 2026-10-27

Read `final-source-review.md` and addressed both P2 findings plus the related new-R4 provenance default identified by root. No CAD geometry changes, commits or subagents.

## RFQ completeness and retained revisions

Added pure, CAD-free `tools/r4_rfq.py`, consumed by `tools/build_r4_candidate.py`. RFQ membership is the union of every family declared in `data/r4_first_article.json` and additional actual R4 families in the current native index. A missing declared family now raises an error instead of silently disappearing. Formal revision comes from the native family/index revision, never a descriptive provenance note: the retained `PRT-0603-R3-R29-L` jaw and `PRT-0602-R3-BASE` remain R3. Native assembly quantities are not copied into quote quantities. Supplier, quantity, quote and lead time stay unknown/blank; supplier confirmation, first-article release and manufacturing release stay false.

The exporter now calls the same pure provenance helper: explicit modification/source notes are preserved, and new R4 hardware lacking a note defaults to `R4 self-designed candidate`, rather than `R3 retained`. Existing lightweight `test_part_role_contract.py` covers declaration completeness, retained revisions, additional R4 membership, CSV serialization of blanks/false flags, missing-family rejection and the hardware provenance fallback. No CI module-pattern change is needed.

## Actual clamp opening and supported open approach

The ball/contact sequence now derives RELEASE from authoritative `clear_stroke`, matching current `FeedCycle.outputs()` at105mm. Historical `implementation.demo.release_complete_x` no longer controls any R4 checked pose. Nine nominal states cover OPEN_LOAD, CLOSED_GRIP, GUIDE_UP, CLEAR, RELEASE(open at clear), APPROACH_OPEN(prescribed midpoint), CAPTURE_BOUNDARY(`capture_stroke()`), EMPTY_FORWARD and EMPTY_RETURN.

Open jaws at105mm do not mean the ball has departed. RELEASE and the open approach use explicitly prescribed supported contact references. The boundary is the ideal geometric capture position, not measured capture; the fixture contains no wheels and cannot establish actual capture or free trajectory. Only after the assumed boundary handoff is the reference omitted from empty forward/return stages. Expected contact/clearance and native cork/skirt intersections pass at all nine states. The regression compares actual control RELEASE/APPROACH targets and proves that changing the historical release value leaves the entire checked R4 sequence unchanged. Affected mechanical/data prose now describes these nine states and assumptions.

## RED / GREEN commands and evidence

Runtime for each command: `D:/86173/Documents/BM1_V02_Engineering/.venv/Scripts/python.exe`.

RED:
- `-m unittest tests.test_part_role_contract.PartRoleContractTests.test_r4_rfq_includes_declared_retained_candidates_and_actual_revisions -v`: failed before implementation (pure RFQ contract module absent).
- `-m unittest tests.test_r4_mechanics.R4MechanicsTests.test_ball_release_matches_control_and_ignores_historical_animation_release -v`: failed on the original implementation because changing historical release_complete_x from−25 to−20 changed the checked release slide from165 to170mm. The required current control target is105mm.

GREEN:
- `-m unittest tests.test_part_role_contract -v`: **8/8 PASS**,0.025seconds. Pure/lightweight, no CadQuery dependency.
- `-m unittest tests.test_r4_mechanics.R4MechanicsTests.test_ball_sequence_explicitly_releases_ownership tests.test_r4_mechanics.R4MechanicsTests.test_ball_release_matches_control_and_ignores_historical_animation_release -v`: **2/2 PASS**,7.308seconds. These execute native all-context ball checks for nine states and confirm current control target consistency/history independence.

No full working-motion matrix was rerun because no native geometry changed. Root must regenerate RFQ/index/illustrations and perform the final frozen-source build after scoped review. Manufacturing/operation remains BLOCKED by the genuine physical gates; no unknown force, material, vendor, tooling, actual-capture or procurement value was filled in.
