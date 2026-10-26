# R4 low-speed mechanical candidate review

This revision is a **standalone low-speed fixture candidate**, at local H height=0. It is not a whole-machine wheel-clearance check, a load rating, a physical ball compatibility result, or a manufacturing release. Original R1/R2/R3 sources and audit evidence remain unchanged. Stable PRT/ASM IDs are retained; changed bodies carry R4 derived families. Extra derived hardware is permitted and indexed from the actual model.

## Receiving datum and alternatives

M01 and `reports/r4_baseline_support.json` reproduce the R3 counterexample: nominal cork bottom at design `cork_z_min`, axis X=load_x, front-only support whose nearest X edge is load_x+5.5. The gravity projection lies outside that contact. A 1° rotation about that edge descends without meaningful obstruction in R3.

R4 retains a machined integral central land in the original cradle slot: X=load_x−12 to load_x+5.5, Y=±7, Z=−16 to cork bottom −13 mm for current design. The native exact bottom-face contact contains the nominal axis. The regression test rotates the cork about the original failing edge and confirms that this descending mode now intersects the land. Free reference perturbations are transformed independently of any animation parent. Lateral free probes remain reported: the land alone does not prove frictional centering, impact settling, skirt stability, or real-ball compatibility.

Three manufacturable choices are recorded in `data/r4_fixture.json`: integral low land (selected), independently retractable fork, and shallow pocket. The integral land avoids a sixth action and loose shim, is directly measurable, and leaves the current nominal jaw travel clear. A pocket would prematurely fix an unmeasured cork profile; a retractable fork adds guide/holding/interlock cost. No measured cost or ball radius is invented. Full nominal fixture movement checks assess the selected land; wheel-region compatibility remains outside this bench scope.

## Native independent manual functions

| Function | Native guide and stops | Assembly / reaction path |
|---|---|---|
| Upper retainers | Two Y shafts per carrier, paired bored bushes, collar stops at 0/24 mm; manual endpoint pins through shaft holes | Split bush caps, four candidate M3 bolts/nuts per cap; integral web/bridge into original side410 brackets, frame and base |
| Lower gate | Paired X shafts, collar stops at 0/85 mm; manual endpoint lock pin | Rear ribs fit the original 66 mm tube slot; outboard split bushes and explicit wall aperture; custom bridge into rear wall and frame |
| Guide sleeve | Rectangular Z tongue, back web/side walls/front lips, lower stop and detachable upper stops at 0/115 mm; positive crosspin at either endpoint | Explicit narrow neck clears lips; tongue seats in custom way; way/bracket face at Z271 requires detailed welded/fastened process |
| Receiving slide | Paired carriage flanges inside C ways, rear stop and removable front stops at 0/185 mm; endpoint pins | Front stops detach via candidate M2 screws for flange insertion; revised shoe pockets clear channels; rail/posts/base carry reaction |
| Receiving gripper | Rear arm extensions, captured rear/top/bottom channels, travel slots and stepped pins with separate candidate M4 lower nuts; endpoint pins | Symmetric crossbeam retains original cradle mating faces; candidate pin and slot/channel reaction into cradle, carriage and rail |

The slide interface was corrected from an initial 210 mm transcription to the authoritative current design stroke of 185 mm. These are actual custom native parts and bores, not imagined supplier interfaces. Actuator supplier, force, measured friction, fastening grade/preload, pin detent/tether and strength remain unknown. The pins provide an inspectable nominal holding topology; a collision-free installed pin is not a rated lock. Support the member manually before withdrawing its pin. Unattended or powered operation remains blocked.

## Conflicts found and explicit revisions

1. An initial upper web missed the actual side410 bracket material (its bounding box overstated the solid). The bridge now reaches the actual Y65–70 material. Single-solid tests catch a disconnected bridge.
2. Added slide channels initially intersected two existing shoes. Explicit R4 pockets remove the interfering upper/inner strips; remaining shoe load capacity is OPEN.
3. Initial front gate ears crossed the tube's retained side ligaments at gate travel 10–60 mm. They were replaced by rear ribs within the original slot and outboard bushes. The tube was not enlarged, hidden, or shrunk.
4. Integral shaft collars would make closed bushes unassemblable. Upper and gate bushes now have separate caps and candidate screws/nuts.
5. Captive slide flanges and sleeve tongue need real insertion routes. Front slide stops and upper sleeve stops now detach as separate parts; neither is silently omitted from the operational model.
6. A 3 mm thick sleeve stop was split by a 3.4 mm screw bore. It was thickened to 6 mm and rechecked as one solid.
7. Clamp pin bottom collars were initially integral and conflicted with original crossbeam material. They now use separate candidate M4 lower nuts and explicit clearance pockets.
8. A parked slide endpoint pin initially intersected a support shoe. Its actual locking station moved to X=−205/−20, preserving 185 mm travel and avoiding the shoe.

## Checks and their limits

The full checker samples each named manual path with explicit start/end states and checks **all fixture context-context pairs**, using exact native intersections after broad phase. It reports working motion, independent free reference perturbations, planar contact projection, native connectivity/endpoint fits, pin installed fits, and tool channels separately. It does not prove continuous swept-volume clearance or arbitrary simultaneous combinations. The movement includes open load, close, sleeve retract, clear/withdraw, release opening, final empty slide travel and empty return. No ball flight/settling dynamics are inferred from a posed reference.

Upper M4 service tooling is checked after an explicit empty, supported sequence: remove manual hold pins and cap fasteners/caps, lift the upper assembly 6 mm, then withdraw from work opening 24 mm to service opening 40 mm. The remaining native parts stay in the model. The nominal lifted/withdrawn path and four specified M4 straight tool envelopes are checked. The cap/fastener withdrawal routes, new M3/M2 tool envelopes, pin detents and full human hand/wrench access are still NOT_RUN. This is why the overall mechanical report remains BLOCKED even if collision and original M4 tool arrays are empty.

`tools/build_r4_package.py` exports the actual assembly, every actual derived family and optional jaw family, two native Boolean sections, mesh and previews. Expected STEP paths are computed before writing, all exported STEP files reopen as valid native solids, and STEP/index/mesh hashes are included in the independent export-stage report. Successful export does not upgrade mechanical approval.

## Required review inputs

The question list in `data/r4_mechanical_interfaces.json` covers actual ball envelopes and settling, guide/lock force and stiffness, upper cap assembly/tool access, sleeve way attachment process and gravity holding, clamp pin edge distance and thread/preload, thin gate-rib bending, and table/anchor capacity. Original actuator drawings are needed for any future powered adapter; the current manual candidate does not require fabricated vendor hole dimensions. All physical measurements and suppliers remain null/empty until supplied or measured.
