"""Independent deck, ownership, volume-record, surface and source audit.

This read-only audit does not import Gmsh or recompute C3D10 Jacobians. Those
quality values remain separately covered by the parent Jacobian audit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))

from fea import wood_joint_wj24_patch_mesh as wj24_mesh

EXPECTED_BODY_IDS = (
    "base_rail_service_lower_right",
    "base_rail_service_upper_right",
    "base_principal_center_right",
    "wj04_lower_full_stock_cleat",
    "wj04_upper_g7_crosscut_full_stock_cleat",
)
EXPECTED_SOURCE_FILES = (
    "fea/floor_contact.py",
    "fea/stitch_joint_mesh.py",
    "fea/wood_joint_patch_mesh.py",
    "fea/wood_joint_wj24_patch_mesh.py",
    "scripts/wood_joint_wj24_patch_reconciliation.py",
)
FACE_NODES_C3D10 = (
    (0, 1, 2, 4, 5, 6),
    (0, 3, 1, 7, 8, 4),
    (1, 3, 2, 8, 9, 5),
    (2, 3, 0, 9, 7, 6),
)
EXPECTED_IMAGE_ID = "sha256:083de8eefd4d9d9029d28ac1fdbb933a3b1e024225d8048165d6ef580d1b8f59"
EXPECTED_SETTINGS = {
    "global_max_size_mm": 40.0,
    "axis_local_min_size_mm": 3.0,
    "axis_refinement_band_mm": 12.0,
}
EXPECTED_RECONCILIATION_SHA256 = "256af45c2a6b2b48726d86f95e2f4febdd8cad726d690738e9cb1fad87a89711"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def positive_ints(value: Any, context: str) -> list[int]:
    require(isinstance(value, list) and bool(value), f"{context}: expected a nonempty ID list")
    result: list[int] = []
    for item in value:
        require(
            isinstance(item, int) and not isinstance(item, bool) and item > 0,
            f"{context}: expected positive integer IDs",
        )
        result.append(item)
    require(len(result) == len(set(result)), f"{context}: duplicate IDs")
    return result


def parse_deck(path: Path) -> tuple[dict[int, tuple[float, float, float]], dict[str, dict[int, tuple[int, ...]]], list[str]]:
    nodes: dict[int, tuple[float, float, float]] = {}
    element_sets: dict[str, dict[int, tuple[int, ...]]] = {}
    cards: list[str] = []
    mode: str | None = None
    active_set: str | None = None
    for line_number, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("**"):
            continue
        if line.startswith("*"):
            card = line.upper()
            cards.append(card)
            if card == "*HEADING":
                mode, active_set = "heading", None
            elif card == "*NODE":
                mode, active_set = "nodes", None
            elif card.startswith("*ELEMENT,TYPE=C3D10,ELSET="):
                mode = "elements"
                active_set = card.split("ELSET=", 1)[1]
                require(bool(active_set), f"deck line {line_number}: empty C3D10 set name")
                require(active_set not in element_sets, f"duplicate C3D10 set {active_set}")
                element_sets[active_set] = {}
            else:
                raise ValueError(f"deck line {line_number}: unsupported keyword {card}")
            continue
        if mode == "heading":
            continue
        fields = [item.strip() for item in line.split(",")]
        if mode == "nodes":
            if len(fields) != 4:
                raise ValueError(f"deck line {line_number}: malformed node row")
            tag = int(fields[0])
            xyz = tuple(float(item) for item in fields[1:])
            require(tag > 0 and tag not in nodes, f"deck line {line_number}: duplicate/invalid node ID")
            require(len(xyz) == 3 and all(math.isfinite(item) for item in xyz), f"deck line {line_number}: invalid node coordinates")
            nodes[tag] = xyz  # type: ignore[assignment]
        elif mode == "elements" and active_set is not None:
            if len(fields) != 11:
                raise ValueError(f"deck line {line_number}: malformed C3D10 row")
            tag = int(fields[0])
            connectivity = tuple(int(item) for item in fields[1:])
            require(tag > 0, f"deck line {line_number}: invalid element ID")
            require(tag not in element_sets[active_set], f"deck line {line_number}: duplicate element ID")
            require(len(set(connectivity)) == 10, f"deck line {line_number}: C3D10 repeats a node")
            element_sets[active_set][tag] = connectivity
        else:
            raise ValueError(f"deck line {line_number}: data outside a supported card")
    require(bool(nodes), "deck has no node data")
    require(bool(element_sets), "deck has no C3D10 elements")
    return nodes, element_sets, cards


def edge_midpoints(face_nodes: tuple[int, ...]) -> dict[tuple[int, int], int]:
    require(len(face_nodes) == 6 and len(set(face_nodes)) == 6, "invalid C3D10 face topology")
    corners = face_nodes[:3]
    return {
        tuple(sorted((corners[0], corners[1]))): face_nodes[3],
        tuple(sorted((corners[1], corners[2]))): face_nodes[4],
        tuple(sorted((corners[2], corners[0]))): face_nodes[5],
    }


def independent_exterior_faces(elements: dict[int, tuple[int, ...]]) -> dict[tuple[int, int], tuple[int, ...]]:
    by_corner_face: dict[tuple[int, int, int], list[tuple[int, int, tuple[int, ...], dict[tuple[int, int], int]]]] = {}
    for element_id, connectivity in elements.items():
        require(len(connectivity) == 10 and len(set(connectivity)) == 10, "expected distinct C3D10 connectivity")
        for face_number, indices in enumerate(FACE_NODES_C3D10, 1):
            face = tuple(connectivity[index] for index in indices)
            corner_key = tuple(sorted(face[:3]))
            by_corner_face.setdefault(corner_key, []).append(
                (element_id, face_number, face, edge_midpoints(face))
            )
    exterior: dict[tuple[int, int], tuple[int, ...]] = {}
    for rows in by_corner_face.values():
        if len(rows) == 1:
            element_id, face_number, face, _midpoints = rows[0]
            exterior[(element_id, face_number)] = face
        elif len(rows) == 2:
            require(rows[0][3] == rows[1][3], "interior C3D10 face has incompatible mid-edge nodes")
        else:
            raise ValueError("nonmanifold C3D10 face has more than two adjacent elements")
    require(bool(exterior), "body has no exterior quadratic faces")
    return exterior


def validate_surface_ownership(body_id: str, body: dict[str, Any], exterior: dict[tuple[int, int], tuple[int, ...]]) -> dict[str, int]:
    surface_rows = body.get("surface_inventory")
    require(isinstance(surface_rows, dict) and bool(surface_rows), f"{body_id}: missing CAD surface inventory")
    covered: list[tuple[int, int]] = []
    surface_face_counts: dict[str, int] = {}
    for tag, row in surface_rows.items():
        require(isinstance(row, dict), f"{body_id}/{tag}: malformed CAD surface row")
        require(row.get("cad_entity_tag") == int(tag), f"{body_id}/{tag}: CAD tag does not match its map key")
        require(isinstance(row.get("cad_type"), str) and bool(row["cad_type"]), f"{body_id}/{tag}: missing CAD type")
        bounds = row.get("bounds_xyz_mm")
        require(isinstance(bounds, list) and len(bounds) == 6, f"{body_id}/{tag}: malformed CAD bounds")
        numeric_bounds = [float(value) for value in bounds]
        require(all(math.isfinite(value) for value in numeric_bounds), f"{body_id}/{tag}: nonfinite CAD bounds")
        require(all(numeric_bounds[index] <= numeric_bounds[index + 1] for index in (0, 2, 4)), f"{body_id}/{tag}: inverted CAD bounds")
        area = float(row.get("area_mm2", float("nan")))
        require(math.isfinite(area) and area > 0, f"{body_id}/{tag}: invalid CAD area")
        faces = row.get("tri6_exterior_face_refs")
        require(isinstance(faces, list) and bool(faces), f"{body_id}/{tag}: empty TRI6 surface ownership")
        pairs: list[tuple[int, int]] = []
        for ref in faces:
            require(isinstance(ref, list) and len(ref) == 2, f"{body_id}/{tag}: malformed face reference")
            element_id, face_number = ref
            require(isinstance(element_id, int) and not isinstance(element_id, bool), f"{body_id}/{tag}: invalid exterior element ID")
            require(isinstance(face_number, int) and not isinstance(face_number, bool) and 1 <= face_number <= 4, f"{body_id}/{tag}: invalid C3D10 face number")
            pairs.append((element_id, face_number))
        require(len(pairs) == len(set(pairs)), f"{body_id}/{tag}: duplicate surface face references")
        node_ids = set(positive_ints(row.get("tri6_node_ids"), f"{body_id}/{tag} TRI6 nodes"))
        expected_nodes: set[int] = set()
        for pair in pairs:
            require(pair in exterior, f"{body_id}/{tag}: face reference is not exterior")
            expected_nodes.update(exterior[pair])
        require(node_ids == expected_nodes, f"{body_id}/{tag}: TRI6 node list differs from its faces")
        covered.extend(pairs)
        surface_face_counts[tag] = len(pairs)
    require(len(covered) == len(set(covered)), f"{body_id}: exterior face is assigned to multiple CAD surfaces")
    require(set(covered) == set(exterior), f"{body_id}: CAD surfaces do not cover the complete exterior TRI6 face set")
    return surface_face_counts


def _relative_error(first: float, second: float) -> float:
    return abs(first / second - 1.0) if second else float("inf")


def audit(
    mesh_directory: Path,
    bundle_directory: Path,
    launch_path: Path,
    log_path: Path,
    launcher_path: Path,
    test_snapshot_path: Path,
) -> dict[str, Any]:
    mesh_directory = mesh_directory.resolve()
    bundle_directory = bundle_directory.resolve()
    report_path = mesh_directory / "mesh.json"
    deck_path = mesh_directory / "mesh.inp"
    report_bytes = report_path.read_bytes()
    report = json.loads(report_bytes)
    require(report.get("schema") == "wood_joint_wj24_patch_mesh/v1", "mesh report has the wrong schema")
    require(report.get("status") == "VERIFIED_WJ24_C3D10_MESH_ONLY_NO_SOLVER", "mesh report is not a verified WJ24 mesh-only result")
    require(report.get("accepted") is False and report.get("solved") is False, "mesh report exceeds mesh-only claim boundary")
    require(report.get("WJ16_mesh_geometry_reused") is False, "WJ16 mesh geometry was claimed as reused")
    require(report.get("WJ24_G7_relief_variant_included") is False, "mesh report includes an unexported G7 relief variant")
    require(report.get("contact_or_interface_classification_assigned") is False, "mesh report assigns semantic contacts")
    require(report.get("capacity_or_release_claim") is False and report.get("full_candidate_acceptance_claim") is False, "mesh report exceeds its claim boundary")
    require(report.get("configuration") == EXPECTED_SETTINGS, "mesh settings differ from the pinned launch")
    require(report.get("mesh_input_sha256") == sha256_file(deck_path), "deck hash differs from the mesh report")
    require(report.get("input_bundle_reconciliation_sha256") == EXPECTED_RECONCILIATION_SHA256, "input reconciliation digest differs from the frozen WJ24 export")

    input_bundle = wj24_mesh.load_wj24_patch_bundle(bundle_directory)
    require(input_bundle["reconciliation_sha256"] == EXPECTED_RECONCILIATION_SHA256, "WJ24 bundle reconciliation SHA changed")
    require(report.get("WJ24_composition_binding") == input_bundle["source_composition"], "mesh report source composition differs from the authenticated bundle")
    require(report.get("WJ16_to_WJ24_reconciliation_sha256") == input_bundle["reconciliation_sha256"], "mesh report WJ16/WJ24 reconciliation digest changed")
    require(report.get("input_bundle_file_sha256_before") == input_bundle["input_file_sha256"], "pre-mesh input file hashes differ from WJ24 bundle")
    require(report.get("input_bundle_file_sha256_after") == input_bundle["input_file_sha256"], "input bundle changed during meshing")
    require(report.get("mesh_worker_source_sha256") == report.get("mesh_worker_source_sha256_after"), "mesh worker sources changed during preparation")
    require(set(report["mesh_worker_source_sha256"]) == set(EXPECTED_SOURCE_FILES), "mesh source hash inventory is incomplete")
    for relative in EXPECTED_SOURCE_FILES:
        expected_sha = report["mesh_worker_source_sha256"][relative]
        snapshot_path = mesh_directory / "sources" / f"{relative}.snapshot"
        require(snapshot_path.is_file() and sha256_file(snapshot_path) == expected_sha, f"mesh source snapshot changed: {relative}")
        require(sha256_file(ROOT / relative) == expected_sha, f"live mesh source differs from run snapshot: {relative}")

    launch = json.loads(launch_path.read_text())
    log_bytes = log_path.read_bytes()
    launcher_bytes = launcher_path.read_bytes()
    require(launch.get("image_id") == EXPECTED_IMAGE_ID, "launcher did not pin the available mechanics image")
    require(launch.get("returncode") == 0 and launch.get("source_unchanged") is True, "pinned launch did not complete cleanly with unchanged adapter inputs")
    require(launch.get("native_solve_run") is False, "launcher reports a native solve")
    require(launch.get("scope") == "five-body current WJ24 baseline wood mesh only; no G7 relief variant", "launcher scope changed")
    require(launch.get("source_sha256_before") == launch.get("source_sha256_after"), "adapter/test source hashes changed during the launch")
    for relative, digest in launch["source_sha256_before"].items():
        require(sha256_file(ROOT / relative) == digest, f"launcher input source changed: {relative}")
    command = launch.get("command")
    require(isinstance(command, list), "launcher command is absent")
    require("python3" in command and "-m" in command and "fea.wood_joint_wj24_patch_mesh" in command, "launcher command did not invoke the WJ24 mesh adapter")
    require(EXPECTED_IMAGE_ID in command, "launcher command does not contain the pinned image")
    require("--global-max-size-mm" in command and "40" in command, "launcher did not use the 40 mm global size")
    require("--axis-local-size-mm" in command and "3" in command, "launcher did not use the 3 mm local size")
    require("--axis-refinement-band-mm" in command and "12" in command, "launcher did not use the 12 mm refinement band")
    require(sha256_file(mesh_directory / "sources" / "fea/wood_joint_wj24_patch_mesh.py.snapshot") == launch["source_sha256_before"]["fea/wood_joint_wj24_patch_mesh.py"], "run source and launcher snapshot differ")
    require(sha256_file(test_snapshot_path) == launch["source_sha256_before"]["tests/test_wood_joint_wj24_patch_mesh.py"], "run test snapshot differs from launcher input")

    nodes, element_sets, cards = parse_deck(deck_path)
    require(set(element_sets) == {body_id.upper() for body_id in EXPECTED_BODY_IDS}, "deck element sets differ from the exact five-body WJ24 contract")
    require(report.get("body_count") == 5, "mesh report body count differs from WJ24 contract")
    require(report.get("completed_body_ids") == list(EXPECTED_BODY_IDS), "completed body order differs from WJ24 contract")
    require(set(report.get("bodies", {})) == set(EXPECTED_BODY_IDS), "mesh report body inventory differs from WJ24 contract")
    require(report.get("node_count") == len(nodes), "mesh report and deck node counts differ")
    require(report.get("element_count") == sum(len(rows) for rows in element_sets.values()), "mesh report and deck element counts differ")
    require(len(nodes) == 89743 and report.get("element_count") == 46629, "deck counts differ from the observed pinned attempt")

    global_node_owners: set[int] = set()
    global_element_owners: set[int] = set()
    body_summaries: dict[str, Any] = {}
    coincident_coordinate_bodies: dict[tuple[float, float, float], set[str]] = {}
    for body_id in EXPECTED_BODY_IDS:
        body = report["bodies"][body_id]
        deck_elements = element_sets[body_id.upper()]
        reported_nodes = set(positive_ints(body.get("nodes"), f"{body_id} reported nodes"))
        reported_elements = set(positive_ints(body.get("elements"), f"{body_id} reported elements"))
        require(not (global_node_owners & reported_nodes), f"{body_id}: node ownership overlaps another body")
        require(not (global_element_owners & reported_elements), f"{body_id}: element ownership overlaps another body")
        global_node_owners.update(reported_nodes)
        global_element_owners.update(reported_elements)
        require(reported_elements == set(deck_elements), f"{body_id}: mesh report element ownership differs from the deck ELSET")
        used_nodes = {node for connectivity in deck_elements.values() for node in connectivity}
        require(used_nodes == reported_nodes, f"{body_id}: node ownership differs from its C3D10 connectivity")
        require(used_nodes <= nodes.keys(), f"{body_id}: element references an absent deck node")
        exterior = independent_exterior_faces(deck_elements)
        surface_face_counts = validate_surface_ownership(body_id, body, exterior)
        require(len(exterior) == body.get("exterior_tri6_face_count"), f"{body_id}: reported exterior face count differs from independent reconstruction")
        require(sum(surface_face_counts.values()) == len(exterior), f"{body_id}: surface face counts do not exhaust exterior")

        source_geometry = input_bundle["body_rows"][body_id]["WJ24_finished_geometry"]
        imported = body.get("imported_cad")
        require(isinstance(imported, dict), f"{body_id}: missing Gmsh CAD import evidence")
        expected_volume = float(source_geometry["volume_mm3"])
        imported_volume = float(imported.get("volume_mm3", float("nan")))
        import_tolerance = float(imported.get("relative_volume_tolerance", float("nan")))
        require(math.isfinite(imported_volume) and import_tolerance > 0, f"{body_id}: invalid imported CAD volume evidence")
        require(_relative_error(imported_volume, expected_volume) <= import_tolerance, f"{body_id}: imported CAD volume differs from the WJ24 STEP source")
        imported_centroid = imported.get("centroid_global_xyz_mm")
        source_centroid = source_geometry["centroid_global_xyz_mm"]
        position_tolerance = float(imported.get("position_tolerance_mm", float("nan")))
        require(len(imported_centroid) == 3 and all(abs(float(a) - float(b)) <= position_tolerance for a, b in zip(imported_centroid, source_centroid, strict=True)), f"{body_id}: imported centroid differs from the WJ24 STEP source")
        volume_audit = body.get("integrated_mesh_audit")
        require(isinstance(volume_audit, dict), f"{body_id}: missing integrated volume report")
        cad_volume = float(volume_audit.get("cad_volume_mm3", float("nan")))
        mesh_volume = float(volume_audit.get("integrated_mesh_volume_mm3", float("nan")))
        recorded_error = float(volume_audit.get("relative_volume_error", float("nan")))
        volume_tolerance = float(volume_audit.get("relative_volume_tolerance", float("nan")))
        require(all(math.isfinite(value) for value in (cad_volume, mesh_volume, recorded_error, volume_tolerance)), f"{body_id}: nonfinite integrated-volume record")
        require(volume_tolerance == 0.001, f"{body_id}: integrated-volume tolerance changed")
        require(_relative_error(cad_volume, imported_volume) <= import_tolerance, f"{body_id}: integrated-volume CAD basis differs from imported STEP volume")
        require(math.isclose(recorded_error, _relative_error(mesh_volume, cad_volume), rel_tol=1e-9, abs_tol=1e-12), f"{body_id}: relative volume error record is inconsistent")
        require(recorded_error <= volume_tolerance, f"{body_id}: integrated mesh volume exceeds tolerance")
        require(float(volume_audit.get("minimum_sampled_jacobian", 0)) > 0, f"{body_id}: report records nonpositive sampled Jacobian")
        require(float(volume_audit.get("minimum_integration_jacobian", 0)) > 0, f"{body_id}: report records nonpositive integration Jacobian")
        for node_id in reported_nodes:
            coincident_coordinate_bodies.setdefault(nodes[node_id], set()).add(body_id)
        body_summaries[body_id] = {
            "node_count": len(reported_nodes),
            "element_count": len(reported_elements),
            "exterior_tri6_face_count": len(exterior),
            "surface_count": len(surface_face_counts),
            "integrated_mesh_volume_mm3_reported": mesh_volume,
            "cad_volume_mm3_from_WJ24_STEP": expected_volume,
            "relative_volume_error_reported": recorded_error,
            "minimum_sampled_jacobian_reported": float(volume_audit["minimum_sampled_jacobian"]),
            "minimum_integration_jacobian_reported": float(volume_audit["minimum_integration_jacobian"]),
            "semantic_surface_binding": body.get("surface_semantic_binding_status"),
        }
    require(global_node_owners == set(nodes), "body node ownership does not cover all deck nodes")
    require(global_element_owners == {tag for rows in element_sets.values() for tag in rows}, "body element ownership does not cover all deck elements")
    require(len(global_node_owners) == 89743 and len(global_element_owners) == 46629, "global ownership totals differ from attempt counts")
    require(cards.count("*HEADING") == 1 and cards.count("*NODE") == 1 and len([card for card in cards if card.startswith("*ELEMENT,")]) == 5, "deck has unexpected or missing structural cards")

    warning_lines = [line.strip() for line in log_bytes.decode("utf-8", errors="replace").splitlines() if "Volume mesh: worst distortion" in line]
    require(len(warning_lines) == 3, "run log distortion-warning count differs from the recorded attempt")
    coordinate_overlap_groups = [sorted(ids) for ids in coincident_coordinate_bodies.values() if len(ids) > 1]
    result = {
        "status": "parent_deck_body_ownership_and_surface_audit_passed",
        "audit_scope": "read-only deck, body ownership, exterior quadratic faces, volume-record consistency and source binding",
        "structural_solve_run": False,
        "solver_cards_present": False,
        "C3D10_jacobians_independently_recomputed_by_this_audit": False,
        "independent_jacobian_audit_expected_separately": True,
        "mesh_directory": str(mesh_directory),
        "input_bundle_directory": str(bundle_directory),
        "mesh_report_sha256": sha256_file(report_path),
        "mesh_input_sha256": sha256_file(deck_path),
        "input_reconciliation_sha256": input_bundle["reconciliation_sha256"],
        "launch_record_sha256": sha256_file(launch_path),
        "run_log_sha256": sha256_bytes(log_bytes),
        "launcher_source_sha256": sha256_bytes(launcher_bytes),
        "focused_test_snapshot_sha256": sha256_file(test_snapshot_path),
        "pinned_container_image": EXPECTED_IMAGE_ID,
        "launcher_elapsed_seconds": launch["elapsed_seconds"],
        "node_count": len(nodes),
        "element_count": sum(len(rows) for rows in element_sets.values()),
        "body_count": len(body_summaries),
        "shared_global_node_ids_between_bodies": 0,
        "cross_body_coincident_coordinate_groups": len(coordinate_overlap_groups),
        "body_coordinate_overlap_groups": coordinate_overlap_groups,
        "deck_keyword_cards": cards,
        "material_contact_or_solver_cards": False,
        "reported_mesh_warning_lines_before_high_order_optimization": warning_lines,
        "bodies": body_summaries,
        "source_and_input_hashes_reconcile": True,
        "capacity_or_release_claim": False,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mesh-directory",
        type=Path,
        default=ROOT / "fea/generated/wj24-baseline-patch-mesh/attempt-01",
    )
    parser.add_argument(
        "--bundle-directory",
        type=Path,
        default=ROOT / "fea/results/diagnostics/wj24-baseline-patch-geometry-v1",
    )
    parser.add_argument(
        "--launch-record",
        type=Path,
        default=Path("/tmp/wj24-baseline-mesh-attempt-01/launch.json"),
    )
    parser.add_argument(
        "--run-log",
        type=Path,
        default=Path("/tmp/wj24-baseline-mesh-attempt-01/run.log"),
    )
    parser.add_argument(
        "--launcher-source",
        type=Path,
        default=Path("/tmp/run-wj24-baseline-mesh-attempt01.py"),
    )
    parser.add_argument(
        "--test-snapshot",
        type=Path,
        default=Path("/tmp/wj24-baseline-mesh-attempt-01/test_wood_joint_wj24_patch_mesh.py.snapshot"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("parent-audit.json"),
    )
    args = parser.parse_args()
    result = audit(
        args.mesh_directory,
        args.bundle_directory,
        args.launch_record,
        args.run_log,
        args.launcher_source,
        args.test_snapshot,
    )
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
