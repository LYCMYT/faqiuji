#!/usr/bin/env python3
"""Reproduce BM1 offline-contract review findings without modifying the repository.

This is an audit probe, not firmware, not a patch, and not a hardware test.
All result files must be outside the inspected repository. Python bytecode writes
are disabled before importing its modules. A finding marked ``reproduced`` means
the observed behavior matches the reviewed defect, not that the defect is fixed.

Usage:
    python reproduce_control_findings.py --repo /absolute/path/to/faqiuji --output /tmp/control-results.json --mass-output /tmp/mass-results.json
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
import runpy
import subprocess
import sys
from datetime import datetime, timezone

sys.dont_write_bytecode = True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo", type=Path,
        required=True,
    )
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("results.json"))
    parser.add_argument(
        "--mass-output", type=Path,
        default=Path(__file__).with_name("mass_solver_counterexample.json"),
    )
    args = parser.parse_args()
    repo = args.repo.resolve()
    for output in (args.output, args.mass_output):
        if output.resolve().is_relative_to(repo):
            parser.error("Audit output must be outside the inspected repository")
    sys.path.insert(0, str(repo))

    import numpy as np
    from control.feed_cycle import FeedCycle
    from cad.assemblies.kinematics import permitted
    from engineering.evaluate import evaluate

    def git(*arguments):
        result = subprocess.run(
            ["git", "-C", str(repo), *arguments],
            capture_output=True, text=True, check=True,
        )
        return result.stdout

    revision = git("rev-parse", "HEAD").strip()
    diff_before = git("diff", "--binary", "HEAD")
    status_before = git("status", "--short")

    def initial():
        return dict(
            cover_closed=True, estop_ok=True, cassette_locked=True,
            exit=False, capture_detected=False, head_home=True,
            slide_home=True, slide_clear=False, aim_reached=False,
            guide_up=True, guide_down=False, gate_closed=True,
            gate_open=False, clamp_closed=False, clamp_open=True,
        )

    def run_trace(changes, dt=0.1):
        controller = FeedCycle()
        sample = initial()
        trace = []
        for index, change in enumerate(changes):
            sample.update(change)
            output = controller.step(sample, dt)
            trace.append(dict(
                index=index, dt_s=dt, change=change,
                input=sample.copy(), output=output,
            ))
        return controller, sample, trace

    findings = []

    def add(identifier, priority, title, locations, observations, reproduced, expected):
        findings.append(dict(
            id=identifier, priority=priority, title=title,
            source_locations=[dict(file=str(repo / file), lines=lines)
                              for file, lines in locations],
            observations=observations, reproduced=bool(reproduced),
            expected_after_fix=expected,
        ))

    # Reachable path: loss of guide-down confirmation immediately before DROP.
    _, _, trace = run_trace([
        dict(start=True),
        dict(guide_up=False, guide_down=True),
        dict(guide_down=False, upper_held=True),
    ])
    output = trace[-1]["output"]
    add(
        "C01", "P1", "Guide-down loss does not prevent opening the drop gate",
        [("control/feed_cycle.py", [40, 41, 54, 62, 82, 88])], trace,
        output["state"] == "DROP" and output["gate_target"] == "open"
        and output["enable_motion"] and output["fault"] is None,
        "Required guide-down feedback must remain confirmed during loading/drop; loss must fault before opening the gate.",
    )

    # Reachable path: the gate reopens after its first closing confirmation.
    _, _, trace = run_trace([
        dict(start=True),
        dict(guide_up=False, guide_down=True),
        dict(upper_held=True),
        dict(gate_open=True, gate_closed=False, ball_present=True),
        dict(gate_closed=True, gate_open=False),
        dict(clamp_closed=True, clamp_open=False, gate_closed=False, gate_open=True),
    ])
    output = trace[-1]["output"]
    add(
        "C02", "P1", "Gate-closed loss after releasing upper retention does not fault",
        [("control/feed_cycle.py", [43, 44, 60, 62, 89])], trace,
        trace[-2]["output"]["upper_target"] == "open"
        and output["state"] == "GUIDE_UP" and output["fault"] is None,
        "Define and enforce the continuous gate/upper-retention handover invariant; reopening must not continue the normal cycle.",
    )

    # Each string probe follows a reachable path from IDLE.
    string_cases = []
    for name, changes, target in [
        ("start_string_false", [dict(start="false")], "GUIDE_DOWN"),
        ("guide_down_string_false", [dict(start=True), dict(guide_up=False, guide_down="false")], "RETAIN"),
        ("upper_held_string_false", [dict(start=True), dict(guide_up=False, guide_down=True), dict(upper_held="false")], "DROP"),
    ]:
        _, _, trace = run_trace(changes)
        output = trace[-1]["output"]
        string_cases.append(dict(
            case=name, trace=trace,
            reproduced=output["state"] == target and output["fault"] is None,
        ))
    add(
        "C03", "P1", "String false is accepted as affirmative input",
        [("control/feed_cycle.py", [20, 21, 22, 35, 39, 40, 41])], string_cases,
        all(case["reproduced"] for case in string_cases),
        "Validate every required digital input as an actual bool before transitions/output decisions.",
    )

    # Zero-angle/unchanged-home assumption: head_home truthfully stays high.
    home_changes = [
        dict(start=True),
        dict(guide_up=False, guide_down=True),
        dict(upper_held=True),
        dict(gate_open=True, gate_closed=False, ball_present=True),
        dict(gate_closed=True, gate_open=False),
        dict(clamp_closed=True, clamp_open=False),
        dict(guide_up=True, guide_down=False),
        dict(slide_clear=True, slide_home=False),
        dict(aim_reached=True, wheels_ready=True),
        dict(clamp_open=True, clamp_closed=False),
        dict(capture_detected=True, slide_clear=False),
        dict(exit=True), dict(exit=False), dict(slide_clear=True), {}, {},
    ]
    controller, sample, trace = run_trace(home_changes)
    timeout_output = controller.step(sample, 10.0)
    trace.append(dict(index=len(trace), dt_s=10.0, change={}, input=sample.copy(), output=timeout_output))
    add(
        "C04", "P2", "Already-home cycle stalls waiting for a false-to-true home edge",
        [("control/feed_cycle.py", [32, 35, 36, 37, 50, 51, 73, 75])],
        dict(assumption="Zero-angle target/unchanged home pose; head_home remains True throughout. No hardware motion was exercised.", trace=trace),
        all(entry["input"]["head_home"] is True for entry in trace)
        and trace[-2]["output"]["state"] == "HOME"
        and timeout_output["fault"] == "state_timeout",
        "Use fresh command completion identity/handshake while allowing a validated already-at-target case; do not require fabricated physical departure.",
    )

    dt_cases = []
    for label, interval in [("true_boolean", True), ("string_0.1", "0.1"), ("null", None), ("nan", math.nan), ("zero", 0)]:
        controller = FeedCycle()
        controller.state = "RETAIN"
        sample = {**initial(), "guide_up": False, "guide_down": True, "upper_held": True}
        record = dict(case=label, initial_state="RETAIN")
        try:
            record["output"] = controller.step(sample, interval)
            record["raised"] = None
        except Exception as error:
            record["raised"] = dict(type=type(error).__name__, message=str(error))
            record["output_after_exception"] = controller.outputs()
        dt_cases.append(record)
    add(
        "C05", "P2", "Invalid dt types can bypass the fault path",
        [("control/feed_cycle.py", [18, 19])], dt_cases,
        dt_cases[0]["output"]["state"] == "DROP"
        and all(case["raised"] and case["raised"]["type"] == "TypeError"
                and case["output_after_exception"]["enable_motion"]
                for case in dt_cases[1:3]),
        "Reject bool/non-real dt before math.isfinite and latch invalid_sample_interval consistently.",
    )

    permit_cases = []
    for name, state in [
        ("slide_nan", dict(guide=115, slide=math.nan, clamp=14)),
        ("guide_nan", dict(guide=math.nan, slide=105, clamp=0)),
        ("yaw_nan", dict(guide=115, slide=105, yaw=math.nan, clamp=0)),
        ("negative_slide", dict(guide=115, slide=-100, clamp=0)),
        ("empty_slide_1000mm", dict(guide=115, slide=1000, clamp=14, loaded=False)),
        ("yaw180_pitch80", dict(guide=115, slide=105, yaw=180, pitch=80, clamp=0)),
    ]:
        serial_state = {key: ("NaN" if isinstance(value, float) and math.isnan(value) else value)
                        for key, value in state.items()}
        permit_cases.append(dict(case=name, input=serial_state, permitted=bool(permitted(state))))
    add(
        "C06", "P2", "permitted accepts nonfinite and out-of-range states",
        [("cad/assemblies/kinematics.py", [45, 46, 47, 48, 49, 51, 53, 54])],
        permit_cases, all(case["permitted"] for case in permit_cases),
        "Validate finite typed coordinates and axis ranges separately from relative-motion interlocks, or provide one complete permission function.",
    )

    # Reuse the repository's test fixture and exact tested observations.
    test_namespace = runpy.run_path(str(repo / "tests/test_r1.py"), run_name="bm1_existing_test_fixtures")
    test_safe = test_namespace["RevisionContracts"]().safe()
    controller = FeedCycle()
    capture_output = controller.step(dict(cover_closed=True, estop_ok=True, cassette_locked=True, capture_detected=True), 0.1)
    controller = FeedCycle()
    controller.state = "CLEAR"
    held_output = controller.step({**test_safe, "ball_present": False, "clamp_closed": True, "clamp_open": False}, 0.1)
    controller = FeedCycle()
    isolated_capture = controller.step({**test_safe, "capture_detected": True}, 0.1)
    controller = FeedCycle()
    controller.state = "CLEAR"
    isolated_held = controller.step({**test_safe, "ball_present": False, "clamp_closed": True, "clamp_open": False, "slide_clear": False}, 0.1)
    add(
        "C07", "P2", "Two existing tests are satisfied by earlier unrelated faults",
        [("tests/test_r1.py", [36, 37, 83, 84, 85, 86, 87])],
        dict(
            existing_capture_test=capture_output,
            existing_held_ball_test=held_output,
            isolated_capture_guard=isolated_capture,
            isolated_held_ball_guard=isolated_held,
        ),
        capture_output["fault"] == "exit_feedback_missing_or_invalid"
        and held_output["fault"] == "arrival_feedback_missing_slide_clear"
        and isolated_capture["fault"] == "capture_sensor_high_before_approach"
        and isolated_held["fault"] == "held_ball_feedback_lost",
        "Start from complete valid observations, change one condition, and assert the exact fault cause. The guards themselves work for isolated inputs.",
    )

    # Document unsupported API fields separately; these are not asserted defects.
    controller = FeedCycle()
    controller.state = "RETAIN"
    stop_output = controller.step({**initial(), "guide_up": False, "guide_down": True, "upper_held": True, "stop": True}, 0.1)
    controller = FeedCycle()
    controller.trip("audit_fault")
    reset_output = controller.step({**initial(), "reset": True}, 0.1)
    boundary_observations = dict(
        notice="Normal stop/reset/cycle scheduling and timestamp/replay contracts are not implemented. These observations describe current scope, not failed implemented features.",
        unsupported_stop_field=stop_output,
        reset_does_not_clear_latched_fault=reset_output,
    )

    # Fixed support-solver counterexample. Reference solution checks all active
    # subsets, equilibrium, nonnegative active forces, and inactive gaps.
    xy = np.array([[350, -180], [90, 380], [-440, -500], [-250, -300], [440, -320]], float)
    stiffness = np.array([1000.0, 3.0, 1.0, 1.0, 10.0])
    center = np.array([70.0, -280.0, 1000.0])
    weight = 40.0 * 9.80665
    A = np.column_stack([np.ones(5), xy])
    rhs = np.array([weight, weight * center[0], weight * center[1]])
    supports = [dict(x_mm=float(x), y_mm=float(y), vertical_stiffness_N_mm=float(k))
                for (x, y), k in zip(xy, stiffness)]
    mass_rows = [dict(instance_id="audit_demo", mass_kg=40.0,
                      com_world_mm=center.tolist(), evidence_status="measured_or_supplier_verified")]
    actual = evaluate(mass_rows, supports)
    actual_forces = np.array(actual["support_reactions_N"])
    actual_active = np.flatnonzero(actual_forces > 1e-8).tolist()
    sub = A[actual_active]
    actual_plane = np.linalg.solve(sub.T @ (stiffness[actual_active, None] * sub), rhs)
    actual_deflections = A @ actual_plane
    reference_solutions = []
    for count in range(3, len(supports) + 1):
        for subset in itertools.combinations(range(len(supports)), count):
            active = list(subset)
            sub = A[active]
            if np.linalg.matrix_rank(sub) < 3:
                continue
            plane = np.linalg.solve(sub.T @ (stiffness[active, None] * sub), rhs)
            deflections = A @ plane
            if min(deflections[active]) < -1e-8:
                continue
            if any(deflections[index] > 1e-8 for index in range(len(supports)) if index not in active):
                continue
            forces = stiffness * np.maximum(deflections, 0)
            reference_solutions.append(dict(
                active_indices=active, support_reactions_N=forces.tolist(),
                all_support_deflections_mm=deflections.tolist(),
                equilibrium_residual_N_Nmm=(A.T @ forces - rhs).tolist(),
            ))
    mass_result = dict(
        revision=revision, hardware_test=False,
        title="Five-support input exposes missing reactivation/complementarity checks",
        scope="Generic evaluate API defect. The current BM1 template uses four rectangular supports; this example does not claim that template has already produced incorrect forces.",
        source_location=dict(file=str(repo / "engineering/evaluate.py"), lines=[19, 20, 21, 22, 23, 24, 25, 26]),
        input=dict(components=mass_rows, supports=supports, gravity=9.80665),
        actual_output=actual,
        actual_active_indices=actual_active,
        actual_solution_all_support_deflections_mm=actual_deflections.tolist(),
        reference_method="Enumerate all support subsets; solve equilibrium; require active deflections >= 0 and inactive deflections <= 0.",
        reference_solutions=reference_solutions,
        reproduced=bool(actual_forces[4] == 0 and actual_deflections[4] > 1e-8
                        and len(reference_solutions) == 1
                        and reference_solutions[0]["support_reactions_N"][4] > 0),
    )

    # Small data-contract probes, separate from the support algorithm example.
    rectangle = [dict(x_mm=x, y_mm=y, vertical_stiffness_N_mm=100)
                 for x in [-400, 400] for y in [-400, 400]]
    row = dict(instance_id="x", mass_kg=40, com_world_mm=[0, 0, 1000],
               evidence_status="measured_or_supplier_verified", source=None)
    data_probes = []
    for label, rows in [
        ("source_none", [row]), ("duplicate_instance", [row, row]),
        ("boolean_mass", [{**row, "mass_kg": True}]),
        ("boolean_com", [{**row, "com_world_mm": [True, False, True]}]),
        ("string_mass", [{**row, "mass_kg": "40"}]),
    ]:
        record = dict(case=label, input_rows=rows)
        try:
            record["output"] = evaluate(rows, rectangle)
        except Exception as error:
            record["raised"] = dict(type=type(error).__name__, message=str(error))
        data_probes.append(record)
    mass_result["additional_data_contract_probes"] = data_probes

    diff_after = git("diff", "--binary", "HEAD")
    status_after = git("status", "--short")
    result = dict(
        audit_time_utc=datetime.now(timezone.utc).isoformat(), repository=str(repo),
        revision=revision, hardware_test=False, repository_mutations_performed=False,
        tracked_diff_unchanged=diff_before == diff_after,
        git_status_before=status_before.splitlines(),
        git_status_after=status_after.splitlines(),
        finding_count=len(findings),
        reproduced_count=sum(item["reproduced"] for item in findings),
        findings=findings, scope_observations=boundary_observations,
        mass_solver_counterexample_file=str(args.mass_output.resolve()),
        mass_solver_counterexample_reproduced=mass_result["reproduced"],
        existing_tests_log=str(Path(__file__).with_name("existing_tests.log")),
        existing_tests_note="Raw unittest output is generated separately; this probe does not substitute for that run.",
    )
    for path, data in [(args.mass_output, mass_result), (args.output, result)]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Reproduced {result['reproduced_count']}/{result['finding_count']} control/test findings")
    print(f"Mass solver counterexample reproduced: {mass_result['reproduced']}")
    print(f"Tracked repository diff unchanged: {result['tracked_diff_unchanged']}")
    print(f"Results: {args.output.resolve()}")
    print(f"Mass counterexample: {args.mass_output.resolve()}")
    return 0 if all(item["reproduced"] for item in findings) and mass_result["reproduced"] and diff_before == diff_after else 1


if __name__ == "__main__":
    raise SystemExit(main())
