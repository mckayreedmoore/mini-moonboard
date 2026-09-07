"""Archived fixture DAT plus explicitly synthetic section output; no new solve."""
import copy
import hashlib
import re
import tarfile

import pytest

from fea import independent_leg_response as profile
from fea import leg_section_response as response
from fea.floor_contact_results import cross


@pytest.fixture(scope="module")
def prepared():
    return {size: response.prepare(size) for size in (40, 25)}


@pytest.fixture(scope="module")
def fixture_dat():
    with tarfile.open(response.selection.ARCHIVE) as archive:
        return archive.extractfile("independent40.dat").read().decode()


def synthetic_sections(context):
    """Invent exact equilibrium resultants, not native curved-section evidence."""
    records = []
    for time, case in enumerate(context["section_cases"], 1):
        for name, sign in (("LOWER_CUT", 1), ("UPPER_CUT", -1)):
            expected = [sign*v for v in case["expected_upper_on_lower_force_moment"]]
            force = expected[:3]
            origin = [v+d for v, d in zip(expected[3:], cross(context["section_reference"], force), strict=True)]
            records.append([name, time, [force+origin, [0., 0., 0., 0., 0., float(sign)],
                                        [0., 0., 0.], [6230.132227635516, 0., 0., 0., 0.]]])
    return records


def dat(records):
    return "".join(f"\nstatistics for surface set {name} and time {time}\n"+
                   "\n".join(" ".join(format(v, ".17g") for v in row) for row in values)+"\n"
                   for name, time, values in records)


@pytest.fixture(scope="module")
def valid(prepared, fixture_dat):
    context = prepared[40][1]
    areas = {name: 6230.132227635516 for name in ("LOWER_CUT", "UPPER_CUT")}
    return response.audit(fixture_dat+dat(synthetic_sections(context)), context, areas)


def test_only_surface_and_output_cards_change_actual_archived_decks(prepared):
    assert response.GATES == {"force_n": .001, "moment_nmm": .01, "relative_component": .01, "relative_area": .0001}
    assert profile.GATES == {"force_n": .001, "moment_nmm": .01, "fixed_displacement_mm": 1e-9,
                             "unloaded_displacement_mm": 1e-9, "relative_mesh_compliance": .05,
                             "relative_energy_work": .001, "unloaded_energy_nmm": 1e-10}
    with tarfile.open(response.selection.ARCHIVE) as archive:
        for size, (text, context) in prepared.items():
            original = archive.extractfile(f"independent{size}.inp").read().decode()
            without_surfaces = re.sub(r"\*SURFACE,NAME=(?:LOWER|UPPER)_CUT\n(?:\d+,S[1-4]\n)+", "", text)
            assert without_surfaces.replace(response.OUTPUT, "") == original
            assert text.count(response.OUTPUT) == 9 and text.count("*SURFACE,NAME=") == 2
            assert context["original_sha256"] == hashlib.sha256(original.encode()).hexdigest()
            assert context["deck_sha256"] == hashlib.sha256(text.encode()).hexdigest()
            assert context["gates"] == profile.GATES
            assert len(context["section_cases"]) == 9
            assert not any(word in text for word in ("*CONTACT", "*TIE", "NLGEOM"))
    with pytest.raises(ValueError):
        response.prepare(20)


def test_archived_fixture_with_synthetic_sections_is_unqualified(valid):
    assert valid["pass"] is True and valid["qualified_for_design"] is False
    assert valid["gates"] == response.GATES and len(valid["rows"]) == 9
    for row in valid["rows"]:
        assert row["fixture"]["pass"] is True and row["pass"] is True
        assert row["opposed_residual"] == pytest.approx([0.]*6, abs=1e-10)
        for section in row["sections"].values():
            assert section["error"] == pytest.approx([0.]*6, abs=1e-10)
            assert section["force_moment_at_reference"] == pytest.approx(section["expected"], abs=1e-10)


@pytest.mark.parametrize("damage", ["missing", "duplicate", "extra", "nonfinite", "short_row"])
def test_rejects_incomplete_or_corrupted_section_records(prepared, fixture_dat, damage):
    context = prepared[40][1]
    records = synthetic_sections(context)
    if damage == "missing":
        records.pop()
    elif damage == "duplicate":
        records.append(copy.deepcopy(records[0]))
    elif damage == "extra":
        records[-1][1] = 10
    elif damage == "nonfinite":
        records[0][2][0][1] = float("nan")
    else:
        records[0][2][0].pop()
    with pytest.raises(ValueError):
        response.audit(fixture_dat+dat(records), context, {name: 6230.132227635516 for name in ("LOWER_CUT", "UPPER_CUT")})


