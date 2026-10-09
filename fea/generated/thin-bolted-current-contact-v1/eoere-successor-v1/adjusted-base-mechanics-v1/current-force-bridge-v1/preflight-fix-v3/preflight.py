"""Source-only preflight supplement retaining the validated raw-input pin.

Two exact AST substitutions reuse the frozen preflight: name the pins returned
by read_inputs, then pass those pins to the unchanged review authenticator.
The reviewed producer/admission491653, input, review and method stay intact.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
BASE = OWN.parent.parent
CORRECTED = BASE / "review-fix-v2/bridge.py"
CORRECTED_SHA = "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
FROZEN = {
    BASE / "bridge.py": "ddc85386050d97145597dc720bef78634c9b326f0878aced8c02c8df4710c05b",
    BASE / "test_bridge.py": "72cdd692b40df93e2a6a194e31d9bd03fe7125baf6fb605a09b66954bbecacf6",
    BASE / "source-preflight.json": "4118719a61da4645085f4840b1888ac6df600df2307edc8c0d40ffb79d4eafe0",
    BASE / "verification.json": "7ca9a676dd1c7b1ae41a4408caeae6d0d22c0ee57da43095663b8587238d5fab",
    CORRECTED: CORRECTED_SHA,
    CORRECTED.with_name("test_bridge.py"): "cdaf6e63a542b738fd81b99e4c211952dd46765fb8c2082a1d43c0d977b88c90",
    CORRECTED.with_name("source-preflight.json"): "158b2fd603cabac3d5e39ac81f726da251ce6a393b797e7e047daef3dee85fdc",
    CORRECTED.with_name("verification.json"): "18903e345a4c7f59ecbf0036cd68946733981f8a8b9de29a3fef0a63b68a3f7a",
}
REVIEWS = {"correctness": "0ee88c66b883d762674621983c962e109a48e7efc4eaa939a29278bded529e95",
           "testing": "9db34a9c26936df6ce8bec97b1b41294ead2f53e02e14eead8dd40b402ad5d93",
           "structure": "270ad77e1c6b865383e1597bc21e72001aebf931f6747c2a2a343d1c4e13894e"}
_corrected = None


def corrected():
    global _corrected
    if hashlib.sha256(CORRECTED.read_bytes()).hexdigest() != CORRECTED_SHA:
        raise ValueError("preserve reviewed producer/admission wrapper")
    if _corrected is None:
        spec = importlib.util.spec_from_file_location("eoere_preflight_only_frozen_corrected_wrapper", CORRECTED)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _corrected = module
    return _corrected


def frozen_pins(w):
    sources = {**FROZEN, OWN: LOADED_SHA,
        **{BASE.parent / "current-force-bridge-review-v2" / name / "receipt.json": sha for name, sha in REVIEWS.items()}}
    for path, sha in sources.items():
        w.checked_bytes(path, sha)
    return {str(path.relative_to(ROOT)): sha for path, sha in sources.items()}


def compile_preflight(w, b):
    raw = w.checked_bytes(w.FROZEN, w.FROZEN_SHA)
    tree = w.checked_ast(w.FROZEN_SHA).parse(raw)
    node = copy.deepcopy(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "preflight"))
    assignment = ast.parse("data, _ = read_inputs(args.inputs, args.inputs_sha256)").body[0]
    pin_call = ast.parse('source_pins(data["source_sha256"])', mode="eval").body
    counts = {"returned_raw_input_pins": 0, "authenticated_raw_input_pins": 0}
    for item in ast.walk(node):
        if isinstance(item, ast.Assign) and ast.dump(item) == ast.dump(assignment):
            item.targets[0].elts[1].id = "input_pins"
            counts["returned_raw_input_pins"] += 1
        elif isinstance(item, ast.Call) and ast.dump(item) == ast.dump(pin_call):
            item.args[0] = ast.Name(id="input_pins", ctx=ast.Load())
            counts["authenticated_raw_input_pins"] += 1
    w.require(counts == {"returned_raw_input_pins": 1, "authenticated_raw_input_pins": 1},
              "exact source-only raw-input pin seam differs")
    context = dict(vars(b))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(OWN), "exec"), context)  # noqa: S102
    return context["preflight"]


def preflight(args, w, b):
    w.require(args.mode == "preflight" and not args.run, "supplement is source-preflight-only")
    pins = frozen_pins(w)
    result = compile_preflight(w, b)(args)
    result["source_sha256"] = b.source_pins({**result["source_sha256"], **pins})
    result["source_preflight_supplement"] = {
        "path": str(OWN.relative_to(ROOT)), "sha256": LOADED_SHA,
        "frozen_producer_and_admission": {"path": str(CORRECTED.relative_to(ROOT)), "sha256": CORRECTED_SHA},
        "validated_read_inputs_returned_pins_retained_for_review_authentication": True,
        "review_authenticator_or_source_aliases_changed": False,
        "producer_admission_mechanics_or_tolerances_changed": False}
    result["source_preflight_execution"] = {"command": list(sys.orig_argv), "source_preflight_only": True}
    frozen_pins(w)
    return result


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    early = argparse.ArgumentParser(description=__doc__, add_help=False)
    early.add_argument("--out", type=Path, required=True)
    args, _ = early.parse_known_args(argv)
    w = corrected()  # This wrapper imports stdlib only; frozen() is still lazy.
    with w.reserve(args.out) as output:
        frozen_pins(w)
        b = w.frozen()
        with w.corrected_context(b):
            result = preflight(b.parse_args(argv), w, b)
            output.write(b.core.serial(result))
        print(json.dumps({"output": str(output.path), "sha256": hashlib.sha256(output.path.read_bytes()).hexdigest(),
                          "missing": result["missing"], "production_readiness_claimed": False}))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
