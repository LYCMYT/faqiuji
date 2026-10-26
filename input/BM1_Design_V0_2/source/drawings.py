"""Deterministic vector illustrations for the concept brief. This is not a CAD kernel."""
from math import sin, cos, pi, sqrt
import html
from pathlib import Path
from design_data import PARTS, PARAMS, ASM

INK='#243847'; LIGHT='#DDE7EB'; METAL='#A8BAC2'; DARK='#405360'
def add(a,b): return tuple(x+y for x,y in zip(a,b))
def mul(a,s): return tuple(x*s for x in a)
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(a):
    l=sqrt(dot(a,a)) or 1
    return mul(a,1/l)
def rgb(h): return tuple(int(h.lstrip('#')[i:i+2],16)/255 for i in (0,2,4))
def hexcol(c): return '#'+''.join(f'{max(0,min(255,round(v*255))):02x}' for v in c)
def shade(col,k): return hexcol(tuple(min(1,c*k+(1-k)*.08) for c in rgb(col)))

class Mesh:
    def __init__(self,faces,color=METAL,pid='',alpha=1):
        self.faces=faces; self.color=color; self.pid=pid; self.alpha=alpha
    def transformed(self,origin=(0,0,0),ry=0,rz=0):
        a,b=ry*pi/180,rz*pi/180
        def tr(p):
            x,y,z=p
            x,z=x*cos(a)+z*sin(a),-x*sin(a)+z*cos(a)
            return (x*cos(b)-y*sin(b)+origin[0],x*sin(b)+y*cos(b)+origin[1],z+origin[2])
        return Mesh([[tr(p) for p in f] for f in self.faces],self.color,self.pid,self.alpha)

