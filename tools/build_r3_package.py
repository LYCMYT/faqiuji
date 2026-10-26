"""Export detailed native connection kit, drawings, hole tables and mesh data."""
from pathlib import Path
import sys,json,csv,math,copy
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import cadquery as cq
from cad.assemblies.r3_fixture import model,posed
from cad.export_all import exact_bbox
from tools.render_cad_preview import render
from PIL import Image,ImageDraw,ImageFont
O=R/'output/fixture_r3'
for d in ['step/parts','step/sections','dxf','drawings']:(O/d).mkdir(parents=True,exist_ok=True)
rows,variants,s,b=model();validation=json.loads((R/'reports/r3_geometry_validation.json').read_text(encoding='utf-8'))
assert validation['status']=='PASS','Resolve actual interference before publication'
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def csvout(name,keys,items):
    with (O/name).open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(items)
state={**b['state'],'guide':0,'upper':0,'gate':0};placed=posed(rows,state)
assy=cq.Assembly(name='BM1_R3_LOW_SPEED_CONNECTION_VARIANT');groups={};meshes=[]
for a,sh in placed:
    colors={'context':'#8CA4AF','custom':'#E28362','revised_context':'#7DA99F','hardware':'#B8BEC4'};color=colors[a['kind']]
    rgb=tuple(int(color[j:j+2],16)/255 for j in (1,3,5));assy.add(sh,name=a['instance_id'],color=cq.Color(*rgb))
    vv,tt=sh.tessellate(.2,.2);bb=exact_bbox(sh)
    meshes.append(dict(instance_id=a['instance_id'],family=a['family'],part_id=a['part_id'],assembly_id=a['assembly_id'],kind=a['kind'],parent=a['parent'],color=color,vertices=[list(v.toTuple()) for v in vv],triangles=tt,bounds_mm=[bb.xmin,bb.ymin,bb.zmin,bb.xmax,bb.ymax,bb.zmax]))
    groups.setdefault(a['family'],[]).append(a)
assy.export(str(O/'step/BM1_R3_fixture_assembly.step'))
dump(O/'mesh.json',meshes)
render([(a['instance_id'],sh) for a,sh in placed],O/'drawings/assembly','BM1 R3 / 低速台架连接变体，驱动适配仍待确认')
render([(a['instance_id'],sh) for a,sh in placed if a['kind']!='context' and 'WALL' not in a['instance_id'] and '0603' not in a['instance_id']],O/'drawings/base_connections','BM1 R3 / 基板、压板、支柱、支脚与紧固件')
render([(a['instance_id'],sh) for a,sh in placed if '0603' in a['instance_id']],O/'drawings/jaw_connections','BM1 R3 / 可换夹块与托板；执行器侧连接待冻结')
# Real boolean half-sections of all placed bodies, at a stud plane and jaw screw plane.
compound=cq.Compound.makeCompound([sh for _,sh in placed]);bb=exact_bbox(compound)
sections=[]
for name,axis,position in [('SECTION_POST_Y',1,s['rail_posts']['bolt_y'][1]),('SECTION_JAW_X',0,json.loads((R/'data/design.json').read_text(encoding='utf-8'))['parameters']['load_x']['value'])]:
    mins=[bb.xmin,bb.ymin,bb.zmin];maxs=[bb.xmax,bb.ymax,bb.zmax];maxs[axis]=position
    cutter=cq.Solid.makeBox(*[hi-lo for lo,hi in zip(mins,maxs)],cq.Vector(*mins));cut=[]
    for a,sh in placed:
        q=sh.cut(cutter)
        if q.Volume()>.001:cut.append((a['instance_id'],q))
    sec=cq.Compound.makeCompound([q for _,q in cut]);cq.exporters.export(sec,str(O/'step/sections'/f'{name}.step'));render(cut,O/'drawings'/name,'BM1 R3 / 原生布尔剖切 '+name);sections.append(name)

font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19)
drawings=[];hole_rows=[];bom=[];checks=[]
all_families={**groups}
for a in variants:
    if a['family'] not in all_families:all_families[a['family']]=[a]
if (O/'parts_index.json').exists():
    old=json.loads((O/'parts_index.json').read_text(encoding='utf-8'))
    for a in old:
        if a['family'] not in all_families:
            obsolete=(O/'step/parts'/f'{a["family"]}.step').resolve()
            assert obsolete.parent==(O/'step/parts').resolve()
            if obsolete.exists():obsolete.unlink()
