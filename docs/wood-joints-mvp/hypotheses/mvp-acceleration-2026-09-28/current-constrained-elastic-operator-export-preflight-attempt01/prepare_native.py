"""Parent-only preparation of the constrained, rotated-material export coupon."""
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from fea.horizontal_panel_frame import Structure
from fea.wood_joint_reduced_native import digest, freeze


def prepare():
    pins = json.loads((HERE / "source-pins.json").read_text())
    for name in ("manual", "rotated_material_oracle", "pinned_runtime_profile"):
        item = pins[name]
        assert digest(ROOT / item["path"]) == item["sha256"]
    model = Structure()
    # Canonical node order is independently checked by the pinned oracle.
    coords = [(0,0,0),(1,0,0),(1,1,0),(0,1,0),
              (0,0,1),(1,0,1),(1,1,1),(0,1,1),
              (.5,0,0),(1,.5,0),(.5,1,0),(0,.5,0),
              (.5,0,1),(1,.5,1),(.5,1,1),(0,.5,1),
              (0,0,.5),(1,0,.5),(1,1,.5),(0,1,.5)]
    for xyz in coords:
        model.node(xyz)
    model.element("C3D20", range(1,21), "SOLID")
    eid = model.element("SPRING2", [9,2], "PROJECTED_SPRING")
    model.equations = [[(9,1,1.),(1,1,-.5),(2,1,-.5)]]
    model.springs = [{"element": eid, "name": "PROJECTED_SPRING",
                      "group": "PROJECTED_SPRING", "nodes": [9,2],
                      "dof": 1, "stiffness_n_per_mm": 100.,
                      "bearing_closed_assumption": False}]
    metadata = {
        "scope": "Synthetic constrained rotated C3D20/SPC/MPC/SPRING2 elastic export mapping only",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "synthetic_only": True, "frame_ready": False,
        "boundary_conditions": [{"node":1,"first_dof":1,"last_dof":1,"value_mm":0.}],
        "fixed_nodes_policy": "No fully fixed node; the single partial SPC is explicitly listed in boundary_conditions.",
        "material": {"engineering_constants": [1200,800,600,.2,.15,.1,300,250,200],
                     "orientation_Z_degrees":37., "density_tonne_per_mm3":1.e-9},
        "expected_equations": 58,
        "expected_omitted_coordinates": [[1,1],[9,1]],
        "expected_projected_spring_tangent_N_per_mm": 25.,
        "reference_offsets_are_external": True,
        "mechanical_acceptance": False,
    }
    deck = (HERE / "coupon-constrained-matrixstorage.inp").read_text()
    sources = [HERE / name for name in ("README.md", "source-pins.json",
               "constrained_matrix_export_oracle.py", "coupon-constrained-matrixstorage.inp", "prepare_native.py")]
    sources.append(ROOT / pins["rotated_material_oracle"]["path"])
    target = HERE.parent / "current-constrained-matrix-export-native-attempt01"
    packet = freeze(target, model, metadata, sources, deck_text=deck)
    print(json.dumps({"directory":str(target.relative_to(ROOT)), "scope":packet["scope"]}))


if __name__ == "__main__":
    prepare()
