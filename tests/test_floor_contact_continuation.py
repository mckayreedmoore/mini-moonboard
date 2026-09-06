import hashlib
import json
import re
import tarfile
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from fea.floor_contact import FACES, deck, floor_faces, mesh
from fea.floor_contact_continuation import audit_three, continuation_deck
from fea.floor_contact_results import blocks, cross


@pytest.mark.parametrize("fraction", [.1, .05])
def test_only_free_and_loaded_steps_are_refined_after_full_preload(fraction):
    base = "*BOUNDARY\nGROUND_LEFT,1,3,0\n" + 2 * (
        "*STEP,NLGEOM,INC=200\n*STATIC\n0.05,1,1e-6,0.1\n*END STEP\n"
    )
    original = continuation_deck(base, {"LEFT": []}, [1], True)
    result = continuation_deck(base, {"LEFT": []}, [1], free_increment=fraction)
    _, preload, released, loaded = result.split("*STEP,NLGEOM,INC=200\n")
    assert "*STATIC\n1,1,1e-6,1\n" in preload
    assert released.startswith("*BOUNDARY,OP=NEW\nGROUND_LEFT,1,3,0\n")
    refined = f"*STATIC\n{fraction!r},1,1e-6,{fraction!r}\n"
    assert refined in released and refined in loaded
    assert result.replace(refined, "*STATIC\n1,1,1e-6,1\n") == original


@pytest.mark.parametrize("fraction", [float("nan"), float("inf"), 0., -.1, 1.1, .001, 1e-7])
def test_invalid_free_increment_is_rejected(fraction):
    with pytest.raises(ValueError, match="Free increment"):
        continuation_deck("", {}, [], free_increment=fraction)


def test_refined_and_full_increment_modes_are_exclusive():
    with pytest.raises(ValueError, match="Free increment"):
        continuation_deck("", {}, [], True, .1)


def test_full_increment_sensitivity_changes_only_static_step_sizes():
    base = "*BOUNDARY\nGROUND_LEFT,1,3,0\n" + 2 * (
        "*STEP,NLGEOM,INC=200\n*STATIC\n0.05,1,1e-6,0.1\n*END STEP\n"
    )
    original = continuation_deck(base, {"LEFT": []}, [1])
    larger = continuation_deck(base, {"LEFT": []}, [1], True)
    assert larger.count("*STATIC\n1,1,1e-6,1\n") == 3
    assert larger.replace("*STATIC\n1,1,1e-6,1\n", "*STATIC\n0.05,1,1e-6,0.1\n") == original


def test_full_release_precedes_free_gravity_and_original_load():
    base = "*BOUNDARY\nGROUND_LEFT,1,3,0\n*STEP,NLGEOM,INC=200\n*STATIC\n0.05,1,1e-6,0.1\n*DLOAD\nTIMBER,GRAV,9806.65,0,0,-1\n*END STEP\n*STEP,NLGEOM,INC=200\n*STATIC\n0.05,1,1e-6,0.1\n*CLOAD\n1,3,-1200\n*END STEP\n"
    text = continuation_deck(base, {"LEFT": []}, [1, 2, 3])
    model, guided, released, loaded = text.split("*STEP,NLGEOM,INC=200\n")
    assert "PRELOAD_GUIDE,1,2,0" in model
    assert released.startswith("*BOUNDARY,OP=NEW\nGROUND_LEFT,1,3,0\n*STATIC\n")
    assert "*DLOAD\nTIMBER,GRAV" in guided and "*DLOAD\nTIMBER,GRAV" in released
    assert "*CLOAD" not in guided+released
    assert "1,3,-1200" in loaded
    assert "PRELOAD_GUIDE,1" not in released+loaded
    assert "*CONTROLS" not in text
    assert text.count("*CONTACT PRINT\nCDIS,CSTR") == 3


