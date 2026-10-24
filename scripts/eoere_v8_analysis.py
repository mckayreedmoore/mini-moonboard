"""Bind the established conditional response method to cumulative v8 inputs.

The caller supplies frozen receipt and physical-geometry hashes. They identify
inputs and do not grant execution authorization. No v6 force result transfers.
The inherited nominal metal-role gravity, uniform nominal shaft stiffness,
perfect plywood bond and declared four-host floor remain analytical scenarios.
"""

from __future__ import annotations

import argparse
import fcntl
import inspect
import json
import re
from pathlib import Path

import numpy as np

from scripts import eoere_v6_analysis as previous
from scripts.eoere_paired_frame_basis import CASES, ROOT, read, ref, sha

OWN = Path(__file__).resolve()
LOADED_SHA = sha(OWN)
WORK = previous.WORK
BASE = WORK / "owner-inward-angles-v8/analysis-v1"
PHYSICAL = WORK / "owner-inward-angles-v8/geometry/geometry.json"
RECEIPT = Path("docs/bolted-frame-development/owner-frame-v8/geometry.json")
PHYSICAL_REVISION = "eoere-inward-bolts-and-angles-v8"
REVISION = "eoere-v8-perfect-bond-four-host-analysis-v1"
FROZEN_METHODS = {
    "scripts/eoere_v6_analysis.py": "90cde1884f4e9d85c40107c88be00d6affda626663e12e1692a81a91d92158be",
    "scripts/eoere_leg_header_mechanics.py": "903dd7836811d30c20a1149e079863077fb336bcc1086c1cceb16e076487a114",
    "scripts/eoere_current_response.py": "3340243bd8127d3fa9fd8c2f5b1778db7abadc6da8a05c901e33b79b503a7944",
}
FROZEN_METHODS.update(
    {
        str((WORK / name).relative_to(ROOT)): digest
        for name, digest in {
            "owner_laminated_floor.py": "b380e8777ae58af18aeb9044346125be2929c660c087b1732f564a32047ddb31",
            "owner_laminated_mechanics.py": "c950234f1994a34969d711ef4235722e51f36361c3b3de2d6ebeae17eb7af84a",
            "owner_laminated_mechanics_v2.py": "e9fe0fa103e873eea0865dc10e2d0a6d34cfe3817ceb8e708c2d8eb4b87c31c3",
        }.items()
    }
)
METAL_GRAVITY = {
    "basis": "inherited nominal local-hardware scalar volumes and axial centroids, with aggregated spacer roles",
    "cached_hardware_BRep_mass_or_centroid_used": False,
    "A574_head_approximation": "The inherited generic solid-hex head role differs from the displayed socket-head/recess geometry; the v7 comparison found up to 0.646358 mm axial centroid difference. This is a nominal gravity scenario, not exact CAD metal gravity.",
    "shaft_stiffness": "uniform nominal circular major diameter; no constitutive body/thread transition",
    "orientation_specific_thread_strength_or_delivered_shank_qualified": False,
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_inward_axis(axis, prior, translation):
    """Require a moved axis to retain its exact v7 installation orientation."""
    require(axis["id"] == prior["id"], "same inward shaft identity required")
    for key in (
        "direction_xyz",
        "before_plate_mm",
        "after_plate_mm",
        "diameter_mm",
        "bore_diameter_mm",
        "grip_mm",
        "nominal_under_head_length_mm",
        "nut_side_spacer_mm",
        "hardware_scenario",
    ):
        require(axis.get(key) == prior.get(key), "inward installation changed: " + key)
    require(
        np.allclose(
            axis["point_xyz_mm"],
            np.asarray(prior["point_xyz_mm"]) + translation,
            rtol=0.0,
            atol=1e-8,
        ),
        "current inward origin must receive only the recorded translation",
    )
    require(
        axis.get("head_faces") == "exterior"
        and axis.get("nut_faces") == "interior"
        and axis.get("installation_orientation_revision")
        == "eoere-inward-exterior-bolts-v7",
        "all inward head/nut identities must remain explicit",
    )


def context(receipt_sha, physical_sha, receipt_path=RECEIPT):
    """Validate the caller's frozen inputs without constructing or solving."""
    require(
        all(
            isinstance(v, str) and re.fullmatch(r"[a-f0-9]{64}", v)
            for v in (receipt_sha, physical_sha)
        ),
        "explicit SHA-256 input bindings required",
    )
    path = (ROOT / receipt_path).resolve()
    require(path.is_relative_to(ROOT), "repository receipt required")
    pins = {**FROZEN_METHODS, ref(OWN)["path"]: LOADED_SHA}
    for name, digest in pins.items():
        require(sha(name) == digest, "frozen response source changed: " + name)
    receipt = read(path, pins, receipt_sha)
    expected = {"path": str(PHYSICAL.relative_to(ROOT)), "sha256": physical_sha}
    require(
        receipt.get("revision") == PHYSICAL_REVISION
        and receipt.get("checked_geometry") == expected,
        "receipt must bind the caller's exact cumulative physical geometry",
    )
    require(
        receipt.get("fabrication_released") is False
        and receipt.get("climbing_released") is False,
        "conditional geometry receipt required",
    )
    geometry = read(PHYSICAL, pins, physical_sha)
    clear_ref = receipt["checked_clearance"]
    clearance = read(clear_ref["path"], pins, clear_ref["sha256"])
    require(
        clearance.get("geometry") == expected
        and clearance.get("nominal_geometry_clear") is True
        and not clearance.get("collisions")
        and not clearance.get("missing_candidates")
        and clearance.get("occupied_part_count") == 1037,
        "own exact nominal occupied clearance required",
    )
    require(
        geometry.get("revision") == PHYSICAL_REVISION
        and len(geometry["axes"]) == 96
        and len(geometry["fitting_poses"]) == 24
        and len(geometry["profiles"]) == 30
        and len(geometry["screw_axes"]) == 66,
        "own cumulative physical census required",
    )
    study = geometry["inward_angle_study"]
    moved = set(study["moved_axis_ids"])
    require(
        len(moved) == 24
        and len(study["moved_angle_ids"]) == 8
        and study["world_translation_xyz_mm"] == [0.0, 6.0, 0.0],
        "bounded eight-angle translation required",
    )
    parent_ref = study["parent_geometry"]
    parent = read(parent_ref["path"], pins, parent_ref["sha256"])
    require(
        parent.get("revision") == "eoere-inward-exterior-bolts-v7"
        and geometry["screw_axes"] == parent["screw_axes"],
        "preserve current v7 and all 66 screw descriptors",
    )
    old_axes = {a["id"]: a for a in parent["axes"]}
    inward = [
        a
        for a in geometry["axes"]
        if a.get("installation_orientation_revision")
        == "eoere-inward-exterior-bolts-v7"
    ]
    require(
        len(inward) == 40
        and {a["id"] for a in inward}
        == {r["after"]["id"] for r in parent["inward_bolt_revision"]["axis_updates"]},
        "all 40 reviewed inward-facing stacks must remain",
    )
    for axis in inward:
        verify_inward_axis(
            axis,
            old_axes[axis["id"]],
            [0.0, 6.0, 0.0] if axis["id"] in moved else [0.0, 0.0, 0.0],
        )
    require(
        geometry["selected_stack_overrides"] == parent["selected_stack_overrides"],
        "selected lengths, grades, spacers and orientation flags must remain v7's",
    )
    return {
        "receipt": ref(path),
        "physical_geometry": expected,
        "physical_clearance": clear_ref,
        "parent_v7_geometry": parent_ref,
        "source_sha256": pins,
        "explicit_hashes_are_execution_authorization": False,
    }


def functions(bindings):
    """Rebind paths and two frozen input guards; retain numerical kernels."""
    namespace = {
        **vars(previous),
        "OWN": OWN,
        "BASE": BASE,
        "PHYSICAL": PHYSICAL,
        "RECEIPT": ROOT / bindings["receipt"]["path"],
        "REVISION": REVISION,
        "GEOMETRY": BASE / "geometry/geometry.json",
        "MATERIAL": BASE / "material.json",
        "RUN": BASE / "four-hosts",
        "INPUTS": BASE / "four-hosts/preparation/inputs.json",
        "PARENT_SOURCE_PINS": bindings["source_sha256"],
        "METAL_GRAVITY": METAL_GRAVITY,
    }
    source = inspect.getsource(previous.prepare)
    for before, after in (
        (
            '"d2849e0bb7e3751396854556fa0bb411d83f3cf94dec55ec157a582f4f5b6e80"',
            repr(bindings["receipt"]["sha256"]),
        ),
        (
            'g["revision"] == "eoere-flat-cleats-principal-upper-pairs-v6"',
            'g["revision"] == ' + repr(PHYSICAL_REVISION),
        ),
        (
            'pins = {ref(OWN)["path"]: sha(OWN)}',
            'pins = {**PARENT_SOURCE_PINS, ref(OWN)["path"]: sha(OWN)}',
        ),
        (
            'material["source_sha256"].update({ref(OWN)["path"]: sha(OWN), ref(old_material)["path"]: sha(old_material)})',
            'material["source_sha256"].update({**PARENT_SOURCE_PINS, ref(OWN)["path"]: sha(OWN), ref(old_material)["path"]: sha(old_material)})',
        ),
        (
            'data = parameterize_inputs(data, LoadParameters(weight=250, unit="lb"))',
            (
                'data = parameterize_inputs(data, LoadParameters(weight=250, unit="lb"))\n'
                '    data["source_sha256"].update(PARENT_SOURCE_PINS)\n'
                '    data["scenario"]["nominal_metal_role_gravity_approximation"] = METAL_GRAVITY'
            ),
        ),
    ):
        source = previous.edited(source, before, after)
    floor = previous.edited(
        inspect.getsource(previous.floor_method),
        '"current_v6_fixed_floor"',
        '"current_v8_fixed_floor"',
    )
    exec(  # noqa: S102 -- pinned numerical method with explicit path/input guards only
        compile(
            floor + "\n" + source + "\n" + inspect.getsource(previous.run),
            str(OWN),
            "exec",
        ),
        namespace,
    )
    return namespace


def prepare(bindings, namespace):
    namespace["prepare"]()
    snapshots = {}
    for relative in FROZEN_METHODS:
        source = ROOT / relative
        target = BASE / (source.stem + "-method-snapshot.py")
        target.write_bytes(source.read_bytes())
        snapshots[relative] = ref(target)
    for path, digest in bindings["source_sha256"].items():
        require(sha(path) == digest, "frozen input changed during preparation: " + path)
    previous.mechanics.write(
        BASE / "adapter-readiness.json",
        {
            "schema": "eoere_v8_existing_response_method_readiness/v1",
            "analysis_revision": REVISION,
            **bindings,
            "producer": ref(OWN),
            "frozen_method_snapshots": snapshots,
            "analysis_geometry": ref(namespace["GEOMETRY"]),
            "material": ref(namespace["MATERIAL"]),
            "inputs": ref(namespace["INPUTS"]),
            "method_readiness": ref(BASE / "readiness.json"),
            "load_contract": {
                "weight_lb": 250,
                "downward_multiplier": 2,
                "horizontal_force_N": 300,
                "accessory_mass_kg": 25,
                "duration_factor_CD": 1,
            },
            "metal_role_gravity": METAL_GRAVITY,
            "new_force_response_computed": False,
            "historical_force_pass_transferred": False,
            "complete_joint_or_frame_qualified": False,
        },
    )


def run(bindings, namespace, case):
    ready = json.loads((BASE / "adapter-readiness.json").read_bytes())
    for key in (
        "receipt",
        "physical_geometry",
        "physical_clearance",
        "parent_v7_geometry",
    ):
        require(
            ready[key] == bindings[key], "prepared candidate binding differs: " + key
        )
    require(ready["producer"] == ref(OWN), "prepared v8 producer changed")
    for name in ("analysis_geometry", "material", "inputs", "method_readiness"):
        require(
            sha(ready[name]["path"]) == ready[name]["sha256"],
            "prepared input changed: " + name,
        )
    namespace["run"](case)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", *CASES))
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
        (
            prepare(bindings, namespace)
            if args.action == "prepare"
            else run(bindings, namespace, args.action)
        )


if __name__ == "__main__":
    main()
