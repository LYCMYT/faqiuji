"""R4 revision overlays R3; historical recipes remain untouched."""
import json,math
from pathlib import Path
import cadquery as cq
from cad.assemblies.r3_fixture import model as r3_model, posed
R=Path(__file__).resolve().parents[2]
def model():
    rows,variants,old,b=r3_model()
    s=json.loads((R/'data/r4_fixture.json').read_text(encoding='utf-8'))
    from cad.assemblies.kinematics import parameters
    x=parameters()['load_x'];land=s['seat'];lo=[x+land['x_relative'][0],land['y'][0],land['z'][0]];hi=[x+land['x_relative'][1],land['y'][1],land['z'][1]]
    for a in rows:
        if a['instance_id']==land['instance_id']:
            a['shape']=a['shape'].fuse(cq.Solid.makeBox(*[q-p for p,q in zip(lo,hi)],cq.Vector(*lo))).clean()
            a['family']=land['family'];a['kind']='revised_context';a['recipe']=None;a['dynamic_slide']=False;a['source_revision']='R3 unchanged + integral R4 low land'
    def block(lo,hi):return cq.Solid.makeBox(*[q-p for p,q in zip(lo,hi)],cq.Vector(*lo))
    def cylinder(radius,start,end):
        delta=cq.Vector(*end).sub(cq.Vector(*start));return cq.Solid.makeCylinder(radius,delta.Length,cq.Vector(*start),delta.normalized())
    def symbox(xr,yr,zr):return block([xr[0],min(sign*yr[0],sign*yr[1]),zr[0]],[xr[1],max(sign*yr[0],sign*yr[1]),zr[1]])
    def revise(a,shape,note):
        a['shape']=shape.clean();a['family']=a['family'].replace('-R3-','-R4-') if '-R3-' in a['family'] else (a['family'] if '-R4' in a['family'] else a['family']+'-R4');a['kind']='revised_context';a['dynamic_slide']=False;a['recipe']=None;a['r4_revision']=note
    def extra(id,shape,parent='FIXED_HEAD_CARRIER',kind='custom',family=None):
        rows.append(dict(instance_id=id,family=family or id,part_id=id[:8],assembly_id='ASM-'+id[4:6],parent=parent,kind=kind,holes=[],material='Self-designed candidate; material, grade, threads/preload OPEN',shape=shape.clean()))
    g=s['manual_guides']['upper']
    for sign,side in [(1,'L'),(-1,'R')]:
        carrier=next(a for a in rows if a['instance_id']=='PRT-0603-R3-CARRIER-'+side)
        fixed=next(a for a in rows if a['instance_id']=='PRT-0602-C__'+side+'410')
        moving=carrier['shape'];sleeve=symbox([x-g['sleeve_size_xz'][0]/2,x+g['sleeve_size_xz'][0]/2],g['sleeve_y'],[g['z']-g['sleeve_size_xz'][1]/2,g['z']+g['sleeve_size_xz'][1]/2])
        for dx in g['shaft_x_offsets']:
            xx=x+dx
            moving=moving.fuse(cylinder(g['shaft_radius'],[xx,sign*g['shaft_y'][0],g['z']],[xx,sign*g['shaft_y'][1],g['z']]))
            for cy in g['collar_y']:
                moving=moving.fuse(cylinder(g['collar_radius'],[xx,sign*(cy-g['collar_thickness']/2),g['z']],[xx,sign*(cy+g['collar_thickness']/2),g['z']]))
            sleeve=sleeve.cut(cylinder(g['bore_radius'],[xx,sign*(g['sleeve_y'][0]-1),g['z']],[xx,sign*(g['sleeve_y'][1]+1),g['z']]))
        web=symbox(g['web_x'],g['web_y'],g['web_z']);bridge=symbox(g['bridge_x'],g['bridge_y'],g['bridge_z'])
        cap=sleeve.intersect(block([x-g['sleeve_size_xz'][0],min(sign*g['sleeve_y'][0],sign*g['sleeve_y'][1]),g['split_z']],[x+g['sleeve_size_xz'][0],max(sign*g['sleeve_y'][0],sign*g['sleeve_y'][1]),g['split_z']+g['sleeve_size_xz'][1]]));body=fixed['shape'].fuse(sleeve).fuse(web).fuse(bridge).cut(cap)
        for dx in g['cap_fastener_x_offsets']:
            for yy0 in g['cap_fastener_y']:
                xx=x+dx;yy=sign*yy0;body=body.cut(cylinder(g['cap_hole_radius'],[xx,yy,g['cap_screw_z'][0]-1],[xx,yy,g['cap_screw_head_z'][1]+1]));cap=cap.cut(cylinder(g['cap_hole_radius'],[xx,yy,g['cap_screw_z'][0]-1],[xx,yy,g['cap_screw_head_z'][1]+1]))
                screw=cylinder(g['cap_screw_radius'],[xx,yy,g['cap_screw_z'][0]],[xx,yy,g['cap_screw_z'][1]]).fuse(cylinder(g['cap_screw_head_radius'],[xx,yy,g['cap_screw_head_z'][0]],[xx,yy,g['cap_screw_head_z'][1]]))
                nz=g['cap_nut_z'];nut=cq.Workplane('XY').polygon(6,g['cap_nut_AF']/math.cos(math.pi/6)).extrude(nz[1]-nz[0]).val().translate((xx,yy,nz[0])).cut(cylinder(g['cap_nut_bore_radius'],[xx,yy,nz[0]-1],[xx,yy,nz[1]+1]))
                for typ,sh in [('SCREW',screw),('NUT',nut)]:
                    rows.append(dict(instance_id=f'PRT-0603-R4-CAP-{side}-{dx}-{yy0}-{typ}',family=f'PRT-0603-R4-CAP-M3-{typ}',part_id='PRT-0603',assembly_id='ASM-06',parent='FIXED_HEAD_CARRIER',kind='hardware',holes=[],material='Custom M3 candidate; grade, thread and preload OPEN',shape=sh))
        rows.append(dict(instance_id='PRT-0603-R4-BUSHCAP-'+side,family='PRT-0603-R4-BUSHCAP-'+side,part_id='PRT-0603',assembly_id='ASM-06',parent='FIXED_HEAD_CARRIER',kind='custom',holes=[],material='Custom split guide cap; material/fit OPEN',shape=cap))
        revise(carrier,moving,'Integral paired manual guide shafts/collars; assembled by split bush cap; prototype friction/holding unknown')
        revise(fixed,body,'Integral split manual guide lower bush support and reaction bridge; explicit four M3 cap through-holes')
    g=s['manual_guides']['gate'];gate=next(a for a in rows if a['instance_id']=='PRT-0604');wall=next(a for a in rows if a['instance_id']=='PRT-0602-G');moving=gate['shape'];fixed=wall['shape']
    fixed=fixed.cut(block([g['wall_aperture_x'][0],g['wall_aperture_y'][0],g['wall_aperture_z'][0]],[g['wall_aperture_x'][1],g['wall_aperture_y'][1],g['wall_aperture_z'][1]]))
    for sign in [-1,1]:
        yy=sign*g['shaft_y_abs'];zz=g['z'];moving=moving.fuse(symbox(g['rib_x'],g['rib_y_abs'],g['rib_z']));moving=moving.fuse(block([g['ear_x'][0],min(sign*g['ear_y'][0],sign*g['ear_y'][1]),g['ear_z'][0]],[g['ear_x'][1],max(sign*g['ear_y'][0],sign*g['ear_y'][1]),g['ear_z'][1]]))
        moving=moving.fuse(cylinder(g['shaft_radius'],[g['shaft_x'][0],yy,zz],[g['shaft_x'][1],yy,zz]))
        for xx in g['collar_x']:moving=moving.fuse(cylinder(g['collar_radius'],[xx-g['collar_thickness']/2,yy,zz],[xx+g['collar_thickness']/2,yy,zz]))
        fixed=fixed.fuse(block([g['sleeve_x'][0],yy-g['sleeve_size_yz'][0]/2,zz-g['sleeve_size_yz'][1]/2],[g['sleeve_x'][1],yy+g['sleeve_size_yz'][0]/2,zz+g['sleeve_size_yz'][1]/2]))
        fixed=fixed.cut(cylinder(g['bore_radius'],[g['sleeve_x'][0]-1,yy,zz],[g['sleeve_x'][1]+1,yy,zz]))
        fixed=fixed.fuse(symbox(g['reaction_bridge_x'],g['reaction_bridge_y_abs'],g['reaction_bridge_z'])).fuse(symbox(g['reaction_sleeve_riser_x'],g['reaction_bridge_y_abs'],g['reaction_sleeve_riser_z'])).fuse(symbox(g['reaction_wall_riser_x'],g['reaction_bridge_y_abs'],g['reaction_wall_riser_z']))
        # Split the gate bush so captive shaft collars are actually assemblable.
        h=g['split_caps'];cap=fixed.intersect(block([g['sleeve_x'][0],yy-g['sleeve_size_yz'][0]/2,h['split_z']],[g['sleeve_x'][1],yy+g['sleeve_size_yz'][0]/2,zz+g['sleeve_size_yz'][1]/2]));fixed=fixed.cut(cap)
        # The riser is relieved for access to the cap's lower nuts.
        for xx in h['bolt_x']:
            for by in [yy+v for v in h['bolt_y_relative']]:
                bore=cylinder(h['bore_radius'],[xx,by,h['nut_clearance_pocket_z'][0]],[xx,by,h['head_z'][1]+1]);fixed=fixed.cut(bore);cap=cap.cut(bore)
                nutpocket=cylinder(h['nut_clearance_pocket_radius'],[xx,by,h['nut_clearance_pocket_z'][0]],[xx,by,h['nut_clearance_pocket_z'][1]]);fixed=fixed.cut(nutpocket)
                screw=cylinder(h['screw_radius'],[xx,by,h['screw_z'][0]],[xx,by,h['screw_z'][1]]).fuse(cylinder(h['head_radius'],[xx,by,h['head_z'][0]],[xx,by,h['head_z'][1]]));nut=cylinder(h['nut_radius'],[xx,by,h['nut_z'][0]],[xx,by,h['nut_z'][1]]).cut(cylinder(h['nut_bore_radius'],[xx,by,h['nut_z'][0]-1],[xx,by,h['nut_z'][1]+1]))
                extra(f'PRT-0604-R4-CAP-{sign}-{xx}-{by}-SCREW',screw,kind='hardware',family='PRT-0604-R4-CAP-M3-SCREW');extra(f'PRT-0604-R4-CAP-{sign}-{xx}-{by}-NUT',nut,kind='hardware',family='PRT-0604-R4-CAP-M3-NUT')
        extra('PRT-0604-R4-BUSHCAP-'+str(sign),cap)
    revise(gate,moving,'Integral gate ears and paired manual shafts; end collar stops at 0/85mm')
    revise(wall,fixed,'Integral paired gate bushes; explicit R4 through aperture for gate plate')
    g=s['manual_guides']['slide'];rail=next(a for a in rows if a['instance_id']=='PRT-0703-A');carriage=next(a for a in rows if a['instance_id']=='PRT-0703-C');fixed=rail['shape'];moving=carriage['shape']
    for sign in [-1,1]:
        moving=moving.fuse(symbox(g['moving_flange_x'],g['moving_flange_y_abs'],g['moving_flange_z']))
        for key in ['channel_side','channel_lower_lip','channel_upper_lip']:fixed=fixed.fuse(symbox(g['channel_x'],g[key+'_y_abs'],g[key+'_z']))
        # End plates meet the moving flange faces at exactly 0 and 185 mm.
        for xr in g['stop_x']:fixed=fixed.fuse(symbox(xr,g['channel_lower_lip_y_abs'],[g['channel_lower_lip_z'][0],g['channel_upper_lip_z'][1]]))
        for a in rows:
            if a['instance_id'].startswith('PRT-0703-R3-SHOE-'):
                cut=symbox(g['shoe_relief_x'],g['shoe_relief_y_abs'],g['shoe_relief_z']);revise(a,a['shape'].cut(cut),'R4 explicit pocket clears captive slide channel; retained underside side support requires load review')
    revise(rail,fixed,'Integral captive flange ways and 0/185 hard stops')
    revise(carriage,moving,'Integral paired retaining flanges captured under rail lips')
    # Front retaining stops detach in +X before carriage/flange insertion/removal.
    fixed=rail['shape']
    for sign in [-1,1]:
        stop=fixed.intersect(symbox(g['stop_x'][1],g['channel_lower_lip_y_abs'],[g['channel_lower_lip_z'][0],g['channel_upper_lip_z'][1]]));fixed=fixed.cut(stop)
        h=g['removable_front_stop']
        for yy in [sign*v for v in h['screw_y_abs']]:
            bore=cylinder(h['bore_radius'],[h['shaft_x'][0]-1,yy,h['screw_z']],[h['head_x'][1]+1,yy,h['screw_z']]);fixed=fixed.cut(bore);stop=stop.cut(bore)
            screw=cylinder(h['shaft_radius'],[h['shaft_x'][0],yy,h['screw_z']],[h['shaft_x'][1],yy,h['screw_z']]).fuse(cylinder(h['head_radius'],[h['head_x'][0],yy,h['screw_z']],[h['head_x'][1],yy,h['screw_z']]));extra(f'PRT-0703-R4-ENDSTOP-{sign}-{yy}-SCREW',screw,kind='hardware',family='PRT-0703-R4-ENDSTOP-M2-SCREW')
        extra('PRT-0703-R4-ENDSTOP-'+str(sign),stop,parent='MOVING_HEAD')
    rail['shape']=fixed.clean()
    guide=next(a for a in rows if a['instance_id']=='PRT-0607-A');neck=next(a for a in rows if a['instance_id']=='PRT-0606-A')
    g=s['manual_guides']['guide_sleeve'];way=block(*g['back_web_bounds'])
    for sign in [-1,1]:
        way=way.fuse(symbox(g['side_wall_x'],g['side_wall_y_abs'],g['side_wall_z']))
        way=way.fuse(symbox(g['lip_x'],g['lip_y_abs'],g['lip_z']))
        for zr in g['stop_z']:way=way.fuse(symbox(g['stop_x'],g['stop_y_abs'],zr))
    # Upper tongue stop blocks withdraw sideways after their horizontal screws.
    for sign in [-1,1]:
        h=g['top_stop_screw'];stop=way.intersect(symbox(g['stop_x'],g['stop_y_abs'],g['stop_z'][1]));way=way.cut(stop)
        bore=cylinder(h['bore_radius'],[h['x'],sign*(h['shaft_y_abs'][0]-2),h['z']],[h['x'],sign*(h['head_y_abs'][1]+1),h['z']]);way=way.cut(bore);stop=stop.cut(bore)
        screw=cylinder(h['shaft_radius'],[h['x'],sign*h['shaft_y_abs'][0],h['z']],[h['x'],sign*h['shaft_y_abs'][1],h['z']]).fuse(cylinder(h['head_radius'],[h['x'],sign*h['head_y_abs'][0],h['z']],[h['x'],sign*h['head_y_abs'][1],h['z']]))
        extra('PRT-0607-R4-UPSTOP-'+str(sign),stop);extra('PRT-0607-R4-UPSTOP-'+str(sign)+'-SCREW',screw,kind='hardware',family='PRT-0607-R4-UPSTOP-M3-SCREW')
    revise(guide,way,'Self-designed captive Z way replaces supplier actuator envelope; face weld interface to original bracket at z271 remains load OPEN')
    revise(neck,block(*g['neck_bounds']).fuse(block(*g['flange_bounds'])).cut(next(a for a in rows if a['instance_id']=='PRT-0606')['shape']),'R4 explicit narrow guide neck clears retaining lips; flange retains sleeve attachment face')
    cross=next(a for a in rows if a['instance_id']=='PRT-0701-C');cradle=next(a for a in rows if a['instance_id']=='PRT-0701-A')
    g=s['manual_guides']['clamp'];bridge=block(*g['crossbeam_bounds']).cut(cradle['shape']);fixed=cross['shape'].fuse(bridge)
    for sign,side in [(1,'L'),(-1,'R')]:
        arm=next(a for a in rows if a['instance_id']=='PRT-0702-A__'+side)
        arm['shape']=arm['shape'].fuse(symbox(g['arm_rear_extension']['x'],g['arm_rear_extension']['y_abs'],g['arm_rear_extension']['z'])).clean()
        slot=symbox(g['slot_box_bounds_x'],g['slot_endpoint_y_abs'],g['slot_z'])
        for yy in [sign*v for v in g['slot_endpoint_y_abs']]:slot=slot.fuse(cylinder(g['slot_radius'],[g['slot_x_center'],yy,g['slot_z'][0]],[g['slot_x_center'],yy,g['slot_z'][1]]))
        revise(arm,arm['shape'].cut(slot),'Explicit manual travel slot; nominal14mm,0.2mm pin radial running clearance')
        channel=symbox(g['channel_x'],g['channel_y_abs'],g['channel_z']).cut(symbox(g['channel_open_cavity_x'],g['channel_open_cavity_y_abs'],g['channel_open_cavity_z']))
        # Pin is a removable custom stepped candidate, no supplier hole inference.
        yy=sign*g['travel_pin_y_abs'];xx=g['travel_pin_x'];pz=g['travel_pin_z'];channel=channel.cut(cylinder(g['slot_radius'],[xx,yy,pz[0]],[xx,yy,pz[1]]));fixed=fixed.fuse(channel).cut(cylinder(g['collar_clearance_pocket_radius'],[xx,yy,g['collar_clearance_pocket_z'][0]],[xx,yy,g['collar_clearance_pocket_z'][1]])).cut(cylinder(g['slot_radius'],[xx,yy,g['collar_clearance_pocket_z'][0]],[xx,yy,pz[1]]))
        pin=cylinder(g['travel_pin_radius'],[xx,yy,pz[0]],[xx,yy,pz[1]])
        zr=g['pin_collar_z'][0];pin=pin.fuse(cylinder(g['pin_collar_radius'],[xx,yy,zr[0]],[xx,yy,zr[1]]))
        # Separate removable lower nut makes installation possible, thread teeth omitted.
        h=g['lower_nut'];nut=cq.Workplane('XY').polygon(6,h['AF']/math.cos(math.pi/6)).extrude(h['height']).val().translate((xx,yy,h['z'][0])).cut(cylinder(h['bore_radius'],[xx,yy,h['z'][0]-1],[xx,yy,h['z'][1]+1]))
        fixed=fixed.cut(cylinder(h['clearance_pocket_radius'],[xx,yy,h['clearance_pocket_z'][0]],[xx,yy,h['clearance_pocket_z'][1]]));extra('PRT-0702-R4-TRAVELNUT-'+side,nut,parent='CARRIAGE',kind='hardware',family='PRT-0702-R4-TRAVELNUT-M4')
        rows.append(dict(instance_id='PRT-0702-R4-TRAVELPIN-'+side,family='PRT-0702-R4-TRAVELPIN',part_id='PRT-0702',assembly_id='ASM-07',parent='CARRIAGE',kind='hardware',holes=[],material='Custom stepped pin with candidate M4 tail; thread teeth/grade OPEN',shape=pin))
    revise(cross,fixed,'Integral symmetric captive clamp channels and nominal travel pin seats; collar retention requires prototype')
    # Positive manual endpoint pins are shown withdrawn during all working paths.
    # Their installed endpoint solids are checked separately, never glued to a mover.
    def lockpin(id,shape,park,axis,endpoints,parent='FIXED_HEAD_CARRIER'):
        extra(id,shape.translate(park),parent=parent,kind='hardware')
        rows[-1].update(installed_shape=shape,park_delta_mm=park,lock_axis=axis,lock_endpoints_mm=endpoints,source_status='custom positive manual lock candidate; detent/tether, grade and force OPEN')
    def row(id):return next(a for a in rows if a['instance_id']==id)
    def axial_pin(radius,head_radius,coordinate,shaft,head,axis):
        first=list(coordinate);last=list(coordinate);first[axis]=shaft[0];last[axis]=shaft[1];shape=cylinder(radius,first,last);first[axis]=head[0];last[axis]=head[1];return shape.fuse(cylinder(head_radius,first,last))
    g=s['manual_guides']['holding']['upper']
    for sign,side in [(1,'L'),(-1,'R')]:
        xx=x+g['x_offset'];yy=sign*g['fixed_y_abs'];carrier=row('PRT-0603-R3-CARRIER-'+side);cap=row('PRT-0603-R4-BUSHCAP-'+side);body=row('PRT-0602-C__'+side+'410')
        for cy in g['moving_hole_y_abs']:carrier['shape']=carrier['shape'].cut(cylinder(g['bore_radius'],[xx,sign*cy,g['shaft_z'][0]-1],[xx,sign*cy,g['head_z'][1]+1]))
        cap['shape']=cap['shape'].fuse(block([xx-g['boss_xyz_half'][0],yy-g['boss_xyz_half'][1],g['boss_z'][0]],[xx+g['boss_xyz_half'][0],yy+g['boss_xyz_half'][1],g['boss_z'][1]]))
        bore=cylinder(g['bore_radius'],[xx,yy,g['shaft_z'][0]-1],[xx,yy,g['head_z'][1]+1]);cap['shape']=cap['shape'].cut(bore);body['shape']=body['shape'].cut(bore)
        pin=axial_pin(g['pin_radius'],g['head_radius'],[xx,yy,0],g['shaft_z'],g['head_z'],2);lockpin('PRT-0603-R4-HOLDPIN-'+side,pin,tuple(g['park_delta_mm']),'upper',g['endpoints_mm'])
    g=s['manual_guides']['holding']['gate'];gate=row('PRT-0604');body=row('PRT-0602-G');cap=row('PRT-0604-R4-BUSHCAP-1');xx=g['x'];yy=g['y']
    for cx in g['moving_hole_x']:gate['shape']=gate['shape'].cut(cylinder(g['bore_radius'],[cx,yy,g['shaft_z'][0]-1],[cx,yy,g['head_z'][1]+1]))
    cap['shape']=cap['shape'].fuse(block([xx-g['boss_xy_half'],yy-g['boss_xy_half'],g['boss_z'][0]],[xx+g['boss_xy_half'],yy+g['boss_xy_half'],g['boss_z'][1]]));bore=cylinder(g['bore_radius'],[xx,yy,g['shaft_z'][0]-1],[xx,yy,g['head_z'][1]+1]);cap['shape']=cap['shape'].cut(bore);body['shape']=body['shape'].cut(bore)
    pin=axial_pin(g['pin_radius'],g['head_radius'],[xx,yy,0],g['shaft_z'],g['head_z'],2);lockpin('PRT-0604-R4-HOLDPIN',pin,tuple(g['park_delta_mm']),'gate',g['endpoints_mm'])
    g=s['manual_guides']['holding']['guide'];way=row('PRT-0607-A');tongue=row('PRT-0607-B');tongue['shape']=tongue['shape'].cut(cylinder(g['bore_radius'],[g['x'],-g['tongue_bore_y_half'],g['moving_hole_z']],[g['x'],g['tongue_bore_y_half'],g['moving_hole_z']]))
    for zz,end in zip(g['fixed_z'],g['endpoints_mm']):
        way['shape']=way['shape'].fuse(block([*g['boss_bounds_xy'][0],zz-g['boss_z_half']],[*g['boss_bounds_xy'][1],zz+g['boss_z_half']])).cut(cylinder(g['bore_radius'],[g['x'],g['way_bore_y'][0],zz],[g['x'],g['way_bore_y'][1],zz]))
        pin=axial_pin(g['pin_radius'],g['head_radius'],[g['x'],0,zz],g['shaft_y'],g['head_y'],1);lockpin('PRT-0607-R4-HOLDPIN-'+str(end),pin,tuple(g['park_delta_mm']),'guide',[end])
    g=s['manual_guides']['holding']['slide'];rail=row('PRT-0703-A');carriage=row('PRT-0703-C');carriage['shape']=carriage['shape'].cut(cylinder(g['bore_radius'],[g['moving_hole_x'],g['y'],g['shaft_z'][0]-1],[g['moving_hole_x'],g['y'],g['shaft_z'][1]+1]))
    for xx,end in zip(g['fixed_x'],g['endpoints_mm']):
        rail['shape']=rail['shape'].cut(cylinder(g['bore_radius'],[xx,g['y'],g['shaft_z'][0]-1],[xx,g['y'],g['shaft_z'][1]+1]));pin=axial_pin(g['pin_radius'],g['head_radius'],[xx,g['y'],0],g['shaft_z'],g['head_z'],2);lockpin('PRT-0703-R4-HOLDPIN-'+str(end),pin,tuple(g['park_delta_mm']),'slide',[end],parent='MOVING_HEAD')
    g=s['manual_guides']['holding']['clamp'];cross=row('PRT-0701-C')
    for sign,side in [(1,'L'),(-1,'R')]:
        arm=row('PRT-0702-A__'+side);xx=g['x'];yy=sign*g['fixed_y_abs']
        for cy in g['moving_hole_y_abs']:arm['shape']=arm['shape'].cut(cylinder(g['bore_radius'],[xx,sign*cy,g['shaft_z'][0]-1],[xx,sign*cy,g['head_z'][1]+1]))
        cross['shape']=cross['shape'].fuse(block([xx-g['boss_xy_half'],yy-g['boss_xy_half'],g['boss_z'][0]],[xx+g['boss_xy_half'],yy+g['boss_xy_half'],g['boss_z'][1]])).cut(cylinder(g['bore_radius'],[xx,yy,g['shaft_z'][0]-1],[xx,yy,g['head_z'][1]+1]))
        pin=axial_pin(g['pin_radius'],g['head_radius'],[xx,yy,0],g['shaft_z'],g['head_z'],2);lockpin('PRT-0702-R4-HOLDPIN-'+side,pin,tuple(g['park_delta_mm']),'clamp',g['endpoints_mm'],parent='CARRIAGE')
    for a in rows:a['shape']=a['shape'].clean()
    return rows,variants,s,b
