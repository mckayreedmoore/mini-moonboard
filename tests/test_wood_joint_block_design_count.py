import cadquery as cq

from scripts.wood_joint_block_design_count import equivalent_by_rotation


def block():
    raw = cq.Solid.makeBox(30, 40, 50)
    return raw.cut(
        cq.Solid.makeCylinder(2, 50, cq.Vector(7, 9, 0)),
        cq.Solid.makeCylinder(3, 50, cq.Vector(21, 15, 0)),
        cq.Solid.makeCylinder(2, 30, cq.Vector(0, 27, 31), cq.Vector(1, 0, 0)),
    )


def test_rotation_and_translation_preserve_drilled_design():
    a = block()
    b = a.rotate((0, 0, 0), (1, 2, 3), 47).translate((123, -456, 789))
    assert equivalent_by_rotation(a, b) is not None


def test_mirror_and_changed_hole_are_distinct_designs():
    a = block()
    assert equivalent_by_rotation(a, a.mirror("YZ")) is None
    altered = a.cut(cq.Solid.makeCylinder(2, 50, cq.Vector(17, 29, 0)))
    assert equivalent_by_rotation(a, altered) is None
