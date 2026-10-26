# BM1 V0.2 engineering implementation

Spec: ../input/BM1_Design_V0_2/docs/CODEX_TASK.md and the user's explicit A-F request.
Architecture: data-only constructive solid geometry recipes evaluated by CadQuery; one kinematic tree; tessellated CAD solids passed to Blender in metres; local viewer uses the exported GLB. No external CAD geometry reused.

- [x] A Inputs read and hashes recorded; 100 mm and signed-axis exchange checks passed.
- [x] B Native wheel/frame/carriage/finger solids built; release-before-capture interlock tested. Post-capture dynamics remains unvalidated.
- [x] C Fixed feeder, tube, gate, sleeve and 115 mm stroke modeled. Real nested shuttle stack remains unvalidated.
- [x] D Base, columns, yaw/pitch and nominal wires modeled; collision and conditional service paths checked. Cable length/bend, tools, stability and convenient refill remain open.
- [x] E Materials, 150-page book (44 main + 70 derived independent pages), animations and local viewer generated. Feed animation stops at capture boundary.
- [x] F STEP/GLB/BLEND reopened; two full parameter variants rebuilt; PDF reviewed; acceptance report generated. Delivery ZIP integrity is checked by tools/package_delivery.py.

These marks record execution and evidence delivery, not production approval. See reports/acceptance_report.md and reports/open_issues.md for unresolved engineering requirements; U01-U10 remain open.

Global constraints: millimetres in CAD, Z up, H at axis height; positive pitch about -Y; data/ authoritative; original IDs; null experimental values preserved; no manufacturing/safety/performance certification.
Review focus: forbidden skirt-wheel collision; feeder follows height only; real release geometry; captured shuttle not attached to carriage; dimensions and object counts survive exchanges.

Files: cad/parts/recipe.py (native CSG), cad/assemblies/kinematics.py (transforms/interlocks), cad/export_all.py (exports); blender/build_scene.py; tools/build_book.py; tools/validate.py; viewer/index.html.
Validation: tests/test_contract.py plus reports with actual geometry intersections and reopened output measurements. Project is a new isolated artifact directory, not an existing git branch. No deployment.
