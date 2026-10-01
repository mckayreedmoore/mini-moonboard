"""Reconcile geometry tolerances and pin the complete overlap evidence chain.

Attempt03 remains a geometry-only adapter. It does not establish active
contact, load transfer, mechanical response, or criterion acceptance.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts import wood_joint_wj08_overlap_contact_geometry_attempt02 as attempt02

ROOT = attempt02.ROOT
ATTEMPT_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-overlap-contact-geometry-evidence-attempt03"
)
PRODUCER_REL = Path("scripts/wood_joint_wj08_overlap_contact_geometry_attempt03.py")
TEST_REL = Path("tests/test_wood_joint_wj08_overlap_contact_geometry_attempt03.py")
T04_REL = attempt02.attempt01.T04_REL
T04_VERIFY_REL = T04_REL / "verify_packet.py"
T04_SUMS_REL = T04_REL / "SHA256SUMS"

ATTEMPT02_PACKET_HASHES = {
    attempt02.ATTEMPT_REL
    / "README.md": "090731fdddcfbe13a6dacc5f15c5b2f38aa5862edb325ad84092debb3878d152",
    attempt02.ATTEMPT_REL
    / "geometry-evidence.json": "9ec0e34f49d07074e86b39ee48f3eb6862d4ee615e191621534e4c111bde9df3",
    attempt02.ATTEMPT_REL
    / "source-pins.json": "0833b1a02f2b3243907e82baab159e1dfddc66cf50a348f1f38682f0bf4761cc",
    attempt02.ATTEMPT_REL
    / "SHA256SUMS": "36e3ee59062ebed3d8ef2948c066544d475924e4b8c69250b1df332af85d0c5d",
}
EXPECTED_ADDITIONAL_INPUTS = {
    T04_VERIFY_REL: "f839cfe233155bcd5ab56fea943cc2a13d211053d4876e98f4cb48dfdb3c3e43",
    T04_SUMS_REL: "478fc2b3ed41c47f73a0087a4ebf4b127cd9400ac771487c1a28e238ab50b960",
    Path(
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-overlap-contact-geometry-attempt02-correctness-review-2026-09-28/"
        "review-record.md"
    ): "2ded811c4913ec56665a4e03b3684380da2538a8212c728759738ccc5a096873",
    Path(
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-overlap-contact-geometry-attempt02-testing-review-2026-09-28/"
        "review-record.md"
    ): "4c5c6df4108541fe683bee8e98173c7383ef6b8b19a4bf458c8f2c04bc46da67",
    Path(
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-overlap-contact-geometry-attempt02-architecture-review-2026-09-28/"
        "review-record.md"
    ): "aa8eff4c41655fc4e82f2c6d8da26412e393a8c0bda30b7a04eba39690ae4c99",
}

GEOMETRY_TOLERANCE_MM = attempt02.GEOMETRY_TOLERANCE_MM
AREA_TOLERANCE_MM2 = attempt02.AREA_TOLERANCE_MM2
VOLUME_TOLERANCE_MM3 = 1e-6
EXACT_BREP_BASIS = attempt02.EXACT_BREP_BASIS
AABB_BASIS = attempt02.AABB_BASIS
SCHEMA = "wood_joint_overlap_contact_geometry_evidence/v3"
SOURCE_PINS_SCHEMA = "wood_joint_overlap_contact_geometry_source_pins/v3"
ATTEMPT_ID = "current-overlap-contact-geometry-evidence-attempt03"


def _load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _current_source_hashes(root: Path = ROOT) -> dict[str, str]:
    root = Path(root)
    hashes = attempt02._current_source_hashes(root)
    for rel, expected in ATTEMPT02_PACKET_HASHES.items():
        path = root / rel
        if not path.is_file():
            raise ValueError(f"Pinned attempt03 input is missing: {rel.as_posix()}")
        actual = attempt02.attempt01.sha256_file(path)
        if actual != expected:
            raise ValueError(f"Pinned attempt03 input hash mismatch: {rel.as_posix()}")
        hashes[rel.as_posix()] = actual
    for rel, expected in EXPECTED_ADDITIONAL_INPUTS.items():
        path = root / rel
        if not path.is_file():
            raise ValueError(f"Pinned attempt03 input is missing: {rel.as_posix()}")
        actual = attempt02.attempt01.sha256_file(path)
        if actual != expected:
            raise ValueError(f"Pinned attempt03 input hash mismatch: {rel.as_posix()}")
        hashes[rel.as_posix()] = actual

    # The attempt02 verifier invokes the upstream T04 packet verifier. Pin its
    # executable and checksum manifest above before relying on that rerun.
    attempt02.verify_packet(root=root)
    hashes[PRODUCER_REL.as_posix()] = attempt02.attempt01.sha256_file(
        root / PRODUCER_REL
    )
    hashes[TEST_REL.as_posix()] = attempt02.attempt01.sha256_file(root / TEST_REL)
    return dict(sorted(hashes.items()))


def _finite(value: Any) -> bool:
    return attempt02.attempt01._finite_nonnegative(value)


def validate_geometry_consistency(graph: dict[str, Any]) -> dict[str, int]:
    """Reject pair rows that contradict pinned geometry classification tolerances."""
    source = attempt02.attempt01
    if graph.get("schema") != "wood_joint_current_contact_graph/v1":
        raise ValueError("Unsupported upstream contact graph schema")
    if graph.get("revision_id") != source.EXPECTED_REVISION:
        raise ValueError("Upstream contact graph revision is stale")
    edges = graph.get("edges")
    if not isinstance(edges, list):
        raise TypeError("Upstream graph pair inventory is missing")

    counts: dict[str, int] = {}
    for edge in edges:
        if not isinstance(edge, dict):
            raise TypeError("Upstream graph contains a non-object pair")
        geometry_state = edge.get("geometry_state")
        interface_state = edge.get("interface_geometry_state")
        broadphase = edge.get("broadphase_candidate")
        basis = edge.get("contact_measurement_basis")
        distance = edge.get("minimum_separation_mm")
        lower_bound = edge.get("aabb_separation_lower_bound_mm")
        shared = edge.get("finite_shared_planar_face_area_mm2")
        opposed = edge.get("opposed_planar_face_contact_area_mm2")
        cooriented = edge.get("cooriented_planar_face_contact_area_mm2")
        volume = edge.get("common_volume_mm3")
        if not all(
            _finite(value)
            for value in (lower_bound, shared, opposed, cooriented, volume)
        ):
            raise ValueError(
                "Upstream pair has non-finite or negative geometric measurements"
            )

        if (
            geometry_state == "separated"
            and interface_state == "not_evaluated_aabb_separated"
        ):
            if (
                broadphase is not False
                or basis != AABB_BASIS
                or distance is not None
                or lower_bound <= GEOMETRY_TOLERANCE_MM
                or shared != 0
                or opposed != 0
                or cooriented != 0
                or volume != 0
            ):
                raise ValueError(
                    "AABB-only separated pair has contradictory exact geometry fields"
                )
            key = "aabb_separated_not_exactly_evaluated"
        elif (
            geometry_state == "finite_opposed_planar_touch"
            and interface_state == "finite_planar_face_contact"
        ):
            if (
                broadphase is not True
                or basis != EXACT_BREP_BASIS
                or not _finite(distance)
                or distance > GEOMETRY_TOLERANCE_MM
                or shared <= AREA_TOLERANCE_MM2
                or opposed <= AREA_TOLERANCE_MM2
                or abs(opposed - shared) > AREA_TOLERANCE_MM2
                or cooriented > AREA_TOLERANCE_MM2
                or volume > VOLUME_TOLERANCE_MM3
            ):
                raise ValueError(
                    "Finite-touch pair has contradictory exact geometry fields"
                )
            key = "finite_opposed_planar_geometry"
        elif geometry_state == "separated" and interface_state == "separated":
            if (
                broadphase is not True
                or basis != EXACT_BREP_BASIS
                or not _finite(distance)
                or distance <= GEOMETRY_TOLERANCE_MM
                or shared > AREA_TOLERANCE_MM2
                or opposed > AREA_TOLERANCE_MM2
                or cooriented > AREA_TOLERANCE_MM2
                or volume > VOLUME_TOLERANCE_MM3
            ):
                raise ValueError(
                    "Exact-BRep separated pair has contradictory distance/contact fields"
                )
            key = "exact_brep_separated_geometry"
        elif (
            geometry_state == "zero_area_touch_or_unresolved"
            and interface_state == "zero_area_touch_or_unresolved_contact"
        ):
            if (
                broadphase is not True
                or basis != EXACT_BREP_BASIS
                or not _finite(distance)
                or distance > GEOMETRY_TOLERANCE_MM
                or shared > AREA_TOLERANCE_MM2
                or opposed != 0
                or cooriented != 0
                or volume > VOLUME_TOLERANCE_MM3
            ):
                raise ValueError(
                    "Zero-area/unresolved pair has contradictory exact geometry fields"
                )
            key = "zero_area_or_unresolved_geometry"
        else:
            raise ValueError(
                "Unrecognized or contradictory geometry state: "
                f"{geometry_state!r}/{interface_state!r}"
            )
        counts[key] = counts.get(key, 0) + 1

    if counts != source.EXPECTED_CLASS_COUNTS:
        raise ValueError(f"Attempt03 geometry-class counts do not reconcile: {counts}")
    return dict(sorted(counts.items()))


def build_geometry_evidence(
    graph: dict[str, Any], source_hashes: dict[str, str]
) -> dict[str, Any]:
    counts = validate_geometry_consistency(graph)
    evidence = attempt02.attempt01.build_geometry_evidence(graph, source_hashes)
    evidence["schema"] = SCHEMA
    evidence["counts"]["geometry_classifications"] = counts
    evidence["upstream_classification_tolerances"] = {
        "distance_mm": GEOMETRY_TOLERANCE_MM,
        "face_area_mm2": AREA_TOLERANCE_MM2,
        "common_volume_mm3": VOLUME_TOLERANCE_MM3,
        "source": {
            attempt02.GRAPH_PRODUCER_REL.as_posix(): source_hashes[
                attempt02.GRAPH_PRODUCER_REL.as_posix()
            ],
            attempt02.RECEIVER_PRODUCER_REL.as_posix(): source_hashes[
                attempt02.RECEIVER_PRODUCER_REL.as_posix()
            ],
        },
        "interpretation": "Numerical geometry classification only; not an installed fit or contact law.",
    }
    return evidence


def _build_current(root: Path = ROOT) -> dict[str, Any]:
    root = Path(root)
    source_hashes = _current_source_hashes(root)
    graph = _load_json(root / attempt02.attempt01.GRAPH_REL)
    return build_geometry_evidence(graph, source_hashes)


def _predecessor_review_records() -> list[dict[str, str]]:
    return [
        {"path": rel.as_posix(), "sha256": digest}
        for rel, digest in EXPECTED_ADDITIONAL_INPUTS.items()
        if "review-record.md" in rel.name
    ]


def _render_readme(evidence: dict[str, Any], pins: dict[str, Any]) -> str:
    counts = evidence["counts"]
    classes = counts["geometry_classifications"]
    return f"""# `overlap_contact` geometry inventory — attempt 03

