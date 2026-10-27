"""Additional nominal jaw review sheets, derived only from frozen STEP/index/data."""
import json
from pathlib import Path
import cadquery as cq
from PIL import Image,ImageDraw,ImageFont

def generate(root,out,families):
    index={row['family']:row for row in json.loads((root/'output/fixture_r4/parts_index.json').read_text(encoding='utf-8'))}
    jaw=json.loads((root/'data/r3_fixture.json').read_text(encoding='utf-8'))['jaw']
    folder=out/'candidate_drawings';folder.mkdir();records=[]
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',23);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
    for family in sorted(families):
        entry=index[family];shape=cq.importers.importStep(str(root/'output/fixture_r4'/entry['step'])).val()
        if not shape.isValid() or len(shape.Solids())!=1:raise RuntimeError('Invalid source STEP '+family)
        bb=shape.BoundingBox();dims=[bb.xlen,bb.ylen,bb.zlen];mins=[bb.xmin,bb.ymin,bb.zmin]
        im=Image.new('RGB',(1500,1100),'#f4f7f9');d=ImageDraw.Draw(im)
        d.text((28,20),family+' / 候选夹块评审图 / mm',font=font,fill='#183a4d')
        for axes,origin,label in [((0,1),(370,255),'俯视 XY'),((0,2),(370,670),'正视 XZ'),((1,2),(1100,670),'侧视 YZ')]:
            scale=min(620/max(dims[axes[0]],1),270/max(dims[axes[1]],1))
            for edge in shape.Edges():
                points,_=edge.sample(65 if edge.geomType()!='LINE' else 2)
                line=[(origin[0]+(v.toTuple()[axes[0]]-mins[axes[0]]-dims[axes[0]]/2)*scale,origin[1]-(v.toTuple()[axes[1]]-mins[axes[1]]-dims[axes[1]]/2)*scale) for v in points]
                d.line(line,fill='#183a4d',width=2)
            d.text((origin[0]-70,origin[1]-170),label,font=font,fill='#087b80')
            d.text((origin[0]-130,origin[1]+155),f'{dims[axes[0]]:.3f} x {dims[axes[1]]:.3f} mm',font=small,fill='#183a4d')
        local=[{**hole,**{key:hole[key]-entry['local_origin_H_mm'][axis] for axis,key in enumerate(('x','y','z')) if key in hole}} for hole in entry['holes']]
        notes=['源：冻结 R4 导出中的 R3 夹块，非新选型。','候选 A=Z底面 / B=Y最小侧 / C=X最小侧','局部STEP基准，不是总装H基准。','接触轮廓按本件原生STEP；半径方案待筛选。','M4为间隙通孔+顶面沉孔，不是螺纹孔。','配合/轮廓/形位/表面状态及材料批次 OPEN。']
        for hole in local:
            notes.append(f"孔局部XY {hole['x']:.3f}, {hole['y']:.3f}; D{hole['diameter']}")
            if 'counterbore_diameter' in hole:notes.append(f"顶面沉孔D{hole['counterbore_diameter']} 深{hole['counterbore_depth']}")
        for n,line in enumerate(notes):d.text((790,90+n*31),line,font=small,fill='#183a4d')
        for n,line in enumerate(['名义几何的全部边投影，未区分隐藏线，不按图片比例量图加工。','左右件分别引用各自STEP，公差/材质/采购组合需逐件审核。','候选评审图，首件及制造放行 false；不能替代批准加工图。']):d.text((28,930+38*n),line,font=font,fill='#a4492b')
        im.save(folder/(family+'_review.png'))
        records.append(dict(family=family,revision='R3',derived_status='CANDIDATE_REVIEW_NOT_RELEASED',source_step=entry['step'],dimensions_mm=dims,local_STEP_min_mm=mins,local_origin_H_mm=entry['local_origin_H_mm'],holes_local_mm=local,jaw_source=jaw,critical_fit_tolerance=None,manufacturing_release=False,first_article_release=False))
    (out/'additional_jaw_features.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    return families
