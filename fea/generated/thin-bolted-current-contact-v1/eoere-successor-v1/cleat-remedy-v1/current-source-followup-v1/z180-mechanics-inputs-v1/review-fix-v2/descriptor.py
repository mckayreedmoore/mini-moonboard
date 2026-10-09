"""Preserve exact inherited absolute provenance pins in the frozen descriptor.

The original source-only geometry arithmetic and output reservation are reused.
Only its source-closure verifier is scoped to accept the two exact absolute
references already present in authenticated current descriptor0f7e95. Their
original path spellings and hashes remain unchanged in the resulting closure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType

OWN = Path(__file__).resolve()
FROZEN = OWN.parent.parent / "descriptor.py"
FROZEN_SHA256 = "691f46fd47b2e952e3b8911d61ddf855d9806c20190f77a1d6e0f57ad022a9ac"
INHERITED_ABSOLUTE_PINS = {
    "/home/mckay-linux/repos/mini-moonboard-cleanup-backups-2026-10-08/eoere-aligned-wire-cutouts-v1.tar.gz.manifest.json":
        "688acf55c2884086ff14352d6d5ac6377b8f6bcebeb29c0e8275e4ffcdf3a15c",
    "/home/mckay-linux/repos/mini-moonboard/scripts/eoere_2026_adjustments.py":
        "136d7e63f1e337ef8a65421d22d4614b336697cb1b8556ff099995fe26a92821",
}


def frozen_module():
    raw = FROZEN.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN_SHA256:
        raise ValueError("frozen geometry descriptor source bytes differ")
    module = ModuleType("eoere_z180_frozen_geometry_descriptor")
    module.__file__ = str(FROZEN)
    exec(compile(raw, str(FROZEN), "exec"), module.__dict__)  # noqa: S102 -- exact frozen bytes checked immediately above
    return module


def verify_pins(frozen, pins, root, *, inherited_absolute=INHERITED_ABSOLUTE_PINS):
    for path, digest in pins.items():
        if Path(path).is_absolute():
            frozen.require(inherited_absolute.get(path) == digest and frozen.sha(Path(path)) == digest,
                           "exact inherited absolute source bytes differ: " + path)
        else:
            frozen.exact_ref({"path": path, "sha256": digest}, root)


@contextmanager
def source_context(frozen):
    previous = frozen.verify
    def verify(pins, root=frozen.ROOT):
        # Reauthenticate the reused implementation on both closure checks.
        frozen.require(frozen.sha(FROZEN) == FROZEN_SHA256, "frozen geometry descriptor source bytes differ")
        verify_pins(frozen, pins, root)
    frozen.verify = verify
    try:
        yield frozen
    finally:
        frozen.verify = previous


def write_descriptor(inputs_path, inputs_sha256, out):
    frozen = frozen_module()
    with source_context(frozen):
        return frozen.write_descriptor(inputs_path, inputs_sha256, out)


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
