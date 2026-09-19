"""Explicit physical records for the unqualified bolted candidate.

These records describe hardware, stacks, and move semantics. They do not
provide connection resistance or turn the AB90 prototype into a build release.
All dimensions are millimetres and all identifiers are physical identities.
"""

from dataclasses import dataclass
from typing import Literal

HardwareScope = Literal["structural", "panel", "hold", "service"]
ThreadSubstrate = Literal["metal", "wood", "none"]
AssessmentStatus = Literal["prototype", "unresolved", "checked", "accepted"]


class ConnectionRecordError(ValueError):
    """Raised when a physical connection record is internally inconsistent."""


def _positive(value: float, label: str) -> float:
    if value <= 0:
        raise ConnectionRecordError(f"{label} must be positive")
    return float(value)


@dataclass(frozen=True)
class LocalBasis:
    """Right-handed local frame attached to a joint reference point."""

    reference_point_mm: tuple[float, float, float]
    u: tuple[float, float, float]
    v: tuple[float, float, float]
    w: tuple[float, float, float]


@dataclass(frozen=True)
class HoleDefinition:
    """One physical bore or factory hole in a named participant."""

    receiver_id: str
    diameter_mm: float
    kind: Literal["clearance", "factory", "pilot", "none"]
    axis: tuple[float, float, float]
    tolerance_mm: float | None = None

    def __post_init__(self) -> None:
        if not self.receiver_id:
            raise ConnectionRecordError("hole receiver_id is required")
        _positive(self.diameter_mm, "hole diameter")
        if self.tolerance_mm is not None and self.tolerance_mm < 0:
            raise ConnectionRecordError("hole tolerance cannot be negative")


@dataclass(frozen=True)
class StackComponent:
    """An ordered bearing element; None thickness means the grip is unresolved."""

    order: int
    component_id: str
    role: Literal["head", "washer", "plate", "receiver", "nut", "spacer"]
    thickness_mm: float | None
    substrate: ThreadSubstrate
    retained_on_move: bool

    def __post_init__(self) -> None:
        if self.order < 0 or not self.component_id:
            raise ConnectionRecordError("stack order and component_id are required")
        if self.thickness_mm is not None and self.thickness_mm < 0:
            raise ConnectionRecordError("stack thickness cannot be negative")
        if self.role not in ("head", "washer", "plate", "receiver", "nut", "spacer"):
            raise ConnectionRecordError("invalid stack role")
        if self.substrate not in ("metal", "wood", "none"):
            raise ConnectionRecordError("invalid stack substrate")


@dataclass(frozen=True)
class FastenerRecord:
    """A single physical fastener, including complete stack semantics."""

    physical_fastener_id: str
    product_or_design_id: str
    fastener_type: Literal["machine_bolt", "wood_screw", "panel_screw", "hold_bolt"]
    hardware_scope: HardwareScope
    thread_substrate_during_operation: ThreadSubstrate
    wood_engaging_component_remains_installed: bool
    nominal_diameter_mm: float
    nominal_thread: str
    strength_source: str | None
    head_type_and_dimensions: str
    length_mm: float
    length_reference: str
    ordered_stack: tuple[StackComponent, ...]
    smooth_body_mm: tuple[float, float] | None
    thread_runout_mm: tuple[float, float] | None
    engagement_bounds_mm: tuple[float, float] | None
    holes: tuple[HoleDefinition, ...]
    bearing_elements: tuple[str, ...]
    tool_envelope: str
    insertion_vector: tuple[float, float, float]
    retained_on_move: bool
    legacy_mapping: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.physical_fastener_id or not self.product_or_design_id:
            raise ConnectionRecordError("fastener identity is required")
        if self.fastener_type not in ("machine_bolt", "wood_screw", "panel_screw", "hold_bolt"):
            raise ConnectionRecordError("invalid fastener type")
        if self.hardware_scope not in ("structural", "panel", "hold", "service"):
            raise ConnectionRecordError("invalid hardware scope")
        if self.thread_substrate_during_operation not in ("metal", "wood", "none"):
            raise ConnectionRecordError("invalid thread substrate")
        _positive(self.nominal_diameter_mm, "fastener diameter")
        _positive(self.length_mm, "fastener length")
        if len(self.ordered_stack) < 2:
            raise ConnectionRecordError("fastener stack needs at least two components")
        orders = [component.order for component in self.ordered_stack]
        if orders != list(range(len(orders))):
            raise ConnectionRecordError("stack components must have contiguous order")
        for label, region in (
            ("thread engagement", self.engagement_bounds_mm),
            ("smooth-body", self.smooth_body_mm),
            ("thread runout", self.thread_runout_mm),
        ):
            if region is not None and (region[0] < 0 or region[1] < region[0] or region[1] > self.length_mm):
                raise ConnectionRecordError(f"invalid {label} bounds")
        if self.hardware_scope == "structural" and self.thread_substrate_during_operation == "wood":
            raise ConnectionRecordError("structural move hardware cannot silently use wood threads")
        if self.hardware_scope == "panel" and self.thread_substrate_during_operation not in ("wood", "metal"):
            raise ConnectionRecordError("panel fastener must declare its thread substrate")