def test_missing_final_steps_and_invalid_weights_fail_closed():
    nodes, elements, groups, record, _ = equilibrium_fixture()
    record["nodal_volume_mm3"][1] = float("nan")
    with pytest.raises(ValueError, match="Invalid gravity context"):
        audit_three("", nodes, elements, groups, record)
    record["nodal_volume_mm3"][1] = 1.
    with pytest.raises(ValueError, match="Incomplete accepted endpoint"):
        audit_three("", nodes, elements, groups, record)


def equilibrium_fixture():
    # Deliberately tiny algebraic output fixture, not a solver/mesh validation.
    nodes = {1: (0., 0., 0.), 2: (0., 0., 0.)}
    elements = {1: (1, 2, 1, 2, 1, 2, 1, 2, 1, 2)}
    groups = {"LEFT": [(1, 1)]}
    record = {
        "nodal_volume_mm3": {1: 1., 2: 1.}, "guide_nodes": [1, 2],
        "ground_nodes": {"LEFT": {11: (0., 0., 0.), 12: (1., 0., 0.)}},
        "load_nodes": [1], "mu": .3,
    }
    rows = {}
    for endpoint in (1., 2., 3.):
        rows[("displacements", "WOODN", endpoint)] = {1: (0., 0., 0.), 2: (0., 0., 0.)}
        rows[("forces", "PRELOAD_GUIDE", endpoint)] = {1: (0., 0., 0.), 2: (0., 0., 0.)}
        rows[("forces", "GROUND_LEFT", endpoint)] = {
            11: (0., 0., 2*6e-10*9806.65+(1200. if endpoint == 3. else 0.)),
            12: (0., 0., 0.),
        }
    return nodes, elements, groups, record, rows


def output_text(rows):
    return "\n".join(
        f"{kind} for set {name} and time {endpoint}\n"+
        "\n".join(f"{node} "+" ".join(map(str, xyz)) for node, xyz in values.items())+"\n"
        for (kind, name, endpoint), values in rows.items()
    )


def test_complete_three_step_equilibrium_is_accepted():
    nodes, elements, groups, record, rows = equilibrium_fixture()
    result = audit_three(output_text(rows), nodes, elements, groups, record)
    assert [step["time"] for step in result] == [1., 2., 3.]
    assert [step["temporary_guides_active"] for step in result] == [True, False, False]
    assert [step["load_n"] for step in result] == [0., 0., 1200.]
    assert all(max(map(abs, step["force_residual_n"])) < 1e-9 for step in result)
    assert all(max(map(abs, step["moment_residual_nmm"])) < 1e-9 for step in result)


def test_guided_preload_reactions_are_included_only_in_first_step():
    nodes, elements, groups, record, rows = equilibrium_fixture()
    record["nodal_volume_mm3"] = {1: 1e6, 2: 1e6}
    weight = 2e6*6e-10*9806.65
    for endpoint in (1., 2., 3.):
        rows[("forces", "GROUND_LEFT", endpoint)][11] = (
            -1. if endpoint == 1. else 0., 0., weight+(1200. if endpoint == 3. else 0.)
        )
    rows[("forces", "PRELOAD_GUIDE", 1.)][1] = (1., 0., 0.)
    result = audit_three(output_text(rows), nodes, elements, groups, record)
    assert [step["guide_lateral_resultant_n"] for step in result] == [[1., 0.], [0., 0.], [0., 0.]]


@pytest.mark.parametrize("mu", [0., -1., 1.01, float("nan"), float("inf")])
def test_invalid_friction_context_fails(mu):
    nodes, elements, groups, record, rows = equilibrium_fixture()
    record["mu"] = mu
    with pytest.raises(ValueError, match="friction"):
        audit_three(output_text(rows), nodes, elements, groups, record)


