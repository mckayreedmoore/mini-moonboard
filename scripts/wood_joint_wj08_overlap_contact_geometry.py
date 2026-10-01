"""Build a fail-closed geometry-only inventory for ``overlap_contact``.

This adapter preserves the distinctions in the reviewed T04 BRep map. It does
not identify face owners, activate contact, establish a load path, or dispose
the structural criterion.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ATTEMPT_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-overlap-contact-geometry-evidence-attempt01"
)
T04_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-geometric-interface-map-attempt02-2026-09-28"
)
T04_REVIEW_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-geometric-interface-map-attempt02-independent-review-2026-09-28"
)
GRAPH_REL = T04_REL / "complete-contact-graph.json"
T04_SOURCE_PINS_REL = T04_REL / "source-pins.json"
T04_README_REL = T04_REL / "README.md"
T04_REVIEW_RECORD_REL = T04_REVIEW_REL / "review-record.json"
CRITERIA_REL = Path("docs/wood-joints-mvp/criteria.json")
COVERAGE_REL = Path("docs/wood-joints-mvp/current-criteria-coverage.json")
METHOD_MAP_REL = Path("docs/wood-joints-mvp/criteria-method-map.md")
CANDIDATE_REL = Path("wood-joints-candidate.json")
PRODUCER_REL = Path("scripts/wood_joint_wj08_overlap_contact_geometry.py")
TEST_REL = Path("tests/test_wood_joint_wj08_overlap_contact_geometry.py")

EXPECTED_CANDIDATE = "compact-floor-flush-wood-joints-development"
EXPECTED_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_GRAPH_COUNTS = {
    "physical_member_nodes": 50,
    "unique_member_pairs": 1225,
    "exact_brep_pairs_evaluated": 147,
    "aabb_separated_pairs_not_exactly_evaluated": 1078,
    "candidate_bolt_axes": 92,
    "retained_frame_bolt_axes": 12,
    "current_panel_screw_axes": 66,
}
EXPECTED_CLASS_COUNTS = {
    "finite_opposed_planar_geometry": 115,
    "exact_brep_separated_geometry": 26,
    "aabb_separated_not_exactly_evaluated": 1078,
    "zero_area_or_unresolved_geometry": 6,
}

# These hashes freeze the reviewed input snapshot. A successor attempt must
# explicitly rebind them rather than silently consume changed geometry or
# criterion policy.
PINNED_INPUTS = {
    T04_REL
    / "README.md": "00ea09173fa3e15f3a90b5bdc7297de7bf7ac8ef358e7015508bed6c94bfa47e",
    GRAPH_REL: "7806242ac48b198becf5db97b16b6a5605021b8d86b964f0f02adb6806aeec26",
    T04_SOURCE_PINS_REL: "590112932d73dc57da015382a8ebf6e0fc85a8c5e8338549f381b8bd7732ba5c",
    T04_REVIEW_RECORD_REL: "2c0d3bc43ce3c48e923317fc426d93c2dae12e60abc211ef62d65582073254da",
    CRITERIA_REL: "fd1df5f106b944d21bc237d0ff789eb30437640ce81cb3e059c7e21f3a531784",
    COVERAGE_REL: "c07c786c37a745aec1c28f917ec6d326cef09b73fa9b14b0d76fb9d06c0d059c",
    METHOD_MAP_REL: "2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7",
    CANDIDATE_REL: "2d1c43eae6f1515ad9fbb052d208b14648f4bf4f9003f49a7268d2ecb8ec545d",
}

SCHEMA = "wood_joint_overlap_contact_geometry_evidence/v1"
SOURCE_PINS_SCHEMA = "wood_joint_overlap_contact_geometry_source_pins/v1"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _finite_nonnegative(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
    )


def _load_and_check_pinned_inputs(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for rel, expected in PINNED_INPUTS.items():
        path = root / rel
        if not path.is_file():
            raise ValueError(f"Pinned input is missing: {rel.as_posix()}")
        actual = sha256_file(path)
        if actual != expected:
            raise ValueError(f"Pinned input hash mismatch: {rel.as_posix()}")
        hashes[rel.as_posix()] = actual

    criteria = _load_json(root / CRITERIA_REL)
    coverage = _load_json(root / COVERAGE_REL)
    candidate = _load_json(root / CANDIDATE_REL)
    legacy_rows = criteria.get("legacy_criteria", [])
    criterion_rows = [
        row for row in legacy_rows if row.get("legacy_id") == "overlap_contact"
    ]
    coverage_rows = [
        row
        for row in coverage.get("criteria", [])
        if row.get("criterion_id") == "overlap_contact"
    ]
    if criteria.get("candidate") != EXPECTED_CANDIDATE:
        raise ValueError(
            "Criteria register candidate does not match this development lane"
        )
    if candidate.get("candidate") != EXPECTED_CANDIDATE:
        raise ValueError("Candidate authority does not match this development lane")
    if len(criterion_rows) != 1 or criterion_rows[0].get("status") != "pending":
        raise ValueError(
            "Exact overlap_contact source row is missing or no longer pending"
        )
    if len(coverage_rows) != 1 or coverage_rows[0].get("status") != "pending":
        raise ValueError(
            "Current overlap_contact coverage is missing or no longer pending"
        )
    if coverage.get("current_geometry_pin", {}).get("revision_id") != EXPECTED_REVISION:
        raise ValueError(
            "Coverage register is not bound to the reviewed geometry revision"
        )

    graph = _load_json(root / GRAPH_REL)
    if graph.get("schema") != "wood_joint_current_contact_graph/v1":
        raise ValueError("Unsupported upstream contact graph schema")
    if graph.get("revision_id") != EXPECTED_REVISION:
        raise ValueError("Upstream contact graph revision is stale")
    source_pins = _load_json(root / T04_SOURCE_PINS_REL)
    if (
        source_pins.get("attempt_id")
        != "current-geometric-interface-map-attempt02-2026-09-28"
    ):
        raise ValueError("Upstream T04 map attempt identity is unexpected")
    review = _load_json(root / T04_REVIEW_RECORD_REL)
    if (
        review.get("verdict") != "CONFIRMED_WITH_SCOPE_LIMITS"
        or review.get("findings") != []
    ):
        raise ValueError("Upstream independent review is not a bounded pass")

    hashes[PRODUCER_REL.as_posix()] = sha256_file(root / PRODUCER_REL)
    hashes[TEST_REL.as_posix()] = sha256_file(root / TEST_REL)
    return hashes


def _classify_edge(edge: dict[str, Any]) -> str:
    geometry_state = edge.get("geometry_state")
    interface_state = edge.get("interface_geometry_state")
    broadphase = edge.get("broadphase_candidate")
    if (
        geometry_state == "finite_opposed_planar_touch"
        and interface_state == "finite_planar_face_contact"
    ):
        if broadphase is not True:
            raise ValueError(
                "Finite contact is missing the exact-BRep broadphase marker"
            )
        area = edge.get("opposed_planar_face_contact_area_mm2")
        if not _finite_nonnegative(area) or area <= 0:
            raise ValueError(
                "Finite contact classification lacks a positive measured area"
            )
        return "finite_opposed_planar_geometry"
    if (
        geometry_state == "separated"
        and interface_state == "not_evaluated_aabb_separated"
    ):
        if broadphase is not False or edge.get("minimum_separation_mm") is not None:
            raise ValueError(
                "AABB-only pair is incorrectly represented as exact-BRep evaluated"
            )
        return "aabb_separated_not_exactly_evaluated"
    if geometry_state == "separated" and interface_state == "separated":
        if broadphase is not True or not _finite_nonnegative(
            edge.get("minimum_separation_mm")
        ):
            raise ValueError(
                "Exact-BRep separated pair lacks a finite measured separation"
            )
        return "exact_brep_separated_geometry"
    if (
        geometry_state == "zero_area_touch_or_unresolved"
        and interface_state == "zero_area_touch_or_unresolved_contact"
    ):
        if broadphase is not True or not _finite_nonnegative(
            edge.get("minimum_separation_mm")
        ):
            raise ValueError(
                "Unresolved pair lacks exact-BRep evaluation or a finite distance"
            )
        if edge.get("opposed_planar_face_contact_area_mm2") != 0:
            raise ValueError(
                "Zero-area/unresolved pair unexpectedly carries opposed contact area"
            )
        return "zero_area_or_unresolved_geometry"
    raise ValueError(
        f"Unrecognized or contradictory geometry classification: {geometry_state!r}/{interface_state!r}"
    )


def build_geometry_evidence(
    graph: dict[str, Any], source_hashes: dict[str, str]
) -> dict[str, Any]:
    """Translate the reviewed graph without upgrading it to mechanical evidence."""
    if graph.get("schema") != "wood_joint_current_contact_graph/v1":
        raise ValueError("Unsupported upstream contact graph schema")
    if graph.get("revision_id") != EXPECTED_REVISION:
        raise ValueError("Upstream contact graph revision is stale")
    inventories = graph.get("inventories")
    members = (
        inventories.get("physical_members") if isinstance(inventories, dict) else None
    )
    edges = graph.get("edges")
    if not isinstance(members, list) or not isinstance(edges, list):
        raise TypeError("Upstream graph lacks member or pair inventories")
    member_ids = [row.get("member_id") for row in members if isinstance(row, dict)]
    if len(member_ids) != EXPECTED_GRAPH_COUNTS["physical_member_nodes"] or any(
        not isinstance(member_id, str) or not member_id for member_id in member_ids
    ):
        raise ValueError("Upstream member inventory is incomplete or malformed")
    if len(set(member_ids)) != len(member_ids):
        raise ValueError("Upstream member inventory contains duplicate identities")

    expected_pairs = {
        tuple(sorted(pair)) for pair in itertools.combinations(member_ids, 2)
    }
    seen_pairs: set[tuple[str, str]] = set()
    classifications: dict[str, int] = {}
    output_pairs: list[dict[str, Any]] = []
    exact_brep_count = 0
    aabb_only_count = 0
    for edge in edges:
        if not isinstance(edge, dict):
            raise TypeError("Upstream graph contains a non-object pair")
        pair_members = edge.get("member_ids")
        if (
            not isinstance(pair_members, list)
            or len(pair_members) != 2
            or any(not isinstance(value, str) for value in pair_members)
        ):
            raise ValueError("Upstream pair must name exactly two member identities")
        pair = tuple(sorted(pair_members))
        if pair[0] == pair[1] or pair not in expected_pairs:
            raise ValueError("Upstream pair refers to an invalid member identity")
        if pair in seen_pairs:
            raise ValueError("Upstream graph contains a duplicate unordered pair")
        seen_pairs.add(pair)

        classification = _classify_edge(edge)
        classifications[classification] = classifications.get(classification, 0) + 1
        exact = edge.get("broadphase_candidate") is True
        exact_brep_count += int(exact)
        aabb_only_count += int(not exact)
        measurement_fields = (
            "aabb_separation_lower_bound_mm",
            "minimum_separation_mm",
            "finite_shared_planar_face_area_mm2",
            "opposed_planar_face_contact_area_mm2",
            "cooriented_planar_face_contact_area_mm2",
            "common_volume_mm3",
        )
        measurements = {key: edge.get(key) for key in measurement_fields}
        for key, value in measurements.items():
            if value is not None and not _finite_nonnegative(value):
                raise ValueError(
                    f"Pair measurement {key} is not finite and nonnegative"
                )
        output_pairs.append(
            {
                "pair_id": f"pair:{pair[0]}|{pair[1]}",
                "member_ids": list(pair),
                "geometry_classification": classification,
                "exact_brep_evaluated": exact,
                "measurement_basis": edge.get("contact_measurement_basis"),
                "measurements": measurements,
                "candidate_bolt_associations": edge.get(
                    "candidate_bolt_associations", []
                ),
                "retained_frame_bolt_source_membership": edge.get(
                    "retained_frame_bolt_source_membership", []
                ),
                "panel_screw_associations": edge.get(
                    "current_panel_screw_associations", []
                ),
                "face_owner_ids": None,
                "active_contact_state": "not_established_by_geometry_evidence",
                "contact_law": None,
                "load_path_owner_ids": None,
                "mechanical_disposition": "unresolved",
            }
        )

    if seen_pairs != expected_pairs:
        raise ValueError(
            "Upstream graph does not contain every unordered member pair exactly once"
        )
    if classifications != EXPECTED_CLASS_COUNTS:
        raise ValueError(
            f"Upstream geometry-class counts differ from the frozen attempt: {classifications}"
        )
    graph_counts = graph.get("counts", {})
    for key, expected in EXPECTED_GRAPH_COUNTS.items():
        if graph_counts.get(key) != expected:
            raise ValueError(
                f"Upstream graph count {key} differs from frozen value {expected}"
            )
    if exact_brep_count != EXPECTED_GRAPH_COUNTS["exact_brep_pairs_evaluated"]:
        raise ValueError("Exact-BRep pair count does not reconcile")
    if (
        aabb_only_count
        != EXPECTED_GRAPH_COUNTS["aabb_separated_pairs_not_exactly_evaluated"]
    ):
        raise ValueError("AABB-only pair count does not reconcile")
    if len(edges) != EXPECTED_GRAPH_COUNTS["unique_member_pairs"]:
        raise ValueError("Member-pair inventory count does not reconcile")

    pairs_by_id = {row["pair_id"]: row for row in output_pairs}
    if len(pairs_by_id) != len(output_pairs):
        raise ValueError("Canonical output pair IDs are not unique")
    output_pairs = [pairs_by_id[key] for key in sorted(pairs_by_id)]
    return {
        "schema": SCHEMA,
        "candidate": EXPECTED_CANDIDATE,
        "revision_id": EXPECTED_REVISION,
        "criterion_id": "overlap_contact",
        "criterion_disposition": "pending",
        "evidence_status": "partial_geometry_inventory_only",
        "source_hashes": dict(sorted(source_hashes.items())),
        "inventory_scope": {
            "included": "All unordered pairs among the 50 current member/panel solids in the reviewed T04 graph.",
            "excluded_or_unbound": [
                "Connector and fastener solids are not nodes in this member/panel graph.",
                "Exact face identities and face ownership are not emitted by the source graph.",
                "The 1,078 AABB-separated pairs were not exact-BRep evaluated.",
                "Six exact-BRep pairs remain zero-area or unresolved.",
                "No active unilateral contact set, gap/opening law, load-path owner, or six-case reaction is bound.",
            ],
        },
        "counts": {
            "physical_member_nodes": len(member_ids),
            "unordered_member_pairs": len(output_pairs),
            "exact_brep_evaluated_pairs": exact_brep_count,
            "aabb_separated_not_exactly_evaluated_pairs": aabb_only_count,
            "geometry_classifications": dict(sorted(classifications.items())),
        },
        "mechanics": {
            "active_contact_established": False,
            "bearing_or_pressure_established": False,
            "load_path_ownership_established": False,
            "contact_law_established": False,
            "force_transfer_established": False,
            "criterion_acceptance": False,
        },
        "pairs": output_pairs,
        "required_followup": [
            "Bind finite physical face IDs and owning bodies for each applicable interface.",
            "Add connector/fastener and internal connector interfaces to the physical interface inventory.",
            "Resolve the six zero-area/unresolved pairs and obtain exact BRep checks for any pair needed by a load path.",
            "Assign supported finite unilateral contact/gap laws and joint-level load-path owners.",
            "Audit active contact, pressure, action/reaction, and equilibrium in accepted fresh frame cases.",
        ],
        "limits": [
            "A finite geometric touch is not active bearing or a strength result.",
            "AABB separation is only a broadphase geometry observation; exact BRep distance is not reported for those pairs.",
            "This packet does not close overlap_contact and does not change any criterion status.",
        ],
    }


def _current_source_hashes(root: Path) -> dict[str, str]:
    hashes = _load_and_check_pinned_inputs(root)
    return dict(sorted(hashes.items()))


def _build_current(root: Path) -> dict[str, Any]:
    source_hashes = _current_source_hashes(root)
    graph = _load_json(root / GRAPH_REL)
    return build_geometry_evidence(graph, source_hashes)


def _run_upstream_verifier(root: Path) -> None:
    verifier = root / T04_REL / "verify_packet.py"
    completed = subprocess.run(
        [sys.executable, str(verifier), "--verify"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        raise ValueError(
            "Upstream T04 verifier failed: "
            + (completed.stdout + completed.stderr).strip()
        )


def _packet_files(packet_dir: Path) -> list[str]:
    return ["README.md", "geometry-evidence.json", "source-pins.json"]


def _render_readme(evidence: dict[str, Any], pins: dict[str, Any]) -> str:
    counts = evidence["counts"]
    classes = counts["geometry_classifications"]
    return f"""# `overlap_contact` geometry inventory — attempt 01

