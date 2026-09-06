import hashlib
import json
import tarfile
from copy import deepcopy
from pathlib import Path

import pytest

from fea.floor_contact_results import cross
from fea.section_force_coupon import audit
from fea.section_force_tet_coupon import (
    FACES,
    deck,
    force_token,
    geometry_audit,
    triangle_loads,
    verify_serialized_loads,
)


def test_published_pair_replays_raw_results_and_rejects_original_inputs():
    directory = Path("fea/results/section_force_tet_coupon")
    report = json.loads((directory/"report.json").read_text())
    path = directory/report["archive"]
    assert path.stat().st_size == report["archive_bytes"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == report["archive_sha256"]
    with tarfile.open(path) as archive:
        members = archive.getmembers()
        assert all(m.isfile() and not Path(m.name).is_absolute() and ".." not in Path(m.name).parts for m in members)
        assert len({m.name for m in members}) == len(members)
        raw = {m.name: archive.extractfile(m).read() for m in members}
    assert {name: hashlib.sha256(data).hexdigest() for name,data in raw.items()} == report["archive_contents"]
    for trial in ("unsafe-original", "corrected"):
        for n in (2, 4):
            prefix = trial+"/"
            record = json.loads(raw[prefix+f"tet{n}.json"])
            assert {key: value for key,value in record.items()
                    if key not in {"nodes", "elements", "fixed", "loads", "surfaces"}} == report["records"][trial][str(n)]
            assert record["exit_code"] == 0
            text = raw[prefix+f"tet{n}.inp"].decode()
            assert hashlib.sha256(text.encode()).hexdigest() == record["deck_sha256"]
            for name,digest in record["source_sha256"].items():
                assert hashlib.sha256(raw[prefix+"launch_sources/"+Path(name).name]).hexdigest() == digest
            for name,digest in record["output_sha256"].items():
                assert hashlib.sha256(raw[prefix+name]).hexdigest() == digest
            assert "*ERROR" not in raw[prefix+f"tet{n}.log"].decode().upper()
            expected, context = deck(n)
            normalized = json.loads(json.dumps(context))
            for key in ("nodes", "elements", "fixed", "loads", "surfaces", "geometry"):
                assert record[key] == normalized[key]
            # Source snapshots are historical; current reconstruction must still
            # reproduce the intended geometry and all non-CLOAD deck content.
            if trial == "corrected":
                assert text == expected
                assert verify_serialized_loads(text, context) == record["serialized_load_resultants_fz_mxyz"]
            else:
                import re
                strip = lambda value: re.sub(r"\*CLOAD,OP=NEW\n[^*]+", "*CLOAD,OP=NEW\n", value)
                assert strip(text) == strip(expected)
                with pytest.raises(ValueError, match="width"):
                    verify_serialized_loads(text, context)
            results = audit(raw[prefix+f"tet{n}.dat"].decode(), context)
            assert results == record["endpoints"]
            assert results[0]["external_balance_pass"]
            assert results[1]["external_balance_pass"] == (trial == "corrected")
            if trial == "corrected":
                for row in results:
                    low,high = [row["sections"][name] for name in ("LOWER_CUT", "UPPER_CUT")]
                    assert low["native_force_moment"] == pytest.approx([-v for v in high["native_force_moment"]], abs=1e-7)
                    assert low["area_normal_shear"][0] == pytest.approx(100.)
                assert results[0]["sections"]["LOWER_CUT"]["error"][2] == pytest.approx(-.0012)
                assert abs(results[1]["sections"]["LOWER_CUT"]["error"][4]) < .012


def test_quadratic_triangle_loads_include_midsides_and_linear_corner_terms():
    points = [(0.,0.,0.), (2.,0.,0.), (0.,1.,0.)]  # Area1.
    uniform = triangle_loads(points, [6.,6.,6.])
    assert uniform == pytest.approx([0.,0.,0.,2.,2.,2.])
    linear = triangle_loads(points, [0.,2.,0.])  # Traction x.
    assert linear == pytest.approx([-1/30, 1/15, -1/30, 4/15, 4/15, 2/15])
    assert sum(linear) == pytest.approx(2/3)  # Integral x dA.
    all_points = points+[(1.,0.,0.), (1.,.5,0.), (0.,.5,0.)]
    assert sum(point[0]*force for point,force in zip(all_points, linear, strict=True)) == pytest.approx(2/3)  # Integral x² dA.


@pytest.mark.parametrize("divisions", [2, 4])
def test_straight_tets_complete_opposed_cuts_and_exact_end_resultants(divisions):
    text, context = deck(divisions)
    assert "*ELEMENT,TYPE=C3D10" in text and "C3D8" not in text
    assert "NLGEOM" not in text and "*DLOAD" not in text
    assert context["geometry"]["element_count"] == 30*divisions**3
    assert context["geometry"]["volume_mm3"] == pytest.approx(10000.)
    assert context["geometry"]["minimum_jacobian"] > 0
    for name in ("LOWER_CUT", "UPPER_CUT", "TOP"):
        assert context["geometry"]["surfaces"][name] == {"face_count": 2*divisions**2, "area_mm2": 100.}
    assert {node for node,p in context["nodes"].items() if p[2] == 0} == set(context["fixed"])
    for load, expected_force, expected_moment in zip(context["loads"], (120.,0.), (0.,-1200.), strict=True):
        assert sum(load.values()) == pytest.approx(expected_force, abs=1e-10)
        moments = [sum(cross(context["nodes"][node], (0.,0.,force))[axis] for node,force in load.items()) for axis in range(3)]
        assert moments == pytest.approx([0., expected_moment, 0.], abs=1e-9)
    for element, face in context["surfaces"]["TOP"]:
        ids = [context["elements"][element][i] for i in FACES[face-1]]
        assert any(context["loads"][0][node] > 0 for node in ids[3:])


@pytest.mark.parametrize("mutation", ["curved", "inverted", "missing_cut", "duplicate_cut"])
def test_wrong_geometry_is_rejected(mutation):
    _, original = deck(2)
    context = deepcopy(original)
    if mutation == "curved":
        node = context["elements"][1][4]
        x,y,z = context["nodes"][node]
        context["nodes"][node] = (x,y,z+.1)
    elif mutation == "inverted":
        ids = context["elements"][1]
        ids[0], ids[1] = ids[1], ids[0]
    elif mutation == "missing_cut":
        context["surfaces"]["LOWER_CUT"].pop()
    else:
        context["surfaces"]["LOWER_CUT"].append(context["surfaces"]["LOWER_CUT"][0])
    with pytest.raises(ValueError):
        geometry_audit(context["nodes"], context["elements"], context["surfaces"])


@pytest.mark.parametrize("points,traction", [([(0,0,0)]*3,[1,1,1]), ([(0,0,0),(1,0,0),(0,1,0)],[1,float("nan"),1])])
def test_invalid_traction_triangle_fails(points, traction):
    with pytest.raises(ValueError):
        triangle_loads(points, traction)


def test_calculix_twenty_character_reader_cannot_truncate_exponent():
    value = -4.44089209850063e-16
    unsafe = f"{value:.15g}"
    assert len(unsafe) == 21
    assert float(unsafe[:20]) == pytest.approx(-.444089209850063)
    safe = force_token(value)
    assert len(safe) <= 20 and float(safe[:20]) == pytest.approx(value, rel=1e-12, abs=0)
    text, context = deck(2)
    assert verify_serialized_loads(text, context) == context["serialized_load_resultants_fz_mxyz"]
    changed = text.replace(force_token(context["loads"][1][95]), unsafe)
    assert changed != text
    with pytest.raises(ValueError, match="overwidth"):
        verify_serialized_loads(changed, context)


@pytest.mark.parametrize("value", [-1e308, -1e-308, 1e308, 1e-308, -0., 120.])
def test_finite_force_tokens_fit_entire_fortran_input_field(value):
    assert len(force_token(value)) <= 20
    assert float(force_token(value)[:20]) == pytest.approx(value, rel=1e-12, abs=0)
