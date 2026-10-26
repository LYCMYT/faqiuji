"""Explicit nominal mechanical predicates; no material/load qualification."""
import math
import cadquery as cq
from cad.assemblies.r4_fixture import posed
from cad.export_all import exact_bbox

def cylinder(radius,start,end):
    v=cq.Vector(*end).sub(cq.Vector(*start));return cq.Solid.makeCylinder(radius,v.Length,cq.Vector(*start),v.normalized())
def box(lo,hi):return cq.Solid.makeBox(*[b-a for a,b in zip(lo,hi)],cq.Vector(*lo))
def compound(shapes):return cq.Compound.makeCompound(shapes)

def retention_acceptance(rows,s,p,axis,state,check_stops=True,placed_override=None):
    """Test actual material engagement, restraining guide material and overtravel stops.

    Virtual inspection probes are declared in data, not substitutes for missing
    geometry: both moving material and stationary restraining material must exist.
    """
    cfg=s['inspection']['retention'];g=s['manual_guides'][{'guide':'guide_sleeve'}.get(axis,axis)]
    bodies=placed_override or {a['instance_id']:sh for a,sh in posed(rows,state)};checks=[];pairs=[]
    step=cfg['overtravel_probe_mm'];r=cfg['probe_radius_mm'];q=cfg['fixture_probe_box_mm'];tol=cfg['nominal_tolerance_mm'];x=p['load_x']
    def material(name,probe,target,minimum=None):
        fraction=probe.intersect(target).Volume()/probe.Volume();minimum=cfg['minimum_material_fraction'] if minimum is None else minimum
        checks.append(dict(check=name,material_fraction=fraction,minimum_fraction=minimum,status='PASS' if fraction>=minimum-tol else 'FAIL'))
    def cube(center):return box([v-q/2 for v in center],[v+q/2 for v in center])
    if axis=='upper':
        for sign,side in [(1,'L'),(-1,'R')]:
            moving_id='PRT-0603-R3-CARRIER-'+side;fixed_ids=['PRT-0602-C__'+side+'410','PRT-0603-R4-BUSHCAP-'+side];fixed=compound([bodies[k] for k in fixed_ids]);pairs.append((moving_id,fixed_ids))
            for dx in g['shaft_x_offsets']:
                start=[x+dx,sign*g['sleeve_y'][0],g['z']];end=[x+dx,sign*g['sleeve_y'][1],g['z']]
                material(side+':shaft_engaged',cylinder(r,start,end),bodies[moving_id])
                shell=cylinder(g['bore_radius']+cfg['shell_outer_margin_mm'],start,end).cut(cylinder(g['bore_radius']+cfg['shell_inner_margin_mm'],start,end));material(side+':bush_retaining_material',shell,fixed)
    elif axis=='gate':
        for sign in [-1,1]:
            fixed_ids=['PRT-0602-G','PRT-0604-R4-BUSHCAP-'+str(sign)];pairs.append(('PRT-0604',fixed_ids));fixed=compound([bodies[k] for k in fixed_ids]);start=[g['sleeve_x'][0],sign*g['shaft_y_abs'],g['z']];end=[g['sleeve_x'][1],sign*g['shaft_y_abs'],g['z']]
            material(str(sign)+':shaft_engaged',cylinder(r,start,end),bodies['PRT-0604'])
            material(str(sign)+':bush_retaining_material',cylinder(g['bore_radius']+cfg['shell_outer_margin_mm'],start,end).cut(cylinder(g['bore_radius']+cfg['shell_inner_margin_mm'],start,end)),fixed)
    elif axis=='guide':
        moving=bodies['PRT-0607-B'];bb=exact_bbox(moving);z=(bb.zmin+bb.zmax)/2;fixed_ids=['PRT-0607-A','PRT-0607-R4-UPSTOP--1','PRT-0607-R4-UPSTOP-1'];pairs.append(('PRT-0607-B',fixed_ids));fixed=compound([bodies[k] for k in fixed_ids])
        span=max(0,min(bb.zmax,g['lip_z'][1])-max(bb.zmin,g['lip_z'][0]));fraction=span/bb.zlen
        checks.append(dict(check='tongue_axial_engagement',engaged_mm=span,total_mm=bb.zlen,status='PASS' if fraction>=1-tol else 'FAIL'))
        material('tongue_present',cube([s['manual_guides']['holding']['guide']['x'],0,bb.zmin+bb.zlen/4]),moving)
        for sign in [-1,1]:material(str(sign)+':front_lip_retains_tongue',cube([sum(g['lip_x'])/2,sign*sum(g['side_wall_y_abs'])/2,z]),fixed)
        material('back_web_present',cube([g['back_web_bounds'][1][0]-q,0,z]),fixed)
    elif axis=='slide':
        fixed_ids=['PRT-0703-A','PRT-0703-R4-ENDSTOP--1','PRT-0703-R4-ENDSTOP-1'];pairs.append(('PRT-0703-C',fixed_ids));fixed=compound([bodies[k] for k in fixed_ids]);xx=sum(g['moving_flange_x'])/2+state.get('slide',0)
        for sign in [-1,1]:
            material(str(sign)+':flange_engaged',cube([xx,sign*sum(g['moving_flange_y_abs'])/2,sum(g['moving_flange_z'])/2]),bodies['PRT-0703-C'])
            for tag in ['channel_upper_lip','channel_lower_lip']:material(str(sign)+':'+tag,cube([xx,sign*sum(g[tag+'_y_abs'])/2,sum(g[tag+'_z'])/2]),fixed)
    elif axis=='clamp':
        shift=state.get('slide',0);extension=g['arm_rear_extension'];yy=sum(g['channel_y_abs'])/2
        for sign,side in [(1,'L'),(-1,'R')]:
            moving_id='PRT-0702-A__'+side;fixed_ids=['PRT-0701-C','PRT-0702-R4-TRAVELPIN-'+side];pairs.append((moving_id,fixed_ids));fixed=compound([bodies[k] for k in fixed_ids]);xx=extension['x'][0]+(extension['x'][1]-extension['x'][0])/4+shift
            material(side+':arm_engaged_in_portal',cube([xx,sign*yy,sum(extension['z'])/2]),bodies[moving_id])
            for zz,tag in [(sum([g['channel_z'][0],g['channel_open_cavity_z'][0]])/2,'lower_lip'),(sum([g['channel_z'][1],g['channel_open_cavity_z'][1]])/2,'upper_lip')]:material(side+':'+tag,cube([sum(g['channel_x'])/2+shift,sign*yy,zz]),fixed)
            material(side+':rear_wall',cube([sum([g['channel_x'][0],g['channel_open_cavity_x'][0]])/2+shift,sign*yy,sum(extension['z'])/2]),fixed)
    limits={'upper':[0,s['manual_guides']['holding']['upper']['endpoints_mm'][-1]],'gate':[0,s['manual_guides']['holding']['gate']['endpoints_mm'][-1]],'guide':[0,p['guide_stroke']],'slide':[0,p['carriage_total_stroke']],'clamp':[0,g.get('nominal_stroke_mm',0)]}[axis]
    value=state.get(axis,0);checks.append(dict(check='within_nominal_stops',value_mm=value,limits_mm=limits,status='PASS' if limits[0]-tol<=value<=limits[1]+tol else 'FAIL'))
    if check_stops:
        for endpoint,sign in [(limits[0],-1),(limits[1],1)]:
            beyond={**state,axis:endpoint+sign*step};placed={a['instance_id']:sh for a,sh in posed(rows,beyond)}
            for moving_id,fixed_ids in pairs:
                volume=placed[moving_id].intersect(compound([placed[k] for k in fixed_ids])).Volume()
                checks.append(dict(check='hard_stop_blocks_overtravel',moving=moving_id,endpoint_mm=endpoint,probe_mm=sign*step,blocked_volume_mm3=volume,status='PASS' if volume>s['inspection']['collision_threshold_mm3'] else 'FAIL'))
    return dict(axis=axis,value_mm=value,status='PASS' if all(v['status']=='PASS' for v in checks) else 'FAIL',checks=checks,load_and_material_rating='OPEN')

