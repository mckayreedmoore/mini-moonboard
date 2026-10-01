"""Strengthen and re-freeze the overlap-contact geometry adapter.

Attempt02 rejects graph rows whose exact-distance values contradict their
geometry states. It still reports geometry only and leaves the criterion
pending.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts import wood_joint_wj08_overlap_contact_geometry as attempt01

ROOT = Path(__file__).resolve().parents[1]
ATTEMPT_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-overlap-contact-geometry-evidence-attempt02"
)
PRODUCER_REL = Path("scripts/wood_joint_wj08_overlap_contact_geometry_attempt02.py")
TEST_REL = Path("tests/test_wood_joint_wj08_overlap_contact_geometry_attempt02.py")
GRAPH_PRODUCER_REL = Path("scripts/wood_joint_current_contact_graph.py")
RECEIVER_PRODUCER_REL = Path("scripts/wood_joint_current_receiver_screen.py")
PREDECESSOR_REVIEW_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-overlap-contact-geometry-evidence-attempt01-independent-review-2026-09-28/"
    "review-record.md"
)

EXPECTED_EXTRA_INPUTS = {
    GRAPH_PRODUCER_REL: "8afed27a493719354c55b6c0deb5faeb1cd40068519d4578c365db120f293f7d",
    RECEIVER_PRODUCER_REL: "e827d30f6dfdffed3bd9f17a7f905e03d4c936c56a8a0d0890ca3b1dcfb2caa2",
    PREDECESSOR_REVIEW_REL: "57d0328624e5b37efdd99ec63a0c7795428e1aa8bea01b746fa8d19de086f01c",
}

GEOMETRY_TOLERANCE_MM = 1e-5
AREA_TOLERANCE_MM2 = 1e-6
EXACT_BREP_BASIS = "exact BRep via current receiver interface helper"
AABB_BASIS = (
    "disjoint cached AABBs; lower bound only, exact BRep distance not evaluated"
)
SCHEMA = "wood_joint_overlap_contact_geometry_evidence/v2"
SOURCE_PINS_SCHEMA = "wood_joint_overlap_contact_geometry_source_pins/v2"
ATTEMPT_ID = "current-overlap-contact-geometry-evidence-attempt02"


def _load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _current_source_hashes(root: Path = ROOT) -> dict[str, str]:
    root = Path(root)
    # The predecessor verifier binds the reviewed graph, criterion policy,
    # candidate authority, and its first-generation adapter inputs.
    hashes = attempt01._load_and_check_pinned_inputs(root)
    for rel, expected in EXPECTED_EXTRA_INPUTS.items():
        path = root / rel
        if not path.is_file():
            raise ValueError(f"Pinned attempt02 input is missing: {rel.as_posix()}")
        actual = attempt01.sha256_file(path)
        if actual != expected:
            raise ValueError(f"Pinned attempt02 input hash mismatch: {rel.as_posix()}")
        hashes[rel.as_posix()] = actual
    hashes[PRODUCER_REL.as_posix()] = attempt01.sha256_file(root / PRODUCER_REL)
    hashes[TEST_REL.as_posix()] = attempt01.sha256_file(root / TEST_REL)
    return dict(sorted(hashes.items()))


def validate_geometry_consistency(graph: dict[str, Any]) -> dict[str, int]:
    """Reject pair rows whose exact measurement contradicts the source state."""
    if graph.get("schema") != "wood_joint_current_contact_graph/v1":
        raise ValueError("Unsupported upstream contact graph schema")
    if graph.get("revision_id") != attempt01.EXPECTED_REVISION:
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
        measurements = (lower_bound, shared, opposed, cooriented, volume)
        if not all(attempt01._finite_nonnegative(value) for value in measurements):
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
                or not attempt01._finite_nonnegative(distance)
                or distance > GEOMETRY_TOLERANCE_MM
                or shared <= AREA_TOLERANCE_MM2
                or opposed <= AREA_TOLERANCE_MM2
                or abs(opposed - shared) > AREA_TOLERANCE_MM2
                or cooriented > AREA_TOLERANCE_MM2
                or volume != 0
            ):
                raise ValueError(
                    "Finite-touch pair has contradictory exact geometry fields"
                )
            key = "finite_opposed_planar_geometry"
        elif geometry_state == "separated" and interface_state == "separated":
            if (
                broadphase is not True
                or basis != EXACT_BREP_BASIS
                or not attempt01._finite_nonnegative(distance)
                or distance <= GEOMETRY_TOLERANCE_MM
                or shared != 0
                or opposed != 0
                or cooriented != 0
                or volume != 0
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
                or not attempt01._finite_nonnegative(distance)
                or distance > GEOMETRY_TOLERANCE_MM
                or shared != 0
                or opposed != 0
                or cooriented != 0
                or volume != 0
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

    if counts != attempt01.EXPECTED_CLASS_COUNTS:
        raise ValueError(f"Attempt02 geometry-class counts do not reconcile: {counts}")
    return dict(sorted(counts.items()))


def build_geometry_evidence(
    graph: dict[str, Any], source_hashes: dict[str, str]
) -> dict[str, Any]:
    counts = validate_geometry_consistency(graph)
    evidence = attempt01.build_geometry_evidence(graph, source_hashes)
    evidence["schema"] = SCHEMA
    evidence["counts"]["geometry_classifications"] = counts
    evidence["upstream_classification_tolerances"] = {
        "distance_mm": GEOMETRY_TOLERANCE_MM,
        "face_area_mm2": AREA_TOLERANCE_MM2,
        "source": {
            GRAPH_PRODUCER_REL.as_posix(): source_hashes[GRAPH_PRODUCER_REL.as_posix()],
            RECEIVER_PRODUCER_REL.as_posix(): source_hashes[
                RECEIVER_PRODUCER_REL.as_posix()
            ],
        },
        "interpretation": "Numerical geometry classification only; not an installed fit or contact law.",
    }
    return evidence


def _build_current(root: Path = ROOT) -> dict[str, Any]:
    root = Path(root)
    source_hashes = _current_source_hashes(root)
    graph = _load_json(root / attempt01.GRAPH_REL)
    return build_geometry_evidence(graph, source_hashes)


def _render_readme(evidence: dict[str, Any], pins: dict[str, Any]) -> str:
    counts = evidence["counts"]
    classes = counts["geometry_classifications"]
    return f"""# `overlap_contact` geometry inventory — attempt 02