def test_aggregate_friction_uses_recorded_sensitivity_value():
    nodes, elements, groups, record, rows = equilibrium_fixture()
    record["nodal_volume_mm3"] = {1: 1e6, 2: 1e6}
    weight = 2e6*6e-10*9806.65
    for endpoint in (1., 2., 3.):
        rows[("forces", "GROUND_LEFT", endpoint)][11] = (
            -4. if endpoint == 1. else 0., 0., weight+(1200. if endpoint == 3. else 0.)
        )
    rows[("forces", "PRELOAD_GUIDE", 1.)][1] = (4., 0., 0.)
    with pytest.raises(ValueError, match="compression/friction"):
        audit_three(output_text(rows), nodes, elements, groups, record)
    record["mu"] = .5
    assert len(audit_three(output_text(rows), nodes, elements, groups, record)) == 3


def deformed_equilibrium_fixture(*, undeformed_balance=False):
    nodes, elements, groups, record, rows = equilibrium_fixture()
    nodes.update({1: (2., 0., 1.), 2: (4., 0., 2.)})
    record["nodal_volume_mm3"] = {1: 1e6, 2: 1e6}
    record["ground_nodes"]["LEFT"][12] = (10., 0., 0.)
    nodal_weight = 1e6*6e-10*9806.65
    for endpoint in (1., 2., 3.):
        # The first step's XY guides allow only Z motion; subsequent steps
        # translate laterally after release. This remains an algebraic fixture.
        shift = 0. if endpoint == 1. else 1.
        u = {1: (shift, 0., 0.), 2: (shift, 0., 2.)}
        rows[("displacements", "WOODN", endpoint)] = u
        positions = nodes if undeformed_balance else {
            n: tuple(a+b for a, b in zip(xyz, u[n], strict=True))
            for n, xyz in nodes.items()
        }
        lateral = 2. if endpoint == 1. else 0.
        load = 1200. if endpoint == 3. else 0.
        rows[("forces", "PRELOAD_GUIDE", endpoint)][2] = (lateral, 0., 0.)
        # Nonzero gravity, applied-load, and guide moments balance the two
        # ground reactions in the deformed configuration, about the origin.
        applied_moment_y = (
            sum(p[0]*nodal_weight for p in positions.values())
            + positions[1][0]*load + positions[2][2]*lateral
        )
        right_normal = applied_moment_y/10.
        rows[("forces", "GROUND_LEFT", endpoint)] = {
            11: (-lateral, 0., 2*nodal_weight+load-right_normal),
            12: (0., 0., right_normal),
        }
    return nodes, elements, groups, record, rows


def test_translated_deformed_equilibrium_includes_all_applied_moments():
    nodes, elements, groups, record, rows = deformed_equilibrium_fixture()
    result = audit_three(output_text(rows), nodes, elements, groups, record)
    for step in result:
        assert step["force_residual_n"] == pytest.approx([0., 0., 0.], abs=1e-9)
        assert step["moment_residual_nmm"] == pytest.approx([0., 0., 0.], abs=1e-9)


def test_undeformed_balance_cannot_pass_deformed_equilibrium():
    nodes, elements, groups, record, rows = deformed_equilibrium_fixture(undeformed_balance=True)
    with pytest.raises(ValueError, match="Deformed equilibrium failed"):
        audit_three(output_text(rows), nodes, elements, groups, record)


@pytest.mark.parametrize("reaction", [(0., 0., -1.), (1., 0., 0.)])
def test_tension_and_excess_aggregate_friction_fail(reaction):
    nodes, elements, groups, record, rows = equilibrium_fixture()
    rows[("forces", "GROUND_LEFT", 1.)][11] = reaction
    with pytest.raises(ValueError, match="compression/friction"):
        audit_three(output_text(rows), nodes, elements, groups, record)


@pytest.mark.parametrize("endpoint", [1., 2., 3.])
@pytest.mark.parametrize("kind,name", [("displacements", "WOODN"), ("forces", "PRELOAD_GUIDE"), ("forces", "GROUND_LEFT")])
def test_each_endpoint_requires_every_node_output(endpoint, kind, name):
    nodes, elements, groups, record, rows = equilibrium_fixture()
    rows[(kind, name, endpoint)].pop(next(iter(rows[(kind, name, endpoint)])))
    with pytest.raises(ValueError):
        audit_three(output_text(rows), nodes, elements, groups, record)


