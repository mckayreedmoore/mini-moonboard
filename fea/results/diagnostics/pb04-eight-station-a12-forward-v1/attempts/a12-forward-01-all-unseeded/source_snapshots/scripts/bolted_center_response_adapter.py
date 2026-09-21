"""Provisional center-bolt topology around the pinned current response model."""

import numpy as np

from fea import current_response_model as base
from fea import round_insert_frame as shared
from fea.floor_flush_mesh import FlushStructure, prepare_flush

REPLACED_CLIPS = {
    "clip_split_base_center_left",
    "clip_split_header_center_left",
}


def rigid_bolt(structure, points):
    """Free vertical shaft with translation and two bending tilts."""
    centre = np.mean(points, axis=0)
    translation = structure.node(centre)
    rotation = structure.node(centre)
    structure.rotation_masters.add(rotation)
    tags = []
    for point in points:
        tag = structure.node(point)
        r = np.array(point) - centre
        for i in range(3):
            j, k = (i + 1) % 3, (i + 2) % 3
            terms = [(tag, i + 1, 1.), (translation, i + 1, -1.)]
            if j < 2 and abs(r[k]) > 1.e-13:
                terms.append((rotation, j + 1, -float(r[k])))
            if k < 2 and abs(r[j]) > 1.e-13:
                terms.append((rotation, k + 1, float(r[j])))
            structure.equations.append(terms)
        tags.append(tag)
    return tags


def add_joint(structure, metadata, joint):
    """Add only the representative angles, shaft and contact branches."""
    ownership = metadata["connection_ownership"]
    tags = {}
    for angle in joint["angles"]:
        points = [np.asarray(p) for p in (
            *angle["vertical_points"], *angle["header_points"], *angle["contact_points"]
        )]
        tags[angle["name"]] = structure.rigid_angle(angle["name"], points)
        for index, point in enumerate(points[:2]):
            name = f"{angle['name']}_wood_{index}"
            owner = {"first": angle["wood_member"], "second": angle["name"],
                     "point": point.tolist(), "axis": [1., 0., 0.]}
            base.directional_connector(
                structure, structure.attachment(angle["wood_member"], point),
                tags[angle["name"]][index], joint["vertical_spring"], name, owner
            )
            ownership[name] = owner
        for index, point in enumerate(points[4:]):
            name = f"{angle['name']}_flange_contact_{index}"
            inward = angle["contact_inward_xyz"]
            shared.normal_contact(
                structure, name, structure.attachment("base_header", point),
                [tags[angle["name"]][index + 4]], [1.], point, inward,
                joint["flange_contact_n_per_mm"]
            )
            ownership[name] = {"first": "base_header", "second": angle["name"],
                               "point": point.tolist(), "scalar_normal": inward}
    for index, bolt in enumerate(joint["shared_header_bolts"]):
        points = [np.asarray(bolt[key]) for key in (
            "top_point", "wood_upper_point", "wood_lower_point", "bottom_point"
        )]
        bolt_tags = rigid_bolt(structure, points)
        for angle_index, angle in enumerate(joint["angles"]):
            side = 0 if angle_index == 0 else 3
            name = f"{bolt['name']}_{angle['name']}"
            owner = {"first": angle["name"], "second": bolt["name"],
                     "point": points[side].tolist(), "axis": [0., 0., 1.]}
            base.directional_connector(
                structure, tags[angle["name"]][index + 2], bolt_tags[side],
                joint["steel_bolt_spring"], name, owner
            )
            ownership[name] = owner
        for side, label in ((1, "upper"), (2, "lower")):
            name = f"{bolt['name']}_header_bearing_{label}"
            owner = {"first": "base_header", "second": bolt["name"],
                     "point": points[side].tolist(), "axis": [0., 0., 1.]}
            structure.spring(
                structure.attachment("base_header", points[side]), bolt_tags[side],
                joint["wood_bearing_lateral_n_per_mm"], name, dofs=(1, 2)
            )
            ownership[name] = owner
    metadata["diagnostic_center_joint"] = joint
    metadata["legacy_center_hardware_mass_surrogate"] = True


def prepare_center(module, joint, **kwargs):
    if set(joint["replaced_clips"]) != REPLACED_CLIPS:
        raise ValueError("Only the left center representative clip pair may be replaced")

    extra = {angle["wood_member"]: [np.asarray(p) for p in angle["vertical_points"]]
             for angle in joint["angles"]}
    extra["base_header"] = [
        np.asarray(p) for angle in joint["angles"] for p in angle["contact_points"]
    ] + [
        np.asarray(bolt[key]) for bolt in joint["shared_header_bolts"]
        for key in ("wood_upper_point", "wood_lower_point")
    ]

    class CenterModule:
        def __getattr__(self, name):
            return getattr(module, name)

        def connections(self):
            return tuple(c for c in module.connections()
                         if not (c.name.startswith("clip_") and
                                 c.members[0] in REPLACED_CLIPS))

    original_mass, original_member = base.mass_by_body, FlushStructure.member

    def legacy_mass(_module, raw, materials):
        return original_mass(module, raw, materials)

    def joint_member(self, record, attachment_points=(), size=100.):
        return original_member(
            self, record, [*attachment_points, *extra.get(record["name"], ())], size
        )

    try:
        base.mass_by_body = legacy_mass
        FlushStructure.member = joint_member
        structure, metadata = prepare_flush(CenterModule(), **kwargs)
    finally:
        base.mass_by_body, FlushStructure.member = original_mass, original_member
    add_joint(structure, metadata, joint)
    return structure, metadata
