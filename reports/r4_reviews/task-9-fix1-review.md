# Task 9 fix 1 review

Scope: commit `29df3ff`, supplied task-9-fix1.diff and appended report only. Verdict: **CHANGES REQUIRED** — one narrow remaining validation gap.

- Prior numerical finding: addressed. The numpy error-state wrapper converts arithmetic/linear algebra failures into ValueError, and solution/residual finiteness is checked before success. The reported overflow regression and solver tests passed; not rerun.
- Prior empty-source/file and unspecified-pose finding: empty/blank sources, empty files, empty revisions, and missing/incomplete index poses are now rejected. However, row/record pose validation remains incomplete (below).
- Prior instructions finding: addressed by docs/engineering_evidence_r4.md, covering manifest scope, record linkage, full versus partial semantics, assumptions and an explicitly incomplete input example.

**[P2] Apply finite pose validation to each row and source record, not just the index** — `engineering/evidence_schema.py:28-35`. Only evidence_index.pose is checked with finite_number. Row/record poses use dictionary equality, where Python considers False equal to 0 and True equal to 1. An additional focused probe accepted a row with pose `{height: False, yaw: False, pitch: False}` against the index's numeric zero pose and valid nonempty linked file. The same bypass applies to a record pose. Validate the required numeric fields of all three pose objects before comparing them, using the same finite non-bool contract, and add row/record boolean-pose regression cases.

No full suite or already evidenced tests were rerun. Only the new focused boolean-pose probe was executed. No other material regression found in this fix diff.
