import hashlib
import json
import math
from pathlib import Path

import pytest

from fea.box_results import parse_results
from fea.record_updated_results import verify_hashes

RESULTS=Path(__file__).resolve().parents[1]/"fea/results"


def test_evidence_verification_rejects_changed_files(tmp_path):
    evidence=tmp_path/"test.dat"
    evidence.write_bytes(b"solver output")
    record={"evidence_sha256":{"test.dat":hashlib.sha256(evidence.read_bytes()).hexdigest()}}
    verify_hashes(record,tmp_path)
    evidence.write_bytes(b"changed output")
    with pytest.raises(ValueError,match="Changed solver evidence"):
        verify_hashes(record,tmp_path)


@pytest.mark.parametrize("size",[60,40])
def test_audited_bulk_records_match_raw_output(size):
    stem=f"box_audited_{size}_7000"
    record=json.loads((RESULTS/f"{stem}.json").read_text())
    assert record["geometry_commit"].startswith("d2a596d")
    assert record["min_jacobian"]>0
    assert len(record["load_nodes"])==5
    assert len(record["load_basis"])==6
    assert max(record["load_target_distances_mm"])<12
    cases=[(c["name"],tuple(v/1200 for v in c["force_n"])) for c in record["load_basis"]]
    raw=(RESULTS/f"{stem}.dat").read_bytes()
    assert hashlib.sha256(raw).hexdigest()==record["evidence_sha256"][f"{stem}.dat"]
    maxima,reactions=parse_results(raw.decode(),cases)
    assert maxima==record["max_top_displacement_mm"]
    assert reactions==record["reaction_totals_n"]
    values=list(maxima.values())
    assert values[1]==pytest.approx(2*values[0],rel=1e-6)


@pytest.mark.parametrize("size",[20,15])
def test_panel_records_have_expected_cases_and_equilibrium(size):
    records=json.loads((RESULTS/f"panel_screen_{size}.json").read_text())
    assert {(r["panel"],r["target"]) for r in records}=={
        ("main_upper_left","C10"),("main_upper_left","C12"),("kicker_left","3")}
    assert len(records)==3
    for r in records:
        assert r["geometry_commit"].startswith("d2a596d")
        assert r["mesh_mm"]==size
        assert r["screw_count"]==(8 if r["panel"]=="kicker_left" else 12)
        assert len(r["head_reactions_n"])==r["screw_count"]
        assert r["min_jacobian"]>0
        assert r["nodes"]>1000 and r["stress_points"]%4==0
        assert 390<r["load_patch_area_mm2"]<420
        for key in ("max_displacement_mm","peak_equivalent_stress_mpa","p95_equivalent_stress_mpa"):
            assert math.isfinite(r[key]) and r[key]>0
        assert math.sqrt(sum(v*v for v in r["applied_force_n"]))==pytest.approx(1200)
        for i in range(3):
            assert abs(r["reaction_n"][i]+r["applied_force_n"][i])<.1
            assert abs(r["reaction_moment_nmm"][i]+r["applied_moment_nmm"][i])<1
            assert sum(v[i] for v in r["head_reactions_n"].values())==pytest.approx(r["reaction_n"][i],abs=.1)
