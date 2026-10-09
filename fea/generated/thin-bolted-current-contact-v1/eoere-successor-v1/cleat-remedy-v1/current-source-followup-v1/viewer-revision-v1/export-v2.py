"""Supported preflight/export entrypoint; retain all original v1 evidence.

The narrow added gate joins the parent's reviewed native-result digest to the
actual source pin before the frozen exporter or any native display work runs.
Current output is verified without another BREP import or tessellation.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

OWN = Path(__file__).resolve()
HERE = OWN.parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
ORIGINAL_SHA = "8e6511c73d8f38e749476d3e783cf67c8a291ebb904a8ab9a571e6c0828cac15"


def read(path):
    return json.loads(Path(path).read_bytes(), parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def guarded_original():
    require(sha(HERE / "export.py") == ORIGINAL_SHA, "original exporter changed")
    guard = read(HERE / "parent-readiness-v2.json")
    require(guard["schema"] == "eoere_lower_cleat_z180_display_parent_readiness/v2"
            and guard["exporter_sha256"] == sha(OWN)
            and guard["only_four_saved_BREP_display_tessellations"] is True
            and guard["native_mechanics_or_full_frame_CAD_authorized"] is False
            and guard["geometry_adoption_authorized_by_this_file"] is False,
            "source-bound v2 parent readiness required")
    spec = importlib.util.spec_from_file_location("z180_frozen_original_export", HERE / "export.py")
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    original.verify(guard["source_sha256"])
    inp = read(HERE / "inputs.json")
    parent = read(HERE / "parent-readiness.json")
    expected = inp["source_sha256"][inp["native_result"]]
    require(parent["reviewed_native_result_sha256"] == expected
            and guard["reviewed_native_result_sha256"] == expected
            and sha(ROOT / inp["native_result"]) == expected,
            "parent review and consumed native-result digest differ")
    prepare_v1 = original.prepare

    def prepare():
        values = prepare_v1()
        pins = values[1]
        pins.update(guard["source_sha256"])
        pins[str(OWN.relative_to(ROOT))] = guard["exporter_sha256"]
        pins[str((HERE / "parent-readiness-v2.json").relative_to(ROOT))] = sha(HERE / "parent-readiness-v2.json")
        original.verify(pins)
        return values

    original.prepare = prepare
    return original


def verify_current():
    original = guarded_original()
    inp, pins, runtime, descriptor, bodies, audit = original.prepare()
    out = HERE / "runs-v1/export01"
    report = read(out / "export-result.json")
    require(report["schema"] == "eoere_lower_cleat_z180_display_export/v1"
            and report["status"] == "DISPLAY_EXPORT_COMPLETE"
            and report["native_cuts_Boolean_or_mechanics"] is False
            and report["saved_response_transferred"] is False
            and report["release"] == original.FLAGS,
            "original display scope differs")
    original.verify(report["source_sha256"])
    for name in ("layout.json", "scene.json.gz"):
        row = report["output"][name]
        require(row["path"] == str((out / name).relative_to(ROOT))
                and sha(out / name) == row["sha256"]
                and (out / name).stat().st_size == row["bytes"], "original output binding differs")
    require(read(out / "layout.json") == descriptor, "current proposed descriptor differs")
    original.verify(pins)
    return {"schema": "eoere_lower_cleat_z180_v2_source_and_output_verification/v1",
            "passed": True, "source_sha256": pins, "runtime": runtime,
            "parent_review_consumed_native_digest_joined": True,
            "original_export_sha256": sha(out / "export-result.json"),
            "original_outputs": report["output"], "saved_receiver_audit": audit,
            "native_geometry_or_mechanics_executed": False, "release": original.FLAGS}


if __name__ == "__main__":
    import sys

    if sys.argv[1:] == ["--verify-only"]:
        result = verify_current()
        with (HERE / "source-verification-v2.json").open("x") as stream:
            json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
        print(json.dumps({"passed": True, "native_geometry_or_mechanics_executed": False}))
    elif not sys.argv[1:]:
        guarded_original().main()
    else:
        raise ValueError("only --verify-only or a fresh fixed-destination export is supported")
