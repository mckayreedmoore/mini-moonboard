"""Prepare width-grain operators for the frozen hypothetical 98-screw packet.

Reuse the frozen four-panel C3D20 reassembly/KKT producer, changing only its
input-directory and expected model identity. Its full B projection includes
all appended screw rows; no old-grain added compliance is appended afterward.
The parent owns execution in the serialized mechanics slot.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "pyproject.toml").exists())
SOURCE = HERE.parent / "panel-attachment/results/count20-operators-attempt01"
PRODUCER = HERE / "panel_orientation.py"
PINS = {
    PRODUCER: "3268faa94ba050d82d66df1393fc4b8e4d9e4a79b87412fe0f4cfdbf72dd7e93",
    SOURCE / "operator-assessment.json": "852891ede7be6d88e0b59546f0e01fed4e90b905c2ae6fbb93bfc1772082ddb9",
    SOURCE / "model.json": "5c31f8c471e8f0772d280b9679c72368ded28d932375eed5b9edff7445db18e2",
    SOURCE / "operators.npz": "6b87b74f8a14c4ca794cc6e61c30969d0d2eee18ac1dd42fb67965ef06da4ac7",
    SOURCE / "B.npz": "e8714805be6e190be304e4b2768d67730ca7a1050e31cb1251ebcdf6263b92ee",
    SOURCE / "row-identities.json": "625c87215a41f5c4eea51c28e3253041825f2a098c4105572b434ac950c3b648",
    SOURCE / "model-inputs.json": "603f06db9b52aff9ad3422dcdf9e4f03928ea2a5ec68ff833494c79132258687",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, document):
    path.write_text(json.dumps(document, indent=2, allow_nan=False) + "\n")


def adapted_source():
    """Retarget two explicit source identities; retain every mechanics operation."""
    text = PRODUCER.read_text()
    substitutions = {
        'SOURCE = HERE / "operators-attempt02"':
            'SOURCE = HERE.parent / "panel-attachment/results/count20-operators-attempt01"',
        '"b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626"':
            '"5c31f8c471e8f0772d280b9679c72368ded28d932375eed5b9edff7445db18e2"',
    }
    for old, new in substitutions.items():
        if text.count(old) != 1:
            raise ValueError("Frozen orientation producer adaptation site changed")
        text = text.replace(old, new, 1)
    return text, substitutions


def build(output):
    """Execute only on the parent's reserved projection slot, with fresh output."""
    if output.exists():
        raise ValueError("Preserve prior packets; use a fresh output directory")
    pins = {**PINS, Path(__file__): sha(Path(__file__))}
    for path, expected in pins.items():
        if sha(path) != expected:
            raise ValueError(f"Changed frozen input: {path.relative_to(ROOT)}")
    inputs = json.loads((SOURCE / "model-inputs.json").read_text())
    screws = [c for c in inputs["connections"] if c["kind"] == "panel_screw"]
    if len(screws) != 98:
        raise ValueError("Expected 80 main-panel plus 18 kicker screws")
    text, substitutions = adapted_source()
    # ponytail: two pinned identity substitutions reuse the complete existing
    # mechanics producer; its actual adapted source is preserved for audit.
    namespace = {"__file__": str(Path(__file__).resolve()),
                 "__name__": "frozen_count20_panel_orientation"}
    exec(compile(text, str(PRODUCER), "exec"), namespace)  # noqa: S102 -- hash-pinned source, two checked substitutions
    namespace["build"](output)
    assessment = json.loads((output / "operator-assessment.json").read_text())
    if len(assessment["bodies_recomputed"]) != 4:
        raise ValueError("Require all four main-panel native-K comparisons")
    source_assessment = json.loads((SOURCE / "operator-assessment.json").read_text())
    for path, expected in pins.items():
        if sha(path) != expected:
            raise ValueError(f"Input changed during projection: {path.relative_to(ROOT)}")
    assessment["source_sha256"].update({str(p.relative_to(ROOT)): h for p, h in pins.items()})
    assessment.update(
        schema="hypothetical_count20_four_main_panel_width_grain_comparison/v1",
        producer_sha256=pins[Path(__file__)],
        old_scalar_row_count=source_assessment["old_scalar_row_count"],
        appended_scalar_row_count=source_assessment["appended_scalar_row_count"],
        hypothetical_panel_screw_count=98,
        proposed_main_panel_screw_count=20,
        added_hardware_mass_included=False,
        reviewed_geometry_changed=True,
        panel_benchmark_recomputed=False,
    )
    assessment["limits"].append(
        "All four panel H/e contributions use the entire 98-screw packet B, "
        "including appended rows and cross terms; D/W/F and receiver contributions "
        "remain unchanged. No old-grain panel benchmark is copied or adopted."
    )
    (output / "adapted-orientation.py.snapshot").write_text(text)
    write(output / "adaptation.json", {
        "source_producer_sha256": PINS[PRODUCER],
        "substitutions": substitutions,
        "adapted_source_sha256": sha(output / "adapted-orientation.py.snapshot"),
        "mechanics_algorithm_changed": False,
        "frame_solve_executed": False,
        "native_launch": False,
    })
    assessment["output_sha256"].update({name: sha(output / name) for name in
                                      ("adapted-orientation.py.snapshot", "adaptation.json")})
    write(output / "operator-assessment.json", assessment)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    lock = ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ledger = json.loads(lock.with_suffix(".json").read_text())
        if ledger["slot"]["state"] != "idle":
            raise ValueError("Shared mechanics slot occupied")
        build(args.output.resolve())
