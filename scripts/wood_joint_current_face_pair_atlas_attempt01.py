"""Build a geometry-only face-pair atlas from the reviewed current STEP bodies.

The atlas identifies exact opposed planar source faces behind T04's 115
finite opposed body-pair rows. It does not assign contact ownership or infer
any mechanical behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PACKET_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-geometric-interface-face-atlas-attempt01-2026-09-28"
)
PRODUCER_REL = Path("scripts/wood_joint_current_face_pair_atlas_attempt01.py")
TEST_REL = Path("tests/test_wood_joint_current_face_pair_atlas_attempt01.py")
MAP_PACKET_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-geometric-interface-map-attempt02-2026-09-28"
)
MAP_REVIEW_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-geometric-interface-map-attempt02-independent-review-2026-09-28"
)
OVERLAP_PACKET_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-overlap-contact-geometry-evidence-attempt07"
)
OVERLAP_REVIEW_RELS = (
    Path(
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-overlap-contact-geometry-attempt07-correctness-review-2026-09-28"
    ),
    Path(
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-overlap-contact-geometry-attempt07-testing-review-2026-09-28"
    ),
    Path(
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-overlap-contact-geometry-attempt07-architecture-review-2026-09-28"
    ),
)
SOLIDS_PACKET_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-full-frame-member-solids-attempt01"
)
SOLIDS_MANIFEST_REL = SOLIDS_PACKET_REL / "bundle/current-full-frame-member-solids.json"
INPUT_MANIFEST_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
)
GRAPH_REL = MAP_PACKET_REL / "complete-contact-graph.json"
MAP_PIN_REL = MAP_PACKET_REL / "source-pins.json"
OVERLAP_EVIDENCE_REL = OVERLAP_PACKET_REL / "geometry-evidence.json"

EXPECTED_CANDIDATE = "compact-floor-flush-wood-joints-development"
EXPECTED_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_CLASS_COUNTS = {
    "aabb_separated_not_exactly_evaluated": 1078,
    "exact_brep_separated_geometry": 26,
    "finite_opposed_planar_geometry": 115,
    "zero_area_or_unresolved_geometry": 6,
}
EXPECTED_TOOLCHAIN = {
    "python": "3.12.3",
    "cadquery": "2.8.0",
    "cadquery_ocp": "7.9.3.1.1",
    "ocp_module": "7.9.3.1",
}
GEOMETRY_TOLERANCE_MM = 1e-5
AREA_TOLERANCE_MM2 = 1e-6
NORMAL_TOLERANCE = 1e-7
AREA_RECONCILIATION_REL_TOLERANCE = 1e-10
SCOPE = "source-bound finite opposed planar face geometry only; no mechanics or acceptance"
SCHEMA = "wood_joint_current_geometric_interface_face_pair_atlas/v1"
PINS_SCHEMA = "wood_joint_current_geometric_interface_face_pair_atlas_source_pins/v1"
ATTEMPT_ID = PACKET_REL.name
PIN_FIELDS = {
    "schema",
    "attempt_id",
    "candidate",
    "revision_id",
    "source_hashes",
    "output_sha256",
    "scope",
    "criterion_disposition",
    "predecessor_bindings",
    "toolchain",
}
ATLAS_FILES = ["README.md", "face-pair-atlas.json", "source-pins.json"]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _canonical_sha256(value: Any) -> str:
    return sha256_bytes(_canonical_json(value).encode("utf-8"))


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _load_json(path: Path) -> Any:
    return json.loads(
        Path(path).read_text(encoding="utf-8"), object_pairs_hook=_unique_object
    )


def _finite(value: Any, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def _round9(value: Any, label: str) -> float:
    rounded = round(_finite(value, label), 9)
    return 0.0 if rounded == 0.0 else rounded


def _vector3(value: Any, label: str) -> list[float]:
    if hasattr(value, "toTuple"):
        value = value.toTuple()
    result = [_round9(component, label) for component in value]
    if len(result) != 3:
        raise ValueError(f"{label} must have three components")
    return result


def _bounds(shape: Any, label: str) -> list[float]:
    box = shape.BoundingBox()
    return [
        _round9(value, label)
        for value in (box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax)
    ]


def _edge_geometry_signature(edge: Any) -> dict[str, Any]:
    endpoints = sorted(
        _vector3(vertex.Center(), "edge endpoint") for vertex in edge.Vertices()
    )
    return {
        "curve_type": str(edge.geomType()),
        "length_mm": _round9(edge.Length(), "edge length"),
        "center_xyz_mm": _vector3(edge.Center(), "edge center"),
        "bounds_xyz_mm": _bounds(edge, "edge bound"),
        "vertex_xyz_mm": endpoints,
    }


def _face_signature_data(face: Any) -> dict[str, Any]:
    if face.geomType() != "PLANE":
        raise ValueError("source face signature requested for a non-planar face")
    normal = face.normalAt().normalized()
    edges = [_edge_geometry_signature(edge) for edge in face.Edges()]
    edges.sort(key=_canonical_json)
    vertices = sorted(
        _vector3(vertex.Center(), "face vertex") for vertex in face.Vertices()
    )
    return {
        "surface_type": "PLANE",
        "area_mm2": _round9(face.Area(), "face area"),
        "center_xyz_mm": _vector3(face.Center(), "face center"),
        "oriented_normal_xyz": _vector3(normal, "face normal"),
        "bounds_xyz_mm": _bounds(face, "face bound"),
        "vertex_xyz_mm": vertices,
        "edge_signatures": edges,
        "wire_count": len(face.Wires()),
    }


def _region_geometry_data(face: Any) -> dict[str, Any]:
    """Describe a Boolean intersection region without assigning face ownership."""
    edges = [_edge_geometry_signature(edge) for edge in face.Edges()]
    edges.sort(key=_canonical_json)
    vertices = sorted(
        _vector3(vertex.Center(), "overlap-region vertex")
        for vertex in face.Vertices()
    )
    return {
        "surface_type": str(face.geomType()),
        "area_mm2": _round9(face.Area(), "overlap-region area"),
        "center_xyz_mm": _vector3(face.Center(), "overlap-region center"),
        "bounds_xyz_mm": _bounds(face, "overlap-region bound"),
        "vertex_xyz_mm": vertices,
        "edge_signatures": edges,
        "wire_count": len(face.Wires()),
    }


def source_face_records(member_id: str, shape: Any) -> list[dict[str, Any]]:
    """Return every planar source face with a STEP-body ordinal and signature."""
    records = []
    for index, face in enumerate(shape.Faces(), start=1):
        if face.geomType() != "PLANE" or float(face.Area()) <= 1e-8:
            continue
        signature = _face_signature_data(face)
        signature_sha = _canonical_sha256(signature)
        records.append(
            {
                "face_id": f"{member_id}/step-face-{index:04d}-{signature_sha[:16]}",
                "face_ordinal_1_based": index,
                "signature_sha256": signature_sha,
                "signature": signature,
                "_shape": face,
            }
        )
    ids = [row["face_id"] for row in records]
    ordinals = [row["face_ordinal_1_based"] for row in records]
    if len(ids) != len(set(ids)) or len(ordinals) != len(set(ordinals)):
        raise ValueError(f"{member_id}: planar face identities are not unique")
    return records


def _face_boxes_overlap(first: Any, second: Any, tolerance_mm: float) -> bool:
    a = _bounds(first, "first face bound")
    b = _bounds(second, "second face bound")
    return all(
        not (
            a[2 * axis + 1] < b[2 * axis] - tolerance_mm
            or b[2 * axis + 1] < a[2 * axis] - tolerance_mm
        )
        for axis in range(3)
    )


def _intersection_regions(first: Any, second: Any) -> list[dict[str, Any]]:
    common = first.intersect(second)
    regions = []
    for region in common.Faces():
        area = _finite(region.Area(), "overlap-region area")
        if area <= AREA_TOLERANCE_MM2:
            continue
        data = _region_geometry_data(region)
        regions.append(
            {
                "region_signature_sha256": _canonical_sha256(data),
                **data,
            }
        )
    regions.sort(
        key=lambda row: (
            row["region_signature_sha256"],
            row["area_mm2"],
            row["center_xyz_mm"],
        )
    )
    return regions


def collect_opposed_face_pairs(
    first_member: str,
    first_faces: list[dict[str, Any]],
    second_member: str,
    second_faces: list[dict[str, Any]],
    *,
    expected_area_mm2: float,
    expected_shared_area_mm2: float,
) -> dict[str, Any]:
    """Intersect source planar faces and reconcile against the frozen graph."""
    if not first_member or not second_member or first_member == second_member:
        raise ValueError("face-pair members must be distinct nonempty identities")
    expected_area = _finite(expected_area_mm2, "expected opposed area")
    expected_shared = _finite(expected_shared_area_mm2, "expected shared area")
    if expected_area <= AREA_TOLERANCE_MM2 or expected_shared <= AREA_TOLERANCE_MM2:
        raise ValueError("finite face-pair rows need positive graph areas")

    result = []
    for face_a in first_faces:
        shape_a = face_a["_shape"]
        normal_a = shape_a.normalAt().normalized()
        center_a = shape_a.Center()
        for face_b in second_faces:
            shape_b = face_b["_shape"]
            if not _face_boxes_overlap(shape_a, shape_b, GEOMETRY_TOLERANCE_MM):
                continue
            normal_b = shape_b.normalAt().normalized()
            dot = _finite(normal_a.dot(normal_b), "source face normal dot")
            if abs(abs(dot) - 1.0) > NORMAL_TOLERANCE:
                continue
            plane_offset = abs(
                _finite((shape_b.Center() - center_a).dot(normal_a), "plane offset")
            )
            if plane_offset > GEOMETRY_TOLERANCE_MM:
                continue
            regions = _intersection_regions(shape_a, shape_b)
            area = sum(_finite(row["area_mm2"], "overlap-region area") for row in regions)
            if area <= AREA_TOLERANCE_MM2:
                continue
            if dot >= 0.0:
                raise ValueError(
                    f"{first_member}|{second_member}: finite planar intersection is not opposed"
                )
            result.append(
                {
                    "face_a_id": face_a["face_id"],
                    "face_a_signature_sha256": face_a["signature_sha256"],
                    "face_b_id": face_b["face_id"],
                    "face_b_signature_sha256": face_b["signature_sha256"],
                    "face_a_oriented_normal_xyz": _vector3(normal_a, "face-a normal"),
                    "face_b_oriented_normal_xyz": _vector3(normal_b, "face-b normal"),
                    "normal_dot": _round9(dot, "normal dot"),
                    "coplanar_offset_mm": _round9(plane_offset, "plane offset"),
                    "overlap_area_mm2": _round9(area, "overlap area"),
                    "overlap_regions": regions,
                }
            )
    result.sort(
        key=lambda row: (
            row["face_a_id"],
            row["face_b_id"],
            row["overlap_area_mm2"],
        )
    )
    total = sum(row["overlap_area_mm2"] for row in result)
    allowed = max(AREA_TOLERANCE_MM2, expected_area * AREA_RECONCILIATION_REL_TOLERANCE)
    if not result or abs(total - expected_area) > allowed:
        raise ValueError(
            "source face intersections do not reproduce frozen opposed area: "
            f"{first_member}|{second_member} expected {expected_area:.12g} mm^2, "
            f"found {total:.12g} mm^2"
        )
    shared_allowed = max(AREA_TOLERANCE_MM2, expected_shared * AREA_RECONCILIATION_REL_TOLERANCE)
    if abs(total - expected_shared) > shared_allowed:
        raise ValueError(
            "source face intersections do not reproduce frozen total shared area: "
            f"{first_member}|{second_member} expected {expected_shared:.12g} mm^2, "
            f"found {total:.12g} mm^2"
        )
    return {
        "face_pairs": result,
        "face_pair_count": len(result),
        "reconstructed_opposed_area_mm2": _round9(total, "reconstructed opposed area"),
        "frozen_graph_opposed_area_mm2": _round9(expected_area, "frozen opposed area"),
        "frozen_graph_shared_area_mm2": _round9(expected_shared, "frozen shared area"),
        "area_reconciliation_tolerance_mm2": _round9(allowed, "area tolerance"),
    }


def _validate_revision_identity(candidate: Any, revision_id: Any) -> None:
    if candidate != EXPECTED_CANDIDATE:
        raise ValueError(f"stale or unsupported candidate: {candidate!r}")
    if revision_id != EXPECTED_REVISION:
        raise ValueError(f"stale or unsupported geometry revision: {revision_id!r}")


def _unique_index(rows: list[dict[str, Any]], key: str, label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        identity = row.get(key)
        if not isinstance(identity, str) or not identity:
            raise ValueError(f"{label} needs a nonempty {key}")
        if identity in result:
            raise ValueError(f"{label} contains duplicate {key}: {identity}")
        result[identity] = row
    return result


def _validate_graph_and_evidence(graph: dict[str, Any], evidence: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if graph.get("schema") != "wood_joint_current_contact_graph/v1":
        raise ValueError("unsupported current contact-graph schema")
    if graph.get("revision_id") != EXPECTED_REVISION:
        raise ValueError("contact graph revision is stale")
    if evidence.get("candidate") != EXPECTED_CANDIDATE:
        raise ValueError("attempt07 evidence candidate is stale")
    if evidence.get("revision_id") != EXPECTED_REVISION:
        raise ValueError("attempt07 evidence revision is stale")
    if evidence.get("criterion_disposition") != "pending":
        raise ValueError("geometry atlas requires overlap_contact to remain pending")
    if evidence.get("mechanics", {}).get("active_contact_established") is not False:
        raise ValueError("attempt07 evidence changed its mechanics boundary")

    counts = graph.get("counts", {})
    expected_graph_counts = {
        "physical_member_nodes": 50,
        "unique_member_pairs": 1225,
        "exact_brep_pairs_evaluated": 147,
        "aabb_separated_pairs_not_exactly_evaluated": 1078,
    }
    for key, expected in expected_graph_counts.items():
        if counts.get(key) != expected:
            raise ValueError(f"contact graph {key} changed: {counts.get(key)!r}")

    graph_by_pair = _unique_index(
        [
            {
                **row,
                "pair_id": "pair:" + "|".join(sorted(map(str, row.get("member_ids", [])))),
            }
            for row in graph.get("edges", [])
        ],
        "pair_id",
        "contact graph",
    )
    evidence_by_pair = _unique_index(evidence.get("pairs", []), "pair_id", "attempt07 evidence")
    if set(graph_by_pair) != set(evidence_by_pair) or len(graph_by_pair) != 1225:
        raise ValueError("attempt02 and attempt07 pair identity inventories differ")

    finite = []
    unresolved = []
    graph_state_counts = Counter()
    for pair_id, graph_row in graph_by_pair.items():
        evidence_row = evidence_by_pair[pair_id]
        members = graph_row.get("member_ids")
        if (
            not isinstance(members, list)
            or len(members) != 2
            or members != sorted(set(map(str, members)))
        ):
            raise ValueError(f"{pair_id}: graph member identities are not canonical")
        state = graph_row.get("geometry_state")
        graph_state_counts[state] += 1
        evidence_state = evidence_row.get("geometry_classification")
        if state == "finite_opposed_planar_touch":
            if evidence_state != "finite_opposed_planar_geometry":
                raise ValueError(f"{pair_id}: attempt07 class disagrees with graph")
            if graph_row.get("interface_geometry_state") != "finite_planar_face_contact":
                raise ValueError(f"{pair_id}: finite graph row lacks planar interface state")
            finite.append(graph_row)
        elif state == "zero_area_touch_or_unresolved":
            if evidence_state != "zero_area_or_unresolved_geometry":
                raise ValueError(f"{pair_id}: unresolved class disagrees with attempt07")
            unresolved.append(graph_row)
        elif state == "separated":
            if evidence_state not in {
                "exact_brep_separated_geometry",
                "aabb_separated_not_exactly_evaluated",
            }:
                raise ValueError(f"{pair_id}: separated class disagrees with attempt07")
        else:
            raise ValueError(f"{pair_id}: unsupported graph state {state!r}")
    if graph_state_counts != Counter(
        {
            "finite_opposed_planar_touch": 115,
            "separated": 1104,
            "zero_area_touch_or_unresolved": 6,
        }
    ):
        raise ValueError(f"contact-graph state counts changed: {dict(graph_state_counts)}")
    class_counts = evidence.get("counts", {}).get("geometry_classifications")
    if class_counts != EXPECTED_CLASS_COUNTS:
        raise ValueError("attempt07 geometry classification counts changed")
    if len(finite) != 115 or len(unresolved) != 6:
        raise ValueError("finite or unresolved interface count changed")
    return finite, unresolved


def _load_toolchain() -> tuple[Any, dict[str, str]]:
    import sys
    from importlib.metadata import version

    import cadquery as cq
    import OCP

    observed = {
        "python": ".".join(map(str, sys.version_info[:3])),
        "cadquery": str(cq.__version__),
        "cadquery_ocp": version("cadquery-ocp"),
        "ocp_module": str(OCP.__version__),
    }
    if observed != EXPECTED_TOOLCHAIN:
        raise RuntimeError(
            "unsupported CAD toolchain; refusing geometry substitution: "
            f"expected {EXPECTED_TOOLCHAIN}, observed {observed}"
        )
    return cq, observed


def _shape_summary(shape: Any) -> dict[str, Any]:
    bounds = shape.BoundingBox()
    center = shape.Center()
    surface_area_by_type: Counter[str] = Counter()
    for face in shape.Faces():
        surface_area_by_type[str(face.geomType())] += float(face.Area())
    return {
        "valid": bool(shape.isValid()),
        "solid_count": len(shape.Solids()),
        "shell_count": len(shape.Shells()),
        "face_count": len(shape.Faces()),
        "edge_count": len(shape.Edges()),
        "vertex_count": len(shape.Vertices()),
        "volume_mm3": _round9(shape.Volume(), "solid volume"),
        "surface_area_mm2": _round9(shape.Area(), "solid area"),
        "center_xyz_mm": _vector3(center, "solid center"),
        "bounds_xyz_mm": [
            _round9(value, "solid bound")
            for value in (
                bounds.xmin,
                bounds.xmax,
                bounds.ymin,
                bounds.ymax,
                bounds.zmin,
                bounds.zmax,
            )
        ],
        "surface_area_by_type_mm2": {
            key: _round9(value, "surface area by type")
            for key, value in sorted(surface_area_by_type.items())
        },
    }


def _add_pin(root: Path, pins: dict[str, str], relative: str, expected: str | None = None) -> None:
    path = root / relative
    if not path.is_file():
        raise FileNotFoundError(f"pinned source is missing: {relative}")
    actual = sha256_file(path)
    if expected is not None and actual != expected:
        raise ValueError(f"pinned source hash mismatch: {relative}")
    existing = pins.get(relative)
    if existing is not None and existing != actual:
        raise ValueError(f"conflicting source hashes for {relative}")
    pins[relative] = actual


def _verify_attempt02_map(root: Path) -> dict[str, Any]:
    verifier_path = root / MAP_PACKET_REL / "verify_packet.py"
    spec = importlib.util.spec_from_file_location(
        "_current_geometric_interface_map_attempt02_verify", verifier_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load the attempt02 public packet verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.verify(root)


def _current_source_hashes(root: Path = ROOT) -> dict[str, str]:
    root = Path(root)
    map_result = _verify_attempt02_map(root)
    if map_result.get("result") != "PASS" or map_result.get("step_files") != 50:
        raise ValueError("attempt02 geometric-interface packet did not verify")

    # The attempt07 public verifier authenticates its predecessor chain and
    # strict geometry-only evidence before this atlas consumes its pair set.
    from scripts import wood_joint_wj08_overlap_contact_geometry_attempt07 as attempt07

    overlap_result = attempt07.verify_packet(root=root)
    if (
        overlap_result.get("status") != "PASS_GEOMETRY_ONLY_CRITERION_PENDING"
        or overlap_result.get("criterion_disposition") != "pending"
    ):
        raise ValueError("attempt07 geometry packet did not verify as pending")

    source_hashes: dict[str, str] = {}

    # Carry the exact 142-source T04 map closure, including all 50 STEP files.
    map_pins = _load_json(root / MAP_PIN_REL)
    _validate_revision_identity(
        EXPECTED_CANDIDATE, map_pins.get("geometry_revision_id")
    )
    for source in map_pins.get("sources", []):
        if not isinstance(source, dict):
            raise TypeError("attempt02 source inventory contains a malformed row")
        _add_pin(root, source_hashes, source.get("path", ""), source.get("sha256"))

    # Preserve attempt07's inherited geometry/source chain after its verifier
    # has established that all of those bytes still match.
    evidence = _load_json(root / OVERLAP_EVIDENCE_REL)
    inherited = evidence.get("source_hashes")
    if not isinstance(inherited, dict):
        raise TypeError("attempt07 evidence has no source-hash inventory")
    for relative, expected in sorted(inherited.items()):
        _add_pin(root, source_hashes, relative, expected)

    # Explicit packet-file lists keep predecessor evidence append-only and
    # make changes to the verification method visible in this source closure.
    explicit_relative = [
        "current-candidate.json",
        "site/owner-wood-joints-review-report.json",
    ]
    explicit_relative.extend(
        (MAP_PACKET_REL / name).as_posix()
        for name in [
            "README.md",
            "source-pins.json",
            "complete-contact-graph.json",
            "receiver-screen.json",
            "scope-summary.json",
            "verify_packet.py",
            "SHA256SUMS",
        ]
    )
    explicit_relative += [
        (MAP_REVIEW_REL / name).as_posix()
        for name in ("README.md", "review-record.json", "SHA256SUMS")
    ]
    explicit_relative += [
        (OVERLAP_PACKET_REL / name).as_posix()
        for name in ("README.md", "geometry-evidence.json", "source-pins.json", "SHA256SUMS")
    ]
    for review_dir in OVERLAP_REVIEW_RELS:
        review_files = sorted(
            path.relative_to(root).as_posix()
            for path in (root / review_dir).iterdir()
            if path.is_file()
        )
        if not review_files:
            raise FileNotFoundError(f"attempt07 review packet is empty: {review_dir}")
        explicit_relative.extend(review_files)
    explicit_relative += [
        SOLIDS_MANIFEST_REL.as_posix(),
        INPUT_MANIFEST_REL.as_posix(),
        (SOLIDS_PACKET_REL / "produce.py").as_posix(),
        PRODUCER_REL.as_posix(),
        TEST_REL.as_posix(),
    ]
    for relative in explicit_relative:
        _add_pin(root, source_hashes, relative)
    return dict(sorted(source_hashes.items()))


def _predecessor_bindings(root: Path) -> dict[str, Any]:
    return {
        "attempt02_map": {
            "path": MAP_PACKET_REL.as_posix(),
            "complete_contact_graph_sha256": sha256_file(root / GRAPH_REL),
            "source_pins_sha256": sha256_file(root / MAP_PIN_REL),
            "public_verifier_sha256": sha256_file(root / MAP_PACKET_REL / "verify_packet.py"),
            "independent_review_sha256": sha256_file(root / MAP_REVIEW_REL / "review-record.json"),
        },
        "attempt07_inventory": {
            "path": OVERLAP_PACKET_REL.as_posix(),
            "geometry_evidence_sha256": sha256_file(root / OVERLAP_EVIDENCE_REL),
            "source_pins_sha256": sha256_file(root / OVERLAP_PACKET_REL / "source-pins.json"),
        },
        "current_member_solids": {
            "path": SOLIDS_PACKET_REL.as_posix(),
            "manifest_sha256": sha256_file(root / SOLIDS_MANIFEST_REL),
            "revision_id": EXPECTED_REVISION,
            "member_count": 50,
        },
    }


def _build_current(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, str], dict[str, str]]:
    root = Path(root)
    source_hashes = _current_source_hashes(root)
    graph = _load_json(root / GRAPH_REL)
    evidence = _load_json(root / OVERLAP_EVIDENCE_REL)
    finite_rows, unresolved_rows = _validate_graph_and_evidence(graph, evidence)

    solids_manifest = _load_json(root / SOLIDS_MANIFEST_REL)
    input_manifest = _load_json(root / INPUT_MANIFEST_REL)
    _validate_revision_identity(
        solids_manifest.get("candidate"), solids_manifest.get("geometry_revision_id")
    )
    _validate_revision_identity(
        input_manifest.get("candidate"), input_manifest.get("geometry_revision_id")
    )
    solid_readiness = solids_manifest.get("readiness", {})
    for flag in (
        "candidate_accepted",
        "criterion_resolved",
        "native_solve_executed",
        "full_frame_demands_available",
        "per_member_material_mapping_ready",
        "selected_structural_hardware_ready",
        "fabrication_released",
        "climbing_released",
    ):
        if solid_readiness.get(flag) is not False:
            raise ValueError(f"member-solids package flag {flag} must remain false")
    for key, value in solids_manifest.get("release", {}).items():
        if (key.endswith("released") or key == "candidate_accepted") and value is not False:
            raise ValueError(f"member-solids package release flag {key} must remain false")
    input_release = input_manifest.get("release", {})
    for flag in (
        "engineering_mvp_complete",
        "structural_released",
        "fabrication_released",
        "climbing_released",
        "candidate_accepted",
    ):
        if input_release.get(flag) is not False:
            raise ValueError(f"full-frame input manifest release flag {flag} must remain false")

    member_rows = solids_manifest.get("members")
    if not isinstance(member_rows, list) or len(member_rows) != 50:
        raise ValueError("current member-solids descriptor must bind exactly 50 bodies")
    member_by_id = _unique_index(member_rows, "member_id", "member-solids descriptor")
    graph_members = {
        str(row["member_id"]) for row in graph.get("inventories", {}).get("physical_members", [])
    }
    if set(member_by_id) != graph_members or len(graph_members) != 50:
        raise ValueError("exact STEP bodies do not join to all 50 graph body identities")

    cq, toolchain = _load_toolchain()
    shapes: dict[str, Any] = {}
    body_inventory = []
    body_faces: dict[str, list[dict[str, Any]]] = {}
    for member_id in sorted(member_by_id):
        row = member_by_id[member_id]
        relative = (SOLIDS_PACKET_REL / row["step_file"]).as_posix()
        if relative not in source_hashes or source_hashes[relative] != row.get("step_sha256"):
            raise ValueError(f"{member_id}: STEP source is not bound by current input hashes")
        imported = cq.importers.importStep(str(root / relative)).val()
        if len(imported.Solids()) != 1 or not imported.isValid():
            raise ValueError(f"{member_id}: STEP must import as exactly one valid solid")
        actual_summary = _shape_summary(imported)
        if actual_summary != row.get("step_roundtrip_summary"):
            raise ValueError(f"{member_id}: STEP readback differs from pinned descriptor")
        planar_faces = source_face_records(member_id, imported)
        shapes[member_id] = imported
        body_faces[member_id] = planar_faces
        body_inventory.append(
            {
                "member_id": member_id,
                "member_kind": row.get("member_kind"),
                "step_path": relative,
                "step_sha256": row["step_sha256"],
                "source_shape_fingerprint_sha256": row[
                    "source_shape_fingerprint_sha256"
                ],
                "shape_summary_sha256": row["shape_summary_sha256"],
                "solid_count": actual_summary["solid_count"],
                "face_count": actual_summary["face_count"],
                "planar_face_count": len(planar_faces),
                "planar_faces": [
                    {key: value for key, value in face.items() if key != "_shape"}
                    for face in planar_faces
                ],
            }
        )

    interfaces = []
    for graph_row in finite_rows:
        member_a, member_b = graph_row["member_ids"]
        measured = collect_opposed_face_pairs(
            member_a,
            body_faces[member_a],
            member_b,
            body_faces[member_b],
            expected_area_mm2=graph_row["opposed_planar_face_contact_area_mm2"],
            expected_shared_area_mm2=graph_row["finite_shared_planar_face_area_mm2"],
        )
        interfaces.append(
            {
                "pair_id": "pair:" + "|".join(graph_row["member_ids"]),
                "member_ids": graph_row["member_ids"],
                "source_geometry_classification": "finite_opposed_planar_geometry",
                "source_measurement_basis": graph_row["contact_measurement_basis"],
                "face_pair_count": measured["face_pair_count"],
                "reconstructed_opposed_area_mm2": measured[
                    "reconstructed_opposed_area_mm2"
                ],
                "frozen_graph_opposed_area_mm2": measured[
                    "frozen_graph_opposed_area_mm2"
                ],
                "frozen_graph_shared_area_mm2": measured[
                    "frozen_graph_shared_area_mm2"
                ],
                "area_reconciliation_tolerance_mm2": measured[
                    "area_reconciliation_tolerance_mm2"
                ],
                "face_pairs": measured["face_pairs"],
            }
        )
    interfaces.sort(key=lambda row: row["pair_id"])

    unresolved = []
    for row in sorted(unresolved_rows, key=lambda item: item["member_ids"]):
        unresolved.append(
            {
                "pair_id": "pair:" + "|".join(row["member_ids"]),
                "member_ids": row["member_ids"],
                "source_geometry_classification": "zero_area_or_unresolved_geometry",
                "interface_geometry_state": row["interface_geometry_state"],
                "finite_shared_planar_face_area_mm2": row[
                    "finite_shared_planar_face_area_mm2"
                ],
                "minimum_separation_mm": row["minimum_separation_mm"],
                "face_pair_mapping": "unresolved; no source face identity assigned",
            }
        )

    atlas = {
        "schema": SCHEMA,
        "candidate": EXPECTED_CANDIDATE,
        "revision_id": EXPECTED_REVISION,
        "criterion_id": "overlap_contact",
        "criterion_disposition": "pending",
        "evidence_status": "face_identity_geometry_only",
        "scope": SCOPE,
        "coordinate_units": "millimeters",
        "toolchain": toolchain,
        "method": {
            "source_body_identity": "all 50 exact STEP bodies from the independently checked T04 attempt02 member-solid descriptor",
            "source_face_identity": "one-based face ordinal from CadQuery STEP import plus geometry signature SHA-256; exact STEP file hash and toolchain are part of the identity context",
            "source_face_signature_fields": [
                "surface type",
                "area",
                "center",
                "oriented normal",
                "bounds",
                "vertices",
                "edge curve types/lengths/centers/bounds/endpoints",
                "wire count",
            ],
            "intersection_method": "CadQuery Shape.intersect on source planar faces, backed by OCP 7.9.3.1.1; retain only finite-area planar intersection faces",
            "candidate_filters": {
                "face_aabb_overlap_tolerance_mm": GEOMETRY_TOLERANCE_MM,
                "plane_normal_parallel_tolerance": NORMAL_TOLERANCE,
                "coplanarity_tolerance_mm": GEOMETRY_TOLERANCE_MM,
                "minimum_overlap_area_mm2": AREA_TOLERANCE_MM2,
                "opposed_normal_rule": "source-face normal dot product < 0 after parallel check",
            },
            "area_reconciliation": {
                "absolute_tolerance_mm2": AREA_TOLERANCE_MM2,
                "relative_tolerance": AREA_RECONCILIATION_REL_TOLERANCE,
                "target": "attempt02 graph opposed planar area and total shared planar area for each of the 115 finite opposed pairs",
            },
            "face_ordinal_limit": "Ordinal is stable for these pinned STEP bytes and the pinned CadQuery/OCP importer; it is not a native CAD face name or guaranteed cross-exporter identity.",
        },
        "counts": {
            "exact_step_bodies": len(body_inventory),
            "planar_source_faces": sum(row["planar_face_count"] for row in body_inventory),
            "finite_opposed_body_pairs": len(interfaces),
            "finite_opposed_source_face_pairs": sum(
                row["face_pair_count"] for row in interfaces
            ),
            "exact_separated_pairs_not_mapped": 26,
            "aabb_only_pairs_not_evaluated": 1078,
            "zero_area_or_unresolved_pairs_not_mapped": len(unresolved),
        },
        "body_inventory": body_inventory,
        "finite_opposed_interfaces": interfaces,
        "unresolved_pairs": unresolved,
        "mechanics": {
            "active_contact_established": False,
            "bearing_or_pressure_established": False,
            "contact_law_established": False,
            "load_path_ownership_established": False,
            "force_transfer_established": False,
            "capacity_established": False,
            "criterion_acceptance": False,
            "readiness": False,
            "release": False,
        },
        "limitations": [
            "Face identity is a reproducible geometry signature plus source STEP face ordinal, not a mechanical owner or active contact designation.",
            "The six exact-BRep zero-area/unresolved body pairs remain unresolved and have no assigned face mapping.",
            "The 1,078 AABB-only pairs were not exact-BRep evaluated here; no exact result is inferred for them.",
            "The 26 exact-BRep separated pairs are not included in this face atlas.",
            "Boolean face intersections and normals describe nominal STEP geometry only; they establish no bearing, pressure, gap law, load-path ownership, force transfer, stiffness, fastener engagement, resistance, response, equivalence, capacity, acceptance, fabrication release, or climbing release.",
            "Connector and fastener solids are not part of the 50-body member/panel inventory.",
        ],
    }
    return atlas, source_hashes, _predecessor_bindings(root)


def _render_readme(atlas: dict[str, Any], pins: dict[str, Any]) -> str:
    unresolved = "\n".join(
        f"- `{row['pair_id']}`: `{', '.join(row['member_ids'])}` (preserved unresolved)"
        for row in atlas["unresolved_pairs"]
    )
    counts = atlas["counts"]
    return f"""# Current geometric interface face-pair atlas — attempt 01

