"""Repeat the frozen offline audit with Fortran's omitted-E exponent spelling."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
FROZEN_VERIFIER_SHA = "bcc10408e3ecdc65731ce928cba959808964b7daf61eb35fe8668f6a117e3170"
EXECUTION_SHA = "c09e9d37dff3f8702c5a651f78f7ab44f508265ea82c5f2ef3f0019cb209c49c"
SOURCE = "https://www.intel.com/content/www/us/en/docs/fortran-compiler/developer-guide-reference/2023-0/e-and-d-editing.html"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit():
    if sha(HERE / "verifier.py") != FROZEN_VERIFIER_SHA or sha(HERE / "execution.json") != EXECUTION_SHA:
        raise ValueError("Frozen verifier or native execution changed")
    spec = importlib.util.spec_from_file_location("frozen_fixture_verifier", HERE / "verifier.py")
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    parse_original = original.number
    spellings = {}

    def number(value):
        # Fortran Ew.d without explicit Ee emits +/-nnn without E for |exp|>99.
        match = re.fullmatch(r"\s*([+-]?(?:\d+\.\d*|\.\d+))([+-]\d{3})\s*", value)
        if match and abs(int(match[2])) > 99:
            normalized = match[1] + "E" + match[2]
            spellings[value] = normalized
            return parse_original(normalized)
        return parse_original(value)

    original.number = number
    result = original.audit()
    result.update(
        audit_revision="attempt02_numeric_parser_only",
        frozen_verifier_sha256=FROZEN_VERIFIER_SHA,
        execution_sha256=EXECUTION_SHA,
        prior_failed_audit_sha256=sha(HERE / "verifier.json"),
        verifier_attempt02_sha256=sha(Path(__file__)),
        parser_reference=SOURCE,
        normalized_exponent_spellings=spellings,
        acceptance_gates_changed=False,
        native_solver_rerun=False,
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = audit()
    if args.write:
        with (HERE / "verifier-attempt02.json").open("x") as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
            stream.write("\n")
    print(json.dumps({"status": result["status"],
                      "cases": {k: {a:b for a,b in v.items() if a in ("status", "error", "accepted_states", "iterations")}
                                for k,v in result["cases"].items()},
                      "normalized_spelling_count": len(result["normalized_exponent_spellings"])}))
    raise SystemExit(0 if result["status"] == "PASS_METHOD_FIXTURE" else 1)
