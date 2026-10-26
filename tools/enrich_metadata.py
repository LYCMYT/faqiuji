import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
def read(name):return json.loads((R/'data'/name).read_text(encoding='utf-8'))
def write(name,v):(R/'data'/name).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
rows=read('instances.json');parts=read('parts.json');contacts=[]
for side in ['L','R']:
    contacts += [dict(pair=['PRT-0505__'+side,'PRT-REF-CORK'],type='elastic_contact',states=['ST08','ST09'],source='expected_contacts.json',condition='仅球头侧面；捕获阈值需实测'),dict(pair=['PRT-0702__'+side,'PRT-REF-CORK'],type='controlled_clamping',states=['ST04','ST05','ST06','ST07'],source='expected_contacts.json',condition='仅闭夹；鼻端形面待球型测量'),dict(pair=['PRT-0503-B__'+side,'PRT-0504__'+side],type='shaft_fit',states=['all'],source='expected_contacts.json',condition='孔轴候选尺寸，不是配合公差')]
write('contact_pairs.json',contacts)
materials=[]
for p in parts:
    materials.append(dict(part_id=p['part_id'],candidate=p['material_candidate'],color=p['color'],density_kg_m3=None,status='concept',supplier_model=None,finish=None))
write('materials.json',materials)
ex=read('exploded.json');ex['instances']=[]
for aid in [a['id'] for a in read('assemblies.json')]:
    subset=[i for i in rows if i['assembly_id']==aid]
    for n,i in enumerate(subset):ex['instances'].append(dict(instance_id=i['instance_id'],reference_parent=aid,translation_mm=[(n%3-1)*70,((n//3)%3-1)*70,n*23],order=n+1,anchor_mm=[(i['bounds_mm'][k]+i['bounds_mm'][k+3])/2 for k in range(3)]))
write('exploded.json',ex)
v=read('viewshots.json');v.extend([dict(id='VIEW-08',name='真实CAD剖切',plane='WORLD Y=0',keep='Y<=0',source='output/step/BM1_Y0_section.step'),dict(id='VIEW-09',name='维修路径',data='service_spaces.json'),dict(id='VIEW-10',name='高度链与三位置',parameter_source='design.json')]);v=list({x['id']:x for x in v}.values());v[0].update(yaw=0,pitch=0,pose_note='装载零位展示；倾转需先脱筒');write('viewshots.json',v)
for i in read('interfaces.json'):
    i['instance_ids']=[x['instance_id'] for x in rows if x['part_id'] in i['parts']]
    i['manufacturing_status']='concept; supplier hole patterns remain null'
    # Reconcile instance references in source definitions via a dedicated measured/model position listing.
    i['model_datums_status']='see instances.json and geometry.json; conceptual additions recorded in design_changes.md'
interfaces=read('interfaces.json')
for i in interfaces:i['instance_ids']=[x['instance_id'] for x in rows if x['part_id'] in i['parts']];i['manufacturing_status']='concept; supplier hole patterns remain null'
write('interfaces.json',interfaces)
print('Metadata expanded',len(rows),'instances')
