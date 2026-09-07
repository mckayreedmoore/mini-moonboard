"""Product decisions only: no CAD, installation approval or resistance credit.

Sources/limits: docs/selected-bolt-hardware.md and selected-wood-fasteners.md.
Nominal dimensions, published maxima and project allowances stay distinct.
"""
from dataclasses import dataclass
from math import isclose
from types import MappingProxyType

BOLT_SOURCE = "https://www.fastenersplus.com/cdn/shop/files/CQ-Hex-Head-Bolts-Spec-Sheet.pdf?v=17509241941931126534"
GRK_SOURCE = "https://www.grkfasteners.com/getattachment/9a082069-c76f-4f86-9d32-76965836742c/GRK-R4-Customer-Drawing-%281%29.pdf?ext=.pdf&lang=en-US"
SIMPSON_SOURCE = "https://ssttoolbox.widen.net/content/07il60awb7/pdf/C-F-2025.pdf"


@dataclass(frozen=True)
class BoltSpec:
    product: str
    length_mm: float
    grip_mm: float
    length_under_tolerance_mm: float
    source_url: str = BOLT_SOURCE
    diameter_nominal_mm: float = 9.525
    body_diameter_max_mm: float = 9.8552
    head_across_flats_max_mm: float = 14.2748
    head_across_corners_max_mm: float = 16.51
    head_height_max_mm: float = 6.8072
    nut_height_max_mm: float = 8.5598
    nut_across_flats_max_mm: float = 14.2748
    nut_across_corners_max_mm: float = 16.51
    nut_product: str = "FMW 3/8-16 finished hex nut zinc; ASTM A563 Grade A"
    nut_source_url: str = "https://www.fmwfasteners.com/products/3-8-16-grade-2-finished-hex-nut-zinc-plated"
    washer_product: str = "CDE 599192 3/8 SAE carbon-steel zinc washer; not F844-certified"
    washer_source_url: str = "https://cdefasteners.com/sites/default/files/product-specs/washerssae.pdf"
    washer_count: int = 2
    washer_od_nominal_mm: float = 20.6375
    washer_od_max_mm: float = 21.0058
    washer_id_min_mm: float = 10.1854
    washer_id_max_mm: float = 10.6426
    washer_thickness_nominal_mm: float = 1.651  # Project CAD assumption, not a published nominal.
    washer_thickness_min_mm: float = 1.2954
    washer_thickness_max_mm: float = 2.032
    thread_length_reference_mm: float = 25.4
    pitch_mm: float = 1.5875
    drive: str = "9/16 in hex; actual socket outside diameter unresolved"
    qualified_for_design: bool = False


@dataclass(frozen=True)
class ScrewSpec:
    product: str
    source_url: str
    length_nominal_mm: float
    length_screen_min_mm: float
    length_screen_max_mm: float
    thread_length_nominal_mm: float
    thread_length_screen_min_mm: float
    thread_length_screen_max_mm: float
    major_diameter_nominal_mm: float
    shank_diameter_nominal_mm: float
    root_diameter_nominal_mm: float | None
    head_diameter_nominal_mm: float  # Integrated washer OD for SD/SDS.
    head_rim_height_nominal_mm: float | None
    head_allowance_diameter_mm: float
    head_allowance_height_mm: float
    tool_allowance_diameter_mm: float
    tool_allowance_length_mm: float
    seating: str
    length_datum: str
    drive: str
    limits: str
    qualified_for_design: bool = False


R4_LIMITS = ("Nominal customer drawing only; full tapered seat, reamer and tolerances unresolved. "
             "Head/tool dimensions are project allowances, not manufacturer maxima. "
             "Screen ranges span documented generations, not manufacturing tolerances; no capacity transfer.")
R4_2 = ScrewSpec("GRK R4 Climatek #9 x 2 in; 103099", GRK_SOURCE,
    50.8, 50.8, 50.8, 33.02, 31.75, 33.02, 4.3942, 3.2512, 2.8448,
    8.3566, 1.5494, 10., 5., 12., 50., "flush", "head_top", "T25", R4_LIMITS)
R4_2_5 = ScrewSpec("GRK R4 Climatek #9 x 2.5 in; 103101", GRK_SOURCE,
    63.5, 60.325, 63.5, 39.878, 39.878, 41.275, 4.3942, 3.2512, 2.8448,
    8.3566, 1.5494, 10., 5., 12., 50., "flush", "head_top", "T25", R4_LIMITS)