@pytest.mark.parametrize("endpoint", [2., 3.])
def test_released_guide_forces_cannot_cancel_each_other(endpoint):
    nodes, elements, groups, record, rows = equilibrium_fixture()
    rows[("forces", "PRELOAD_GUIDE", endpoint)] = {1: (1., 0., 0.), 2: (-1., 0., 0.)}
    with pytest.raises(ValueError, match="guide"):
        audit_three(output_text(rows), nodes, elements, groups, record)


@pytest.mark.parametrize("pure_moment", [False, True])
def test_force_and_pure_moment_imbalances_fail(pure_moment):
    nodes, elements, groups, record, rows = equilibrium_fixture()
    reactions = rows[("forces", "GROUND_LEFT", 3.)]
    reactions[12] = (0., 0., 2.)
    if pure_moment:
        reactions[11] = (0., 0., reactions[11][2]-2.)
    with pytest.raises(ValueError, match="equilibrium"):
        audit_three(output_text(rows), nodes, elements, groups, record)


@pytest.mark.parametrize("field", ["load_nodes", "guide_nodes"])
@pytest.mark.parametrize("values", [[], [1, 1], [999]])
def test_empty_duplicate_and_unknown_node_contexts_fail(field, values):
    nodes, elements, groups, record, rows = equilibrium_fixture()
    record[field] = values
    if field == "load_nodes" and not values:
        # Without validation this gravity-only solve claims a 1,200 N endpoint.
        rows[("forces", "GROUND_LEFT", 3.)][11] = (0., 0., 2*6e-10*9806.65)
    with pytest.raises(ValueError):
        audit_three(output_text(rows), nodes, elements, groups, record)


@pytest.mark.parametrize("location", ["wood", "ground"])
@pytest.mark.parametrize("xyz", [(0., float("nan"), 0.), (0., float("inf"), 0.), (0., 0.), (0., 0., 0., 0.)])
def test_nonfinite_or_malformed_coordinates_fail(location, xyz):
    nodes, elements, groups, record, rows = equilibrium_fixture()
    if location == "wood":
        nodes[1] = xyz
    else:
        record["ground_nodes"]["LEFT"][11] = xyz
    with pytest.raises(ValueError):
        audit_three(output_text(rows), nodes, elements, groups, record)


def test_finite_inputs_whose_moments_overflow_fail():
    nodes, elements, groups, record, rows = equilibrium_fixture()
    record["ground_nodes"]["LEFT"][11] = (1e308, 0., 0.)
    with pytest.raises(ValueError):
        audit_three(output_text(rows), nodes, elements, groups, record)


@pytest.mark.parametrize("mapping", [{}, {"RIGHT": {11: (0., 0., 0.)}}, {"LEFT": {}}])
def test_ground_patch_context_must_match_contact_groups(mapping):
    nodes, elements, groups, record, rows = equilibrium_fixture()
    record["ground_nodes"] = deepcopy(mapping)
    with pytest.raises(ValueError):
        audit_three(output_text(rows), nodes, elements, groups, record)


def assert_complete_replay(data, nodes, elements, groups, record):
    if "audit_error" in record:
        with pytest.raises(ValueError) as error:
            audit_three(data, nodes, elements, groups, record)
        # Rounded archived coordinates can slightly alter the numeric residual;
        # the failed gate and endpoint must still be identical.
        assert str(error.value).split(":", 1)[0] == record["audit_error"].split(":", 1)[0]
        assert "audited_steps" not in record
        return
    result = audit_three(data, nodes, elements, groups, record)
    for actual, expected in zip(result, record["audited_steps"], strict=True):
        assert actual.keys() == expected.keys()
        for key in ("time", "temporary_guides_active", "load_n"):
            assert actual[key] == expected[key]
        for key in ("force_residual_n", "moment_residual_nmm", "guide_lateral_resultant_n"):
            assert actual[key] == pytest.approx(expected[key], abs=2e-5, rel=0)
        assert actual["patches"].keys() == expected["patches"].keys()
        for name, patch in actual["patches"].items():
            assert patch.keys() == expected["patches"][name].keys()
            for key, values in patch.items():
                assert values == pytest.approx(expected["patches"][name][key], abs=2e-5, rel=0)


