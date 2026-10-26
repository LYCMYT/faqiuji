"""R3 native fixture variant; dimensions originate in data/, no supplier hole guesses."""
from pathlib import Path
import json,copy,math
import cadquery as cq
from cad.parts.recipe import build
from cad.export_all import locate,exact_bbox
R=Path(__file__).resolve().parents[2]
def read(p):return json.loads((R/p).read_text(encoding='utf-8'))

def model():
    s=read('data/r3_fixture.json');b=read('data/r1_testbench.json');h=s['hardware'];rows=[]
    p={k:v['value'] for k,v in read('data/design.json')['parameters'].items()}
    for a in read('data/parts.json'):
        for axis,v in zip('xyz',a['bbox_mm']):p[a['part_id'].replace('PRT-','P')+'_'+axis]=v
    p['wheel_center_y']=(p['wheel_diameter']+p['wheel_gap_visual'])/2;p['slide']=0
    def box(size,at):return cq.Workplane('XY').box(*size).val().translate(tuple(at))
    def cyl(d,length,at,axis=(0,0,1)):
        return cq.Solid.makeCylinder(d/2,length,cq.Vector(*[a-length*v/2 for a,v in zip(at,axis)]),cq.Vector(*axis))
    def hole(shape,d,at,axis=(0,0,1),length=None):
        bb=exact_bbox(shape);length=length or max(bb.xlen,bb.ylen,bb.zlen)*2
        return shape.cut(cyl(d,length,at,axis))
    def add(id,shape,family=None,parent='FIXED_HEAD_CARRIER',kind='custom',holes=None,material='6061-T651',**extra):
        assert shape.isValid() and shape.Volume()>0,id
        rows.append(dict(instance_id=id,family=family or id,part_id=id[:8],assembly_id='ASM-'+id[4:6],parent=parent,kind=kind,holes=holes or [],material=material,shape=shape,**extra));return rows[-1]
    def nut(d,af,height,at):
        poly=cq.Workplane('XY').polygon(6,af/math.cos(math.pi/6)).extrude(height).val().translate((at[0],at[1],at[2]-height/2))
        return hole(poly,d,at)
    def washer(at):return cyl(h['washer_M6_OD'],h['washer_M6_t'],at).cut(cyl(h['washer_M6_ID'],h['washer_M6_t']*2,at))
    def stack(id,x,y,rod_bottom,rod_length,bottom_washer_bottom,top_washer_bottom):
        prefix=id[:8];family=f'{prefix}-R3-ROD-M6-L{rod_length}'
        add(id+'-ROD',cyl(h['rod_diameter'],rod_length,[x,y,rod_bottom+rod_length/2]),family,kind='hardware',material='M6全螺纹杆，等级待定',fastener_axis=[x,y],rod_z=[rod_bottom,rod_bottom+rod_length])
        for tag,z,up in [('LOW',bottom_washer_bottom,False),('UP',top_washer_bottom,True)]:
            add(id+'-WASHER-'+tag,washer([x,y,z+h['washer_M6_t']/2]),prefix+'-R3-WASHER-M6',kind='hardware',material='金属垫圈，实际材质待定')
            nz=z+h['washer_M6_t']+h['nut_M6_height']/2 if up else z-h['nut_M6_height']/2
            add(id+'-NUT-'+tag,nut(h['nut_M6_envelope_bore'],h['nut_M6_AF'],h['nut_M6_height'],[x,y,nz]),prefix+'-R3-NUT-M6',kind='hardware',material='M6螺母，等级/防松待定',engagement_z=[nz-h['nut_M6_height']/2,nz+h['nut_M6_height']/2],rod_id=id+'-ROD')
    holes=[]
    # Source body is retained at its exact coordinates and thickness.
    base=build(b['fixture_instances'][0]['shape'],p);bb=exact_bbox(base)
    arm=s['arm_clamps'];post=s['rail_posts'];feet=s['feet'];anchor=s['anchors']
    for x in arm['x']:
        for y in arm['y']:
            for sign in [-1,1]:holes.append(dict(x=x,y=y+sign*arm['bolt_dy'],diameter=h['clearance_M6'],purpose='筒架压板拉杆'))
    for x in post['bolt_x']:
        for y in post['bolt_y']:holes.append(dict(x=x,y=y,diameter=h['clearance_M6'],purpose='滑台支柱拉杆'))
    for x in feet['x']:
        for y in feet['y']:holes.append(dict(x=x,y=y,diameter=h['clearance_M6'],purpose='支脚穿杆'))
    for x in anchor['x']:
        for y in anchor['y']:holes.append(dict(x=x,y=y,diameter=anchor['hole_diameter'],purpose='台面锚固预留'))
    for a in holes:base=hole(base,a['diameter'],[a['x'],a['y'],(bb.zmin+bb.zmax)/2])
    add(s['base_id'],base,holes=holes,source='R1基板+R3孔表')
    for xi,x in enumerate(arm['x']):
        for yi,y in enumerate(arm['y']):
            suffix=f'{xi}{yi}';hs=[dict(x=x,y=y+sign*arm['bolt_dy'],diameter=h['clearance_M6'],purpose='M6通孔') for sign in [-1,1]]
            for typ,key,zkey in [('PED','pedestal_size','pedestal_z'),('STRAP','strap_size','strap_z')]:
                sh=box(arm[key],[x,y,arm[zkey]])
                for a in hs:sh=hole(sh,a['diameter'],[a['x'],a['y'],arm[zkey]])
                add('PRT-0602-R3-'+typ+'-'+suffix,sh,'PRT-0602-R3-'+typ,holes=hs)
            for n,a in enumerate(hs):stack('PRT-0602-R3-ARMFAST-'+suffix+str(n),a['x'],a['y'],**{k:arm[k] for k in ['rod_bottom','rod_length','bottom_washer_bottom','top_washer_bottom']})
    for n,(x,bx) in enumerate(zip(post['x'],post['bolt_x'])):
        sh=box(post['tube_size'],[x,0,post['tube_z']]);inner=[post['tube_size'][0]-2*post['tube_wall'],post['tube_size'][1]-2*post['tube_wall'],post['tube_size'][2]+2*post['tube_wall']]
        sh=sh.cut(box(inner,[x,0,post['tube_z']]))
        add(f'PRT-0703-R3-TUBE-{n}',sh,'PRT-0703-R3-TUBE',material='矩形金属管/自制空心柱，材料批次待确认')
        hs=[dict(x=bx,y=y,diameter=h['clearance_M6'],purpose='M6拉杆通孔') for y in post['bolt_y']]
        for tag,zkey in [('LOW','bottom_cap_z'),('UP','top_cap_z')]:
            sh=box(post['cap_size'],[x,0,post[zkey]])
            for a in hs:sh=hole(sh,a['diameter'],[a['x'],a['y'],post[zkey]])
            add(f'PRT-0703-R3-CAP-{n}-{tag}',sh,f'PRT-0703-R3-CAP-{n}',holes=hs)
        for side,y in enumerate(post['bolt_y']):
            sign=1 if y>0 else -1;out=post['shoe_outer_y'];inn=post['shoe_inner_y'];oz=post['shoe_outer_z'];iz=post['shoe_inner_z']
            sh=box([post['shoe_size_x'],out[1]-out[0],oz[1]-oz[0]],[bx,sign*sum(out)/2,sum(oz)/2]).fuse(box([post['shoe_size_x'],inn[1]-inn[0],iz[1]-iz[0]],[bx,sign*sum(inn)/2,sum(iz)/2])).clean()
            sh=hole(sh,h['clearance_M6'],[bx,y,sum(oz)/2])
            sh=sh.cut(cyl(post['shoe_nut_recess_diameter'],post['shoe_nut_recess_depth'],[bx,y,oz[1]-post['shoe_nut_recess_depth']/2]))
            hs2=[dict(x=bx,y=y,diameter=h['clearance_M6'],counterbore_diameter=post['shoe_nut_recess_diameter'],counterbore_depth=post['shoe_nut_recess_depth'],purpose='侧压爪通孔；上方开边圆形螺母/工具凹台')]
            add(f'PRT-0703-R3-SHOE-{n}-{side}',sh,f'PRT-0703-R3-SHOE-{side}',holes=hs2)
            stack(f'PRT-0703-R3-POSTFAST-{n}-{side}',bx,y,**{k:post[k] for k in ['rod_bottom','rod_length','bottom_washer_bottom','top_washer_bottom']})
    for xi,x in enumerate(feet['x']):
        for yi,y in enumerate(feet['y']):
            sh=box(feet['size'],[x,y,feet['z']]).cut(box(feet['window_size'],[x,y,feet['window_z']]))
            sh=hole(sh,h['clearance_M6'],[x,y,feet['z']]);hs=[dict(x=x,y=y,diameter=h['clearance_M6'],purpose='M6穿杆；侧窗放入螺母及垫圈')]
            add(f'PRT-0602-R3-FOOT-{xi}{yi}',sh,'PRT-0602-R3-FOOT',holes=hs)
            stack(f'PRT-0602-R3-FOOTFAST-{xi}{yi}',x,y,**{k:feet[k] for k in ['rod_bottom','rod_length','bottom_washer_bottom','top_washer_bottom']})
    # All original bench bodies remain, with two explicitly revised wall openings.
    jaw=s['jaw'];originals=read('data/geometry.json')['instances']
    for a in originals:
        if a['part_id'] not in b['include_parts'] or a.get('reference') or a['part_id']=='PRT-0603':continue
        sh=build(a['shape'],p)
        if a['derived_id']=='PRT-0602-F':
            sign=1 if a['instance_id'].endswith('1') and not a['instance_id'].endswith('-1') else -1
            # Wall center is source geometry, not an invented supplier interface.
            wall_y=a['shape']['children'][0]['at'][1]
            sh=sh.cut(box(jaw['side_window_size'],[p['load_x'],wall_y,jaw['side_window_z']]))
            add('PRT-0602-R3-WALL-'+str(sign),sh,parent=a['parent'],source_instance=a['instance_id'],kind='revised_context')
        else:add(a['instance_id'],sh,parent=a['parent'],kind='context',material='沿用R1候选',source_instance=a['instance_id'],dynamic_slide=a.get('dynamic_slide',False),dynamic_height=a.get('dynamic_height',False),recipe=a['shape'])
    for sign,side in [(1,'L'),(-1,'R')]:
        parent='UPPER_'+side
        sh=box(jaw['carrier_size'],[p['load_x'],sign*jaw['carrier_y_abs'],jaw['carrier_z']])
        sh=sh.cut(cyl(jaw['carrier_tube_relief_radius']*2,jaw['carrier_size'][2]*2,[p['load_x'],0,jaw['carrier_z']]))
        hs=[dict(x=p['load_x'],y=sign*y,diameter=jaw['through_diameter'],purpose='夹块穿透连接') for y in jaw['hole_y_abs']]
        for a in hs:sh=hole(sh,a['diameter'],[a['x'],a['y'],jaw['carrier_z']])
        sh=hole(sh,jaw['pin_hole_diameter'],[p['load_x'],sign*jaw['pin_y_abs'],jaw['carrier_z']],axis=(1,0,0))
        hs.append(dict(x=p['load_x'],y=sign*jaw['pin_y_abs'],z=jaw['carrier_z'],diameter=jaw['pin_hole_diameter'],axis='X',purpose='自定义执行连接销孔；适配件待冻结'))
        add('PRT-0603-R3-CARRIER-'+side,sh,parent=parent,holes=hs)
        for n,y in enumerate(jaw['hole_y_abs']):
            y*=sign;uz=jaw['screw_underhead_z'];head=cyl(h['screw_M4_head_d'],h['screw_M4_head_h'],[p['load_x'],y,uz+h['screw_M4_head_h']/2])
            socket=cq.Workplane('XY').polygon(6,h['screw_M4_socket_AF']/math.cos(math.pi/6)).extrude(h['screw_M4_socket_depth']).val().translate((p['load_x'],y,uz+h['screw_M4_head_h']-h['screw_M4_socket_depth']))
            head=head.cut(socket);shaft=cyl(h['screw_M4_d'],h['screw_M4_L'],[p['load_x'],y,uz-h['screw_M4_L']/2])
            add(f'PRT-0603-R3-SCREW-{side}{n}',head.fuse(shaft),'PRT-0603-R3-SCREW-M4x25',parent=parent,kind='hardware',material='M4x25钢制内六角螺钉，实际等级待确认')
            nz=jaw['carrier_z']-jaw['carrier_size'][2]/2-h['nut_M4_height']/2
            add(f'PRT-0603-R3-NUT-{side}{n}',nut(h['nut_M4_envelope_bore'],h['nut_M4_AF'],h['nut_M4_height'],[p['load_x'],y,nz]),'PRT-0603-R3-NUT-M4',parent=parent,kind='hardware',material='M4金属螺母，防松方式待验证')
    variants=[]
    radii=read('data/r1_engineering.json')['separator']['pad_radius_candidates_mm']
    for radius in radii:
        for a in [a for a in originals if a['part_id']=='PRT-0603']:
            side=a['instance_id'].split('__')[-1];sign=1 if side=='L' else -1
            rec=copy.deepcopy(a['shape']);rec['children'][1]['radius']=radius
            rec['children'][0]['size'][1]+=jaw['rear_extension_mm'];rec['children'][0]['at'][1]+=sign*jaw['rear_extension_mm']/2
            sh=build(rec,p);hs=[]
            for y in jaw['hole_y_abs']:
                at=[p['load_x'],sign*y,jaw['top_z']];sh=hole(sh,jaw['through_diameter'],at)
                cb_at=[at[0],at[1],jaw['top_z']-jaw['counterbore_depth']/2]
                sh=sh.cut(cyl(jaw['counterbore_diameter'],jaw['counterbore_depth'],cb_at))
                hs.append(dict(x=at[0],y=at[1],diameter=jaw['through_diameter'],counterbore_diameter=jaw['counterbore_diameter'],counterbore_depth=jaw['counterbore_depth'],purpose='从Z+沉孔，螺钉头低于顶面'))
            row=dict(instance_id=f'PRT-0603-R3-R{radius}-{side}',family=f'PRT-0603-R3-R{radius}-{side}',part_id='PRT-0603',assembly_id='ASM-06',parent=a['parent'],kind='custom',holes=hs,material='未填充本色POM-C',shape=sh,radius_mm=radius)
            variants.append(row)
            if radius==jaw['assembly_radius']:rows.append(row)
    return rows,variants,s,b

def posed(rows,state):
    from cad.assemblies.posing import pose_shape
    return [(a,pose_shape(a,a['shape'],state,a.get('recipe'))) for a in rows]
