"""R4 nominal support and full-context discrete collision diagnostic; never release proof."""
from pathlib import Path
import sys,json,math
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import cadquery as cq
from cad.assemblies.r4_fixture import model,posed
from cad.assemblies.kinematics import parameters,motion_limits
from cad.parts.recipe import build
from cad.export_all import exact_bbox
from tools.check_collisions import bbox,overlaps
from tools.build_context import active_context,atomic_json

def run():
    mode='static' if '--static' in sys.argv else 'full';ctx=active_context(R,'r4_geometry',mode)
    out=R/'reports'/('r4_geometry_static.json' if mode=='static' else 'r4_geometry_validation.json')
    atomic_json(out,ctx.report('RUNNING'))
    rows,variants,s,b=model();p=parameters();open_mm=motion_limits()['clamp'][1];base=dict(height=s['local_height_mm'],guide=0,slide=0,clamp=open_mm,upper=0,gate=0)
    limit=s['inspection']['collision_threshold_mm3'];hits=[];states=[];exact=0
    def check(state,label):
        nonlocal exact
        bodies=posed(rows,state);bb=[bbox(sh) for _,sh in bodies];states.append(dict(name=label,state=state))
        for i,(a,sh) in enumerate(bodies):
            for j,(c,other) in enumerate(bodies[:i]):
                if overlaps(bb[i],bb[j]):
                    exact+=1;v=sh.intersect(other).Volume()
                    if v>limit:hits.append(dict(state=label,pair=[a['instance_id'],c['instance_id']],volume_mm3=v))
        return bodies
    bodies=check(base,'OPEN_LOAD')
    refs=[a for a in json.loads((R/'data/geometry.json').read_text(encoding='utf-8'))['instances'] if a.get('reference') and a['instance_id'] in ['PRT-REF-CORK','PRT-REF-SKIRT']]
    refs=[(a['instance_id'],build(a['shape'],p)) for a in refs];cork=refs[0][1]
    contacts=[]
    for a,sh in bodies:
        common=cork.intersect(sh);area=sum(f.Area() for f in common.Faces()) if common.Volume()<1e-7 else 0
        # Intersections of coplanar faces preserve exact planar contact regions.
        for f in cork.Faces():
            fb=exact_bbox(f)
            if abs(fb.zmin-p['cork_z_min'])<1e-6 and abs(fb.zmax-p['cork_z_min'])<1e-6:
                q=f.intersect(sh);ar=q.Area()
                if ar>1e-5:
                    qb=exact_bbox(q);contacts.append(dict(instance=a['instance_id'],area_mm2=ar,bbox=[qb.xmin,qb.ymin,qb.xmax,qb.ymax],axis_inside_contact=bool(q.isInside(cq.Vector(p['load_x'],0,p['cork_z_min']),1e-6))))
    perturb=[]
    for axis in [(0,1,0),(1,0,0)]:
        for deg in s['inspection']['perturbation_deg']:
            # Free reference is transformed independently of carriage parents.
            pivot=(p['load_x'],0,p['cork_z_min']);end=tuple(x+y for x,y in zip(pivot,axis));hh=[]
            for name,ref in refs:
                moved=ref.rotate(pivot,end,deg)
                for a,sh in bodies:
                    if overlaps(bbox(moved),bbox(sh)):
                        v=moved.intersect(sh).Volume()
                        if v>limit:hh.append(dict(reference=name,instance=a['instance_id'],volume_mm3=v))
            perturb.append(dict(axis=axis,deg=deg,hits=hh))
    translations=[]
    probe=s['inspection']['free_translation_mm']
    for delta in [(0,0,-probe),(probe,0,0),(-probe,0,0),(0,probe,0),(0,-probe,0)]:
        hh=[]
        for name,ref in refs:
            moved=ref.translate(delta)
            for a,sh in bodies:
                if overlaps(bbox(moved),bbox(sh)):
                    v=moved.intersect(sh).Volume()
                    if v>limit:hh.append(dict(reference=name,instance=a['instance_id'],volume_mm3=v))
        translations.append(dict(delta_mm=delta,hits=hh))
    paths=[]
    if mode=='full':
        lim=motion_limits();paths=[('upper',{},0,lim['upper'][1]),('gate',{},0,lim['gate'][1]),('clamp',{},open_mm,0),('guide',{'clamp':0},0,lim['guide'][1]),('slide',{'clamp':0,'guide':lim['guide'][1]},0,p['clear_stroke']),('clamp',{'guide':lim['guide'][1],'slide':p['clear_stroke']},0,open_mm),('slide',{'guide':lim['guide'][1],'clamp':open_mm},p['clear_stroke'],lim['slide'][1]),('slide',{'guide':lim['guide'][1],'clamp':open_mm},lim['slide'][1],0)]
        for n,(key,over,start,end) in enumerate(paths):
            count=math.ceil(abs(end-start)/s['inspection']['motion_step_mm'])
            for j in range(count+1):check({**base,**over,key:start+(end-start)*j/count},f'PATH{n}:{key}={start+(end-start)*j/count:g}')
            print('checked',n,key,flush=True)
    native=all(a['shape'].isValid() and len(a['shape'].Solids())==1 for a in rows+variants)
    interfaces=json.loads((R/'data/r4_mechanical_interfaces.json').read_text(encoding='utf-8'));indexed={a['instance_id']:sh for a,sh in bodies}
    connections=[]
    for a in interfaces['axes']:
        endpoints=[]
        for value in a['limits']['nominal_mm']:
            st={**base,a['axis_id']:value}
            if a['axis_id']=='slide':st['guide']=p['guide_stroke']
            placed={q['instance_id']:sh for q,sh in posed(rows,st)};moving=placed[a['moving_instance']];fixed=placed[a['fixed_instance']]
            endpoints.append(dict(value_mm=value,distance_mm=moving.distance(fixed),overlap_mm3=moving.intersect(fixed).Volume()))
        connections.append(dict(axis_id=a['axis_id'],endpoints=endpoints,status='NATIVE_GEOMETRY_INSPECTED_LOAD_HOLDING_OPEN',reason=a['guide_pair']['description'],reaction_path=a['reaction_path']))
    locks=[]
    for a in rows:
        if 'installed_shape' not in a:continue
        for end in a['lock_endpoints_mm']:
            st={**base,a['lock_axis']:end}
            if a['lock_axis']=='slide':st['guide']=p['guide_stroke']
            hh=[];pin=a['installed_shape']
            for c,sh in posed(rows,st):
                if c['instance_id']==a['instance_id']:continue
                if overlaps(bbox(pin),bbox(sh)):
                    v=pin.intersect(sh).Volume()
                    if v>limit:hh.append(dict(instance=c['instance_id'],volume_mm3=v))
            locks.append(dict(pin=a['instance_id'],axis=a['lock_axis'],endpoint_mm=end,installed_intersections=hh,park_delta_mm=a['park_delta_mm'],holding_strength='OPEN',detent_and_tether='OPEN'))
    reaction_pairs=[('PRT-0602-C__L410','PRT-0602-A__L'),('PRT-0602-C__R410','PRT-0602-A__R'),('PRT-0602-G','PRT-0602-A__L'),('PRT-0602-G','PRT-0602-A__R'),('PRT-0607-A','PRT-0607-C'),('PRT-0607-C','PRT-0602-G'),('PRT-0701-C','PRT-0701-A'),('PRT-0703-C','PRT-0701-A'),('PRT-0703-A','PRT-0703-R3-SHOE-1-1'),('PRT-0703-R3-SHOE-1-1','PRT-0703-R3-CAP-1-UP'),('PRT-0703-R3-CAP-1-UP','PRT-0703-R3-TUBE-1'),('PRT-0703-R3-TUBE-1','PRT-0703-R3-CAP-1-LOW'),('PRT-0703-R3-CAP-1-LOW','PRT-0602-R3-BASE')]
    reaction_contacts=[dict(pair=[a,c],distance_mm=indexed[a].distance(indexed[c]),overlap_mm3=indexed[a].intersect(indexed[c]).Volume(),connection_rating='OPEN; nominal mating contact only, not weld/fastener load approval') for a,c in reaction_pairs]
    # Real R3 threaded-stack engagement check retained; does not close actuator guides.
    rods={a['instance_id']:a for a in rows};engagement=[]
    for a in rows:
        if 'rod_id' in a:
            z0,z1=rods[a['rod_id']]['rod_z'];n0,n1=a['engagement_z'];engagement.append(dict(instance=a['instance_id'],engaged=z0<n0<n1<z1))
    # Explicit maintenance sequence: empty/support upper members, withdraw cap
    # fasteners, lift both split caps, lift the upper assembly 6mm, withdraw40mm.
    removed=[a['instance_id'] for a in rows if a['instance_id'].startswith(('PRT-0603-R4-CAP-','PRT-0603-R4-BUSHCAP-','PRT-0603-R4-HOLDPIN-'))]
    service_hits=[];service=[]
    for lift,opening in [(v,s['service']['upper_work_open_mm']) for v in s['service']['lift_samples_mm']]+[(s['service']['upper_lift_mm'],v) for v in s['service']['withdraw_samples_mm']]:
        ss=[]
        for a,sh in posed(rows,{**base,'upper':opening,'guide':p['guide_stroke']}):
            if a['instance_id'] in removed:continue
            if a['parent'] in ['UPPER_L','UPPER_R']:sh=sh.translate((0,0,lift))
            ss.append((a,sh))
        for i,(a,sh) in enumerate(ss):
            for c,other in ss[:i]:
                if a['parent'] not in ['UPPER_L','UPPER_R'] and c['parent'] not in ['UPPER_L','UPPER_R']:continue
                if overlaps(bbox(sh),bbox(other)):
                    v=sh.intersect(other).Volume()
                    if v>limit:service_hits.append(dict(lift_mm=lift,upper_mm=opening,pair=[a['instance_id'],c['instance_id']],volume_mm3=v))
        service=ss
    tool_hits=[];tool_count=0
    for a,sh in service:
        if a['family']=='PRT-0603-R3-SCREW-M4x25':
            bb=exact_bbox(sh);tool_input=json.loads((R/'data/r3_fixture.json').read_text(encoding='utf-8'))['inspection'];tool=cq.Solid.makeCylinder(tool_input['tool_M4_radius'],tool_input['tool_M4_length'],cq.Vector((bb.xmin+bb.xmax)/2,(bb.ymin+bb.ymax)/2,bb.zmax));tool_count+=1
            for c,other in service:
                if c['instance_id']==a['instance_id']:continue
                if overlaps(bbox(tool),bbox(other)):
                    v=tool.intersect(other).Volume()
                    if v>limit:tool_hits.append(dict(tool_for=a['instance_id'],obstruction=c['instance_id'],volume_mm3=v))
    completed=['native_solids','support_projection','free_motion_probe','connections','tool_channels']+(['sampled_motion'] if mode=='full' else [])
    report=ctx.report('BLOCKED',completed,reference_geometry={'type':'nominal visual cork/skirt','axis_mm':[p['load_x'],0],'cork_bottom_z_mm':p['cork_z_min'],'real_samples':[]},expected_contacts=contacts,support_projection={'status':'PASS_NOMINAL' if any(a['axis_inside_contact'] for a in contacts) else 'FAIL','claim':'Vertical gravity projection only; friction/impact/lateral capture not proven'},free_motion_probe={'rotations':perturb,'translations':translations,'lateral_retention':'Not claimed from planar support; inspect free lateral probe results'},clearances={'all_context_pairs_checked':True,'threshold_mm3':limit,'intersections':hits,'exact_pair_checks':exact},assumptions=['R3 local height=0, no wheel solids in fixture; no full-machine wheel clearance claim','No ball attached to animation parent during perturbation','Five native captive guide candidates examined; holding, cap assembly, weld/fastener and strength remain OPEN','Specified M4 tool envelopes tested after explicit empty-supported upper cap removal +6mm lift +40mm withdrawal; cap/fastener withdrawal path and new M3/M2 tooling NOT_RUN'],all_native_single_solids=native,states=states,connections=connections,manual_endpoint_locks=locks,reaction_path_contacts=reaction_contacts,rod_engagement=engagement,service_sequence={'removed_parts':removed,'upper_lift_mm':s['service']['upper_lift_mm'],'upper_withdraw_mm':s['service']['upper_withdraw_mm'],'intersections':service_hits,'cap_and_fastener_withdrawal':'NOT_RUN'},tool_channels=tool_count,tool_intersections=tool_hits,tool_status='FAIL' if tool_hits else 'PASS_SPECIFIED_ENVELOPES',motion_scope='All fixture context-context pairs at each explicitly sampled endpoint-inclusive path; not continuous or arbitrary simultaneous motion',continuous_motion='NOT_RUN',physical_testing_performed=False,manufacturing_release=False)
    atomic_json(out,report);print('BLOCKED',len(hits),'collisions;',len(states),'states;',exact,'pairs; support',report['support_projection']['status']);return False
if __name__=='__main__':raise SystemExit(0 if run() else 1)

