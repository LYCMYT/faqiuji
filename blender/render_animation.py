"""Render both real Blender actions at 6 sampling frames/s; encode separately.
The source animation remains 24 fps and can be rendered at full sampling.
"""
import bpy,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(R/'output/blend/BM1_V0_master.blend'))
for prefix,match,step in [('feed','装配',4),('explode','爆炸',4),('service','后抽',4)]:
    sc=next(s for s in bpy.data.scenes if match in s.name);bpy.context.window.scene=sc
    sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=960;sc.render.resolution_y=720;sc.render.resolution_percentage=100
    folder=R/'output/animation'/prefix;folder.mkdir(exist_ok=True)
    if prefix=='feed':
        for o in sc.objects:
            if o.type=='MESH' and o.get('cover'):o.hide_render=True
    for idx,f in enumerate(range(1,sc.frame_end+1,step)):
        sc.frame_set(f);sc.render.filepath=str(folder/f'{idx:04d}.png');bpy.ops.render.render(write_still=True)
    print('RENDERED',prefix,flush=True)