def box(s,center=(0,0,0),color=METAL,pid=''):
    x,y,z=[v/2 for v in s]
    vs=[(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
    f=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    return Mesh([[add(vs[i],center) for i in ff] for ff in f],color,pid)

def cylinder(r,h,center=(0,0,0),color=METAL,pid='',axis='z',r2=None,n=24):
    r2=r if r2 is None else r2
    rings=[[(rr*cos(2*pi*i/n),rr*sin(2*pi*i/n),zz) for i in range(n)] for rr,zz in [(r,-h/2),(r2,h/2)]]
    fs=[list(reversed(rings[0])),rings[1]]
    fs += [[rings[0][i],rings[0][(i+1)%n],rings[1][(i+1)%n],rings[1][i]] for i in range(n)]
    def orient(p):
        x,y,z=p
        return add((x,z,-y) if axis=='y' else (z,y,-x) if axis=='x' else p,center)
    return Mesh([[orient(p) for p in f] for f in fs],color,pid)

def tube(ro,ri,h,center=(0,0,0),color=METAL,pid='',n=32):
    rings=[[ (r*cos(2*pi*i/n),r*sin(2*pi*i/n),z) for i in range(n)] for r,z in [(ro,-h/2),(ro,h/2),(ri,-h/2),(ri,h/2)]]
    fs=[]
    for i in range(n):
        j=(i+1)%n
        fs.extend([[rings[0][i],rings[0][j],rings[1][j],rings[1][i]],
                   [rings[2][j],rings[2][i],rings[3][i],rings[3][j]],
                   [rings[1][i],rings[1][j],rings[3][j],rings[3][i]],
                   [rings[0][j],rings[0][i],rings[2][i],rings[2][j]]])
    return Mesh([[add(p,center) for p in f] for f in fs],color,pid)

def square_tube(x,y,z,t=4,color=METAL,pid=''):
    return [box((x,t,z),(0,-(y-t)/2,0),color,pid),box((x,t,z),(0,(y-t)/2,0),color,pid),
            box((t,y-2*t,z),(-(x-t)/2,0,0),color,pid),box((t,y-2*t,z),((x-t)/2,0,0),color,pid)]

def capsule(s,color=METAL,pid=''):
    x,y,z=s
    return [box((x*.75,y,z),color=color,pid=pid),cylinder(y/2,z,(-x*.375,0,0),color,pid),cylinder(y/2,z,(x*.375,0,0),color,pid)]

def part_mesh(p):
    x,y,z=p['bbox_mm']; k=p['shape']; c=p['color']; pid=p['part_id']; m=[]
    B=lambda s,at=(0,0,0),co=c: box(s,at,co,pid)
    C=lambda r,h,at=(0,0,0),co=c,axis='z': cylinder(r,h,at,co,pid,axis)
    if k=='frame':
        for yy in [-y/2+20,y/2-20]:m.append(B((x,40,40),(0,yy,-z/2+20)))
        for xx in [-x/2+20,x/2-20]:m.append(B((40,y-80,40),(xx,0,-z/2+20)))
        m.extend([B((40,y-80,40),(xx,0,-z/2+20)) for xx in [-100,100]])
        m.append(B((x*.8,y*.8,6),(0,0,z/2-3),LIGHT))
    elif k in ('plate_holes','slotted_plate','head_plate','gate','window'):
        m=[B((x,y,z),co=LIGHT if k=='window' else c)]
        if k!='window':
            for xx in [-x*.37,x*.37]:
                for yy in [-y*.32,y*.32]:
                    m.append(C(min(x,y)*.035,.5,(xx,yy,z/2+.3),DARK))
            if k=='slotted_plate':
                for xx in [-x*.3,x*.3]:m.append(B((6,y*.6,.5),(xx,0,z/2+.5),DARK))
            if k=='gate':m.append(C(min(x,y)*.28,.5,(0,0,z/2+.6),LIGHT))
    elif k in ('beam',):m=[a.transformed(ry=90) for a in square_tube(z,y,x,min(y,z)*.15,c,pid)]
    elif k=='square_tube':m=square_tube(x,y,z,4,c,pid)
    elif k=='square_collar':
        m=square_tube(x,y,z,(x-84)/2,c,pid)
        m.append(C(8,45,(x/2+18,0,0),DARK,axis='x'))
    elif k=='foot':m=[C(x/2,z*.18,(0,0,-z*.41),DARK),C(x*.12,z*.75,(0,0,z*.08),METAL),C(x*.2,8,(0,0,z*.27),c)]
    elif k=='pin':m=[C(x/2,z*.85,(0,0,-z*.07),METAL),C(x,8,(0,0,z*.42),c)]
    elif k=='shaft_y':m=[C(x/2,y,co=METAL,axis='y'),C(x*.9,8,(0,0,0),c,axis='y')]
    elif k=='caster':
        m=[C(x*.44,y*.8,(0,0,-z*.08),DARK,axis='y'),C(x*.22,y*.85,(0,0,-z*.08),METAL,axis='y'),B((x*.65,y,6),(0,0,z*.47)),B((8,8,z*.45),(0,y*.35,z*.2)),B((8,8,z*.45),(0,-y*.35,z*.2))]
    elif k in ('ring','tire','tube','guide_tube'):
        if k=='ring':ri=x*.27
        elif k=='tire':ri=50
        elif k=='tube':ri=38
        else:ri=41
        m=[tube(x/2,ri,z,color=DARK if k=='tire' else c,pid=pid)]
    elif k=='wheel_hub':
        m=[tube(x/2,9,z,color=c,pid=pid),tube(20,9,z*1.5,color=METAL,pid=pid)]
        for a in [0,pi/2,pi,3*pi/2]:m.append(C(3,.5,(x*.32*cos(a),x*.32*sin(a),z/2+.5),DARK))
    elif k=='bearing_unit':m=[B((x,y,10),(0,0,-22.5)),C(19,20,(0,0,-7.5),METAL),C(8,35,(0,0,10),DARK)]
    elif k=='motor':
        m=[C(x/2,z*.88,(0,0,-z*.06)),C(x*.47,z*.1,(0,0,z*.43),DARK),C(x*.09,z*.25,(0,0,z*.6),METAL)]
        for a in range(8):m.append(B((2,5,z*.65),(x*.48*cos(a*pi/4),x*.48*sin(a*pi/4),-z*.06),DARK))
    elif k=='gear_motor':m=[B((x*.6,y,z*.7),(-x*.2,0,-z*.1)),C(y*.42,x*.4,(x*.3,0,0),DARK,axis='x'),C(y*.1,x*.2,(x*.55,0,0),METAL,axis='x')]
    elif k=='yoke':
        m=[B((x,y,12),(0,0,-z/2+6)),B((x*.42,20,z),(0,-y/2+10,0)),B((x*.42,20,z),(0,y/2-10,0))]
        for yy in [-y/2,y/2]:m.append(C(16,3,(0,yy,z/2-10),DARK,axis='y'))
    elif k=='head_frame':
        # Center is (-42.5,0,-87.5) in H; stepped narrow tail is intentional.
        m=[B((240,340,12),(72.5,0,-87.5)),B((145,90,12),(-120,0,37.5))]
        for yy in [-37,37]:m.append(B((12,10,125),(-47.5,yy,-25)))
        for yy in [-200,200]:
            m.append(B((100,12,175),(42.5,yy,0)))
            m.append(B((100,40,12),(42.5,yy-(-15 if yy<0 else 15),-81.5)))
    elif k=='tube_bracket':
        m=[B((30,30,z),(-x*.4,0,0)),B((x,30,20),(0,0,z*.3)),B((x*.8,y,z*.12),(x*.1,0,z*.08))]
        m.append(tube(43,40,20,(x*.4,0,z*.3),LIGHT,pid))
    elif k=='jaw':m=[B((x*.7,y,z),(-x*.15,0,0)),B((x*.3,y*1.5,z),(x*.35,0,0),LIGHT)]
    elif k=='servo':m=[B((x,y,z*.8),(0,0,-z*.1)),B((x*1.2,y*.6,z*.12),(0,0,-z*.15),LIGHT),C(y*.25,z*.25,(x*.2,0,z*.42),METAL),B((x*.8,y*.25,3),(x*.2,0,z*.55),DARK)]
    elif k in ('linear_actuator','rail'):
        if k=='rail':
            m=[B((x,y*.7,z*.4),(0,0,-z*.3),DARK),B((x*.96,y*.25,z*.6),(0,0,0),METAL),B((x*.18,y,z*.6),(-x*.12,0,z*.2)),C(6,x*.85,co=LIGHT,axis='x')]
        else:m=[B((x*.6,y*.7,z),co=DARK),B((x,y,z*.18),(0,0,z*.22)),C(x*.12,z*.9,co=METAL)]
    elif k=='cradle':
        m=[B((x,y,5),(0,0,-7.5)),B((18,y,12),(-21,0,0)),B((45,10,7),(7.2,0,4)),C(7,6,(21,0,5),LIGHT),B((10,12,18),(-2,0,19),LIGHT)]
    elif k=='guard':
        # Front cover is wide; tail cover is narrow and elevated.
        for yy in [-142.5,142.5]:
            m.extend([B((240,85,4),(72.5,yy,133)),B((240,4,270),(72.5,(-183 if yy<0 else 183),0))])
        for yy in [-53,53]:m.append(B((145,4,100),(-120,yy,35)))
        m.append(B((4,110,100),(-190,0,35)))
    elif k=='electronics_case':
        m=[B((x,y,4),(0,0,-z/2)),B((x,y,4),(0,0,z/2)),B((x,4,z),(0,-y/2,0)),B((x,4,z),(0,y/2,0)),B((4,y,z),(x/2,0,0))]
        for yy in [-y*.3,0,y*.3]:m.append(B((x*.5,5,2),(0,yy,z/2+2),DARK))
    elif k=='pcb':
        m=[B((x,y,2),(0,0,-z*.35),c),B((x*.28,y*.4,z*.6),(0,0,0),DARK)]
        for yy in [-y*.4,y*.4]:m.append(B((x*.85,8,z*.55),(0,yy,-z*.05),LIGHT))
        for xx in [-x*.4,x*.4]:
            for yy in [-y*.35,y*.35]:m.append(C(2,z*.3,(xx,yy,-z*.3),METAL))
    elif k in ('power_supply','control_box'):
        m=[B((x,y,z))]
        for i in range(7):m.append(B((x*.7,3,.6),(0,-y*.3+i*y*.1,z/2+.5),DARK))
        m.append(B((15,y*.8,z*.4),(-x/2,0,-z*.1),LIGHT))
    elif k=='estop':m=[C(x*.18,z*.65,(0,0,-z*.1),DARK),C(x*.5,z*.24,(0,0,z*.35),'#C7493A'),C(x*.4,z*.1,(0,0,z*.18),'#F3C746')]
    elif k=='sensor':m=[B((x,y,z)),C(y*.3,2,(x/2+1,0,0),'#B9E5DF',axis='x')]
    elif k=='phone':m=[B((x,y,z),co=DARK),B((x*.91,y*.88,1),(0,0,z/2+.5),'#C4E2DB')]
    elif k=='remote':m=[B((x,y,z),co=DARK),C(y*.2,z*.18,(x*.2,0,z*.56),'#C7493A'),C(y*.12,z*.1,(-x*.25,0,z*.52),'#7BC4AD')]
    elif k=='phone_mount':m=[B((x*.8,y*.8,6),(0,0,0)),B((10,y*.85,z),(-x*.45,0,z*.18)),B((10,y*.85,z),(x*.45,0,z*.18)),B((x*.25,y*.25,z*.4),(0,0,-z*.25),DARK)]
    else:m=[B((x,y,z))]
    return m

def shuttle(center=(0,0,0),color='#F5F1DE',pid='TEST-SHUTTLE'):
    m=[cylinder(13.25,26,(0,0,0),color,pid),cylinder(13,70,(0,0,48),'#DDE7E1',pid,r2=34,n=16)]
    return [a.transformed(center) for a in m]

def world_scene(show_guards=True,head_pitch=0,head_yaw=0,height=1500,carriage=-85,guide_up=True):
    m=[]
    pp={p['part_id']:p for p in PARTS}
    def inst(pid,at,ry=0,rz=0):
        ms=part_mesh(pp[pid]); m.extend(a.transformed(at,ry,rz) for a in ms)
    inst('PRT-0101',(0,0,120)); inst('PRT-0102',(0,0,100))
    # Slant the four support beams to meet a wide stance.
    for sx in [-1,1]:
        for sy in [-1,1]:
            ang=42*sy*sx
            inst('PRT-0103',(sx*340,sy*305,75),rz=ang)
            inst('PRT-0104',(sx*425,sy*400,45))
    for sy in [-1,1]:inst('PRT-0105',(-270,sy*245,55))
    inst('PRT-0201',(0,0,600))
    inst('PRT-0202',(0,0,height-667))
    inst('PRT-0204',(0,0,1015));inst('PRT-0204',(0,0,800))
    inst('PRT-0301',(0,0,height-336))
    inst('PRT-0302',(0,0,height-315))
    inst('PRT-0303',(-75,-45,height-350))
    # The yoke is a yaw child but is not a pitch child.
    m.extend(a.transformed((0,0,height-145),rz=head_yaw) for a in part_mesh(pp['PRT-0401']))
    h=[]
    def hi(pid,at,ry=0,rz=0):h.extend(a.transformed(at,ry,rz) for a in part_mesh(pp[pid]))
    hi('PRT-0501',(-42.5,0,-87.5))
    for sy in [-1,1]:
        hi('PRT-0402',(0,sy*210,0))
        hi('PRT-0502',(0,sy*82.5,-165))
        hi('PRT-0503',(0,sy*82.5,-27.5))
        hi('PRT-0504',(0,sy*82.5,0))
        hi('PRT-0505',(0,sy*82.5,0))
        hi('PRT-0506',(0,sy*82.5,-105))
    hi('PRT-0703',(-115,0,-30))
    hi('PRT-0701',(carriage-16,0,-22))
    hi('PRT-0702',(carriage,14,-16));hi('PRT-0702',(carriage,-14,-16))
    hi('PRT-0704',(carriage-35,0,-55))
    h.extend(shuttle((carriage,0,0)))
    if show_guards:
        hi('PRT-0801',(-42.5,0,-35));hi('PRT-0802',(-35,-188,-60),ry=90)
    m.extend(a.transformed((0,0,height),ry=-head_pitch,rz=head_yaw) for a in h)
    # Pitch drive body attaches to the yaw yoke, not to a spinning shaft.
    m.extend(a.transformed((0,-270,height),rz=head_yaw) for a in part_mesh(pp['PRT-0403']))
    # Fixed feeder follows lift carriage but neither yaw nor pitch.
    m.append(box((30,30,880),(-310,0,height+120),ASM['ASM-06']['color'],'PRT-0602'))
    m.append(box((140,30,20),(-250,0,height+400),ASM['ASM-06']['color'],'PRT-0602'))
    for y in [-66,66]:m.append(box((140,10,90),(-190,y,height+320),ASM['ASM-06']['color'],'PRT-0602'))
    inst('PRT-0601',(-190,0,height+380))
    inst('PRT-0606',(-190,0,height+(185 if guide_up else 70)))
    inst('PRT-0607',(-280,45,height+160))
    for sy in [-1,1]:
        inst('PRT-0603',(-190,sy*55,height+320))
        inst('PRT-0605',(-235,sy*88,height+320))
    inst('PRT-0604',(-190,0,height+290))
    # Lower cabinet and visible operator controls.
    if show_guards:inst('PRT-0803',(0,0,285))
    inst('PRT-0902',(-70,65,235));inst('PRT-0903',(100,55,245));inst('PRT-0901',(90,-110,235))
    for xx in [-100,35]:inst('PRT-0507',(xx,-90,220))
    inst('PRT-0904',(-95,-90,940))
    inst('PRT-1003',(-90,-90,1000));inst('PRT-1001',(-100,-90,1040),ry=70)
    inst('PRT-1002',(-240,-110,420))
    return m

def camera(view='iso'):
    if view=='front':return (0,1,0),(0,0,1),(1,0,0)
    if view=='side':return (1,0,0),(0,0,1),(0,-1,0)
    if view=='top':return (1,0,0),(0,1,0),(0,0,1)
    cam=norm((6,-8,5));u=norm(cross((0,0,1),cam));v=cross(cam,u)
    return u,v,cam

def projected(meshes,view='iso'):
    u,v,cam=camera(view); light=norm((-.4,-.5,1)); out=[]; allpts=[]
    for m in meshes:
        for f in m.faces:
            normal=norm(cross(add(f[1],mul(f[0],-1)),add(f[2],mul(f[0],-1))))
            if dot(normal,cam)<-.02:continue
            pts=[(dot(p,u),dot(p,v)) for p in f];allpts.extend(pts)
            lum=.64+.36*max(0,dot(normal,light))
            out.append(dict(points=pts,depth=sum(dot(p,cam) for p in f)/len(f),fill=shade(m.color,lum),alpha=m.alpha,pid=m.pid))
    out.sort(key=lambda f:f['depth'])
    if not allpts:return [],(0,0,1,1)
    return out,(min(p[0] for p in allpts),min(p[1] for p in allpts),max(p[0] for p in allpts),max(p[1] for p in allpts))

def draw_mesh(c,meshes,rect,view='iso',wire=False):
    x,y,w,h=rect; fs,bb=projected(meshes,view)
    sx=w/max(1,bb[2]-bb[0]);sy=h/max(1,bb[3]-bb[1]);s=min(sx,sy)
    ox=x+(w-(bb[2]-bb[0])*s)/2-bb[0]*s;oy=y+(h-(bb[3]-bb[1])*s)/2-bb[1]*s
    c.saveState();c.setLineWidth(.28)
    for f in fs:
        pts=[(ox+a*s,oy+b*s) for a,b in f['points']]
        path=c.beginPath();path.moveTo(*pts[0])
        for p in pts[1:]:path.lineTo(*p)
        path.close()
        from reportlab.lib.colors import HexColor
        c.setFillColor(HexColor('#FFFFFF' if wire else f['fill']));c.setStrokeColor(HexColor('#5F7381' if wire else f['fill']))
        c.drawPath(path,fill=1,stroke=1)
    c.restoreState()
    def project_point(p):
        u,v,cam=camera(view)
        return ox+dot(p,u)*s,oy+dot(p,v)*s
    return project_point

def svg(meshes,path,view='iso',width=1200,height=900,title='',subtitle='Concept geometry; not a manufacturing drawing'):
    fs,bb=projected(meshes,view);margin=60
    s=min((width-2*margin)/max(1,bb[2]-bb[0]),(height-2*margin-50)/max(1,bb[3]-bb[1]))
    ox=(width-(bb[2]-bb[0])*s)/2-bb[0]*s;oy=(height-50-(bb[3]-bb[1])*s)/2-bb[1]*s
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
         '<rect width="100%" height="100%" fill="#f5f8f8"/>']
    for f in fs:
        pts=' '.join(f'{ox+a*s:.2f},{height-50-(oy+b*s):.2f}' for a,b in f['points'])
        out.append(f'<polygon points="{pts}" fill="{f["fill"]}" stroke="{f["fill"]}" stroke-width="0.5"/>')
    out.append(f'<text x="40" y="{height-32}" font-family="sans-serif" font-size="20" fill="#243847">{html.escape(title)}</text>')
    out.append(f'<text x="40" y="{height-10}" font-family="sans-serif" font-size="13" fill="#657887">{html.escape(subtitle)}</text></svg>')
    Path(path).write_text('\n'.join(out),encoding='utf-8')

def subassembly_mesh(aid,exploded=False):
    ps=[p for p in PARTS if p['assembly_id']==aid];out=[]
    # Exploded catalogue view: all unique types, not an installation drawing.
    for i,p in enumerate(ps):
        col=i%3;row=i//3
        mesh=part_mesh(p)
        maxd=max(p['bbox_mm']);sc=125/maxd
        for m in mesh:
            m=Mesh([[mul(v,sc) for v in f] for f in m.faces],m.color,m.pid)
            out.append(m.transformed((col*170,row*170,0)))
    return out

def exploded_subassembly(aid):
    """Unfused illustrative placement; independent type offsets, never a removal-path claim."""
    scene=[m for m in world_scene(True) if m.pid.startswith('PRT-'+aid[-2:])]
    if aid=='ASM-05':scene=[m for m in scene if m.pid!='PRT-0507']
    if aid=='ASM-08':scene=[m for m in scene if m.pid!='PRT-0803']
    ps=[p['part_id'] for p in PARTS if p['assembly_id']==aid]
    out=[]
    for m in scene:
        i=ps.index(m.pid)
        # An exploded sheet may compress large already-separated layout distances.
        if aid in ['ASM-09','ASM-10']:
            return subassembly_mesh(aid,True)
        out.append(m.transformed((i*32,0,i*55)))
    return out or subassembly_mesh(aid,True)
