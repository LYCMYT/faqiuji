"""Pose cached solids while rebuilding any state-dependent geometry."""
from cad.parts.recipe import build
from cad.assemblies.kinematics import parameters

def pose_shape(item,cached_shape,state,recipe):
    from cad.export_all import locate
    shape=cached_shape
    if item.get('dynamic_height') or item.get('dynamic_slide'):
        p=parameters();env=dict(p,head_axis_height=state.get('height',p['head_axis_height']),slide=state.get('slide',0))
        shape=build(recipe,env)
    return locate(shape,item['parent'],state)