Status: **partial geometry evidence only; criterion remains pending** for
`{evidence["revision_id"]}`.

Attempt02 retains the attempt01 member/panel pair inventory and adds strict
consistency checks against the pinned upstream distance (`1e-5 mm`) and face
area (`1e-6 mm²`) classification tolerances. It rejects exact-separated rows
at or below the distance tolerance, finite-touch rows beyond that tolerance,
and contradictory AABB/unresolved measurement states. The prior independent
review recorded these classifier and README command findings; this packet
addresses both.

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
.venv/bin/python -m scripts.wood_joint_wj08_overlap_contact_geometry_attempt02 --verify
(cd docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-overlap-contact-geometry-evidence-attempt02 && sha256sum -c SHA256SUMS)
```

The verifier reruns the reviewed upstream T04 check, validates all bound source
hashes, applies the stricter distance/state checks, and compares the frozen
output byte-for-byte after canonical JSON parsing. The packet pins
{len(pins["source_hashes"])} repository inputs, including the attempt01 review,
both geometry producers, this producer, and its focused tests. The criterion
status stays pending.
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
    attempt01._run_upstream_verifier(root)
    evidence = _build_current(root)
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = output_dir / "geometry-evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    pins = {
        "schema": SOURCE_PINS_SCHEMA,
        "attempt_id": ATTEMPT_ID,
        "candidate": attempt01.EXPECTED_CANDIDATE,
        "revision_id": attempt01.EXPECTED_REVISION,
        "source_hashes": evidence["source_hashes"],
        "output_sha256": attempt01.sha256_file(evidence_path),
        "criterion_disposition": "pending",
        "scope": "partial member/panel geometric pair inventory; no mechanics or acceptance",
        "predecessor_review": {
            "path": PREDECESSOR_REVIEW_REL.as_posix(),
            "sha256": EXPECTED_EXTRA_INPUTS[PREDECESSOR_REVIEW_REL],
            "findings_addressed": ["F-01", "F-02"],
        },
    }
    (output_dir / "source-pins.json").write_text(
        json.dumps(pins, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "README.md").write_text(
        _render_readme(evidence, pins), encoding="utf-8"
    )
    sums = [
        f"{attempt01.sha256_file(output_dir / relative)}  {relative}"
        for relative in _packet_files()
    ]
    (output_dir / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")
    return pins


def verify_packet(root: Path = ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    root = Path(root)
    output_dir = Path(output_dir) if output_dir else root / ATTEMPT_REL
    attempt01._run_upstream_verifier(root)
    pins = _load_json(output_dir / "source-pins.json")
    if pins.get("schema") != SOURCE_PINS_SCHEMA or pins.get("attempt_id") != ATTEMPT_ID:
        raise ValueError("Unsupported or stale attempt02 source-pins record")
    expected = _build_current(root)
    evidence_path = output_dir / "geometry-evidence.json"
    evidence = _load_json(evidence_path)
    if evidence != expected:
        raise ValueError(
            "Attempt02 evidence does not reproduce from pinned current inputs"
        )
    if pins.get("source_hashes") != expected["source_hashes"]:
        raise ValueError("Attempt02 source pins do not match current repository inputs")
    if pins.get("output_sha256") != attempt01.sha256_file(evidence_path):
        raise ValueError("Attempt02 output hash differs from source pins")
    if pins.get("criterion_disposition") != "pending":
        raise ValueError("Attempt02 cannot change the overlap_contact disposition")
    if pins.get("predecessor_review") != {
        "path": PREDECESSOR_REVIEW_REL.as_posix(),
        "sha256": EXPECTED_EXTRA_INPUTS[PREDECESSOR_REVIEW_REL],
        "findings_addressed": ["F-01", "F-02"],
    }:
        raise ValueError("Attempt02 predecessor review binding is stale")
    if (output_dir / "README.md").read_text(encoding="utf-8") != _render_readme(
        expected, pins
    ):
        raise ValueError("Attempt02 README does not reproduce")
    sums = (output_dir / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    parsed: dict[str, str] = {}
    for line in sums:
        digest, separator, filename = line.partition("  ")
        if not separator or filename in parsed:
            raise ValueError("Malformed or duplicate attempt02 SHA256SUMS row")
        parsed[filename] = digest
    if set(parsed) != set(_packet_files()):
        raise ValueError("Attempt02 SHA256SUMS does not cover exactly the packet files")
    for filename, digest in parsed.items():
        if digest != attempt01.sha256_file(output_dir / filename):
            raise ValueError(f"Attempt02 packet checksum mismatch: {filename}")
    return {
        "status": "PASS_GEOMETRY_ONLY_CRITERION_PENDING",
        "criterion_id": "overlap_contact",
        "criterion_disposition": "pending",
        "counts": expected["counts"],
        "classification_tolerances": {
            "distance_mm": GEOMETRY_TOLERANCE_MM,
            "face_area_mm2": AREA_TOLERANCE_MM2,
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
