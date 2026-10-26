# BM1 V0.2 R1 implementation

User authorized all five next steps. Preserve the delivered V0.2 ZIP; implement all digitally executable work in the current checkout. Physical measurements, supplier confirmation and hardware tests remain missing inputs, never fabricated.

## Decisions
- Retain CadQuery, Blender, data authority, all 44 main IDs and original mechanical limits.
- Replace post-capture forward feeding with a contact-boundary hold and feedback-gated retreat. X=-5 remains an empty-carriage mechanical travel check, not a loaded command. This closes a commanded geometric overrun, not the unknown traction dynamics.
- Replace the obstructed bare-tube rear removal procedure with a complete feeder cassette: tube, separator, sleeve and associated sensors removed together. Add mating receiver channels and transverse release pins. Check actual pin and cassette paths without hiding obstructing parts.
- Replace rectangular upper contact faces with curved replaceable pads and export alternative fit-test inserts. Stack pitch and feather compression stay unmeasured; produce an instrumented separator test fixture and measurement records.
- Replace the variable-length carriage wire with a constant-length analytic U loop. Its design radius remains a candidate until cable procurement; other rotary/mast circuits remain documented work, not falsely validated.
- Build runnable feedback/interlock fault tests; generate measurement, supplier-interface, mass/stability and prototype-test packages. Do not select torque/speed/electrical ratings without measured loads.

## Tasks and evidence
1. Archive baseline metadata and add data/r1_engineering.json. Read current contact geometry and service obstructions.
2. Tests: loaded overrun rejected; dry travel permitted; capture and departure independently confirmed; unsafe feedback faults latch; synthetic stack input never promoted to measured. Implement controller simulator and data-based capture boundary.
3. Model cassette receivers/pins, pad inserts and constant-length carriage cable. Export native STEP; exact static and service collision checks, fix actual intersections.
4. Re-run full motion grid with distinct loaded/empty states and world-frozen reference after capture. Include conservative no-flight hold/retreat checks. Sample cable length/radius.
5. Export low-speed bench fixture and variants. Prepare CSV/JSON blank measurements, interface RFQ, wiring/stop functional diagram, executable stability calculation which blocks on missing mass/COM, and test protocols mapping U01-U10.
6. Rebuild BLEND/GLB, views/PDF/animations/viewer, re-open exports, render and inspect. Generate R1 acceptance report and integrity-checked R1 ZIP.
7. Independent final review per executing-plans skill; fix important findings with regression evidence.

## Review focus
- A sensor that is already stuck high must not authorize departure. Capture timeout and open cover remove actuator enables.
- Loaded and empty travel are distinct; capture is derived from wheel and cork geometry.
- A frozen world marker cannot follow the carriage after capture or receive a blanket collision exemption.
- Cassette interfaces stay on the mast; pin withdrawal is checked before cassette extraction.
- No measured records, purchased model, test result or safety rating may be inferred from a generated file.

Execution status and limitations are maintained in reports/r1_progress.md. No design approval pause: user explicitly requested full execution of the preceding proposal.