Status: **partial geometry evidence only; criterion remains pending** for
`{evidence["revision_id"]}`.

Attempt03 preserves the attempt02 inventory and aligns consistency checks with
the pinned upstream distance, face-area, and common-volume classification
tolerances. It binds the three attempt02 independent review records, the full
attempt02 packet, and the upstream T04 verifier and checksum manifest. Tests
exercise a temporary freeze/verify/checksum cycle.

The inventory contains {counts["physical_member_nodes"]} nodes and
{counts["unordered_member_pairs"]} unordered pairs: {counts["exact_brep_evaluated_pairs"]}
were evaluated by exact BRep, while
{counts["aabb_separated_not_exactly_evaluated_pairs"]} were excluded by disjoint
AABBs and were not exact-BRep evaluated. Classifications are
{classes["finite_opposed_planar_geometry"]} finite opposed planar touches,
{classes["exact_brep_separated_geometry"]} exact-BRep separated pairs,
{classes["aabb_separated_not_exactly_evaluated"]} AABB-only pairs, and
{classes["zero_area_or_unresolved_geometry"]} zero-area/unresolved pairs.

No face-owner IDs, contact law, active-contact state, or load-path owner is
inferred. Connector and fastener solids are outside the 50-node member/panel
graph. The six unresolved pairs remain unresolved. This evidence does not
establish bearing, pressure, force transfer, capacity, case response, or
acceptance; `overlap_contact` remains `pending`.