def service_removal_checks(rows,s,p,state):
    """Ordered component withdrawal and proposed tool envelopes, all native context retained."""
    from tools.check_collisions import bbox,overlaps
    cfg=s['service']['candidate_tools'];limit=s['inspection']['collision_threshold_mm3'];parts={a['instance_id']:a for a in rows};shapes={a['instance_id']:sh for a,sh in posed(rows,state)};removed=set();failed_parts=set();blocked_dependencies={};paths=[];tools=[];unlock_setup=[]
    from cad.export_all import locate
    from cad.assemblies.kinematics import matrix
    for a in rows:
        if 'installed_shape' not in a:continue
        value=state.get(a['lock_axis'],0);eligible=any(abs(value-v)<=s['inspection']['retention']['nominal_tolerance_mm'] for v in a['lock_endpoints_mm'])
        if eligible:
            shapes[a['instance_id']]=locate(a['installed_shape'],a['parent'],state)
            transform=matrix(a['parent'],state);delta=[sum(transform[i,j]*a['park_delta_mm'][j] for j in range(3)) for i in range(3)]
            unlock_setup.append(dict(instance=a['instance_id'],axis=a['lock_axis'],endpoint_mm=value,state=dict(state),delta_mm=delta,start_geometry='installed_shape transformed by actual parent/state'))
    def hits(shape,exclude):
        result=[]
        for id,other in shapes.items():
            if id in removed or id in exclude:continue
            if overlaps(bbox(shape),bbox(other)):
                volume=shape.intersect(other).Volume()
                if volume>limit:result.append(dict(obstruction=id,volume_mm3=volume))
        return result
    def withdraw(ids,delta,phase,final=True):
        # Remove parts one by one, preserving every still-installed context body.
        for id in ids:
            if id in removed:continue
            if id in failed_parts:
                paths.append(dict(instance=id,phase=phase,delta_mm=delta,samples=0,intersections=[],status='FAIL',blocked_by_prior_step=True,blocked_by_dependency=blocked_dependencies.get(id)));continue
            length=math.sqrt(sum(v*v for v in delta));count=max(1,math.ceil(length/cfg['withdraw_step_mm']));hh=[]
            for n in range(count+1):
                moved=shapes[id].translate(tuple(v*n/count for v in delta))
                for h in hits(moved,{id}):hh.append(dict(sample=n,**h))
            first=exact_bbox(shapes[id]);last=exact_bbox(moved)
            paths.append(dict(instance=id,phase=phase,delta_mm=delta,samples=count+1,start_bbox_mm=[first.xmin,first.ymin,first.zmin,first.xmax,first.ymax,first.zmax],end_bbox_mm=[last.xmin,last.ymin,last.zmin,last.xmax,last.ymax,last.zmax],intersections=hh,status='PASS' if not hh else 'FAIL'))
            # A failed removal does not authorize pretending that body disappeared.
            if not hh:
                if final:removed.add(id)
                else:shapes[id]=moved
            else:failed_parts.add(id)
    def access(id,axis,sign,size='M3',wrench=False):
        sh=shapes[id];bb=exact_bbox(sh);center=[(bb.xmin+bb.xmax)/2,(bb.ymin+bb.ymax)/2,(bb.zmin+bb.zmax)/2]
        if wrench:
            width=cfg['M3_open_wrench_width_mm'];thick=cfg['M3_open_wrench_thickness_mm'];reach=cfg['M3_open_wrench_reach_mm'];lo=[center[0]-width/2,min(center[1],center[1]+sign*reach),center[2]-thick/2];hi=[center[0]+width/2,max(center[1],center[1]+sign*reach),center[2]+thick/2];tool=box(lo,hi)
        else:
            extents=[(bb.xmin,bb.xmax),(bb.ymin,bb.ymax),(bb.zmin,bb.zmax)];center[axis]=extents[axis][1 if sign>0 else 0];end=list(center);radius=cfg[size+'_driver_radius_mm'];length=cfg[size+'_driver_length_mm'];end[axis]+=sign*length;tool=cylinder(radius,center,end)
        # Exclude this fastener and its paired screw/nut: tool tips act on that joint.
        paired=id.removesuffix('-NUT').removesuffix('-SCREW');exclude={k for k in shapes if k.startswith(paired) and k.endswith(('-NUT','-SCREW'))}|{id};hh=hits(tool,exclude)
        tools.append(dict(instance=id,tool='proposed_open_wrench' if wrench else 'proposed_'+size+'_driver',intersections=hh,status='PASS' if not hh else 'FAIL'))
        if hh:failed_parts.add(id)
    distance=s['service']['fastener_withdraw_mm'];lift=s['service']['cap_lift_mm']
    # Empty members are manually supported before each real installed-to-park unlock.
    for pin in unlock_setup:withdraw([pin['instance']],tuple(pin['delta_mm']),'unlock_installed_to_park',False)
    # Upper: pins, cap screws/nuts, then caps; empty upper at24mm opening.
    ids=[k for k in shapes if k.startswith('PRT-0603-R4-HOLDPIN-')];withdraw(ids,(0,0,distance),'upper_lock_pins')
    ids=[k for k in shapes if k.startswith('PRT-0603-R4-CAP-') and k.endswith('-SCREW')]
    for id in ids:access(id,2,1)
    withdraw(ids,(0,0,distance),'upper_cap_screws')
    ids=[k for k in shapes if k.startswith('PRT-0603-R4-CAP-') and k.endswith('-NUT')]
    for id in sorted(ids,key=lambda k:abs((exact_bbox(shapes[k]).ymin+exact_bbox(shapes[k]).ymax)/2),reverse=True):
        access(id,1,1 if exact_bbox(shapes[id]).ymin>0 else -1,wrench=True);withdraw([id],(0,0,-distance),'upper_cap_nuts_outer_first')
    withdraw([k for k in shapes if k.startswith('PRT-0603-R4-BUSHCAP-')],(0,0,lift),'upper_caps')
    # Gate: retract holding pin, unfasten caps, slide nuts outward below bush.
    withdraw([k for k in shapes if k=='PRT-0604-R4-HOLDPIN'],(0,0,distance),'gate_lock_pin')
    ids=[k for k in shapes if k.startswith('PRT-0604-R4-CAP-') and k.endswith('-SCREW')]
    for id in ids:access(id,2,1)
    withdraw(ids,(0,0,distance),'gate_cap_screws')
    for id in [k for k in shapes if k.startswith('PRT-0604-R4-CAP-') and k.endswith('-NUT')]:
        center=(exact_bbox(shapes[id]).ymin+exact_bbox(shapes[id]).ymax)/2;guide_center=(1 if center>0 else -1)*s['manual_guides']['gate']['shaft_y_abs'];sign=1 if center>guide_center else -1;access(id,1,sign,wrench=True);withdraw([id],(0,sign*distance,0),'gate_cap_nuts')
    withdraw([k for k in shapes if k.startswith('PRT-0604-R4-BUSHCAP-')],(0,0,lift),'gate_caps')
    ids=[k for k in shapes if k.startswith('PRT-0703-R4-ENDSTOP-') and k.endswith('-SCREW')]
    for id in ids:access(id,0,1,'M2')
    withdraw(ids,(distance,0,0),'slide_stop_screws');withdraw([k for k in shapes if k.startswith('PRT-0703-R4-ENDSTOP-') and not k.endswith('-SCREW')],(distance,0,0),'slide_stops')
    for sign in [-1,1]:
        id='PRT-0607-R4-UPSTOP-'+str(sign)+'-SCREW';access(id,1,sign);withdraw([id],(0,sign*distance,0),'sleeve_stop_screw');withdraw(['PRT-0607-R4-UPSTOP-'+str(sign)],(0,sign*distance,0),'sleeve_stop')
    # Clamp lower nuts: specified candidate socket from underside, then lift pins.
    withdraw([k for k in shapes if k.startswith('PRT-0702-R4-HOLDPIN-')],(0,0,distance),'clamp_lock_pins')
    for id in [k for k in shapes if k.startswith('PRT-0702-R4-TRAVELNUT-')]:
        bb=exact_bbox(shapes[id]);start=[(bb.xmin+bb.xmax)/2,(bb.ymin+bb.ymax)/2,bb.zmin];end=[*start[:2],start[2]-cfg['M4_nut_socket_length_mm']];exclude={id,id.replace('TRAVELNUT','TRAVELPIN')};hh=hits(cylinder(cfg['M4_nut_socket_radius_mm'],start,end),exclude);tools.append(dict(instance=id,tool='proposed_M4_lower_nut_socket',intersections=hh,status='PASS' if not hh else 'FAIL'))
        if hh:failed_parts.add(id)
        withdraw([id],(0,0,-s['service']['clamp_nut_initial_drop_mm']),'clamp_lower_nuts_drop',False);withdraw([id],(0,(1 if start[1]>0 else -1)*s['service']['clamp_nut_side_withdraw_mm'],0),'clamp_lower_nuts_side')
    for id in [k for k in shapes if k.startswith('PRT-0702-R4-TRAVELPIN-')]:
        nut=id.replace('TRAVELPIN','TRAVELNUT')
        if nut not in removed:failed_parts.add(id);blocked_dependencies[id]=nut
        withdraw([id],(0,0,distance),'clamp_travel_pins')
    return dict(status='PASS' if all(v['status']=='PASS' for v in paths+tools) else 'FAIL',paths=paths,unlock_setup=unlock_setup,candidate_tool_channels=tools,actually_removed=sorted(removed),actual_tool_selection='OPEN',human_hand_access='OPEN')

