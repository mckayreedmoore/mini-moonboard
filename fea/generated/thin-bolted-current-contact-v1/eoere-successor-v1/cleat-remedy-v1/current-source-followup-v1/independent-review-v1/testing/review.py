"""Independent source/identity, scalar capsule and output-guard testing review."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve().parent
ROOT = next(p for p in OWN.parents if (p/"AGENTS.md").is_file())
TARGET = ROOT/"fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1"
EXPECTED = {
    "inputs.json": "989a518a33f05c72c38613e9b8c53fc85458fc1aabc94948803ff5f9fe2bbb7f",
    "prepare.py": "9d12bcaa8d375153f4e93e4bfbc36c283ee3167bd614049e698d92ed067395c4",
    "placement.json": "5e131e9f58014b4a9426aa6a976338b930f471221e19b8e0e122ceff105f9b39",
    "result.json": "26d27f9c8f5e3c1d91e48143341a8e808d0ece99f316eaf789e2fcbe22e4252a",
    "verify.py": "267ff85c8fa87930a56f960f9c12c5a01329c546e117f012d1f16eae34b3d0d4",
    "verification.json": "ba4ed094c618cc71385754f6c4d06a05787f3706273a4faa4c6987f650c48acb",
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(path):
    return digest(Path(path).read_bytes())


def read(path):
    return json.loads(Path(path).read_bytes())


def canonical(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def dot(a, b):
    return math.fsum(x*y for x, y in zip(a, b, strict=True))


def sub(a, b):
    return [x-y for x, y in zip(a, b, strict=True)]


def position(a, u, t):
    return [x+t*y for x, y in zip(a, u, strict=True)]


def segment_distance(a, b, c, d):
    """Minimize the convex squared distance on the closed parameter square."""
    u, v, w = sub(b, a), sub(d, c), sub(a, c)
    aa, bb, cc = dot(u, u), dot(u, v), dot(v, v)
    candidates = []
    for point in (a, b):
        t = 0 if cc == 0 else max(0, min(1, dot(sub(point, c), v)/cc))
        q = sub(point, position(c, v, t))
        candidates.append(dot(q, q))
    for point in (c, d):
        s = 0 if aa == 0 else max(0, min(1, dot(sub(point, a), u)/aa))
        q = sub(point, position(a, u, s))
        candidates.append(dot(q, q))
    denominator = aa*cc-bb*bb
    if denominator > 1e-12*aa*cc:
        dd, ee = dot(u, w), dot(v, w)
        s, t = (bb*ee-cc*dd)/denominator, (aa*ee-bb*dd)/denominator
        if 0 <= s <= 1 and 0 <= t <= 1:
            q = sub(position(a, u, s), position(c, v, t))
            candidates.append(dot(q, q))
    return math.sqrt(max(0, min(candidates)))


def primitive(ident, role, origin, direction, low, high, radius):
    length = math.sqrt(dot(direction, direction))
    assert abs(length-1) < 1e-8 and radius >= 0 and high > low
    unit = [v/length for v in direction]
    return (ident, role, position(origin, unit, low), position(origin, unit, high), radius)


def hardware(axis, maximum=False):
    h, g = axis["hardware_scenario"], axis["grip_mm"]
    w = h["washer_thickness_mm"]
    head, nut = -axis["before_plate_mm"]-w, g+axis["after_plate_mm"]+w
    intervals = [("shaft", head, head+axis["nominal_under_head_length_mm"], axis["diameter_mm"]/2),
                 ("head", head-h["head_height_mm"], head, h["hex_across_flats_mm"]/math.sqrt(3)),
                 ("head_washer", head, head+w, h["washer_od_mm"]/2),
                 ("nut_washer", nut-w, nut, h["washer_od_mm"]/2),
                 ("nut", nut, nut+h["nut_height_mm"], h["hex_across_flats_mm"]/math.sqrt(3)),
                 ("wood_bore_cutter", -1, g+1, (11.1125 if maximum else axis["bore_diameter_mm"])/2)]
    return [primitive(axis["id"], role, axis["point_xyz_mm"], axis["direction_xyz"], low, high, radius) for role, low, high, radius in intervals]


def check_summary(observed, first, second, own_pairs=False):
    count = positive = 0
    minimum = math.inf
    roles, maximum_pair_error = {}, 0.0
    witness_values = {}
    for a, b in itertools.product(first, second):
        if own_pairs and a[0] >= b[0]:
            continue
        distance = segment_distance(a[2], a[3], b[2], b[3])
        gap = distance-a[4]-b[4]
        count += 1
        positive += gap > 0
        minimum = min(minimum, gap)
        roles[a[1]] = min(roles.get(a[1], math.inf), gap)
        witness_values[a[:2]+b[:2]] = (distance, gap)
    assert count == observed["count"] and positive == observed["positive_bound_count"]
    assert observed["all_bounds_positive"] is (positive == count)
    assert abs(minimum-observed["minimum"]["capsule_separation_lower_bound_mm"]) < 1e-9
    assert set(roles) == set(observed["minimum_by_lower_role"])
    for role, witness in [(None, observed["minimum"]), *observed["minimum_by_lower_role"].items()]:
        distance, gap = witness_values[(witness["first"], witness["first_role"], witness["second"], witness["second_role"])]
        assert abs(distance-witness["finite_axis_distance_mm"]) < 1e-9
        assert abs(gap-witness["capsule_separation_lower_bound_mm"]) < 1e-9
        maximum_pair_error = max(maximum_pair_error, abs(gap-witness["capsule_separation_lower_bound_mm"]))
        if role is not None:
            assert witness["first_role"] == role and abs(gap-roles[role]) < 1e-9
    return count, maximum_pair_error


def main():
    assert not (OWN/"receipt.json").exists(), "do not overwrite a frozen review receipt"
    assert {n: sha(TARGET/n) for n in EXPECTED} == EXPECTED
    config, result, placement, verification = [read(TARGET/n) for n in ("inputs.json", "result.json", "placement.json", "verification.json")]
    assert len(config["sources"]) == 11 and len(result["source_sha256"]) == 13
    for path, expected in verification["source_sha256"].items():
        assert sha(ROOT/path) == expected, path
    current = read(ROOT/config["current_geometry"])
    cache = read(ROOT/config["current_cached_descriptors"])
    base_path = next(p for p in config["sources"] if p.endswith("occupied-adjusted-base-v3.json"))
    base = read(ROOT/base_path)
    assert current["axes"] == base["axes"] and current["screw_axes"] == base["screw_axes"]
    assert {a["id"]: a for a in current["axes"]} == {r["axis_id"]: r["source_axis"] for r in cache["shafts"]}
    assert {s["axis_id"]: s for s in current["screw_axes"]} == {r["id"]: r["source_screw_descriptor"] for r in cache["hillman_rows"]}
    targets = {f"cleat_post_bolt_{side}_{n}" for side in ("left", "right") for n in (1, 2)}
    assert set(config["target_axis_ids"]) == targets
    proposed_by_id = {a["id"]: a for a in placement["proposed_axes"]}
    assert set(proposed_by_id) == targets
    proposed = copy.deepcopy(current["axes"])
    changes = []
    for a in proposed:
        if a["id"] in targets:
            assert a["point_xyz_mm"][2] == 200
            before = copy.deepcopy(a)
            a["point_xyz_mm"][2] = 180.0
            assert a == proposed_by_id[a["id"]]
            changes.append({"axis_id": a["id"], "current_point_xyz_mm": before["point_xyz_mm"], "proposed_point_xyz_mm": a["point_xyz_mm"], "translation_xyz_mm": [0., 0., -20.]})
    assert changes == placement["changes"] and len(changes) == 4
    fixed = [a for a in current["axes"] if a["id"] not in targets]
    assert len(fixed) == 96 and len(current["screw_axes"]) == 66
    for key, rows in [("current_fixed_96_canonical_sha256", fixed), ("current_66_screws_canonical_sha256", current["screw_axes"]), ("current_100_axes_canonical_sha256", current["axes"]), ("proposed_100_axes_canonical_sha256", proposed)]:
        assert canonical(rows) == placement[key]
    assert result["placement"]["sha256"] == EXPECTED["placement.json"]
    assert placement["geometry_adopted"] is False and placement["optional_2026_extra"] is False
    assert all(v is False for v in result["release"].values())
    assert result["new_bore_wall_seat_tool_or_response_qualification"] is False
    assert set(result["current_drilling_holds"]) == targets

    # Independent scalar, general 3D distances for every issued comparison.
    screws = [primitive(s["axis_id"], role, s["origin_xyz_mm"], s["direction_xyz"], low, high, radius) for s in current["screw_axes"] for role, low, high, radius in [("screw_body", 3., 63.5, 2.5), ("screw_head_containing_cylinder", 0., 3., 4.5)]]
    fixed_primitives = [p for a in fixed for p in hardware(a)]
    count, max_error = 0, 0.0
    independent_screens = []
    assert [s["id"] for s in result["screens"]] == ["current_Z200", "proposed_Z180"]
    for screen, axes in zip(result["screens"], (current["axes"], proposed), strict=True):
        lower = [a for a in axes if a["id"] in targets]
        nominal = [p for a in lower for p in hardware(a)]
        maximum = [p for a in lower for p in hardware(a, True)]
        for key, a, b, own in [("nominal_bore_vs_66_current_screws", nominal, screws, False), ("maximum_bore_vs_66_current_screws", maximum, screws, False), ("maximum_bore_vs_96_current_fixed_bolts", maximum, fixed_primitives, False), ("maximum_bore_vs_other_lower_bolts", maximum, maximum, True)]:
            n, error = check_summary(screen[key], a, b, own)
            count += n
            max_error = max(max_error, error)
        independent_screens.append({"id": screen["id"], "nominal_screw_minimum_mm": screen["nominal_bore_vs_66_current_screws"]["minimum"]["capsule_separation_lower_bound_mm"], "maximum_screw_minimum_mm": screen["maximum_bore_vs_66_current_screws"]["minimum"]["capsule_separation_lower_bound_mm"], "maximum_screw_nonpositive_bounds": 3168-screen["maximum_bore_vs_66_current_screws"]["positive_bound_count"]})
    assert count == 40752 == verification["general_segment_comparisons"]
    assert abs(independent_screens[0]["maximum_screw_minimum_mm"]+.05625) < 1e-9
    assert abs(independent_screens[1]["maximum_screw_minimum_mm"]-3.94375) < 1e-9

    producer = module(TARGET/"prepare.py", "testing_placement_producer")
    capsules = module(ROOT/config["capsule_method"], "testing_frozen_capsule_method")
    assert capsules.known_answers() == 4
    distance_fixtures = [
        (([0, 0, 0], [10, 0, 0], [5, 3, 4], [7, 3, 4]), 5.),
        (([0, 0, 0], [10, 0, 0], [12, 3, 0], [12, 7, 0]), math.sqrt(13)),
        (([10, 0, 0], [0, 0, 0], [5, 3, 4], [5, -3, -4]), 0.),
        (([0, 0, 0], [10, 0, 0], [5, 3, 4], [5, 9, 12]), 5.),
        (([0, 0, 0], [0, 0, 0], [0, 3, 4], [0, 3, 4]), 5.),
        (([0, 0, 0], [10, 0, 0], [15, 0, 0], [20, 0, 0]), 5.),
    ]
    for args, expected in distance_fixtures:
        assert abs(segment_distance(*args)-expected) < 1e-12
    summary_controls = 0
    sample = result["screens"][1]["maximum_bore_vs_other_lower_bolts"]
    a = [p for row in placement["proposed_axes"] for p in hardware(row, True)]
    for mutate in [lambda r: r.update(count=0), lambda r: r.update(positive_bound_count=0), lambda r: r.update(all_bounds_positive=False), lambda r: r["minimum"].update(capsule_separation_lower_bound_mm=0), lambda r: r["minimum"].update(finite_axis_distance_mm=0), lambda r: r["minimum_by_lower_role"]["head"].update(first_role="shaft")]:
        bad = copy.deepcopy(sample)
        mutate(bad)
        try:
            check_summary(bad, a, a, True)
        except (AssertionError, KeyError):
            summary_controls += 1
        else:
            raise AssertionError("tampered summary accepted by independent checker")

    semantic = []
    with tempfile.TemporaryDirectory(prefix="cheap-source-", dir=OWN) as temporary:
        temp = Path(temporary)
        process = subprocess.run([sys.executable, "-B", str(TARGET/"verify.py"), "--out", str(temp/"verification")], cwd=ROOT, capture_output=True, text=True, check=False, timeout=120)
        assert process.returncode == 0, process.stderr
        fresh = read(temp/"verification/receipt.json")
        assert fresh == verification
        raw_read = Path.read_bytes
        input_path = producer.INPUTS.resolve()
        geometry_path = Path(config["current_geometry"]).resolve()
        cache_path = Path(config["current_cached_descriptors"]).resolve()
        mutations = {
            "wrong_revision": lambda c, g, k: g.update(revision="old-revision"),
            "optional_extra": lambda c, g, k: c.update(optional_2026_extra=True),
            "wrong_targets": lambda c, g, k: c["target_axis_ids"].__setitem__(0, "eoere_bolt_001"),
            "wrong_proposal_z": lambda c, g, k: c.update(proposed_Z_mm=190),
            "duplicate_geometry_axis": lambda c, g, k: g["axes"].__setitem__(0, copy.deepcopy(g["axes"][1])),
            "geometry_cache_axis_drift": lambda c, g, k: g["axes"][0]["point_xyz_mm"].__setitem__(0, 1),
            "geometry_cache_screw_drift": lambda c, g, k: g["screw_axes"][0]["origin_xyz_mm"].__setitem__(0, 1),
        }
        for name, mutate in mutations.items():
            c, g = copy.deepcopy(config), copy.deepcopy(current)
            mutate(c, g, None)
            geometry_raw = producer.encode(g)
            c["sources"][config["current_geometry"]] = digest(geometry_raw)
            config_raw = producer.encode(c)
            expected_sha = producer.INPUT_SHA
            producer.INPUT_SHA = digest(config_raw)
            def virtual_read(path):
                if path.resolve() == input_path:
                    return config_raw
                if path.resolve() == geometry_path:
                    return geometry_raw
                return raw_read(path)
            output = temp/name
            try:
                with patch.object(Path, "read_bytes", virtual_read):
                    producer.build(producer.INPUTS, output)
            except ValueError as error:
                assert not any(output.iterdir()), (name, str(error))
                semantic.append({"name": name, "rejection": str(error)})
            else:
                raise AssertionError("source-only semantic fixture accepted: "+name)
            finally:
                producer.INPUT_SHA = expected_sha
        assert cache_path.exists()  # The current cache was authenticated, never edited.
        # Occupied output is rejected before input reads or capsule work.
        occupied = temp/"occupied"
        occupied.mkdir()
        marker = occupied/"keep"
        marker.write_bytes(b"keep\n")
        with patch.object(Path, "read_bytes", lambda p: (_ for _ in ()).throw(AssertionError("read reached after occupied output"))):
            try:
                producer.build(producer.INPUTS, occupied)
            except FileExistsError:
                pass
            else:
                raise AssertionError("occupied output accepted")
        assert marker.read_bytes() == b"keep\n"
        ruff = subprocess.run([str(ROOT/".venv/bin/ruff"), "check", "--no-cache", str(TARGET/"prepare.py"), str(TARGET/"verify.py")], cwd=ROOT, capture_output=True, text=True, check=False)
        assert ruff.returncode == 0, ruff.stdout+ruff.stderr
    assert {n: sha(TARGET/n) for n in EXPECTED} == EXPECTED
    for path, expected in verification["source_sha256"].items():
        assert sha(ROOT/path) == expected, path
    assert not any(k in sys.modules for k in ("cadquery", "OCP"))
    receipt = {
        "schema": "eoere_current_Z180_independent_testing_review/v1", "passed": True, "substantial_findings": [],
        "target": {"path": str(TARGET.relative_to(ROOT)), "sha256": EXPECTED}, "reviewer_sha256": sha(__file__),
        "sources": {"producer_direct_pin_count": 13, "verifier_bound_pin_count": len(verification["source_sha256"]), "authenticated_before_and_after": True, "recursive_581_or343_source_admission": False},
        "identity": {"current_geometry_matches_current_v3_axes_and_screws": True, "cache_exact_100_axes_66_screws": True, "four_only_Z200_to180_changes": True, "current_fixed_axes_unchanged": 96, "all_current_screws_unchanged": 66, "four_canonical_maps_checked": True},
        "independent_scalar_capsules": {"all_comparisons": count, "maximum_summary_witness_gap_error_mm": max_error, "screens": independent_screens, "six_scalar_distance_fixtures": True, "four_preserved_capsule_fixtures_rerun": True, "tampered_summary_controls": summary_controls},
        "source_semantic_controls": semantic, "controls_are_in_memory_repin_interpositions_not_live_source_edits": True,
        "producer_verification_reused_and_rerun": {"exact_receipt_replay": True, "seven_controls": fresh["controls"], "general_3D_segment_comparisons": 40752},
        "occupied_output_rejected_before_reads": True, "ruff_frozen_helpers_no_cache": True,
        "target_and_all_verifier_bound_bytes_unchanged": True, "release": result["release"],
        "limits": ["A source-only four-axis placement proposal is preserved; no model adoption or finished solid reconstruction was performed.", "Capsules contain declared nominal hardware/bore/screw envelopes; positive gaps prove their separation, negative bounds are inconclusive. Delivered dimensions and uncertainty are unverified.", "New bore material, eight seats, changed cuts/screw backing, tool/removal paths, current loads/actions and full joint resistance remain open.", "No recursive source closure, CAD/BREP/K/frame/native/browser work, genuine force-field consumption, model edits, shared writes, staging or commits occurred. Four current drilling holds remain."],
    }
    with (OWN/"receipt.json").open("x") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"passed": True, "findings": 0, "receipt_sha256": sha(OWN/"receipt.json")}))


if __name__ == "__main__":
    main()
