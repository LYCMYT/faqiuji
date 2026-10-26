"""CAD-derived Blender model, real motion hierarchy, separate explode action.
Run with portable Blender --background --python blender/build_scene.py
"""
import bpy,json,math,sys
import ast,operator
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R))
from cad.parts.cable import return_loop_points
mesh=json.loads((R/'output/mesh/model.json').read_text(encoding='utf-8'))
P={k:v['value'] for k,v in json.loads((R/'data/design.json').read_text(encoding='utf-8'))['parameters'].items()}
D=json.loads((R/'data/implementation.json').read_text(encoding='utf-8'))['demo']
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene;sc.name='BM1 | 装配与供球顺序';sc.unit_settings.system='METRIC';sc.unit_settings.length_unit='MILLIMETERS';sc.unit_settings.scale_length=1
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.studiolight_rotate_z=.5
sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.display.shading.show_object_outline=True
sc.display.shading.background_type='WORLD';sc.world=bpy.data.worlds.new('Studio World');sc.world.color=(.90,.92,.94)
sc.render.resolution_x=1400;sc.render.resolution_y=1400;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.film_transparent=False
sc.render.fps=D['fps'];sc.frame_start=1;sc.frame_end=528
groups={}
def empty(name,parent=None,z=0):
    o=bpy.data.objects.new(name,None);sc.collection.objects.link(o);o.empty_display_size=.04;o.parent=groups.get(parent);o.location.z=z;groups[name]=o;return o
empty('WORLD_STATIC');empty('FIXED_HEAD_CARRIER',z=P['head_axis_height']/1000);empty('YAW_CARRIER','FIXED_HEAD_CARRIER');empty('MOVING_HEAD','YAW_CARRIER');empty('CARRIAGE','MOVING_HEAD');empty('CLAMP_L','CARRIAGE');empty('CLAMP_R','CARRIAGE');empty('GUIDE_SLEEVE','FIXED_HEAD_CARRIER',P['guide_stroke']/1000)
for n in ['LOWER_GATE','UPPER_L','UPPER_R','CASSETTE_PIN_L','CASSETTE_PIN_R']:empty(n,'FIXED_HEAD_CARRIER')
for n,sg in [('WHEEL_LEFT',1),('WHEEL_RIGHT',-1)]:
    o=empty(n,'MOVING_HEAD');o.location.y=sg*(P['wheel_diameter']+P['wheel_gap_visual'])/2000
objs=[]; refs=[];dynamic_curves=[]
def scalar(v,slide=0):
    if not isinstance(v,str):return v
    env={**P,'slide':slide}
    def ev(n):
        if isinstance(n,ast.Constant):return n.value
        if isinstance(n,ast.Name):return env[n.id]
        if isinstance(n,ast.UnaryOp):return -ev(n.operand)
        if isinstance(n,ast.BinOp):return {ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv}[type(n.op)](ev(n.left),ev(n.right))
        raise ValueError(v)
    return ev(ast.parse(v,mode='eval').body)
def cable_points(item,slide=0):
    if 'dynamic_loop' in item:
        r=item['dynamic_loop']
        return return_loop_points(*[scalar(r[k],slide) for k in ['fixed_x','moving_x','lower_z','upper_z','y','length']],segments=64,direction=r.get('direction',-1),exit_y=r.get('exit_y'))
    return [[scalar(v,slide) for v in xyz] for xyz in item['dynamic_path']]

for item in mesh:
    verts=[Vector(v)/1000 for v in item['vertices']]
    center=sum(verts,Vector())/len(verts)
    me=bpy.data.meshes.new(item['instance_id']);me.from_pydata([v-center for v in verts],[],item['triangles']);me.update()
    o=bpy.data.objects.new(item['instance_id'],me);sc.collection.objects.link(o)
    o.parent=groups[item['parent']];o.location=center
    if item['parent'] in ('WHEEL_LEFT','WHEEL_RIGHT'):o.location-=o.parent.location
    for k in ['part_id','instance_id','assembly_id','derived_id','status','name']:o[k]=item[k]
    o['parent_frame']=item['parent'];o['source']='CadQuery native B-rep tessellation';o['cover']=item.get('cover',False);o['explosion_mm']=item['explode'];o['reference_only']=item.get('reference',False)
    rgb=[int(item['color'][j:j+2],16)/255 for j in (1,3,5)]
    mat=bpy.data.materials.new(item['instance_id']+'_material');mat.diffuse_color=(*rgb,item.get('alpha',1));mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(*rgb,1);bsdf.inputs['Metallic'].default_value=.45 if item['assembly_id'] in ['ASM-01','ASM-02','ASM-04','ASM-05'] else .08;bsdf.inputs['Roughness'].default_value=.34
    if item.get('alpha'):bsdf.inputs['Transmission Weight'].default_value=.55;bsdf.inputs['Alpha'].default_value=item['alpha'];mat.surface_render_method='DITHERED'
    o.data.materials.append(mat);o.color=mat.diffuse_color;objs.append(o)
    if item.get('reference'):refs.append(o)
    if item.get('dynamic_slide'):
        # Same data-defined nominal cable, represented as an animated bevelled polyline.
        curve=bpy.data.curves.new(item['instance_id']+'_route','CURVE');curve.dimensions='3D';curve.bevel_depth=.002;curve.bevel_resolution=3
        route=cable_points(item);spl=curve.splines.new('POLY');spl.points.add(len(route)-1)
        for pt,xyz in zip(spl.points,route):pt.co=(*[v/1000 for v in xyz],1)
        old=o;props={k:(list(v) if hasattr(v,'to_list') else v) for k,v in old.items()};parent=old.parent;old_name=old.name
        bpy.data.objects.remove(old,do_unlink=True)
        o=bpy.data.objects.new(old_name,curve);sc.collection.objects.link(o);o.parent=parent;o.location=(0,0,0)
        for k,v in props.items():o[k]=v
        curve.materials.append(mat);objs[-1]=o;dynamic_curves.append((o,item))

