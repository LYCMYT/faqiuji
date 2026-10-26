from pathlib import Path
import sys,json,math
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from control.feed_cycle import FeedCycle
from cad.assemblies.kinematics import capture_stroke,permitted,parameters
from cad.parts.cable import return_loop_points,loop_geometry
from cad.parts.recipe import number
spec=json.loads((R/'data/r1_engineering.json').read_text(encoding='utf-8'))
c=FeedCycle();s=dict(start=False,cover_closed=True,estop_ok=True,cassette_locked=True,exit=False,capture_detected=False,head_home=True,slide_home=True,slide_clear=False,aim_reached=False,guide_up=True,guide_down=False,gate_closed=True,gate_open=False,clamp_closed=False,clamp_open=True)
steps=[{},dict(start=True),dict(guide_up=False,guide_down=True),dict(upper_held=True),dict(gate_open=True,gate_closed=False,ball_present=True),dict(gate_closed=True,gate_open=False),dict(clamp_closed=True,clamp_open=False),dict(guide_up=True,guide_down=False),dict(slide_clear=True,slide_home=False),dict(aim_reached=True,wheels_ready=True,head_home=False),dict(clamp_open=True,clamp_closed=False),dict(capture_detected=True,slide_clear=False),dict(exit=True),dict(exit=False),dict(slide_clear=True),dict(head_home=True),dict(slide_home=True)]
trace=[]
for i,change in enumerate(steps):
    s.update(change);out=c.step(s,.1);trace.append(dict(sample=i,input=s.copy(),output=out));assert c.state!='FAULT',out
assert c.state=='DONE'
faults=[]
for key in ['cover_closed','estop_ok','cassette_locked','guide_up','clamp_open']:
    f=FeedCycle();f.state='APPROACH';obs=dict(gate_closed=True,cover_closed=True,estop_ok=True,cassette_locked=True,guide_up=True,clamp_open=True,exit=False,capture_detected=False,wheels_ready=True)
    obs[key]=False;out=f.step(obs,.1);assert out['state']=='FAULT' and not out['enable_motion'] and not out['enable_wheels'];faults.append(dict(injected=key,output=out))
item=next(i for i in json.loads((R/'data/geometry.json').read_text(encoding='utf-8'))['instances'] if i['instance_id']=='PRT-0704-WIRE_A')
route=item['shape'];assert route==item['dynamic_loop'],'Blender cable recipe differs from CAD'
p=parameters();lengths=[];rad=(route['upper_z']-route['lower_z'])/2;L=route['length'];y=route['y'];ey=route['exit_y'];direction=route['direction']
assert rad==spec['cable']['slide_centerline_radius_mm'] and L==spec['cable']['slide_loop_length_mm']
for q in range(int(p['carriage_total_stroke'])+1):
    fx=number(route['fixed_x'],dict(p,slide=q));mx=number(route['moving_x'],dict(p,slide=q));lo=route['lower_z'];hi=route['upper_z']
    pts=return_loop_points(fx,mx,lo,hi,y,L,96,direction,ey)
    r,bx,cz=loop_geometry(fx,mx+direction*rad,lo,hi,L,direction)
    length=abs(fx-bx)+abs(mx+direction*rad-bx)+math.pi*r+math.pi*r/2+(ey-y-r)
    lengths.append(length);assert pts[-1]==(mx,ey,hi)
assert max(lengths)-min(lengths)<1e-8
report=dict(cycle_trace=trace,fault_cases=faults,full_cycle_passed=True,loaded_185_rejected=not permitted(dict(slide=185,clamp=14,loaded=True)),empty_185_permitted=permitted(dict(slide=185,clamp=14,loaded=False)),capture_first_tangency_stroke_mm=capture_stroke(),cable=dict(samples=186,analytic_length_min_mm=min(lengths),analytic_length_max_mm=max(lengths),minimum_centerline_radius_mm=rad,cable_radius_mm=2,minimum_inner_radius_mm=rad-2,supplier_minimum_radius_mm=None,supplier_compliance_verified=False),physical_test_results=[])
(R/'reports/r1_contract_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('R1 CONTRACTS PASS cycle',len(trace),'faults',len(faults),'cable length',lengths[0])
