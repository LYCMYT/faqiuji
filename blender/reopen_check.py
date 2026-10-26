import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
P={k:v['value'] for k,v in json.loads((R/'data/design.json').read_text(encoding='utf-8'))['parameters'].items()}
bpy.ops.wm.open_mainfile(filepath=str(R/'output/blend/BM1_V0_master.blend'))
sc=next(s for s in bpy.data.scenes if '装配' in s.name);bpy.context.window.scene=sc
meshes=[o for o in sc.objects if o.type=='MESH'];parts=set(o.get('part_id') for o in meshes if not o.get('reference_only'))
assert len(parts)==44
assert all(o.get('instance_id') for o in meshes)
assert len(bpy.data.scenes)>=2 and len([o for o in sc.objects if o.type=='CAMERA'])>=5
assert sc.objects.get('FIXED_HEAD_CARRIER') and sc.objects.get('MOVING_HEAD')
refs=[o for o in meshes if o.get('reference_only')];assert all(o.parent is None for o in refs)
result={'blend_reopened':True,'blend_scenes':len(bpy.data.scenes),'blend_main_items':len(parts),'blend_meshes':len(meshes),'reference_shuttle_independent':True,'materials':len(bpy.data.materials),'actions':len(bpy.data.actions)}
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'output/glb/BM1_V0_assembly.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];verts=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
bb=[min(v[k] for v in verts) for k in range(3)]+[max(v[k] for v in verts) for k in range(3)]
wheel=next(o for o in meshes if o.get('part_id')=='PRT-0505');wv=[wheel.matrix_world@Vector(v) for v in wheel.bound_box];h=(min(v.z for v in wv)+max(v.z for v in wv))/2
assert abs(h-P['head_axis_height']/1000)<1e-5
assert abs(bb[5]-(P['head_axis_height']+P['tube_bottom_z_H']+P['tube_length']+P['tube_cap_allowance'])/1000)<1e-5
assert len(set(o.get('part_id') for o in meshes))==44
result.update(glb_reopened=True,glb_meshes=len(meshes),world_bounds_m=bb,H_m=h,cap_top_m=bb[5],glb_ids_preserved=True)
(R/'reports/blender_roundtrip.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
