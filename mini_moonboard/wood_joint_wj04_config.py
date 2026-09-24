"""Canonical, CAD-free WJ-04 ordinary joint trial configuration.

Geometry and hardware here are development inputs. Catalog candidates are for
modeling only; CAD occupancy values remain separate and are not purchase,
drilling, capacity, or fabrication approvals.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Literal

Vector3 = tuple[float, float, float]
AxisName = Literal["X", "T", "N"]


@dataclass(frozen=True)
class FrameBasis:
    """Right-handed station basis; coordinates are in millimetres."""

    x_global: Vector3
    t_global: Vector3
    n_global: Vector3
    origin_global_mm: Vector3 = (0.0, 0.0, 0.0)

    def to_global(self, point_basis_mm: Vector3) -> Vector3:
        return tuple(
            round(
                self.origin_global_mm[i]
                + self.x_global[i] * point_basis_mm[0]
                + self.t_global[i] * point_basis_mm[1]
                + self.n_global[i] * point_basis_mm[2],
                9,
            )
            for i in range(3)
        )  # type: ignore[return-value]

    def vector_to_global(self, vector_basis: Vector3) -> Vector3:
        return tuple(
            round(
                self.x_global[i] * vector_basis[0]
                + self.t_global[i] * vector_basis[1]
                + self.n_global[i] * vector_basis[2],
                9,
            )
            for i in range(3)
        )  # type: ignore[return-value]


@dataclass(frozen=True)
class SourceBounds:
    rail_x_butt_x_mm: float
    rail_t_min_mm: float
    rail_t_max_mm: float
    rail_n_min_mm: float
    rail_n_max_mm: float


@dataclass(frozen=True)
class JointMember:
    member_id: str
    role: Literal["principal", "rail", "cleat"]
    grain_axis: AxisName
    source_part_id: str | None
    source_face_ids: tuple[str, ...]
    size_x_t_n_mm: Vector3 | None = None
    origin_x_t_n_mm: Vector3 | None = None
    stock_note: str | None = None
    stock_source_urls: tuple[str, ...] = ()


@dataclass(frozen=True)
class LayerConfig:
    """One actual wood member thickness along the bolt axis, in head-to-nut order."""

    member_id: str
    thickness_mm: float


@dataclass(frozen=True)
class CadHardwareEnvelope:
    """Active occupied shape dimensions for collision modeling, not drilling."""

    shaft_diameter_mm: float
    bore_occupancy_diameter_mm: float
    head_diameter_mm: float
    head_height_mm: float
    washer_outer_diameter_mm: float
    washer_inner_diameter_mm: float
    washer_thickness_mm: float
    nut_diameter_mm: float
    nut_height_mm: float
    required_tip_projection_mm: float
    product_bound_head_dimensions: bool = True
    product_bound_nut_outer_dimensions: bool = True
    product_bound_shaft_diameter: bool = False
    washer_maximum_bounds_applied: bool = True
    nut_maximum_thickness_applied: bool = True
    published_all_component_tolerances: bool = False
    status: str = (
        "Active collision envelope uses K.L. Jack published 1/4-in head maximums, "
        "B18.2.2 maximum hex-nut bounds, candidate maximum washer dimensions, and "
        "K.L. Jack maximum body diameter. The 7.5 mm bore occupancy is a CAD screen, "
        "not a drill instruction; received-part and assembly tolerances remain open."
    )


@dataclass(frozen=True)
class HexHeadBounds:
    across_flats_range_mm: tuple[float, float]
    across_corners_range_mm: tuple[float, float]
    height_range_mm: tuple[float, float]
    standard: str
    source_urls: tuple[str, ...]


@dataclass(frozen=True)
class BoltCandidate:
    """Source-backed bolt envelope for candidate modeling and later receiving."""

    candidate_id: str
    manufacturer: str
    sku: str
    thread: str
    grade: str
    nominal_length_mm: float
    length_minus_tolerance_mm: float
    minimum_smooth_body_mm: float
    maximum_full_thread_start_mm: float
    body_diameter_range_mm: tuple[float, float]
    dimensional_standard: str
    source_urls: tuple[str, ...]
    full_form_thread_end_guaranteed: bool = False
    receiving_measurement_required: bool = True
    status: str = "catalog candidate for modeling only; no purchase or strength approval"


@dataclass(frozen=True)
class WasherCandidate:
    candidate_id: str
    manufacturer: str
    description: str
    standard: str
    inner_diameter_range_mm: tuple[float, float]
    outer_diameter_range_mm: tuple[float, float]
    thickness_range_mm: tuple[float, float]
    material: str
    source_urls: tuple[str, ...]
    published_tolerance_bounds: bool = True
    status: str = "catalog dimensional candidate; compatibility and bearing remain open"


@dataclass(frozen=True)
class NutCandidate:
    candidate_id: str
    manufacturer: str
    sku: str
    thread: str
    grade: str
    standard: str
    thickness_range_mm: tuple[float, float]
    across_flats_range_mm: tuple[float, float]
    across_corners_max_mm: float
    source_urls: tuple[str, ...]
    status: str = "catalog candidate for modeling only; engagement needs receiving check"


@dataclass(frozen=True)
class ToolCandidate:
    candidate_id: str
    manufacturer: str
    description: str
    wrench_size_in: str
    head_width_mm: float
    head_thickness_mm: float
    overall_length_mm: float
    head_offsets_degrees: tuple[float, float]
    source_urls: tuple[str, ...]
    published_dimension_tolerances: bool = False
    handle_sweep_verified: bool = False
    status: str = "catalog geometry only; tool access and working sweep unverified"


@dataclass(frozen=True)
class FastenerCandidates:
    bolts: tuple[BoltCandidate, ...]
    head: HexHeadBounds
    nut: NutCandidate
    washer: WasherCandidate
    washers_per_stack: int
    tools: tuple[ToolCandidate, ...]

    def bolt_by_id(self, candidate_id: str) -> BoltCandidate:
        for bolt in self.bolts:
            if bolt.candidate_id == candidate_id:
                return bolt
        raise KeyError(candidate_id)


@dataclass(frozen=True)
class BoltStackConfig:
    stack_id: str
    interface_id: Literal["rail_to_cleat", "principal_to_cleat"]
    axis_point_basis_mm: Vector3
    axis_direction_basis: Vector3
    layers: tuple[LayerConfig, ...]
    cad_envelope: CadHardwareEnvelope
    hardware_candidate: BoltCandidate

    @property
    def grip_mm(self) -> float:
        return round(sum(layer.thickness_mm for layer in self.layers), 6)

@dataclass(frozen=True)
class WJ04TrialConfig:
    schema: str
    trial_id: str
    development_candidate_id: str
    preserved_selected_candidate_id: str
    station_id: str
    source_variant: str
    source_inventory_path: str
    source_inventory_sha256: str
    source_commit: str
    coordinate_convention: str
    frame: FrameBasis
    source_bounds: SourceBounds
    cleat_front_offset_n_mm: float
    members: tuple[JointMember, ...]
    stacks: tuple[BoltStackConfig, ...]
    fasteners: FastenerCandidates
    fixed_panel_kicker_screw_axis_count: int
    screw_axis_policy: str
    diagnostic_tool_widths_mm: tuple[float, ...]
    status: str
    stock_grade_verified: bool
    purchase_approved: bool
    drilling_released: bool
    fabrication_released: bool
    structural_released: bool

    @property
    def cleat(self) -> JointMember:
        return next(member for member in self.members if member.member_id == "wj04_cleat")

    def stack_by_id(self, stack_id: str) -> BoltStackConfig:
        for stack in self.stacks:
            if stack.stack_id == stack_id:
                return stack
        raise KeyError(stack_id)

    def axis_point_global(self, stack_id: str) -> Vector3:
        return self.frame.to_global(self.stack_by_id(stack_id).axis_point_basis_mm)

    def axis_direction_global(self, stack_id: str) -> Vector3:
        return self.frame.vector_to_global(self.stack_by_id(stack_id).axis_direction_basis)

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serializable copy, including computed grips and global axes."""
        payload = asdict(self)
        for stack, stack_payload in zip(self.stacks, payload["stacks"], strict=True):
            stack_payload["grip_mm"] = stack.grip_mm
            stack_payload["axis_point_global_mm"] = self.frame.to_global(stack.axis_point_basis_mm)
            stack_payload["axis_direction_global"] = self.frame.vector_to_global(stack.axis_direction_basis)
            stack_payload["hardware_candidate_id"] = stack.hardware_candidate.candidate_id
            del stack_payload["hardware_candidate"]
        return payload

    @property
    def canonical_sha256(self) -> str:
        encoded = json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()


