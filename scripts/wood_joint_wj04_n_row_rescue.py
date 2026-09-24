"""Historical WJ-04 rail-row N sweep for the catalog bolt/spacer diagnostic.

This is retained as history after the owner selected the ordinary
bolt/nut/two-washer approach. It intentionally leaves the shared WJ-04
producer unchanged. Tool bodies are exterior bounds, not purchased tool CAD
or a service release.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import cadquery as cq

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from mini_moonboard.wood_joint_frame import validate_source_binding
from scripts.wood_joint_clearance import _wj03_protected_inventory

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/wood-joints-mvp/wj04-n-row-rescue.json"
SOURCE_INVENTORY = ROOT / "docs/wood-joints-mvp/source-inventory.json"
HISTORICAL_SOURCE_INVENTORY_SHA256 = "07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78"
HISTORICAL_PROTECTED_BUILDER_SHA256 = "580f0989c300087cd66bf998e9d6d83965604fdf9e98ee1cdb4746f3e688b774"
HISTORICAL_SOURCE_COMMIT = "df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb"
UPRIGHT = "base_principal_center_right"
RAIL = "base_rail_service_lower_right"
NEIGHBOR = "base_rail_service_upper_right"
LEGACY_DUTY = "clip_horizontal_lower_right_1"
FRONT_SHIFT_MM = 20.0
SECTION_T_MM = 38.1
CLEAT_X_MM = 95.25
HISTORICAL_FRAME_DEGREES = 50.0
T = cq.Vector(0, 0.6427876096865394, 0.766044443118978)
N = cq.Vector(0, -0.766044443118978, 0.6427876096865394)
X = cq.Vector(1, 0, 0)
HIT_MM3 = 1e-6
ROWS = [245.0 + 2.5 * i for i in range(9)]
X_OFFSETS = (38.1, 63.5)
WOOD_GRIP = 76.2
WASHER_MIN, WASHER_MAX = 1.2954, 2.032
SPACER_MIN, SPACER_MAX = 12.573, 12.827
NUT_MIN, NUT_MAX = 5.3848, 5.7404
BOLT_MAX = 114.3
SOCKET_LENGTH = 22.0
SOCKET_DIAMETER_MAX = 15.8
RATCHET_HEAD_THICKNESS = 8.89
RATCHET_HEAD_WIDTH = 24.892
OPEN_HEAD_THICKNESS = 3.0
OPEN_HEAD_WIDTH = 23.0


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _historical_source():
    """Bind this parked sweep to its recorded baseline, not current WJ-04 config."""
    if _sha256(SOURCE_INVENTORY) != HISTORICAL_SOURCE_INVENTORY_SHA256:
        raise ValueError("Historical WJ-04 rescue source inventory changed")
    inventory = json.loads(SOURCE_INVENTORY.read_text(encoding="utf-8"))
    if inventory.get("source_commit") != HISTORICAL_SOURCE_COMMIT:
        raise ValueError("Historical WJ-04 rescue source commit changed")
    protected_builder = ROOT / "scripts/wood_joint_clearance.py"
    if _sha256(protected_builder) != HISTORICAL_PROTECTED_BUILDER_SHA256:
        raise ValueError("Historical WJ-04 rescue protected inventory builder changed")
    source = variant(KERF_RIGHT)
    binding = validate_source_binding(source)
    if binding.inventory_sha256 != HISTORICAL_SOURCE_INVENTORY_SHA256:
        raise ValueError("Historical WJ-04 rescue source binding changed")
    return source


def _world(x: float, t: float, n: float) -> cq.Vector:
    return X * x + T * t + N * n


def _extent(shape: cq.Shape, axis: cq.Vector) -> tuple[float, float]:
    values = [vertex.Center().dot(axis) for vertex in shape.Vertices()]
    return min(values), max(values)


def _intersect_volume(first: cq.Shape, second: cq.Shape) -> float:
    a, b = first.BoundingBox(), second.BoundingBox()
    if (
        a.xmax < b.xmin or b.xmax < a.xmin
        or a.ymax < b.ymin or b.ymax < a.ymin
        or a.zmax < b.zmin or b.zmax < a.zmin
    ):
        return 0.0
    return first.intersect(second).Volume()


def _hits(shape: cq.Shape, others: dict[str, cq.Shape]) -> dict[str, float]:
    return {
        name: round(volume, 6)
        for name, other in others.items()
        if (volume := _intersect_volume(shape, other)) > HIT_MM3
    }


def _protected(source) -> dict[str, cq.Shape]:
    rows = _wj03_protected_inventory(source)["solids"]
    return {
        f"{family}/{name}": shape
        for family, family_rows in rows.items()
        for name, shape in family_rows.items()
        if LEGACY_DUTY not in name
    }


def cylinder(radius: float, length: float, start: cq.Vector) -> cq.Shape:
    return cq.Solid.makeCylinder(radius, length, start, T)


def report() -> dict:
    source = _historical_source()
    wood = {part.name: part.shape for part in source.uncut_wood_parts()}
    rail, upright, upper = wood[RAIL], wood[UPRIGHT], wood[NEIGHBOR]
    t0, t1 = _extent(rail, T)
    n0, n1 = _extent(rail, N)
    upper_t0, upper_t1 = _extent(upper, T)
    upper_n0, upper_n1 = _extent(upper, N)
    x0 = upright.BoundingBox().xmax
    cleat_front = n0 + FRONT_SHIFT_MM
    cleat = cq.Solid.makeBox(CLEAT_X_MM, SECTION_T_MM, n1 - cleat_front)
    cleat = cleat.rotate((0, 0, 0), (1, 0, 0), 50)
    cleat = cleat.translate(_world(x0, t1, cleat_front))
    protected = _protected(source)
    other_wood = {name: part for name, part in wood.items() if name not in (RAIL, UPRIGHT)}
    rows = []
    for n in ROWS:
        axes = []
        for number, x_offset in enumerate(X_OFFSETS, 1):
            x = x0 + x_offset
            bore = cylinder(3.75, WOOD_GRIP + 0.2, _world(x, t0 - 0.1, n))
            rail_segment = cylinder(3.75, 38.1, _world(x, t0, n))
            cleat_segment = cylinder(3.75, 38.1, _world(x, t1, n))
            # Max catalog exterior sizes, plus minimum head washer for the
            # farthest bolt/tool projection toward the neighboring rail.
            head = cylinder(9.525 / 2, 6.35, _world(x, t0 - WASHER_MIN - 6.35, n))
            head_washer = cylinder(19.0246 / 2, WASHER_MIN, _world(x, t0 - WASHER_MIN, n))
            wood_washer = cylinder(19.0246 / 2, WASHER_MAX, _world(x, t0 + WOOD_GRIP, n))
            spacer = cylinder(12.827 / 2, SPACER_MAX, _world(x, t0 + WOOD_GRIP + WASHER_MAX, n))
            outer_washer = cylinder(19.0246 / 2, WASHER_MAX, _world(x, t0 + WOOD_GRIP + WASHER_MAX + SPACER_MAX, n))
            nut_t = t0 + WOOD_GRIP + WASHER_MAX * 2 + SPACER_MAX
            nut = cylinder(12.827 / 2, NUT_MAX, _world(x, nut_t, n))
            tip_t = t0 - WASHER_MIN + BOLT_MAX
            shaft = cylinder(6.35 / 2, BOLT_MAX, _world(x, t0 - WASHER_MIN, n))
            socket_sweep = cylinder(SOCKET_DIAMETER_MAX / 2, tip_t + 0.1 + SOCKET_LENGTH - nut_t, _world(x, nut_t, n))
            ratchet_sweep = cylinder(RATCHET_HEAD_WIDTH / 2, tip_t + 0.1 + SOCKET_LENGTH + RATCHET_HEAD_THICKNESS - (nut_t + SOCKET_LENGTH), _world(x, nut_t + SOCKET_LENGTH, n))
            nut_sweep = cylinder(12.827 / 2, tip_t + 0.1 + NUT_MAX - nut_t, _world(x, nut_t, n))
            detached_nut_rearward = cq.Solid.makeCylinder(
                12.827 / 2, 100.0, _world(x, tip_t + 0.1 + NUT_MAX / 2, n), N
            )
            # A circular bound for the documented 23-mm-wide 7/16 open-end
            # head, translated with the nut; no handle or jaw shape claimed.
            open_head_start_t = nut_t + (NUT_MIN - OPEN_HEAD_THICKNESS) / 2
            open_head_end_t = tip_t + 0.1 + (NUT_MIN + OPEN_HEAD_THICKNESS) / 2
            open_head_sweep = cylinder(OPEN_HEAD_WIDTH / 2, open_head_end_t - open_head_start_t, _world(x, open_head_start_t, n))
            exterior = {"head": head, "head_washer": head_washer, "wood_washer": wood_washer, "spacer": spacer, "outer_washer": outer_washer, "nut": nut}
            sweeps = {"socket": socket_sweep, "ratchet_head": ratchet_sweep, "nut": nut_sweep, "detached_nut_rearward": detached_nut_rearward, "open_end_head": open_head_sweep}
            axes.append({
                "id": f"rail_{number}",
                "x_mm": round(x, 6),
                "n_mm": n,
                "rail_segment_wood_fraction": round(_intersect_volume(rail_segment, rail) / rail_segment.Volume(), 6),
                "cleat_segment_wood_fraction": round(_intersect_volume(cleat_segment, cleat) / cleat_segment.Volume(), 6),
                "bore_other_wood_hits": _hits(bore, other_wood),
                "bore_protected_hits": _hits(bore, protected),
                "shaft_other_wood_hits": _hits(shaft, other_wood),
                "shaft_protected_hits": _hits(shaft, protected),
                "installed_exterior_hits": {key: {"other_wood": _hits(shape, other_wood), "protected": _hits(shape, protected)} for key, shape in exterior.items()},
                "moving_envelope_hits": {key: {"other_wood": _hits(shape, other_wood), "protected": _hits(shape, protected)} for key, shape in sweeps.items()},
                "tool_upper_rail_gap_mm": round(upper_t0 - (tip_t + 0.1 + SOCKET_LENGTH + RATCHET_HEAD_THICKNESS), 6),
                "removed_nut_upper_rail_gap_mm": round(upper_t0 - (tip_t + 0.1 + NUT_MAX), 6),
                "open_end_head_upper_rail_gap_mm": round(upper_t0 - open_head_end_t, 6),
                "principal_bolt_n_separation_min_mm": round(293.0 - n, 6),
            })
        rows.append({
            "n_mm": n,
            "rail_front_lateral_margin_mm": round(n - n0, 6),
            "rail_rear_lateral_margin_mm": round(n1 - n, 6),
            "cleat_front_grain_end_margin_mm": round(n - cleat_front, 6),
            "cleat_rear_grain_end_margin_mm": round(n1 - n, 6),
            "cleat_front_minus_conditional_4d_mm": round(n - cleat_front - 25.4, 6),
            "temporary_100mm_nut_exit_excess_past_ordinary_rear_mm": round(max(0.0, n + 100.0 + 12.827 / 2 - n1), 6),
            "rail_x_near_end_minus_conditional_7d_mm": -6.35,
            "axes": axes,
        })
    return {
        "schema": "wood_joint_wj04_n_row_rescue/v1",
        "historical_only": True,
        "superseded_by": "owner direction to prioritize one ordinary bolt/nut/two-washer WJ-04 joint",
        "status": "diagnostic_revise",
        "source": "compact-floor-flush-development kerf-right uncut parts; local WJ-04 station",
        "station": "clip_horizontal_lower_right_1",
        "rail_t_mm": [round(t0, 6), round(t1, 6)],
        "upper_rail_t_mm": [round(upper_t0, 6), round(upper_t1, 6)],
        "rail_n_mm": [round(n0, 6), round(n1, 6)],
        "upper_rail_n_mm": [round(upper_n0, 6), round(upper_n1, 6)],
        "cleat_n_mm": [round(cleat_front, 6), round(n1, 6)],
        "x_offsets_mm": list(X_OFFSETS),
        "protected_body_count": len(protected),
        "rows": rows,
        "limits": ["Catalog outer bounds only; no nut hex, socket bore, drive tang, jaw/handle swing, or full assembly CAD", "No material capacity or NDS signed-edge acceptance", "WJ-03 connector parts absent from protected inventory; selected 66 screws retained", "No tolerance-aware hardware/tool release"],
    }


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(report(), indent=2) + "\n")
    print(OUTPUT)
