"""Bind the panel-restraint method to the cumulative v8 admitted force bank.

Reuse the issued numerical helper unchanged. The intake requires six own v8
fields, independent force/plywood replays and captured operators; v6 gains,
contact branches and force states never supply current results.
"""

from __future__ import annotations

import argparse
import fcntl
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import eoere_panel_bracing_review as method
from scripts import eoere_v8_analysis as analysis
from scripts.eoere_paired_frame_basis import CASES, ROOT, read, ref, sha

OWN = Path(__file__).resolve()
METHOD_SHA = "461d0141a1ce308100f98d52ab25ef47cf48d3db28d5ffb94935c2f88f7e8c1b"
METHOD_PATH = Path(method.__file__).resolve()
GEOMETRY = analysis.BASE / "geometry/geometry.json"
MATERIAL = analysis.BASE / "material.json"
RUN = analysis.BASE / "four-hosts"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def admit_field(field, replay, plywood, binding, geometry_ref, material_ref):
    """Reject cross-revision, unreplayed or historical response inputs."""
    require(field["trial_parent_geometry"] == geometry_ref, "own v8 analysis geometry required")
    require(field["source_inputs"]["plywood_material"] == material_ref, "own v8 plywood operator required")
    require(replay["field"] == plywood["field"] == binding, "independent replay field join differs")
    require(replay["false_screw_and_floor_forces_rejected"] is True
            and replay["same_state_declared_fixed_floor_replayed"] is True
            and replay["all_credited_hosts_in_bearing"] is True, "independent force/support admission required")
    require(replay["equilibrium"]["gradient_inf_n"] < 1e-5, "unchanged full-field residual gate")
    require(replay["equilibrium"]["physical_body_count"] == field["counts"]["physical_bodies"] == 148,
            "own current body census required")
    require(field["counts"]["shaft"] == 96 and field["counts"]["fitting"] == 24
            and len(field["panel_screw_actions"]) == 66, "own current hardware census required")
    require(len(plywood["raw_operator_checks"]) == 2, "both current bonded operators required")
    require(field["execution"]["historical_q_used"] is False and field["native_FEA_performed"] is False,
            "own first-order response, not historical state transfer")
    require(field["response"]["converged"] is True, "converged own field required")
    parameters = field["source_inputs"]["scenario"]["climber_load_parameters"]
    require(parameters["input_weight"] == 250 and parameters["input_unit"] == "lb"
            and parameters["downward_multiplier"] == 2. and parameters["horizontal_force_n"] == 300.,
            "owner 250 lb / 2.0 / 300 N scenario required")


class Intake:
    def __init__(self, bindings):
        self.bindings = bindings
        self.captured = {}

    def load(self):
        pins = {ref(OWN)["path"]: sha(OWN), ref(METHOD_PATH)["path"]: METHOD_SHA}
        require(sha(METHOD_PATH) == METHOD_SHA, "preserve issued panel-restraint method")
        ready = read(analysis.BASE / "adapter-readiness.json", pins)
        for name in ("receipt", "physical_geometry", "physical_clearance", "parent_v7_geometry"):
            require(ready[name] == self.bindings[name], "prepared candidate binding differs: " + name)
        require(ready["producer"] == ref(analysis.OWN), "prepared v8 analysis producer changed")
        for name in ("analysis_geometry", "material", "inputs", "method_readiness"):
            binding = ready[name]
            read(binding["path"], pins, binding["sha256"])
        geometry = read(GEOMETRY, pins, ready["analysis_geometry"]["sha256"])
        material = read(MATERIAL, pins, ready["material"]["sha256"])
        require(geometry["revision"] == analysis.REVISION
                and geometry["parent_owner_geometry"] == self.bindings["physical_geometry"],
                "current analytical/physical geometry join required")
        require(geometry["perfect_bond_analysis"] is True
                and len(geometry["axes"]) == 96 and len(geometry["screw_axes"]) == 66,
                "own nominal current analytical inventory required")
        require(material["physical_qualification"] is False, "analytical bond/operator must remain unqualified")
        fields = []
        missing = [case for case in CASES if not all((RUN / case / name).is_file() for name in
                   ("field.json", "independent-replay.json", "independent-replay-plywood.json"))]
        require(not missing, "own admitted v8 fields not ready: " + ", ".join(missing))
        for case in CASES:
            folder = RUN / case
            field = read(folder / "field.json", pins)
            replay = read(folder / "independent-replay.json", pins)
            plywood = read(folder / "independent-replay-plywood.json", pins)
            binding = ref(folder / "field.json")
            require(field["case_id"] == case, "case identity differs")
            admit_field(field, replay, plywood, binding, ref(GEOMETRY), ref(MATERIAL))
            require(field["source_inputs"]["scenario"]["perfect_bond_analysis"]["physical_parent"]
                    == self.bindings["physical_geometry"], "field physical-parent join differs")
            fields.append(("nominal", case, binding, field))
        pins.update(self.bindings["source_sha256"])
        self.captured = {"prepared_readiness": ref(analysis.BASE / "adapter-readiness.json"),
                         "analysis_geometry": ref(GEOMETRY), "material": ref(MATERIAL),
                         "fields": [row[2] for row in fields]}
        return geometry, fields, pins


def run(out, bindings):
    require(out.resolve().is_relative_to(analysis.BASE), "use the own v8 ignored packet")
    intake = Intake(bindings)
    intake.load()  # Admit all six before creating an output or solving a probe.
    scenario = SimpleNamespace(BASE=analysis.BASE, GEOMETRY=GEOMETRY, MATERIAL=MATERIAL,
                               HOSTS=analysis.previous.HOSTS, ROOT=ROOT)
    with patch.object(method, "analysis", scenario), patch.object(method, "checks", intake), \
            patch.object(method, "OWN", OWN):
        method.run(out, list(CASES))
    result = ref(out / "result.json")
    receipt = {"schema": "eoere_v8_panel_bracing_candidate_intake/v1", "producer": ref(OWN),
               "method": {"path": str(Path(method.__file__).resolve().relative_to(ROOT)), "sha256": METHOD_SHA},
               "physical_geometry_revision": analysis.PHYSICAL_REVISION, **bindings, **intake.captured,
               "result": result, "method_formula_or_tolerance_changed": False,
               "historical_force_or_stiffness_gain_transferred": False,
               "fresh_unbraced_climber_load_equilibrium": False,
               "strength_gain_established": False, "structural_acceptance": False, "release": False}
    with (out / "candidate-intake.json").open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(ref(out / "candidate-intake.json"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt-sha256", required=True)
    parser.add_argument("--physical-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with (ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        bindings = analysis.context(args.receipt_sha256, args.physical_sha256)
        run(args.out, bindings)


if __name__ == "__main__":
    main()
