# Task 6 fix round 1 re-review

Scope: commit `dbf38f2`, task-6-fix1.diff and updated task-6-report.md. Static review; documented RED/GREEN runs were not repeated.

**Verdict: APPROVED within the scoped fix review.**

- Original P2 (completion evidence lost before later physical arrival): **ADDRESSED**. `CommandLifecycle.observe()` returns retained completion before processing later status; missing acknowledgements and fresh noncompletion status cannot revoke it. The controller can combine the retained evidence with a later physical observation. Replacement lifecycle objects clear it on command/state transitions and abandonment. Added HOME/LOAD delayed-arrival and pause/reset/restart regressions exercise the relevant behavior.
- Additional strict-ack validation changes validate all required fields and finite numeric position before changing acceptance/sample cursor. Malformed first acknowledgements cannot seed acceptance.
- Accumulated clock/state-time overflow is rejected before storing nonfinite values or issuing a command. The documented regression checks the fault and preserved finite clock.

No new actionable breakage found in the fix diff. Covering evidence in the report: 39 passed, 1267 subtests passed. This is an offline contract review and does not establish hardware timing or stopping capability.
