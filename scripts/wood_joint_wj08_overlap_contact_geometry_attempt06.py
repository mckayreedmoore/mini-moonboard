"""Enforce strict JSON evidence equality for the overlap geometry inventory.

Attempt06 remains geometry-only and keeps ``overlap_contact`` pending.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from scripts import wood_joint_wj08_overlap_contact_geometry_attempt05 as attempt05

ROOT = Path(__file__).resolve().parents[1]
ATTEMPT_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-overlap-contact-geometry-evidence-attempt06"
)
PRODUCER_REL = Path("scripts/wood_joint_wj08_overlap_contact_geometry_attempt06.py")
TEST_REL = Path("tests/test_wood_joint_wj08_overlap_contact_geometry_attempt06.py")
GRAPH_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-geometric-interface-map-attempt02-2026-09-28/complete-contact-graph.json"
)
GRAPH_PRODUCER_REL = Path("scripts/wood_joint_current_contact_graph.py")
RECEIVER_PRODUCER_REL = Path("scripts/wood_joint_current_receiver_screen.py")
EXPECTED_CANDIDATE = "compact-floor-flush-wood-joints-development"
EXPECTED_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_CLASS_COUNTS = {
    "aabb_separated_not_exactly_evaluated": 1078,
    "exact_brep_separated_geometry": 26,
    "finite_opposed_planar_geometry": 115,
    "zero_area_or_unresolved_geometry": 6,
}
SCOPE = "partial member/panel geometric pair inventory; no mechanics or acceptance"

PREDECESSOR_PACKET_HASHES = {
    attempt05.ATTEMPT_REL
    / "README.md": "420301193bd8a98b21386e69e073b5f4037ebcdd2d84fcd6cbf25db7a93fa2d8",
    attempt05.ATTEMPT_REL
    / "geometry-evidence.json": "4a709240b65d01288fdd4ce66e84b338ebda9a7d1bdf0b64c7904ac9c925a538",
    attempt05.ATTEMPT_REL
    / "source-pins.json": "681727cfb78207ff78b0154a61258e7520957f1d51d46f4cb6bb37ca556e95db",
    attempt05.ATTEMPT_REL
    / "SHA256SUMS": "9bb82b634b2c2e942543d8c63a210e08d9b7b582e95bfb8ef1445c00ea7df85d",
}
PREDECESSOR_REVIEWS = {
    Path(
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-overlap-contact-geometry-attempt05-correctness-review-2026-09-28/"
        "review-record.md"
    ): "cbc6616e36ddfbfefa7edabeda9c28c797abbedf309a7fdeeca73aca27ac2878",
    Path(
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-overlap-contact-geometry-attempt05-testing-review-2026-09-28/"
        "review-record.md"
    ): "fbd11f24fade90b8e25341ea4ae7eaf13195b3e8fce6c7625080d70f5511dfc9",
    Path(
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-overlap-contact-geometry-attempt05-architecture-review-2026-09-28/"
        "architecture-review.md"
    ): "5856b74418fb04ea351226d91aab40fc6d6611c880ab0e579e92eb8d1e9eb9f3",
}

SCHEMA = "wood_joint_overlap_contact_geometry_evidence/v6"
SOURCE_PINS_SCHEMA = "wood_joint_overlap_contact_geometry_source_pins/v6"
ATTEMPT_ID = "current-overlap-contact-geometry-evidence-attempt06"
SOURCE_PINS_FIELDS = {
    "schema",
    "attempt_id",
    "candidate",
    "revision_id",
    "source_hashes",
    "output_sha256",
    "criterion_disposition",
    "scope",
    "predecessor_packet",
    "predecessor_reviews",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


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


def _verify_fixed_hashes(
    root: Path, expected_hashes: dict[Path, str], label: str
) -> dict[str, str]:
    root = Path(root)
    verified: dict[str, str] = {}
    for rel, expected in expected_hashes.items():
        path = root / rel
        if not path.is_file():
            raise ValueError(f"Pinned {label} input is missing: {rel.as_posix()}")
        actual = sha256_file(path)
        if actual != expected:
            raise ValueError(f"Pinned {label} input hash mismatch: {rel.as_posix()}")
        verified[rel.as_posix()] = actual
    return verified


def _current_source_hashes(root: Path = ROOT) -> dict[str, str]:
    root = Path(root)
    # Treat the reviewed predecessor as a black-box verifier. Its frozen source
    # pins are imported only after its public verifier has validated them.
    attempt05.verify_packet(root=root)
    predecessor_pin_path = root / attempt05.ATTEMPT_REL / "source-pins.json"
    predecessor_pins = _load_json(predecessor_pin_path)
    inherited = predecessor_pins.get("source_hashes")
    if not isinstance(inherited, dict) or not all(
        isinstance(path, str) and isinstance(digest, str)
        for path, digest in inherited.items()
    ):
        raise ValueError("Attempt05 source pins lack a valid inherited hash map")
    hashes = dict(inherited)
    hashes.update(_verify_fixed_hashes(root, PREDECESSOR_PACKET_HASHES, "attempt06"))
    hashes.update(_verify_fixed_hashes(root, PREDECESSOR_REVIEWS, "attempt06"))
    hashes[PRODUCER_REL.as_posix()] = sha256_file(root / PRODUCER_REL)
    hashes[TEST_REL.as_posix()] = sha256_file(root / TEST_REL)
    return dict(sorted(hashes.items()))


def validate_geometry_consistency(graph: dict[str, Any]) -> dict[str, int]:
    """Apply the predecessor's source-bound geometry threshold checks."""
    return attempt05.validate_geometry_consistency(graph)


def build_geometry_evidence(
    graph: dict[str, Any], source_hashes: dict[str, str]
) -> dict[str, Any]:
    evidence = attempt05.build_geometry_evidence(graph, source_hashes)
    evidence["schema"] = SCHEMA
    return evidence


