"""Exact B-rep collision and connection checks for the R3 low-speed fixture."""
from pathlib import Path
import sys,json,math
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import cadquery as cq
from cad.assemblies.r3_fixture import model,posed
from cad.export_all import exact_bbox
from tools.check_collisions import bbox,overlaps

def run():
    rows,variants,s,b=model();limit=s['inspection']['collision_threshold_mm3'];base={**b['state'],'guide':0,'upper':0,'gate':0};tested=0;hits=[]
    def check(state,label,only_moved=None):
        nonlocal tested
        shapes=posed(rows,state);bounds=[bbox(sh) for _,sh in shapes]
        for n,(a,sh) in enumerate(shapes):
            for j,(c,other) in enumerate(shapes[:n]):
                if only_moved and a['parent'] not in only_moved and c['parent'] not in only_moved and not a.get('dynamic_slide') and not c.get('dynamic_slide'):continue
                if only_moved and a['kind']=='context' and c['kind']=='context':continue
                if overlaps(bounds[n],bounds[j]):
                    tested+=1;volume=sh.intersect(other).Volume()
                    if volume>limit:hits.append(dict(state=label,pair=[a['instance_id'],c['instance_id']],volume_mm3=volume))
    check(base,'STATIC')
    static_hits=list(hits)
    if '--static' not in sys.argv:
        impl=json.loads((R/'data/implementation.json').read_text(encoding='utf-8'))['demo']
        design={k:v['value'] for k,v in json.loads((R/'data/design.json').read_text(encoding='utf-8'))['parameters'].items()}
        slide_end=next(j['range'][1] for j in json.loads((R/'data/joints.json').read_text(encoding='utf-8')) if j['id']=='J05')
        paths=[('upper',impl['upper_open_mm'],{'UPPER_L','UPPER_R'},{}),('gate',impl['gate_open_mm'],{'LOWER_GATE'},{}),('guide',design['guide_stroke'],{'GUIDE_SLEEVE'},{}),('slide',slide_end,{'CARRIAGE','CLAMP_L','CLAMP_R'},{'guide':design['guide_stroke']}),('clamp',impl['clamp_open_mm'],{'CLAMP_L','CLAMP_R'},{'guide':design['guide_stroke'],'slide':design['clear_stroke']})]
        states=1
        for key,end,moved,override in paths:
            for n in range(1,math.ceil(end/s['inspection']['motion_step_mm'])+1):
                v=min(n*s['inspection']['motion_step_mm'],end);check({**base,**override,key:v},f'{key}={v}',moved);states+=1
            print('checked',key,flush=True)
        for n in range(math.ceil(s['service']['upper_withdraw_mm']/s['inspection']['motion_step_mm'])+1):
            v=min(n*s['inspection']['motion_step_mm'],s['service']['upper_withdraw_mm']);check({**s['service']['tool_pose'],'upper':v},f'SERVICE_UPPER={v}',{'UPPER_L','UPPER_R'});states+=1
    else:states=1
    # Every structural nut must lie fully on its rod, with protrusion at both ends.
    indexed={a['instance_id']:a for a in rows};engagement=[]
    for a in rows:
        if 'rod_id' not in a:continue
        rod=indexed[a['rod_id']];z0,z1=rod['rod_z'];n0,n1=a['engagement_z'];assert z0<n0<n1<z1,a['instance_id']
        engagement.append(dict(nut=a['instance_id'],full_axial_overlap=True,rod_end_margins_mm=[n0-z0,z1-n1]))
    # No claim for threaded tooth interference: the actual thread is a BOM interface.
    valid=all(a['shape'].isValid() and len(a['shape'].Solids())==1 for a in rows+variants)
    tools=[];tool_hits=[];service_shapes=posed(rows,s['service']['tool_pose'])
    for a,sh in service_shapes:
        if 'SCREW-' in a['instance_id'] and a['family']=='PRT-0603-R3-SCREW-M4x25':
            bb=exact_bbox(sh);x=(bb.xmin+bb.xmax)/2;y=(bb.ymin+bb.ymax)/2
            tool=cq.Solid.makeCylinder(s['inspection']['tool_M4_radius'],s['inspection']['tool_M4_length'],cq.Vector(x,y,bb.zmax))
            tools.append((a['instance_id'],tool,{a['instance_id']}))
        elif a['family']=='PRT-0603-R3-NUT-M4':
            bb=exact_bbox(sh);x=(bb.xmin+bb.xmax)/2;y=(bb.ymin+bb.ymax)/2
            tool=cq.Solid.makeCylinder(s['inspection']['tool_M4_nut_radius'],s['inspection']['tool_M4_nut_length'],cq.Vector(x,y,bb.zmin),cq.Vector(0,0,-1))
            tools.append((a['instance_id'],tool,{a['instance_id'],a['instance_id'].replace('-NUT-','-SCREW-')}))
        elif a['instance_id'].endswith('-NUT-UP'):
            bb=exact_bbox(sh);x=(bb.xmin+bb.xmax)/2;y=(bb.ymin+bb.ymax)/2
            tool=cq.Solid.makeCylinder(s['inspection']['tool_M6_radius'],s['inspection']['tool_M6_length'],cq.Vector(x,y,bb.zmin))
            root=a['instance_id'].removesuffix('-NUT-UP');tools.append((a['instance_id'],tool,{a['instance_id'],root+'-ROD',root+'-WASHER-UP'}))
    for name,tool,targets in tools:
        for a,sh in service_shapes:
            if a['instance_id'] in targets:continue
            if overlaps(bbox(tool),bbox(sh)):
                v=tool.intersect(sh).Volume()
                if v>limit:tool_hits.append(dict(tool_for=name,obstruction=a['instance_id'],volume_mm3=v))
    report=dict(status='PASS' if not hits and not tool_hits and valid else 'FAIL',instances=len(rows),jaw_variants=len(variants),states=states,exact_pair_intersections=tested,static_intersections=static_hits,motion_intersections=[x for x in hits if x['state']!='STATIC'],all_native_single_solids=valid,rod_nut_checks=engagement,tool_channels=len(tools),tool_intersections=tool_hits,tool_pose=s['service']['tool_pose'],motion_scope='指定各轴路径与40mm上夹检修抽出采样；运动仅检查涉及R3新件/改件的配对，不重复原context-context配对；不是任意轴组合或连续扫掠证明',tool_scope='4处M4头部直杆、4处M4下螺母反扭工具、16处M6上螺母；不包含M6底螺母/台面/支撑作业验证',thread_tooth_modelled=False,structural_strength_verified=False,physical_testing_performed=False)
    (R/'reports/r3_geometry_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(report['status'],len(hits),'intersections;',states,'states;',tested,'exact pair checks')
    for h in hits[:30]:print(h)
    for h in tool_hits[:20]:print(h)
    return not hits and not tool_hits and valid
if __name__=='__main__':raise SystemExit(0 if run() else 1)
