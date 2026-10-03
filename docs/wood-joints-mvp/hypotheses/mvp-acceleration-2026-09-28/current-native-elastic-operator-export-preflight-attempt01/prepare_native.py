"""Parent preparation only: freeze the source-reviewed free-solid export coupon."""
from pathlib import Path
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from fea.horizontal_panel_frame import Structure
from fea.wood_joint_reduced_native import freeze


def prepare():
    pins = json.loads((HERE / "source-pins.json").read_text())
    for item in (pins["manual"], pins["pinned_runtime_profile"]):
        assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    deck = (HERE / "coupon-free-c3d20-matrixstorage.inp").read_text()
    model = Structure()
    card = ""
    connectivity = []
    for line in deck.splitlines():
        if line.startswith("*"):
            card = line.split(",")[0]
        elif card == "*NODE":
            fields = line.split(",")
            assert model.node(list(map(float, fields[1:]))) == int(fields[0])
        elif card == "*ELEMENT":
            connectivity.extend(map(int, line.split(",")))
    assert connectivity == [1, *range(1, 21)]
    assert model.element("C3D20", connectivity[1:], "SOLID") == connectivity[0]
    metadata = {
        "scope": "free unit C3D20 native MATRIXSTORAGE known-answer export only",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "synthetic_only": True,
        "material": {"E_N_per_mm2": 1.0, "nu": 0.25, "density_consistent_units": 1.0},
        "expected_equations": 60, "expected_rigid_modes": 6,
        "expected_shear_energy_N_mm": 0.00002,
        "expected_translation_mass": 1.0,
        "frame_ready": False, "mechanical_acceptance": False,
    }
    target = HERE.parent / "current-free-c3d20-matrix-export-native-attempt01"
    sources = [HERE / name for name in ("README.md", "source-pins.json", "coupon-free-c3d20-matrixstorage.inp", "matrix_export_oracle.py", "prepare_native.py")]
    packet = freeze(target, model, metadata, sources, deck_text=deck)
    print(json.dumps({"directory": str(target.relative_to(ROOT)), "scope": packet["scope"]}))


if __name__ == "__main__":
    prepare()
