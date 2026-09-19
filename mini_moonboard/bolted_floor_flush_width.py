"""Official and kerf-right presentations for the AB90 prototype candidate."""

from dataclasses import replace

from . import compact_floor_flush_bolted_frame as candidate
from . import floor_flush_width as baseline_width

OFFICIAL = "official"
KERF_RIGHT = "kerf-right"
OPTIONS = (OFFICIAL, KERF_RIGHT)
KERF_RIGHT_MM = baseline_width.KERF_RIGHT_MM
TRANSLATE_NAMES = baseline_width.TRANSLATE_NAMES


def require_option(option: str) -> str:
    if option not in OPTIONS:
        raise ValueError(f"Width option must be {OFFICIAL} or {KERF_RIGHT}")
    return option


def _right_side(name: str) -> bool:
    return any(token in name for token in ("_right", "_right_"))


def _translate_connection(connection, option: str):
    # The frozen width packet moves only outer-right receivers. Center/right
    # panel axes remain at their official X positions despite their names.
    return baseline_width.transform_connection(connection, option)


def _translate_joint(joint, option: str):
    if option != KERF_RIGHT or not any(name in TRANSLATE_NAMES for name in joint.connected_members):
        return joint
    point = joint.local_basis.reference_point_mm
    basis = replace(joint.local_basis, reference_point_mm=(point[0] - KERF_RIGHT_MM, point[1], point[2]))
    return replace(joint, local_basis=basis)


class WidthAdapter:
    """Transform the candidate's participants without routing to old connections."""

    def __init__(self, option: str):
        self.option = require_option(option)
        self.source = candidate

    @property
    def KEY(self) -> str:
        return f"{candidate.KEY}-{self.option}"

    def candidate_metadata(self):
        return {**candidate.candidate_metadata(), "width": self.option, "width_evidence": "prototype geometry only"}

    def uncut_wood_parts(self):
        return tuple(baseline_width.transform_part(part, self.option) for part in self.source.uncut_wood_parts())

    def connections(self):
        return tuple(_translate_connection(connection, self.option) for connection in self.source.connections())

    def panel_connections(self):
        names = {connection.name for connection in self.source.panel_connections()}
        return tuple(connection for connection in self.connections() if connection.name in names)

    def structural_joint_records(self):
        return tuple(_translate_joint(joint, self.option) for joint in self.source.structural_joint_records())

    def fastener_stack_records(self):
        return self.source.fastener_stack_records()

    def assembly_interface_records(self):
        return self.source.assembly_interface_records()

    def machining_records(self):
        return tuple({**record, "width": self.option} for record in self.source.machining_records())

    def attachment_datums(self):
        xs = {connection.name: connection.start.x for connection in self.panel_connections()}
        return tuple({**row, "x": xs[row["name"]]} for row in self.source.attachment_datums())

    def parts(self):
        return self.source.parts()


def variant(option: str = OFFICIAL):
    return WidthAdapter(KERF_RIGHT) if require_option(option) == KERF_RIGHT else WidthAdapter(OFFICIAL)


def geometry_screen() -> dict[str, object]:
    official = variant(OFFICIAL)
    kerf = variant(KERF_RIGHT)
    official_right = {c.name: c for c in official.connections() if _right_side(c.name)}
    kerf_right = {c.name: c for c in kerf.connections() if _right_side(c.name)}
    shifted = [name for name, connection in official_right.items()
               if any(member in TRANSLATE_NAMES for member in connection.members)]
    stationary = set(official_right) - set(shifted)
    shifts = [official_right[name].start.x - kerf_right[name].start.x for name in shifted]
    stationary_shifts = [official_right[name].start.x - kerf_right[name].start.x for name in stationary]
    return {
        "official_key": official.KEY,
        "kerf_right_key": kerf.KEY,
        "right_interface_count": len(shifts),
        "stationary_right_interface_count": len(stationary_shifts),
        "right_shift_mm": KERF_RIGHT_MM,
        "right_shift_consistent": bool(shifts) and all(abs(value - KERF_RIGHT_MM) < 1e-6 for value in shifts)
        and all(abs(value) < 1e-6 for value in stationary_shifts),
        "panel_axes_official": len(official.panel_connections()),
        "panel_axes_kerf_right": len(kerf.panel_connections()),
        "structural_joints_official": len(official.structural_joint_records()),
        "structural_joints_kerf_right": len(kerf.structural_joint_records()),
        "mechanical_evidence_for_kerf_right": False,
        "scope": "Width presentation screen only; official native evidence is not transferred.",
    }
