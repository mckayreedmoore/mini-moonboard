#!/usr/bin/env python3
"""Read-only audit of CLOAD/BOUNDARY F20.0 fields in preserved decks."""
from __future__ import annotations

import hashlib
import json
import tarfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
E = HERE.parent
ROOTS = (
    E / "ordinary-external-force-transient-attempt01",
    E / "ordinary-external-force-transient-attempt02",
    E / "ordinary-external-force-transient-attempt03",
    E / "ordinary-external-force-transient-attempt04-diagnostic",
    E / "ordinary-port-motion-attempt09-common-map",
)
SOURCE_ARCHIVE = (E / "ordinary-external-force-transient-attempt04-diagnostic"
                  / "build-attempt02" / "source.tar.bz2")
SOURCE_ARCHIVE_SHA256 = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
SOURCE_MEMBERS = ("cloads.f", "boundarys.f", "nodes.f", "equations.f")


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def canonical_sha(value: object) -> str:
    return sha_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=True).encode("ascii"))


def number_or_zero(token: str) -> float:
    token = token.strip()
    return 0.0 if not token else float(token)


def compare_scalar(token: str) -> dict:
    token = token.strip()
    parser_text = token[:20]
    full_value = number_or_zero(token)
    parser_value = number_or_zero(parser_text)
    difference = parser_value - full_value
    relative = abs(difference) / abs(full_value) if full_value else 0.0
    return {"source_token": token, "source_token_chars": len(token),
            "parser_text_first20": parser_text,
            "parser_text_chars": len(parser_text),
            "full_token_value": full_value,
            "parser_visible_value": parser_value,
            "parser_minus_full": difference,
            "absolute_difference": abs(difference),
            "relative_difference": relative}


def summarize_scalars(rows: list[dict]) -> dict:
    values = [row["scalar"] for row in rows]
    diffs = [value["absolute_difference"] for value in values]
    relative = [value["relative_difference"] for value in values]
    token_widths: dict[str, int] = {}
    for value in values:
        width = str(value["source_token_chars"])
        token_widths[width] = token_widths.get(width, 0) + 1
    return {
        "scalar_field_count": len(values),
        "over20_field_count": sum(v["source_token_chars"] > 20 for v in values),
        "max_token_chars": max((v["source_token_chars"] for v in values), default=0),
        "token_width_histogram_chars": token_widths,
        "nonzero_numeric_difference_count": sum(v["absolute_difference"] != 0.0 for v in values),
        "max_absolute_difference": max(diffs, default=0.0),
        "max_relative_difference": max(relative, default=0.0),
        "full_value_sequence_sha256": canonical_sha([
            value["full_token_value"] for value in values]),
        "parser_value_sequence_sha256": canonical_sha([
            value["parser_visible_value"] for value in values]),
    }


