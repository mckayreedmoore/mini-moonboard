"""Audit CalculiX ``pilot.cel`` contact elements by iteration and owner pair.

This is a post-run diagnostic. It refuses to read a live checkpoint, verifies
the completed launcher output hash and frozen mesh/contact inputs, then maps
each CEL element's master/slave connectivity owners to the original contact
manifest. It reports generated contact-element topology/count changes only;
it does not infer contact force, residual convergence, or joint capacity.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[5]
DEFAULT_CHECKPOINT = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-transient-checkpoint-attempt01"
)
OUTPUT_DIR = Path(__file__).resolve().parent
WRITER_SOURCE = Path("/tmp/ccx221-source/CalculiX/ccx_2.21/src/gencontelem_f2f.f")
EXPECTED_PAIR_COUNT = 35
HEADER_RE = re.compile(
    r"^\s*\*ELEMENT\s*,\s*TYPE\s*=\s*(C3D8|C3D6)\s*,\s*ELSET\s*=\s*([^,\s]+)\s*$",
    re.IGNORECASE,
)
SETNAME_RE = re.compile(
    r"^contactelements_st(?P<step>\d+)_in(?P<increment>\d+)_at(?P<attempt>\d+)_it(?P<iteration>\d+)$",
    re.IGNORECASE,
)
INTEGER_RE = re.compile(r"[-+]?\d+")


@dataclass(frozen=True, order=True)
class IterationKey:
    step: int
    increment: int
    attempt: int
    iteration: int


@dataclass(frozen=True)
class CelElement:
    key: IterationKey
    set_name: str
    element_type: str
    element_id: int
    connectivity: tuple[int, ...]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _key_from_setname(set_name: str) -> IterationKey:
    match = SETNAME_RE.fullmatch(set_name)
    if match is None:
        raise ValueError(f"unexpected CEL element set name: {set_name!r}")
    return IterationKey(**{name: int(value) for name, value in match.groupdict().items()})


def parse_cel(text: str) -> list[CelElement]:
    """Read element cards emitted by gencontelem_f2f and keep iteration keys."""
    elements: list[CelElement] = []
    current: tuple[IterationKey, str, str] | None = None
    expected_counts = {"C3D8": 9, "C3D6": 7}  # element label plus connectivity

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            match = HEADER_RE.fullmatch(line)
            if match is None:
                current = None
                if line.upper().startswith("*ELEMENT"):
                    raise ValueError(f"line {line_number}: unsupported CEL element header: {line}")
                continue
            element_type = match.group(1).upper()
            set_name = match.group(2)
            current = (_key_from_setname(set_name), set_name, element_type)
            continue
        if current is None:
            raise ValueError(f"line {line_number}: numeric CEL record outside an element card")
        values = [int(token) for token in INTEGER_RE.findall(line)]
        expected = expected_counts[current[2]]
        if len(values) != expected:
            raise ValueError(
                f"line {line_number}: {current[2]} requires {expected} integer fields, got {len(values)}"
            )
        label, *connectivity = values
        if label <= 0 or any(node <= 0 for node in connectivity):
            raise ValueError(f"line {line_number}: CEL labels and node IDs must be positive")
        elements.append(CelElement(current[0], current[1], current[2], label, tuple(connectivity)))
    if not elements:
        raise ValueError("CEL contains no contact elements")
    return elements


def parse_cvg(text: str) -> dict[IterationKey, int]:
    """Read contact-element totals from numeric CalculiX convergence rows."""
    rows: dict[IterationKey, int] = {}
    for line_number, line in enumerate(text.splitlines(), start=1):
        fields = line.split()
        if len(fields) < 5:
            continue
        try:
            step, increment, attempt, iteration, contact_count = map(int, fields[:5])
        except ValueError:
            continue
        key = IterationKey(step, increment, attempt, iteration)
        if key in rows:
            raise ValueError(f"pilot.cvg line {line_number}: duplicate iteration row {key}")
        rows[key] = contact_count
    return rows


def build_owner_index(
    mesh: Mapping[str, Any], manifest: Mapping[str, Any]
) -> tuple[dict[int, str | None], dict[tuple[str, str], list[Mapping[str, Any]]], dict[str, Mapping[str, Any]]]:
    """Build node ownership and oriented pair lookup from frozen inputs."""
    bodies = mesh.get("bodies")
    if not isinstance(bodies, Mapping):
        raise ValueError("mesh.json does not contain body ownership")
    node_owners: dict[int, str | None] = {}
    duplicate_nodes: set[int] = set()
    for owner, body in bodies.items():
        for raw_node in body.get("nodes", ()):
            node = int(raw_node)
            if node in node_owners and node_owners[node] != owner:
                duplicate_nodes.add(node)
                node_owners[node] = None
            else:
                node_owners[node] = str(owner)

    pairs = manifest.get("pairs")
    if not isinstance(pairs, list) or len(pairs) != EXPECTED_PAIR_COUNT:
        raise ValueError(f"contact manifest must contain exactly {EXPECTED_PAIR_COUNT} original pairs")
    pair_lookup: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    pair_by_id: dict[str, Mapping[str, Any]] = {}
    for pair in pairs:
        pair_id = str(pair["pair_id"])
        owners = (str(pair["master_owner"]), str(pair["slave_owner"]))
        if pair_id in pair_by_id:
            raise ValueError(f"duplicate pair ID in contact manifest: {pair_id}")
        if any(owner not in bodies for owner in owners):
            raise ValueError(f"{pair_id}: pair owner is absent from mesh body ownership")
        pair_by_id[pair_id] = pair
        pair_lookup[owners].append(pair)
    if len(pair_by_id) != EXPECTED_PAIR_COUNT:
        raise ValueError("contact manifest pair IDs are not unique")
    return node_owners, dict(pair_lookup), pair_by_id


def classify_element(
    element: CelElement,
    node_owners: Mapping[int, str | None],
    pair_lookup: Mapping[tuple[str, str], Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    """Infer an exact pair from ordered master/slave connectivity ownership."""
    face_width = 4 if element.element_type == "C3D8" else 3
    if len(element.connectivity) != face_width * 2:
        return {"status": "unmapped", "reason": "unexpected_contact_connectivity_width"}
    master_nodes = element.connectivity[:face_width]
    slave_nodes = element.connectivity[face_width:]

    def face_owner(nodes: Sequence[int]) -> tuple[str | None, str | None]:
        found = {node_owners.get(node) for node in nodes}
        if None in found:
            return None, "node_missing_or_has_ambiguous_mesh_owner"
        if len(found) != 1:
            return None, "one_contact_face_spans_multiple_mesh_owners"
        return next(iter(found)), None  # type: ignore[return-value]

    master_owner, master_issue = face_owner(master_nodes)
    slave_owner, slave_issue = face_owner(slave_nodes)
    if master_issue or slave_issue:
        return {
            "status": "ambiguous",
            "reason": master_issue or slave_issue,
            "master_owner": master_owner,
            "slave_owner": slave_owner,
        }
    if master_owner == slave_owner:
        return {
            "status": "unmapped",
            "reason": "both_contact_faces_map_to_same_mesh_owner",
            "master_owner": master_owner,
            "slave_owner": slave_owner,
        }
    matches = pair_lookup.get((str(master_owner), str(slave_owner)), ())
    if len(matches) != 1:
        return {
            "status": "ambiguous" if matches else "unmapped",
            "reason": "ordered_owner_tuple_not_unique_in_manifest" if matches else "ordered_owner_tuple_absent_from_manifest",
            "master_owner": master_owner,
            "slave_owner": slave_owner,
        }
    pair = matches[0]
    return {
        "status": "exact",
        "pair_id": str(pair["pair_id"]),
        "category": str(pair["category"]),
        "master_owner": str(master_owner),
        "slave_owner": str(slave_owner),
        "signature": [
            sorted(set(master_nodes)),
            sorted(set(slave_nodes)),
        ],
    }


def _category_bucket(category: str) -> str:
    if category == "wood_wood_finite_interface":
        return "wood_wood_finite_interface"
    if category.startswith("open_bolt_shank_to_wood_bore"):
        return "open_bolt_shank_to_wood_bore"
    if category.startswith("open_bolt_shank_to_washer_bore"):
        return "open_bolt_shank_to_washer_bore"
    return "bolt_seat"


def _signature_counter(
    records: Iterable[tuple[CelElement, Mapping[str, Any]]],
) -> dict[IterationKey, dict[str, Counter[tuple[tuple[int, ...], tuple[int, ...]]]]]:
    result: dict[IterationKey, dict[str, Counter[tuple[tuple[int, ...], tuple[int, ...]]]]] = defaultdict(
        lambda: defaultdict(Counter)
    )
    for element, classification in records:
        if classification.get("status") != "exact":
            continue
        signature_raw = classification["signature"]
        signature = (tuple(signature_raw[0]), tuple(signature_raw[1]))
        result[element.key][str(classification["pair_id"])][signature] += 1
    return result


def build_audit(
    elements: Sequence[CelElement],
    mesh: Mapping[str, Any],
    manifest: Mapping[str, Any],
    *,
    convergence_counts: Mapping[IterationKey, int] | None = None,
    provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    node_owners, pair_lookup, pair_by_id = build_owner_index(mesh, manifest)
    duplicates = [node for node, owner in node_owners.items() if owner is None]
    owned_records = [
        (element, classify_element(element, node_owners, pair_lookup))
        for element in elements
    ]
    signatures = _signature_counter(owned_records)
    groups = sorted({element.key for element in elements})
    pairs = [pair_by_id[pair_id] for pair_id in sorted(pair_by_id)]
    pair_counts_by_key: dict[IterationKey, Counter[str]] = defaultdict(Counter)
    unknown_by_key: Counter[IterationKey] = Counter()
    unknown_reasons: Counter[str] = Counter()
    unknown_examples: list[dict[str, Any]] = []
    for element, classification in owned_records:
        if classification.get("status") == "exact":
            pair_counts_by_key[element.key][str(classification["pair_id"])] += 1
        else:
            unknown_by_key[element.key] += 1
            reason = str(classification.get("reason", "unknown"))
            unknown_reasons[reason] += 1
            if len(unknown_examples) < 20:
                unknown_examples.append(
                    {
                        "set_name": element.set_name,
                        "element_type": element.element_type,
                        "element_id": element.element_id,
                        "connectivity": list(element.connectivity),
                        **classification,
                    }
                )

    cel_total_by_key = {
        key: sum(pair_counts_by_key[key].values()) + unknown_by_key[key]
        for key in groups
    }
    cvg_counts = dict(convergence_counts or {})
    cvg_mismatches = [
        {
            "step": key.step,
            "increment": key.increment,
            "attempt": key.attempt,
            "iteration": key.iteration,
            "cvg_contact_element_count": int(cvg_count),
            "cel_contact_element_count": cel_total_by_key.get(key),
        }
        for key, cvg_count in sorted(cvg_counts.items())
        if cel_total_by_key.get(key) != int(cvg_count)
    ]
    cvg_rows_without_cel = [key for key in sorted(cvg_counts) if key not in cel_total_by_key]
    cel_groups_without_cvg = [key for key in groups if key not in cvg_counts]
    aligned_keys = {
        key for key, cvg_count in cvg_counts.items()
        if cel_total_by_key.get(key) == int(cvg_count)
    }
    pair_index = {str(pair["pair_id"]): pair for pair in pairs}
    groups_out: list[dict[str, Any]] = []
    for key in groups:
        counter = pair_counts_by_key[key]
        category_counts: Counter[str] = Counter()
        pair_rows = []
        for pair in pairs:
            pair_id = str(pair["pair_id"])
            count = counter[pair_id]
            category_counts[_category_bucket(str(pair["category"]))] += count
            pair_rows.append(
                {
                    "pair_id": pair_id,
                    "category": str(pair["category"]),
                    "master_owner": str(pair["master_owner"]),
                    "slave_owner": str(pair["slave_owner"]),
                    "contact_element_count": count,
                    "active_face_pair_signature_count": len(signatures.get(key, {}).get(pair_id, {})),
                }
            )
        groups_out.append(
            {
                "step": key.step,
                "increment": key.increment,
                "attempt": key.attempt,
                "iteration": key.iteration,
                "contact_element_count": sum(counter.values()) + unknown_by_key[key],
                "exactly_mapped_contact_element_count": sum(counter.values()),
                "ambiguous_or_unmapped_contact_element_count": unknown_by_key[key],
                "cvg_contact_element_count": cvg_counts.get(key),
                "cel_count_matches_cvg": (
                    cel_total_by_key[key] == cvg_counts[key] if key in cvg_counts else None
                ),
                "category_counts": dict(sorted(category_counts.items())),
                "pair_counts": pair_rows,
            }
        )

    group_by_key = {key: group for key, group in zip(groups, groups_out)}
    blocks_by_run: dict[tuple[int, int, int], list[IterationKey]] = defaultdict(list)
    for key in groups:
        blocks_by_run[(key.step, key.increment, key.attempt)].append(key)
    transitions: list[dict[str, Any]] = []
    churn_by_pair: dict[str, dict[str, int]] = {
        pair_id: {"changed_iteration_transitions": 0, "count_changed_transitions": 0, "signature_turnover": 0, "max_abs_count_delta": 0}
        for pair_id in pair_index
    }
    for run_key, run_groups in sorted(blocks_by_run.items()):
        run_groups.sort(key=lambda key: key.iteration)
        for before, after in zip(run_groups, run_groups[1:]):
            transition_verified = before in aligned_keys and after in aligned_keys
            pair_transition_rows = []
            for pair in pairs:
                pair_id = str(pair["pair_id"])
                before_count = pair_counts_by_key[before][pair_id]
                after_count = pair_counts_by_key[after][pair_id]
                before_sig = signatures.get(before, {}).get(pair_id, Counter())
                after_sig = signatures.get(after, {}).get(pair_id, Counter())
                retained = sum((before_sig & after_sig).values())
                appeared = sum((after_sig - before_sig).values())
                disappeared = sum((before_sig - after_sig).values())
                delta = after_count - before_count
                stats = churn_by_pair[pair_id]
                if transition_verified and (appeared or disappeared):
                    stats["changed_iteration_transitions"] += 1
                    stats["signature_turnover"] += appeared + disappeared
                if transition_verified and delta:
                    stats["count_changed_transitions"] += 1
                if transition_verified:
                    stats["max_abs_count_delta"] = max(stats["max_abs_count_delta"], abs(delta))
                pair_transition_rows.append(
                    {
                        "comparison_status": "cvg_aligned" if transition_verified else "unverified_cel_only_or_mismatched_endpoint",
                        "pair_id": pair_id,
                        "category": str(pair["category"]),
                        "master_owner": str(pair["master_owner"]),
                        "slave_owner": str(pair["slave_owner"]),
                        "contact_element_count_before": before_count,
                        "contact_element_count_after": after_count,
                        "contact_element_count_delta": delta,
                        "retained_face_pair_signature_multiplicity": retained,
                        "appeared_face_pair_signature_multiplicity": appeared,
                        "disappeared_face_pair_signature_multiplicity": disappeared,
                    }
                )
            transitions.append(
                {
                    "step": run_key[0],
                    "increment": run_key[1],
                    "attempt": run_key[2],
                    "iteration_before": before.iteration,
                    "iteration_after": after.iteration,
                    "iteration_gap": after.iteration - before.iteration,
                    "comparison_status": "cvg_aligned" if transition_verified else "unverified_cel_only_or_mismatched_endpoint",
                    "contact_element_count_before_cvg_aligned": before in aligned_keys,
                    "contact_element_count_after_cvg_aligned": after in aligned_keys,
                    "pair_transitions": pair_transition_rows,
                }
            )

    aligned_group_rows = [group for group in groups_out if group["cel_count_matches_cvg"] is True]
    endpoint_comparison: dict[str, Any] | None = None
    if len(aligned_group_rows) >= 2:
        first_group, last_group = aligned_group_rows[0], aligned_group_rows[-1]
        first_pairs = {row["pair_id"]: row for row in first_group["pair_counts"]}
        last_pairs = {row["pair_id"]: row for row in last_group["pair_counts"]}
        endpoint_pairs = []
        for pair in pairs:
            pair_id = str(pair["pair_id"])
            first_count = first_pairs[pair_id]["contact_element_count"]
            last_count = last_pairs[pair_id]["contact_element_count"]
            endpoint_pairs.append(
                {
                    "pair_id": pair_id,
                    "category": str(pair["category"]),
                    "master_owner": str(pair["master_owner"]),
                    "slave_owner": str(pair["slave_owner"]),
                    "first_aligned_contact_element_count": first_count,
                    "last_aligned_contact_element_count": last_count,
                    "count_delta": last_count - first_count,
                }
            )
        endpoint_comparison = {
            "meaning": "first and last CVG-aligned solver-iteration diagnostics, not accepted time-step endpoints",
            "first_group": {key: first_group[key] for key in ("step", "increment", "attempt", "iteration")},
            "last_group": {key: last_group[key] for key in ("step", "increment", "attempt", "iteration")},
            "first_contact_element_count": first_group["contact_element_count"],
            "last_contact_element_count": last_group["contact_element_count"],
            "contact_element_count_delta": last_group["contact_element_count"] - first_group["contact_element_count"],
            "first_category_counts": first_group["category_counts"],
            "last_category_counts": last_group["category_counts"],
            "pair_counts": endpoint_pairs,
        }

    category_churn: Counter[str] = Counter()
    for pair in pairs:
        category_churn[_category_bucket(str(pair["category"]))] += churn_by_pair[str(pair["pair_id"])]["signature_turnover"]
    ranked_pairs = []
    for pair_id, stats in churn_by_pair.items():
        pair = pair_index[pair_id]
        ranked_pairs.append(
            {
                "pair_id": pair_id,
                "category": str(pair["category"]),
                "switching_bucket": _category_bucket(str(pair["category"])),
                "master_owner": str(pair["master_owner"]),
                "slave_owner": str(pair["slave_owner"]),
                **stats,
            }
        )
    ranked_pairs.sort(
        key=lambda row: (
            -int(row["signature_turnover"]),
            -int(row["changed_iteration_transitions"]),
            row["pair_id"],
        )
    )

    return {
        "schema": "ordinary_contact_iteration_audit/v1",
        "status": "post_run_contact_element_topology_diagnostic",
        "contact_pair_count": len(pairs),
        "element_count": len(elements),
        "iteration_group_count": len(groups),
        "ordered_owner_pair_identity": {
            "cel_explicitly_stores_pair_id": False,
            "cel_set_name_stores": "step, increment, cutback attempt, and iteration only",
            "connectivity_orientation_source": "pinned gencontelem_f2f.f writes master face nodes (nodefm) before slave face nodes (nodefs); C3D8 uses 4+4 slots, C3D6 uses 3+3 slots",
            "mesh_node_owners_disjoint": not duplicates,
            "duplicate_or_multibody_node_count": len(duplicates),
            "ordered_owner_pair_tuple_count": len(pair_lookup),
            "ordered_owner_pair_tuple_is_unique": all(len(matches) == 1 for matches in pair_lookup.values()),
            "interpretation": "Pair identity is reconstructed from ordered connectivity-side mesh-body ownership and the frozen contact manifest; no pair name is present in the CEL set name.",
        },
        "classification": {
            "exactly_mapped_contact_element_count": sum(
                1 for _, row in owned_records if row.get("status") == "exact"
            ),
            "ambiguous_or_unmapped_contact_element_count": sum(
                1 for _, row in owned_records if row.get("status") != "exact"
            ),
            "ambiguous_or_unmapped_reasons": dict(sorted(unknown_reasons.items())),
            "examples": unknown_examples,
        },
        "provenance": dict(provenance or {}),
        "convergence_alignment": {
            "cvg_row_count": len(cvg_counts),
            "cel_iteration_group_count": len(groups),
            "cvg_rows_aligned_by_exact_contact_element_count": len(aligned_keys),
            "cvg_rows_without_cel_group": [
                {"step": key.step, "increment": key.increment, "attempt": key.attempt, "iteration": key.iteration}
                for key in cvg_rows_without_cel
            ],
            "count_mismatches": cvg_mismatches,
            "cel_groups_without_cvg_row": [
                {
                    "step": key.step,
                    "increment": key.increment,
                    "attempt": key.attempt,
                    "iteration": key.iteration,
                    "contact_element_count": cel_total_by_key[key],
                    "all_record_lines_parse": True,
                    "complete_iteration_dump_authenticated": False,
                }
                for key in cel_groups_without_cvg
            ],
            "final_group_assessment": (
                "The terminal CEL group parses structurally but lacks a matching CVG row; the launcher ended by bounded timeout, so this group may be pre-solve or partially appended and its completeness is unverified. It is excluded from confirmed switching rankings."
                if cel_groups_without_cvg
                else "All CEL iteration groups have matching CVG total counts."
            ),
            "confirmed_adjacent_transition_count": sum(
                1 for row in transitions if row["comparison_status"] == "cvg_aligned"
            ),
            "unverified_adjacent_transition_count": sum(
                1 for row in transitions if row["comparison_status"] != "cvg_aligned"
            ),
            "first_last_cvg_aligned_iteration_comparison": endpoint_comparison,
        },
        "category_signature_turnover": dict(sorted(category_churn.items())),
        "pair_switching_rank": ranked_pairs,
        "iterations": groups_out,
        "adjacent_iteration_transitions": transitions,
        "limits": [
            "Contact-element counts and master/slave face-node signatures are topology indicators only; they do not contain contact force, pressure, displacement, residual norms, or convergence status.",
            "The set name identifies step/increment/attempt/iteration. Pair identity is inferred only if connectivity-side node owners map exactly to one frozen ordered owner pair; all unresolved records remain explicitly ambiguous or unmapped.",
            "Iteration-to-iteration node-signature turnover locates changing generated contact-face associations, but by itself does not establish physical chatter or its cause.",
            "No capacity, contact stiffness, material property, force equilibrium, or joint acceptance is inferred.",
        ],
    }


def load_terminal_checkpoint(checkpoint: Path) -> tuple[dict[str, Any], Mapping[str, Any], Mapping[str, Any], bytes, bytes, dict[str, Any]]:
    checkpoint = checkpoint.resolve()
    execution = json.loads((checkpoint / "execution.json").read_text())
    if execution.get("status") == "running":
        raise RuntimeError("checkpoint execution.json still says running; refusing to parse live pilot.cel")
    if "returncode" not in execution:
        raise RuntimeError("terminal execution record lacks a solver return code")
    input_freeze_bytes = (checkpoint / "input-freeze.json").read_bytes()
    input_freeze = json.loads(input_freeze_bytes)
    if execution.get("input_freeze_sha256") != sha256_bytes(input_freeze_bytes):
        raise ValueError("execution record input-freeze hash does not match checkpoint")
    relevant = ("mesh.inp", "mesh.json", "contact-fragment.inc", "contact-manifest.json")
    for name in relevant:
        expected = input_freeze.get("source_sha256", {}).get(name)
        if not expected:
            raise ValueError(f"input-freeze.json does not bind required source {name}")
        actual = sha256_file(checkpoint / name)
        if actual != expected:
            raise ValueError(f"frozen checkpoint source hash mismatch: {name}")
    mesh = json.loads((checkpoint / "mesh.json").read_text())
    manifest = json.loads((checkpoint / "contact-manifest.json").read_text())
    if mesh.get("mesh_input_sha256") != sha256_file(checkpoint / "mesh.inp"):
        raise ValueError("mesh.json does not bind the current mesh.inp bytes")
    if manifest.get("contact_fragment_sha256") != sha256_file(checkpoint / "contact-fragment.inc"):
        raise ValueError("contact manifest does not bind contact-fragment.inc")
    cel_path = checkpoint / "pilot.cel"
    cel_bytes = cel_path.read_bytes()
    cel_sha = sha256_bytes(cel_bytes)
    expected_cel_sha = execution.get("outputs_sha256", {}).get("pilot.cel")
    if not expected_cel_sha:
        raise RuntimeError("terminal execution record has no pilot.cel output hash; refusing an unbound CEL file")
    if expected_cel_sha != cel_sha:
        raise ValueError("pilot.cel bytes differ from the terminal execution output hash")
    cvg_path = checkpoint / "pilot.cvg"
    cvg_bytes = cvg_path.read_bytes()
    cvg_sha = sha256_bytes(cvg_bytes)
    expected_cvg_sha = execution.get("outputs_sha256", {}).get("pilot.cvg")
    if not expected_cvg_sha:
        raise RuntimeError("terminal execution record has no pilot.cvg output hash; refusing unbound convergence rows")
    if expected_cvg_sha != cvg_sha:
        raise ValueError("pilot.cvg bytes differ from the terminal execution output hash")
    provenance = {
        "checkpoint_path": str(checkpoint),
        "execution_status": execution.get("status"),
        "solver_returncode": execution.get("returncode"),
        "input_freeze_sha256": execution.get("input_freeze_sha256"),
        "pilot_cel_sha256": cel_sha,
        "pilot_cel_matches_terminal_output_hash": True,
        "pilot_cvg_sha256": cvg_sha,
        "pilot_cvg_matches_terminal_output_hash": True,
        "pilot_rout_present": (checkpoint / "pilot.rout").is_file(),
        "mesh_json_sha256": sha256_file(checkpoint / "mesh.json"),
        "mesh_inp_sha256": sha256_file(checkpoint / "mesh.inp"),
        "contact_manifest_sha256": sha256_file(checkpoint / "contact-manifest.json"),
        "contact_fragment_sha256": sha256_file(checkpoint / "contact-fragment.inc"),
        "solver_observations": execution.get("observations", []),
    }
    if WRITER_SOURCE.is_file():
        provenance["pinned_gencontelem_f2f_path"] = str(WRITER_SOURCE)
        provenance["pinned_gencontelem_f2f_sha256"] = sha256_file(WRITER_SOURCE)
    return execution, mesh, manifest, cel_bytes, cvg_bytes, provenance


def _write_outputs(result: Mapping[str, Any], output_dir: Path) -> tuple[Path, Path, Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "ordinary-contact-iteration-audit.json"
    counts_path = output_dir / "iteration-pair-counts.csv"
    transitions_path = output_dir / "pair-switching-transitions.csv"
    endpoints_path = output_dir / "endpoint-pair-counts.csv"
    markdown_path = output_dir / "ordinary-contact-iteration-audit.md"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    with counts_path.open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "step", "increment", "attempt", "iteration", "pair_id", "category",
                "master_owner", "slave_owner", "contact_element_count", "active_face_pair_signature_count",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for group in result["iterations"]:
            for pair in group["pair_counts"]:
                writer.writerow(
                    {
                        "step": group["step"], "increment": group["increment"],
                        "attempt": group["attempt"], "iteration": group["iteration"],
                        **pair,
                    }
                )
    with transitions_path.open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "step", "increment", "attempt", "iteration_before", "iteration_after", "iteration_gap", "comparison_status",
                "pair_id", "category", "master_owner", "slave_owner", "contact_element_count_before",
                "contact_element_count_after", "contact_element_count_delta",
                "retained_face_pair_signature_multiplicity", "appeared_face_pair_signature_multiplicity",
                "disappeared_face_pair_signature_multiplicity",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for transition in result["adjacent_iteration_transitions"]:
            for pair in transition["pair_transitions"]:
                writer.writerow(
                    {
                        "step": transition["step"], "increment": transition["increment"],
                        "attempt": transition["attempt"], "iteration_before": transition["iteration_before"],
                        "iteration_after": transition["iteration_after"], "iteration_gap": transition["iteration_gap"],
                        **pair,
                    }
                )

    endpoints = result["convergence_alignment"]["first_last_cvg_aligned_iteration_comparison"]
    with endpoints_path.open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "pair_id", "category", "master_owner", "slave_owner",
                "first_aligned_step", "first_aligned_increment", "first_aligned_attempt", "first_aligned_iteration",
                "last_aligned_step", "last_aligned_increment", "last_aligned_attempt", "last_aligned_iteration",
                "first_aligned_contact_element_count", "last_aligned_contact_element_count", "count_delta",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for pair in endpoints["pair_counts"]:
            writer.writerow(
                {
                    **pair,
                    **{f"first_aligned_{key}": value for key, value in endpoints["first_group"].items()},
                    **{f"last_aligned_{key}": value for key, value in endpoints["last_group"].items()},
                }
            )

    identity = result["ordered_owner_pair_identity"]
    classification = result["classification"]
    provenance = result["provenance"]
    alignment = result["convergence_alignment"]
    endpoints = alignment["first_last_cvg_aligned_iteration_comparison"]
    changing = [row for row in result["pair_switching_rank"] if row["signature_turnover"] > 0]
    lines = [
        "# Ordinary transient contact iteration audit",
        "",
        "**Scope: post-run generated contact-element topology only.** No solver execution or CAD work is performed by this parser. It refuses a live checkpoint and binds the parsed CEL bytes to the terminal execution record.",
        "",
        f"Checkpoint: `{provenance.get('checkpoint_path', 'unknown')}`. Execution status: `{provenance.get('execution_status', 'unknown')}`; solver return code: `{provenance.get('solver_returncode', 'unknown')}`. Parsed {result['element_count']} CEL elements in {result['iteration_group_count']} distinct step/increment/attempt/iteration groups. A `pilot.rout` file is present: {str(provenance.get('pilot_rout_present', False)).lower()}; no final converged response is available.",
        "",
        f"Contact-element pair identity is **not explicit** in the CEL set name. The set name records step, increment, attempt, and iteration. The parser assigns pair ID from ordered master/slave connectivity owners, using the pinned source's `nodefm` then `nodefs` output order, the frozen disjoint mesh node-owner table, and the original contact manifest. The static owner mapping has {identity['ordered_owner_pair_tuple_count']} ordered owner tuples for {result['contact_pair_count']} pairs; mesh node ownership disjoint={str(identity['mesh_node_owners_disjoint']).lower()}. Exactly mapped={classification['exactly_mapped_contact_element_count']}; ambiguous/unmapped={classification['ambiguous_or_unmapped_contact_element_count']}.",
        "",
        f"CEL SHA-256: `{provenance.get('pilot_cel_sha256', 'unknown')}`; terminal output hash match={str(provenance.get('pilot_cel_matches_terminal_output_hash', False)).lower()}. Contact manifest SHA-256: `{provenance.get('contact_manifest_sha256', 'unknown')}`. Mesh JSON SHA-256: `{provenance.get('mesh_json_sha256', 'unknown')}`. `gencontelem_f2f.f` SHA-256: `{provenance.get('pinned_gencontelem_f2f_sha256', 'not available')}`.",
        "",
        "## CEL/CVG alignment and final block",
        "",
        f"There are {alignment['cvg_row_count']} CVG rows and {alignment['cel_iteration_group_count']} CEL iteration groups. {alignment['cvg_rows_aligned_by_exact_contact_element_count']} CVG rows match CEL totals exactly; there are {len(alignment['count_mismatches'])} count mismatches and {len(alignment['cel_groups_without_cvg_row'])} CEL-only group(s). {alignment['final_group_assessment']}",
        "",
        "## CVG-aligned iteration endpoints",
        "",
        f"The first and last rows with exact CVG/CEL total agreement are step {endpoints['first_group']['step']}, increment {endpoints['first_group']['increment']}, attempt {endpoints['first_group']['attempt']}, iterations {endpoints['first_group']['iteration']} and {endpoints['last_group']['iteration']}. These are solver iteration diagnostics, not accepted time-step endpoints. The total generated contact-element count changes from {endpoints['first_contact_element_count']} to {endpoints['last_contact_element_count']} ({endpoints['contact_element_count_delta']:+d}).",
        "",
        "| Contact family | First aligned count | Last aligned count | Delta |",
        "| --- | ---: | ---: | ---: |",
    ]
    for category in sorted(set(endpoints["first_category_counts"]) | set(endpoints["last_category_counts"])):
        first_count = int(endpoints["first_category_counts"].get(category, 0))
        last_count = int(endpoints["last_category_counts"].get(category, 0))
        lines.append(f"| `{category}` | {first_count} | {last_count} | {last_count - first_count:+d} |")
    lines.extend(
        [
            "",
            "Owner-resolved first/last counts for all 35 original pairs are in [`endpoint-pair-counts.csv`](endpoint-pair-counts.csv). No owner-level run-to-run comparison is possible here because the older pilot did not emit `pilot.cel`.",
            "",
            "## Pair switching rank",
            "",
            "Ranked by cumulative appeared plus disappeared master/slave face-node signature multiplicity across adjacent CVG-aligned iterations within the same step, increment, and cutback attempt. Equal counts can still have turnover; regenerated element labels are not used as identities. Transitions involving unaligned CEL-only/mismatched groups are excluded from this ranking and remain in the CSV as unverified.",
            "",
            "| Rank | Pair ID | Category | Master owner | Slave owner | Iteration transitions with change | Count-changing transitions | Signature turnover | Maximum absolute count change |",
            "| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for index, row in enumerate(changing[:20], start=1):
        lines.append(
            f"| {index} | `{row['pair_id']}` | `{row['switching_bucket']}` | `{row['master_owner']}` | `{row['slave_owner']}` | {row['changed_iteration_transitions']} | {row['count_changed_transitions']} | {row['signature_turnover']} | {row['max_abs_count_delta']} |"
        )
    if not changing:
        lines.append("| — | No signature turnover observed in adjacent iteration records. | — | — | — | — | — | 0 | 0 |")
    lines.extend(
        [
            "",
            "## Switching by contact family",
            "",
            "| Family | Cumulative signature turnover |",
            "| --- | ---: |",
        ]
    )
    for category, count in sorted(result["category_signature_turnover"].items()):
        lines.append(f"| `{category}` | {count} |")
    lines.extend(
        [
            "",
            "## Files and limits",
            "",
            f"- Full per-iteration counts for all {result['contact_pair_count']} manifest pairs, including zeros: [`iteration-pair-counts.csv`](iteration-pair-counts.csv).",
            "- Adjacent-iteration count changes and retained/appeared/disappeared face signatures: [`pair-switching-transitions.csv`](pair-switching-transitions.csv).",
            "- Owner-resolved first/last CVG-aligned comparison: [`endpoint-pair-counts.csv`](endpoint-pair-counts.csv).",
            "- Full machine-readable grouped result and unresolved element samples: [`ordinary-contact-iteration-audit.json`](ordinary-contact-iteration-audit.json).",
            "",
            "Counts/signature changes locate where generated contact-face associations changed. They do not establish physical chatter, normal pressure, contact force, residual or force convergence, a cause for the change, or structural acceptance. Rounded solver fields printed as `0.000000` are not treated as exact zeros. A missing/ambiguous owner mapping remains unresolved.",
            "",
        ]
    )
    markdown_path.write_text("\n".join(lines))
    return json_path, counts_path, transitions_path, endpoints_path, markdown_path


def audit_checkpoint(checkpoint: Path, output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    execution, mesh, manifest, cel_bytes, cvg_bytes, provenance = load_terminal_checkpoint(checkpoint)
    elements = parse_cel(cel_bytes.decode("ascii", errors="strict"))
    convergence_counts = parse_cvg(cvg_bytes.decode("ascii", errors="replace"))
    result = build_audit(elements, mesh, manifest, convergence_counts=convergence_counts, provenance=provenance)
    paths = _write_outputs(result, output_dir)
    return {"result": result, "outputs": [str(path) for path in paths]}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", nargs="?", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args(argv)
    try:
        outcome = audit_checkpoint(args.checkpoint, args.output_dir)
    except Exception as error:  # print a clear reason; do not silently produce partial artifacts
        print(f"contact audit refused/failed: {error}", file=sys.stderr)
        return 2
    result = outcome["result"]
    print(
        json.dumps(
            {
                "status": result["status"],
                "elements": result["element_count"],
                "iteration_groups": result["iteration_group_count"],
                "exactly_mapped": result["classification"]["exactly_mapped_contact_element_count"],
                "ambiguous_or_unmapped": result["classification"]["ambiguous_or_unmapped_contact_element_count"],
                "outputs": outcome["outputs"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
