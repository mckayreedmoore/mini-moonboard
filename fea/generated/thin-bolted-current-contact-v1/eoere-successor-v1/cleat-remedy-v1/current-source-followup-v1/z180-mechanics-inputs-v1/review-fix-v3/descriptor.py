"""Authenticate the distinct proposal release contract without altering records.

Reuse frozen691f geometry arithmetic and frozen8ab6 source verification. One
verified AST comparison checks the proposal's exact six release keys against
their authentic all-false contract; the current export and output retain their
own different release keys. No source record is mapped or relabeled.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from types import ModuleType

OWN = Path(__file__).resolve()
V2 = OWN.parent.parent / "review-fix-v2/descriptor.py"
V2_SHA256 = "8ab67c15c544ba1cf1f0209020fb87614072c665a8eaa39dc667a23db5b2823a"
PROPOSAL_RELEASE = {key: False for key in ("candidate_accepted", "climbing_released", "drilling_released",
    "fabrication_released", "geometry_adopted", "structural_accepted")}


def source_ref(path):
    root = OWN.parents[8]
    return {"path": str(path.relative_to(root)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def verified_v2():
    raw = V2.read_bytes()
    if hashlib.sha256(raw).hexdigest() != V2_SHA256:
        raise ValueError("frozen source verification adapter bytes differ")
    module = ModuleType("eoere_z180_frozen_source_verification")
    module.__file__ = str(V2)
    exec(compile(raw, str(V2), "exec"), module.__dict__)  # noqa: S102 -- exact bytes checked above
    return module


def release_contract_tree(raw, filename):
    tree = ast.parse(raw, filename=filename)
    target = ast.parse('layout["release"] == RELEASE', mode="eval").body
    matches = [node for node in ast.walk(tree) if isinstance(node, ast.Compare)
               and ast.dump(node) == ast.dump(target)]
    if len(matches) != 1:
        raise ValueError("exact single frozen proposal release comparison required")
    matches[0].comparators[0] = ast.copy_location(ast.Name(id="PROPOSAL_RELEASE", ctx=ast.Load()), matches[0].comparators[0])
    return ast.fix_missing_locations(tree)


def corrected_frozen_module(v2):
    raw = v2.FROZEN.read_bytes()
    if hashlib.sha256(raw).hexdigest() != v2.FROZEN_SHA256:
        raise ValueError("frozen geometry descriptor source bytes differ")
    tree = release_contract_tree(raw, str(v2.FROZEN))
    module = ModuleType("eoere_z180_frozen_geometry_with_distinct_release_contract")
    module.__file__ = str(v2.FROZEN)
    module.PROPOSAL_RELEASE = dict(PROPOSAL_RELEASE)
    exec(compile(tree, str(v2.FROZEN), "exec"), module.__dict__)  # noqa: S102 -- authenticated exact AST seam
    original_build = module.build_descriptor
    def build_descriptor(bundle):
        corrections = source_correction_record(bundle["input"])
        result = original_build(bundle)
        result["descriptor_source_corrections"] = corrections
        return result
    module.build_descriptor = build_descriptor
    return module


def source_correction_record(inp):
    required = {"source_verification_adapter": source_ref(V2), "layout_release_contract_adapter": source_ref(OWN)}
    for key, ref in required.items():
        if inp["sources"].get(key) != ref:
            raise ValueError("exact input/helper correction provenance join required: " + key)
    return {"frozen_source_verification_adapter": required["source_verification_adapter"],
        "distinct_proposal_release_contract_adapter": required["layout_release_contract_adapter"],
        "original_helper": inp["helper"], "authentic_proposal_release_keys": dict(PROPOSAL_RELEASE),
        "records_relabelled_or_release_granted": False}


def write_descriptor(inputs_path, inputs_sha256, out):
    v2 = verified_v2()
    v2.frozen_module = lambda: corrected_frozen_module(v2)
    return v2.write_descriptor(inputs_path, inputs_sha256, out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--inputs-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(write_descriptor(args.inputs, args.inputs_sha256, args.out), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
