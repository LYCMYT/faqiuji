# Task 7 — concrete R4 mechanical review candidate

Implemented without changing R1/R2/R3 history or audit input. No commits made. The full mechanism remains **BLOCKED for operation/manufacturing**, with an explicit nominal candidate and review artifacts ready.

## Files

- `data/r4_fixture.json`: low land; three compared manufacturing alternatives; all new guide, stop, pin, cap, fastener and service/section dimensions; real measurements remain empty/null.
- `data/r4_mechanical_interfaces.json`: five independent manual functions, stable moving/fixed IDs, actual guide topology, nominal strokes, reaction paths, holding/service status and review questions. Slide corrected to authoritative185mm.
- `cad/assemblies/r4_fixture.py`: R3 overlay, stable source IDs, changed R4 families, actual integral land, paired/captive guides, physical stops, split bushes/caps, detachable assembly stops, simplified candidate fasteners, nine positive manual endpoint lock pins and their matching bores.
- `tools/check_r4_geometry.py`: independent full-context exact collision sampling, native support-face/projection, free reference rotations/translations, original rod/nut engagement, native endpoint/lock fits, reaction-contact distances, separate supported maintenance state and specified M4 tool channels; atomic provenance reports.
- `tools/build_r4_package.py`: expected STEP set computed from actual rows/families before writing; assembly/per-family/two native sections, mesh/index/previews; every STEP reopened and checked for native validity, solid count and volume; hashes for all96STEP files plus index/mesh.
- `tests/test_r4_mechanics.py`: sixteen current regressions; `docs/mechanical_r4_review.md`: structure, alternatives, conflict resolution, assembly/service sequence and remaining opens.

## Initial development runs (before independent review)

Runtime: `D:/86173/Documents/BM1_V02_Engineering/.venv/Scripts/python.exe`.

- `python -m unittest tests.test_r4_mechanics -v`: **7/7 PASS**, latest5.343seconds. Includes the M01 original descending tipping mode and free downward-drop counterexamples, native single-solid integrity, five independent fixed/moving guides, detachable assembly parts and185mm authoritative travel.
- `python tools/check_r4_geometry.py`: latest working-path model run **134 endpoint-inclusive states**, **43,032 exact pair checks**, **0 intersection volumes above0.01mm³**. All214 assembly bodies and optional jaw variants were valid single native solids. Overall status deliberately **BLOCKED**, exit1; zero collision arrays do not imply operational approval.
- Exact open-cork bottom-face contact: **378.336405175854mm²**, bboxX[−202,−176.75], Y[−12.0545634512414,+12.0545634512414] for current nominal design. Axis(−190,0) lies in the contact. Free downward0.1mm movement intersects the land. Four horizontal±0.1mm probes are unobstructed: no lateral centering/friction claim is made.
- **14 installed endpoint lock fits** from nine positive pins: no native overlap above threshold. Two upper carrier sides, one gate lock, two sleeve locking stations, two slide locking stations and two clamp-side locks are checked separately from parked motion.
- Upper supported service sequence: actual cap hardware/lock pins removed,6mm lift,24→40mm withdrawal; **0 sampled service collisions**, **4 original M4 straight tool channels clear**. The parts removed are enumerated explicitly.
- Latest `--static` diagnostic after adding reaction-chain checks: **0 collisions**,325exact pair checks;13specified structural mating pairs each measured distance0 and overlap0. Full report gains these new fields on root's final rerun; the earlier full run already checked the same unchanged solids.
- `python tools/build_r4_package.py`: **214 instances,96STEP files reopened**, PASS quantitative native roundtrip,98artifact hashes. Largest absolute volume difference0.008464mm³ in the large assembly, within relative1e−8 tolerance; per-file source/reopened volumes and solid counts are recorded. Visually inspected the exported assembly preview; candidate labels and full fixture are visible.

Development reports were generated while root was integrating other source files. Root must perform the final frozen-source/same-run provenance rerun. This report does not assert that development report fingerprints remain current after subsequent documentation/source changes.

## Genuine remaining blockers

1. Review fix1 completed nominal split-cap/fastener withdrawal and proposed new-tool envelope checks. Actual selected tools, drive features and human handling remain OPEN; those physical confirmations are not implied by digital clearance.
2. Positive lock pins and installed fit geometry exist, but pin grade, shear/bearing strength, anti-loss detents/tethers, fastening grades/preload and required operating/holding force remain OPEN. Support moving members before pin withdrawal; no unattended or powered operation.
3. The sleeve way's physical attachment process into the original bracket is a candidate mating/weld interface, with no weld procedure or strength result. Native contact/reaction topology is inspected, not load approved.
4. Thin rear gate ribs, changed shoe pockets, arm lock-hole edge distance, table/anchors and fixture stiffness need measured load/first-article review.
5. Real cork/skirt range, friction, impact settling, feed/drop and release performance remain unmeasured. Continuous sweep, arbitrary simultaneous states and whole-machine wheel clearance are NOT_RUN.

No supplier hole pattern, force, approval, physical result or manufacturing release was fabricated. The standalone review candidate is concrete and exportable; remaining blockers must stay visible in any packaged result.


## Review fix round1 — 2026-10-27

Addressed all four findings in `task-7-review.md`:

