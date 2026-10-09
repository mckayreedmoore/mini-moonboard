"""Source-only method-reference equality around frozen v3 preflight.

Each supplied input, review, manifest, panel bank and descriptor-export reference
must equal the corresponding method-bound reference. Missing references remain
explicitly unchecked. Producer/admission491653 and all arithmetic stay intact.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
BASE = OWN.parent.parent
V3 = BASE / "preflight-fix-v3/preflight.py"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
FROZEN = {
    V3: "a557f8ee72a211f809220f5ac25621e2c7a6c0d9fdfdadd94b95cc8d31c0254c",
    V3.with_name("test_preflight.py"): "ff06c0b5f2b8d951f72f6f071141633950f82c50c904388ceb3f1386ecfb4334",
    V3.with_name("all-bindings.json"): "780b589d2381fa2d469ff075f500f744142207957de1d663b1f8c4c3f801624e",
    V3.with_name("verification.json"): "c5348a6100dfb2bae65e52499044a3d41c60a4fe5d351a4d83f46e40bb1107fd",
}
REVIEWS = {"correctness": "786118273cf2f1004fde447f801a80834244629786a6491501a6726360afa62f",
           "testing": "bbfab7047ae927cece449f54599523d481f9a18f48728d4f3c99530e3e7c5da2",
           "structure": "a5261622c8c6280f748ce610055686f9d8128542145ee2fc1dd4f395897e2294"}
REFERENCE_KEYS = ("inputs", "input_review", "source_manifest", "panel_bank", "source_export")
_v3 = None


def frozen_pins():
    sources = {**FROZEN, OWN: LOADED_SHA,
        **{BASE.parent / "current-force-bridge-review-v3" / name / "receipt.json": sha for name, sha in REVIEWS.items()}}
    for path, sha in sources.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != sha:
            raise ValueError("preserve frozen source-preflight evidence: " + str(path))
    return {str(path.relative_to(ROOT)): sha for path, sha in sources.items()}


def previous():
    global _v3
    frozen_pins()
    if _v3 is None:
        spec = importlib.util.spec_from_file_location("eoere_method_bound_preflight_frozen_v3", V3)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _v3 = module
    return _v3


def method_reference_bindings(args, b):
    supplied = {key: {"path": b.bundle.artifact_path(getattr(args, key).resolve()),
                      "sha256": getattr(args, key + "_sha256")}
        for key in REFERENCE_KEYS
        if getattr(args, key) is not None and getattr(args, key + "_sha256") is not None}
    if args.method_input is None or args.method_input_sha256 is None:
        return {"method_provided": False, "checked": {}, "unchecked": list(REFERENCE_KEYS),
                "complete": False, "reason": "No complete method reference supplied."}
    method = b.read_method(args.method_input, args.method_input_sha256)
    bound = {"inputs": method["input"], "input_review": method["input_review"],
             "source_manifest": method["source_manifest"], "panel_bank": method["panel_bank"]}
    geometry = b.read_ref(method["input"])["geometry"]
    b.require(geometry["report"] == method["geometry"] and geometry["source_manifest"] == method["source_manifest"],
              "method-bound input geometry/manifest references differ")
    bound["source_export"] = geometry["cached_source_export"]
    for key, ref in supplied.items():
        b.require(ref == bound[key], "supplied " + key + " reference differs from method binding")
    return {"method_provided": True, "method": method["input_record"], "checked": supplied,
            "unchecked": [key for key in REFERENCE_KEYS if key not in supplied],
            "complete": len(supplied) == len(REFERENCE_KEYS)}


def preflight(args, s, w, b):
    w.require(args.mode == "preflight" and not args.run, "supplement is source-preflight-only")
    bindings = method_reference_bindings(args, b)
    result = s.preflight(args, w, b)
    result["source_sha256"] = b.source_pins({**result["source_sha256"], **frozen_pins()})
    result["method_reference_bindings"] = bindings
    result["method_binding_preflight_supplement"] = {"path": str(OWN.relative_to(ROOT)), "sha256": LOADED_SHA,
        "reference_equality_checks_only": True, "producer_authenticator_math_or_tolerances_changed": False}
    frozen_pins()
    return result


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    early = argparse.ArgumentParser(description=__doc__, add_help=False)
    early.add_argument("--out", type=Path, required=True)
    args, _ = early.parse_known_args(argv)
    s = previous()  # Both supplements import stdlib only.
    w = s.corrected()
    with w.reserve(args.out) as output:
        b = w.frozen()
        with w.corrected_context(b):
            result = preflight(b.parse_args(argv), s, w, b)
            output.write(b.core.serial(result))
        print(json.dumps({"output": str(output.path), "sha256": hashlib.sha256(output.path.read_bytes()).hexdigest(),
            "missing": result["missing"], "method_reference_bindings_complete": result["method_reference_bindings"]["complete"],
            "production_readiness_claimed": False}))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
