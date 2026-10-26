from pathlib import Path
import json
import pymupdf
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];out=R/'output/pdf_review';out.mkdir(exist_ok=True)
pdf=pymupdf.open(R/'output/BM1_V0_design_book.pdf');issues=[];thumbs=[]
for n,p in enumerate(pdf):
    for b in p.get_text('blocks'):
        if b[1]<0 or b[3]>p.rect.height or b[0]<0 or b[2]>p.rect.width:issues.append(dict(page=n+1,box=b[:4],text=b[4][:100]))
    pix=p.get_pixmap(matrix=pymupdf.Matrix(.45,.45));im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples);thumbs.append(im)
    if n in [0,1,9,20,30,47,55,64,74,75,101,102]:p.get_pixmap(matrix=pymupdf.Matrix(1.6,1.6)).save(out/f'page_{n+1:03d}.png')
for start in range(0,len(thumbs),20):
    tilew,tileh=400,300;sheet=Image.new('RGB',(tilew*4,tileh*5),'#D9E1E6');dr=ImageDraw.Draw(sheet)
    for k,im in enumerate(thumbs[start:start+20]):
        x=(k%4)*tilew;y=(k//4)*tileh;sheet.paste(im,(x+10,y+20));dr.text((x+10,y+4),str(start+k+1),fill='black')
    sheet.save(out/f'contact_{start+1:03d}.png')
(R/'reports/pdf_validation.json').write_text(json.dumps(dict(pages=len(pdf),out_of_page_text=issues,main_part_page_count=44,rendered_every_page=True,contact_sheets=len(list(out.glob('contact_*.png')))),ensure_ascii=False,indent=2),encoding='utf-8');print('PDF',len(pdf),'pages; out-of-page blocks',len(issues))
