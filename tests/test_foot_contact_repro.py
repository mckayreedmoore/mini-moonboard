import hashlib
import json
import math
import tarfile
from pathlib import Path

import pytest

from fea.floor_contact import FACES, integrated_weights, mesh
from fea.foot_contact_repro import EDGES, audit, coupon_deck, extract, geometry_audit


def frozen_example():
    lines = ["*NODE"]
    nodes, elements = {}, {}
    for element, (x, y) in enumerate(((-100, 2000), (100, 2000), (0, 0)), 1):
        corners = [(x, y, 0), (x+10, y, 0), (x, y+10, 0), (x, y, 100)]
        points = corners+[tuple((corners[a][i]+corners[b][i])/2 for i in range(3)) for a, b in EDGES]
        ids = tuple(range(element*10, element*10+10))
        nodes.update(zip(ids, points, strict=True))
        elements[element] = ids
    lines += [f"{n},"+",".join(map(str, xyz)) for n, xyz in nodes.items()]
    for element, ids in elements.items():
        lines += [f"*ELEMENT,TYPE=C3D10,ELSET=Volume{element}", f"{element},"+",".join(map(str, ids))]
    return "\n".join(lines)


def test_extract_preserves_actual_volume_and_contact_geometry():
    nodes, elements, groups, volume = extract(frozen_example())
    assert volume == "VOLUME1"
    assert set(elements) == {1}
    assert set(nodes) == set(range(10, 20))
    assert groups == {"LEFT": [(1, 1)]}
    assert geometry_audit(nodes, elements, groups) == {"max_midside_offset_mm": 0., "minimum_outward_down_cosine": 1.}
    with pytest.raises(ValueError, match="outward normal"):
        geometry_audit(nodes, elements, {"LEFT": [(1, 2)]})


def test_coupon_explicitly_guides_upper_xy_but_leaves_z_free():
    nodes, elements, groups, _ = extract(frozen_example())
    text, ground, top = coupon_deck(nodes, elements, groups)
    assert "TOP,1,2,0" in text
    assert "TOP,3" not in text
    assert "*NODE PRINT,NSET=TOP\nRF" in text
    assert "NOT FREE BOARD" in text
    assert len(top) >= 3
    assert len(ground["LEFT"]) == 8


def test_partial_or_nonfinite_output_cannot_pass_coupon_audit():
    nodes, elements, groups, _ = extract(frozen_example())
    _, ground, top = coupon_deck(nodes, elements, groups)
    with pytest.raises(ValueError, match="Incomplete"):
        audit("", nodes, ground, top, dict.fromkeys(nodes, 1.))
    with pytest.raises(ValueError, match="Nonfinite"):
        audit("displacements for set WOODN and time 1.0\n10 NaN 0 0\n", nodes, ground, top, dict.fromkeys(nodes, 1.))


@pytest.mark.parametrize("weights", [{}, {10: float("nan")}, {n: -1. for n in range(10, 20)}, {n: float("nan") for n in range(10, 20)}])
def test_invalid_gravity_context_is_rejected_before_output(weights):
    nodes, elements, groups, _ = extract(frozen_example())
    _, ground, top = coupon_deck(nodes, elements, groups)
    with pytest.raises(ValueError, match="gravity context"):
        audit("", nodes, ground, top, weights)


def balanced_coupon():
    """Two-node force/moment fixture, not a physical finite-element solve."""
    nodes = {1: (0., 0., 1.), 2: (0., 0., 2.)}
    ground = {"LEFT": {3: (-1., 0., 0.), 4: (1., 0., 0.)}}
    weights = {1: 1e6, 2: 1e6}
    weight = sum(weights.values()) * 6e-10 * 9806.65
    chunks = []
    for time, load in ((1., 0.), (2., 1200.)):
        chunks.append(
            f"displacements for set WOODN and time {time}\n1 0 0 0\n2 0 0 0\n\n"
            f"forces for set TOP and time {time}\n2 0 0 0\n\n"
            f"forces for set GROUND_LEFT and time {time}\n"
            f"3 0 0 {(weight+load)/2!r}\n4 0 0 {(weight+load)/2!r}\n\n"
        )
    return "".join(chunks), nodes, ground, [2], weights


def test_complete_balanced_endpoints_pass_with_explicit_conditional_support():
    result = audit(*balanced_coupon())
    assert [step["time"] for step in result] == [1., 2.]
    assert [step["downward_upper_load_n"] for step in result] == [0., 1200.]
    for step in result:
        assert step["force_residual_n"] == pytest.approx([0., 0., 0.], abs=1e-10)
        assert step["moment_residual_nmm"] == pytest.approx([0., 0., 0.], abs=1e-10)
        assert step["upper_guide_resultant_n"] == [0., 0., 0.]


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
@pytest.mark.parametrize("location", ["wood", "ground"])
def test_nonfinite_coordinate_context_cannot_pass(value, location):
    data, nodes, ground, top, weights = balanced_coupon()
    if location == "wood":
        nodes[1] = (value, 0., 1.)
    else:
        ground["LEFT"][3] = (value, 0., 0.)
    with pytest.raises(ValueError):
        audit(data, nodes, ground, top, weights)