_T = (0.0, math.cos(math.radians(50.0)), math.sin(math.radians(50.0)))
_N = (0.0, -math.sin(math.radians(50.0)), math.cos(math.radians(50.0)))

_RAIL_BOLT = BoltCandidate(
    candidate_id="kl_jack_25c375hcs5z",
    manufacturer="K.L. Jack",
    sku="25C375HCS5Z",
    thread="1/4-20 UNC",
    grade="Grade 5",
    nominal_length_mm=95.25,
    length_minus_tolerance_mm=1.524,
    minimum_smooth_body_mm=69.85,
    maximum_full_thread_start_mm=76.2,
    body_diameter_range_mm=(6.223, 6.35),
    dimensional_standard="ASME B18.2.1",
    source_urls=(
        "https://www.kljack.com/products/25c375hcs5z/",
        "https://www.nickel-systems.com/wp-content/uploads/2025/01/Hex-Head-Cap-Screws-Partially-Threaded-Minimum-Body-Maximum-Grip-Gaging-Lengths-1.pdf",
        "https://www.nickel-systems.com/products/bolts-screws/hex-head-cap/",
    ),
)

_PRINCIPAL_BOLT = BoltCandidate(
    candidate_id="kl_jack_25c600hcs5z",
    manufacturer="K.L. Jack",
    sku="25C600HCS5Z",
    thread="1/4-20 UNC",
    grade="Grade 5",
    nominal_length_mm=152.4,
    length_minus_tolerance_mm=2.54,
    minimum_smooth_body_mm=127.0,
    maximum_full_thread_start_mm=133.35,
    body_diameter_range_mm=(6.223, 6.35),
    dimensional_standard="ASME B18.2.1",
    source_urls=(
        "https://www.kljack.com/products/25c600hcs5z/",
        "https://www.nickel-systems.com/wp-content/uploads/2025/01/Hex-Head-Cap-Screws-Partially-Threaded-Minimum-Body-Maximum-Grip-Gaging-Lengths-1.pdf",
        "https://www.nickel-systems.com/products/bolts-screws/hex-head-cap/",
    ),
)

