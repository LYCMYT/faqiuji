import json,sys,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import cadquery as cq
from cad.assemblies.kinematics import parameters
from cad.export_all import locate
p=parameters();rows=json.loads((R/'data/instances.json').read_text(encoding='utf-8'));d={i['instance_id']:i for i in rows}
def shape(id):return cq.Shape.importBrep(str(R/'output/mesh'/(id+'.brep')))
wheel=shape('PRT-0505__L');feather=shape('PRT-REF-SKIRT');cork=shape('PRT-REF-CORK')
wheel_skirt=min(wheel.distance(feather.translate((q,0,0))) for q in range(0,186,2))
jaw=shape('PRT-0702__L');open_jaw=jaw.translate((165,14,0));cork_release=cork.translate((165,0,0));release_gap=open_jaw.distance(cork_release)
guide=d['PRT-0606']['local_bounds_mm'];tube=d['PRT-0601']['local_bounds_mm'];wide=d['PRT-0701-A']['local_bounds_mm'];rim=d['PRT-0505__L']['local_bounds_mm']
tests={'tube_length_mm':tube[5]-tube[2],'guide_length_mm':guide[5]-guide[2],'guide_load_bottom_H':guide[2],'guide_clear_bottom_H':guide[2]+p['guide_stroke'],'guide_clear_top_H':guide[5]+p['guide_stroke'],'wheel_width_mm':rim[5]-rim[2],'wheel_skirt_min_sampled_mm':wheel_skirt,'open_finger_cork_gap_mm':release_gap,'wide_carriage_top_H':wide[5],'inner_outer_overlap_h1800_mm':p['base_top_z']+p['outer_mast_length']-(p['head_height_max']+p['inner_mast_top_z_H']-650)}
assert abs(tests['tube_length_mm']-p['tube_length'])<.001;assert abs(tests['guide_length_mm']-p['guide_length'])<.001;assert wheel_skirt>=p['static_shuttle_margin'];assert release_gap>0;assert wide[5]<=p['cradle_structure_z_max_H']+.001
experimental=json.loads((R/'data/design.json').read_text(encoding='utf-8'))['experimental'];assert all(experimental[k] is None for k in ['rpm_limits','motor_electrical_ratings','wheel_gap_effective','feather_clearance_dynamic','capacity_verified']);assert experimental['landing_calibration']==[]
assert json.loads((R/'data/measured_calibration.json').read_text(encoding='utf-8'))['shots']==[]
tests.update(passed=True,scope='sampled concept geometry only; not dynamic feather or manufacturing clearance',experimental_nulls_preserved=True)
(R/'reports/dimension_validation.json').write_text(json.dumps(tests,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(tests))
