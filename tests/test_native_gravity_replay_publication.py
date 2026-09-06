import math

import pytest

from fea.native_gravity_supplement import verify as verify_supplement
from fea.publish_native_gravity_replay import close, verify


def test_published_gravity_correction_replays_original_raw_states_without_gmsh():
    report = verify()
    assert report["node_count"] == 62020
    assert report["element_count"] == 32511
    assert max(abs(v) for row in report["endpoints"] for v in row["delta_gravity_moment_nmm"]) == pytest.approx(.0008193227551339094)
    assert max(abs(v) for row in report["endpoints"] for v in row["candidate_moment_residual_nmm"]) == pytest.approx(30.28374970307231)


def test_independent_comparison_rejects_changed_or_nonfinite_correction():
    for changed in ([0,0,.001],[0,0,math.nan],[0,0,math.inf],[0,0]):
        with pytest.raises(ValueError,match="arithmetic"):
            close(changed,[0,0,0])


def test_strict_import_supplement_preserves_all_original_weights():
    report = verify_supplement()
    assert report["verified_weight_count"] == 62020
    assert report["all_weights_exactly_equal"]
