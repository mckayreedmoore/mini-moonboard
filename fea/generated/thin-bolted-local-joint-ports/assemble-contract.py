"""Bind the narrow local inputs without copying cached assets or contact cells."""

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OWN = Path(__file__).resolve()
OUT = OWN.with_name("contract.json")
REMOTE = OWN.with_name("input.json")
CONTACT = OWN.with_name("direct-timber-contact.json")
HARDWARE = ROOT / "fea/generated/thin-bolted-b104-local-hardware-inputs/inputs.json"
EXPECTED = {REMOTE: "90ec100d85d101796bc16a9966b7b4f001a35f4ebf74b06f6f533f8c5e7c0679",
            CONTACT: "ead9fee6a06d1233ac4cfd006fb2c681241d6ea2e81ddc410b1e47d9550e7dfa",
            HARDWARE: "8cebc830001ed86114bce7363f7fc3a0105c258885cdaa80a869245bea73d731"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assemble():
    assert all(sha(path) == expected for path, expected in EXPECTED.items())
    remote, contact, hardware = (json.loads(path.read_bytes()) for path in (REMOTE, CONTACT, HARDWARE))
    assert remote["candidate"] == hardware["candidate"]
    patches = []
    for index, old in enumerate(remote["patches"]):
        profile = hardware["patches"][index]
        assert old["selected_axis_ids"] == profile["axis_ids"]
        assert set(old["timber_body_order"]) == set(profile["timber_ids"])
        assert set(old["fitting_body_order"]) == set(profile["fitting_ids"])
        own = [r for r in contact["patches"] if {r["first"], r["second"]} <= set(old["timber_body_order"])]
        assert len(own) == index + 1
        resolved = []
        for patch in own:
            assert abs(sum(c["area_mm2"] for c in patch["cells"]) - patch["area_mm2"]) < 1e-7
            assert np.linalg.norm(np.asarray(patch["first_outward_normal_xyz"])
                                  + np.asarray(patch["normal_from_second_to_first_xyz"])) < 1e-10
            assert all(c["reference_centroid_on_trimmed_patch"]
                       and c["both_inward_material_probes_occupied"] for c in patch["cells"])
            resolved.append({"id": patch["id"], "first": patch["first"], "second": patch["second"],
                "source_first_face_id": patch["source_first_face"]["face_id"],
                "source_second_face_id": patch["source_second_face"]["face_id"],
                "centroid_reference_xyz_mm": patch["centroid_xyz_mm"], "area_reference_mm2": patch["area_mm2"],
                "first_outward_normal_xyz": patch["first_outward_normal_xyz"],
                "second_outward_normal_xyz": patch["normal_from_second_to_first_xyz"],
                "cell_count": len(patch["cells"]), "exact_cells_and_face_signatures_in": str(CONTACT.relative_to(ROOT)),
                "physical_contact_law_or_stiffness_supplied": False})
        patches.append({"id": old["id"], "remote_input_patch_id": old["id"],
            "hardware_input_patch_id": profile["id"], "timber_body_order": old["timber_body_order"],
            "fitting_body_order": old["fitting_body_order"], "selected_axis_ids": old["selected_axis_ids"],
            "remote_port_count": len(old["remote_ports"]),
            "resolved_direct_timber_geometry": resolved,
            "superseded_only_geometric_missing_atlas_statements": True,
            "panel_and_adjacent_shaft_duties_remain_explicit_neighbor_inputs": True})
    layout_path = ROOT / next(p for p in remote["source_sha256"] if p.endswith("mixed-offset-rows-shallow-wires-v4.json"))
    layout = json.loads(layout_path.read_bytes())
    duty_pairs = sorted({(r["beam"], r["post"]) for r in layout["raw_fittings"]})
    resolved_pairs = {(r["first"], r["second"]) for r in contact["patches"]}
    assert len(duty_pairs) == 24 and len(resolved_pairs) == 3
    pins = {str(p.relative_to(ROOT)): expected for p, expected in EXPECTED.items()}
    pins[str(OWN.relative_to(ROOT))] = sha(OWN)
    for path, expected in {**remote["source_sha256"], **contact["source_sha256"],
                           **hardware["source_sha256"]}.items():
        assert sha(ROOT / path) == expected
    return {"schema": "thin_bolted_local_remote_neighbor_contract/v1", "source_sha256": pins,
        "candidate": remote["candidate"], "patches": patches,
        "remote_geometry_and_crossing_inventory": str(REMOTE.relative_to(ROOT)),
        "hardware_own_planes_and_axis_occupancy": str(HARDWARE.relative_to(ROOT)),
        "direct_contact_trimmed_geometry": str(CONTACT.relative_to(ROOT)),
        "grain_frames": [{"member": r["member"], "grain_frame_rows_xyz": r["grain_frame_rows_xyz"]}
                         for r in remote["members"]],
        "neighbor_contract": {
            "outerbase_left": "Keep adjacent005/header outer-post fitting, kicker header screws4/5, kicker-left and main-lower-left surface duties explicit. Their external wrenches/compliance are not bounded by the isolated019/020 patch.",
            "sharedcenter_left": "Keep kicker header screws1/2/3 and round-kicker-center-left screw2, kicker-left on header/post and main-lower-left on principal explicit. Two header cuts share one timber; their six self-balanced port-load modes can strain that timber despite zero rigid-body work.",
            "no_hardware_free_plane_is_proved_contact_free": True,
            "full_cut_cross_boundary_occupancy_or_neighbor_impedance": None},
        "unit_work_and_compliance_contract": remote["work_contract"],
        "direct_contact_response_correction": "Only trimmed reference geometry is resolved. Before response, explicitly add the three paired compression interfaces in a distinct source-bound model; preserve reviewed prior operators and do not silently assert bilateral ties, preload or active closure.",
        "whole_frame_direct_contact_coverage": {
            "existing_retained_axis_interface_proof_pairs": 6,
            "additional_local_trimmed_pairs": 3,
            "angle_duty_pair_candidates": len(duty_pairs),
            "other_angle_duty_pairs_needing_trimmed_geometry":
                [{"first": a, "second": b} for a, b in duty_pairs if (a, b) not in resolved_pairs],
            "complete_all_pair_contact_enumeration": False,
            "unintended_non_duty_contacts_or_overlap_excluded": False},
        "limits": ["No compliance value, force bound, physical bedding/preload/friction law or resistance is supplied.",
            "Remote reference planes retain full saved section area but are not Saint-Venant or exact section-stiffness qualifications.",
            "Global six modes and all remaining unilateral/internal free modes must be retained; incompatible loads are rejected instead of fixing neighbors.",
            "Numerical reciprocity applies only to a symmetric elastic operator on one fixed admissible active branch.",
            "All reference geometry reused from previous packets is independent of old forces, q, reactions or acceptance."],
        "release": remote["release"]}


if __name__ == "__main__":
    if OUT.exists():
        raise SystemExit("Preserve issued local neighbor contract")
    result = assemble()
    OUT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"path": str(OUT.relative_to(ROOT)), "sha256": sha(OUT), "producer_sha256": sha(OWN),
                      "patches": len(result["patches"]), "ports": sum(p["remote_port_count"] for p in result["patches"])}))
