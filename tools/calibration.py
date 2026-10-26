"""Deliberately independent 100 mm unit and three signed axis artifacts."""
from pathlib import Path
import cadquery as cq,json
R=Path(__file__).resolve().parents[1];D=R/'output/calibration';D.mkdir(parents=True,exist_ok=True)
a=cq.Assembly(name='BM1_units_axes')
shapes={'BLOCK_100mm':cq.Workplane().box(100,100,100).val(),'AXIS_X_200':cq.Workplane().box(200,5,5).translate((150,0,0)).val(),'AXIS_Y_300':cq.Workplane().box(5,300,5).translate((0,200,0)).val(),'AXIS_Z_400':cq.Workplane().box(5,5,400).translate((0,0,250)).val()}
for n,s in shapes.items():a.add(s,name=n)
a.export(str(D/'unit_axes.step'));a.export(str(D/'unit_axes_cq.glb'))
back=cq.importers.importStep(str(D/'unit_axes.step')).val()
assert len(back.Solids())==4
(D/'cad_check.json').write_text(json.dumps({'step_solids':4,'block_mm':[100,100,100],'cq_glb_note':'CadQuery exports mm-scale coordinates with Y-up transform; Blender adapter checks and converts exactly once.'},indent=2))
print('Calibration STEP/GLB exported')
