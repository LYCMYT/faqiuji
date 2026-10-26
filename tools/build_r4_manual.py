"""Current-run Chinese R4 review book; render/text checks are not human signoff."""
from pathlib import Path
import json
import os
import sys
from html import escape
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from tools.build_context import active_context, atomic_json, file_hash
from tools.validate_release import require_report
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
import pymupdf
from PIL import Image as PILImage, ImageDraw


def main():
    ctx=active_context(R,'r4_documents');O=R/'output/fixture_r4';O.mkdir(parents=True,exist_ok=True)
    atomic_json(R/'reports/r4_document_validation.json',ctx.report('RUNNING'))
    def read(name):return json.loads((R/name).read_text(encoding='utf-8'))
    geo=read('reports/r4_geometry_validation.json');exports=read('reports/r4_export_validation.json')
    require_report(exports,ctx.for_stage('r4_exports'),['expected_step_set','step_roundtrip'],R)
    # Readiness remains separate from document creation; a book can describe OPEN mechanisms.
    for key in ('run_id','input_sha256','code_sha256'):
        if geo.get(key)!=getattr(ctx,key):raise RuntimeError('Stale geometry evidence '+key)
    font=Path(os.environ.get('BM1_CHINESE_FONT','C:/Windows/Fonts/msyh.ttc'))
    if not font.is_file():raise RuntimeError('Chinese font unavailable')
    pdfmetrics.registerFont(TTFont('BM1CN',str(font),subfontIndex=0))
    normal=ParagraphStyle('normal',fontName='BM1CN',fontSize=10.2,leading=16,spaceAfter=8,wordWrap='CJK',textColor=colors.HexColor('#243e4b'))
    heading=ParagraphStyle('heading',parent=normal,fontSize=18,leading=26,spaceAfter=14,textColor=colors.HexColor('#087b80'))
    small=ParagraphStyle('small',parent=normal,fontSize=8.5,leading=13)
    story=[]
    def para(text,style=normal):return Paragraph(escape(str(text)).replace('\n','<br/>'),style)
    def title(text):story.append(para(text,heading))
    def image(path):
        path=Path(path)
        if not path.is_file():raise RuntimeError('Missing book figure: '+str(path))
        with PILImage.open(path) as im:w,h=im.size
        scale=min(500/w,390/h);story.append(Image(str(path),width=w*scale,height=h*scale));story.append(Spacer(1,8))
    def table(rows,widths=(120,380)):
        grid=[[para(c,small) for c in row] for row in rows]
        t=Table(grid,colWidths=list(widths),hAlign='LEFT')
        t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#c6d1d7')),('BACKGROUND',(0,0),(0,-1),colors.HexColor('#e9f0f2')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.append(t)
    title('BM1 R4 · 工程评审候选包')
    story.append(para('沿用 R1–R3 参数化工程、44 主项和 ASM/PRT 编号。此册区分实际数字检查、尚未运行的检查、采购接口与实物试验；整机制造放行始终为 false。'))
    image(O/'R4_assembly.png')
    table([['本次构建',ctx.run_id],['几何报告',geo.get('status','NOT_RUN')],['参考坐标','右手坐标，mm/deg；台架局部 height=0，不是整机出球高度。'],['交付性质','低速人工验证候选；没有采购、真实球测量、夹力/轮速验证或安全等级结论。']])
    story.append(PageBreak());title('总装分解与来源')
    image(O/'R4_exploded.png')
    table([['Git 基准',ctx.commit_sha],['权威输入 SHA-256',ctx.input_sha256],['源码 SHA-256',ctx.code_sha256],['审查基准','c8c52514a80f52c364950852ed2fde2a1d926e62'],['数字范围','源文件/工具指纹、原生实体、声明的离散状态、STEP 回读、BLEND/GLB 回读、PDF 渲染和浏览器交互分别记录；不是连续运动或实物验收。']])
    story.append(PageBreak());title('接球承托与数字检查')
    for key in ('reference_geometry','support_projection','free_motion_probe','clearances','assumptions'):
        if key in geo:
            story.append(para(key,heading));story.append(para(json.dumps(geo[key],ensure_ascii=False,indent=2),small))
    story.append(para('实际球头可能偏心、变形或回弹；名义支撑不代替真实球样的接球姿态和损伤试验。'))
    interfaces=read('data/r4_mechanical_interfaces.json')
    for axis in interfaces['axes']:
        story.append(PageBreak());title('五功能约束 · '+axis['axis_id'])
        table([[key,json.dumps(value,ensure_ascii=False) if isinstance(value,(dict,list)) else str(value)] for key,value in axis.items()])
    index=read('output/fixture_r4/parts_index.json')
    # Newly revised R4 parts get individual pages; legacy part drawings remain in preserved R1–R3 books.
    selected=[p for p in index if 'R4' in p.get('family',p.get('part_id',''))]
    import cadquery as cq
    from tools.render_cad_preview import render
    for item in selected:
        family=item.get('family',item.get('part_id'));story.append(PageBreak());title('独立部件 · '+family)
        shape=cq.importers.importStep(str(O/item['step'])).val()
        target=O/'drawings'/family;target.parent.mkdir(exist_ok=True)
        render([(family,shape)],target,'BM1 R4 / '+family)
        image(target.with_suffix('.png'))
        table([['料号/版次',family],['STEP',item['step']],['材料与工艺',item.get('material','候选；按首件图与供应方确认')],['基准/孔位',json.dumps(item.get('holes',[]),ensure_ascii=False)],['状态','项目自定义候选几何；真实材料/配合/预紧和承载待首件及实测。'],['检查',f'原生导出后回读；体积 {shape.Volume():.3f} mm³，仅几何量，不是实际质量。']])
    story.append(PageBreak());title('44 主项功能与工艺核对')
    roles=read('data/part_roles.json')
    entries=roles if isinstance(roles,list) else roles.get('parts',roles.get('roles',[]))
    if isinstance(entries,dict):entries=[dict(part_id=key,**value) for key,value in entries.items()]
    for row in entries:
        story.append(para(f"{row.get('part_id','')} · {row.get('source_name',row.get('name',''))}",small))
        story.append(para(row.get('reviewed_route',row.get('route',row.get('role',''))),small))
    for filename,label in [('docs/test_protocol_r4.md','首件与实测协议'),('docs/engineering_evidence_r4.md','质量/支承证据录入'),('docs/control_contract_r4.md','离线控制合同')]:
        story.append(PageBreak());title(label)
        for text in (R/filename).read_text(encoding='utf-8').split('\n\n'):
            if text.strip():story.append(para(text,small))
    story.append(PageBreak());title('具体剩余输入与放行边界')
    scope=read('data/r4_release_scope.json')
    table([[item['id']+' / '+item['status'],item['required']] for item in scope['open_inputs']])
    story.append(para('自动生成的图页、联系表或渲染不能自动成为人工审核。人工签核必须记录审核人、时间和当前产物散列；没有签核时状态为 NOT_RUN。'))
    output=O/'BM1_R4_review_book.pdf'
    def footer(c,doc):
        c.setFont('BM1CN',8);c.setFillColor(colors.HexColor('#526677'));c.drawString(42,25,'BM1 R4 · 数字候选 / 制造未放行');c.drawRightString(553,25,str(doc.page))
    SimpleDocTemplate(str(output),pagesize=(595,842),leftMargin=44,rightMargin=44,topMargin=42,bottomMargin=42).build(story,onFirstPage=footer,onLaterPages=footer)
    doc=pymupdf.open(output);review=R/'tmp/pdfs/r4_review';review.mkdir(parents=True,exist_ok=True);overflow=[];pages=[]
    for n,page in enumerate(doc):
        for block in page.get_text('blocks'):
            if block[0]<-1 or block[1]<-1 or block[2]>page.rect.width+1 or block[3]>page.rect.height+1:overflow.append([n+1,list(block[:4])])
        path=review/f'page_{n+1:03d}.png';page.get_pixmap(matrix=pymupdf.Matrix(1.1,1.1)).save(path);pages.append(path)
    for start in range(0,len(pages),12):
        contact=PILImage.new('RGB',(1200,1240),'white');draw=ImageDraw.Draw(contact)
        for n,path in enumerate(pages[start:start+12]):
            with PILImage.open(path) as im:im.thumbnail((390,280));contact.paste(im,(n%3*400,n//3*310))
            draw.text((n%3*400+8,n//3*310+282),str(start+n+1),fill='black')
        contact.save(review/f'contact_{start//12+1:02d}.png')
    if overflow:raise RuntimeError('PDF text outside page: '+str(overflow))
    atomic_json(R/'reports/r4_document_validation.json',ctx.report('PASS',['pdf_rendered','pdf_text_bounds'],{output.relative_to(R).as_posix():file_hash(output)},pages=len(doc),individual_r4_pages=len(selected),text_overflow=[],manual_signoff='NOT_RUN'))
    print('R4 PDF:',len(doc),'pages;',len(selected),'R4 part pages; automatic render/text check PASS')

if __name__=='__main__':main()
