# Task 5 review

Reviewed commit `5f3c4a8453e9aeb1342b9a83438f1bb155e6fc62` against task-5-brief.md and task-5-report.md. Source review only; the reported 38-method green suite was not rerun. The supplied task-5-review.diff contains unrelated baseline/integration reversions rather than this commit's control changes, so review scope was established using the exact commit diff. Root-owned tool baseline integration and Task 6 identity/command handshake are excluded.

## Verdict

**Spec compliance: FAIL — two important gaps require correction.**

**Code quality: CHANGES REQUESTED.**

The implementation correctly adds strict boolean observations, positive interval validation for ordinary values, continuous guide-down/lower-gate checks, disabled fault targets, layered motion rejection, explicit work/service bounds, per-side clamp travel and reachable ideal capture limits. The two intended guide-loss and reopened-gate paths are covered from IDLE. No physical stopping, capture or hardware claims were introduced.

## Important findings

1. **[P2] Check the release-entry capture guard before emitting the release command.** `control/feed_cycle.py:25,49,61` checks invariants only for the source state; `control/contracts.py:41` rejects high capture only in IDLE/RELEASE. On a valid reachable AIM path with an already observed low aim-arrival followed by `aim_reached=True`, `wheels_ready=True`, and `capture_detected=True`, AIM passes validation and transitions to RELEASE, immediately returning `clamp_target='open'`. Only the following tick faults with `capture_sensor_high_before_approach`. Missing `capture_detected` at this same boundary likewise permits release before next-tick validation rejects it. The brief explicitly requires no advancing/outputting a tick before reporting a protection failure. Require and check the capture-release entry precondition before changing state or issuing the open-clamp target; add a reachable AIM-to-RELEASE injection test asserting the exact fault and all targets inactive on that tick. This is a pre-output guard issue, separate from Task 6's identity handshake.

2. **[P2] Normalize unrepresentable real inputs into contract failures.** `control/contracts.py:15` calls `math.isfinite(dt)` directly; Python raises `OverflowError` for an integer such as `10**1000`. `FeedCycle.step` catches only `ObservationError`, so supplying that dt during an active state escapes instead of latching FAULT, leaving the prior state and its enabled outputs available. `cad/assemblies/kinematics.py:61` has the same escape for an axis value, rather than returning its promised layered reason list. Guard conversion/finiteness checks against overflow and reject such values through the established contract result. Add focused tests for an active cycle's huge integer dt and huge integer axis value; require FAULT/no active targets and a `data:` reason respectively.

## Validation limits

Findings follow directly from the transition ordering and Python numeric conversion semantics. Existing reported tests cover ordinary invalid types/nonfinite floats, but neither release-entry injection nor unrepresentable integers. No existing test commands were repeated and no source files were edited. Continuous guide-down, closed lower-gate and the ordinary work/service motion cases otherwise match the specified scope.
