import hashlib
import json
import tarfile
from pathlib import Path

import pytest

from fea.floor_contact_results import cross
from fea.section_force_coupon import audit, deck, sections


@pytest.mark.parametrize("divisions", [2, 4])
def test_end_loads_have_exact_axial_and_bending_resultants(divisions):
    text, context = deck(divisions)
    assert text.count("*STEP\n") == 2
    assert "NLGEOM" not in text and "*DLOAD" not in text
    assert "*ELEMENT,TYPE=C3D8" in text
    for forces, expected_force, expected_moment in zip(context["loads"], (120., 0.), (0., -1200.), strict=True):
        assert sum(forces.values()) == pytest.approx(expected_force, abs=1e-10)
        assert sum(cross(context["nodes"][node], (0, 0, force))[1] for node, force in forces.items()) == pytest.approx(expected_moment, abs=1e-10)
    assert text.count("*SECTION PRINT,SURFACE=LOWER_CUT,NAME=LOWER\nSOF") == 2
    assert text.count("*SECTION PRINT,SURFACE=UPPER_CUT,NAME=UPPER\nSOM") == 2


def exact_output():
    _, context = deck(2)
    output = ""
    for time, forces in enumerate(context["loads"], 1):
        output += f"forces for set FIXED and time {time}\n"
        for node in context["fixed"]:
            top_node = next(tag for tag in forces if context["nodes"][tag][:2] == context["nodes"][node][:2])
            output += f"{node} 0 0 {-forces[top_node]}\n"
        output += f"\ndisplacements for set ALLN and time {time}\n"
        output += "".join(f"{node} 0 0 0\n" for node in context["nodes"])
        for name, sign in (("LOWER_CUT", 1), ("UPPER_CUT", -1)):
            fz, my = (120*sign, 0) if time == 1 else (0, -1200*sign)
            output += (f"\nstatistics for surface set {name} and time {time}\n"
                       f"\n0 0 {fz} 0 {my} 0\n\n0 0 50 0 0 {sign}\n\n0 {my} 0\n\n100 {fz*sign} 0 0 {abs(my)}\n")
    return output, context


def test_native_vectors_are_checked_against_external_freebody():
    data, context = exact_output()
    result = audit(data, context)
    assert len(result) == 2 and all(row["external_balance_pass"] for row in result)
    assert all(section["error"] == pytest.approx([0.]*6, abs=1e-9) for row in result for section in row["sections"].values())
    changed = data.replace("0 0 0 0 -1200 0", "0 0 0 0 -800 0")
    result = audit(changed, context)
    assert result[1]["external_balance_pass"]
    assert result[1]["sections"]["LOWER_CUT"]["error"][4] == pytest.approx(400.)


def test_missing_duplicate_and_nonfinite_native_output_rejected():
    data, context = exact_output()
    with pytest.raises(ValueError, match="Missing"):
        audit("", context)
    with pytest.raises(ValueError, match="Duplicate"):
        sections(data+data)
    with pytest.raises(ValueError, match="Nonfinite"):
        sections(data.replace("0 0 120 0 0 0", "0 0 nan 0 0 0"))
    missing = data.replace("forces for set FIXED and time 2", "forces for set OTHER and time 2")
    with pytest.raises(ValueError, match="Incomplete nodal"):
        audit(missing, context)


def test_published_native_sections_replay_without_solver_or_generated_files():
    directory = Path("fea/results/section_force_coupon")
    report = json.loads((directory/"report.json").read_text())
    archive_path = directory/report["archive"]
    assert archive_path.stat().st_size == report["archive_bytes"]
    assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == report["archive_sha256"]
    with tarfile.open(archive_path) as archive:
        members = archive.getmembers()
        assert all(member.isfile() and not Path(member.name).is_absolute() and ".." not in Path(member.name).parts for member in members)
        assert len({member.name for member in members}) == len(members)
        raw = {member.name: archive.extractfile(member).read() for member in members}
    assert {name: hashlib.sha256(content).hexdigest() for name, content in raw.items()} == report["archive_contents"]
    launch = raw["section_force_coupon.launch.py"]
    assert launch == (directory/"section_force_coupon.launch.py").read_bytes()
    assert "BENDING RESULTANTS NOT CONVERGED" in report["status"]
    errors = []
    for n in (2, 4):
        record = json.loads(raw[f"section{n}.json"])
        text, context = deck(n)
        assert text.encode() == raw[f"section{n}.inp"]
        assert hashlib.sha256(text.encode()).hexdigest() == record["deck_sha256"]
        assert hashlib.sha256(launch).hexdigest() == record["source_sha256"]
        assert record["exit_code"] == 0
        assert "*ERROR" not in raw[f"section{n}.log"].decode().upper()
        for name, digest in record["helper_sha256"].items():
            assert hashlib.sha256(raw["helpers/"+Path(name).name]).hexdigest() == digest
        for name, digest in record["output_sha256"].items():
            assert hashlib.sha256(raw[name]).hexdigest() == digest
        result = audit(raw[f"section{n}.dat"].decode(), context)
        saved = report["comparisons"][str(n)]
        assert result == record["endpoints"] == saved["endpoints"]
        assert all(row["external_balance_pass"] for row in result)
        assert saved["element_count"] == 5*n**3
        for row in result:
            lower, upper = [row["sections"][name] for name in ("LOWER_CUT", "UPPER_CUT")]
            assert lower["native_force_moment"] == pytest.approx([-v for v in upper["native_force_moment"]], abs=1e-8, rel=0)
            assert lower["area_normal_shear"][0] == pytest.approx(100.)
        axial, bending = [row["sections"]["LOWER_CUT"] for row in result]
        assert saved["axial_force_n"] == axial["native_force_moment"][2]
        assert saved["axial_error_percent"] == pytest.approx(100*axial["error"][2]/120)
        assert saved["bending_magnitude_nmm"] == abs(bending["native_force_moment"][4])
        assert saved["bending_shortfall_percent"] == pytest.approx(100*abs(bending["error"][4])/1200)
        errors.append(saved["bending_shortfall_percent"])
    assert errors[0] > errors[1] > 10  # Refinement improves this failure, not convergence.