def screen_machine_bolt_stack(
    fastener: FastenerRecord, *, closed_nut_depth_mm: float | None = None,
    minimum_projection_mm: float = 0.0,
) -> str:
    """Check declared nominal grip, shoulder, full thread, and nut fit.

    Prototype or missing delivered dimensions remain unresolved. This checks
    assembly geometry only, never bolt or joint resistance.
    """
    if fastener.fastener_type != "machine_bolt":
        raise ConnectionRecordError("machine bolt stack screen requires a machine bolt")
    if closed_nut_depth_mm is not None and closed_nut_depth_mm <= 0:
        raise ConnectionRecordError("closed nut depth must be positive")
    if minimum_projection_mm < 0:
        raise ConnectionRecordError("minimum projection cannot be negative")
    stack = fastener.ordered_stack
    if stack[0].role != "head" or stack[-1].role != "nut":
        return "fail_missing_head_or_nut_bearing"
    if (
        "prototype" in fastener.length_reference
        or any(part.thickness_mm is None for part in stack)
        or fastener.smooth_body_mm is None
        or fastener.thread_runout_mm is None
        or fastener.engagement_bounds_mm is None
    ):
        return "unresolved_delivered_stack_geometry"
    grip = sum(part.thickness_mm for part in stack[1:-1] if part.thickness_mm is not None)
    nut_height = stack[-1].thickness_mm
    assert nut_height is not None
    if fastener.smooth_body_mm[1] > grip or fastener.thread_runout_mm[1] > grip:
        return "fail_nut_on_shoulder_or_runout"
    full_start, full_end = fastener.engagement_bounds_mm
    if full_start > grip or full_end < grip + nut_height:
        return "fail_incomplete_full_thread_engagement"
    if fastener.length_mm < grip + nut_height + minimum_projection_mm:
        return "fail_insufficient_bolt_projection"
    if closed_nut_depth_mm is not None and fastener.length_mm - grip > closed_nut_depth_mm:
        return "fail_closed_nut_bottoming"
    return "nominal_geometry_pass_only"


@dataclass(frozen=True)
class AssemblyInterfaceRecord:
    """Removal and retention behavior for one physical joint interface."""

    assembly_interface_id: str
    separation_members: tuple[str, ...]
    retained_fasteners: tuple[str, ...]
    removed_fasteners: tuple[str, ...]
    tool_access: str
    withdrawal_path: str
    temporary_support: str

    def __post_init__(self) -> None:
        if not self.assembly_interface_id or len(self.separation_members) < 2:
            raise ConnectionRecordError("assembly interface needs an id and two members")
        overlap = set(self.retained_fasteners) & set(self.removed_fasteners)
        if overlap:
            raise ConnectionRecordError(f"fasteners cannot be retained and removed: {sorted(overlap)}")


@dataclass(frozen=True)
class JointRecord:
    """One structural or retained joint with complete physical references."""

    joint_id: str
    joint_family: str
    legacy_station_or_axis_ids: tuple[str, ...]
    connected_members: tuple[str, ...]
    local_basis: LocalBasis
    contact_surfaces: tuple[str, ...]
    fastener_ids: tuple[str, ...]
    receiver_ids: tuple[str, ...]
    simultaneous_case_wrenches: tuple[str, ...]
    capacity_basis_and_edition: str | None
    stiffness_and_clearance_basis: str
    required_actions_and_unresolved_actions: tuple[str, ...]
    assembly_interface_id: str
    assessment_status: AssessmentStatus

    def __post_init__(self) -> None:
        if not self.joint_id or not self.joint_family or len(self.connected_members) < 2:
            raise ConnectionRecordError("joint identity and two connected members are required")
        if not self.fastener_ids:
            raise ConnectionRecordError("joint must identify at least one physical fastener")


