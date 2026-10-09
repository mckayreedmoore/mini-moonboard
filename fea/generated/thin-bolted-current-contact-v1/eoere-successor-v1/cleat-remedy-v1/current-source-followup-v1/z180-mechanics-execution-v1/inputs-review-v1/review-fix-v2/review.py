"""Exact two inherited absolute-pin exceptions around the frozen input reviewer."""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
FROZEN = OWN.parent.parent / "review.py"
FROZEN_SHA = "11635d72001de630af7929692bf154a9e7a32d91bf14fb2da663ecbfb432f474"
FROZEN_FILES = {
    FROZEN: FROZEN_SHA,
    FROZEN.with_name("test_review.py"): "8eb19d4fcb96b68f678007c276eed6c6419a20a4e20d7c4f07ce7b9f265f649c",
    FROZEN.with_name("preflight.json"): "00bc002da4de197a9dacceeff17f7b3b6e4bd6ecc24607a8dc9cb11d4f2cb767",
}
INHERITED_ABSOLUTE = {
    "/home/mckay-linux/repos/mini-moonboard-cleanup-backups-2026-10-08/eoere-aligned-wire-cutouts-v1.tar.gz.manifest.json":
        "688acf55c2884086ff14352d6d5ac6377b8f6bcebeb29c0e8275e4ffcdf3a15c",
    "/home/mckay-linux/repos/mini-moonboard/scripts/eoere_2026_adjustments.py":
        "136d7e63f1e337ef8a65421d22d4614b336697cb1b8556ff099995fe26a92821",
}
_loaded = None


def frozen_pins(root):
    sources = {**FROZEN_FILES, OWN: LOADED_SHA}
    for path, digest in sources.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("preserve exact frozen/corrected input-review bytes: " + str(path))
    return {str(path.relative_to(root)): digest for path, digest in sources.items()}


def original():
    global _loaded
    for path, digest in {**FROZEN_FILES, OWN: LOADED_SHA}.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("preserve exact frozen/corrected input-review bytes: " + str(path))
    if _loaded is None:
        spec = importlib.util.spec_from_file_location("z180_saved_input_frozen_independent_review", FROZEN)
        _loaded = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = _loaded
        spec.loader.exec_module(_loaded)
        _loaded.absolute_fix_original_verify = _loaded.verify_pins
        _loaded.absolute_fix_original_preflight = _loaded.preflight
    return _loaded


def verify_pins(frozen, pins):
    additions = frozen_pins(frozen.ROOT)
    for path, digest in additions.items():
        frozen.require(path not in pins or pins[path] == digest, "corrected input-review identity pin conflict")
    for path, digest in pins.items():
        if Path(path).is_absolute():
            frozen.require(INHERITED_ABSOLUTE.get(path) == digest and frozen.sha(Path(path)) == digest,
                           "exact inherited absolute input-review source differs: " + path)
        else:
            frozen.absolute_fix_original_verify({path: digest})
    frozen.absolute_fix_original_verify(additions)
    pins.update(additions)
    frozen_pins(frozen.ROOT)
    return pins


def preflight(frozen):
    result = frozen.absolute_fix_original_preflight()
    result["source_sha256"] = verify_pins(frozen, frozen.merge_pins(result["source_sha256"], INHERITED_ABSOLUTE))
    result["inherited_absolute_source_correction"] = {
        "exact_path_and_sha256_exceptions": dict(INHERITED_ABSOLUTE),
        "ordinary_relative_references_and_verification_unchanged": True,
        "independent_math_source_joins_and_authentication_unchanged": True,
        "frozen_review": {"path": str(FROZEN.relative_to(frozen.ROOT)), "sha256": FROZEN_SHA}}
    return result


@contextmanager
def corrected_context(frozen):
    original()
    frozen.require(frozen.OWN == FROZEN and frozen.LOADED_SHA == FROZEN_SHA, "input-review correction must be unnested")
    try:
        with patch.object(frozen, "OWN", OWN), patch.object(frozen, "LOADED_SHA", LOADED_SHA), \
                patch.object(frozen, "verify_pins", side_effect=lambda pins: verify_pins(frozen, pins)), \
                patch.object(frozen, "preflight", side_effect=lambda: preflight(frozen)):
            yield frozen
    finally:
        frozen_pins(frozen.ROOT)


def main(argv=None):
    frozen = original()  # Stdlib definitions only; main reserves before dependent imports.
    with corrected_context(frozen):
        return frozen.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
