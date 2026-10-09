"""Source-only frozen v1 review; no CAD/BREP/native execution or adoption."""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = OWN.parents[2]
EXPECTED = {
    "query.py": "b9a888032c19a7616619bb27355aa2aeb5a0ade862aa748ad08d80ababd0ebfb",
    "inputs.json": "1480f590f0b870a86acf489b780d4eb34c4ef7760a8dc88bc0c70c58b311bf24",
    "parent-method-readiness-v1.json": "4c32ef7dd354049921f88511dbba969775701379634c9b8764030d7cc3208e09",
    "runs-v1/method01/result.json": "f833ad8f03a3cedaab27c9af4c91a0584a808cfce183958b75d3536499c7750a",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Vector:
    """Arithmetic-only vector, deliberately unrelated to CAD objects."""

    def __init__(self, *values):
        self.values = tuple(values)
        self.x, self.y, self.z = values

    def __add__(self, other):
        return Vector(*(a+b for a, b in zip(self.values, other.values, strict=True)))

    def __sub__(self, other):
        return Vector(*(a-b for a, b in zip(self.values, other.values, strict=True)))

    def multiply(self, factor):
        return Vector(*(v*factor for v in self.values))

    def toTuple(self):
        return self.values


def reject(call, text):
    try:
        call()
    except ValueError as error:
        require(text in str(error), "unexpected rejection: " + str(error))
        return str(error)
    raise ValueError("negative control accepted")


def main():
    target = {str((PACKET/p).relative_to(ROOT)): h for p, h in EXPECTED.items()}
    require(all(sha(ROOT/p) == h for p, h in target.items()), "target changed before review")
    query = load(PACKET / "query.py", "frozen_v1_method_query_review")
    inp = read(PACKET / "inputs.json")
    pins = {**inp["source_sha256"], **target}
    query.verify(pins)
    fixture = read(PACKET / "runs-v1/method01/result.json")
    require(fixture["query_sha256"] == EXPECTED["query.py"]
            and fixture["inputs_sha256"] == EXPECTED["inputs.json"]
            and fixture["pass"] is True, "fixture source binding differs")
    require(fixture["fixtures"]["known_answer_or_negative_checks"] == 7
            and fixture["fixtures"]["candidate_BREP_imports"] == 0, "fixture declared scope differs")
    with patch.object(query, "methods", side_effect=AssertionError("native methods forbidden")):
        query.preflight(PACKET / "parent-method-readiness-v1.json", True)
        unauthorized = reject(lambda: query.preflight(PACKET / "parent-method-readiness-v1.json", False),
                              "mode not authorized by parent")
        intake_failure = reject(lambda: query.source_inventory(inp), "analytic source inventory differs")

    analytic = query.module(inp["helpers"]["analytic_inventory"], "frozen_analytic_inventory_review")
    bound = query.read(ROOT / inp["analytic_inputs"]["path"])
    data = {k: query.read(ROOT/ref["path"]) for k, ref in bound["sources"].items()
            if ref["path"].endswith(".json")}
    datum = query.module(bound["sources"]["datum_helper"], "frozen_datum_review")
    axes, proposed, members, cuts = analytic.existing_inventory(bound, data, datum)
    prior = query.read(ROOT/inp["analytic_result"]["path"])
    require(members != prior["affected_members"] and query.canonical(members) == query.canonical(prior["affected_members"]),
            "confirmed tuple/list-only inventory difference not reproduced")
    require(isinstance(members["eoere_cleat_left"]["YZ_polygon_mm"][0], tuple)
            and isinstance(prior["affected_members"]["eoere_cleat_left"]["YZ_polygon_mm"][0], list)
            and list(proposed.values()) == prior["proposed_axes"], "tuple/list failure cause differs")

    # Bypass only the confirmed failed join in this review's memory. This is not
    # a corrected producer and never invokes the candidate reconstruction.
    geometry = data["geometry"]
    before = copy.deepcopy(geometry)
    scenario_checks = []
    cq_stub = SimpleNamespace(cq=SimpleNamespace(Vector=Vector))
    for scenario in inp["scenarios"]:
        selected = query.local_axes(geometry, proposed, members, cq_stub, scenario=scenario)
        require(len(selected) == 12 and sum(len(a["receivers"]) for a in selected) == 16,
                "local axes/receiver census differs")
        moves = []
        external_seats = []
        for axis in selected:
            expected = copy.deepcopy(axes[axis["id"]])
            expected["receivers"] = [n for n in expected["receivers"] if n in members]
            if axis["id"] in proposed and scenario != "current_Z200_modeled":
                expected["point_xyz_mm"][2] = 180.0
                moves.append(axis["id"])
            if scenario == "proposed_Z180_all11p1125":
                expected["bore_diameter_mm"] = 11.1125
            require({k: v for k, v in axis.items() if k not in ("point", "direction")} == expected,
                    "unexpected local-axis mutation")
            for name in axis["receivers"]:
                row = members[name]
                interval = sorted(axis["direction_xyz"][0]*(x-axis["point_xyz_mm"][0])
                                  for x in row["X_interval_mm"])
                require(interval[0] >= -1e-6 and interval[1] <= axis["grip_mm"]+1e-6
                        and abs(interval[1]-interval[0]-row["thickness_mm"]) < 1e-6,
                        "finite cutter does not cover own receiver")
                require(analytic.polygon_margin(axis["point_xyz_mm"][1:], row["YZ_polygon_mm"])
                        > axis["bore_diameter_mm"]/2, "bore crosses raw stock edge")
                for end, station, sign in (("head", 0., 1), ("nut", axis["grip_mm"], -1)):
                    point = axis["point"]+axis["direction"].multiply(station)
                    inward = axis["direction"].multiply(sign)
                    face_x = row["X_interval_mm"][0 if inward.x > 0 else 1]
                    if abs(point.x-face_x) < inp["tolerances"]["coordinate_mm"]:
                        require(axis["before_plate_mm" if end == "head" else "after_plate_mm"] == 0,
                                "wood seat actually belongs behind an external plate")
                        external_seats.append((axis["id"], name, end))
                        require(axis["bore_diameter_mm"] <= axis["hardware_scenario"]["washer_id_mm"],
                                "own bore exceeds nominal annulus opening")
        require(len(moves) == (0 if scenario == "current_Z200_modeled" else 4)
                and len(external_seats) == len(set(external_seats)) == 16, "substitution/seat census differs")
        for name in members:
            own = [a for a in selected if name in a["receivers"]]
            require(len(own) == len(cuts[name]) == 4, "incomplete own cut inventory")
            require(all(math.dist(a["point_xyz_mm"][1:], b["point_xyz_mm"][1:])
                        > (a["bore_diameter_mm"]+b["bore_diameter_mm"])/2
                        for index, a in enumerate(own) for b in own[index+1:]), "own cylinders overlap")
        scenario_checks.append({"scenario": scenario, "axes": 12, "receiver_occurrences": 16,
                                "translated_axis_ids": sorted(moves), "external_own_nominal_seats": 16})
    require(geometry == before, "scenario view mutated current geometry")

    raw_manifest = read(ROOT/inp["raw_post_manifest"]["path"])
    raw_records = {r["member"]: r for r in raw_manifest["raw_parts"] if r["member"] in inp["raw_post_sources"]}
    for name, ref in inp["raw_post_sources"].items():
        row = raw_records[name]
        require(all(row[k] == ref[k] for k in ("path", "sha256")), "raw post source join differs")
        profile = members[name]
        expected_bounds = [profile["X_interval_mm"], [min(p[0] for p in profile["YZ_polygon_mm"]),
                           max(p[0] for p in profile["YZ_polygon_mm"])],
                           [min(p[1] for p in profile["YZ_polygon_mm"]), max(p[1] for p in profile["YZ_polygon_mm"])]]
        query.close_bounds(row["bounds_xyz_mm"], expected_bounds, inp["tolerances"]["coordinate_mm"])
        require(abs(row["volume_mm3"]-profile["raw_volume_mm3"]) < inp["tolerances"]["volume_mm3"],
                "old raw post metadata not current profile compatible")
    # Inspect only the AST of native-facing methods, never import their modules.
    reviewed_functions = {
        "bore": ["bore_wood"], "wall": ["finished_bore_wall_intervals"],
        "annulus": ["annular_backing"], "strict_solid": ["strict_solid", "wrapper_fixture"],
        "overlap": ["overlaps"], "pure_loader": ["pinned_functions"], "brep": ["brep_sha"],
    }
    for key, names in reviewed_functions.items():
        tree = ast.parse((ROOT/inp["helpers"][key]["path"]).read_bytes())
        require({n.name for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names} == set(names),
                "reused method AST census differs")
    require(not any(n == "cadquery" or n == "OCP" or n.startswith("OCP.") for n in sys.modules),
            "native module imported during source review")
    query.verify(pins)
    findings = [{
        "severity": "P1", "file": str((PACKET/"query.py").relative_to(ROOT)), "line": 168,
        "title": "Normalize the JSON inventory join before the candidate query",
        "impact": "The exact frozen source_inventory call always raises 'analytic source inventory differs': its four profile polygons contain tuples, whereas prior saved JSON contains lists. The seven native toy fixtures never exercise this source intake, so they cannot make the candidate path executable.",
        "fix": "In a new frozen revision, compare canonical JSON representations (or normalize recomputed tuples to lists) for the exact member and proposed-axis joins; add a source-only inventory intake check before any candidate geometry execution.",
    }]
    receipt = {
        "schema": "eoere_four_finished_receiver_v1_independent_correctness_method_review/v1",
        "status": "CONFIRMED_SOURCE_INTAKE_BLOCKER", "target_sha256": target,
        "review_helper_sha256": sha(OWN), "source_files_rehashed_before_after": len(pins),
        "sources_unchanged_before_after": True, "findings": findings,
        "checks": {"exact_intake_failure": intake_failure, "canonical_member_join_equal": True,
                   "candidate_permit_rejected": unauthorized, "scenario_views": scenario_checks,
                   "current100_and66_unchanged": True, "four_hosts_four_own_bores_each": True,
                   "raw_post_manifest_coordinates_already_current": True,
                   "native_method_functions_read_as_source_only": reviewed_functions,
                   "saved_native_toy_checks_reused_without_rerun": 7},
        "reviewed_scope": [
            "Complete frozen query/inputs/fixture-only permit/result and all38 direct source pins; exact current and placement identity through reused stdlib inventory.",
            "Four source-only Z200-to-Z180 substitutions, twelve local axes/sixteen own receiver occurrences, all four recorded own cuts per host, finite cutter coverage and disjoint full circles in each raw profile.",
            "Raw post BREP manifest coordinate role checked as saved metadata only; no additional right-side translation; full current sloping cleat profiles.",
            "Reused bore cutter, own cylindrical-face/radius/axis matching, merged full-wall interval logic, nominal annular inward skin with exactly one own host, strict transparent compound chain and location/orientation retention.",
            "Producer source inspection of current Boolean missing/added-volume/bounds comparison, export/reimport before wall/annulus observations, volume identity, three scenarios, false release flags and active retention wording.",
        ],
        "limits": [
            "Source-only method review. No CAD/OCP import, BREP query/reconstruction, actual native toy rerun, candidate geometry execution, mechanics/global solve, adoption or physical work.",
            "Later method logic reviewed after a review-only in-memory bypass of the confirmed join failure; the frozen producer was not changed and remains blocked.",
            "Saved native fixtures are authenticated supporting evidence, not an independent native audit. Baseline Boolean volume/bounds comparison is within numerical tolerance, not byte identity or general topology equivalence.",
            "All11p1125 is a local four-host maximum wood-hole scenario: twelve viewed axes/sixteen bore occurrences; no full-frame sensitivity or delivered/catalog-corner washer/tolerance qualification.",
            "Nominal annular geometry does not establish physical contact pressure, directional bearing, complete joint resistance, force transfer, fabrication or climbing release. Unmodeled screw pilots/countersinks remain excluded.",
        ],
    }
    out = OWN.with_name("receipt.json")
    with out.open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    query.verify(pins)
    print(json.dumps({"receipt": str(out.relative_to(ROOT)), "sha256": sha(out), "helper_sha256": sha(OWN),
                      "findings": len(findings), "source_files": len(pins)}, sort_keys=True))


if __name__ == "__main__":
    main()
