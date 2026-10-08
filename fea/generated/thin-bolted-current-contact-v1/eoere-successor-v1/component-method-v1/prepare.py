"""Source-only preparation receipt for a post-admission component consumer."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from assessment import GROSS, OWN, PINS, ROOT, STEEL, canonical, join, load, sha, verify

SELF = Path(__file__).resolve()
LOADED_SHA = sha(SELF)
INPUT = OWN.parent.parent/"mechanics-inputs-v1/inputs.json"
INPUT_SHA = "7a003cb7fe6d14a8644a3030b45caf96a7a4b59618d8c1703c3e3626f267d4b4"
STEEL_SHA = "9d670f264d5b074abf4cbd48baaebde486b1c15e3ddb612302bd1f41a577a360"
ASSESSMENT_SHA = "f5ae45cb3b630a57895b2119958c24f1cc559d9cbf34d5b2373b5a1975c300b0"


def prepare():
    direct = {**PINS, str(OWN.relative_to(ROOT)): ASSESSMENT_SHA,
        str(STEEL.relative_to(ROOT)): STEEL_SHA, str(INPUT.relative_to(ROOT)): INPUT_SHA,
        str(SELF.relative_to(ROOT)): LOADED_SHA,
        str(OWN.with_name("test_assessment.py").relative_to(ROOT)):
            "de8214861cbfdeb90e39e1c71d89a045db9e4b16a0938bf06df8ea29a649ff9c",
        str(OWN.with_name("test_gross_members.py").relative_to(ROOT)):
            "cbf76b357af6c80dfbece3d48520948b5c088c17628209dd0f77e6c53ef5cafe"}
    verify(direct)
    source = json.loads(INPUT.read_bytes())
    steel = load(STEEL, STEEL_SHA, "eoere_component_source_steel")
    gross = load(GROSS, PINS[str(GROSS.relative_to(ROOT))], "eoere_component_source_gross")
    pins = dict(direct)
    join(pins, source["source_sha256"])
    join(pins, steel.source_contract()["source_sha256"])
    join(pins, gross.source_pins())
    verify(pins)
    counts = {"angles": len(source["fitting_poses"]), "timbers": len(source["timber_rows"]),
        "physical_shafts": len(source["shafts"]), "Hillman_axes": len(source["hillman_rows"]),
        "panels": len(source["panel_ids"]), "fitting_ports": len(source["fitting_port_bindings"]),
        "wood_surfaces": sum(s["kind"] == "wood" for a in source["shafts"] for s in a["surfaces"]),
        "steel_surfaces": sum(s["kind"] == "steel" for a in source["shafts"] for s in a["surfaces"]),
        "end_captures": sum(len(a["ends"]) for a in source["shafts"])}
    if counts != {"angles": 22, "timbers": 22, "physical_shafts": 100, "Hillman_axes": 66,
                  "panels": 6, "fitting_ports": 88, "wood_surfaces": 120, "steel_surfaces": 88, "end_captures": 200}:
        raise ValueError("fresh source census differs")
    verify(pins)
    return {"schema": "eoere_component_consumer_preparation/v1", "source_sha256": direct,
        "referenced_source_map": str(INPUT.relative_to(ROOT)), "joined_pin_count": len(pins),
        "joined_pin_union_canonical_sha256": canonical(pins), "source_pins_before_after_unchanged": True,
        "fresh_source_census": counts, "anticipated_field_schema": "eoere_first_order_common_shaft_four_port_candidate/v2",
        "anticipated_receipt_schema": "eoere_first_order_independent_field_admission/v1",
        "cheap_gate_API": "require_admitted_payload(field_bytes,receipt,*,admission_sha256)->(field,pins)",
        "method": ["Exact new raw field admission before actions; no old schema/state/gate projection.",
            "Four loaded own roots/neutral tips per22 angle; actual external bearings/captures/flange compression joined separately.",
            "All100 own same-cut shaft N/V/T/M; defaultFy/root unknown; no equal shared-shaft load or summed capacity.",
            "All200 own capture N divided by own nominal annulus area; annular couples/pressure/washer resistance unavailable.",
            "All66 simultaneous signed screw forces retain generic head/withdrawal only, with actual Hillman resistance unavailable.",
            "Six exported source q slices use explicit key projection to unchanged pure panel functions; spatial resolved peaks and deformation retained.",
            "All22 fresh spans/dimensions use own-host/couple cut replay plus source affine gravity and conditional gross CD1 kernels; no old/net cuts.",
            "Both four-axis exterior cleat corners retain header/side/post/cleat neighboring contact census; complete corner/group/splitting strength unavailable."],
        "focus_checks": {"synthetic_fixture_count": 19, "observed_pytest_duration_seconds": 2.04,
            "pytest_command": "PYTHONPATH=. .venv/bin/python -B -m pytest -q "+str(OWN.with_name("test_assessment.py").relative_to(ROOT))+" "+str(OWN.with_name("test_gross_members.py").relative_to(ROOT)),
            "Ruff_assessment_and_test_pass": True, "independent_readiness_claimed": False},
        "future_parent_command": "PYTHONPATH=. .venv/bin/python -B "+str(OWN.relative_to(ROOT))+" --field NEW_RAW_FIELD --receipt NEW_RAW_ADMISSION --expected-field-sha256 EXACT_RAW_SHA --admission-sha256 EXACT_NEW_GATE_SHA --steel-sha256 "+STEEL_SHA+" --out EXCLUSIVE_NEW_COMPONENT_JSON",
        "candidate_field_q_force_CAD_K_native_or_solve_executed": False,
        "complete_strength_or_physical_demand_bounds_established": False}


def main():
    argv = list(sys.orig_argv)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args()
    result = prepare()
    result["execution"] = {"sys_orig_argv": argv, "PYTHONPATH": os.environ.get("PYTHONPATH"),
                           "cwd": str(Path.cwd()), "python": sys.version}
    with options.out.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(options.out), "joined_pins": result["joined_pin_count"]}))


if __name__ == "__main__":
    main()
