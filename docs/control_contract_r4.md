# R4 offline command and cycle contract

No hardware adapter, clock synchronization, debounce, communication delay or real stopping capability is implemented. All acceptance/completion evidence below is simulated.

Positional states CLEAR, AIM, RETREAT, HOME and LOAD expose one immutable command with command_id, cycle_id, action, target and issued_at (simulation elapsed seconds). AIM currently commands the simulator's zero-angle target; arbitrary aiming is not implemented. Actuator pneumatic transitions continue to require their strict physical observations.

step(observation, dt, ack=...) accepts acknowledgements containing cycle_id, accepted_id, completed_id, actual_position, in_tolerance and integer sample_id. A matching fresh acceptance must precede a later fresh completion sample for the same command and cycle. Completion additionally requires numeric finite actual_position exactly equal to the target and literal boolean in_tolerance=True. Exact equality is a conservative offline policy; hardware tolerances remain BLOCKED pending selection/tests. Physical arrival feedback remains required but cannot substitute for command completion. A target already reached, including zero-angle HOME with head_home=True throughout, completes through acceptance then completion without moving away to manufacture an edge. Old identities, repeated samples, cross-cycle acknowledgements and wrong positions cannot advance a state. Sample ordering is command-scoped; identities isolate commands and cycles.

A new or recreated object starts disarmed IDLE. It requires explicit restart() followed by a separate start input to begin one cycle. Persistent start=True alone cannot start a recreated controller. DONE stays DONE even with start=True. No continuous scheduling exists. pause() abandons the current cycle and enters PAUSED; it does not resume in place. trip() latches FAULT; pause and ordinary samples cannot clear FAULT. reset() is valid only from PAUSED/FAULT/DONE, clears the latch to unarmed IDLE, and issues no command. restart() is valid only from IDLE and creates a new cycle identity/arms the explicit start request; it does not itself advance or launch. Unknown step stop/reset keywords are rejected by Python, and invalid reset/restart state raises ValueError. No reconnect routine exists and restart/reconnect must never replay a stored start request; the adapter is a separate BLOCKED stage.

Stopped output includes actuator-specific requested safe intent, never a claim of verified safety:

| Actuator | Pause/fault requested intent | Capability evidence |
|---|---|---|
| Upper retainer | Hold remaining stack | BLOCKED: retention under loss of energy unknown |
| Lower gate | Controlled close | BLOCKED: closing clearance/energy unknown |
| Guide | Hold position | BLOCKED: gravity/backdrive restraint unknown |
| Slide | Controlled stop then hold | BLOCKED: braking distance/load capability unknown |
| Catch clamp | Hold current state | BLOCKED: retained ball/drop consequences unknown |
| Future wheel group | Controlled deceleration | BLOCKED: drive/brake/coast behavior unknown |

These are coordinated engineering requirements for a future hardware adapter. They are not emitted to GPIO or a drive. enable_motion=False and enable_wheels=False only disable simulated active targets. All per-actuator stopped intents remain BLOCKED until mechanics and hardware tests establish a usable stopping procedure.