def _build_current(root: Path = ROOT) -> dict[str, Any]:
    root = Path(root)
    source_hashes = _current_source_hashes(root)
    return build_geometry_evidence(_load_json(root / GRAPH_REL), source_hashes)


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _predecessor_packet_record() -> dict[str, Any]:
    return {
        "path": attempt05.ATTEMPT_REL.as_posix(),
        "files": {
            rel.name: digest for rel, digest in PREDECESSOR_PACKET_HASHES.items()
        },
    }


def _predecessor_review_records() -> list[dict[str, str]]:
    return [
        {"path": rel.as_posix(), "sha256": digest}
        for rel, digest in PREDECESSOR_REVIEWS.items()
    ]


def _render_readme(evidence: dict[str, Any], pins: dict[str, Any]) -> str:
    counts = evidence["counts"]
    classes = counts["geometry_classifications"]
    return f"""# `overlap_contact` geometry inventory — attempt 05

Status: **partial geometry evidence only; criterion remains pending** for
`{evidence["revision_id"]}`.

Attempt06 retains the reviewed geometry inventory and tolerance checks. It
uses attempt05's public packet verifier, rejects duplicate JSON object keys,
requires the exact source-pin fields, and compares canonical JSON encodings so
JSON booleans and numbers cannot compare equal by Python's loose value rules.

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
.venv/bin/python -m scripts.wood_joint_wj08_overlap_contact_geometry_attempt06 --verify
(cd docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-overlap-contact-geometry-evidence-attempt06 && sha256sum -c SHA256SUMS)
```

The verifier checks the attempt05 packet and its reviews, reuses its validated
source-hash chain, validates the candidate/revision/scope metadata, applies the
upstream-consistent measurement thresholds, and compares canonical JSON
representations of the frozen and regenerated evidence. It rejects duplicate
JSON object keys and unrecognized source-pin fields. The packet pins
{len(pins["source_hashes"])} repository inputs. The criterion status stays
pending.
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
        "candidate": EXPECTED_CANDIDATE,
        "revision_id": EXPECTED_REVISION,
        "source_hashes": evidence["source_hashes"],
        "output_sha256": sha256_file(evidence_path),
        "criterion_disposition": "pending",
        "scope": SCOPE,
        "predecessor_packet": _predecessor_packet_record(),
        "predecessor_reviews": _predecessor_review_records(),
    }
    (output_dir / "source-pins.json").write_text(
        json.dumps(pins, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "README.md").write_text(
        _render_readme(evidence, pins), encoding="utf-8"
    )
    sums = [f"{sha256_file(output_dir / rel)}  {rel}" for rel in _packet_files()]
    (output_dir / "SHA256SUMS").write_text("\n".join(sums) + "\n", encoding="utf-8")
    return pins


def verify_packet(root: Path = ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    root = Path(root)
    output_dir = Path(output_dir) if output_dir else root / ATTEMPT_REL
    expected = _build_current(root)
    pins = _load_json(output_dir / "source-pins.json")
    if not isinstance(pins, dict) or set(pins) != SOURCE_PINS_FIELDS:
        raise ValueError("Attempt06 source-pins fields are missing or unrecognized")
    if pins.get("schema") != SOURCE_PINS_SCHEMA or pins.get("attempt_id") != ATTEMPT_ID:
        raise ValueError("Unsupported or stale attempt06 source-pins record")
    if pins.get("candidate") != EXPECTED_CANDIDATE:
        raise ValueError("Attempt06 source-pins candidate is stale or contradictory")
    if pins.get("revision_id") != EXPECTED_REVISION:
        raise ValueError("Attempt06 source-pins revision is stale or contradictory")
    if pins.get("scope") != SCOPE:
        raise ValueError("Attempt06 source-pins scope is stale or contradictory")
    if _canonical_json(
        _load_json(output_dir / "geometry-evidence.json")
    ) != _canonical_json(expected):
        raise ValueError("Attempt06 evidence does not reproduce from pinned inputs")
    if pins.get("source_hashes") != expected["source_hashes"]:
        raise ValueError("Attempt06 source pins do not match current repository inputs")
    if pins.get("output_sha256") != sha256_file(output_dir / "geometry-evidence.json"):
        raise ValueError("Attempt06 output hash differs from source pins")
    if pins.get("criterion_disposition") != "pending":
        raise ValueError("Attempt06 cannot change the overlap_contact disposition")
    if pins.get("predecessor_packet") != _predecessor_packet_record():
        raise ValueError("Attempt06 predecessor packet binding is stale")
    if pins.get("predecessor_reviews") != _predecessor_review_records():
        raise ValueError("Attempt06 predecessor review bindings are stale")
    if (output_dir / "README.md").read_text(encoding="utf-8") != _render_readme(
        expected, pins
    ):
        raise ValueError("Attempt06 README does not reproduce")
    parsed: dict[str, str] = {}
    for line in (output_dir / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, separator, filename = line.partition("  ")
        if not separator or filename in parsed:
            raise ValueError("Malformed or duplicate attempt06 SHA256SUMS row")
        parsed[filename] = digest
    if set(parsed) != set(_packet_files()):
        raise ValueError("Attempt06 SHA256SUMS does not cover exactly the packet files")
    for filename, digest in parsed.items():
        if digest != sha256_file(output_dir / filename):
            raise ValueError(f"Attempt06 packet checksum mismatch: {filename}")
    return {
        "status": "PASS_GEOMETRY_ONLY_CRITERION_PENDING",
        "criterion_id": "overlap_contact",
        "criterion_disposition": "pending",
        "counts": expected["counts"],
        "classification_tolerances": expected["upstream_classification_tolerances"],
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
