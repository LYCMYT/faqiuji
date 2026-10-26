"""Render R3 native-CAD meshes, export and reopen BLEND/GLB."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];O=R/'output/fixture_r3';P=json.loads((R/'data/r3_presentation.json').read_text(encoding='utf-8'));rows=json.loads((O/'mesh.json').read_text(encoding='utf-8'))
bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.name='R3装配与连接件分解';sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=1
sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=P['resolution'][0];sc.render.resolution_y=P['resolution'][1];sc.render.resolution_percentage=100
sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.display.shading.background_type='WORLD';sc.world=bpy.data.worlds.new('R3 world');sc.world.color=(.88,.92,.94)
sc.render.fps=P['fps'];sc.frame_start=1;sc.frame_end=P['duration_frames'];mats={}
for a in rows:
    me=bpy.data.meshes.new(a['instance_id']);me.from_pydata([[x/1000 for x in v] for v in a['vertices']],[],a['triangles']);me.update();o=bpy.data.objects.new(a['instance_id'],me);sc.collection.objects.link(o)
    for key in ['instance_id','family','part_id','assembly_id','kind','parent']:o[key]=a[key]
    if a['color'] not in mats:
        c=a['color'];mat=bpy.data.materials.new(c);mat.diffuse_color=tuple(int(c[j:j+2],16)/255 for j in (1,3,5))+(1,);mats[c]=mat
    me.materials.append(mats[a['color']]);centers=[(a['bounds_mm'][j]+a['bounds_mm'][j+3])/2 for j in range(3)]
    kind='jaw' if '0603-R3' in a['instance_id'] else 'foot' if 'FOOT' in a['instance_id'] else a['kind'] if a['kind'] in P['explode_mm'] else 'context'
    ex=P['explode_mm'][kind].copy()
    if ex[1] and centers[1]<0:ex[1]=-ex[1]
    if a['instance_id']=='PRT-0602-R3-BASE':ex=[0,0,0]
    for frame,factor in [(1,0),((P['duration_frames']+1)//2,1),(P['duration_frames'],0)]:
        o.location=[v*factor/1000 for v in ex];o.keyframe_insert('location',frame=frame)
camd=bpy.data.cameras.new('R3 Camera');cam=bpy.data.objects.new('R3 Camera',camd);sc.collection.objects.link(cam);target=Vector(P['camera_target_m']);cam.location=target+Vector(P['camera_offset_m']);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camd.type='ORTHO';camd.ortho_scale=P['ortho_scale_m'];sc.camera=cam
sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(O/'BM1_R3_fixture.blend'))
bpy.ops.export_scene.gltf(filepath=str(O/'BM1_R3_fixture.glb'),export_format='GLB',export_animations=False,export_extras=True)
(O/'frames').mkdir(exist_ok=True)
if '--export-only' not in sys.argv:
    for frame in range(1,P['duration_frames']+1,P['render_sample_step']):
        sc.frame_set(frame);sc.render.filepath=str(O/'frames'/f'{frame:04d}.png');bpy.ops.render.render(write_still=True)
    sc.frame_set(1);sc.render.filepath=str(O/'R3_assembly.png');bpy.ops.render.render(write_still=True)
    sc.frame_set((P['duration_frames']+1)//2);sc.render.filepath=str(O/'R3_exploded.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.open_mainfile(filepath=str(O/'BM1_R3_fixture.blend'));assert len([o for o in bpy.context.scene.objects if o.type=='MESH'])==len(rows)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(O/'BM1_R3_fixture.glb'));meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(meshes)==len(rows);assert {o.get('instance_id') for o in meshes}=={a['instance_id'] for a in rows}
vertices=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box];bounds=[min(v[k] for v in vertices) for k in range(3)]+[max(v[k] for v in vertices) for k in range(3)]
expected=[min(a['bounds_mm'][k] for a in rows)/1000 for k in range(3)]+[max(a['bounds_mm'][k] for a in rows)/1000 for k in range(3,6)]
assert all(abs(a-b)<1e-5 for a,b in zip(bounds,expected)),(bounds,expected)
(R/'reports/r3_blender_validation.json').write_text(json.dumps(dict(blend_reopened=True,glb_reopened=True,meshes=len(meshes),ids_preserved=True,bounds_m=bounds,expected_bounds_m=expected),indent=2),encoding='utf-8');print('R3 BLEND/GLB REOPEN PASS',len(meshes))
