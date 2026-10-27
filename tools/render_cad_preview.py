"""Depth-tested orthographic CAD raster, also saved in an SVG image wrapper."""
from pathlib import Path
import os
import base64
import numpy as np
from PIL import Image,ImageDraw,ImageFont

def render(shapes,path,title):
    z=np.array([1.3,-1.8,1.05]);z/=np.linalg.norm(z);x=np.cross([0,0,1],z);x/=np.linalg.norm(x);y=np.cross(z,x);B=np.array([x,y,z])
    bundles=[];verts=[]
    for n,(name,s) in enumerate(shapes):
        vv,tt=s.tessellate(.3,.2);v=np.array([p.toTuple() for p in vv]);pr=v@B.T;verts.append(pr);bundles.append((n,pr,np.array(tt)))
    allv=np.concatenate(verts);lo=allv[:,:2].min(0);hi=allv[:,:2].max(0);center=(lo+hi)/2;scale=min(1060/(hi[0]-lo[0]),700/(hi[1]-lo[1]))
    palette=['#7DA99F','#E28362','#526677','#C49B51']
    pixels=np.full((900,1200,3),(244,247,249),dtype=np.uint8);depth_buffer=np.full((900,1200),-np.inf)
    light=np.array([-.35,.55,.8]);light/=np.linalg.norm(light)
    for n,pr,t in bundles:
        triangles=pr[t];p=(triangles[:,:,:2]-center)*[scale,-scale]+[600,450]
        normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
        normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-12)
        shades=.48+.52*np.abs(normals@light)
        base=np.array([int(palette[n%4][j:j+2],16) for j in (1,3,5)])
        # Per-pixel depth prevents long faces from painting over nearer bore walls.
        for triangle,screen,shade in zip(triangles,p,shades):
            color=np.clip(base*shade,0,255).astype(np.uint8)
            x0=max(0,int(np.floor(screen[:,0].min())));x1=min(1199,int(np.ceil(screen[:,0].max())))
            y0=max(0,int(np.floor(screen[:,1].min())));y1=min(899,int(np.ceil(screen[:,1].max())))
            if x1<x0 or y1<y0:continue
            a,b,c=screen;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-12:continue
            xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
            u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
            v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;w=1-u-v
            depth=u*triangle[0,2]+v*triangle[1,2]+w*triangle[2,2]
            current=depth_buffer[y0:y1+1,x0:x1+1];mask=(u>=-1e-9)&(v>=-1e-9)&(w>=-1e-9)&(depth>current)
            current[mask]=depth[mask];pixels[y0:y1+1,x0:x1+1][mask]=color
    im=Image.fromarray(pixels);d=ImageDraw.Draw(im)
    font=ImageFont.truetype(os.environ.get('BM1_CHINESE_FONT','C:/Windows/Fonts/msyh.ttc'),25);d.text((30,25),title,fill='#183a4d',font=font);d.text((30,850),'原生CAD实体投影 / 低速试装候选 / 非制造批准',fill='#183a4d',font=font)
    png=Path(path).with_suffix('.png');im.save(png)
    encoded=base64.b64encode(png.read_bytes()).decode('ascii')
    Path(path).with_suffix('.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="900"><image width="1200" height="900" href="data:image/png;base64,'+encoded+'"/></svg>',encoding='utf-8')
