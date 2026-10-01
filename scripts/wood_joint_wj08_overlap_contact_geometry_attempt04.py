"""Harden overlap geometry packet identity checks and failure-path coverage.

Attempt04 remains geometry-only. It does not establish active contact, load
transfer, mechanical response, or criterion acceptance.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts import wood_joint_wj08_overlap_contact_geometry_attempt03 as attempt03

ROOT = attempt03.ROOT
ATTEMPT_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-overlap-contact-geometry-evidence-attempt04"
)
PRODUCER_REL = Path("scripts/wood_joint_wj08_overlap_contact_geometry_attempt04.py")
TEST_REL = Path("tests/test_wood_joint_wj08_overlap_contact_geometry_attempt04.py")
SCOPE = "partial member/panel geometric pair inventory; no mechanics or acceptance"

PREDECESSOR_PACKET_HASHES = {
    attempt03.ATTEMPT_REL
    / "README.md": "52528d7b1655fc44b5ddcbc05202babbc6c0378a77cf0bc7a6fc264e60d90e69",
    attempt03.ATTEMPT_REL
    / "geometry-evidence.json": "33d7a6032f720b4bf18bf17ccd55d73b3c751067803b43296d461f7610708155",
    attempt03.ATTEMPT_REL
    / "source-pins.json": "7e25f09e7653b7b97e833b81905edbbd3caa9bece9962a7c9db9d814653cbed1",
    attempt03.ATTEMPT_REL
    / "SHA256SUMS": "5f8b05653b21c34c0dc0e77a83757213099368f78f7b6b0dd9fea3fdb3f14195",
}
PREDECESSOR_REVIEWS = {
    Path(
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-overlap-contact-geometry-attempt03-correctness-review-2026-09-28/"
        "review-record.md"
    ): "0419f5d5848d2078217eb21b7d2d471e51c9dcb214c9e6f02b75b89fd90d77c9",
    Path(
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-overlap-contact-geometry-evidence-attempt03-testing-review-2026-09-28/"
        "review-record.md"
    ): "793fad6e50ed15df9b9efb7f949851780a8dea6cb36eb40609c761c033e9fd3f",
    Path(
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
        "current-overlap-contact-geometry-attempt03-architecture-review-2026-09-28/"
        "architecture-review.md"
    ): "92fdb04db5bb372f99bda32e01787392c706cedc5f7e9a7b07767ca5c3c054c3",
}

SCHEMA = "wood_joint_overlap_contact_geometry_evidence/v4"
SOURCE_PINS_SCHEMA = "wood_joint_overlap_contact_geometry_source_pins/v4"
ATTEMPT_ID = "current-overlap-contact-geometry-evidence-attempt04"


def _load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _verify_fixed_hashes(
    root: Path, expected_hashes: dict[Path, str], label: str
) -> dict[str, str]:
    root = Path(root)
    verified: dict[str, str] = {}
    for rel, expected in expected_hashes.items():
        path = root / rel
        if not path.is_file():
            raise ValueError(f"Pinned {label} input is missing: {rel.as_posix()}")
        actual = attempt03.attempt02.attempt01.sha256_file(path)
        if actual != expected:
            raise ValueError(f"Pinned {label} input hash mismatch: {rel.as_posix()}")
        verified[rel.as_posix()] = actual
    return verified


def _current_source_hashes(root: Path = ROOT) -> dict[str, str]:
    root = Path(root)
    hashes = attempt03._current_source_hashes(root)
    hashes.update(_verify_fixed_hashes(root, PREDECESSOR_PACKET_HASHES, "attempt04"))
    hashes.update(_verify_fixed_hashes(root, PREDECESSOR_REVIEWS, "attempt04"))
    attempt03.verify_packet(root=root)
    hashes[PRODUCER_REL.as_posix()] = attempt03.attempt02.attempt01.sha256_file(
        root / PRODUCER_REL
    )
    hashes[TEST_REL.as_posix()] = attempt03.attempt02.attempt01.sha256_file(
        root / TEST_REL
    )
    return dict(sorted(hashes.items()))


def validate_geometry_consistency(graph: dict[str, Any]) -> dict[str, int]:
    """Use the independently frozen attempt03 geometry tolerance checks."""
    return attempt03.validate_geometry_consistency(graph)


def build_geometry_evidence(
    graph: dict[str, Any], source_hashes: dict[str, str]
) -> dict[str, Any]:
    evidence = attempt03.build_geometry_evidence(graph, source_hashes)
    evidence["schema"] = SCHEMA
    return evidence


def _build_current(root: Path = ROOT) -> dict[str, Any]:
    root = Path(root)
    source_hashes = _current_source_hashes(root)
    graph_rel = attempt03.attempt02.attempt01.GRAPH_REL
    graph = _load_json(root / graph_rel)
    return build_geometry_evidence(graph, source_hashes)


def _predecessor_review_records() -> list[dict[str, str]]:
    return [
        {"path": rel.as_posix(), "sha256": digest}
        for rel, digest in PREDECESSOR_REVIEWS.items()
    ]


def _predecessor_packet_record() -> dict[str, Any]:
    return {
        "path": attempt03.ATTEMPT_REL.as_posix(),
        "files": {
            rel.name: digest for rel, digest in PREDECESSOR_PACKET_HASHES.items()
        },
    }


def _render_readme(evidence: dict[str, Any], pins: dict[str, Any]) -> str:
    counts = evidence["counts"]
    classes = counts["geometry_classifications"]
    return f"""# `overlap_contact` geometry inventory — attempt 04

