"""Bind the canonical output parent before the frozen exclusive reservation.

Only the parent's resolved path is joined with the original leaf name. The
leaf remains unresolved so existing files and dangling links are rejected by
the frozen writer's exclusive open. Frozen v4 geometry arithmetic, inode and
STARTED/FAILED guards are reused unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from types import ModuleType

OWN = Path(__file__).resolve()
V4 = OWN.parent.parent / "review-fix-v4/descriptor.py"
V4_SHA256 = "a7b27b82eb3bafc698d371ce2f4b2e71c89cc4306459cd795ed1ca1c983ae106"


def bind_output(out):
    out = Path(os.path.abspath(out))
    canonical_parent = out.parent.resolve()
    owned_runs = (OWN.parent.parent / "runs-v1").resolve()
    if not canonical_parent.is_relative_to(owned_runs):
        raise ValueError("full descriptor belongs under this packet runs-v1")
    return canonical_parent / out.name


def verified_v4():
    raw = V4.read_bytes()
    if hashlib.sha256(raw).hexdigest() != V4_SHA256:
        raise ValueError("frozen mixed-contact adapter bytes differ")
    module = ModuleType("eoere_z180_frozen_mixed_contact_adapter")
    module.__file__ = str(V4)
    exec(compile(raw, str(V4), "exec"), module.__dict__)  # noqa: S102 -- exact bytes checked immediately above
    return module


def corrected_v4():
    v4 = verified_v4()
    original = v4.corrected_v3
    def corrected_v3():
        v3 = original()
        original_record = v3.source_correction_record
        def record(inp):
            value = original_record(inp)
            ref = v3.source_ref(OWN)
            if inp["sources"].get("canonical_output_adapter") != ref:
                raise ValueError("exact canonical-output correction provenance required")
            value["canonical_output_adapter"] = ref
            return value
        v3.source_correction_record = record
        return v3
    v4.corrected_v3 = corrected_v3
    return v4


def write_descriptor(inputs_path, inputs_sha256, out):
    # Bind before loading source adapters, mkdir, exclusive open or callbacks.
    bound = bind_output(out)
    return corrected_v4().write_descriptor(inputs_path, inputs_sha256, bound)


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
