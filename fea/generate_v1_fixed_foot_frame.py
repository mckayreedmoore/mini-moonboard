"""Generate a deliberately conservative fixed-foot CalculiX frame screen.

This is a repeatable *screening* deck, not an approved wood design. It turns
the CAD frame centre-lines into B31 beams and intentionally excludes panels,
holes, holds, T-nuts, LEDs, fastener strength, adhesive, contact, and floor
uplift.  Fixed feet make it useful only for identifying likely frame issues;
the separately generated stability screen governs unanchored safety.
"""

from __future__ import annotations

from itertools import pairwise
from pathlib import Path

from mini_moonboard.model import (
    V1_PANEL_SIZE_MM,
    V1_SUPPORT_THICKNESS_MM,
    V1_SUPPORT_WIDTH_MM,
    v1_face_rail_centres,
    v1_leg_geometry,
    v1_support_side_point,
)

OUTPUT = Path("fea/generated/v1_fixed_foot_frame.inp")
RAIL_DISTANCES = (0.0, 400.0, 1000.0, 1600.0, 1880.0, 2 * V1_PANEL_SIZE_MM)
PLYWOOD_E_MPA = 7_000.0
PLYWOOD_NU = 0.30
CLIMBER_LOAD_N = 1_200.0


def build_deck() -> str:
    """Return the self-contained CalculiX input deck for five screen cases."""
    nodes: list[tuple[str, float, float, float]] = []
    elements: list[tuple[str, str, str]] = []

    def node(name: str, x: float, y: float, z: float) -> None:
        nodes.append((name, x, y, z))

    def element(name: str, first: str, second: str) -> None:
        elements.append((name, first, second))

    rails = v1_face_rail_centres()
    for rail_index, x in enumerate(rails, start=1):
        for distance_index, distance in enumerate(RAIL_DISTANCES):
            y, z = v1_support_side_point(distance, 72.0)
            node(f"R{rail_index}_{distance_index}", x, y, z)
        for distance_index in range(len(RAIL_DISTANCES) - 1):
            element(f"rail_{rail_index}_{distance_index}", f"R{rail_index}_{distance_index}", f"R{rail_index}_{distance_index + 1}")

    # Rail-grid ties at the three actual cross-tie distances. Sort rails by X
    # because the seam rail is deliberately offset from the primary sequence.
    ordered_rails = tuple(sorted(enumerate(rails, start=1), key=lambda item: item[1]))
    for distance_index in (1, 2, 3):
        for (first, _), (second, _) in pairwise(ordered_rails):
            element(f"tie_{distance_index}_{first}_{second}", f"R{first}_{distance_index}", f"R{second}_{distance_index}")

    leg = v1_leg_geometry()
    leg_x = V1_PANEL_SIZE_MM + V1_SUPPORT_WIDTH_MM / 2 + V1_SUPPORT_THICKNESS_MM / 2
    for side, sign, outer_rail in (("left", -1, 1), ("right", 1, 4)):
        node(f"{side}_foot", sign * leg_x, leg["foot_y"], 0.0)
        node(f"{side}_bend", sign * leg_x, leg["bend_y"], leg["bend_z"])
        node(f"{side}_upper", sign * leg_x, leg["upper_y"], leg["upper_z"])
        element(f"{side}_lower_leg", f"{side}_foot", f"{side}_bend")
        element(f"{side}_upper_leg", f"{side}_bend", f"{side}_upper")
        element(f"{side}_rail_link", f"{side}_upper", f"R{outer_rail}_4")
        element(f"{side}_knee_brace", f"{side}_bend", f"R{outer_rail}_3")

    number = {name: index for index, (name, *_coords) in enumerate(nodes, start=1)}
    lines = [
        "** V1 fixed-foot linear frame screen. Generated; do not hand-edit.",
        "** Assumptions: isotropic E=7000 MPa, nu=0.30; 36 x 180 mm B31 members.",
        "** Fixed feet are a structural upper bound only; unanchored stability fails separately.",
        "*NODE",
        *(f"{number[name]}, {x:.6f}, {y:.6f}, {z:.6f}" for name, x, y, z in nodes),
        "*ELEMENT, TYPE=B31, ELSET=FRAME",
        *(f"{index}, {number[first]}, {number[second]}" for index, (_name, first, second) in enumerate(elements, start=1)),
        "*NSET, NSET=FEET",
        f"{number['left_foot']}, {number['right_foot']}",
        "*NSET, NSET=TOP_RAILS",
        ", ".join(str(number[f"R{rail_index}_{len(RAIL_DISTANCES) - 1}"]) for rail_index in range(1, len(rails) + 1)),
        "*MATERIAL, NAME=PLYWOOD_SCREEN",
        "*ELASTIC",
        f"{PLYWOOD_E_MPA:.1f}, {PLYWOOD_NU:.3f}",
        "*BEAM SECTION, ELSET=FRAME, MATERIAL=PLYWOOD_SCREEN, SECTION=RECT",
        f"{V1_SUPPORT_THICKNESS_MM:.1f}, {V1_SUPPORT_WIDTH_MM:.1f}",
        "0., 0., 1.",
    ]
    load_cases = (
        ("TOP_NORMAL_TO_SUPPORT", (0.0, CLIMBER_LOAD_N * 0.7660444431 / len(rails), -CLIMBER_LOAD_N * 0.6427876097 / len(rails))),
        ("TOP_NORMAL_FROM_SUPPORT", (0.0, -CLIMBER_LOAD_N * 0.7660444431 / len(rails), CLIMBER_LOAD_N * 0.6427876097 / len(rails))),
        ("TOP_DOWN_BOARD", (0.0, -CLIMBER_LOAD_N * 0.6427876097 / len(rails), -CLIMBER_LOAD_N * 0.7660444431 / len(rails))),
        ("TOP_LATERAL_LEFT", (-CLIMBER_LOAD_N / len(rails), 0.0, 0.0)),
        ("TOP_COMBINED", (-CLIMBER_LOAD_N * 0.4 / len(rails), CLIMBER_LOAD_N * 0.7660444431 / len(rails), -CLIMBER_LOAD_N * 0.6427876097 / len(rails))),
    )
    top_nodes = [number[f"R{rail_index}_{len(RAIL_DISTANCES) - 1}"] for rail_index in range(1, len(rails) + 1)]
    for name, (load_x, load_y, load_z) in load_cases:
        lines.extend((f"** CASE {name}", "*STEP", "*STATIC", "*BOUNDARY", "FEET, 1, 6, 0."))
        lines.append("*CLOAD")
        for node_number in top_nodes:
            for dof, value in enumerate((load_x, load_y, load_z), start=1):
                if value:
                    lines.append(f"{node_number}, {dof}, {value:.6f}")
        lines.extend(("*NODE PRINT, NSET=TOP_RAILS", "U", "*EL PRINT, ELSET=FRAME", "S", "*END STEP"))
    return "\n".join(lines) + "\n"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_deck())
    print(OUTPUT)


if __name__ == "__main__":
    main()
