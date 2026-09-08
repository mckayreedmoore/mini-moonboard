"""Independent free-body controls reject force-only and local-law false passes."""
import pytest

from fea.panel_contact_audit import audit, audit_history, time_rows


def fixture():
    context = {"nodes": {1: (75., 50., 100.), 2: (75., 50., 0.),
                         3: (75., 50., 0.), 4: (75., 50., -100.)},
               "upper": [1, 2], "lower": [3, 4], "top": [1], "support": [4],
               "prescribed_top_z_mm": {1: -.00175}, "penalty": 10000.,
               "surfaces": {"SLAVE": [(1, 1)]}}
    data = """
 displacements for set UPPER and time 1.0

 1 0 0 -.00175
 2 0 0 -.00001

 displacements for set LOWER and time 1.0

 3 0 0 0
 4 0 0 0

 forces for set TOP and time 1.0

 1 0 0 -100

 forces for set SUPPORT and time 1.0

 4 0 0 100

 relative contact displacement for all contact elements and time 1.0

 1 1 -.00001 0 0

 contact stress for all contact elements and time 1.0

 1 1 .1 0 0

 total number of contact elements for time 1.0

 1

 statistics for slave set SLAVE, master set MASTER and time 1.0

 total surface force and moment about the origin

 0 0 100 5000 -7500 0

"""
    return data, context


def test_eccentric_contact_wrench_matches_both_independent_bodies():
    data, context = fixture()
    row, = audit(data, context)
    assert row["contact_moment_about_face_center_nmm"] == [0., -2500., 0.]
    for residual in row["residual_wrenches_n_nmm"].values():
        assert residual == pytest.approx([0.]*6)


@pytest.mark.parametrize("old,new,match", [
    ("100 5000 -7500", "100 5000 -7000", "wrench mismatch"),
    ("4 0 0 100", "4 0 0 95", "wrench mismatch"),
    ("1 1 .1 0 0", "1 1 .2 0 0", "penalty law"),
    ("1 1 .1 0 0", "1 1 .1 .01 0", "frictional"),
    ("1 0 0 -.00175", "1 0 0 -.002", "Actuator"),
    ("master set MASTER", "master set WRONG", "contact endpoints"),
])
def test_changed_force_moment_history_and_contact_law_fail(old, new, match):
    data, context = fixture()
    with pytest.raises(ValueError, match=match):
        audit(data.replace(old, new), context)


def test_duplicate_contact_rows_rejected():
    data, _ = fixture()
    with pytest.raises(ValueError, match="Duplicate"):
        time_rows(data+data, "contact stress")


def test_extra_declared_but_unreported_contact_face_rejected():
    data, context = fixture()
    context["surfaces"]["SLAVE"].append((2, 1))
    with pytest.raises(ValueError, match="coverage"):
        audit(data, context)


def test_status_must_cover_all_endpoints_with_bounded_increments():
    rows = [{"time": t} for t in (.25, .5, .75, 1.)]
    status = "\n".join(f"1 {i} 1 2 {row['time']} {row['time']} .25"
                       for i, row in enumerate(rows, 1))
    audit_history(status, rows, .25)
    with pytest.raises(ValueError, match="counts"):
        audit_history(status, rows[:-1], .25)
    with pytest.raises(ValueError, match="limit"):
        audit_history(status, rows, .125)
    with pytest.raises(ValueError, match="sequence"):
        audit_history(status.replace("1 2 1 2", "1 3 1 2"), rows, .25)
