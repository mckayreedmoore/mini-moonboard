"""Separate descriptor-review release keys around the frozen Z180 consumer.

Only its review-release comparison changes. Raw receipts, mechanics field and
output release rules, admission, source joins and deferred reducers stay intact.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
FROZEN = OWN.parent.parent / "consume.py"
FROZEN_SHA = "673498ce0cb1cb95bf6f263e2710b357f9792eaf8d12020c25a0812dc12a1d80"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
DESCRIPTOR_RELEASE = dict.fromkeys(("candidate_admitted", "climbing", "complete_joint_resistance",
                                    "fabrication", "physical_contact", "structural"), False)
_original = None
_original_authenticate = None


def original():
    global _original, _original_authenticate
    for path, expected in ((FROZEN, FROZEN_SHA), (OWN, LOADED_SHA)):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("exact original/corrected consumer bytes changed")
    if _original is None:
        spec = importlib.util.spec_from_file_location("eoere_z180_component_frozen_673498", FROZEN)
        _original = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = _original
        spec.loader.exec_module(_original)
        _original_authenticate = _original.authenticate
    return _original


def corrected_authenticate(a):
    """Compile the exact original function with one declared AST comparison fix."""
    raw = FROZEN.read_bytes()
    a.require(hashlib.sha256(raw).hexdigest() == FROZEN_SHA, "exact original compiler bytes changed")
    functions = [n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef) and n.name == "authenticate"]
    a.require(len(functions) == 1, "one frozen authenticate function required")
    function = functions[0]
    expected = ast.dump(ast.parse("review['release'] == RELEASE", mode="eval").body)
    comparisons = [n for n in ast.walk(function) if isinstance(n, ast.Compare) and ast.dump(n) == expected]
    a.require(len(comparisons) == 1, "one exact descriptor-review release comparison required")
    comparisons[0].comparators[0] = ast.Name(id="DESCRIPTOR_RELEASE", ctx=ast.Load())
    namespace = {**vars(a), "DESCRIPTOR_RELEASE": dict(DESCRIPTOR_RELEASE)}
    tree = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    exec(compile(tree, str(FROZEN), "exec"), namespace)  # noqa: S102
    corrected = namespace["authenticate"]

    def authenticate(*args, **kwargs):
        original()
        result = corrected(*args, **kwargs)
        pins = result[3]
        a.merge(pins, {str(OWN.relative_to(a.ROOT)): LOADED_SHA})
        a.verify(pins)
        return result
    return authenticate


@contextmanager
def corrected_context():
    a = original()
    with a.LOCK:
        a.require(a.authenticate is _original_authenticate, "consumer correction must be unnested and serialized")
        try:
            with patch.object(a, "authenticate", corrected_authenticate(a)):
                yield a
        finally:
            original()


def consume(*args, **kwargs):
    with corrected_context() as a:
        return a.consume(*args, **kwargs)


def consume_to_file(*args, **kwargs):
    with corrected_context() as a:
        return a.consume_to_file(*args, **kwargs)


def main(argv=None):
    with corrected_context() as a:
        return a.main(argv)


if __name__ == "__main__":
    main()