1. `PRT-0607-B` retains its stable instance ID but its positive lock-bore modification now uses `revise()`, a derived R4 family and explicit R4 modification provenance. It will no longer export as `R3 retained`.
2. Added `tools/r4_mechanical_checks.py` and declared all candidate tool dimensions in `data/r4_fixture.json`. Actual ordered removal is checked without prematurely deleting obstructing parts: upper hold pins; cap screws; outer-first upper nuts; caps; gate pin/screws/nuts/caps; slide stop screws/stops; sleeve upper stop screws/stops; clamp locking pins/lower nuts/travel pins. The57 path legs include start/end samples. Forty new proposed driver/open-wrench/socket envelopes and4 inherited M4 channels are checked separately. New diagnostics found and resolved upper neighboring-nut wrench access (outer-first order), gate riser/nut-tool access (explicit narrowed/relocated support), and clamp lower nut access (through-pocket,20mm candidate socket,10mm drop then25mm side withdrawal, avoiding post cap). Actual tool selection/drive details/handling remain OPEN.
3. Durable native cork/skirt sequence checks cover seven named stages. Expected land contact and closed/open jaw clearance predicates are explicit. Every ball-present pose is a stated nominal assumption, independent of animation parenting. RELEASE is a free reference at the specified release plane; EMPTY_FORWARD and EMPTY_RETURN contain no ball. Grasp/release dynamics, settling and whole-machine wheel clearance remain NOT_RUN.
4. Connection completion now requires actual moving guide material at the guide window, actual restraining bush/lip/back material, nominal engagement/bounds and positive hard-stop collision on both ends, including both symmetric sides. Full working motion evaluates the changed axis at every sample. Installed pins require native pin material crossing the mover and native moving material around the bore, in addition to non-interference. Reports carry per-predicate PASS/FAIL. Adversarial tests reject a detached mover, detached fixed bush, overtravel and a shifted/nonengaging lock pin.

Latest affected test run: `python -m unittest tests.test_r4_mechanics -v`, **16/16 PASS**,33.774seconds. Static review-fix diagnostic: **digital_status PASS**, no digital failures,57 removal legs/40 new tool channels clear, all14 endpoint pin fits/engagement predicates pass, five guide/retention/stop acceptance groups pass, seven nominal ball stages pass,214 native single-solid bodies and zero static collisions. Overall remains BLOCKED solely with explicit physical-blocker fields until physical ratings/measurements and actual tooling/handling are validated. Full working-path rerun completed: **134 states,43,032 exact fixture-pair checks,0 collisions,133 moving-axis retention evaluations PASS**,14 positive-pin fits/engagement checks PASS,57 ordered removal path legs PASS,44 total candidate/inherited tool channels PASS and seven ball stages PASS. `digital_status=PASS`, `digital_failures=[]`; overall `status=BLOCKED` retains only explicit physical-blocker fields. The helper also fails closed after a blocked tool/removal phase instead of silently dropping the part. Root will regenerate changed-family outputs and perform final frozen-source/same-run provenance validation.


## Review fix round2 — actual unlocking and fail-closed socket handling

Read and addressed both findings in `task-7-fix1-review.md`. Minimal changes are confined to `tools/r4_mechanical_checks.py`, `tests/test_r4_mechanics.py` and this report; no native model/data geometry changes, commits or subagents.

- Eligible pins now start from `installed_shape` transformed by their actual kinematic parent and current endpoint state. The current supported empty service pose engages seven pins spanning all five functions: two upper pins, one gate pin, one115mm sleeve pin, one0mm slide pin and two clamp pins. The other endpoint-station pins correctly remain parked. Each engaged pin receives an explicit installed-to-park trajectory before later removal/fastener work. Native start/end bounds, endpoint/state and transformed withdrawal vector are reported. Seven unlocking legs extend the service report from57 to **64** path legs; the earlier57-leg evidence alone did not cover real unlocking.
- A failed M4 socket now adds its nut to the same blocked-part handling used by other tools. Failed nuts remain in native context and `actually_removed` excludes them. Each dependent travel pin requires successful removal of its own lower nut; otherwise it receives an explicit dependency-blocked FAIL and remains present.
- Negative regression1 adds an annular obstruction that clears every later parked-to-removed pin pose but catches the engaged pin head during installed-to-park withdrawal. The new unlock fails and that pin is not removed.
- Negative regression2 sets only candidate M4 socket radius to20mm. Both socket channels fail, both lower nuts remain unremoved, and both corresponding travel pins remain unremoved with explicit nut dependencies. The nominal test also asserts the native start bounds of all seven unlocks against correctly transformed installed solids.

Validation: `python -m unittest tests.test_r4_mechanics -v` — **18/18 PASS**,91.152seconds. `python tools/check_r4_geometry.py --static` — **digital_status PASS**, `digital_failures=[]`, zero static collisions/325exact pair checks, all **64** ordered path legs (including seven actual unlocks) PASS, **44** specified tool channels PASS. Overall remains BLOCKED with physical blocker fields; actual tooling/handling, loads/material/fastener/weld/detent qualification and real-ball performance are unchanged UNKNOWN/OPEN. No model geometry changed, so a development full working-motion rerun was not required in this fix; root will perform the final frozen-source full rerun after scoped review.