def camera(name,location,target,scale):
    data=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,data);sc.collection.objects.link(o);o.location=location;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=scale;return o
hero=camera('CAM_整体',(3.5,-4.5,3.1),(0,0,1.08),2.65)
core=camera('CAM_供球近景',(1.7,-2.4,2.4),(-.12,0,1.61),1.1)
camera('CAM_正视',(4,0,1.1),(0,0,1.1),2.5);camera('CAM_侧视',(0,-4,1.1),(0,0,1.1),2.5);camera('CAM_顶视',(0,0,4),(0,0,0),1.2)
sc.camera=hero
for name,loc,power,size in [('Key',(2,-3,4),1500,4),('Fill',(-2,-1,3),900,3),('Rim',(0,3,4),1800,3)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;o=bpy.data.objects.new(name,data);sc.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()

# Default scene is an inspectable loaded, sleeve-up assembly.
sc.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(R/'output/blend/BM1_V0_master.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in objs:
    if not o.get('reference_only'):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'output/glb/BM1_V0_assembly.glb'),export_format='GLB',use_selection=True,export_extras=True,export_animations=False)

# Render CAD-derived full and exposed views. Covers are hidden only for the explicitly labelled cutaway.
sc.render.filepath=str(R/'output/render/overall.png');bpy.ops.render.render(write_still=True)
for o in objs:
    if o.get('cover'):o.hide_render=True
sc.render.filepath=str(R/'output/render/cutaway.png');bpy.ops.render.render(write_still=True)
sc.camera=core;sc.render.filepath=str(R/'output/render/core.png');bpy.ops.render.render(write_still=True)
for o in objs:o.hide_render=False

# Stored mechanical demo keyframes. Real controller feedback is deliberately not simulated.
states=json.loads((R/'data/animation_keyframes.json').read_text(encoding='utf-8'))
# Bake independent world-space shuttle transforms. It stops at capture as an UNKNOWN DYNAMICS marker.
for o in refs:
    world=o.matrix_world.copy();o.parent=None;o.matrix_world=world
frozen=None
for frame,label,guide,slide,yaw,pitch,clamp,gate,upper,fall in states:
    sc.timeline_markers.new(label,frame=frame)
    groups['GUIDE_SLEEVE'].location.z=guide/1000;groups['CARRIAGE'].location.x=slide/1000
    groups['YAW_CARRIER'].rotation_euler.z=math.radians(yaw);groups['MOVING_HEAD'].rotation_euler.y=-math.radians(pitch)
    groups['CLAMP_L'].location.y=clamp/1000;groups['CLAMP_R'].location.y=-clamp/1000
    groups['LOWER_GATE'].location.x=-gate/1000;groups['UPPER_L'].location.y=upper/1000;groups['UPPER_R'].location.y=-upper/1000
    for o,item in dynamic_curves:
        for pt,xyz in zip(o.data.splines[0].points,cable_points(item,slide)):
            pt.co=(*[v/1000 for v in xyz],1);pt.keyframe_insert(data_path='co',frame=frame)
    for name in ['GUIDE_SLEEVE','CARRIAGE','CLAMP_L','CLAMP_R','LOWER_GATE','UPPER_L','UPPER_R']:groups[name].keyframe_insert(data_path='location',frame=frame)
    for name in ['YAW_CARRIER','MOVING_HEAD']:groups[name].keyframe_insert(data_path='rotation_euler',frame=frame)
    bpy.context.view_layer.update()
    if frame<=390:
        frozen=[]
        for o,item in zip(refs,[m for m in mesh if m.get('reference')]):
            vs=[Vector(v)/1000 for v in item['vertices']];center=sum(vs,Vector())/len(vs);center.z+=fall/1000
            T=groups['CARRIAGE'].matrix_world@Matrix.Translation(center);frozen.append(T.copy())
    for o,T in zip(refs,frozen):
        o.matrix_world=T;o.keyframe_insert(data_path='location',frame=frame);o.keyframe_insert(data_path='rotation_euler',frame=frame);o['capture_parent']='WORLD: frozen unknown-dynamics marker after ST09'
