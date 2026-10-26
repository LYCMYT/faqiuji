"""Rebuild from current data only. NEVER run seed/refine scripts here."""
import os,sys,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
blender=os.environ.get('BM1_BLENDER_EXE') or shutil.which('blender')
if not blender:
    candidates=list((R/'tools/blender').glob('*/blender.exe'));blender=str(candidates[0]) if candidates else None
if not blender:raise SystemExit('Blender 4.5.9 LTS not found. Set BM1_BLENDER_EXE to blender.exe path; see README_DELIVERY.md.')
def py(script,*args):subprocess.run([sys.executable,str(R/script),*args],cwd=R,check=True)
def bl(script):subprocess.run([blender,'--background','--python',str(R/script)],cwd=R,check=True)
py('tools/calibration.py');bl('blender/check_calibration.py');py('cad/export_all.py')
py('tools/check_dimensions.py');py('tools/check_collisions.py','static');py('tools/check_collisions.py','motion');py('tools/check_service.py');py('tools/check_r1_service.py');py('tools/check_r1_contracts.py');py('tools/make_section.py');py('tools/enrich_metadata.py')
bl('blender/build_scene.py');bl('blender/reopen_check.py');bl('blender/render_animation.py');py('tools/encode_animations.py')
py('tools/build_book.py');py('tools/check_pdf.py');py('tools/validate_outputs.py');py('tools/check_parameter_rebuild.py');py('tools/build_r1_engineering_package.py');py('tools/build_r1_manual.py');py('tools/check_viewer_isolated.py');py('tools/final_report.py')
with (R/'reports/r1_review_green.log').open('w',encoding='utf-8') as log:
    subprocess.run([sys.executable,'-m','unittest','discover','-s','tests'],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
py('tools/check_r1_delivery.py')
py('tools/build_r2_prototype.py');py('tools/check_r2_prototype.py')
py('tools/check_r3_geometry.py');py('tools/build_r3_package.py');bl('blender/build_r3_scene.py');py('tools/build_r3_manual.py');py('tools/finish_r3_delivery.py');py('tools/check_r3_viewer.py')
print('Rebuild complete. Read reports/acceptance_report.html for limitations and failures.')
