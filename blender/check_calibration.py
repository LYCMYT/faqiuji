import bpy,json
from mathutils import Vector
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'output/calibration'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(D/'unit_axes_cq.glb'))
obs=[o for o in bpy.context.scene.objects if o.type=='MESH']
# Observe actual imported scale before selecting the single conversion.
block=next(o for o in obs if 'BLOCK' in o.name)
raw=list(block.dimensions);factor=.001 if abs(max(raw)-100)<.01 else 1.0
for o in bpy.context.scene.objects:
    if o.parent is None:o.scale*=factor
bpy.context.view_layer.update()
assert abs(max(block.dimensions)-.1)<1e-5,(raw,list(block.dimensions))
before={o.name:{'dimensions_m':list(o.dimensions),'center_m':list(o.matrix_world.translation)} for o in obs}
bpy.ops.export_scene.gltf(filepath=str(D/'unit_axes_blender.glb'),export_format='GLB')
bpy.ops.wm.save_as_mainfile(filepath=str(D/'unit_axes.blend'))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(D/'unit_axes_blender.glb'))
after={o.name:{'dimensions_m':list(o.dimensions),'center_m':list(o.matrix_world.translation)} for o in bpy.context.scene.objects if o.type=='MESH'}
for n,v in before.items():
    assert all(abs(a-b)<1e-6 for a,b in zip(v['dimensions_m'],after[n]['dimensions_m']))
for label,idx in [('AXIS_X',0),('AXIS_Y',1),('AXIS_Z',2)]:
    o=next(o for o in bpy.context.scene.objects if label in o.name and o.type=='MESH');center=sum((o.matrix_world@Vector(v) for v in o.bound_box),Vector())/8;assert center[idx]>0
(D/'roundtrip.json').write_text(json.dumps(dict(raw_blender_block=raw,scale_applied=factor,before=before,after=after,passed=True),indent=2))
print('UNIT/DIRECTION ROUNDTRIP PASSED')
