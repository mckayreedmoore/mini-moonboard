"""Clarify the drafted washer-dimension keys; preserve its source/result bytes."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT, LEAF = OWN.parents[6], OWN.parent
ORIGINAL = "4560697b1cd044d61ef7aacaa86656e64518e2227fed6071ab085605333159c9"
DRAFT = "b1bba474bf394a4e740417e4971380550befdcba7dacea1c1a4306a0e356be39"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def worksheet():
    producer = LEAF / "prepare_product_inputs.py"
    draft = LEAF / "product-inputs.json"
    assert sha(producer) == ORIGINAL and sha(draft) == DRAFT
    spec = importlib.util.spec_from_file_location("eoere_preserved_product_conversions", producer)
    method = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(method)
    result = method.worksheet()
    dimensions = result["nonselected_washer_comparison"]["published_dimensions_mm"]
    result["nonselected_washer_comparison"]["published_dimensions_mm"] = {
        key.removesuffix("_inches"): value for key, value in dimensions.items()}
    result["source_sha256"].update({str(OWN.relative_to(ROOT)): sha(OWN), str(draft.relative_to(ROOT)): DRAFT})
    method.verify(result["source_sha256"])
    manifest = method.canonical(result["source_sha256"])
    result["source_manifest_before_after_sha256"] = [manifest, manifest]
    result["schema"] = "eoere_successor_conditional_product_and_interface_worksheet/v2"
    result["finalizer_actual_orig_argv"] = list(sys.orig_argv)
    result["draft_unit_label_correction"] = "The original drafted published_dimensions_mm values were correctly converted to mm but retained nested *_inches key names. The final names omit that suffix; numerical values and all source claims are unchanged. The original draft and producer remain byte-identical."
    result["reproduction_command"] = "uv run python -B " + str(OWN.relative_to(ROOT)) + " --out <fresh-output.json>"
    assert sha(producer) == ORIGINAL and sha(draft) == DRAFT
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    data = (json.dumps(worksheet(), sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with args.out.open("xb") as stream:
        stream.write(data)
    print(json.dumps({"out": str(args.out), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}))


if __name__ == "__main__":
    main()