_NUT = NutCandidate(
    candidate_id="kl_jack_25cnfh5z",
    manufacturer="K.L. Jack",
    sku="25CNFH5Z",
    thread="1/4-20 UNC",
    grade="Grade 5",
    standard="SAE J995; ASME B18.2.2",
    thickness_range_mm=(5.3848, 5.7404),
    across_flats_range_mm=(10.8712, 11.1252),
    across_corners_max_mm=12.827,
    source_urls=(
        "https://www.kljack.com/products/25cnfh5z/",
        "https://www.nickel-systems.com/products/nuts/finished-hex/",
    ),
)

_WASHER = WasherCandidate(
    candidate_id="fastenal_type_a_wide_uss_plain_steel",
    manufacturer="Fastenal",
    description="1/4-in Type A Wide plain steel washer",
    standard="ASME B18.21.1",
    inner_diameter_range_mm=(7.7978, 8.3058),
    outer_diameter_range_mm=(18.4658, 19.0246),
    thickness_range_mm=(1.2954, 2.032),
    material="plain steel",
    source_urls=("https://www.fastenal.com/content/product_specifications/FW.LC.USS.A.P.00.pdf",),
)

_FASTENERS = FastenerCandidates(
    bolts=(_RAIL_BOLT, _PRINCIPAL_BOLT),
    head=HexHeadBounds(
        across_flats_range_mm=(10.8712, 11.1252),
        across_corners_range_mm=(12.3952, 12.827),
        height_range_mm=(3.81, 4.1402),
        standard="ASME B18.2.1; K.L. Jack 2009/10 technical data, p.159",
        source_urls=(
            "https://www.kljack.com/docs/default-source/technical-information/kl_jack_fasteners-technical_data_and_charts.pdf",
            "https://www.nickel-systems.com/products/bolts-screws/hex-head-cap/",
        ),
    ),
    nut=_NUT,
    washer=_WASHER,
    washers_per_stack=2,
    tools=(
        ToolCandidate(
            candidate_id="facom_34_7_16",
            manufacturer="FACOM",
            description="midget 15° open-end wrench",
            wrench_size_in="7/16",
            head_width_mm=22.0,
            head_thickness_mm=3.0,
            overall_length_mm=100.0,
            head_offsets_degrees=(15.0, 75.0),
            source_urls=("https://www.facom.fr/products/34-cles-a-fourches-micromecanique-tetes-inclinees-en-pouces",),
        ),
    ),
)

