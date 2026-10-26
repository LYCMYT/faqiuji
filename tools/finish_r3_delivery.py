"""Render-check PDF, validate exports, encode labelled demo, and build local entry."""
from pathlib import Path
import sys,json,math,subprocess,html,csv,shutil
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import cadquery as cq
import pymupdf as fitz
from PIL import Image,ImageDraw,ImageFont
O=R/'output/fixture_r3';P=json.loads((R/'data/r3_presentation.json').read_text(encoding='utf-8'));S=json.loads((R/'data/r3_fixture.json').read_text(encoding='utf-8'))
shutil.copyfile(R/'viewer/r3_template.html',O/'viewer.html')
parts=json.loads((O/'parts_index.json').read_text(encoding='utf-8'));drawings=json.loads((O/'drawing_index.json').read_text(encoding='utf-8'))
expected=json.loads((R/'reports/r3_pdf_expected.json').read_text(encoding='utf-8'))['planned_pages'];pdf=fitz.open(O/'BM1_R3_connection_drawing_book.pdf');assert len(pdf)==expected,('PDF spillover',len(pdf),expected)
review=R/'tmp/pdfs/r3_review';review.mkdir(parents=True,exist_ok=True);pages=[];overflow=[]
for n,p in enumerate(pdf):
    for block in p.get_text('blocks'):
        if block[0]<-1 or block[1]<-1 or block[2]>p.rect.width+1 or block[3]>p.rect.height+1:overflow.append([n+1,list(block[:4])])
    path=review/f'page_{n+1:02d}.png';p.get_pixmap(matrix=fitz.Matrix(1.2,1.2)).save(path);pages.append(path)
assert not overflow,overflow
for start in range(0,len(pages),12):
    contact=Image.new('RGB',(1200,math.ceil(len(pages[start:start+12])/3)*310),'white');d=ImageDraw.Draw(contact)
    for n,path in enumerate(pages[start:start+12]):
        im=Image.open(path);im.thumbnail((390,280));x=n%3*400;y=n//3*310;contact.paste(im,(x,y));d.text((x+8,y+282),str(start+n+1),fill='black')
    contact.save(review/f'contact_{start//12+1}.png')
# Reopen the complete current STEP set, and independently verify closed DXF profiles.
step=[]
for path in (O/'step').rglob('*.step'):
    sh=cq.importers.importStep(str(path)).val();assert sh.isValid() and sh.Volume()>0;step.append(path.relative_to(O).as_posix())
dxf=[]
for name in drawings:
    profile=cq.importers.importDXF(str(O/'dxf'/f'{name}.dxf')).wires().toPending().extrude(1).val();assert profile.isValid() and profile.Volume()>0
    source=cq.importers.importStep(str(O/'step/parts'/f'{name}.step')).val()
    area=sum(face.Area() for face in cq.Workplane('XY').add(source).faces('>Z').vals())
    assert abs(profile.Volume()-area)<.02,(name,profile.Volume(),area)
    dxf.append(dict(family=name,closed_profile=True,area_difference_mm2=abs(profile.Volume()-area)))
frames=sorted((O/'frames').glob('*.png'));assert len(frames)==len(range(1,P['duration_frames']+1,P['render_sample_step']))
w,h=P['resolution'];top_band,bottom_band=P['caption_bands_px'];video_h=h+top_band+bottom_band;font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
proc=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{video_h}','-r',str(P['fps']/P['render_sample_step']),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-r',str(P['fps']),'-movflags','+faststart',str(O/'BM1_R3_connections_explode.mp4')],stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
for path in frames:
    im=Image.new('RGB',(w,video_h),'#183a4d');im.paste(Image.open(path).convert('RGB'),(0,top_band));d=ImageDraw.Draw(im);d.text((18,13),'BM1 R3 / 台架与夹块连接件分解、复原',font=font,fill='white');d.text((18,video_h-62),'展示位移，不是实际拆卸轨迹。驱动适配、导向与紧固载荷仍待确认。',font=small,fill='white');d.text((18,video_h-32),'实际球样、采购、加工和样机试验尚未执行。',font=small,fill='#f3c67d');proc.stdin.write(im.tobytes())
    if path==frames[len(frames)//2]:im.save(O/'animation_preview.png')
proc.stdin.close();err=proc.stderr.read();assert proc.wait()==0,err.decode(errors='replace')
subprocess.run(['ffmpeg','-v','error','-i',str(O/'BM1_R3_connections_explode.mp4'),'-f','null','-'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
links=[('BM1_R3_connection_drawing_book.pdf','中文连接与加工图集'),('step/BM1_R3_fixture_assembly.step','R3低速台总装 STEP'),('BM1_R3_fixture.blend','BLEND 源场景'),('BM1_R3_fixture.glb','GLB 三维模型'),('BM1_R3_connections_explode.mp4','连接件分解动画'),('BOM.csv','BOM'),('hole_table.csv','53行孔位表'),('first_article_inspection_BLANK.csv','首件检查空表'),('viewer.html','交互三维查看器'),('../../reports/r3_acceptance_report.md','验收报告')]
body='<h1>BM1 R3 · 低速台架与夹块连接</h1><p>新连接结构已建模并数字检查；执行器适配、导向、实际轨道兼容、紧固载荷与台面锚固仍待确认。</p><ul>'+''.join(f'<li><a href="{u}">{html.escape(t)}</a></li>' for u,t in links)+'</ul><img src="R3_assembly.png"><img src="R3_exploded.png">'
for a in parts:
    if a['family'] in drawings:body+=f'<h2>{a["family"]}</h2><p><a href="{a["step"]}">STEP</a> · <a href="dxf/{a["family"]}.dxf">顶面DXF</a></p><img src="drawings/{a["family"]}.png">'
(O/'index.html').write_text('<!doctype html><html lang="zh"><meta charset="utf-8"><title>BM1 R3</title><style>body{max-width:1100px;margin:40px auto;font:16px/1.8 system-ui;color:#183a4d;background:#f4f7f9}img{width:100%}a{color:#087b80}</style>'+body+'</html>',encoding='utf-8')
bl=json.loads((R/'reports/r3_blender_validation.json').read_text(encoding='utf-8'));geo=json.loads((R/'reports/r3_geometry_validation.json').read_text(encoding='utf-8'));assert bl['meshes']==geo['instances'] and geo['status']=='PASS'
assert not S['manufacturing_release'] and not any(S[k] for k in ['physical_measurements','supplier_interfaces','prototype_results'])
report=dict(status='PASS',instances=geo['instances'],pdf_pages=len(pdf),pdf_text_overflow=[],step_reopened=len(step),dxf_profiles=dxf,video_fully_decoded=True,video_size=[w,video_h],blend_glb_reopened=True,physical_evidence_empty=True,manufacturing_release=False)
(R/'reports/r3_delivery_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('R3 FINAL PASS',len(pdf),'PDF pages;',len(step),'STEP;',len(dxf),'DXF; video fully decoded')
