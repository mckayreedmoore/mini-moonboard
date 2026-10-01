from __future__ import annotations

import hashlib
import math

import cadquery as cq
import pytest
from envelopes import (
    STATUS_AMBIGUOUS,
    STATUS_CONTAINED,
    STATUS_INCOMPATIBLE,
    EnvelopeError,
    _fit_check,
    canonical_bytes,
    section_basis_from_step,
    verify_canonical_file,
    verify_pin_document,
)
from OCP.gp import gp_Trsf


def rigid_transform(
    x_axis: tuple[float, float, float],
    y_axis: tuple[float, float, float],
    z_axis: tuple[float, float, float],
) -> cq.Matrix:
    transform = gp_Trsf()
    transform.SetValues(
        x_axis[0],
        y_axis[0],
        z_axis[0],
        0.0,
        x_axis[1],
        y_axis[1],
        z_axis[1],
        0.0,
        x_axis[2],
        y_axis[2],
        z_axis[2],
        0.0,
    )
    return cq.Matrix(transform)


def fit(
    shape: cq.Shape,
    grain: tuple[float, float, float],
    section: list[float],
    length: float,
):
    basis = section_basis_from_step(shape, grain)
    assert basis["status"] == STATUS_CONTAINED, basis
    return _fit_check(
        shape,
        tuple(basis["grain_axis_global_xyz"]),
        tuple(basis["section_q_axis_global_xyz"]),
        tuple(basis["section_r_axis_global_xyz"]),
        length,
        section,
    )


def test_rotated_box_with_oblique_grain_has_known_containment() -> None:
    root2 = math.sqrt(0.5)
    grain = (root2, root2, 0.0)
    section_q = (0.0, 0.0, 1.0)
    section_r = (root2, -root2, 0.0)
    local = cq.Solid.makeBox(20.0, 6.0, 4.0)
    shape = local.transformShape(rigid_transform(grain, section_q, section_r))

    result = fit(shape, grain, [8.0, 6.0], 22.0)

    assert result["status"] == STATUS_CONTAINED
    assert result["stock_minus_finished_outside_volume_mm3"] <= 1e-3
    assert result["finished_minus_intersection_volume_mm3"] <= 1e-3
    assert result["finished_oriented_spans_g_q_r_mm"] == pytest.approx([20.0, 6.0, 4.0])
    assert result["length_surplus_mm"] == pytest.approx(2.0)
    assert result["datum_and_surplus_rule"].startswith("finished minimum-grain station")


def test_bored_and_taper_cut_solid_stays_inside_starting_stock() -> None:
    stock = cq.Solid.makeBox(20.0, 8.0, 6.0)
    bore = cq.Solid.makeCylinder(
        1.0, 20.0, cq.Vector(0.0, 4.0, 3.0), cq.Vector(1.0, 0.0, 0.0)
    )
    taper_cut = (
        cq.Workplane("XY")
        .polyline([(15.0, 0.0), (20.0, 0.0), (20.0, 8.0)])
        .close()
        .extrude(6.0)
        .val()
    )
    finished = stock.cut(bore).cut(taper_cut)
    assert finished.isValid()

    result = fit(finished, (1.0, 0.0, 0.0), [8.0, 6.0], 20.0)

    assert result["status"] == STATUS_CONTAINED
    assert result["stock_minus_finished_outside_volume_mm3"] <= 1e-3
    assert result["stock_intersection_volume_mm3"] == pytest.approx(
        finished.Volume(), abs=1e-3
    )


def test_finished_protrusion_is_incompatible_and_reported_by_brep_difference() -> None:
    finished = cq.Solid.makeBox(11.0, 8.0, 6.0)

    result = fit(finished, (1.0, 0.0, 0.0), [8.0, 6.0], 10.0)

    assert result["status"] == STATUS_INCOMPATIBLE
    assert result["length_surplus_mm"] == pytest.approx(-1.0)
    assert result["stock_minus_finished_outside_volume_mm3"] == pytest.approx(48.0)


def test_ambiguous_axis_fails_closed_and_equal_dimensions_use_a_stable_mapping() -> (
    None
):
    cube = cq.Solid.makeBox(10.0, 4.0, 4.0)
    ambiguous = section_basis_from_step(cube, (1.0, 1.0, 1.0))
    assert ambiguous["status"] == STATUS_AMBIGUOUS

    square_result = fit(cube, (1.0, 0.0, 0.0), [4.0, 4.0], 10.0)
    assert square_result["status"] == STATUS_CONTAINED
    assert square_result["section_axis_mapping"]["swapped"] is False

    bad_dimensions = _fit_check(
        cube, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), 10.0, [4.0]
    )
    assert bad_dimensions["status"] == STATUS_AMBIGUOUS


def test_pinned_source_change_and_noncanonical_json_bytes_are_rejected(
    tmp_path,
) -> None:
    pinned = tmp_path / "input.bin"
    pinned.write_bytes(b"frozen")
    pins = {
        "pins": {
            "fixture": {
                "path": "input.bin",
                "sha256": hashlib.sha256(b"frozen").hexdigest(),
                "size_bytes": 6,
            }
        }
    }
    verify_pin_document(tmp_path, pins)
    pinned.write_bytes(b"changed")
    with pytest.raises(EnvelopeError, match="pinned bytes changed"):
        verify_pin_document(tmp_path, pins)

    canonical = tmp_path / "canonical.json"
    value = {"z": 1, "a": "x"}
    canonical.write_bytes(canonical_bytes(value))
    verify_canonical_file(canonical, value, "fixture")
    canonical.write_text('{ "z": 1, "a": "x" }\n', encoding="utf-8")
    with pytest.raises(EnvelopeError, match="exact canonical"):
        verify_canonical_file(canonical, value, "fixture")
