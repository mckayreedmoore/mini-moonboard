import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_c1_screen_is_a_bounded_unresolved_factory_candidate() -> None:
    record = json.loads(
        (ROOT / "docs/bolted-candidate-prototypes/wurth-c1.json").read_text()
    )

    assert record["status"] == "screened_for_joint_prototype"
    assert record["product"]["standard"] == "DIN EN 912:2011-09"
    assert record["applicability"]["softwood_wood_to_wood_listed"] is True
    assert record["applicability"]["through_bolt_and_nut_listed"] is True
    assert record["applicability"]["capacity_for_this_board"] == "unresolved; requires density, bolt grade, plate/washer stack, grain direction, edge/end distances, and combined-action check"
    assert "native solve" in " ".join(record["development_constraints"])