for n,sg in [('WHEEL_LEFT',1),('WHEEL_RIGHT',-1)]:
    o=groups[n];o.rotation_euler.z=0;o.keyframe_insert(data_path='rotation_euler',frame=1);o.rotation_euler.z=sg*2*math.pi*D['rotation_rpm']/60*(528/24);o.keyframe_insert(data_path='rotation_euler',frame=528)
for action in bpy.data.actions:
    if hasattr(action,'fcurves'):
        for fc in action.fcurves:
            for k in fc.keyframe_points:k.interpolation='LINEAR'
sc['demo_notice']=D['notice'];sc['capture_note']='ST09后球体世界坐标冻结，仅表示未知动力学；ST10是收到真实出球确认后才允许的条件复位。'
sc.camera=core;sc.frame_set(205)
bpy.ops.wm.save_as_mainfile(filepath=str(R/'output/blend/BM1_V0_master.blend'))
(R/'data/demo_states.json').write_text(json.dumps([dict(frame=s[0],label=s[1],guide=s[2],slide=s[3],yaw=s[4],pitch=s[5],clamp=s[6],gate=s[7],upper=s[8],fall=s[9]) for s in states],ensure_ascii=False,indent=2),encoding='utf-8')

# Second scene: nested exploded views are independent from assembly/motion.
bpy.ops.scene.new(type='FULL_COPY');ex=bpy.context.scene;ex.name='BM1 | 展示爆炸复原';ex.frame_end=120;ex.camera=next(o for o in ex.objects if o.type=='CAMERA' and '整体' in o.name)
for o in ex.objects:
    o.animation_data_clear()
for o in ex.objects:
    if o.type!='MESH':continue
    world=o.matrix_world.copy();o.parent=None;o.matrix_world=world;start=o.location.copy()
    o.keyframe_insert(data_path='location',frame=1);o.location=start+Vector(o.get('explosion_mm',[0,0,0]))/1000;o.keyframe_insert(data_path='location',frame=55);o.keyframe_insert(data_path='location',frame=70);o.location=start;o.keyframe_insert(data_path='location',frame=120)
ex.camera.data.ortho_scale=3.7;ex.frame_set(55);ex.render.filepath=str(R/'output/render/exploded.png');bpy.ops.render.render(write_still=True)
bpy.context.window.scene=sc;sc.frame_set(205)
# Third scene: explicit service procedure, independent of the supply sequence.
spec=json.loads((R/'data/r1_service.json').read_text(encoding='utf-8'))
bpy.ops.scene.new(type='FULL_COPY');sv=bpy.context.scene;sv.name='BM1 | R1供球组件后抽';sv.frame_end=120
carrier=next(o for o in sv.objects if o.name.startswith('FIXED_HEAD_CARRIER'))
carrier.location.z=spec['service_state']['height']/1000;bpy.context.view_layer.update()
worlds={o.name:o.matrix_world.copy() for o in sv.objects if o.type in ['MESH','CURVE']}
for o in sv.objects:
    o.animation_data_clear()
    if o.data and hasattr(o.data,'animation_data_clear'):o.data.animation_data_clear()
for o in sv.objects:
    if o.type not in ['MESH','CURVE']:continue
    o.parent=None;o.matrix_world=worlds[o.name]
    if o.get('reference_only'):o.hide_render=True;continue
    start=o.location.copy();iid=o.get('instance_id','')
    if iid in spec['pin_instances']:
        o.keyframe_insert(data_path='location',frame=1);o.location.y+=spec['pin_withdraw_mm']/1000*(1 if iid.endswith('__L') else -1);o.keyframe_insert(data_path='location',frame=30)
    elif o.get('part_id') in spec['cassette_parts'] or iid in spec['cassette_instances']:
        o.keyframe_insert(data_path='location',frame=1);o.keyframe_insert(data_path='location',frame=35);o.location.x-=spec['extract_mm']/1000;o.keyframe_insert(data_path='location',frame=90);o.keyframe_insert(data_path='location',frame=120)
sv.camera=next(o for o in sv.objects if o.type=='CAMERA' and '整体' in o.name)
sv.camera.location=(-3.5,-4.5,3);sv.camera.rotation_euler=(Vector((-.15,0,1.04))-sv.camera.location).to_track_quat('-Z','Y').to_euler();sv.camera.data.ortho_scale=2.8
sv.frame_set(90);sv.render.filepath=str(R/'output/render/R1_cassette_service.png');bpy.ops.render.render(write_still=True)
bpy.context.window.scene=sc;sc.frame_set(205)
bpy.ops.wm.save_as_mainfile(filepath=str(R/'output/blend/BM1_V0_master.blend'))
print('BLEND/GLB AND RENDERS CREATED',flush=True)
