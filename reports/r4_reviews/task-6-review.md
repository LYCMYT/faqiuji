# Task 6 independent review

Reviewed commit `7fe4b7b`, task brief/report/diff and current command/controller/tests. Static review only; reported test runs were not repeated. Constructor is disarmed as required; the earlier armed-constructor concern is superseded.

**Verdict: changes requested — one P2 lifecycle issue.**

## P2 — retain completed command evidence until physical arrival can be observed

`control/feed_cycle.py:56-57` uses only the return value of `commands.observe(ack)` for arrival. `control/commands.py:24` returns false whenever a tick has no acknowledgement, despite `self.complete` remaining true. Therefore a valid acceptance, followed by valid completion while the separate physical arrival boolean is still false, cannot later finish when that boolean becomes true without another new completion message. Replaying the original completion is correctly refused by the sample guard, so a device that emits completion once stalls until the simulated timeout and faults. The two independently supplied observations need not arrive in the same tick, and the documented protocol does not require repeated completion transmission. A subsequent fresh noncompletion message can also clear `complete`.

Latch a validated completion for the active immutable command and combine that retained evidence with the current physical observation. Clear it only on new command/cycle or lifecycle abandonment; keep stale IDs/samples unable to create completion. Add a regression with completion received before the physical arrival boolean, then a later arrival tick with no ack (including already-at-target HOME).

## Other requested checks

The implementation separates command/cycle identity from position feedback, requires separate acceptance/completion samples, rejects stale/cross-cycle identities and repeated sample numbers, and explicitly rejects duplicate IDs within a lifecycle. The zero-angle full-cycle regression keeps head_home true throughout. Pause abandons the active lifecycle; FAULT remains latched; reset leaves disarmed IDLE; explicit restart changes identity without motion; constructor recreation and DONE do not start another cycle. Unknown stop/reset step parameters are rejected. Actuator-specific stopped intents and their unverified mechanical capabilities are explicitly BLOCKED. Nonzero aiming and real hardware timing/stopping remain documented limitations, not claimed validation.
