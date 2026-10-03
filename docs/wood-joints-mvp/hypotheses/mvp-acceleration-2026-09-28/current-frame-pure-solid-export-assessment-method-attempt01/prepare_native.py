"""Parent-only exact freeze of the source physical-solid stiffness export."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from fea.horizontal_panel_frame import Structure
from fea.wood_joint_reduced_native import digest, freeze


def prepare():
    proposal = HERE.parent / "current-frame-pure-solid-matrix-export-preflight-attempt01"
    source = HERE.parent / "current-springa-frame-input-adapter-attempt01/a12-rear/model.json"
    model = json.loads(source.read_text())
    physical = {int(n) for ids in model["physical_body_nodes"].values() for n in ids}
    structure = Structure()
    structure.nodes = {int(n): xyz for n, xyz in model["nodes"].items() if int(n) in physical}
    structure.elements = {int(e): (kind, ids, group)
                          for e, (kind, ids, group) in model["elements"].items()
                          if kind == "C3D20"}
    for eid, (_, ids, group) in structure.elements.items():
        assert set(ids) <= physical
        structure.groups.setdefault(group, []).append(eid)
    assert len(structure.nodes) == 12549 and len(structure.elements) == 1903
    metadata = {
        "scope": "Unloaded pure physical-solid elastic stiffness export only; no frame equilibrium or contact selection",
        "candidate": model["candidate"],
        "geometry_revision_id": model["geometry_revision_id"],
        "case_id": "a12-rear",
        "physical_body_nodes": model["physical_body_nodes"],
        "physical_body_elements": model["physical_body_elements"],
        "source_model_sha256": digest(source),
        "source_material_binding": model["material_binding"],
        "auxiliary_density_tonne_per_mm3": 1e-9,
        "auxiliary_density_scope": "Frequency export companion mass only; discard .mas; actual gravity remains in separately pinned source maps",
        "expected_equations": 37647,
        "frame_ready": False,
        "mechanical_acceptance": False,
        "gravity_or_climber_loads_applied": False,
        "boundary_constraints_or_connectors_applied": False,
    }
    sources = [source, HERE / "prepare_native.py", HERE / "assess_matrixstorage.py",
               HERE / "source-pins.json", HERE / "fixture-results.json", HERE / "README.md"]
    sources += [p for p in proposal.iterdir() if p.is_file()]
    target = HERE.parent / "current-frame-pure-solid-matrix-export-native-attempt01"
    freeze(target, structure, metadata, sources,
           deck_text=(proposal / "pure-physical-solid-matrixstorage.inp").read_text())
    print(json.dumps({"directory": str(target.relative_to(ROOT)),
                      "freeze_sha256": digest(target / "freeze.json")}))


if __name__ == "__main__":
    prepare()
