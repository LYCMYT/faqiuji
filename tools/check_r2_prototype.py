"""Reopen independent exports and verify preparation/evidence boundaries."""
from pathlib import Path
import sys,json,csv,math
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import cadquery as cq
import fitz
from PIL import Image,ImageDraw
O=R/'output/prototype_r2'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rows(p):
    with (O/p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
s=read(R/'data/r2_prototype.json');coupons=read(O/'coupon_index.json');build_report=read(R/'reports/r2_build_validation.json')
results=[]
for a in coupons:
    native=cq.importers.importStep(str(O/'step'/(a['part_id']+'.step'))).val()
    dxf=cq.importers.importDXF(str(O/'dxf'/(a['part_id']+'.dxf'))).wires().toPending().extrude(a['bbox_z_mm']).val()
    delta=abs(native.Volume()-dxf.Volume())
    assert native.isValid() and dxf.isValid() and len(native.Solids())==len(dxf.Solids())==1
    assert delta<.01,(a['part_id'],delta)
    symmetric=native.cut(dxf).Volume()+dxf.cut(native).Volume()
    assert symmetric<.02,(a['part_id'],symmetric)
    results.append(dict(part_id=a['part_id'],step_valid=True,dxf_closed=True,dxf_extrusion_valid=True,volume_difference_mm3=delta,symmetric_difference_mm3=symmetric))
planned=rows('sample_register_PLAN.csv');measure=rows('measurements_PLAN.csv');trials=rows('screening_trials_PLAN.csv');routes=rows('manufacturing_routes_44_RFQ.csv')
assert len(planned)==sum(g['planned_count'] for g in s['samples'])
assert len(set(a['sample_id'] for a in planned))==len(planned)
for g in s['samples']:
    assert g['planned_count']==g['tubes']*g['published_per_tube']
    assert sum(a['sample_id'].startswith(g['group']+'-') for a in planned)==g['planned_count']
assert all(a['status']=='PLANNED_NOT_RECEIVED' and not a['actual_batch'] and not a['received_date'] for a in planned)
assert len(measure)==len(planned)*s['measurement']['repeats']
assert all(not a[k] for a in measure for k in a if k not in ['sample_id','repeat','status'])
assert all(not a[k] for a in trials for k in ['actual_cycles','result','single_feed_count','double_feed_count','damage_count','jam_count'])
e=read(O/'evidence_status.json')
assert not e['manufacturing_release'] and all(not e[k] for k in ['orders','physical_measurements','supplier_confirmations','prototype_results'])
assert {a['part_id'] for a in routes}=={a['part_id'] for a in read(R/'data/parts.json')}
pdf=fitz.open(O/'BM1_R2_sample_manufacturing_manual.pdf');review=R/'tmp/pdfs/r2_review';review.mkdir(parents=True,exist_ok=True)
assert len(pdf)==6+math.ceil(len(routes)/8)+len(coupons)+2, 'Unexpected spillover/orphan page'
overflow=[];pages=[]
for n,p in enumerate(pdf):
    for b in p.get_text('blocks'):
        if b[0]<-1 or b[1]<-1 or b[2]>p.rect.width+1 or b[3]>p.rect.height+1:overflow.append(dict(page=n+1,box=b[:4]))
    assert len(p.get_text().strip())>25
    pix=p.get_pixmap(matrix=fitz.Matrix(1.1,1.1));path=review/f'page_{n+1:02d}.png';pix.save(path);pages.append(path)
assert not overflow,overflow
alltext='\n'.join(p.get_text() for p in pdf)
for a in coupons:assert a['part_id'] in alltext
contact=Image.new('RGB',(1000,math.ceil(len(pages)/3)*260),'white');draw=ImageDraw.Draw(contact)
for n,path in enumerate(pages):
    im=Image.open(path);im.thumbnail((320,235));x=(n%3)*333;y=(n//3)*260;contact.paste(im,(x,y));draw.text((x+8,y+236),str(n+1),fill='black')
contact.save(review/'contact.png')
report=dict(status='PASS',scope='R2新增试配毛件与计划文件；不重新声称R1整机或实物通过',step_dxf_roundtrips=results,pdf_pages=len(pdf),pdf_text_overflow=overflow,planned_samples=len(planned),planned_measurement_rows=len(measure),planned_screening_cells=len(trials),manufacturing_routes=len(routes),physical_evidence_empty=True,manufacturing_release=False)
(R/'reports/r2_delivery_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('R2 PASS:',len(results),'STEP/DXF equivalence;',len(pdf),'PDF pages;',len(planned),'samples;',len(routes),'routes; no physical evidence')
