import hashlib
import json
from pathlib import Path

import pytest

from fea.box_results import parse_results
from fea.hybrid_results import deck_geometry, require_candidate, support_moments


def test_candidate_identity_cannot_be_crossed():
    require_candidate({"candidate":"2x8-shallow"},"2x8-shallow")
    for info in ({},{"candidate":"2x8"},{"candidate":"2x10"}):
        with pytest.raises(ValueError,match="candidate"):
            require_candidate(info,"2x8-shallow")


@pytest.mark.parametrize("record_id,geometry_id",[("2x8","2x8-shallow"),("2x8-shallow","2x8")])
def test_recorder_rejects_crossed_identity_before_auditing(tmp_path,monkeypatch,record_id,geometry_id):
    from fea import record_hybrid_results as recorder
    directory=tmp_path/"2x8-shallow"
    directory.mkdir()
    (directory/"box_audited_60_7000.json").write_text(json.dumps({"candidate":record_id}))
    (directory/"box_frame_bulk.json").write_text(json.dumps({"candidate":geometry_id}))
    monkeypatch.setattr(recorder,"verify_hashes",lambda *args:None)
    with pytest.raises(ValueError,match="candidate"):
        recorder.checked_record(directory,60)


def test_reaction_moments_require_complete_balanced_output():
    nodes={1:(0,0,0),2:(0,2,0),3:(0,1,1)}
    text="\n forces (fx,fy,fz)\n\n 1 0 0 600\n 2 0 0 600\n\n total force\n"
    args=(nodes,[1,2],[3],[("down",(0,0,-1))])
    assert support_moments(text,*args)==[[1200,0,0]]
    for broken in (text.replace("2 0 0 600","2 0 0 601"),
                   text.replace("2 0 0 600",""),text.replace("600","nan"),""):
        with pytest.raises(ValueError):
            support_moments(broken,*args)


def test_deck_loads_and_supports_are_not_taken_on_trust():
    deck="*NODE\n"+'\n'.join(f"{i},0,0,{i}" for i in range(1,7))+"\n*NSET,NSET=TOP\n2,3,4,5,6\n*NSET,NSET=FEET\n1\n*BOUNDARY\nFEET,1,3,0\n*CLOAD,OP=NEW\n"
    deck+='\n'.join(f"{i},3,-240" for i in range(2,7))
    cases=[("down",(0,0,-1))]
    assert deck_geometry(deck,cases)[1:]==([1],[2,3,4,5,6])
    for broken in (deck.replace("-240","-241"),deck.replace("OP=NEW","OP=MOD"),
                   deck.replace("FEET,1,3,0","FEET,1,2,0")):
        with pytest.raises(ValueError):
            deck_geometry(broken,cases)


@pytest.mark.parametrize("size",["2x8","2x8-shallow","2x8-foot100","2x10","2x12"])
@pytest.mark.parametrize("mesh",[60,40])
def test_published_hybrid_force_and_displacement_records(size,mesh):
    directory=Path("fea/results/hybrid")/size
    stem=directory/f"box_audited_{mesh}_7000"
    record=json.loads(stem.with_suffix(".json").read_text())
    assert record["candidate"]==size
    assert record["frozen_geometry"]["candidate"]==size
    if size in ("2x8-shallow", "2x8-foot100"):
        for path,digest in record["frozen_geometry"]["geometry_source_sha256"].items():
            assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
        if size == "2x8-shallow":
            # Frozen audit context at dc1659a; adding a separate candidate must
            # not rewrite historical numerical evidence. Geometry and raw
            # DAT/deck reproduction remain checked independently below.
            assert record["audit_context_sha256"] == {
                "fea/solve_box_frame.py": "1d01b3b637a7c48dd31957efa6817d3c4c2c8fa344415fe250137bf93c8c3eff",
                "fea/prepare_hybrid_frame.py": "06e0b2bde3e6f57fbb56b6737c4e7a9b85006ed86478a6e7aa271b09b25b8ee1",
                "fea/hybrid_results.py": "c4eef7ad8b334f41fa8bc18f3278ba80c6644c70034076a1c07dd10d6fc28b62",
                "fea/record_hybrid_results.py": "4eb0647973e5b15e39e41b15c4f6ad12523b18d691df2aab668304a22b1727c1",
            }
        else:
            for path, digest in record["audit_context_sha256"].items():
                assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
    dat=stem.with_suffix(".dat")
    assert hashlib.sha256(dat.read_bytes()).hexdigest()==record["evidence_sha256"][dat.name]
    cases=[(c["name"],tuple(v/1200 for v in c["force_n"])) for c in record["load_basis"]]
    maxima,reactions=parse_results(dat.read_text(),cases)
    assert maxima==record["max_top_displacement_mm"]
    assert reactions==record["reaction_totals_n"]
    nodes={int(t):xyz for t,xyz in record["audit_node_coordinates_mm"].items()}
    assert support_moments(dat.read_text(),nodes,record["support_node_ids"],record["load_nodes"],cases)==record["reaction_moment_nmm"]
    assert len(maxima)==6 and record["min_jacobian"]>0
    raw=Path("fea/generated/hybrid")/size
    if (raw/stem.with_suffix(".inp").name).exists():
        from fea.record_hybrid_results import checked_record
        checked,_=checked_record(raw,mesh)
        assert checked["reaction_moment_nmm"]==record["reaction_moment_nmm"]
