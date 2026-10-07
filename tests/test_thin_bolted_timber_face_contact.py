"""Paired timber compression coupons; no candidate geometry or frame solve."""

import copy
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from scripts import thin_bolted_timber_face_contact as contact


def rows(divisions=2, bedding=1.):
    return [r for r in contact.describe_contacts(contact.coupon_proof(divisions), bedding)
            if r["source_descriptor"]["patch_id"] == "patch-0"]


def rigid_state(translation=(0., 0., 0.), rotation=(0., 0., 0.)):
    centers = np.array([[-50., 0., 0.], [50., 0., 0.]])
    R = contact.finite.mechanical.so3_exp(rotation)
    state = np.zeros((2, 6))
    state[:, :3] = centers @ (R-np.eye(3)).T + translation
    state[:, 3:] = 1000.*np.array(rotation)
    return state


def superpose(q, rotation):
    centers = np.tile([[-50., 0., 0.], [50., 0., 0.]], (2, 1))
    state = q.reshape(4, 6).copy()
    state[:, :3] = (centers+state[:, :3]) @ rotation.T - centers
    for row in state:
        row[3:] = 1000.*contact.finite.mechanical.so3_log(
            rotation @ contact.finite.mechanical.so3_exp(row[3:]/1000.))
    return state.ravel()


def test_rectangle_compression_opening_and_zero_reference_contact():
    for dz, force, energy in ((-.02, 96., .96), (.02, 0., 0.), (0., 0., 0.)):
        q = np.r_[rigid_state((0., 0., dz)).ravel(), np.zeros(12)]
        result = contact.coupon_response(q, rows(), False)
        assert sum(r["axial_scalar_force_n"] for r in result["actions"]) == pytest.approx(force)
        assert result["energy_nmm"] == pytest.approx(energy)
        for row in result["actions"]:
            np.testing.assert_allclose(row["force_on_first_xyz_n"][:2], 0., atol=1e-12)
            assert row["director_owner"] == row["second"]


@pytest.mark.parametrize("angle", [20., 73.])
def test_common_rigid_rotation_preserves_closed_and_open_contact(angle):
    R = contact.finite.mechanical.so3_exp(np.array([.3, -.4, .5])/np.sqrt(.5)*np.deg2rad(angle))
    for dz in (-.02, 0., .02):
        q = np.r_[rigid_state((0., 0., dz)).ravel(), np.zeros(12)]
        before = contact.coupon_response(q, rows(), False)
        after = contact.coupon_response(superpose(q, R), rows(), False)
        assert after["energy_nmm"] == pytest.approx(before["energy_nmm"], abs=2e-12)
        for a, b in zip(before["actions"], after["actions"], strict=True):
            np.testing.assert_allclose(b["force_on_first_xyz_n"], R @ a["force_on_first_xyz_n"], atol=2e-10)


def test_friction_free_slip_does_not_add_force_or_energy_and_owned_couple_closes():
    q = np.r_[rigid_state((3., -5., -.02)).ravel(), np.zeros(12)]
    result = contact.coupon_response(q, rows(), False)
    assert result["energy_nmm"] == pytest.approx(.96)
    for action in result["actions"]:
        F = np.array(action["force_on_first_xyz_n"])
        np.testing.assert_allclose(F[:2], 0., atol=1e-12)
        assert np.linalg.norm(action["moment_on_second_at_current_point_xyz_nmm"]) > 0.
        np.testing.assert_allclose(action["force_on_second_xyz_n"], -F, atol=1e-12)
        p1, p2 = np.array(action["point_on_first_xyz_mm"]), np.array(action["point_on_second_xyz_mm"])
        np.testing.assert_allclose(np.cross(p1-p2, F)+action["moment_on_second_at_current_point_xyz_nmm"], 0., atol=1e-12)
        np.testing.assert_allclose(action["moment_on_first_at_current_point_xyz_nmm"], 0., atol=1e-12)
    slip_direction = np.zeros(24); slip_direction[[0, 6]] = 1.
    assert result["gradient_n"] @ slip_direction == pytest.approx(0., abs=1e-12)


def test_partly_open_rocking_has_hand_active_force_and_original_energy_derivatives():
    angle = .03
    q = np.r_[rigid_state((0., 0., 0.), (0., angle, 0.)).ravel(), np.zeros(12)]
    result = contact.coupon_response(q, rows(), True)
    assert sum(r["axial_scalar_force_n"] > 0. for r in result["actions"]) == 2
    expected_force = 2400.*20.*np.sin(angle)
    expected_energy = .5*2400.*(20.*np.sin(angle))**2
    assert sum(r["axial_scalar_force_n"] for r in result["actions"]) == pytest.approx(expected_force)
    assert result["energy_nmm"] == pytest.approx(expected_energy)
    d = np.random.default_rng(451).normal(size=24); d /= np.linalg.norm(d)
    step = 1e-3
    plus = contact.coupon_response(q+step*d, rows(), False)
    minus = contact.coupon_response(q-step*d, rows(), False)
    assert d @ result["gradient_n"] == pytest.approx((plus["energy_nmm"]-minus["energy_nmm"])/(2*step), rel=2e-7)
    np.testing.assert_allclose(result["hessian_csr"] @ d, (plus["gradient_n"]-minus["gradient_n"])/(2*step), rtol=2e-6, atol=1e-7)
    for a in result["actions"]:
        np.testing.assert_allclose(a["pair_spatial_moment_residual_nmm"], 0., atol=2e-10)


