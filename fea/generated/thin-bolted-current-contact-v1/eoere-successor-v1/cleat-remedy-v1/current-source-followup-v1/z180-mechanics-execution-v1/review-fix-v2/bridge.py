"""Exact shaft-roster intake correction around frozen source adapter fc95da9c.

The original adapter owns every source join, numerical hook and orchestration.
This wrapper adds a unique/exact authenticated 100-axis check and its own source
identity. It performs no candidate work on import and supplies no readiness.
"""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from contextlib import ExitStack, contextmanager
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
FROZEN = OWN.parent.parent / "bridge.py"
FROZEN_SHA = "fc95da9c8b81b8153813b6c98895401c4f4b5cf96e61d68973ba417c386917c6"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
_original = None


def original():
    global _original
    for path, digest in ((FROZEN, FROZEN_SHA), (OWN, LOADED_SHA)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("exact original/corrected adapter bytes changed")
    if _original is None:
        spec = importlib.util.spec_from_file_location("eoere_z180_source_adapter_frozen_fc95", FROZEN)
        _original = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = _original
        spec.loader.exec_module(_original)
    return _original


def complete_axes(a, exported, delegate):
    parent = a.read_ref(a.PARENT_DESCRIPTOR)
    inherited = [row["axis_id"] for row in parent["shafts"]]
    moved = a.manifest()["declared_changes"]["axis_ids"]
    axes = [row["axis_id"] for row in exported["shafts"]]
    a.require(len(inherited) == len(set(inherited)) == 100 and len(moved) == len(set(moved)) == 4
              and set(moved) <= set(inherited) and len(axes) == len(set(axes)) == 100
              and set(axes) == set(inherited) and set(moved) <= set(axes),
              "exact unique 100 authenticated parent axes including all four moved axes required")
    return delegate(exported)


@contextmanager
def corrected_context(a):
    original()
    a.require(a.OWN == FROZEN and a.LOADED_SHA == FROZEN_SHA, "source correction must be unnested and serialized")
    validate, source_pins = a.validate_descriptor, a.source_pins
    def pins(w, b, extra=None, *, method=None):
        additions = dict(extra or {})
        path = str(FROZEN.relative_to(a.ROOT))
        a.require(path not in additions or additions[path] == FROZEN_SHA, "frozen source adapter pin conflict")
        additions[path] = FROZEN_SHA
        return source_pins(w, b, additions, method=method)
    try:
        with ExitStack() as stack:
            for name, value in {"OWN": OWN, "LOADED_SHA": LOADED_SHA,
                                "validate_descriptor": lambda exported: complete_axes(a, exported, validate),
                                "source_pins": pins}.items():
                stack.enter_context(patch.object(a, name, value))
            yield a
    finally:
        original()


def main(argv=None):
    a = original()
    with corrected_context(a):
        return a.main(argv)


def run_case(args):
    a = original()
    with corrected_context(a):
        return a.run_case(args)


def audit(path):
    a = original()
    with corrected_context(a):
        return a.audit(path)


def require_admitted_payload(field_bytes, receipt, *, admission_sha256):
    a = original()
    with corrected_context(a):
        return a.require_admitted_payload(field_bytes, receipt, admission_sha256=admission_sha256)


if __name__ == "__main__":
    raise SystemExit(main())