def ball_sequence_checks(rows,refs,s,p,open_mm,implementation):
    """Nominal supported open approach; no reference after assumed boundary handoff."""
    from cad.assemblies.kinematics import capture_stroke
    cfg=s['inspection']['ball_sequence'];limit=s['inspection']['collision_threshold_mm3'];release=p['clear_stroke'];capture=capture_stroke(p);approach=(release+capture)/2;base=dict(height=s['local_height_mm'],slide=0,guide=0,clamp=open_mm,upper=0,gate=0)
    sequence=[('OPEN_LOAD',{},True,'free nominal settled pose on land; no motion parent'),('CLOSED_GRIP',{'clamp':0},True,'assumed nominal captured pose; holding force unproved'),('GUIDE_UP',{'clamp':0,'guide':p['guide_stroke']},True,'assumed nominal captured pose; no sleeve-driven ball movement'),('CLEAR',{'clamp':0,'guide':p['guide_stroke'],'slide':p['clear_stroke']},True,'explicit prescribed carried pose; not grasp proof'),('RELEASE',{'clamp':open_mm,'guide':p['guide_stroke'],'slide':release},True,'control opens clamp at clear; ball assumed still seated on support, not departed'),('APPROACH_OPEN',{'clamp':open_mm,'guide':p['guide_stroke'],'slide':approach},True,'prescribed supported open-jaw approach; following support is a nominal contact assumption, not grasp or trajectory proof'),('CAPTURE_BOUNDARY',{'clamp':open_mm,'guide':p['guide_stroke'],'slide':capture},True,'prescribed supported reference at ideal capture boundary; assumed handoff only, wheels absent and actual capture NOT_RUN'),('EMPTY_FORWARD',{'guide':p['guide_stroke'],'slide':p['carriage_total_stroke']},False,'ball omitted after assumed handoff; actual capture/free trajectory NOT_RUN'),('EMPTY_RETURN',{'guide':p['guide_stroke']},False,'empty carriage; no ball attached')]
    result=[]
    for name,over,present,ownership in sequence:
        state={**base,**over};bodies=posed(rows,state);indexed={a['instance_id']:sh for a,sh in bodies};hh=[];contact=[]
        if present:
            translated={id:sh.translate((state['slide'],0,0)) for id,sh in refs}
            for id,ref in translated.items():
                for a,sh in bodies:
                    # Exact reference intersections; fixture context never removed.
                    bb=exact_bbox(ref);ob=exact_bbox(sh)
                    if bb.xmin<=ob.xmax and ob.xmin<=bb.xmax and bb.ymin<=ob.ymax and ob.ymin<=bb.ymax and bb.zmin<=ob.zmax and ob.zmin<=bb.zmax:
                        v=ref.intersect(sh).Volume()
                        if v>limit:hh.append(dict(reference=id,instance=a['instance_id'],volume_mm3=v))
            cork=translated['PRT-REF-CORK'];distance=cork.distance(indexed['PRT-0701-A']);contact.append(dict(contact='cork_bottom_to_integral_land',distance_mm=distance,maximum_mm=cfg['seat_contact_tolerance_mm'],status='PASS' if distance<=cfg['seat_contact_tolerance_mm'] else 'FAIL'))
            for side in ['L','R']:
                distance=cork.distance(indexed['PRT-0702__'+side]);closed=state['clamp']==0;ok=distance<=cfg['closed_jaw_nominal_gap_mm'] if closed else distance>=open_mm-cfg['closed_jaw_nominal_gap_mm']
                contact.append(dict(contact='jaw_'+side,assumption='nominal closed clearance, not frictional holding' if closed else 'open non-contact',distance_mm=distance,status='PASS' if ok else 'FAIL'))
        result.append(dict(name=name,state=state,ball_present=present,reference_translation_mm=[state['slide'],0,0] if present else None,ownership_rule=ownership,intersections=hh,expected_contacts=contact,status='PASS' if not hh and all(v['status']=='PASS' for v in contact) else 'FAIL'))
    return dict(status='PASS' if all(v['status']=='PASS' for v in result) else 'FAIL',stages=result,post_release_trajectory='NOT_RUN',grasp_and_release_dynamics='NOT_RUN',whole_machine_wheel_clearance='NOT_RUN',actual_capture='NOT_RUN',historical_animation_release_used=False,control_release_slide_mm=release,ideal_capture_slide_mm=capture)