def audit_deck(path: Path) -> dict:
    lines = path.read_text(encoding="ascii").splitlines()
    keyword = ""
    cload_rows: list[dict] = []
    boundary_rows: list[dict] = []
    parse_errors = []
    for line_number, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("**"):
            continue
        if stripped.startswith("*"):
            keyword = stripped.split(",", 1)[0].upper()
            continue
        if keyword not in ("*CLOAD", "*BOUNDARY"):
            continue
        fields = [field.strip() for field in line.split(",")]
        if keyword == "*CLOAD":
            value_index = 2
            if len(fields) <= value_index:
                token = ""
                node = fields[0] if fields else ""
                dof = fields[1] if len(fields) > 1 else ""
            else:
                token = fields[value_index]
                node, dof = fields[:2]
            try:
                scalar = compare_scalar(token)
                cload_rows.append({"line": line_number, "node": node, "dof": dof,
                                   "scalar": scalar})
            except ValueError as error:
                parse_errors.append({"line": line_number, "card": keyword,
                                     "text": line, "error": str(error)})
        else:
            value_index = 3
            token = fields[value_index] if len(fields) > value_index else ""
            first = fields[1] if len(fields) > 1 else ""
            last = fields[2] if len(fields) > 2 and fields[2] else first
            try:
                scalar = compare_scalar(token)
                dof_count = max(1, int(last) - int(first) + 1)
                boundary_rows.append({"line": line_number,
                                      "node_or_set": fields[0] if fields else "",
                                      "first_dof": first, "last_dof": last,
                                      "expanded_dof_count": dof_count,
                                      "scalar": scalar})
            except (ValueError, TypeError) as error:
                parse_errors.append({"line": line_number, "card": keyword,
                                     "text": line, "error": str(error)})
    cload_summary = summarize_scalars(cload_rows)
    boundary_summary = summarize_scalars(boundary_rows)
    return {
        "path_from_evaluation_root": str(path.relative_to(E)),
        "sha256": sha_file(path),
        "size_bytes": path.stat().st_size,
        "CLOAD": {**cload_summary,
                  "row_count": len(cload_rows),
                  "nonzero_rows": sum(row["scalar"]["full_token_value"] != 0.0
                                       for row in cload_rows),
                  "max_expanded_dof_count": 1,
                  "examples": cload_rows[:2]},
        "BOUNDARY": {**boundary_summary,
                     "row_count": len(boundary_rows),
                     "expanded_dof_count": sum(row["expanded_dof_count"]
                                               for row in boundary_rows),
                     "nonzero_rows": sum(row["scalar"]["full_token_value"] != 0.0
                                          for row in boundary_rows),
                     "examples": boundary_rows[:2]},
        "parse_errors": parse_errors,
    }


