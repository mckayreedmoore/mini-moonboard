"""Pure geometry helpers for the ideal screw-head panel screen."""
import math


def dot(a,b):
    return sum(x*y for x,y in zip(a,b,strict=True))


def minus(a,b):
    return tuple(x-y for x,y in zip(a,b,strict=True))


def head_nodes(nodes, record, screw):
    """Select the modeled conical seating face, not a nearby panel node."""
    result=[]
    for tag,xyz in nodes.items():
        delta=minus(xyz,screw["head_mm"])
        depth=dot(delta,record["normal"])
        radius=math.sqrt(max(0,dot(delta,delta)-depth*depth))
        expected=5-(5-screw["shank_diameter_mm"]/2)*depth/3
        if -1e-5<=depth<=3+1e-5 and abs(radius-expected)<1e-4:
            result.append(tag)
    if len(result)<6:
        raise ValueError(f"Unresolved screw seating face: {screw['name']}")
    return result
