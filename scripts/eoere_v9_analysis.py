"""Bind the established response method to the single-spacer v9 candidate.

Only the frozen eight-stack recipe changes. A fresh preparation is compared
with v8's numerical inputs before the parent decides on a response bank.
Neither matching geometry nor input hashes transfer a historical force pass.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import inspect
import json
import math
import re
from pathlib import Path
from types import FunctionType

from scripts import eoere_v8_analysis as blueprint
from scripts.eoere_paired_frame_basis import CASES, ROOT, read, ref, sha

OWN = Path(__file__).resolve()
LOADED_SHA = sha(OWN)
WORK = blueprint.WORK
BASE = WORK / "owner-single-spacer-stacks-v9/analysis-v1"
PHYSICAL = WORK / "owner-single-spacer-stacks-v9/geometry/geometry.json"
RECEIPT = Path("docs/bolted-frame-development/owner-frame-v9/geometry.json")
GEOMETRY = BASE / "geometry/geometry.json"
MATERIAL = BASE / "material.json"
RUN = BASE / "four-hosts"
INPUTS = RUN / "preparation/inputs.json"
PHYSICAL_REVISION = "eoere-single-spacer-cleat-stacks-v9"
REVISION = "eoere-v9-perfect-bond-four-host-analysis-v1"
PARAMETERS = Path(
    "docs/bolted-frame-development/owner-frame-v9/candidate-parameters.json"
)
PARAMETERS_SHA = "a6bc9c1f654504ed9e90150f0510a1e5de7249b3b734e4023c7609fb9d4f793c"
FACTS = Path("docs/bolted-frame-development/owner-frame-v9/hardware-facts.json")
FACTS_SHA = "7ba6bc079965974d144f1307dfeb724b35d64074cb2b2e9cb4e621a1b8c98608"
PARENT_RECEIPT_SHA = "4119758599d0562cb0dbd9e328273e84ee36526517d3c1d97593bc7dd42ab36b"
PARENT_PHYSICAL_SHA = "6dd5c7d9ce54c7d409e7ebfed0c321c46d57b68a1a8fa97527667a90bd49ebb9"
FROZEN_METHODS = {
    **blueprint.FROZEN_METHODS,
    "scripts/eoere_v8_analysis.py": "d79e511d8626dd4fa014f91d92902eb926704f8ff4be605485daeb8660cff76f",
}
METAL_GRAVITY = blueprint.METAL_GRAVITY
STACK_AXES = {
    "eoere_bolt_067",
    "eoere_bolt_070",
    "eoere_bolt_071",
    "eoere_bolt_074",
} | {f"cleat_post_bolt_{side}_{n}" for side in ("left", "right") for n in (1, 2)}
require = blueprint.require


def verify_recipes(geometry, parent, parameters):
    """Require precisely the frozen eight replacements and all other v8 data."""
    updates = {r["axis_id"]: r for r in parameters["axis_updates"]}
    require(
        len(updates) == len(parameters["axis_updates"]) == 8
        and set(updates) == STACK_AXES,
        "exact eight frozen stack updates required",
    )
    old_axes = {a["id"]: a for a in parent["axes"]}
    axes = {a["id"]: a for a in geometry["axes"]}
    old_selected = {r["axis_id"]: r for r in parent["selected_stack_overrides"]}
    selected = {r["axis_id"]: r for r in geometry["selected_stack_overrides"]}
    require(
        len(axes) == len(geometry["axes"]) == 96
        and axes.keys() == old_axes.keys()
        and len(selected) == 96
        and selected.keys() == old_selected.keys(),
        "complete v9 identity census required",
    )
    for identity, axis in axes.items():
        if identity in updates:
            row = updates[identity]
            require(
                old_axes[identity] == row["before_axis"]
                and old_selected[identity] == row["before_selection"]
                and axis == row["after_axis"]
                and selected[identity] == row["after_selection"],
                "current recipe differs from frozen parameters: " + identity,
            )
            require(
                axis["nominal_under_head_length_mm"] == 190.5
                and axis["nut_side_spacer_mm"] == 25.4
                and selected[identity]["minimum_body_mm"] == 144.272
                and selected[identity]["spacer_piece_count"] == 1,
                "shorter catalog recipe required",
            )
            for key in (
                "point_xyz_mm",
                "direction_xyz",
                "grip_mm",
                "before_plate_mm",
                "after_plate_mm",
                "receivers",
                "attachments",
                "head_faces",
                "nut_faces",
                "installation_orientation_revision",
            ):
                require(
                    axis[key] == old_axes[identity][key],
                    "v8 joint location/orientation changed: " + key,
                )
        else:
            require(
                axis == old_axes[identity]
                and selected[identity] == old_selected[identity],
                "unselected stack changed: " + identity,
            )
    for key in (
        "profiles",
        "fitting_poses",
        "screw_axes",
        "inward_angle_study",
        "inward_bolt_revision",
    ):
        require(
            geometry[key] == parent[key],
            "v8 wood, inset angles or inward orientations changed: " + key,
        )


def context(receipt_sha, physical_sha, receipt_path=RECEIPT):
    require(
        all(
            isinstance(v, str) and re.fullmatch(r"[a-f0-9]{64}", v)
            for v in (receipt_sha, physical_sha)
        ),
        "explicit SHA-256 input bindings required",
    )
    require(sha(OWN) == LOADED_SHA, "loaded v9 adapter changed")
    for name, digest in FROZEN_METHODS.items():
        require(sha(name) == digest, "frozen response source changed: " + name)
    prior = blueprint.context(PARENT_RECEIPT_SHA, PARENT_PHYSICAL_SHA)
    pins = {**prior["source_sha256"], **FROZEN_METHODS, ref(OWN)["path"]: LOADED_SHA}
    parameters = read(PARAMETERS, pins, PARAMETERS_SHA)
    facts = read(FACTS, pins, FACTS_SHA)
    require(
        parameters["facts"] == ref(FACTS)
        and parameters["revision"] == PHYSICAL_REVISION
        and parameters["parent_geometry"]["receipt"] == prior["receipt"]
        and parameters["parent_checked_geometry"] == prior["physical_geometry"],
        "frozen v9 parent/recipe binding required",
    )
    require(
        facts["bolt"]["underhead_length_mm"] == 190.5
        and facts["bolt"]["conservative_analysis_minimum_body_mm"] == 144.272
        and facts["spacer"]["length_mm"] == 25.4,
        "bound catalog input recipe differs",
    )
    producer = parameters["producer"]
    require(ref(producer["path"]) == producer, "frozen recipe producer changed")
    pins[producer["path"]] = producer["sha256"]
    path = (ROOT / receipt_path).resolve()
    require(path.is_relative_to(ROOT), "repository receipt required")
    receipt = read(path, pins, receipt_sha)
    expected = {"path": str(PHYSICAL.relative_to(ROOT)), "sha256": physical_sha}
    require(
        receipt.get("revision") == PHYSICAL_REVISION
        and receipt.get("checked_geometry") == expected
        and receipt.get("fabrication_released") is False
        and receipt.get("climbing_released") is False,
        "conditional exact v9 geometry receipt required",
    )
    geometry = read(PHYSICAL, pins, physical_sha)
    clear_ref = receipt["checked_clearance"]
    clearance = read(clear_ref["path"], pins, clear_ref["sha256"])
    require(
        clearance.get("geometry") == expected
        and clearance.get("nominal_geometry_clear") is True
        and not clearance.get("collisions")
        and not clearance.get("missing_candidates")
        and clearance.get("occupied_part_count") == 1021,
        "own 1021-part occupied clearance required",
    )
    require(
        geometry["revision"] == PHYSICAL_REVISION
        and len(geometry["fitting_poses"]) == 24
        and len(geometry["profiles"]) == 30
        and len(geometry["screw_axes"]) == 66,
        "v9 physical inventory differs",
    )
    parent = read(
        parameters["parent_checked_geometry"]["path"], pins, PARENT_PHYSICAL_SHA
    )
    verify_recipes(geometry, parent, parameters)
    return {
        **prior,
        "receipt": ref(path),
        "physical_geometry": expected,
        "physical_clearance": clear_ref,
        "parent_v8_geometry": parameters["parent_checked_geometry"],
        "parent_v8_receipt": prior["receipt"],
        "candidate_parameters": ref(PARAMETERS),
        "hardware_facts": ref(FACTS),
        "source_sha256": pins,
        "explicit_hashes_are_execution_authorization": False,
    }


def _namespace():
    return {
        **vars(blueprint),
        **{
            key: globals()[key]
            for key in (
                "OWN",
                "LOADED_SHA",
                "BASE",
                "PHYSICAL",
                "RECEIPT",
                "PHYSICAL_REVISION",
                "REVISION",
                "FROZEN_METHODS",
            )
        },
    }


def functions(bindings):
    namespace = _namespace()
    source = inspect.getsource(blueprint.functions)
    source = blueprint.previous.edited(
        source, "'\"current_v8_fixed_floor\"'", "'\"current_v9_fixed_floor\"'"
    )
    exec(compile(source, str(OWN), "exec"), namespace)  # noqa: S102 -- pinned v8 binding blueprint, numerical kernels unchanged
    return namespace["functions"](bindings)


def _rows(rows, keys, identity="id"):
    return sorted(
        ({key: copy.deepcopy(row[key]) for key in keys if key in row} for row in rows),
        key=lambda row: json.dumps(row.get(identity, row), sort_keys=True),
    )


def _semantic_inputs(data, material):
    require(
        material.get("properties"),
        "bound material properties required for a complete comparison",
    )
    shafts = sorted(data["shafts"], key=lambda row: row["axis_id"])
    return {
        "shaft_domains_and_sections": _rows(
            shafts,
            (
                "axis_id",
                "body",
                "point",
                "basis",
                "diameter_mm",
                "bore_diameter_mm",
                "shaft_interval_mm",
            ),
            "axis_id",
        ),
        "bearing_surfaces": [
            {
                "axis_id": s["axis_id"],
                "surfaces": _rows(
                    s["surfaces"],
                    (
                        "host",
                        "kind",
                        "interval_mm",
                        "grain_axis_xyz",
                        "bore_diameter_mm",
                        "flange",
                        "receiver",
                        "entry_xyz_mm",
                    ),
                    "host",
                ),
            }
            for s in shafts
        ],
        "end_support_locations": [
            {
                "axis_id": s["axis_id"],
                "ends": _rows(
                    s["ends"],
                    (
                        "end",
                        "host",
                        "flange",
                        "support_s_mm",
                        "direction_on_shaft_xyz",
                        "own_washer_thickness_mm",
                    ),
                    "end",
                ),
            }
            for s in shafts
        ],
        "end_capture_pressure_locations": [
            {
                "axis_id": s["axis_id"],
                "ends": _rows(
                    s["ends"],
                    ("end", "pressure_face_s_mm", "own_spacer_length_mm", "washer_id"),
                    "end",
                ),
            }
            for s in shafts
        ],
        "metal_gravity_roles": [
            {
                "axis_id": s["axis_id"],
                "roles": _rows(
                    s["metal_roles"],
                    ("id", "kind", "volume_mm3", "mass_kg", "center_of_mass_xyz_mm"),
                ),
            }
            for s in shafts
        ],
        "owner_gravity": _rows(
            data["physical_owner_gravity_rows"],
            ("id", "kind", "mass_kg", "center_xyz_mm"),
        ),
        "timber_response_geometry": _rows(
            data["timber_rows"],
            (
                "name",
                "start",
                "end",
                "axis",
                "section_u",
                "section_v",
                "width_mm",
                "depth_mm",
                "source_centerline_grain_interval_mm",
                "stiffness_scenario",
            ),
            "name",
        ),
        "fitting_poses": _rows(
            data["fitting_poses"],
            ("id", "duty_id", "origin_xyz_mm", "u_xyz", "v_xyz", "w_xyz"),
        ),
        "fitting_ports_and_holes": {
            key: data[key] for key in ("fitting_port_bindings", "all_factory_holes")
        },
        "contact_law_rows": _rows(
            data["direct_contacts"],
            (
                "id",
                "kind",
                "first",
                "second",
                "point_xyz_mm",
                "direction_xyz",
                "stiffness",
                "bedding_n_mm3",
                "reference_area_mm2",
            ),
        ),
        "flange_domain_stiffness": _rows(
            data["flange_domains"],
            (
                "id",
                "fitting",
                "receiver",
                "model_port_id",
                "clipped_area_mm2",
                "declared_flange_area_density_n_mm3",
                "declared_nominal_flange_total_stiffness_n_mm",
                "nominal_full_holed_flange_area_mm2",
                "nominal_half_area_mm2",
            ),
        ),
        "screw_law_rows": _rows(
            data["hillman_rows"],
            (
                "id",
                "first",
                "second",
                "basis",
                "point_xyz_mm",
                "ka",
                "kl",
                "clearance",
                "tension_only",
            ),
        ),
        "floor_footprints": data["floor_footprints"],
        "parameters": data["parameters"],
        "constitutive_scenario": {
            key: value
            for key, value in data["scenario"].items()
            if key
            not in ("perfect_bond_analysis", "nominal_metal_role_gravity_approximation")
        },
        "plywood_material_operator": {
            key: material[key]
            for key in ("properties", "density_kg_m3")
            if key in material
        },
        "panel_machining_and_ids": {
            key: data[key]
            for key in ("panel_ids", "current_panel_machining_descriptors")
        },
        "case_loads": [
            {
                "case_id": c["case_id"],
                "loads": _rows(
                    c["loads"],
                    ("id", "body", "point_xyz_mm", "force_xyz_n", "moment_xyz_nmm"),
                ),
            }
            for c in sorted(data["cases"], key=lambda c: c["case_id"])
        ],
    }


def _changes(first, last, path=""):
    if first == last:
        return []
    if isinstance(first, dict) and isinstance(last, dict):
        return [
            row
            for key in sorted(first.keys() | last.keys())
            for row in _changes(first.get(key), last.get(key), path + "/" + str(key))
        ]
    if isinstance(first, list) and isinstance(last, list) and len(first) == len(last):
        return [
            row
            for i, (a, b) in enumerate(zip(first, last, strict=True))
            for row in _changes(a, b, path + "/" + str(i))
        ]
    row = {"path": path, "before": first, "after": last}
    if all(
        isinstance(v, (int, float)) and not isinstance(v, bool) for v in (first, last)
    ):
        require(
            math.isfinite(first) and math.isfinite(last),
            "finite numerical comparison required",
        )
        row["absolute_change"] = abs(last - first)
    return [row]


def compare_prepared_inputs(before, after, before_material, after_material):
    """Compare consumed mechanical descriptors; ignore provenance-only paths.

    This uses exact numerical equality and exposes differences, including small
    regenerated roundoff. It supplies no stiffness/force equivalence theorem.
    """
    old, new = (
        _semantic_inputs(before, before_material),
        _semantic_inputs(after, after_material),
    )
    json.dumps([old, new], allow_nan=False)
    families = {}
    for key in old:
        changes = _changes(old[key], new[key])
        families[key] = {
            "changed": bool(changes),
            "changed_leaf_count": len(changes),
            "examples": changes[:12],
        }
    return {
        "schema": "eoere_prepared_numerical_input_comparison/v1",
        "families": families,
        "numerical_or_physical_descriptors_changed": any(
            r["changed"] for r in families.values()
        ),
        "source_paths_and_hashes_treated_as_mechanical_values": False,
        "roundoff_suppressed_or_solve_tolerance_relaxed": False,
        "operator_or_response_equivalence_established": False,
        "historical_force_results_transferred": False,
        "complete_joint_qualified": False,
    }


def compare():
    before_input = blueprint.BASE / "four-hosts/preparation/inputs.json"
    before_material = blueprint.BASE / "material.json"
    pins = {}
    old, new = read(before_input, pins), read(INPUTS, pins)
    old_material, new_material = read(before_material, pins), read(MATERIAL, pins)
    report = compare_prepared_inputs(old, new, old_material, new_material)
    report.update(
        producer=ref(OWN),
        before_inputs=ref(before_input),
        after_inputs=ref(INPUTS),
        before_material=ref(before_material),
        after_material=ref(MATERIAL),
        source_sha256=pins,
    )
    blueprint.previous.mechanics.write(BASE / "numerical-input-comparison.json", report)
    return report


def prepare(bindings, namespace):
    scope = _namespace()
    source = blueprint.previous.edited(
        inspect.getsource(blueprint.prepare),
        '"eoere_v8_existing_response_method_readiness/v1"',
        '"eoere_v9_existing_response_method_readiness/v1"',
    )
    exec(compile(source, str(OWN), "exec"), scope)  # noqa: S102 -- unchanged preparation evidence wrapper, v9 schema only
    scope["prepare"](bindings, namespace)
    compare()


def run(bindings, namespace, case):
    ready = json.loads((BASE / "adapter-readiness.json").read_bytes())
    require(
        ready["schema"] == "eoere_v9_existing_response_method_readiness/v1",
        "own v9 readiness required",
    )
    for key in (
        "parent_v8_geometry",
        "parent_v8_receipt",
        "candidate_parameters",
        "hardware_facts",
    ):
        require(
            ready[key] == bindings[key], "prepared v9 recipe binding differs: " + key
        )
    comparison = json.loads((BASE / "numerical-input-comparison.json").read_bytes())
    require(
        comparison["after_inputs"] == ref(INPUTS)
        and comparison["after_material"] == ref(MATERIAL)
        and comparison["producer"] == ref(OWN),
        "current numerical input comparison required before a bank",
    )
    FunctionType(blueprint.run.__code__, _namespace())(bindings, namespace, case)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "compare", *CASES))
    parser.add_argument("--receipt-sha256", required=True)
    parser.add_argument("--physical-sha256", required=True)
    parser.add_argument("--receipt", type=Path, default=RECEIPT)
    args = parser.parse_args()
    with (ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock").open(
        "a+"
    ) as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        bindings = context(args.receipt_sha256, args.physical_sha256, args.receipt)
        namespace = functions(bindings)
        if args.action == "prepare":
            prepare(bindings, namespace)
        elif args.action == "compare":
            compare()
        else:
            run(bindings, namespace, args.action)


if __name__ == "__main__":
    main()