_ACTIVE_CAD_ENVELOPE = CadHardwareEnvelope(
    shaft_diameter_mm=max(bolt.body_diameter_range_mm[1] for bolt in _FASTENERS.bolts),
    bore_occupancy_diameter_mm=7.5,
    head_diameter_mm=_FASTENERS.head.across_corners_range_mm[1],
    head_height_mm=_FASTENERS.head.height_range_mm[1],
    washer_outer_diameter_mm=_FASTENERS.washer.outer_diameter_range_mm[1],
    washer_inner_diameter_mm=_FASTENERS.washer.inner_diameter_range_mm[0],
    washer_thickness_mm=_FASTENERS.washer.thickness_range_mm[1],
    nut_diameter_mm=_FASTENERS.nut.across_corners_max_mm,
    nut_height_mm=_FASTENERS.nut.thickness_range_mm[1],
    required_tip_projection_mm=2.54,
    product_bound_shaft_diameter=True,
)

WJ04_TRIAL = WJ04TrialConfig(
    schema="wood_joint_wj04_trial/v1",
    trial_id="narrow_x95p25_ordinary_bolt_candidate",
    development_candidate_id="compact-floor-flush-wood-joints-development",
    preserved_selected_candidate_id="compact-floor-flush-development",
    station_id="clip_horizontal_lower_right_1",
    source_variant="kerf-right",
    source_inventory_path="docs/wood-joints-mvp/source-inventory.json",
    source_inventory_sha256="07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78",
    source_commit="df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb",
    coordinate_convention=(
        "X/T/N basis coordinates are absolute dot-product projections from global XYZ origin "
        "(0,0,0); frame basis stores global unit directions and has no station translation. "
        "Use source face/datum bounds for placement; to_global reconstructs XYZ from the origin."
    ),
    frame=FrameBasis(
        x_global=(1.0, 0.0, 0.0),
        t_global=_T,
        n_global=_N,
        origin_global_mm=(0.0, 0.0, 0.0),
    ),
    source_bounds=SourceBounds(
        rail_x_butt_x_mm=89.05,
        rail_t_min_mm=1315.774134,
        rail_t_max_mm=1353.874134,
        rail_n_min_mm=209.840968,
        rail_n_max_mm=349.540968,
    ),
    cleat_front_offset_n_mm=20.0,
    members=(
        JointMember(
            member_id="base_principal_center_right",
            role="principal",
            grain_axis="T",
            source_part_id="base_principal_center_right",
            source_face_ids=("planar_face_07", "planar_face_04"),
        ),
        JointMember(
            member_id="base_rail_service_lower_right",
            role="rail",
            grain_axis="X",
            source_part_id="base_rail_service_lower_right",
            source_face_ids=("planar_face_04", "planar_face_02"),
        ),
        JointMember(
            member_id="wj04_cleat",
            role="cleat",
            grain_axis="N",
            source_part_id=None,
            source_face_ids=(),
            size_x_t_n_mm=(95.25, 38.1, 119.7),
            origin_x_t_n_mm=(89.05, 1353.874134, 229.840968),
            stock_note=(
                "Dimensional lead is nominal 2x6 #2 Prime Douglas Fir KD lumber "
                "(listed actual 38.1 x 139.7 mm section): place 38.1 mm thickness "
                "on T, rip X from 139.7 to 95.25 mm, then crosscut along-grain N "
                "to 119.7 mm. Listing is not a received-board inspection or cut "
                "release. Verify delivered grade mark/species group, treatment, "
                "moisture, section, straightness, defects in bolt zone, kerf, and yield."
            ),
            stock_source_urls=(
                "https://www.lowes.com/pd/Top-Choice-2-in-x-6-in-x-8-ft-Douglas-Fir-Lumber-Common-1-5-in-x-5-5-in-x-8-ft-Actual/1000571215",
            ),
        ),
    ),
    stacks=(
        BoltStackConfig(
            stack_id="rail_1",
            interface_id="rail_to_cleat",
            axis_point_basis_mm=(127.15, 1315.774134, 265.0),
            axis_direction_basis=(0.0, 1.0, 0.0),
            layers=(
                LayerConfig("base_rail_service_lower_right", 38.1),
                LayerConfig("wj04_cleat", 38.1),
            ),
            cad_envelope=_ACTIVE_CAD_ENVELOPE,
            hardware_candidate=_RAIL_BOLT,
        ),
        BoltStackConfig(
            stack_id="rail_2",
            interface_id="rail_to_cleat",
            axis_point_basis_mm=(152.55, 1315.774134, 265.0),
            axis_direction_basis=(0.0, 1.0, 0.0),
            layers=(
                LayerConfig("base_rail_service_lower_right", 38.1),
                LayerConfig("wj04_cleat", 38.1),
            ),
            cad_envelope=_ACTIVE_CAD_ENVELOPE,
            hardware_candidate=_RAIL_BOLT,
        ),
        BoltStackConfig(
            stack_id="upright_1",
            interface_id="principal_to_cleat",
            axis_point_basis_mm=(184.3, 1372.924134, 293.0),
            axis_direction_basis=(-1.0, 0.0, 0.0),
            layers=(
                LayerConfig("wj04_cleat", 95.25),
                LayerConfig("base_principal_center_right", 38.1),
            ),
            cad_envelope=_ACTIVE_CAD_ENVELOPE,
            hardware_candidate=_PRINCIPAL_BOLT,
        ),
        BoltStackConfig(
            stack_id="upright_2",
            interface_id="principal_to_cleat",
            axis_point_basis_mm=(184.3, 1372.924134, 320.0),
            axis_direction_basis=(-1.0, 0.0, 0.0),
            layers=(
                LayerConfig("wj04_cleat", 95.25),
                LayerConfig("base_principal_center_right", 38.1),
            ),
            cad_envelope=_ACTIVE_CAD_ENVELOPE,
            hardware_candidate=_PRINCIPAL_BOLT,
        ),
    ),
    fasteners=_FASTENERS,
    fixed_panel_kicker_screw_axis_count=66,
    screw_axis_policy="Use source-bound kerf-right axes unchanged; this config moves none.",
    diagnostic_tool_widths_mm=(40.0, 50.0),
    status="diagnostic_candidate_model_only",
    stock_grade_verified=False,
    purchase_approved=False,
    drilling_released=False,
    fabrication_released=False,
    structural_released=False,
)


