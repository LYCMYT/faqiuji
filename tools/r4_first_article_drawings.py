"""Review drawings from current native STEP; never manufacturing approval."""
import csv,json,os
from pathlib import Path
import cadquery as cq
from PIL import Image,ImageDraw,ImageFont

def generate(root,out,index):
    spec=json.loads((root/'data/r4_first_article.json').read_text(encoding='utf-8'))
    old=json.loads((root/'data/r3_fixture.json').read_text(encoding='utf-8'))
    new=json.loads((root/'data/r4_fixture.json').read_text(encoding='utf-8'))
    fontpath=os.environ.get('BM1_CHINESE_FONT','C:/Windows/Fonts/msyh.ttc')
    font=ImageFont.truetype(fontpath,22);small=ImageFont.truetype(fontpath,18)
    catalog={x['family']:x for x in index};outputs=[];records=[]
    for item in spec['items']:
        entry=catalog[item['family']];shape=cq.importers.importStep(str(out/entry['step'])).val()
        bb=shape.BoundingBox();lengths=[bb.xlen,bb.ylen,bb.zlen]
        im=Image.new('RGB',(1500,1100),'#f4f7f9');d=ImageDraw.Draw(im)
        d.text((28,20),item['family']+' / 首件询价评审图 / mm',font=font,fill='#183a4d')
        for axes,origin,label in [((0,1),(370,255),'俯视 XY'),((0,2),(370,670),'正视 XZ'),((1,2),(1100,670),'侧视 YZ')]:
            scale=min(620/max(lengths[axes[0]],1),270/max(lengths[axes[1]],1))
            for edge in shape.Edges():
                points,_=edge.sample(65 if edge.geomType()!='LINE' else 2)
                line=[(origin[0]+(v.toTuple()[axes[0]]-lengths[axes[0]]/2)*scale,origin[1]-(v.toTuple()[axes[1]]-lengths[axes[1]]/2)*scale) for v in points]
                d.line(line,fill='#183a4d',width=2)
            d.text((origin[0]-70,origin[1]-170),label,font=font,fill='#087b80')
            d.text((origin[0]-125,origin[1]+155),f'{lengths[axes[0]]:.3f} x {lengths[axes[1]]:.3f} mm',font=small,fill='#183a4d')
        tolerance=old['inspection']
        lines=['A: 底面 Z / B: Y最小侧 / C: X最小侧',f'外包络: {lengths[0]:.3f} x {lengths[1]:.3f} x {lengths[2]:.3f}',f'线性询价目标: ±{tolerance["linear_general_tolerance_mm"]} mm',f'孔坐标询价目标: ±{tolerance["hole_position_coordinate_tolerance_mm"]} mm','实际基准面、形位、配合公差: OPEN','上述为项目询价要求，未经加工方确认。','STEP坐标原点为外包络最小角；非装配H原点。','孔位/方向/深度见 first_article_features.json。']
        for n,line in enumerate(lines):d.text((790,100+33*n),line,font=small,fill='#183a4d')
        for n,line in enumerate(['原生实体线框投影，不按图片比例量图加工。','图号版次按family；材料批号、关键配合、预紧及加工方审核未完成。','整机及首件制造放行 false；不得将模型孔径当作螺纹底孔。']):d.text((28,930+38*n),line,font=font,fill='#a4492b')
        path=out/'drawings'/(item['family']+'_first_article.png');im.save(path);outputs.append(path)
        record={**item,'coordinate_datum':spec['coordinate_datum'],'STEP':entry['step'],'local_origin_H_mm':entry['local_origin_H_mm'],'dimensions_mm':lengths,'holes':entry['holes'],'linear_RFQ_tolerance_mm':tolerance['linear_general_tolerance_mm'],'hole_coordinate_RFQ_tolerance_mm':tolerance['hole_position_coordinate_tolerance_mm'],'tolerance_status':spec['tolerance_status'],'manufacturing_release':False}
        if item['family']=='PRT-0701-R4-A':record['land_H']=new['seat']
        record['holes_coordinate_system']='Inherited H/world coordinates; convert to local STEP by subtracting local_origin_H_mm'
        record['holes_local_mm']=[{**hole,**{key:hole[key]-entry['local_origin_H_mm'][axis] for axis,key in enumerate(('x','y','z')) if key in hole}} for hole in entry['holes']]
        if item['family']=='PRT-0603-R3-R29-L':record['jaw_source']=old['jaw']
        if item['family']=='PRT-0602-R3-BASE':record['through_depth_mm']=lengths[2]
        records.append(record)
    path=out/'first_article_features.json';path.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8');outputs.append(path)
    path=out/'first_article_inspection_BLANK.csv'
    with path.open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['family','revision','feature','nominal_source','actual_value','unit','material_lot','instrument','operator','date','raw_evidence','result'])
        for item in records:
            for feature in item['features']:writer.writerow([item['family'],item['family'],feature,'first_article_features.json','','mm','','','','','','OPEN'])
    outputs.append(path)
    return records,outputs