Status: **geometry-only face identity evidence; `overlap_contact` remains pending** for `{atlas['revision_id']}`.

The atlas binds all {counts['exact_step_bodies']} reviewed member/panel STEP bodies and maps {counts['finite_opposed_body_pairs']} finite opposed body-pair rows to {counts['finite_opposed_source_face_pairs']} exact planar source-face intersection regions. Per-body-pair area sums reproduce the independently reviewed attempt02 graph's opposed and total shared planar areas within the recorded tolerance. All {counts['planar_source_faces']} planar source faces are cataloged with a source-body face ordinal and geometry signature.

The mapping was rebuilt with CadQuery {atlas['toolchain']['cadquery']} / OCP {atlas['toolchain']['cadquery_ocp']} using the repository `.venv`. The face ordinal is scoped to the pinned STEP bytes and importer version; it is not a native CAD face name. Source-face normals, areas, and derived Boolean overlap-region geometry are included only for these reproducible exact intersections.

## Unresolved and excluded geometry

The six upstream zero-area/unresolved pairs remain unmapped:

{unresolved}

The {counts['exact_separated_pairs_not_mapped']} exact-BRep separated pairs and {counts['aabb_only_pairs_not_evaluated']} AABB-only pairs are not promoted into this map. No AABB-only pair is reported as an exact result.

