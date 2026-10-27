# Final source fix scoped review

Verdict: APPROVED for commit 3213fb9. Both findings in final-source-review.md are closed at source level, including the related newly designed R4 part provenance fallback. No new important breakage established in this diff.

- RFQ membership now takes all explicitly declared first-article families plus additional native R4 candidates. Missing declared families fail closed. Retained jaw/base receive formal R3 revisions; the actual family/index revision is distinct from descriptive source provenance. Unknown supplier/quantity/quote/lead time serialize blank, and confirmation and release flags remain false.
- Native exporter provenance preserves explicit revision/source notes and identifies new R4 hardware without notes as an R4 self-designed candidate. It no longer silently labels those rows R3 retained.
- The nine-state ball sequence now uses clear_stroke for clamp opening, matching the control RELEASE target, then checks the nominal supported open approach and capture_stroke boundary. It explicitly keeps the ball present on the support through this nominal boundary and removes the reference only after an assumed handoff. The fixture's missing wheels, actual capture and free trajectory remain NOT_RUN. Historical animation release_complete_x no longer selects a checked R4 release position.

Reviewed final-fix.diff, final-fix-report.md and source/test changes. The recorded 8 RFQ/provenance tests and 2 native nine-state ball tests pass, including CSV unknown/false serialization, retained revisions, missing-family rejection, actual control target agreement and historical-animation independence. No redundant suite or CAD matrix was run for this review. No native geometry change is present in this fix.

Task7 fix2 63f4916 is covered by its separate APPROVED scoped review; its two issues are not reopened here. That review's final service count is 64 legs including seven installed-pin unlock legs, superseding historical development counts in the mechanical narrative.

This closes the source CHANGES REQUESTED disposition from final-source-review.md. Overall completion still requires root's final frozen-source same-run report/artifact/package validation. Source approval is not artifact proof, supplier confirmation, manufacturing approval or permission for physical operation. Genuine external gates remain OPEN/BLOCKED.