for family,items in all_families.items():
    a=items[0];sh=a['shape'];bb=exact_bbox(sh);offset=[bb.xmin,bb.ymin,bb.zmin];local=sh.translate(tuple(-v for v in offset));file=O/'step/parts'/f'{family}.step'
    cq.exporters.export(local,str(file));back=cq.importers.importStep(str(file)).val();assert back.isValid() and abs(back.Volume()-local.Volume())<.001
    checks.append(dict(file=file.relative_to(R).as_posix(),valid=True,solids=len(back.Solids()),volume_mm3=back.Volume()))
    bom.append(dict(family=family,quantity_in_assembly=len(groups.get(family,[])),quantity_for_optional_pair=1 if family not in groups else 0,kind=a['kind'],material=a['material'],dimensions_mm=[bb.xlen,bb.ylen,bb.zlen],instance_ids=[q['instance_id'] for q in items],local_origin_H_mm=offset,holes=a['holes'],step=file.relative_to(O).as_posix()))
    if a['kind'] not in ['custom','revised_context']:continue
    top=cq.Workplane('XY').add(local).faces('>Z').vals();wires=[]
    for face in top:
        z=exact_bbox(face).zmax
        wires.extend(w.translate((0,0,-z)) for w in face.Wires())
    cq.exporters.exportDXF(cq.Compound.makeCompound(wires),str(O/'dxf'/f'{family}.dxf'))
    for n,h in enumerate(a['holes'],1):
        hole_rows.append(dict(family=family,hole=n,axis=h.get('axis','Z'),x_local_mm=h['x']-bb.xmin,y_local_mm=h['y']-bb.ymin,z_local_mm=h.get('z',bb.zmax)-bb.zmin,diameter_mm=h['diameter'],counterbore_diameter_mm=h.get('counterbore_diameter'),counterbore_depth_mm=h.get('counterbore_depth'),purpose=h['purpose']))
    im=Image.new('RGB',(1500,1000),'#f4f7f9');d=ImageDraw.Draw(im);d.text((25,18),family+'  /  '+a['material'],font=font,fill='#183a4d')
    lengths=[bb.xlen,bb.ylen,bb.zlen];scale=min(530/max(lengths[0],lengths[1]),250/max(lengths[1],lengths[2]))
    def line(pts,fill='#183a4d',width=2):d.line(pts,fill=fill,width=width)
    for axes,origin,label in [((0,1),(350,255),'俯视 XY'),((0,2),(350,610),'正视 XZ'),((1,2),(1050,610),'侧视 YZ')]:
        for edge in local.Edges():
            vv,_=edge.sample(65 if edge.geomType()!='LINE' else 2)
            pp=[v.toTuple() for v in vv];xy=[(origin[0]+(p[axes[0]]-lengths[axes[0]]/2)*scale,origin[1]-(p[axes[1]]-lengths[axes[1]]/2)*scale) for p in pp];line(xy)
        d.text((origin[0]-70,origin[1]-165),label,font=font,fill='#087b80')
        x0=origin[0]-lengths[axes[0]]*scale/2;x1=origin[0]+lengths[axes[0]]*scale/2;y0=origin[1]+lengths[axes[1]]*scale/2+24
        line([(x0,y0-10),(x0,y0+10)]);line([(x1,y0-10),(x1,y0+10)]);line([(x0,y0),(x1,y0)])
        d.text(((x0+x1)/2-35,y0+5),f'{lengths[axes[0]]:.3f}',font=small,fill='#183a4d')
    d.text((810,105),'A：底面 / B：Y最小侧 / C：X最小侧',font=font,fill='#183a4d')
    texts=[f'外形 X {bb.xlen:.3f} × Y {bb.ylen:.3f} × Z {bb.zlen:.3f} mm',f'装配数量 {len(groups.get(family,[]))}；可选试配件 {int(family not in groups)}',f'源坐标原点：{bb.xmin:.3f}, {bb.ymin:.3f}, {bb.zmin:.3f}',f'线性询价公差 ±{s["inspection"]["linear_general_tolerance_mm"]} mm',f'孔坐标询价公差 ±{s["inspection"]["hole_position_coordinate_tolerance_mm"]} mm','本图为实体线框投影；DXF是顶面投影轮廓。','孔深/方向/沉孔见hole_table.csv与后附孔表。','不按PNG量图；螺纹简化孔不能当攻牙底孔。']
    if 'radius_mm' in a:texts.insert(1,f'球侧接触弧 R{a["radius_mm"]}；后端加长 {s["jaw"]["rear_extension_mm"]} mm')
    for n,t in enumerate(texts):d.text((810,155+n*37),t,font=small,fill='#183a4d')
    for n,h in enumerate(a['holes'],1):
        if h.get('axis','Z')=='Z':
            x=350+(h['x']-bb.xmin-bb.xlen/2)*scale;y=255-(h['y']-bb.ymin-bb.ylen/2)*scale;d.text((x+8,y+5),str(n),font=small,fill='#a4492b')
    d.text((25,920),'原生参数实体 / 首件加工评审候选 / 安装接口、紧固预载和结构承载仍须实物确认',font=font,fill='#183a4d');im.save(O/'drawings'/f'{family}.png')
    drawings.append(family)
csvout('hole_table.csv',['family','hole','axis','x_local_mm','y_local_mm','z_local_mm','diameter_mm','counterbore_diameter_mm','counterbore_depth_mm','purpose'],hole_rows)
csvout('BOM.csv',['family','quantity_in_assembly','quantity_for_optional_pair','kind','material','dimensions_mm'],[{k:a[k] for k in ['family','quantity_in_assembly','quantity_for_optional_pair','kind','material','dimensions_mm']} for a in bom])
csvout('first_article_inspection_BLANK.csv',['family','hole','actual_diameter_mm','actual_x_mm','actual_y_mm','actual_z_mm','actual_counterbore_depth_mm','material_lot','instrument','operator','date','result'],[dict(family=a['family'],hole=a['hole'],**{k:None for k in ['actual_diameter_mm','actual_x_mm','actual_y_mm','actual_z_mm','actual_counterbore_depth_mm','material_lot','instrument','operator','date','result']}) for a in hole_rows])
dump(O/'parts_index.json',bom);dump(O/'drawing_index.json',drawings)
for path in [O/'step/BM1_R3_fixture_assembly.step',*[O/'step/sections'/f'{q}.step' for q in sections]]:
    sh=cq.importers.importStep(str(path)).val();assert sh.isValid() and sh.Volume()>0;checks.append(dict(file=path.relative_to(R).as_posix(),valid=True,solids=len(sh.Solids())))
dump(R/'reports/r3_export_validation.json',dict(instances=len(rows),step_files=len(checks),step_reopened=checks,custom_drawing_pages=len(drawings),hole_table_rows=len(hole_rows),manufacturing_release=False))
print('R3 EXPORT',len(rows),'instances;',len(checks),'STEP files;',len(drawings),'drawing pages;',len(hole_rows),'hole rows')