def validate_records(
    joints: tuple[JointRecord, ...],
    fasteners: tuple[FastenerRecord, ...],
    interfaces: tuple[AssemblyInterfaceRecord, ...],
) -> None:
    """Validate cross-record identity, stack, and move-scope invariants."""
    joint_ids = [joint.joint_id for joint in joints]
    fastener_ids = [fastener.physical_fastener_id for fastener in fasteners]
    interface_ids = [interface.assembly_interface_id for interface in interfaces]
    if len(joint_ids) != len(set(joint_ids)):
        raise ConnectionRecordError("duplicate joint id")
    if len(fastener_ids) != len(set(fastener_ids)):
        raise ConnectionRecordError("duplicate physical fastener id")
    if len(interface_ids) != len(set(interface_ids)):
        raise ConnectionRecordError("duplicate assembly interface id")
    known_fasteners, known_interfaces = set(fastener_ids), set(interface_ids)
    for joint in joints:
        if not set(joint.fastener_ids) <= known_fasteners:
            raise ConnectionRecordError(f"joint {joint.joint_id} references unknown fastener")
        if joint.assembly_interface_id not in known_interfaces:
            raise ConnectionRecordError(f"joint {joint.joint_id} references unknown interface")
    for interface in interfaces:
        if not set(interface.retained_fasteners + interface.removed_fasteners) <= known_fasteners:
            raise ConnectionRecordError(f"interface {interface.assembly_interface_id} references unknown fastener")


def ab90_prototype_fastener(fastener_id: str = "ab90_proto_m10_1") -> FastenerRecord:
    """Return the unqualified M10-class stack used by AB90 geometry prototypes."""
    return FastenerRecord(
        physical_fastener_id=fastener_id,
        product_or_design_id="AB90-prototype-M10-through-bolt",
        fastener_type="machine_bolt",
        hardware_scope="structural",
        thread_substrate_during_operation="metal",
        wood_engaging_component_remains_installed=False,
        nominal_diameter_mm=10.0,
        nominal_thread="M10; exact grade unresolved",
        strength_source=None,
        head_type_and_dimensions="hex head; dimensions unresolved",
        length_mm=100.0,
        length_reference="prototype nominal only; not a purchase length",
        ordered_stack=(
            StackComponent(0, "bolt_head", "head", 8.0, "metal", True),
            StackComponent(1, "washer_a", "washer", 2.0, "metal", True),
            StackComponent(2, "ab90_flange_a", "plate", 2.5, "metal", True),
            StackComponent(3, "timber_receiver", "receiver", 38.1, "wood", False),
            StackComponent(4, "ab90_flange_b", "plate", 2.5, "metal", True),
            StackComponent(5, "washer_b", "washer", 2.0, "metal", True),
            StackComponent(6, "nut", "nut", 8.0, "metal", True),
        ),
        smooth_body_mm=None,
        thread_runout_mm=None,
        engagement_bounds_mm=None,
        holes=(HoleDefinition("ab90_flange_a", 11.0, "factory", (1.0, 0.0, 0.0)),
               HoleDefinition("ab90_flange_b", 11.0, "factory", (1.0, 0.0, 0.0))),
        bearing_elements=("washer_a", "ab90_flange_a", "ab90_flange_b", "washer_b"),
        tool_envelope="hex tool access unresolved at each mirrored station",
        insertion_vector=(1.0, 0.0, 0.0),
        retained_on_move=True,
        legacy_mapping=(),
    )


def a66_prototype_fastener(
    fastener_id: str = "a66_proto_3_8_1", flange: Literal["a", "b"] = "a"
) -> FastenerRecord:
    """Return one A66 flange-to-timber bolt with unresolved bore geometry."""
    if flange not in ("a", "b"):
        raise ValueError("A66 flange must be a or b")
    flange_id = f"a66_flange_{flange}"
    return FastenerRecord(
        physical_fastener_id=fastener_id,
        product_or_design_id="Simpson-A66-prototype-3/8-through-bolt",
        fastener_type="machine_bolt",
        hardware_scope="structural",
        thread_substrate_during_operation="metal",
        wood_engaging_component_remains_installed=False,
        nominal_diameter_mm=9.525,
        nominal_thread="3/8-16; structural grade unresolved",
        strength_source="A66 catalog bolt installation; joint resistance unresolved",
        head_type_and_dimensions="hex head; delivered bolt dimensions unresolved",
        length_mm=90.0,
        length_reference="prototype nominal only; not a purchase length",
        ordered_stack=(
            StackComponent(0, "bolt_head", "head", 8.0, "metal", True),
            StackComponent(1, "washer_a", "washer", 3.0, "metal", True),
            StackComponent(2, flange_id, "plate", 2.5, "metal", True),
            StackComponent(3, "timber_receiver", "receiver", None, "wood", False),
            StackComponent(4, "washer_b", "washer", 3.0, "metal", True),
            StackComponent(5, "nut", "nut", 8.0, "metal", True),
        ),
        smooth_body_mm=None,
        thread_runout_mm=None,
        engagement_bounds_mm=None,
        holes=(),
        bearing_elements=("washer_a", flange_id, "washer_b"),
        tool_envelope="A66 factory hole diameter, washer size, and access envelope unresolved",
        insertion_vector=(1.0, 0.0, 0.0),
        retained_on_move=True,
        legacy_mapping=(),
    )