def test_exact_area_uniform_force_and_cell_refinement_controls_rocking_quadrature():
    uniform = np.r_[rigid_state((0., 0., -.02)).ravel(), np.zeros(12)]
    angle = .03
    rocking = np.r_[rigid_state(rotation=(0., angle, 0.)).ravel(), np.zeros(12)]
    energy = []
    # The exact half-rectangle integral is .5*k*60*sin(a)^2*(40^3/3).
    hand = .5*60.*np.sin(angle)**2*40.**3/3.
    for divisions in (2, 4, 8):
        current = rows(divisions)
        assert sum(r["source_descriptor"]["cell_area_mm2"] for r in current) == 4800.
        assert contact.coupon_response(uniform, current, False)["energy_nmm"] == pytest.approx(.96)
        energy.append(contact.coupon_response(rocking, current, False)["energy_nmm"])
    assert energy == sorted(energy)
    assert abs(hand-energy[-1]) < abs(hand-energy[0])
    assert energy[-1]/hand == pytest.approx(1.-1./8.**2)


@pytest.mark.parametrize("mutation", ["pair", "duplicate-patch", "duplicate-cell", "normal", "area", "centroid", "plane", "nonfinite", "bedding"])
def test_source_geometry_or_scenario_contradictions_reject(mutation):
    proof = contact.coupon_proof(); bedding = 1.
    if mutation == "pair":
        proof["pairs"].pop()
    elif mutation == "duplicate-patch":
        proof["patches"].append(copy.deepcopy(proof["patches"][0]))
    elif mutation == "duplicate-cell":
        proof["patches"][0]["cells"].append(copy.deepcopy(proof["patches"][0]["cells"][0]))
    elif mutation == "normal":
        proof["patches"][0]["normal_from_second_to_first_xyz"] = [0., 0., 2.]
    elif mutation == "area":
        proof["patches"][0]["area_mm2"] += 10.
    elif mutation == "centroid":
        proof["patches"][0]["centroid_xyz_mm"][0] = 1.
    elif mutation == "plane":
        proof["patches"][0]["cells"][0]["point_xyz_mm"][2] = 1.
    elif mutation == "nonfinite":
        proof["patches"][0]["cells"][0]["area_mm2"] = np.nan
    else:
        bedding = np.inf
    with pytest.raises(ValueError):
        contact.describe_contacts(proof, bedding)


def test_explicit_zero_patch_pair_is_retained_as_inventory_without_fictitious_contact():
    proof = contact.coupon_proof()
    proof["patches"].pop()
    assert len(contact.describe_contacts(proof, 1.)) == 20


def test_attachment_copies_lists_and_pins_without_mutating_prepared_source(monkeypatch):
    proof = contact.coupon_proof(); proof["method"] = {"cell_size_mm": 30.}
    old = [{"id": "old", "kind": "floor_normal"}]
    mapped = {name: {"kind": "timber"} for pair in contact.EXPECTED_PAIRS for name in pair}
    potential = SimpleNamespace(interactions=old, source_sha256=contact.source_pins(), map={"mechanical_bodies": mapped})
    original_pins = potential.source_sha256.copy()
    with tempfile.TemporaryDirectory(dir=contact.ROOT/"fea/generated") as temporary:
        path = Path(temporary)/"proof.json"; path.write_text(json.dumps(proof))
        method = Path(temporary)/"method.json"
        method.write_text(json.dumps({"schema": contact.METHOD_SCHEMA, "source_sha256": contact.source_pins()}))
        monkeypatch.setattr(contact, "METHOD_PATH", method)
        monkeypatch.setattr(contact, "read_proof", lambda p, sha: (proof, contact.source_pins()))
        extended = contact.attach_prepared(potential, path, contact.finite.frame.sha(path),
            bedding_n_mm3=1., method_receipt_sha256=contact.finite.frame.sha(method))
        assert extended is not potential
        assert extended.map is potential.map
        assert len(extended.interactions) == 25 and potential.interactions == old
        assert potential.source_sha256 == original_pins
        assert extended.source_sha256 is not potential.source_sha256
        assert extended.timber_face_contact_parameters["timber_face_contact_cell_mm"] == 30.
        with pytest.raises(ValueError, match="already attached"):
            contact.attach_prepared(extended, path, contact.finite.frame.sha(path), method_receipt_sha256=contact.finite.frame.sha(method))


def test_rectangle_method_receipt_coupon_matches_hand_force():
    result = contact.method_coupons()
    assert result["observed_force_n"] == pytest.approx(result["hand_force_n"])


def test_contact_source_pins_cannot_replace_loaded_or_prior_authority():
    with pytest.raises(ValueError, match="contradictory"):
        contact.source_pins({contact.OWN: "0"*64})
    with pytest.raises(ValueError, match="contradictory"):
        contact.merge_pins({"proof.json": "a"}, {"proof.json": "b"})
