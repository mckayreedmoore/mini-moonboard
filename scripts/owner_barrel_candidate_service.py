"""Candidate-only LED passage pose for the integrated barrel-frame proposal.

The selected kerf-right source and its historical 38.1 mm passage are unchanged.
This smaller passage is nominal occupancy, not verified harness feeding.
"""

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT_MM, TRANSLATE_NAMES

F1_G1_BORE = "bore_base_principal_center_right_072"
F1_G1_DIAMETER_MM = 25.4
SOURCE_DIAMETER_MM = 38.1


def candidate_service_cutters(source, wood):
    """Return source passages in active kerf pose, changing only F1–G1 size."""
    record = next(
        (row for row in source.bore_records() if row["name"] == F1_G1_BORE),
        None,
    )
    if (
        record is None
        or record["member"] != "base_principal_center_right"
        or record["datums"] != ["F1", "G1"]
        or abs(record["diameter_mm"] - SOURCE_DIAMETER_MM) > 1e-6
        or record["axis_local"] != "X"
    ):
        raise ValueError("Historical F1–G1 service passage changed")
    reduced = cq.Solid.makeCylinder(
        F1_G1_DIAMETER_MM / 2,
        record["length_mm"],
        cq.Vector(*record["start_mm"]),
        cq.Vector(*record["direction"]),
    )
    rows = []
    replaced = 0
    for member, name, cutter in source.service_cutters():
        if name == F1_G1_BORE:
            if member != record["member"]:
                raise ValueError("F1–G1 passage host changed")
            original = cq.Solid.makeCylinder(
                SOURCE_DIAMETER_MM / 2,
                record["length_mm"],
                cq.Vector(*record["start_mm"]),
                cq.Vector(*record["direction"]),
            )
            if abs(original.Volume() - cutter.Volume()) > 1e-3:
                raise ValueError("F1–G1 cutter differs from its bore record")
            cutter = reduced
            replaced += 1
        if member in TRANSLATE_NAMES:
            cutter = cutter.translate(cq.Vector(-KERF_RIGHT_MM, 0, 0))
        if member in wood and cutter.intersect(wood[member]).Volume() <= 1.0:
            raise ValueError(f"{name}: candidate service passage misses {member}")
        rows.append((member, name, cutter))
    if replaced != 1:
        raise ValueError("Expected exactly one F1–G1 passage")
    return tuple(rows)