def test_complete_replay_allows_only_bounded_numeric_rounding():
    nodes, elements, groups, record, rows = deformed_equilibrium_fixture()
    data = output_text(rows)
    record["audited_steps"] = audit_three(data, nodes, elements, groups, record)
    record["audited_steps"][0]["moment_residual_nmm"][0] += 1e-5
    assert_complete_replay(data, nodes, elements, groups, record)
    record["audited_steps"][0]["moment_residual_nmm"][0] += 1e-3
    with pytest.raises(AssertionError):
        assert_complete_replay(data, nodes, elements, groups, record)


def test_solver_complete_but_rejected_replay_requires_same_gate_and_endpoint():
    nodes, elements, groups, record, rows = deformed_equilibrium_fixture(undeformed_balance=True)
    data = output_text(rows)
    with pytest.raises(ValueError) as error:
        audit_three(data, nodes, elements, groups, record)
    record["audit_error"] = str(error.value)
    assert_complete_replay(data, nodes, elements, groups, record)
    record["audit_error"] = "Deformed equilibrium failed at 2.0: different endpoint"
    with pytest.raises(AssertionError):
        assert_complete_replay(data, nodes, elements, groups, record)
    record["audit_error"] = "Necessary aggregate compression/friction bound failed"
    with pytest.raises(AssertionError):
        assert_complete_replay(data, nodes, elements, groups, record)


