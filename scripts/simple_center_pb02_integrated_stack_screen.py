"""Ten-bolt length and installed-envelope sensitivity at the PB02 working pose."""

import json
from unittest.mock import patch

from scripts import simple_center_current_stack_tip_screen as stack
from scripts import simple_center_pb02_integrated_trial as integrated

SOURCE_COMMIT = "e9e4e42"
TRIALS = {
    "current_lengths": {},
    "principal_pair_5_5in": {"header_cleat": 5.5, "cleat_principal": 5.5},
    "principal_pair_6in": {"header_cleat": 6, "cleat_principal": 6},
    "link_5_5in": {"cleat_link": 5.5},
}
# Facts transcribed only from the repository's maintained retailer-source notes.
# They identify leads; none establishes a complete usable thread interval.
ORDINARY_STORE_LEADS = {
    "800676": {
        "retailer": "Home Depot",
        "brand": "Everbilt",
        "nominal_length_in": 5,
        "product_facts": {
            "grade": "A307",
            "thread_description": "fully threaded",
        },
    },
    "9058745": {
        "retailer": "Home Depot",
        "brand": "Prime-Line",
        "nominal_length_in": 5,
        "product_facts": {"grade": "A307 Grade A", "pack_count": 25},
    },
    "190059": {
        "retailer": "Lowe's",
        "brand": "Hillman",
        "nominal_length_in": 5,
        "product_facts": {"thread_description": "partially threaded"},
    },
    "805336": {
        "retailer": "Home Depot",
        "brand": "Everbilt",
        "nominal_length_in": 5.5,
        "product_facts": {"pack_count": 1},
    },
    "805330": {
        "retailer": "Home Depot",
        "brand": "Everbilt",
        "nominal_length_in": 5.5,
        "product_facts": {
            "grade": "A307",
            "thread_description": "fully threaded",
            "pack_count": 25,
        },
    },
    "190062": {
        "retailer": "Lowe's",
        "brand": "Hillman",
        "nominal_length_in": 5.5,
        "product_facts": {"thread_description": "partially threaded"},
    },
    "805436": {
        "retailer": "Home Depot",
        "brand": "Everbilt",
        "nominal_length_in": 6,
        "product_facts": {
            "grade": "A307",
            "finish": "galvanized",
            "thread_description": "fully threaded",
        },
    },
    "800696": {
        "retailer": "Home Depot",
        "brand": "Everbilt",
        "nominal_length_in": 8,
        "product_facts": {"grade": "A307", "listed_thread_length_in": 6},
    },
    "9058821": {
        "retailer": "Home Depot",
        "brand": "Prime-Line",
        "nominal_length_in": 8,
        "product_facts": {"grade": "A307 Grade A", "pack_count": 10},
    },
}


def _grips_mm(ends):
    return {
        name: round(
            sum(abs(a - b) for a, b in zip(ends[pair[0]][0], ends[pair[1]][0])),
            3,
        )
        for name, pair in stack.PAIRS.items()
    }


def screen():
    """Apply the maintained sensitivity bounds to the checked ten-bore pose."""
    original_grips = _grips_mm(stack._geometry()[2])
    geometry = integrated.working_geometry()
    working_grips = _grips_mm(geometry[2])
    changes = {
        name: round(working_grips[name] - original_grips[name], 3)
        for name in stack.PAIRS
        if working_grips[name] != original_grips[name]
    }
    if changes != {"header_cleat": -4.0, "cleat_link": 4.8}:
        raise ValueError(f"unexpected PB02 grip changes: {changes}")

    scenarios = {}
    with patch.object(stack, "_geometry", return_value=geometry):
        for label, overrides in TRIALS.items():
            trial = stack.screen(length_overrides=overrides)
            hits = {
                end: {kind: end_hits for kind, end_hits in kinds.items() if end_hits}
                for end, kinds in trial["per_end_permanent_occupancy"].items()
                if any(kinds.values())
            }
            scenarios[label] = {
                "rows": trial["rows"],
                "wood_or_fixed_screw_hits_mm3": hits,
                "potential_other_bolt_permanent_hits_mm3": trial[
                    "potential_other_bolt_permanent_hits_mm3"
                ],
                "modeled_wood_and_fixed_screws_clear_both_orientations": trial[
                    "modeled_wood_and_fixed_screws_clear_both_orientations"
                ],
            }
    return {
        "source_commit": SOURCE_COMMIT,
        "pose": "PB02 integrated Z370 working geometry; ten bores",
        "grip_changes_from_maintained_pose_mm": changes,
        "sensitivity_bounds": {
            "wood_grip_each_side_in": stack.GRIP_SENSITIVITY_IN,
            "washer_each_side_in": stack.WASHER_RANGE_IN,
            "nut_height_in": stack.NUT_RANGE_IN,
            "required_tip_beyond_nut_in": stack.TIP_REQUIREMENT_IN,
        },
        "invented_bounds_are_not_product_facts": True,
        "ordinary_store_leads": {
            sku: lead | {"usable_thread_interval_verified": False}
            for sku, lead in ORDINARY_STORE_LEADS.items()
        },
        "scenarios": scenarios,
        "procurement_or_drilling_released": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))
