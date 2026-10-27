# Final whole-branch source review — R4

Review baseline: c8c52514a80f52c364950852ed2fde2a1d926e62. Source reviewed through 60173ca, including the first-article/ball-state additions in 5b292c4. Task7 fix2 was being edited concurrently and is excluded from approval pending its scoped follow-up. Review-only: no implementation changes or full-suite/matrix reruns.

Verdict: CHANGES REQUESTED — two important cross-task integration issues. Final same-run artifacts and package remain pending; this is not a release or physical approval.

## Findings

1. **[P2] Include the actual retained first-article candidates in the RFQ** — `tools/build_r4_candidate.py:64-65`.
   `first_article_RFQ.csv` includes only families whose names contain `R4`, and assigns all included rows revision `R4`. However, `data/r4_first_article.json` explicitly selects `PRT-0603-R3-R29-L` and `PRT-0602-R3-BASE` alongside the R4 receiver; the release scope likewise includes jaw screening and the fixture base. Both retained candidates get new first-article drawings and inspection templates but are absent from the delivered RFQ. A recipient using the stated first-article RFQ cannot quote the complete declared trial scope. Build RFQ membership from the declared first-article families (union any explicitly desired additional R4 candidate scope), retain each family's actual revision, and verify all declared first-article families appear. Quantities, quotes, supplier confirmation and release must remain unknown/false.

2. **[P2] Check the ball at the actual control release position** — `tools/r4_mechanical_checks.py:153-154`.
   The seven-stage ball/contact sequence derives RELEASE from historical `implementation.demo.release_complete_x`, giving slide=165 mm (`-25 - -190`). The current control contract opens the clamp in RELEASE at `clear_stroke=105` (`control/feed_cycle.py:109`), and the working geometry path also opens at 105 (`tools/check_r4_geometry.py:68`). Consequently the ball-contact report and its generated release illustration skip the actual open-at-clear state, then label a ball prescribed 60 mm farther along as the release instant. The context-only working collision path does not include the ball and cannot fill this gap. Derive clamp release from the current control/working-path contract and verify open jaws with the ball at 105. Separately depict/check the supported open-jaw approach and ideal capture boundary, clearly labeling the prescribed reference pose as a nominal contact assumption. Clamp opening at 105 does not establish that the ball has left its support; after the assumed capture/handoff, detach or omit the reference for empty return. The R4 fixture excludes wheels and cannot establish actual capture or any free trajectory; these must remain NOT_RUN. Add a focused consistency assertion so changing a historical animation value cannot silently change the checked R4 control sequence.

## Scope and evidence

Read the requested R4 plan and SDD progress, source producers/consumers for input ownership, provenance, release/review packaging, control lifecycle, evidence/support evaluation, five-function geometry, first-article drawings, protocol and delivery documentation. Confirmed the release-position discrepancy through a read-only parameter query (`load_x=-190`, `clear_stroke=105`, historical `release_complete_x=-25`). The RFQ omission follows directly from its deterministic family predicate and the explicit three-family first-article input. No expensive CAD matrix or full suite was repeated.

The known Task7 installed-pin withdrawal and failed-clamp-socket propagation issues are not duplicated here; their original implementer/scoped review owns closure. Existing cold-core evidence remains evidence for its named source revision, not current final R4 artifact proof. The interrupted build is not treated as PASS.

The remaining supplier drawings, real ball geometry/force, material/fastener grades, preload/load ratings, actual tool/hand access, table/anchor properties, electrical holding/stopping, procurement and physical trials are genuine external gates. Keeping these OPEN/BLOCKED and manufacturing_release=false is correct; this review does not request invented values or blanket release. No additional important source issue was established in the reviewed areas.