def endpoint_pin_acceptance(pin_row,endpoint,placed,s,p):
    """Require actual pin material across the mover and material around its bore."""
    axis=pin_row['lock_axis'];g=s['manual_guides']['holding'][axis];cfg=s['inspection']['retention'];q=cfg['fixture_probe_box_mm'];id=pin_row['instance_id'];side=id.split('-')[-1];sign=1 if side=='L' else -1
    if axis=='upper':center=[p['load_x']+g['x_offset'],sign*g['fixed_y_abs'],s['manual_guides']['upper']['z']];along=2;moving='PRT-0603-R3-CARRIER-'+side
    elif axis=='gate':center=[g['x'],g['y'],s['manual_guides']['gate']['z']];along=2;moving='PRT-0604'
    elif axis=='guide':center=[g['x'],0,g['fixed_z'][g['endpoints_mm'].index(endpoint)]];along=1;moving='PRT-0607-B'
    elif axis=='slide':center=[g['fixed_x'][g['endpoints_mm'].index(endpoint)],g['y'],sum(s['manual_guides']['slide']['moving_flange_z'])/2];along=2;moving='PRT-0703-C'
    else:center=[g['x'],sign*g['fixed_y_abs'],sum(s['manual_guides']['clamp']['arm_rear_extension']['z'])/2];along=2;moving='PRT-0702-A__'+side
    first=list(center);last=list(center);first[along]-=q/2;last[along]+=q/2
    core=cylinder(g['pin_radius']-cfg['shell_inner_margin_mm'],first,last);shell=cylinder(g['bore_radius']+cfg['lock_shell_outer_margin_mm'],first,last).cut(cylinder(g['bore_radius']+cfg['lock_shell_inner_margin_mm'],first,last));pin_fraction=core.intersect(pin_row['installed_shape']).Volume()/core.Volume();mover_fraction=shell.intersect(placed[moving]).Volume()/shell.Volume();minimum=cfg['minimum_material_fraction'];checks=[dict(check='actual_pin_crosses_moving_member',material_fraction=pin_fraction,status='PASS' if pin_fraction>=minimum else 'FAIL'),dict(check='moving_member_surrounds_pin_bore',material_fraction=mover_fraction,status='PASS' if mover_fraction>=minimum else 'FAIL')]
    return dict(status='PASS' if all(v['status']=='PASS' for v in checks) else 'FAIL',checks=checks,load_and_detent_rating='OPEN')
