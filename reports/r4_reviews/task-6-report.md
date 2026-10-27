# Task 6 report

Ready for independent review; no commit made.

Files owned: control/commands.py, control/feed_cycle.py, docs/control_contract_r4.md, tests/test_command_lifecycle.py, tests/test_control_invariants.py, positional-feedback section of tests/test_r1.py, handshake loop of tools/check_r1_contracts.py. Generated reports/r1_contract_validation.json was refreshed by running the checker; no input evidence modified.

Implemented immutable command/cycle identities for positional transitions; fresh separate acceptance and completion samples; actual finite numeric target matching and literal in_tolerance validation; stale/repeated/cross-cycle messages rejected. Physical observations remain separately required. Full zero-angle single-cycle regression keeps head_home True throughout and completes without artificial departure. Pause abandons cycle; fault locks; reset leaves unarmed IDLE; restart changes cycle identity without issuing motion. DONE does not reschedule. Unknown stop/reset keywords raise TypeError; invalid lifecycle operations raise ValueError. Stopped actuator-specific requested intents are explicitly BLOCKED pending mechanical/electrical capability evidence.

RED evidence: initial new tests failed for missing home command and pause API (2 failed); later acceptance-during-motion and historical duplicate-command regressions each failed before their fixes. GREEN: full pytest 50 passed, 1260 subtests passed (8.93 s), runtime D:/86173/Documents/BM1_V02_Engineering/.venv/Scripts/python.exe. R1 checker PASS cycle 22 trace rows, 5 injected faults; start=False and gate_closed entry safeguards retained. No physical hardware testing performed.

Limitations/review points: AIM currently explicitly targets zero degrees; nonzero aim API is not implemented. Numeric equality is conservative offline target validation rather than a fabricated hardware tolerance. Command sample ordering is command-scoped; matching identities and fresh acceptance isolate cycles. Fresh constructor preserves existing explicit-start API (armed=True), while reset requires restart; a future hardware adapter must not replay stored start on reconnect/process restart. Parent notified of this policy point for review. Pneumatic transitions retain strict physical observations rather than receiving positional lifecycle IDs. No continuous scheduler added.

## Conservative recreation follow-up

Parent requested simulator-enforced no-auto-start on process recreation. Fresh FeedCycle now starts disarmed IDLE; only explicit restart() arms a later start input. Added regression covering repeated persistent start=True on two fresh objects, both remaining IDLE; explicit restart itself remains IDLE and a separate start tick begins the cycle. RED: new regression failed on armed=True before changing the constructor. Updated initial-start control helper, full-cycle regression and R1 trace to explicitly call restart(); documentation updated. Covering control tests: 34 passed, 1252 subtests passed (14.56 s). This supersedes the earlier constructor armed=True limitation. No commit made.

## Task 6 fix round 1 — completion evidence latch and oversized input

Addressed independent review P2: validated completion is now terminal retained evidence for the active immutable command. Missing acknowledgements and later noncompletion status cannot erase it; a later physical HOME/LOAD arrival sample can advance without repeated completion transmission. Existing new-command/cycle/abandonment lifecycle replacement clears the latch. Added HOME and LOAD delayed-arrival regressions checking no-ack waiting ticks, later fresh noncompletion status, subsequent physical arrival with no ack, and clearing on the next command; added pause/reset/restart abandonment coverage.

Guarded math.isfinite(actual_position) against OverflowError, so 10**1000 is rejected as a completion position and the controller remains HOME instead of crashing. Added exact oversized numeric regression.

RED: targeted lifecycle run reproduced 3 failures (HOME and LOAD completion cleared by later noncompletion status, plus huge integer OverflowError). GREEN: targeted lifecycle/input/invariants/R1 control tests 37 passed, 1254 subtests passed in 3.55 s using the prescribed virtualenv. Docs updated with retained-evidence semantics. Files changed this round: control/commands.py, tests/test_command_lifecycle.py, docs/control_contract_r4.md, this report. No commit; no subagents; no hardware claims.

## Task 6 fix round 1 — strict acceptance validation follow-up

Moved full required acknowledgement validation ahead of acceptance/sample-cursor mutation. cycle_id and accepted_id must match; completed_id must be None or string; sample_id must be integer/nonboolean; actual_position finite numeric/nonboolean; in_tolerance literal boolean; all protocol fields required. Invalid first acknowledgements (including huge numeric, bool position, inf, malformed tolerance/completion ID and missing fields) cannot establish acceptance or consume sample numbers. Regression proves the following valid completion cannot complete immediately without preceding valid acceptance.

Added finite accumulation guard for both simulation clock and state elapsed time. Overflow latches simulation_clock_overflow FAULT before command issue and preserves prior finite clock. RED: targeted new regressions produced 10 failures (9 strict-ack subcases and clock overflow). GREEN: lifecycle/input/invariants/R1 tests 39 passed, 1267 subtests passed in 3.38 s. Additional file in this follow-up: control/feed_cycle.py. No commit made.