def validate_wj04_trial(config: WJ04TrialConfig = WJ04_TRIAL) -> None:
    """Fail closed if trial geometry and its ordered actual wood layers disagree."""
    if (
        config.trial_id != "narrow_x95p25_ordinary_bolt_candidate"
        or config.station_id != "clip_horizontal_lower_right_1"
        or config.source_variant != "kerf-right"
        or config.source_inventory_sha256 != "07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78"
        or config.source_commit != "df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb"
    ):
        raise ValueError("WJ-04 trial identity must remain bound to the pinned source inventory")
    if config.fixed_panel_kicker_screw_axis_count != 66:
        raise ValueError("WJ-04 trial must preserve exactly 66 panel/kicker screw axes")
    if config.preserved_selected_candidate_id != "compact-floor-flush-development":
        raise ValueError("WJ-04 development config must preserve selected candidate authority")
    if config.frame.origin_global_mm != (0.0, 0.0, 0.0):
        raise ValueError("WJ-04 basis coordinates are absolute projections from global XYZ origin")
    if not all((not config.purchase_approved, not config.drilling_released,
                not config.fabrication_released, not config.structural_released)):
        raise ValueError("WJ-04 trial config cannot release purchase, drilling, fabrication, or structure")

    members = {member.member_id: member for member in config.members}
    if len(members) != len(config.members):
        raise ValueError("WJ-04 member IDs must be unique")
    expected_member_bindings = {
        "base_principal_center_right": (
            "principal", "T", "base_principal_center_right", ("planar_face_07", "planar_face_04"),
        ),
        "base_rail_service_lower_right": (
            "rail", "X", "base_rail_service_lower_right", ("planar_face_04", "planar_face_02"),
        ),
        "wj04_cleat": ("cleat", "N", None, ()),
    }
    actual_member_bindings = {
        member.member_id: (
            member.role, member.grain_axis, member.source_part_id, member.source_face_ids,
        )
        for member in config.members
    }
    if actual_member_bindings != expected_member_bindings:
        raise ValueError("WJ-04 member records must remain bound to source faces and grain axes")
    if len(config.stacks) != 4 or len({stack.stack_id for stack in config.stacks}) != 4:
        raise ValueError("WJ-04 trial requires four uniquely named bolt stacks")
    frame_axes = (config.frame.x_global, config.frame.t_global, config.frame.n_global)
    expected_frame_axes = (
        (1.0, 0.0, 0.0),
        (0.0, math.cos(math.radians(50.0)), math.sin(math.radians(50.0))),
        (0.0, -math.sin(math.radians(50.0)), math.cos(math.radians(50.0))),
    )
    if any(
        not math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-12)
        for actual_axis, expected_axis in zip(frame_axes, expected_frame_axes, strict=True)
        for actual, expected in zip(actual_axis, expected_axis, strict=True)
    ):
        raise ValueError("WJ-04 frame axes must match the source-inventory X/T/N basis")
    if any(not math.isclose(sum(value * value for value in axis), 1.0, abs_tol=1e-9) for axis in frame_axes):
        raise ValueError("WJ-04 source frame axes must be unit vectors")
    if any(abs(sum(a * b for a, b in zip(first, second, strict=True))) > 1e-9
           for first, second in ((frame_axes[0], frame_axes[1]),
                                 (frame_axes[0], frame_axes[2]),
                                 (frame_axes[1], frame_axes[2]))):
        raise ValueError("WJ-04 source frame axes must be orthogonal")
    cross_xt = (
        frame_axes[0][1] * frame_axes[1][2] - frame_axes[0][2] * frame_axes[1][1],
        frame_axes[0][2] * frame_axes[1][0] - frame_axes[0][0] * frame_axes[1][2],
        frame_axes[0][0] * frame_axes[1][1] - frame_axes[0][1] * frame_axes[1][0],
    )
    if sum(a * b for a, b in zip(cross_xt, frame_axes[2], strict=True)) < 1.0 - 1e-9:
        raise ValueError("WJ-04 source frame must remain right-handed")

    expected_axes = {
        "rail_1": ((127.15, 1315.774134, 265.0), (0.0, 1.0, 0.0)),
        "rail_2": ((152.55, 1315.774134, 265.0), (0.0, 1.0, 0.0)),
        "upright_1": ((184.3, 1372.924134, 293.0), (-1.0, 0.0, 0.0)),
        "upright_2": ((184.3, 1372.924134, 320.0), (-1.0, 0.0, 0.0)),
    }

    expected_layers = {
        "rail_to_cleat": (
            ("base_rail_service_lower_right", 38.1),
            ("wj04_cleat", 38.1),
        ),
        "principal_to_cleat": (
            ("wj04_cleat", 95.25),
            ("base_principal_center_right", 38.1),
        ),
    }
    for stack in config.stacks:
        if (stack.axis_point_basis_mm, stack.axis_direction_basis) != expected_axes.get(stack.stack_id):
            raise ValueError(f"{stack.stack_id}: bolt axis moved from canonical WJ-04 trial station")
        if stack.interface_id not in expected_layers:
            raise ValueError(f"Unknown WJ-04 interface: {stack.interface_id}")
        if len(stack.layers) != 2:
            raise ValueError(f"{stack.stack_id}: expected two ordered wood layers")
        actual = tuple((layer.member_id, layer.thickness_mm) for layer in stack.layers)
        if actual != expected_layers[stack.interface_id]:
            raise ValueError(f"{stack.stack_id}: ordered actual layer data disagrees with interface")
        if any(layer.member_id not in members for layer in stack.layers):
            raise ValueError(f"{stack.stack_id}: layer references unknown member")
        if any(not math.isfinite(layer.thickness_mm) or layer.thickness_mm <= 0 for layer in stack.layers):
            raise ValueError(f"{stack.stack_id}: layer thicknesses must be positive and finite")
        if not math.isclose(math.sqrt(sum(value * value for value in stack.axis_direction_basis)), 1.0,
                            rel_tol=0.0, abs_tol=1e-9):
            raise ValueError(f"{stack.stack_id}: bolt-axis direction must be a unit vector")
        candidate = stack.hardware_candidate
        known_candidate = config.fasteners.bolt_by_id(candidate.candidate_id)
        if candidate != known_candidate:
            raise ValueError(f"{stack.stack_id}: bolt candidate differs from canonical hardware record")
        expected_candidate_id = (
            _RAIL_BOLT.candidate_id
            if stack.interface_id == "rail_to_cleat"
            else _PRINCIPAL_BOLT.candidate_id
        )
        if candidate.candidate_id != expected_candidate_id:
            raise ValueError(f"{stack.stack_id}: wrong bolt candidate for interface")
        cad = stack.cad_envelope
        if cad != _ACTIVE_CAD_ENVELOPE:
            raise ValueError(f"{stack.stack_id}: active CAD envelope must come from catalog maxima")
        if candidate.nominal_length_mm <= 0:
            raise ValueError(f"{stack.stack_id}: candidate length must stay positive")
        if cad.bore_occupancy_diameter_mm <= cad.shaft_diameter_mm:
            raise ValueError(f"{stack.stack_id}: bore occupancy must exceed shaft occupancy")
    for interface_id in expected_layers:
        if sum(stack.interface_id == interface_id for stack in config.stacks) != 2:
            raise ValueError(f"WJ-04 interface {interface_id} requires two bolt stacks")

    cleat = config.cleat
    bounds = config.source_bounds
    expected_bounds = SourceBounds(89.05, 1315.774134, 1353.874134, 209.840968, 349.540968)
    if bounds != expected_bounds:
        raise ValueError("WJ-04 source face bounds must match the pinned source inventory")
    expected_origin = (
        bounds.rail_x_butt_x_mm,
        bounds.rail_t_max_mm,
        bounds.rail_n_min_mm + config.cleat_front_offset_n_mm,
    )
    expected_size = (
        95.25,
        38.1,
        round(bounds.rail_n_max_mm - expected_origin[2], 6),
    )
    if (
        cleat.size_x_t_n_mm != expected_size
        or cleat.origin_x_t_n_mm != expected_origin
        or cleat.grain_axis != "N"
    ):
        raise ValueError("WJ-04 narrow trial cleat must remain 95.25 x 38.1 x 119.7 mm, grain N")
    if config.cleat_front_offset_n_mm != 20.0:
        raise ValueError("WJ-04 cleat placement must retain the recorded 20 mm front offset")
    if config.fasteners != _FASTENERS:
        raise ValueError("WJ-04 fastener records must match the pinned catalog candidates")
    if config.fasteners.washers_per_stack != 2:
        raise ValueError("WJ-04 ordinary stack uses two washers per bolt")


validate_wj04_trial()