@pytest.mark.parametrize("report_path", sorted(Path("fea/results/floor_contact_continuation").glob("*/report.json")), ids=lambda p: p.parent.name)
def test_published_continuation_evidence_replays_without_generated_inputs(report_path):
    report = json.loads(report_path.read_text())
    archive_path = report_path.parent/report["archive"]
    assert archive_path.stat().st_size == report["archive_bytes"]
    assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == report["archive_sha256"]
    # Read named regular files in memory; do not extract paths from the archive.
    with tarfile.open(archive_path, "r:gz") as archive:
        members = archive.getmembers()
        assert all(member.isfile() and Path(member.name).name == member.name for member in members)
        assert len({member.name for member in members}) == len(members)
        assert {member.name for member in members} == set(report["archive_contents"])
        raw = {member.name: archive.extractfile(member).read() for member in members}
    record = json.loads(raw["continuation.json"])
    for name, digest in record["output_sha256"].items():
        assert hashlib.sha256(raw[name]).hexdigest() == digest
    assert set(record["output_sha256"]) == {"continuation.dat", "continuation.log", "continuation.sta", "continuation.cvg", "continuation.frd"}
    assert hashlib.sha256(raw["continuation.inp"]).hexdigest() == record["deck_sha256"] == report["deck_sha256"]
    launch_name = "floor_contact_continuation.launch.py"
    assert raw[launch_name] == (report_path.parent/launch_name).read_bytes()
    launch_digest = hashlib.sha256(raw[launch_name]).hexdigest()
    assert launch_digest == report["launch_source_sha256"]
    assert [digest for name, digest in record["prelaunch_sha256"].items()
            if Path(name).name == "floor_contact_continuation.py"] == [launch_digest]
    assert record["prelaunch_sha256"][record["source"]] == record["source_sha256"] == report["source_sha256"]

    text = raw["continuation.inp"].decode()
    all_nodes, elements = mesh(text)
    used = {node for ids in elements.values() for node in ids}
    nodes = {node: xyz for node, xyz in all_nodes.items() if node in used}
    groups = floor_faces(nodes, elements)
    feet = sorted({elements[element][i] for faces in groups.values()
                   for element, face in faces for i in FACES[face-1]})
    assert feet == record["guide_nodes"]
    assert len(nodes) == 62020 and len(elements) == 32511
    assert {name: len(faces) for name, faces in groups.items()} == {"LEFT": 16, "RIGHT": 16, "KICKER": 213}
    baseline, ground = deck(nodes, elements, groups, record["load_nodes"], record["mu"], record["normal_penalty_n_mm3"])
    # The launch rounded wood coordinates to 12 significant figures but wrote
    # ground coordinates at full precision. Restore only that bounded rounding.
    lines = {int(line.split(",")[0]): line for line in text.splitlines()
             if line.split(",")[0].isdigit() and len(line.split(",")) == 4}
    for name, coordinates in ground.items():
        assert set(map(int, record["ground_nodes"][name])) == coordinates.keys()
        for node, xyz in coordinates.items():
            assert xyz == pytest.approx(all_nodes[node], abs=1e-7, rel=0)
            assert record["ground_nodes"][name][str(node)] == list(all_nodes[node])
            baseline = baseline.replace(f"{node},"+",".join(map(str, xyz))+"\n", lines[node]+"\n")
    assert hashlib.sha256(baseline.encode()).hexdigest() == record["baseline_deck_sha256"]
    assert continuation_deck(
        baseline, groups, feet, record.get("full_increment", False), record.get("free_increment")
    ) == text

    fields = ("step", "increment", "attempt", "iterations", "total_time", "step_time", "increment_time")
    accepted = []
    for line in raw["continuation.sta"].decode().splitlines():
        cells = line.split()
        if len(cells) == 7 and all(cell.isdigit() for cell in cells[:4]):
            accepted.append(dict(zip(fields, [*map(int, cells[:4]), *map(float, cells[4:])], strict=True)))
    assert accepted == report["accepted_partial_increments"]
    assert report["last_accepted_total_time"] == (accepted[-1]["total_time"] if accepted else 0.)
    complete = {row["step"] for row in accepted if row["step_time"] == 1.}
    assert report["complete_steps"] == len(complete)
    assert report["free_gravity_reached"] == any(row["step"] == 2 for row in accepted)
    assert report["climber_load_reached"] == any(row["step"] == 3 for row in accepted)
    for field, endpoint in (("free_gravity_complete", 2), ("climber_load_complete", 3)):
        if field in report:
            assert report[field] == (endpoint in complete)
    assert report["exit_code"] == record["exit_code"]
    assert report["max_seconds"] == record["max_seconds"]
    assert report["elapsed_seconds"] == record["elapsed_seconds"]
    if record["exit_code"] == -999:
        assert "TIMEOUT" in report["status"]
        assert "UNRESOLVED" in record["status"]
        assert record["elapsed_seconds"] >= record["max_seconds"]
    parsed = blocks(raw["continuation.dat"].decode())
    for endpoint in complete:
        assert parsed[("displacements", "WOODN", float(endpoint))].keys() == nodes.keys()
        assert parsed[("forces", "PRELOAD_GUIDE", float(endpoint))].keys() == set(feet)
    if complete != {1, 2, 3}:
        assert not report["accepted_physical_solution"]
        assert "NO ACCEPTED" in report["status"] and "BOARD SOLUTION" in report["status"]
        with pytest.raises(ValueError):
            audit_three(raw["continuation.dat"].decode(), nodes, elements, groups, record)
    else:
        assert_complete_replay(raw["continuation.dat"].decode(), nodes, elements, groups, record)
        # Global equilibrium alone never proves local contact or structure.
        assert not report["accepted_physical_solution"]
    if report_path.parent.name == "free-increment0p1-mu0p5":
        assert_refined_independent_moment_claims(report_path.parent, raw, nodes, parsed, record)


