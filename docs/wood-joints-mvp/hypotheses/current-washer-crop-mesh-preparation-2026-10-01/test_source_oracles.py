"""Deterministic source-only arithmetic and mesh-contract tests."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))

import mesh_oracles as mesh
import prepare


TETRA_NODES = {
    1: (0.0, 0.0, 0.0),
    2: (1.0, 0.0, 0.0),
    3: (0.0, 1.0, 0.0),
    4: (0.0, 0.0, 1.0),
    5: (0.5, 0.0, 0.0),
    6: (0.5, 0.5, 0.0),
    7: (0.0, 0.5, 0.0),
    8: (0.0, 0.0, 0.5),
    9: (0.5, 0.0, 0.5),
    10: (0.0, 0.5, 0.5),
}
TETRA = {1: (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)}
TETRA_SURFACES = {
    "face.1": [(1, 2, 3, 5, 6, 7)],
    "face.2": [(1, 4, 2, 8, 9, 5)],
    "face.3": [(2, 4, 3, 9, 10, 6)],
    "face.4": [(3, 4, 1, 10, 8, 7)],
}


def valid_mesh_report() -> tuple[dict, dict]:
    report = {
        "schema": "conditional_washer_crop_mesh_report/v1",
        "status": "VERIFIED_C3D10_MESH_ONLY_NO_SOLVER",
        "source_pins_sha256": "a" * 64,
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "branch": "R75_H1_R_T_A_K12_catalog_nominal_frictionless_mesh_only",
        "body_count": 5,
        "body_ids": list(mesh.BODY_IDS),
        "accepted": False,
        "solved": False,
        "material_cards": False,
        "contact_cards": False,
        "tie_cards": False,
        "load_cards": False,
        "restraint_cards": False,
        "preload_cards": False,
        "solver_cards": False,
        "achieved_minimum_washer_through_thickness_layers": 2,
        "maximum_local_edge_mm": 0.8,
        "bodies": {},
    }
    categories_by_body = {}
    semantic_ids_by_body = {}
    topology_bodies = {}
    all_nodes = 0
    all_elements = 0
    for body_index, body_id in enumerate(mesh.BODY_IDS):
        node_shift = body_index * 20
        element_id = body_index + 1
        elements = {element_id: tuple(node + node_shift for node in TETRA[1])}
        surfaces = {
            name: [tuple(node + node_shift for node in row) for row in triangles]
            for name, triangles in TETRA_SURFACES.items()
        }
        if body_index == 0:
            surfaces = {
                "receiver.crop_cylinder_R75": surfaces.pop("face.1"),
                "receiver.source_face.a": surfaces.pop("face.2"),
                "receiver.source_face.b": surfaces.pop("face.3"),
                "receiver.source_face.c": surfaces.pop("face.4"),
            }
            categories = {
                "source_natural": ["receiver.source_face.a", "receiver.source_face.b", "receiver.source_face.c"],
                "crop_generated": ["receiver.crop_cylinder_R75"],
                "conditional_hardware": [],
            }
        else:
            surfaces = {f"{body_id}.{name}": rows for name, rows in surfaces.items()}
            categories = {
                "source_natural": [],
                "crop_generated": [],
                "conditional_hardware": sorted(surfaces),
            }
        semantic_ids_by_body[body_id] = sorted(surfaces)
        categories_by_body[body_id] = categories
        topology_bodies[body_id] = {"elements": elements, "surface_triangles": surfaces}
        report["bodies"][body_id] = {
            "solid_count": 1,
            "connected_component_count": 1,
            "element_type": "C3D10",
            "source_cad_volume_mm3": 1.0,
            "mesh_integrated_volume_mm3": 1.0,
            "minimum_sampled_jacobian": 1.0,
            "minimum_gauss5_jacobian": 1.0,
            "node_ids": list(range(1 + node_shift, 11 + node_shift)),
            "element_ids": [element_id],
        }
        all_nodes += 10
        all_elements += 1

    # Account for four C3D10 exterior faces on each of the five bodies.
    signature_rows = []
    for surface_id in categories_by_body[mesh.BODY_IDS[0]]["source_natural"]:
        signature_rows.append(
            {
                "semantic_surface_id": surface_id,
                "source_surface_type": "Plane",
                "source_surface_signature_sha256": "b" * 64,
                "clipped_surface_signature_sha256": "c" * 64,
                "source_step_sha256": "9053a7210a781e919038a4a823f867325dd5c78907bd028d8b9e76dc0b46df58",
                "source_face_ancestry_verified": True,
                "source_face_area_mm2": 10.0,
                "clipped_face_area_mm2": 1.0,
            }
        )
    report["surface_ownership"] = {
        "source_ancestry_verified": True,
        "source_face_ownership_complete": True,
        "bbox_only_identity_used": False,
        "unclassified_source_face_count": 0,
        "ambiguous_semantic_face_count": 0,
        "crop_generated_surface_ids": ["receiver.crop_cylinder_R75"],
        "source_signature_family_allowlist": list(mesh.SUPPORTED_SOURCE_SURFACE_TYPES),
        "source_signature_families_seen": ["Plane"],
        "unsupported_source_surface_types": [],
        "unmapped_intersecting_source_face_count": 0,
        "source_face_descendant_coverage_complete": True,
        "source_natural_face_signature_rows": signature_rows,
        "semantic_surface_ids_by_body": semantic_ids_by_body,
        "surface_categories_by_body": categories_by_body,
        "exterior_c3d10_face_count": 20,
        "tri6_face_count": 20,
        "uncovered_exterior_face_count": 0,
        "duplicate_exterior_face_count": 0,
    }
    return report, topology_bodies


class SourcePreparationTests(unittest.TestCase):
    def test_current_pinned_contract_prepares_without_geometry_or_native_work(self) -> None:
        record = prepare.build_record()
        self.assertEqual(
            record["status"],
            "SOURCE_PREPARATION_COMPLETE_NO_FREEZE_NO_GEOMETRY_NO_MESH_NO_SOLVER",
        )
        self.assertEqual(record["mesh_plan"]["body_count"], 5)
        self.assertEqual(record["receiver"]["crop"]["radius_mm"], 75.0)
        self.assertAlmostEqual(
            record["stack_loads"]["center_principal_right_2"]["signed_inward_resultant_N"],
            64.40226,
            places=8,
        )
        self.assertAlmostEqual(
            record["stack_loads"]["center_principal_right_1"]["signed_inward_resultant_N"],
            20.52895,
            places=8,
        )

    def test_hypothetical_nut_and_catalog_washer_arithmetic(self) -> None:
        profile_path = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/conditional-nut-profile.json"
        profile = json.loads(profile_path.read_text())
        h1 = prepare.nut_profile_metrics(profile, "H1")
        h2 = prepare.nut_profile_metrics(profile, "H2")
        washer = prepare.washer_metrics(18.653125, 7.9248, 1.5875)
        self.assertAlmostEqual(h1["volume_mm3"], 415.50205345278425, places=9)
        self.assertAlmostEqual(h2["volume_mm3"], 404.7247322297162, places=9)
        self.assertAlmostEqual(h1["outward_face_area_mm2"], 75.51784511932227, places=10)
        self.assertAlmostEqual(washer["volume_mm3"], 355.5139185846077, places=9)

    def test_source_frame_round_trip_uses_local_x_t_n_columns(self) -> None:
        crosscheck = json.loads((ROOT / "docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/washer-contract-parent-source-crosscheck.json").read_text())
        transform = crosscheck["receiver_frame"]["local_to_global_transform"]
        local = (0.0, 37.575760130041, 95.25)
        global_point = [
            transform[row][3] + sum(transform[row][column] * local[column] for column in range(3))
            for row in range(3)
        ]
        round_trip = prepare.source_to_local(global_point, transform)
        for actual, expected in zip(round_trip, local, strict=True):
            self.assertAlmostEqual(actual, expected, places=9)

    def test_reference_tri6_area_centroid_and_axial_force(self) -> None:
        nodes = {
            1: (0.0, 0.0, 0.0),
            2: (0.0, 1.0, 0.0),
            3: (0.0, 0.0, 1.0),
            4: (0.0, 0.5, 0.0),
            5: (0.0, 0.5, 0.5),
            6: (0.0, 0.0, 0.5),
        }
        area, centroid = mesh.tri6_area_centroid((1, 2, 3, 4, 5, 6), nodes)
        self.assertAlmostEqual(area, 0.5, places=12)
        for value in centroid:
            self.assertAlmostEqual(value, 1 / 3 if value != 0 else 0, places=12)
        integrated = mesh.integrate_uniform_axial_face(
            [(1, 2, 3, 4, 5, 6)],
            nodes,
            cad_area_mm2=0.5,
            force_n=10.0,
            force_direction=(1.0, 0.0, 0.0),
            axis_origin_global_mm=(0.0, 1 / 3, 1 / 3),
            plane_x_global_mm=0.0,
        )
        self.assertTrue(integrated["passes_contact_coupon_quadrature_limits"])
        self.assertAlmostEqual(integrated["integrated_force_global_N"][0], 10.0, places=12)
        self.assertAlmostEqual(integrated["moment_residual_N_mm"], 0.0, places=12)

    def test_exact_exterior_tri6_topology_and_semantic_coverage(self) -> None:
        audit = mesh.audit_c3d10_surface_ownership(TETRA, TETRA_SURFACES)
        self.assertEqual(audit["connected_component_count"], 1)
        self.assertEqual(audit["exterior_c3d10_face_count"], 4)
        self.assertEqual(audit["tri6_face_count"], 4)
        broken = dict(TETRA_SURFACES)
        broken["face.4"] = []
        with self.assertRaisesRegex(ValueError, "has no TRI6"):
            mesh.audit_c3d10_surface_ownership(TETRA, broken)

    def test_mesh_report_contract_rechecks_topology_and_refuses_mechanics_cards(self) -> None:
        report, topology = valid_mesh_report()
        mesh.validate_mesh_report(report, "a" * 64, topology_bodies=topology)
        report["solver_cards"] = True
        with self.assertRaisesRegex(ValueError, "exceeds mesh-only scope"):
            mesh.validate_mesh_report(report, "a" * 64, topology_bodies=topology)

    def test_mesh_deck_rejects_solver_keywords(self) -> None:
        mesh.validate_mesh_deck_keywords(
            "*HEADING\nmesh only\n*NODE\n1,0,0,0\n*ELEMENT,TYPE=C3D10,ELSET=WOOD\n"
        )
        with self.assertRaisesRegex(ValueError, "forbidden"):
            mesh.validate_mesh_deck_keywords("*HEADING\n*STEP\n")


if __name__ == "__main__":
    unittest.main()
