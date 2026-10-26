"""Analytic planar 180-degree return loop with fixed arc length."""
import math

def loop_geometry(fixed_x,moving_x,lower_z,upper_z,total,direction=-1):
    radius=(upper_z-lower_z)/2
    if radius<=0:raise ValueError('upper_z must exceed lower_z')
    bend_x=(fixed_x+moving_x+direction*(total-math.pi*radius))/2
    if direction==-1 and bend_x>=min(fixed_x,moving_x) or direction==1 and bend_x<=max(fixed_x,moving_x):raise ValueError('Cable too short for this travel')
    return radius,bend_x,(upper_z+lower_z)/2

def return_loop_length(fixed_x,moving_x,lower_z,upper_z,total,direction=-1):
    radius,bend_x,_=loop_geometry(fixed_x,moving_x,lower_z,upper_z,total,direction)
    return abs(fixed_x-bend_x)+abs(moving_x-bend_x)+math.pi*radius

def return_loop_points(fixed_x,moving_x,lower_z,upper_z,y,total,segments=48,direction=-1,exit_y=None):
    radius=(upper_z-lower_z)/2;loop_end=moving_x+direction*radius if exit_y is not None else moving_x
    radius,bend_x,cz=loop_geometry(fixed_x,loop_end,lower_z,upper_z,total,direction)
    pts=[(fixed_x,y,lower_z)]
    for i in range(segments+1):
        a=-math.pi/2+direction*math.pi*i/segments
        pts.append((bend_x+radius*math.cos(a),y,cz+radius*math.sin(a)))
    pts.append((loop_end,y,upper_z))
    if exit_y is not None:
        if exit_y<y+radius:raise ValueError('Exit tail too short for smooth radius')
        for i in range(1,segments//2+1):
            a=math.pi/2*i/(segments//2)
            pts.append((loop_end-direction*radius*math.sin(a),y+radius-radius*math.cos(a),upper_z))
        pts.append((moving_x,exit_y,upper_z))
    return pts

def solid(fixed_x,moving_x,lower_z,upper_z,y,total,cable_radius,direction=-1,exit_y=None):
    import cadquery as cq
    rad=(upper_z-lower_z)/2;loop_end=moving_x+direction*rad if exit_y is not None else moving_x
    rad,bx,cz=loop_geometry(fixed_x,loop_end,lower_z,upper_z,total,direction)
    a=cq.Vector(fixed_x,y,lower_z);b=cq.Vector(bx,y,lower_z)
    c=cq.Vector(bx,y,upper_z);d=cq.Vector(loop_end,y,upper_z)
    edges=[cq.Edge.makeLine(a,b),cq.Edge.makeThreePointArc(b,cq.Vector(bx+direction*rad,y,cz),c),cq.Edge.makeLine(c,d)]
    if exit_y is not None:
        if exit_y<y+rad:raise ValueError('Exit tail too short')
        e=cq.Vector(moving_x,y+rad,upper_z);mid=cq.Vector(loop_end-direction*rad/math.sqrt(2),y+rad-rad/math.sqrt(2),upper_z)
        edges += [cq.Edge.makeThreePointArc(d,mid,e),cq.Edge.makeLine(e,cq.Vector(moving_x,exit_y,upper_z))]
    wire=cq.Wire.assembleEdges(edges)
    profile=cq.Wire.makeCircle(cable_radius,a,cq.Vector(1,0,0))
    return cq.Solid.sweep(profile,[],wire,True,False)