Status: **partial geometry evidence only; criterion remains pending** for
`{evidence["revision_id"]}`.

Attempt04 retains the attempt03 inventory and tolerance checks. It also
validates candidate, revision, and scope metadata in its source-pins record.
The verifier compares parsed evidence values with regenerated values and
checks the packet hashes. Its tests exercise successful and tampered packet
verification using temporary directories.

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
.venv/bin/python -m scripts.wood_joint_wj08_overlap_contact_geometry_attempt04 --verify
(cd docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-overlap-contact-geometry-evidence-attempt04 && sha256sum -c SHA256SUMS)
```

The verifier validates the frozen attempt03 packet and its independent reviews,
revalidates the pinned upstream T04 verifier chain, checks all bound source
hashes, applies the upstream-consistent measurement thresholds, and compares
the parsed frozen evidence values with freshly generated values. The packet
pins {len(pins["source_hashes"])} repository inputs. The criterion status stays
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
        "candidate": attempt03.attempt02.attempt01.EXPECTED_CANDIDATE,
        "revision_id": attempt03.attempt02.attempt01.EXPECTED_REVISION,
        "source_hashes": evidence["source_hashes"],
        "output_sha256": attempt03.attempt02.attempt01.sha256_file(evidence_path),
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
    sums = [
        f"{attempt03.attempt02.attempt01.sha256_file(output_dir / relative)}  {relative}"
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
        raise ValueError("Unsupported or stale attempt04 source-pins record")
    if pins.get("candidate") != attempt03.attempt02.attempt01.EXPECTED_CANDIDATE:
        raise ValueError("Attempt04 source-pins candidate is stale or contradictory")
    if pins.get("revision_id") != attempt03.attempt02.attempt01.EXPECTED_REVISION:
        raise ValueError("Attempt04 source-pins revision is stale or contradictory")
    if pins.get("scope") != SCOPE:
        raise ValueError("Attempt04 source-pins scope is stale or contradictory")
    evidence_path = output_dir / "geometry-evidence.json"
    evidence = _load_json(evidence_path)
    if evidence != expected:
        raise ValueError("Attempt04 evidence does not reproduce from pinned inputs")
    if pins.get("source_hashes") != expected["source_hashes"]:
        raise ValueError("Attempt04 source pins do not match current repository inputs")
    if pins.get("output_sha256") != attempt03.attempt02.attempt01.sha256_file(
        evidence_path
    ):
        raise ValueError("Attempt04 output hash differs from source pins")
    if pins.get("criterion_disposition") != "pending":
        raise ValueError("Attempt04 cannot change the overlap_contact disposition")
    if pins.get("predecessor_packet") != _predecessor_packet_record():
        raise ValueError("Attempt04 predecessor packet binding is stale")
    if pins.get("predecessor_reviews") != _predecessor_review_records():
        raise ValueError("Attempt04 predecessor review bindings are stale")
    if (output_dir / "README.md").read_text(encoding="utf-8") != _render_readme(
        expected, pins
    ):
        raise ValueError("Attempt04 README does not reproduce")
    parsed: dict[str, str] = {}
    for line in (output_dir / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, separator, filename = line.partition("  ")
        if not separator or filename in parsed:
            raise ValueError("Malformed or duplicate attempt04 SHA256SUMS row")
        parsed[filename] = digest
    if set(parsed) != set(_packet_files()):
        raise ValueError("Attempt04 SHA256SUMS does not cover exactly the packet files")
    for filename, digest in parsed.items():
        if digest != attempt03.attempt02.attempt01.sha256_file(output_dir / filename):
            raise ValueError(f"Attempt04 packet checksum mismatch: {filename}")
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
