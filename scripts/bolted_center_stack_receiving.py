"""Pure axial receiving screen for a left-center shared-header angle stack.

Distances are millimetres from the underside of the bolt head toward the nut.
Only supplied, measured or explicitly illustrative dimensions are used. A
CONDITIONAL result is geometry evidence, never part acceptance or drill release.
Thread at a shear plane fails the full-shank assumption; root-diameter design
remains unassessed. Washer count does not select a washer stack.
"""

import math

INVENTORIES = frozenset((
    "left-center shared-header AB205",
    "left-center shared-header BR904",
))
DIMENSIONS = (
    "bolt_underhead_length_mm",
    "plain_shank_end_mm",
    "first_usable_thread_mm",
    "head_washer_mm",
    "top_plate_mm",
    "header_mm",
    "bottom_plate_mm",
    "nut_washer_mm",
    "nut_side_washer_count",
    "nut_mm",
    "required_protrusion_mm",
    "axial_tolerance_mm",
    "shear_allowance_mm",
)


def check_stack(
    *,
    inventory=None,
    bolt_underhead_length_mm=None,
    plain_shank_end_mm=None,
    first_usable_thread_mm=None,
    head_washer_mm=None,
    top_plate_mm=None,
    header_mm=None,
    bottom_plate_mm=None,
    nut_washer_mm=None,
    nut_side_washer_count=None,
    nut_mm=None,
    required_protrusion_mm=None,
    axial_tolerance_mm=None,
    shear_allowance_mm=None,
):
    """Screen two steel/wood shear planes and the nut's usable-thread interval.

    ``axial_tolerance_mm`` is a caller-supplied worst-case allowance at each
    comparison. ``shear_allowance_mm`` is additional plain shank beyond the
    far shear plane. The two allowances are not inferred from catalog sizes.
    """
    values = locals().copy()
    missing = tuple(name for name in ("inventory", *DIMENSIONS) if values[name] is None)
    result = {
        "status": "UNRESOLVED",
        "missing_inputs": missing,
        "inventory_matches": None if inventory is None else inventory in INVENTORIES,
        "shear_planes_mm": None,
        "nut_start_mm": None,
        "nut_end_mm": None,
        "protrusion_mm": None,
        "both_shear_planes_plain": None,
        "nut_on_usable_threads": None,
        "full_nut_engagement_and_protrusion": None,
        "root_diameter_design_unassessed": True,
        "washer_stack_selected": False,
        "joint_accepted": False,
        "drill_release": False,
    }
    if missing:
        return result
    if not isinstance(inventory, str):
        raise TypeError("inventory must be a string")
    if not result["inventory_matches"]:
        result["status"] = "WRONG_INVENTORY"
        return result

    for name in DIMENSIONS:
        value = values[name]
        if name == "nut_side_washer_count":
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError("nut_side_washer_count must be a nonnegative integer")
        elif (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError(f"{name} must be finite")
        elif value < 0 or (
            name
            in (
                "bolt_underhead_length_mm",
                "head_washer_mm",
                "top_plate_mm",
                "header_mm",
                "bottom_plate_mm",
                "nut_washer_mm",
                "nut_mm",
            )
            and value == 0
        ):
            raise ValueError(f"{name} must be positive or nonnegative as appropriate")
    if not plain_shank_end_mm <= first_usable_thread_mm <= bolt_underhead_length_mm:
        raise ValueError("shank end, usable thread start and bolt end are out of order")

    near = head_washer_mm + top_plate_mm
    far = near + header_mm
    nut_start = far + bottom_plate_mm + nut_side_washer_count * nut_washer_mm
    nut_end = nut_start + nut_mm
    protrusion = bolt_underhead_length_mm - nut_end
    plain = near + shear_allowance_mm + axial_tolerance_mm <= plain_shank_end_mm and (
        far + shear_allowance_mm + axial_tolerance_mm <= plain_shank_end_mm
    )
    threaded_nut = nut_start >= first_usable_thread_mm + axial_tolerance_mm
    engaged = (
        threaded_nut
        and bolt_underhead_length_mm
        >= nut_end + required_protrusion_mm + axial_tolerance_mm
    )
    result.update(
        {
            "status": (
                "CONDITIONAL"
                if all((plain, threaded_nut, engaged))
                else "FULL_SHANK_ASSUMPTION_FAILED"
                if not plain
                else "STACK_GEOMETRY_FAILED"
            ),
            "shear_planes_mm": (near, far),
            "nut_start_mm": nut_start,
            "nut_end_mm": nut_end,
            "protrusion_mm": protrusion,
            "both_shear_planes_plain": plain,
            "nut_on_usable_threads": threaded_nut,
            "full_nut_engagement_and_protrusion": engaged,
        }
    )
    return result