@pytest.mark.parametrize("damage", ["sign", "zero_area", "wrong_area", "force_error", "moment_error", "zero_reference_error"])
def test_numeric_section_failures_remain_failures(prepared, fixture_dat, damage):
    context = prepared[40][1]
    records = synthetic_sections(context)
    if damage == "sign":
        records[0][2][0] = [-v for v in records[0][2][0]]
    elif damage in ("zero_area", "wrong_area"):
        records[0][2][3][0] *= 0 if damage == "zero_area" else 1.001
    elif damage == "force_error":
        records[0][2][0][0] += .02
    elif damage == "moment_error":
        records[0][2][0][3] += .02
    else:
        # Outer-only loading leaves this inner-ply cut unloaded; absolute gate
        # must still detect errors where a relative-only comparison is undefined.
        records[-1][2][0][0] = .002
    report = response.audit(fixture_dat+dat(records), context, {name: 6230.132227635516 for name in ("LOWER_CUT", "UPPER_CUT")})
    assert report["pass"] is False and report["qualified_for_design"] is False
    assert any(not row["pass"] for row in report["rows"])


def test_fixture_equilibrium_gate_is_not_bypassed(prepared, fixture_dat):
    context = prepared[40][1]
    match = re.search(r"forces[^\n]*for set FIXED and time[^\n]*\n\s*(\d+)\s+(\S+)", fixture_dat)
    assert match
    changed = fixture_dat[:match.start(2)]+"100.0"+fixture_dat[match.end(2):]
    report = response.audit(changed+dat(synthetic_sections(context)), context,
                            {name: 6230.132227635516 for name in ("LOWER_CUT", "UPPER_CUT")})
    assert report["pass"] is False and report["rows"][0]["fixture"]["pass"] is False
    assert all(section["pass"] for section in report["rows"][0]["sections"].values())


def test_input_area_and_vector_validation(prepared):
    for areas in ({}, {"LOWER_CUT": 1., "UPPER_CUT": -1.}, {"LOWER_CUT": 1., "UPPER_CUT": float("nan")}):
        with pytest.raises(ValueError):
            response.audit("", prepared[40][1], areas)
    for vector in ([0.]*5, [0.]*5+[float("nan")]):
        with pytest.raises(ValueError):
            response.within(vector, [0.]*6)
    assert response.within([.001]*3+[.01]*3, [0.]*6)
    assert not response.within([.00101, 0., 0., 0., 0., 0.], [0.]*6)
    assert response.within([1.]*6, [100.]*6)
    assert not response.within([1.01]*6, [100.]*6)


def test_mesh_comparison_detects_difference_despite_individual_acceptance(valid):
    coarse, fine = copy.deepcopy(valid), copy.deepcopy(valid)
    assert response.compare_meshes(coarse, fine)["pass"] is True
    for report, sign in ((coarse, -1), (fine, 1)):
        for name, side in (("LOWER_CUT", 1), ("UPPER_CUT", -1)):
            section = report["rows"][0]["sections"][name]
            section["force_moment_at_reference"][0] += sign*side*.004
            error = [a-b for a, b in zip(section["force_moment_at_reference"], section["expected"], strict=True)]
            assert response.within(error, section["expected"])
    comparison = response.compare_meshes(coarse, fine)
    assert comparison["pass"] is False and comparison["qualified_for_design"] is False
    assert sum(not row["pass"] for row in comparison["checks"]) == 2
    for damage in ("short", "order"):
        broken = copy.deepcopy(valid)
        if damage == "short":
            broken["rows"].pop()
        else:
            broken["rows"][0]["axis"] = 2
        with pytest.raises(ValueError):
            response.compare_meshes(valid, broken)
    failed = copy.deepcopy(valid)
    failed["pass"] = False
    assert response.compare_meshes(valid, failed)["pass"] is False


def test_unchanged_five_percent_fixture_compliance_gate(valid):
    comparison = response.compare_meshes(valid, valid)
    assert len(comparison["fixture_compliance"]) == 9
    assert all(c["pass"] and c["relative_change"] == 0 for c in comparison["fixture_compliance"])
    for factor, accepted in ((1.049, True), (1.051, False), (.949, False)):
        fine = copy.deepcopy(valid)
        fine["rows"][0]["fixture"]["unit_load_compliance_mm_per_n"] *= factor
        result = response.compare_meshes(valid, fine)
        assert result["pass"] is accepted
        assert result["fixture_compliance"][0]["relative_change"] == pytest.approx(abs(factor-1))
        assert result["fixture_compliance"][0]["pass"] is accepted
        assert all(c["pass"] for c in result["checks"])
    for value in (0., -1., float("nan"), float("inf")):
        broken = copy.deepcopy(valid)
        broken["rows"][0]["fixture"]["unit_load_compliance_mm_per_n"] = value
        for a, b in ((valid, broken), (broken, valid)):
            with pytest.raises(ValueError, match="Positive finite fixture compliance"):
                response.compare_meshes(a, b)