## Reproduction

From the repository root, run:

```sh
.venv/bin/python -m scripts.wood_joint_current_face_pair_atlas_attempt01 --verify
(cd {PACKET_REL.as_posix()} && sha256sum -c SHA256SUMS)
```

The verifier first checks attempt02's current geometric-interface packet and attempt07's strict geometry-only inventory, then imports and checks all 50 exact STEP bodies, reconstructs the face signatures and Boolean face intersections, compares the complete canonical atlas, validates source/predecessor hashes and checksums, and rejects stale revision metadata or duplicate JSON object keys. The packet pins {len(pins['source_hashes'])} source files.

## Mechanical and release limits

This is nominal CAD geometry only. A face-pair identity is not a contact owner, contact law, active-bearing state, or load-path edge. The atlas establishes no bearing, pressure, force transfer, stiffness, fastener engagement, resistance, response, equivalence, capacity, criterion acceptance, engineering readiness, fabrication release, or climbing release. All readiness, acceptance, and release flags remain false.
"""


def _packet_checksum_text(output_dir: Path) -> str:
    return "".join(
        f"{sha256_file(output_dir / name)}  {name}\n" for name in ATLAS_FILES
    )


def freeze_packet(root: Path = ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    root = Path(root)
    output_dir = Path(output_dir) if output_dir else root / PACKET_REL
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Refusing to replace nonempty packet directory: {output_dir}")
    atlas, source_hashes, predecessor_bindings = _build_current(root)
    output_dir.mkdir(parents=True, exist_ok=True)
    atlas_path = output_dir / "face-pair-atlas.json"
    atlas_path.write_text(
        json.dumps(atlas, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    _, toolchain = _load_toolchain()
    pins = {
        "schema": PINS_SCHEMA,
        "attempt_id": ATTEMPT_ID,
        "candidate": EXPECTED_CANDIDATE,
        "revision_id": EXPECTED_REVISION,
        "source_hashes": source_hashes,
        "output_sha256": sha256_file(atlas_path),
        "scope": SCOPE,
        "criterion_disposition": "pending",
        "predecessor_bindings": predecessor_bindings,
        "toolchain": toolchain,
    }
    (output_dir / "source-pins.json").write_text(
        json.dumps(pins, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "README.md").write_text(_render_readme(atlas, pins), encoding="utf-8")
    (output_dir / "SHA256SUMS").write_text(
        _packet_checksum_text(output_dir), encoding="utf-8"
    )
    return {
        "status": "FROZEN_FACE_GEOMETRY_ONLY_PENDING",
        "candidate": EXPECTED_CANDIDATE,
        "revision_id": EXPECTED_REVISION,
        "counts": atlas["counts"],
        "source_hash_count": len(source_hashes),
    }


def verify_packet(root: Path = ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    root = Path(root)
    output_dir = Path(output_dir) if output_dir else root / PACKET_REL
    expected, source_hashes, predecessor_bindings = _build_current(root)
    pins = _load_json(output_dir / "source-pins.json")
    if not isinstance(pins, dict) or set(pins) != PIN_FIELDS:
        raise ValueError("source-pins fields are missing or unrecognized")
    if pins.get("schema") != PINS_SCHEMA or pins.get("attempt_id") != ATTEMPT_ID:
        raise ValueError("source-pins schema or attempt ID is stale")
    _validate_revision_identity(pins.get("candidate"), pins.get("revision_id"))
    if pins.get("scope") != SCOPE:
        raise ValueError("source-pins scope is stale or contradictory")
    if pins.get("criterion_disposition") != "pending":
        raise ValueError("face atlas cannot change overlap_contact disposition")
    if pins.get("source_hashes") != source_hashes:
        raise ValueError("source-pins do not match current verified inputs")
    if pins.get("predecessor_bindings") != predecessor_bindings:
        raise ValueError("predecessor bindings are stale")
    _, toolchain = _load_toolchain()
    if pins.get("toolchain") != toolchain:
        raise ValueError("source-pins toolchain differs from the current exact runtime")
    atlas_path = output_dir / "face-pair-atlas.json"
    if _canonical_json(_load_json(atlas_path)) != _canonical_json(expected):
        raise ValueError("face-pair atlas does not reproduce from pinned STEP geometry")
    if pins.get("output_sha256") != sha256_file(atlas_path):
        raise ValueError("face-pair atlas output hash differs from source-pins")
    if (output_dir / "README.md").read_text(encoding="utf-8") != _render_readme(
        expected, pins
    ):
        raise ValueError("README does not reproduce from the verified atlas")
    expected_names = set(ATLAS_FILES)
    parsed: dict[str, str] = {}
    for line in (output_dir / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, separator, filename = line.partition("  ")
        if not separator or not filename or filename in parsed:
            raise ValueError("malformed or duplicate SHA256SUMS row")
        parsed[filename] = digest
    if set(parsed) != expected_names:
        raise ValueError("SHA256SUMS does not cover exactly the atlas packet files")
    for filename, digest in parsed.items():
        if digest != sha256_file(output_dir / filename):
            raise ValueError(f"packet checksum mismatch: {filename}")
    return {
        "status": "PASS_FACE_GEOMETRY_ONLY_CRITERION_PENDING",
        "candidate": EXPECTED_CANDIDATE,
        "revision_id": EXPECTED_REVISION,
        "criterion_disposition": "pending",
        "counts": expected["counts"],
        "source_hash_count": len(source_hashes),
        "predecessor_bindings": predecessor_bindings,
    }


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze", action="store_true")
    mode.add_argument("--verify", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    result = (
        freeze_packet(output_dir=args.output_dir)
        if args.freeze
        else verify_packet(output_dir=args.output_dir)
    )
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