R4_3_5 = ScrewSpec("GRK R4 Climatek #10 x 3.5 in; 02139", GRK_SOURCE,
    88.9, 88.9, 88.9, 50.8, 50.8, 60.325, 4.9022, 3.6068, 3.1496,
    9.3472, 1.7526, 10., 5., 12., 50., "flush", "head_top", "T25", R4_LIMITS)
SD9112 = ScrewSpec("Simpson SD9112; SD9112R100", SIMPSON_SOURCE,
    38.1, 38.1, 38.1, 28.575, 28.575, 28.575, 4.5, 3.302, None,
    9.398, None, 10.5, 6., 14., 50., "flat", "underhead", "1/4 in hex",
    "4.5 mm thread OD is rounded catalog data. US A21 combination selected; UK CAD hole/bend proxy unverified. "
    "Head/tool allowances are project assumptions; no countersink or connector alteration.")
SDS25112 = ScrewSpec("Simpson SDS25112; SDS25112-R25", SIMPSON_SOURCE,
    38.1, 38.1, 38.1, 25.4, 25.4, 25.4, 6.35, 5.969, None,
    12.7, None, 14., 7., 18., 50., "flat", "underhead", "3/8 in hex",
    "Custom 6 mm steel detail, not a rated connector assembly; proposed steel bore 7 mm. "
    "No added washer. Head/tool allowances are project assumptions; point not effective withdrawal length.")


def _inventory():
    result = {}

    def add(name, spec):
        if name in result:
            raise ValueError("Duplicate selected hardware name")
        result[name] = spec

    def bolt(name, grip, length, tolerance):
        add(name, BoltSpec("Conquest 3/8-16 A307 Grade A plain standard hex bolt", length, grip, tolerance))

    for i in range(1, 65):
        add(f"panel_{i}", R4_2)
    for side in ("left", "right"):
        for i in range(1, 4):
            bolt(f"leg_stitch_{side}_{i}", 38.1, 57.15, 1.016)
        for i in range(1, 5):
            bolt(f"analysis_leg_wall_bolt_{side}_{i}", 76.2, 95.25, 1.524)
            add(f"cheek_splice_{side}_{i}", R4_2_5)
        for i in range(1, 7):
            add(f"analysis_edge_screw_{side}_{i}", R4_3_5)
        for edge in ("bottom", "top"):
            for i in range(4):
                add(f"kicker_{side}_{edge}_{i}", R4_2)
        for label in ("top", "cross_1", "cross_2", "cross_3"):
            for leaf in ("wall", "beam"):
                for i in (1, 2):
                    cross_beam = label != "top" and leaf == "beam"
                    bolt(f"angle_{side}_{label}_{leaf}_{i}",
                         94.9 if cross_beam else 44.1, 114.3 if cross_beam else 63.5,
                         2.54 if cross_beam else 1.016)
        for label in ("main", "kicker", "seam", "top", "kicker_bottom"):
            for i in (1, 2):
                thick = label in ("main", "kicker")
                bolt(f"transition_{label}_{side}_bolt_{i}",
                     82.2 if thick else 44.1, 101.6 if thick else 63.5, 1.524 if thick else 1.016)
                add(f"transition_{label}_{side}_screw_{i}", SDS25112)
        for row in (1, 2, 3):
            for label in ("seam", "mid"):
                rib = f"rib_{row}_{label}_{side}"
                add(f"{rib}_front", R4_3_5)
                for i in (1, 2):
                    bolt(f"angle_{rib}_rib_{i}", 69.5, 88.9, 1.524)
                    bolt(f"angle_{rib}_beam_{i}", 44.1, 63.5, 1.016)
        for band in ("lower", "upper"):
            for end in ("bottom", "top"):
                for leaf in ("batten", "rail"):
                    for i in (1, 2):
                        add(f"clip_{band}_{side}_{end}_{leaf}_{i}", SD9112)
    return MappingProxyType(result)


SPECS_BY_NAME = _inventory()


def spec_for(connection) -> BoltSpec | ScrewSpec:
    """Map only the frozen transition inventory; no prefix-based fallbacks."""
    try:
        spec = SPECS_BY_NAME[connection.name]
    except KeyError as error:
        raise ValueError(f"Unselected connection name: {connection.name}") from error
    expected_kind = "bolt" if isinstance(spec, BoltSpec) else "screw"
    expected_grip = spec.grip_mm if isinstance(spec, BoltSpec) else 0.
    if connection.kind != expected_kind or not isclose(connection.grip, expected_grip, rel_tol=0., abs_tol=1e-8):
        raise ValueError(f"Connection kind/grip differs from selected inventory: {connection.name}")
    return spec