Status: **partial geometry evidence only; criterion remains pending** for
`{evidence["revision_id"]}`.

This packet adapts the independently reviewed T04 attempt02 member/panel pair
map into one record per unordered pair. It contains {counts["physical_member_nodes"]}
nodes and {counts["unordered_member_pairs"]} pairs: {counts["exact_brep_evaluated_pairs"]}
were evaluated by exact BRep, while {counts["aabb_separated_not_exactly_evaluated_pairs"]}
were rejected by disjoint AABBs and were not exact-BRep evaluated. Geometry
classifications are {classes["finite_opposed_planar_geometry"]} finite opposed
planar touches, {classes["exact_brep_separated_geometry"]} exact-BRep separated
pairs, {classes["aabb_separated_not_exactly_evaluated"]} AABB-only separated
pairs, and {classes["zero_area_or_unresolved_geometry"]} zero-area/unresolved
pairs.

The adapter preserves measured areas and distances but emits no face-owner
IDs, contact law, active-contact state, or load-path owner. A finite face touch
remains geometry only. Connector and fastener solids are outside the 50-node
member/panel graph, and the six unresolved pairs remain unresolved. No bearing,
pressure, force transfer, capacity, case response, or acceptance is inferred.

The current criterion record remains `pending`. Completion requires an
integrated physical-interface inventory, finite unilateral contact behavior,
mechanical ownership, and accepted response evidence. This packet advances
inventory traceability only; it does not replace those gates.