def test_finite_inputs_with_overflowed_deformed_position_cannot_pass():
    data, nodes, ground, top, weights = balanced_coupon()
    nodes[1] = (1.7e308, 0., 1.)
    data = data.replace("1 0 0 0", "1 1.7e308 0 0")
    with pytest.raises(ValueError):
        audit(data, nodes, ground, top, weights)


@pytest.mark.parametrize("top", [[], [2, 2], [999]])
def test_invalid_upper_patch_cannot_pass(top):
    data, nodes, ground, _, weights = balanced_coupon()
    with pytest.raises(ValueError):
        audit(data, nodes, ground, top, weights)


@pytest.mark.parametrize("pure_moment", [False, True])
def test_force_and_pure_moment_imbalance_cannot_pass(pure_moment):
    data, nodes, ground, top, weights = balanced_coupon()
    gravity_half = sum(weights.values()) * 6e-10 * 9806.65 / 2
    data = data.replace(f"3 0 0 {gravity_half!r}", f"3 0 0 {gravity_half+2!r}")
    if pure_moment:
        data = data.replace(f"4 0 0 {gravity_half!r}", f"4 0 0 {gravity_half-2!r}")
    with pytest.raises(ValueError, match="Equilibrium"):
        audit(data, nodes, ground, top, weights)


def test_missing_second_endpoint_and_duplicate_output_cannot_pass():
    data, nodes, ground, top, weights = balanced_coupon()
    partial = data.split("displacements for set WOODN and time 2.0")[0]
    with pytest.raises(ValueError, match="Incomplete"):
        audit(partial, nodes, ground, top, weights)
    with pytest.raises(ValueError, match="Duplicate"):
        audit(data + partial, nodes, ground, top, weights)


EVIDENCE = Path("fea/results/foot_contact_diagnosis/actual_leg")


def published_coupon():
    record = json.loads((EVIDENCE / "actual_leg.json").read_text())
    with tarfile.open(EVIDENCE / "solver_evidence.tar.gz", "r:gz") as archive:
        raw = {Path(member.name).name: archive.extractfile(member).read()
               for member in archive.getmembers() if member.isfile()}
    for name, expected in record["evidence_sha256"].items():
        assert hashlib.sha256(raw[name]).hexdigest() == expected
    launch = EVIDENCE / "foot_contact_repro.launch.py"
    assert hashlib.sha256(launch.read_bytes()).hexdigest() == record["run_source_sha256"]["/work/fea/foot_contact_repro.py"]
    all_nodes, elements = mesh(raw["actual_leg.inp"].decode())
    used = {n for ids in elements.values() for n in ids}
    nodes = {n: xyz for n, xyz in all_nodes.items() if n in used}
    groups = {"LEFT": [(e, face) for e, ids in elements.items()
                       for face, indices in enumerate(FACES, 1)
                       if all(abs(nodes[ids[i]][2]) < 1e-5 for i in indices)]}
    expected, ground, top = coupon_deck(nodes, elements, groups)
    # Wood coordinates were rounded to 12 significant figures in the launch
    # deck; ground coordinates retained their original precision. Verify the
    # resulting tiny reconstruction difference before restoring that precision.
    for n, xyz in ground["LEFT"].items():
        assert xyz == pytest.approx(all_nodes[n], abs=1e-7, rel=0)
        old = f"{n}," + ",".join(map(str, xyz))
        new = next(line for line in raw["actual_leg.inp"].decode().splitlines()
                   if line.startswith(f"{n},"))
        expected = expected.replace(old + "\n", new + "\n")
        ground["LEFT"][n] = all_nodes[n]
    assert expected.encode() == raw["actual_leg.inp"]
    assert hashlib.sha256(expected.encode()).hexdigest() == record["deck_sha256"]
    assert record["status"] == "TWO COMPLETE EQUILIBRIUM-AUDITED CONDITIONAL COUPON STEPS; LOCAL CONTACT AUDIT STILL REQUIRED"
    return record, raw, nodes, elements, ground, top


def test_published_raw_hashes_and_exact_intended_guided_deck():
    published_coupon()


def test_published_raw_equilibrium_replay_when_gmsh_is_available():
    pytest.importorskip("gmsh", reason="Replay quadrature requires the pinned FEA Docker environment")
    record, raw, nodes, elements, ground, top = published_coupon()
    weights = integrated_weights(elements, nodes)
    result = audit(raw["actual_leg.dat"].decode(), nodes, ground, top, weights)
    assert sum(weights.values()) * 6e-7 == pytest.approx(record["mass_kg"], abs=1e-8)
    for step, expected in zip(result, record["audited_steps"], strict=True):
        for key in ("force_residual_n", "moment_residual_nmm", "floor_resultant_n", "upper_guide_resultant_n"):
            assert step[key] == pytest.approx(expected[key], abs=2e-5)
        assert step["max_displacement_mm"] == pytest.approx(expected["max_displacement_mm"])
