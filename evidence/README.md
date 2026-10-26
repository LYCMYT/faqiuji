# R4 evidence ownership

Design inputs remain in data/. Raw supplier, sample and hardware records belong in evidence/suppliers/, samples/ and runs/. No real records have been supplied. Builds must not write either tree. PLAN/BLANK output is a template, not measurement evidence.

Each real record needs ID, source, acquisition date/person, hardware/sample revision, pose, units, file location, size and SHA-256. Corrections are separate revisions; do not overwrite raw records. External large files may be indexed. A caller-provided verified string is not evidence.

Historical instances/demo_states/animation_keyframes/page_index/deliverable/document_validation/bom files in data are immutable R1-R3 snapshots. New generated versions go to output/generated_metadata. Explicit legacy fallback emits a warning, and cannot prove a new run. Materials/contact rules/interfaces/exploded module definitions/viewshots remain authoritative. Display copies, instance mappings, exploded offsets, page metadata and animation samples are derived. Default initialization is explicit and exclusive-create only.