def audit_node_coordinates(path: Path) -> dict:
    rows = []
    in_nodes = False
    for line_number, line in enumerate(path.read_text(encoding="ascii").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("**"):
            continue
        if stripped.startswith("*"):
            in_nodes = stripped.upper().startswith("*NODE")
            continue
        if not in_nodes:
            continue
        fields = [field.strip() for field in line.split(",")]
        if len(fields) < 4:
            continue
        for axis, token in enumerate(fields[1:4], 1):
            rows.append({"line": line_number, "node": fields[0], "axis": axis,
                         "scalar": compare_scalar(token)})
    summary = summarize_scalars(rows)
    overwidth = [row for row in rows if row["scalar"]["source_token_chars"] > 20]
    examples = [{"line": row["line"], "node": row["node"], "axis": row["axis"],
                 "source_token": row["scalar"]["source_token"],
                 "parser_first20": row["scalar"]["parser_text_first20"],
                 "parser_minus_source": row["scalar"]["parser_minus_full"]}
                for row in overwidth[:5]]
    return {"path_from_evaluation_root": str(path.relative_to(E)),
            "sha256": sha_file(path), "node_coordinate_components": len(rows),
            "overwidth_examples_first_five": examples,
            "overwidth_fields_with_exponent_marker": sum(
                "e" in row["scalar"]["source_token"].lower() for row in overwidth),
            **summary}


def audit_equation_coefficients(path: Path) -> dict:
    lines = path.read_text(encoding="ascii").splitlines()
    coefficients = []
    i = 0
    while i < len(lines):
        if lines[i].strip().upper() != "*EQUATION":
            i += 1
            continue
        i += 1
        while i < len(lines) and (not lines[i].strip() or lines[i].lstrip().startswith("**")):
            i += 1
        if i >= len(lines):
            break
        term_count = int(lines[i].strip())
        i += 1
        tokens = []
        while i < len(lines) and len(tokens) < 3 * term_count:
            if lines[i].strip().startswith("*"):
                raise ValueError(f"truncated equation in {path} near line {i + 1}")
            tokens.extend(token.strip() for token in lines[i].split(",") if token.strip())
            i += 1
        if len(tokens) != 3 * term_count:
            raise ValueError(f"equation term count mismatch in {path}")
        coefficients.extend(compare_scalar(tokens[j])
                             for j in range(2, len(tokens), 3))
    summary = summarize_scalars([{"scalar": value} for value in coefficients])
    return {"path_from_evaluation_root": str(path.relative_to(E)),
            "sha256": sha_file(path), **summary}


def producer_files() -> list[dict]:
    candidates = set()
    for root in ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.name in {"force-producer-runner.py.snapshot",
                             "external-ports-producer.py.snapshot",
                             "port-motion-producer.py.snapshot",
                             "producer.py.snapshot", "run_and_verify.py"}:
                candidates.add(path)
    records = []
    for path in sorted(candidates):
        text = path.read_text(encoding="utf-8", errors="replace")
        relevant = []
        for number, line in enumerate(text.splitlines(), 1):
            if ".13e" in line or "F20.0" in line or "fixed-width" in line.lower():
                relevant.append({"line": number, "text": line.strip()})
        records.append({"path_from_evaluation_root": str(path.relative_to(E)),
                        "sha256": sha_file(path), "relevant_format_lines": relevant})
    return records


def source_pins() -> dict:
    if sha_file(SOURCE_ARCHIVE) != SOURCE_ARCHIVE_SHA256:
        raise ValueError("pinned CalculiX 2.23 source archive changed")
    member_hashes = {}
    with tarfile.open(SOURCE_ARCHIVE, "r:bz2") as archive:
        for name in SOURCE_MEMBERS:
            member = archive.extractfile(f"./CalculiX/ccx_2.23/src/{name}")
            if member is None:
                raise ValueError(f"missing source member {name}")
            contents = member.read()
            member_hashes[name] = {"sha256": sha_bytes(contents),
                                   "size_bytes": len(contents)}
    return {"archive_path_from_evaluation_root": str(SOURCE_ARCHIVE.relative_to(E)),
            "archive_sha256": SOURCE_ARCHIVE_SHA256,
            "parser_contract": {
                "cloads.f": {"line": 267, "read": "CLOAD value textpart(3)(1:20), F20.0"},
                "boundarys.f": {"line": 355, "read": "BOUNDARY value textpart(4)(1:20), F20.0"},
                "nodes.f": {"lines": [140, 150, 160], "read": "NODE coordinate textpart(2:4)(1:20), F20.0"},
                "equations.f": {"line": 415, "read": "EQUATION coefficient textpart(...)(1:20), F20.0"},
            },
            "source_members": member_hashes}


def main() -> None:
    deck_paths = []
    geometry_paths = []
    equation_paths = []
    for root in ROOTS:
        for path in root.rglob("*.inp"):
            text = path.read_text(encoding="ascii", errors="replace").upper()
            if "*CLOAD" in text or "*BOUNDARY" in text:
                deck_paths.append(path)
            if path.name in {"mesh.inp", "nut-coupling.inp"}:
                geometry_paths.append(path)
            if path.name == "nut-coupling.inp":
                equation_paths.append(path)

    decks = [audit_deck(path) for path in sorted(set(deck_paths))]
    unique_geometry = {}
    for path in geometry_paths:
        digest = sha_file(path)
        unique_geometry.setdefault(digest, []).append(path)
    coordinate_records = []
    equation_records = []
    for digest, paths in sorted(unique_geometry.items()):
        path = sorted(paths)[0]
        if path.name in {"mesh.inp", "nut-coupling.inp"}:
            record = audit_node_coordinates(path)
            record["identical_content_paths"] = sorted(str(p.relative_to(E)) for p in paths)
            coordinate_records.append(record)
    unique_equations = {}
    for path in equation_paths:
        unique_equations.setdefault(sha_file(path), []).append(path)
    for digest, paths in sorted(unique_equations.items()):
        path = sorted(paths)[0]
        record = audit_equation_coefficients(path)
        record["identical_content_paths"] = sorted(str(p.relative_to(E)) for p in paths)
        equation_records.append(record)

    unique_decks = {}
    for row in decks:
        unique_decks.setdefault(row["sha256"], row)
    unique_rows = list(unique_decks.values())
    summary = {
        "file_observations_including_preserved_copies": {
            "CLOAD_field_count": sum(row["CLOAD"]["scalar_field_count"] for row in decks),
            "CLOAD_over20_fields": sum(row["CLOAD"]["over20_field_count"] for row in decks),
            "CLOAD_max_token_chars": max((row["CLOAD"]["max_token_chars"] for row in decks), default=0),
            "CLOAD_nonzero_numeric_differences": sum(row["CLOAD"]["nonzero_numeric_difference_count"] for row in decks),
            "BOUNDARY_field_count": sum(row["BOUNDARY"]["scalar_field_count"] for row in decks),
            "BOUNDARY_over20_fields": sum(row["BOUNDARY"]["over20_field_count"] for row in decks),
            "BOUNDARY_max_token_chars": max((row["BOUNDARY"]["max_token_chars"] for row in decks), default=0),
            "BOUNDARY_nonzero_numeric_differences": sum(row["BOUNDARY"]["nonzero_numeric_difference_count"] for row in decks),
            "BOUNDARY_expanded_dof_count": sum(row["BOUNDARY"]["expanded_dof_count"] for row in decks),
            "parse_errors": sum(len(row["parse_errors"]) for row in decks),
        },
        "unique_deck_contents": {
            "count": len(unique_rows),
            "CLOAD_field_count": sum(row["CLOAD"]["scalar_field_count"] for row in unique_rows),
            "CLOAD_over20_fields": sum(row["CLOAD"]["over20_field_count"] for row in unique_rows),
            "CLOAD_max_token_chars": max((row["CLOAD"]["max_token_chars"] for row in unique_rows), default=0),
            "CLOAD_nonzero_numeric_differences": sum(row["CLOAD"]["nonzero_numeric_difference_count"] for row in unique_rows),
            "BOUNDARY_field_count": sum(row["BOUNDARY"]["scalar_field_count"] for row in unique_rows),
            "BOUNDARY_over20_fields": sum(row["BOUNDARY"]["over20_field_count"] for row in unique_rows),
            "BOUNDARY_max_token_chars": max((row["BOUNDARY"]["max_token_chars"] for row in unique_rows), default=0),
            "BOUNDARY_nonzero_numeric_differences": sum(row["BOUNDARY"]["nonzero_numeric_difference_count"] for row in unique_rows),
            "BOUNDARY_expanded_dof_count": sum(row["BOUNDARY"]["expanded_dof_count"] for row in unique_rows),
        },
    }
    file_counts = summary["file_observations_including_preserved_copies"]
    clean = all(file_counts[key] == 0 for key in (
        "CLOAD_over20_fields", "CLOAD_nonzero_numeric_differences",
        "BOUNDARY_over20_fields", "BOUNDARY_nonzero_numeric_differences", "parse_errors"))
    result = {
        "schema": "ccx223_preserved_native_input_f20_audit/v1",
        "scope": [str(root.relative_to(E)) for root in ROOTS],
        "source": source_pins(),
        "deck_file_count_with_CLOAD_or_BOUNDARY": len(decks),
        "deck_files": decks,
        "unique_deck_content_sha256": sorted(unique_decks),
        "producer_files": producer_files(),
        "unique_mesh_coordinate_files": coordinate_records,
        "unique_nut_coupling_equation_files": equation_records,
        "summary": summary,
        "status": "PASS_NO_CLOAD_BOUNDARY_TRUNCATION" if clean else "REVIEW_REQUIRED",
    }
    (HERE / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "deck_files": len(decks),
                      "unique_deck_contents": len(unique_decks),
                      "summary": result["summary"]}, sort_keys=True))


if __name__ == "__main__":
    main()
