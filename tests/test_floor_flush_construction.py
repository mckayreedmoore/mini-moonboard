"""Current cut corners and drilling must use the same physical datum."""
import cadquery as cq
import pytest

from mini_moonboard import compact_floor_flush_frame as model
from scripts import clear_space_construction as shared
from scripts import floor_flush_construction as packet


def test_profile_coordinates_reconstruct_actual_trimmed_corners(tmp_path):
    with packet.sheet_context(tmp_path):
        datums = shared.bolt_member_datums(model.connections())
        corners = packet.profile_corner_rows(datums)
    assert len(datums) == 24
    assert len({r['member'] for r in corners}) == 8
    for row in corners:
        datum = next(d for d in datums if d['member'] == row['member'])
        origin = cq.Vector(*(row[f'origin_{axis}_mm'] for axis in 'xyz'))
        along = cq.Vector(0., datum['along_y'], datum['along_z'])
        cross = cq.Vector(0., datum['cross_y'], datum['cross_z'])
        point = origin + along*row['along_from_corner_mm'] + cross*row['signed_cross_from_corner_mm']
        assert point.toTuple() == pytest.approx(tuple(row[f'world_{axis}_mm'] for axis in 'xyz'), abs=1.e-7)
    for name, end in model.runner_end_geometry().items():
        points = {(round(r['world_y_mm'], 6), round(r['world_z_mm'], 6))
                  for r in corners if r['member'] == name}
        assert points == {(round(y, 6), round(z, 6)) for y, z in end['profile_yz_mm']}


def test_sheet_context_restores_globals_on_failure(tmp_path):
    old_model, old_out = shared.model, shared.OUT
    with pytest.raises(RuntimeError), packet.sheet_context(tmp_path):
        assert shared.model.KEY == model.KEY
        assert shared.model.trim_planes() == {}
        raise RuntimeError('stop generation')
    assert shared.model is old_model
    assert shared.OUT is old_out