## Reproduction

From the repository root, run:

```sh
.venv/bin/python -m scripts.wood_joint_wj08_overlap_contact_geometry_attempt03 --verify
(cd docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-overlap-contact-geometry-evidence-attempt03 && sha256sum -c SHA256SUMS)
```

The verifier revalidates the frozen attempt02 packet, reruns the pinned T04
verifier, checks every bound source hash, applies upstream-consistent
measurement thresholds, and compares the frozen output byte-for-byte after
canonical JSON parsing. The packet pins {len(pins["source_hashes"])} repository
inputs, including the T04 verifier/checksum manifest and all three attempt02
independent reviews. The criterion status stays pending.
"""


def _packet_files() -> list[str]:
    return ["README.md", "geometry-evidence.json", "source-pins.json"]


def freeze_packet(root: Path = ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    root = Path(root)
    output_dir = Path(output_dir) if output_dir else root / ATTEMPT_REL
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(
            f"Refusing to replace nonempty packet directory: {output_dir}"
        )
    evidence = _build_current(root)
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = output_dir / "geometry-evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    pins = {
        "schema": SOURCE_PINS_SCHEMA,
        "attempt_id": ATTEMPT_ID,
        "candidate": attempt02.attempt01.EXPECTED_CANDIDATE,
        "revision_id": attempt02.attempt01.EXPECTED_REVISION,
        "source_hashes": evidence["source_hashes"],
        "output_sha256": attempt02.attempt01.sha256_file(evidence_path),
        "criterion_disposition": "pending",
        "scope": "partial member/panel geometric pair inventory; no mechanics or acceptance",
        "predecessor_packet": {
            "path": attempt02.ATTEMPT_REL.as_posix(),
            "files": {
                rel.name: digest for rel, digest in ATTEMPT02_PACKET_HASHES.items()
            },
        },
        "upstream_verifier": {
            "path": T04_VERIFY_REL.as_posix(),
            "sha256": EXPECTED_ADDITIONAL_INPUTS[T04_VERIFY_REL],
            "checksum_manifest_path": T04_SUMS_REL.as_posix(),
            "checksum_manifest_sha256": EXPECTED_ADDITIONAL_INPUTS[T04_SUMS_REL],
        },
        "predecessor_reviews": _predecessor_review_records(),
    }
    (output_dir / "source-pins.json").write_text(
        json.dumps(pins, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "README.md").write_text(
        _render_readme(evidence, pins), encoding="utf-8"
    )
    sums = [
        f"{attempt02.attempt01.sha256_file(output_dir / relative)}  {relative}"
        for relative in _packet_files()
    ]
    (output_dir / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")
    return pins


def verify_packet(root: Path = ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    root = Path(root)
    output_dir = Path(output_dir) if output_dir else root / ATTEMPT_REL
    expected = _build_current(root)
    pins = _load_json(output_dir / "source-pins.json")
    if pins.get("schema") != SOURCE_PINS_SCHEMA or pins.get("attempt_id") != ATTEMPT_ID:
        raise ValueError("Unsupported or stale attempt03 source-pins record")
    evidence_path = output_dir / "geometry-evidence.json"
    evidence = _load_json(evidence_path)
    if evidence != expected:
        raise ValueError("Attempt03 evidence does not reproduce from pinned inputs")
    if pins.get("source_hashes") != expected["source_hashes"]:
        raise ValueError("Attempt03 source pins do not match current repository inputs")
    if pins.get("output_sha256") != attempt02.attempt01.sha256_file(evidence_path):
        raise ValueError("Attempt03 output hash differs from source pins")
    if pins.get("criterion_disposition") != "pending":
        raise ValueError("Attempt03 cannot change the overlap_contact disposition")
    if pins.get("predecessor_packet") != {
        "path": attempt02.ATTEMPT_REL.as_posix(),
        "files": {rel.name: digest for rel, digest in ATTEMPT02_PACKET_HASHES.items()},
    }:
        raise ValueError("Attempt03 predecessor packet binding is stale")
    if pins.get("upstream_verifier") != {
        "path": T04_VERIFY_REL.as_posix(),
        "sha256": EXPECTED_ADDITIONAL_INPUTS[T04_VERIFY_REL],
        "checksum_manifest_path": T04_SUMS_REL.as_posix(),
        "checksum_manifest_sha256": EXPECTED_ADDITIONAL_INPUTS[T04_SUMS_REL],
    }:
        raise ValueError("Attempt03 upstream verifier binding is stale")
    if pins.get("predecessor_reviews") != _predecessor_review_records():
        raise ValueError("Attempt03 predecessor review bindings are stale")
    if (output_dir / "README.md").read_text(encoding="utf-8") != _render_readme(
        expected, pins
    ):
        raise ValueError("Attempt03 README does not reproduce")
    parsed: dict[str, str] = {}
    for line in (output_dir / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, separator, filename = line.partition("  ")
        if not separator or filename in parsed:
            raise ValueError("Malformed or duplicate attempt03 SHA256SUMS row")
        parsed[filename] = digest
    if set(parsed) != set(_packet_files()):
        raise ValueError("Attempt03 SHA256SUMS does not cover exactly the packet files")
    for filename, digest in parsed.items():
        if digest != attempt02.attempt01.sha256_file(output_dir / filename):
            raise ValueError(f"Attempt03 packet checksum mismatch: {filename}")
    return {
        "status": "PASS_GEOMETRY_ONLY_CRITERION_PENDING",
        "criterion_id": "overlap_contact",
        "criterion_disposition": "pending",
        "counts": expected["counts"],
        "classification_tolerances": {
            "distance_mm": GEOMETRY_TOLERANCE_MM,
            "face_area_mm2": AREA_TOLERANCE_MM2,
            "common_volume_mm3": VOLUME_TOLERANCE_MM3,
        },
    }


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze", action="store_true")
    mode.add_argument("--verify", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.freeze:
        pins = freeze_packet(output_dir=args.output_dir)
        print(
            json.dumps(
                {"status": "FROZEN_GEOMETRY_ONLY_PENDING", "pins": pins}, indent=2
            )
        )
        return 0
    print(json.dumps(verify_packet(output_dir=args.output_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