## Reproduction

From the repository root, verify the input and output bindings with:

```sh
.venv/bin/python scripts/wood_joint_wj08_overlap_contact_geometry.py --verify
sha256sum -c docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-overlap-contact-geometry-evidence-attempt01/SHA256SUMS
```

The producer also reruns the upstream T04 verifier before freezing. The output
pins {len(pins["source_hashes"])} repository inputs, including the producer and
focused tests. The graph source and exact geometry map are not modified.
"""


def freeze_packet(root: Path = ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    root = Path(root)
    output_dir = Path(output_dir) if output_dir else root / ATTEMPT_REL
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(
            f"Refusing to replace nonempty packet directory: {output_dir}"
        )
    _run_upstream_verifier(root)
    evidence = _build_current(root)
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = output_dir / "geometry-evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    pins = {
        "schema": SOURCE_PINS_SCHEMA,
        "attempt_id": "current-overlap-contact-geometry-evidence-attempt01",
        "candidate": EXPECTED_CANDIDATE,
        "revision_id": EXPECTED_REVISION,
        "source_hashes": evidence["source_hashes"],
        "output_sha256": sha256_file(evidence_path),
        "criterion_disposition": "pending",
        "scope": "partial member/panel geometric pair inventory; no mechanics or acceptance",
    }
    pins_path = output_dir / "source-pins.json"
    pins_path.write_text(json.dumps(pins, indent=2) + "\n", encoding="utf-8")
    readme_path = output_dir / "README.md"
    readme_path.write_text(_render_readme(evidence, pins), encoding="utf-8")
    sums_path = output_dir / "SHA256SUMS"
    sums = [
        f"{sha256_file(output_dir / relative)}  {relative}"
        for relative in _packet_files(output_dir)
    ]
    sums_path.write_text("\n".join(sums) + "\n", encoding="utf-8")
    return pins


def verify_packet(root: Path = ROOT, output_dir: Path | None = None) -> dict[str, Any]:
    root = Path(root)
    output_dir = Path(output_dir) if output_dir else root / ATTEMPT_REL
    _run_upstream_verifier(root)
    pins = _load_json(output_dir / "source-pins.json")
    if pins.get("schema") != SOURCE_PINS_SCHEMA:
        raise ValueError("Unsupported geometry evidence source-pins schema")
    if (
        pins.get("candidate") != EXPECTED_CANDIDATE
        or pins.get("revision_id") != EXPECTED_REVISION
    ):
        raise ValueError("Geometry evidence packet candidate/revision is stale")
    expected = _build_current(root)
    evidence_path = output_dir / "geometry-evidence.json"
    evidence = _load_json(evidence_path)
    if evidence != expected:
        raise ValueError(
            "Geometry evidence does not reproduce from pinned current inputs"
        )
    if pins.get("source_hashes") != expected["source_hashes"]:
        raise ValueError("Source pin record does not match current repository inputs")
    if pins.get("output_sha256") != sha256_file(evidence_path):
        raise ValueError("Geometry evidence output hash differs from source pins")
    if pins.get("criterion_disposition") != "pending":
        raise ValueError(
            "Geometry evidence packet cannot change the criterion disposition"
        )
    if (output_dir / "README.md").read_text(encoding="utf-8") != _render_readme(
        expected, pins
    ):
        raise ValueError("Geometry evidence README does not reproduce")
    sums = (output_dir / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    expected_files = _packet_files(output_dir)
    parsed = {}
    for line in sums:
        digest, separator, filename = line.partition("  ")
        if not separator or filename in parsed:
            raise ValueError("Malformed or duplicate SHA256SUMS row")
        parsed[filename] = digest
    if set(parsed) != set(expected_files):
        raise ValueError("SHA256SUMS does not cover exactly the expected packet files")
    for filename in expected_files:
        if parsed[filename] != sha256_file(output_dir / filename):
            raise ValueError(f"Packet checksum mismatch: {filename}")
    return {
        "status": "PASS_GEOMETRY_ONLY_CRITERION_PENDING",
        "criterion_id": "overlap_contact",
        "criterion_disposition": "pending",
        "counts": expected["counts"],
    }


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--freeze", action="store_true", help="write the append-only attempt01 packet"
    )
    mode.add_argument(
        "--verify", action="store_true", help="rebuild and validate attempt01"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="packet directory; defaults to the attempt01 path",
    )
    args = parser.parse_args()
    if args.freeze:
        result = freeze_packet(output_dir=args.output_dir)
        print(
            json.dumps(
                {"status": "FROZEN_GEOMETRY_ONLY_PENDING", "pins": result}, indent=2
            )
        )
        return 0
    result = verify_packet(output_dir=args.output_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