def assert_refined_independent_moment_claims(directory, raw, nodes, parsed, record):
    """Replay the numerical finding, not the publisher or its narrative."""
    audit = json.loads((directory/"independent_audit.json").read_text())
    assert audit["dat_sha256"] == hashlib.sha256(raw["continuation.dat"]).hexdigest()
    assert audit["production_audit_error"] == record["audit_error"]
    assert audit["recorded_exit_code"] == record["exit_code"] == 0
    assert "NOT PHYSICAL OR STRUCTURAL ACCEPTANCE" in audit["status"]
    assert [endpoint["time"] for endpoint in audit["endpoints"]] == [1., 2., 3.]
    for endpoint in audit["endpoints"][1:]:
        time = endpoint["time"]
        displacement = parsed["displacements", "WOODN", time]
        positions = {node: tuple(a+b for a, b in zip(xyz, displacement[node], strict=True))
                     for node, xyz in nodes.items()}
        external = [(positions[int(node)], (0., 0., -volume*6e-10*9806.65))
                    for node, volume in record["nodal_volume_mm3"].items()]
        load = 1200. if time == 3. else 0.
        external += [(positions[node], (0., 0., -load/len(record["load_nodes"])))
                     for node in record["load_nodes"]]
        for name, coordinates in record["ground_nodes"].items():
            external += [(coordinates[str(node)], force)
                         for node, force in parsed["forces", "GROUND_"+name, time].items()]
        force = [sum(v[axis] for _, v in external) for axis in range(3)]
        moment = [sum(cross(point, v)[axis] for point, v in external) for axis in range(3)]
        assert force == pytest.approx(endpoint["force_residual_n"], abs=1e-9, rel=0)
        assert moment == pytest.approx(endpoint["ground_moment_residual_nmm"], abs=1e-7, rel=0)
        assert endpoint["global_equilibrium_pass"] == (max(map(abs, force)) <= .1 and max(map(abs, moment)) <= 1.)
        assert endpoint["global_equilibrium_pass"] == (time == 2.)

    data = raw["continuation.dat"].decode()
    # The deck fixes output order to CF, CFN, CFS. Read the first of the three
    # loaded-kicker result rows and independently propagate printed precision.
    statistics = re.findall(
        r"statistics for slave set SLAVE_KICKER, master set MASTER_KICKER and time\s+(\S+)\s+"
        r"total surface force[^\n]*\n\s*([^\n]+)", data
    )
    loaded = [row.split() for time, row in statistics if float(time) == 3.]
    assert len(loaded) == 3 and all(len(row) == 6 for row in loaded)
    cf_mx = float(loaded[0][3])
    coordinates = record["ground_nodes"]["KICKER"]
    rf = parsed["forces", "GROUND_KICKER", 3.]
    rf_mx = sum(cross(coordinates[str(node)], vector)[0] for node, vector in rf.items())
    patch = audit["endpoints"][2]["patches"]["KICKER"]
    assert cf_mx-rf_mx == pytest.approx(patch["cf_minus_rf_moment_nmm"][0], abs=1e-8, rel=0)
    force_blocks = re.findall(r"forces[^\n]*for set GROUND_KICKER and time\s+(\S+)\n(.*?)(?=\n\s*[A-Za-z]|\Z)", data, re.DOTALL)
    bodies = [body for time, body in force_blocks if float(time) == 3.]
    assert len(bodies) == 1
    rows = [line.split() for line in bodies[0].splitlines() if len(line.split()) == 4]
    assert {int(row[0]) for row in rows} == rf.keys()
    half_quantum = lambda token: .5*10**Decimal(token).as_tuple().exponent
    tolerance = half_quantum(loaded[0][3])+sum(
        abs(coordinates[row[0]][1])*half_quantum(row[3])+
        abs(coordinates[row[0]][2])*half_quantum(row[2]) for row in rows
    )
    assert tolerance == pytest.approx(patch["cf_minus_rf_moment_print_tolerance_nmm"][0], abs=1e-12, rel=0)
    assert abs(cf_mx-rf_mx) > 1000*tolerance
