"""Reuse the established first-order sizing method for the owner revision.

Inventory routing only: 92 shafts, 24 fittings, 24 timber bodies, six panels,
112 receiver walls and 474 metal gravity roles. Frozen methods are unchanged.
The full-width plywood stiffness is an initial sizing approximation; trimmed
plate stiffness and physical qualification are not established by this run.
"""

from __future__ import annotations

import argparse
import copy
import inspect
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import eoere_leg_header_mechanics as mechanics
from scripts.eoere_paired_frame_basis import ROOT, RAW, ref, sha
from scripts.eoere_requested_frame import REVISION

BASE = ROOT / RAW / "frame-completion-v1"
OUTPUT = BASE / "owner-requested-cases-v3"
GEOMETRY = BASE / "owner-requested-geometry-v3/geometry.json"
OWN = Path(__file__).resolve()
METHOD = ROOT / RAW / "runner_roller_review.py"


def rewrite(code, before, after):
    assert code.count(before) == 1, before
    return code.replace(before, after)


def prepare():
    assert not OUTPUT.exists()
    code = inspect.getsource(mechanics.prepare)
    for before, after in [
        ("geometry['revision'] == 'unadopted-coherent-three-pin-shift-v1'", f"geometry['revision'] == {REVISION!r}"),
        ("((106, 26, 102, 556) if three_pin else", "((92, 24, 92, 474) if three_pin else"),
        ("    if returned:\n        expected_added", "    if False:\n        expected_added"),
        ("{28: 34 if returned else 30}", "{28: 30}"),
        ("wall_count = 134 if three_pin", "wall_count = 112 if three_pin"),
        ("len(defaults) == (2 if three_pin else 4)", "len(defaults) == 4"),
    ]:
        code = rewrite(code, before, after)
    namespace = dict(vars(mechanics))
    exec(compile(code, str(OWN), "exec"), namespace)
    material_path = OUTPUT / "material.json"
    old = json.loads((ROOT / "docs/bolted-frame-development/plywood-cleat-operator-scenario-v1.json").read_bytes())
    material = copy.deepcopy(old)
    # Table 9, Sturd-I-Floor24oc, >=5plies. It includes nominal3/4in stock
    # (Table14); the physical panel stamp/thickness remain unobserved.
    material["material"] = "APA Rated Sturd-I-Floor24oc PS1 plywood, >=5plies, Group1 bearing; nominal3/4in"
    material["published_inputs"] = {"EA_parallel_lbf_per_foot_width": 5850000,
                                     "EI_parallel_lbf_in2_per_foot_width": 330000,
                                     "Gvtv_lbf_per_inch_depth": 45000}
    for key in ("EA_N", "EI_y_Nmm2"):
        material["properties"][key] *= 5850000 / 8200000
    material["properties"]["EI_z_Nmm2"] *= 330000 / 1265000
    material["properties"]["GA_v_N"] *= 45000 / 76000
    # Retain the existing declared homogeneous torsion surrogate, scaled to
    # the new panel G and geometric thickness cubed, with rectangle correction.
    b, t0, t1 = 203.2, 28.575, 19.05
    def rectangle(t):
        return b * t**3 * (1 / 3 - .21 * t / b * (1 - t**4 / (12 * b**4)))
    material["properties"]["GJ_Nmm2"] *= (45000 / 76000) * (t0 / t1) * rectangle(t1) / rectangle(t0)
    material["sizing_limits"] = ["Full203.2mm-width plywood beam operator is an initial stiffness hypothesis for the trimmed shape, not a final variable-width plate operator.",
                               "Table9 strength/rigidity uses24oc, not the former48oc. Two leaves stay independent; no glue/friction/composite credit."]
    OUTPUT.mkdir()
    material_path.write_text(json.dumps(material, indent=2) + "\n")
    namespace["prepare"](GEOMETRY, OUTPUT / "geometry-preparation", material_path)
    common = OUTPUT / "geometry-preparation/inputs.json"
    data = json.loads(common.read_bytes())
    review = mechanics.module(METHOD, "requested_frame_existing_floor")
    comparison = review.M
    data["scenario"]["corner_local_floor_comparison"] = comparison.contract()
    data["scenario"]["numerical_stopping_tolerance_N"] = 1e-6
    data["scenario"]["owner_requested_initial_sizing"] = {"geometry": ref(GEOMETRY), "old_force_pass_transferred": False,
                                                            "full_width_plywood_stiffness_hypothesis": True}
    data["source_sha256"].update(comparison.search.source_pins())
    data["source_sha256"].update(comparison.floor.source_pins())
    for p in [OWN, METHOD, comparison.OWN, comparison.BANK.OWN, comparison.BANK.SOURCE,
              comparison.BANK.READER, comparison.BANK.AFFINE, common,
              ROOT / RAW / "runner-roller-comparison-v1/method-coupons.json",
              ROOT / RAW / "runner-roller-comparison-v1/runner-exclusion-control.json"]:
        data["source_sha256"][ref(p)["path"]] = sha(p)
    folder = OUTPUT / "nominal/preparation"
    folder.mkdir(parents=True)
    (folder / "producer-snapshot.py").write_bytes(mechanics.OWN.read_bytes())
    mechanics.write(folder / "inputs.json", data)


def run(case):
    review = mechanics.module(METHOD, "requested_frame_existing_floor")
    comparison, bank = review.M, review.M.BANK
    inp = OUTPUT / "nominal/preparation/inputs.json"
    data = json.loads(inp.read_bytes())
    assert data["geometry"] == ref(GEOMETRY)
    bank.BASE, bank.INPUT, bank.CASES = OUTPUT / "nominal", inp, (case,)
    code = inspect.getsource(bank.run)
    for before, after in [
        ("physical_bodies'] == 166", "physical_bodies'] == 146"),
        ("shaft'] == 106", "shaft'] == 92"),
        ("len(prepared.contacts) == 2150", "len(prepared.contacts) == len(data['direct_contacts'])+184+32"),
    ]:
        code = rewrite(code, before, after)
    ns = dict(vars(bank))
    exec(compile(code, str(OWN), "exec"), ns)
    validator_code = inspect.getsource(mechanics.validator)
    start = validator_code.index("    require((returned and shaft_count")
    stop = validator_code.index("    body_count =", start)
    validator_code = validator_code[:start] + (
        "    require((timber_count,shaft_count)==(24,92), 'own revised inventory required')\n"
        "    fitting_count,port_count,role_count=24,92,474\n") + validator_code[stop:]
    scope = dict(vars(mechanics))
    exec(compile(validator_code, str(OWN), "exec"), scope)
    original_module = mechanics.module

    def module(path, name):
        if Path(path).resolve() == bank.READER.resolve():
            return SimpleNamespace(replay=review.replay)
        return original_module(path, name)

    with patch.object(mechanics, "validator", scope["validator"]), \
            patch.object(mechanics, "module", module), \
            patch.object(comparison.floor, "compatible_contact_solve", comparison.solve), \
            patch.object(comparison.floor, "_validate_final_pattern", comparison.validate), \
            patch.object(comparison.floor, "SUPPORT_BASIS", comparison.BASIS), \
            patch.object(comparison.search.frame, "GENERALIZED_RESIDUAL_TOLERANCE_N", 1e-6), \
            patch.object(bank.trial, "MATERIAL", OUTPUT / "material.json"):
        ns["run"](case)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "a12-forward", "a12-left", "a12-rear", "k12-right", "k12-rear", "a1-rear"])
    args = parser.parse_args()
    if args.action == "prepare":
        prepare()
    else:
        run(args.action)
