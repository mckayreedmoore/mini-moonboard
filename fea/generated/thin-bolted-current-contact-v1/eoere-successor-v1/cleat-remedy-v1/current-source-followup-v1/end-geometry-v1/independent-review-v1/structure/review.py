"""Source/ownership/retention review; no solves, geometry changes or publication."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve().parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
DOC = OWN.parents[1]
EXPECTED = {
    "analyze.py": "fc45c5e990b11c20a3e6e98e9723b25ec366d05a780b229d82cdb639c6dc4ad0",
    "result.json": "4c66a7f194a747a14291e25c4277ec7288aa95a9bef9eab68233312288e9be9b",
}
PRIOR = {
    "inputs.json": "989a518a33f05c72c38613e9b8c53fc85458fc1aabc94948803ff5f9fe2bbb7f",
    "prepare.py": "9d12bcaa8d375153f4e93e4bfbc36c283ee3167bd614049e698d92ed067395c4",
    "placement.json": "5e131e9f58014b4a9426aa6a976338b930f471221e19b8e0e122ceff105f9b39",
    "result.json": "26d27f9c8f5e3c1d91e48143341a8e808d0ece99f316eaf789e2fcbe22e4252a",
    "verify.py": "267ff85c8fa87930a56f960f9c12c5a01329c546e117f012d1f16eae34b3d0d4",
    "verification.json": "ba4ed094c618cc71385754f6c4d06a05787f3706273a4faa4c6987f650c48acb",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def record(path):
    raw = path.read_bytes()
    return {"sha256": digest(raw), "bytes": len(raw)}


def canonical(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def load(path):
    return json.loads(path.read_bytes())


def main():
    require(DOC.name == "end-geometry-v1" and OWN.parts[-2:] == ("independent-review-v1", "structure"), "exclusive output boundary differs")
    target = {n: record(DOC / n) for n in EXPECTED}
    prior = {n: record(DOC.parent / n) for n in PRIOR}
    require({n: r["sha256"] for n, r in target.items()} == EXPECTED, "frozen target differs")
    require({n: r["sha256"] for n, r in prior.items()} == PRIOR, "prior six-file packet differs")
    context = {n: record(ROOT / n) for n in ["AGENTS.md", "docs/wood-joints-mvp/README.md", "docs/wood-joints-mvp/completion-ledger.md"]}
    prior_own_review = {n: record(DOC.parent / "independent-review-v1/structure" / n) for n in ["review.py", "receipt.json"]}
    result = load(DOC / "result.json")
    pins = result["source_sha256"]
    require(len(pins) == 26 and all(record(ROOT / p)["sha256"] == sha for p, sha in pins.items()), "direct source pins differ")
    require(result["direct_sources_unchanged_before_after"] is True and result["inherited_source_closures_or_operator_arithmetic_reaudited"] is False, "source-admission boundary differs")
    require(all(v is False for v in result["release"].values()), "release claimed")
    require(result["execution"]["CAD_native_global_or_component_solve"] is False and result["execution"]["current_Z200_actions_applied_to_Z180_proposal"] is False, "execution/action-transfer claim differs")
    spec = importlib.util.spec_from_file_location("frozen_end_inventory_review", DOC / "analyze.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # methods() checks the frozen source and extracts only the six pure helpers;
    # build()/main(), source_inputs() and the resistance module imports never run.
    resolved, end = module.methods({})
    fixtures = [(33.3375, "softwood_parallel_tension", .5), (66.675, "softwood_parallel_tension", 1.), (33., "softwood_parallel_tension", None), (19.05, "perpendicular", .5), (38.1, "parallel_compression", 1.), (18., "parallel_compression", None)]
    for distance, category, expected in fixtures:
        marker = end(distance, 9.525, category)
        require(marker["end_factor_only"] == expected and marker["complete_geometry_factor"] is None, "pure end fixture differs")
    require(result["execution"]["square_end_helper_known_answer_fixtures"] == len(fixtures) == 6, "fixture count differs")
    source = load(ROOT / module.INPUT)
    summary = load(ROOT / module.SUMMARY)
    placement = load(ROOT / module.PLACEMENT)
    shafts = {s["axis_id"]: s for s in source["shafts"]}
    members = {m["name"]: m for m in source["timber_rows"]}
    require(len(shafts) == 100 and len(source["hillman_rows"]) == 66 and len(members) == 22, "current source census differs")
    geometry_ref = summary["geometry"]["report"]
    require(geometry_ref["sha256"] == "01ba30abe20c2efec136374b8d9a74a098a19929be3cc784b5ebcf7608e62a2d", "current geometry authority differs")
    require(placement["geometry_adopted"] is False and placement["current_geometry_source"] == geometry_ref, "proposal authority differs")
    require(tuple(c["case_id"] for c in summary["cases"]) == tuple(c["case_id"] for c in result["current_Z200_inventory"]["cases"]) == module.CASES, "case ownership/order differs")
    replays = 0
    for case, saved in zip(summary["cases"], result["current_Z200_inventory"]["cases"], strict=True):
        require(saved["report"] == case["rich"]["result"], "own report reference differs")
        report = load(ROOT / saved["report"]["path"])
        require(report["case_id"] == case["case_id"] and report["state_id"] == saved["state_id"] and report["current_geometry"] == geometry_ref, "own report identity differs")
        require(report["raw_field_sha256"] == case["field"]["sha256"] and report["field_admission_receipt_sha256"] == case["admission"]["sha256"], "field/admission report join differs")
        require(report["complete_joint_resistance"] is None and all(v is False for v in report["release"].values()), "report qualification differs")
        rows = {(r["axis_id"], r["receiver"]): r for r in report["findings"]["timber"]["wood_surfaces"] if r["axis_id"] in module.IDS}
        require(len(rows) == len(saved["current_Z200_surfaces"]) == 8, "eight own wood surfaces required")
        for inventory in saved["current_Z200_surfaces"]:
            aid, host = inventory["axis_id"], inventory["receiver"]
            row = rows[aid, host]
            require(inventory["current_axis_Z_mm"] == shafts[aid]["point"][2] == 200 and host in shafts[aid]["source_axis"]["receivers"], "current source/receiver ownership differs")
            bearings = {p["id"]: p for p in row["own_point_actions"] if p["kind"] == "common_shaft_bearing"}
            require(len(bearings) == len(inventory["own_bearings"]) == 2, "two own bearing points required")
            for bearing in inventory["own_bearings"]:
                original = bearings[bearing["id"]]
                signed = original["signed_components"]
                require(resolved(signed["force_on_receiver_xyz_n"], members[host]["axis"], shafts[aid]["basis"][0]) == signed, "pure signed replay differs")
                require(bearing["point_xyz_mm"] == original["point_xyz_mm"] and all(bearing[k] == signed[k] for k in bearing if k not in {"id", "point_xyz_mm"}), "inventory action copied from another owner")
                replays += 1
            require(inventory["bearing_parallel_sign_reversal"] == row["bearing_parallel_sign_reversal"] and inventory["bearing_crossgrain_sign_reversal"] == row["bearing_crossgrain_sign_reversal"] and row["complete_Cdelta"] is row["complete_Cg"] is None, "reversal/qualification changed")
    require(replays == result["current_Z200_inventory"]["bearing_point_count"] == 96, "bearing inventory count differs")
    markers = result["separate_unadopted_Z180_square_end_markers"]
    require(len(markers) == len({(r["axis_id"], r["receiver"]) for r in markers}) == 8, "proposal receiver ownership differs")
    for row in markers:
        require(row["proposed_point_xyz_mm"][2] == 180 and row["force_assigned_to_proposal"] is row["finished_net_section_or_fracture_qualified"] is False and row["complete_Cdelta"] is None, "proposal assigned current forces or capacity")
        require(all(marker["complete_geometry_factor"] is None for side in row["square_end_markers"].values() for marker in side.values()), "square-end marker promoted to complete factor")
        if row["receiver"].startswith("eoere_cleat_"):
            require(row["positive_square_end_mm"] is None and row["sloping_cleat_upper_end_classified"] is False, "sloping upper edge classified as square")
    require(result["primary_source"]["sha256"] == pins[module.NDS] == module.PINS[module.NDS] and result["primary_source"]["edition"] == "NDS2024", "specification provenance differs")
    tree = ast.parse((DOC / "analyze.py").read_bytes())
    method = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "methods")
    wanted = next(ast.literal_eval(n.value) for n in method.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "wanted" for t in n.targets))
    require(wanted == {"vector", "unit", "dot", "cross", "resolved_action", "end_geometry_factor"}, "pure extraction contract differs")
    main_source = ast.unparse(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main"))
    require("require(not args.out.exists(), 'preserve issued evidence')" in main_source and "args.out.open('x')" in main_source, "fresh exclusive output contract differs")
    # Exercise genuine main's occupied-output rejection with an inert parser;
    # replacing build with a sentinel proves no calculation can run here.
    def forbidden_build():
        raise RuntimeError("occupied output reached build")

    actual_parser, actual_build = module.argparse, module.build
    class Parser:
        def add_argument(self, *args, **kwargs):
            pass
        def parse_args(self):
            return SimpleNamespace(out=DOC / "result.json")
    try:
        module.argparse = SimpleNamespace(ArgumentParser=lambda **kwargs: Parser())
        module.build = forbidden_build
        try:
            module.main()
        except ValueError as error:
            require(str(error) == "preserve issued evidence", "wrong occupied-output rejection")
        else:
            raise ValueError("occupied output accepted")
    finally:
        module.argparse, module.build = actual_parser, actual_build
    require({n: record(DOC / n) for n in EXPECTED} == target and {n: record(DOC.parent / n) for n in PRIOR} == prior, "frozen bytes changed during review")
    require(all(record(ROOT / p)["sha256"] == sha for p, sha in pins.items()), "direct source changed during review")
    require(all(record(ROOT / p) == r for p, r in context.items()), "context changed during review")
    require({n: record(DOC.parent / "independent-review-v1/structure" / n) for n in prior_own_review} == prior_own_review, "prior owned review changed")
    receipt = {
        "schema": "eoere_end_geometry_architecture_source_retention_review/v1",
        "status": "NO_SUBSTANTIAL_CONFIRMED_ARCHITECTURE_SOURCE_OR_RETENTION_FINDINGS",
        "findings": [],
        "target": {"path": str(DOC.relative_to(ROOT)), "files": target, "bytes": sum(r["bytes"] for r in target.values())},
        "review_helper": record(Path(__file__)), "current_context": context,
        "direct_source_binding": {"count": 26, "hash_map_canonical_sha256": canonical(pins), "map_retained_in_bound_result_json": True, "authenticated_before_after": True, "recursive_closures_and_operator_arithmetic_reaudited": False},
        "prior_six_file_packet_unchanged": prior, "prior_owned_review_unchanged": prior_own_review,
        "checks": {"pure_extracted_helper_names": sorted(wanted), "end_known_answers": 6, "exact_signed_owner_replays": replays, "current_Z200_cases": 6, "current_Z200_wood_surfaces": 48, "separate_unadopted_Z180_marker_rows": 8, "proposal_force_or_complete_factor_assigned": False, "occupied_output_rejected_before_build": True},
        "architecture_assessment": [
            {"evidence": "analyze.py:52-62,107-144", "assessment": "One wrapper owns saved-record composition. It authenticates the existing resistance source and extracts exactly six pure functions, bypassing all material/CAD imports and component entrypoints. Current geometry/input/proposal identities stay pinned; no replacement model or copied source assets."},
            {"evidence": "analyze.py:145-209; result.json:current_Z200_inventory,separate_unadopted_Z180_square_end_markers", "assessment": "Six existing own-case reports supply 96 current-Z200 signed bearing points with exact receiver/case/state/field/admission bindings. Eight Z180 square-end marker rows have no assigned forces or complete factor. Sloping tops, oblique loaded-edge rules, finished ligaments and complete resistance remain outside the helper."},
            {"evidence": "analyze.py:192-220,223-234", "assessment": "Twenty-six direct sources are authenticated before/after without claiming inherited closure/operator re-admission. The CLI rejects existing output before build and creates files exclusively, preserving issued evidence and source aliases. The two-file 120,214-byte inventory retains useful owner-specific points while referencing existing reports/PDF/helpers. Prior packet/review and raw sources remain active; no cleanup or publication authority is inferred."}
        ],
        "limits": ["No target build/CLI replay, CAD/BREP, native/global/new component solve, geometry modification, cleanup or publication. Only six tiny pure end fixtures, 96 saved-action decompositions and an inert occupied-output guard ran.", "The pinned 2024 specification's mathematical/code applicability, full source closures, operators and admission were not independently re-audited here. Existing reports remain the action authority.", "All four current holds remain; no Z200 demand transfer to Z180, physical/tool qualification, geometry adoption, complete resistance or release follows. Parent owns final validation/publication."],
        "source_and_target_unchanged": True, "shared_edits_staging_commits": False,
        "reproduce_review": "python3 -B " + str(Path(__file__).relative_to(ROOT)),
    }
    raw = (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    (OWN / "receipt.json").write_bytes(raw)
    print(json.dumps({"status": receipt["status"], "receipt_sha256": digest(raw), "receipt_bytes": len(raw), "review_helper_sha256": receipt["review_helper"]["sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
