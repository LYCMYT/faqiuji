# Task 1 report — part roles and RFQ routes

Status: implemented and verified for RFQ engineering review only. Manufacturing release remains false. No physical measurements, supplier selections, materials, model numbers or ratings were supplied as confirmed facts.

## Changes

- Added `data/part_roles.json`: explicit ID-based role and compatible route category for every one of the 44 main items, exact source name/function snapshots from `data/parts.json`, reviewed route text, per-item engineering judgment notes, and null material/model/rating confirmation fields. This is a function/route review, not approval of a complete process or design.
- Corrected `data/r2_process_routes.json`: PRT-0402 is the pitch short trunnion and mating connections; PRT-0702 is the low ball locating clamp; PRT-0704 drives clamp holding/release; PRT-0903 is the power distribution and independent interlock function assembly. Added all-44 route categories. Other existing process choices remain candidates with their unresolved engineering notes.
- Added `tools/part_role_contract.py` and integrated it before R2 generation writes any outputs. Exact ID coverage, source drift, role/category incompatibility and unreviewed route edits fail explicitly. No route is inferred from a display name.
- R2 RFQ now includes the explicit role and route category, while supplier, material lot, cost and lead-time fields stay blank and every manufacture_released flag stays False.
- Regenerated only `output/prototype_r2/manufacturing_routes_44_RFQ.csv` and `BM1_R2_sample_manufacturing_manual.pdf` in the working checkout. All original main IDs, assembly IDs and historical R1/R2/R3 files remain unchanged.
- Added `tests/test_part_role_contract.py`, including the four D01 errors in both the route authority and actual generated RFQ, all-item source traceability, incompatible category rejection, source-function drift and unrelated role relabelling rejection.

## Actual verification

Runtime for every Python invocation: `D:/86173/Documents/BM1_V02_Engineering/.venv/Scripts/python.exe`.

- Initial RED: targeted discovery ran 4 test methods and failed 10 assertions/subtests, including all four incorrect source routes and all four incorrect generated RFQ rows, plus missing role-contract assertions. This established the existing RFQ actually contained the errors.
- Additional RED: unrelated role relabelling test failed with `ValueError not raised`; role/category compatibility table and validation then fixed that hole.
- Final targeted command: `python -m unittest discover -s tests -p 'test_part_role_contract.py' -v`: **5 tests passed**, 0.015 s, exit 0.
- Full available suite: `python -m unittest discover -s tests -v`: **26 tests passed**, 4.353 s, exit 0. The shared checkout also contained the other agents' input-immutability/provenance tests at this point; none failed.
- Inspected the R2 generator before execution: it overwrites PLAN/BLANK and CAD products. Therefore copied only data/cad/tools and the needed bench image into an isolated temporary project, ran `tools/build_r2_prototype.py` and `tools/check_r2_prototype.py` there, then copied back only RFQ/manual. Generator exit 0: 8 native STEP/DXF coupons, 72 planned samples, 44 routes. Checker exit 0: 8 STEP/DXF equivalence checks, **22 PDF pages**, 72 samples, 44 routes, no physical evidence, no text overflow. Checker emitted the existing fitz API FutureWarning.
- SHA-256 comparison confirmed **52 other existing R2 output files unchanged**, including PLAN/BLANK/evidence records. Authority data/parts.json and other authority inputs were only read.
- Rendered the manual in the isolated project; visually inspected pages 8, 10 and 11, which cover all four corrected rows. Text is legible, wrapped within cells, with no clipping. All pages also passed the checker bounds/page-count check.

## Self-review and limits

Reviewed all 44 stable IDs against source name/function and retained unresolved interface, process and material judgments. The compatibility table is an explicit engineering classification; changing a role, route, or source function requires updating the reviewed contract, rather than guessing from its label. Numeric design values in existing routes remain design inputs rather than new measurements.

This task proves static functional consistency and absence of the four RFQ route mistakes. Continuous motion, assembly constraints, structural loads, electrical stopping performance and physical prototype tests were **NOT_RUN** in this task. Supplier confirmation and material/model/rating selection remain **BLOCKED pending evidence**. Manufacturing release stays false.

The unmodified normal R2 generator still overwrites its PLAN/BLANK templates if executed directly; Task 1 avoided that risk by isolated regeneration. The broader build/evidence preservation task is owned separately. No source or evidence protection claim for the broader repository is made here.
