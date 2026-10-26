"""Small orthographic raster/SVG renderer of native CAD tessellations."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

def render(shapes,path,title):
    z=np.array([1.3,-1.8,1.05]);z/=np.linalg.norm(z);x=np.cross([0,0,1],z);x/=np.linalg.norm(x);y=np.cross(z,x);B=np.array([x,y,z])
    bundles=[];verts=[]
    for n,(name,s) in enumerate(shapes):
        vv,tt=s.tessellate(.3,.2);v=np.array([p.toTuple() for p in vv]);pr=v@B.T;verts.append(pr);bundles.append((n,pr,np.array(tt)))
    allv=np.concatenate(verts);lo=allv[:,:2].min(0);hi=allv[:,:2].max(0);center=(lo+hi)/2;scale=min(1060/(hi[0]-lo[0]),700/(hi[1]-lo[1]))
    polys=[];palette=['#7DA99F','#E28362','#526677','#C49B51']
    for n,pr,t in bundles:
        triangles=pr[t];p=(triangles[:,:,:2]-center)*[scale,-scale]+[600,450]
        for depth,tri in zip(triangles[:,:,2].mean(1),p):polys.append((depth,tri,palette[n%4]))
    polys.sort(key=lambda x:x[0]);im=Image.new('RGB',(1200,900),'#f4f7f9');d=ImageDraw.Draw(im)
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="900"><rect width="1200" height="900" fill="#f4f7f9"/>']
    for _,p,c in polys:
        d.polygon([tuple(a) for a in p],fill=c);svg.append('<polygon points="'+' '.join(f'{a:.2f},{b:.2f}' for a,b in p)+f'" fill="{c}"/>')
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',25);d.text((30,25),title,fill='#183a4d',font=font);d.text((30,850),'原生CAD实体投影 / 低速试装候选 / 非制造批准',fill='#183a4d',font=font)
    svg.append('</svg>');im.save(Path(path).with_suffix('.png'));Path(path).with_suffix('.svg').write_text(''.join(svg),encoding='utf-8')
