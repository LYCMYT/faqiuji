# R1 independent review and regression ledger

Read-only reviewer: /root/final_review. Seven substantive findings fixed in one implementation pass; no deferred findings.

1. P1 upper jaw opened while lower gate was still closing. Fixed: retain through GATE_CLOSE and fault on lost retention. `test_upper_retained_until_gate_closed` RED→GREEN.
2. P1 missing exit input interpreted as a falling edge. Fixed: explicit bool input required; missing/invalid values latch fault. `test_missing_exit_is_not_a_falling_edge` RED→GREEN.
3. P1 old position feedback skipped retreat/home. Fixed: each commanded arrival requires observed low then high; full-cycle input trace now represents physical departure and new arrival. `test_old_position_feedback_cannot_skip_return` RED→GREEN.
4. P1 wheel-ready and held-ball feedback not continuously monitored. Fixed: required feedback remains active across relevant phases. `test_feedback_loss_stops_active_cycle` RED→GREEN.
5. P2 nonphysical support stiffness yielded plausible forces. Fixed: finite positive stiffness/gravity and finite coordinates required. `test_nonphysical_supports_rejected` RED→GREEN.
6. P2 absent capture geometry enabled approach and could crash checker. Fixed: cycle faults on missing tangency; checker records unsupported capture geometry. `test_uncapturable_geometry_is_explicit` RED→GREEN.
7. P2 service check used nominal-height dynamic wire. Fixed: state-dependent geometry rebuilt for service pose, including H1400 mast wire. `test_service_dynamic_wire_uses_requested_height` RED→GREEN.

Evidence: reports/r1_review_red.log (6 failures + 1 error before fixes), reports/r1_review_green.log (18/18 passed), r1_contract_validation.json, refreshed r1_service_validation.json. Regression success does not certify hardware or actual ball motion.
