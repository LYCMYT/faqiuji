"""Native OpenCascade solids from declarative data recipes. No mesh-to-STEP.
All dimensions and mounting positions come from data/, expressions may reference
design parameters, derived values, or main-item bounding dimensions.
"""
import ast, math, operator
import cadquery as cq
OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Pow:operator.pow}

def number(value,env):
    if not isinstance(value,str): return value
    def ev(n):
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)): return n.value
        if isinstance(n,ast.Name): return env[n.id]
        if isinstance(n,ast.BinOp) and type(n.op) in OPS: return OPS[type(n.op)](ev(n.left),ev(n.right))
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub): return -ev(n.operand)
        raise ValueError('Non arithmetic expression: '+value)
    return ev(ast.parse(value,mode='eval').body)

def build(r,env):
    n=lambda v:number(v,env); vs=lambda a:[n(v) for v in a]
    op=r['op']
    if op=='box':
        size=vs(r['size']); s=cq.Workplane('XY').box(*size).val()
    elif op in ('cylinder','ring','cone'):
        h=n(r['height']); R=n(r['radius']); s=cq.Solid.makeCone(R,n(r['radius2']),h) if op=='cone' else cq.Solid.makeCylinder(R,h)
        s=s.translate((0,0,-h/2))
        if op=='ring': s=s.cut(cq.Solid.makeCylinder(n(r['inner']),h+2,cq.Vector(0,0,-h/2-1)))
    elif op in ('cut','union','compound'):
        children=[build(x,env) for x in r['children']]; s=children[0]
        if op=='compound': s=cq.Compound.makeCompound(children)
        else:
            for other in children[1:]: s=s.cut(other) if op=='cut' else s.fuse(other)
            s=s.clean()
    elif op=='poly':
        s=cq.Workplane(r.get('plane','XZ')).polyline([tuple(vs(p)) for p in r['points']]).close().extrude(n(r['thickness'])/2,both=True).val()
    elif op=='return_loop':
        from cad.parts.cable import solid
        s=solid(*[n(r[k]) for k in ['fixed_x','moving_x','lower_z','upper_z','y','length','radius']],direction=r.get('direction',-1),exit_y=r.get('exit_y'))
    elif op=='wire':
        pts=[cq.Vector(*vs(p)) for p in r['points']];rad=n(r['radius']);segments=[]
        for a,b in zip(pts[:-1],pts[1:]):
            dv=b-a;segments.append(cq.Solid.makeCylinder(rad,dv.Length,a,dv.normalized()))
        segments.extend(cq.Solid.makeSphere(rad,p) for p in pts[1:-1]);s=segments[0]
        for t in segments[1:]:s=s.fuse(t)
        s=s.clean()
    else: raise ValueError(op)
    if 'rotate' in r:
        axis,angle=r['rotate']; s=s.rotate((0,0,0),tuple(axis),n(angle))
    return s.translate(tuple(vs(r.get('at',[0,0,0]))))
