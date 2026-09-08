"""Unspliced top/bottom crossmembers; connection resistance still unqualified."""
from dataclasses import replace
from functools import cache

from . import box_frame as b
from . import lean_frame as baseline
from . import product_frame as product
from . import wood_mvp as wood

KEY = "continuous-lean-frame"
REPLACEMENTS = {f"lean_beam_{level}_{side}": f"lean_beam_{level}_full"
                for level in ("top", "lower") for side in ("left", "right")}


@cache
def connections():
    result = []
    for c in baseline.connections():
        members = tuple(REPLACEMENTS.get(name, name) for name in c.members)
        station = (c.start-b.point(0, 0, 0)).dot(product.TANGENT)
        if c.name.startswith("lean_panel_") and station > 2400.3:
            members = (c.members[0], "lean_beam_top_full")
        result.append(replace(c, members=members))
    return tuple(result)


@cache
def parts(drilled=True):
    result = {p.name: p for p in baseline.parts(False) if p.name not in REPLACEMENTS}
    for side in ("left", "right"):
        name = "lean_principal_"+side
        p = result[name]
        result[name] = replace(p,
            shape=p.shape.cut(b.block(-b.HALF, b.HALF, 2400.3, b.LENGTH+1, -1, 140.7)).clean(),
            blank=(2400.3-139.7, 139.7, 38.1),
            description="Square-ended 2x6 upright terminating beneath continuous top rail; unqualified joints")
    for level, s0, s1, n0, n1 in (("top", 2400.3, 2438.4, 0., 139.7),
                                 ("lower", 100., 138.1, 38.1, 177.8)):
        name = f"lean_beam_{level}_full"
        result[name] = b.Part(name, b.block(-b.HALF, b.HALF, s0, s1, n0, n1),
            (2*b.HALF, 139.7, 38.1),
            "Continuous unspliced 8-ft 2x6 crossmember tying both sides; grain X; "
            "no central cutout or splice; retained connector proxies and joint strength unqualified", 1)
    return wood.drill_parts(result, connections()) if drilled else tuple(result.values())
