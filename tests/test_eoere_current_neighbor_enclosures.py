import copy
from itertools import product

import numpy as np
import pytest
from OCP.gp import gp_Trsf
from scipy.spatial.transform import Rotation
from test_eoere_current_contact_inverse import current_fixture

from scripts import eoere_current_neighbor_enclosures as neighbors


@pytest.fixture(scope="module")
def kernels():
    return neighbors.inverse.runtime_methods()


def source_fixture(kernels, *, kind="box", rotated=False):
    bedding, method, _adapter, smooth, container, _ = kernels
    cq = smooth.reference.cq
    original_box = np.array([[-15., 125.], [-5., 5.], [-6., 6.]])
    if kind == "cylinder":
        shape = cq.Solid.makeCylinder(5., 140., cq.Vector(-15., 0., 0.), cq.Vector(1., 0., 0.))
    else:
        shape = cq.Solid.makeBox(140., 10., 12., cq.Vector(-15., -5., -6.))
        if kind == "bored":
            shape = shape.cut(cq.Solid.makeCylinder(1., 14., cq.Vector(31., 0., -7.), cq.Vector(0., 0., 1.)))
            shape, _ = container.strict_solid(shape, smooth.reference)
    rotation = Rotation.from_rotvec([.2, -.3, .1]).as_matrix() if rotated else np.eye(3)
    start = np.array([7., -9., 3.]) if rotated else np.zeros(3)
    transform = np.eye(4)
    transform[:3, :3], transform[:3, 3] = rotation, start
    rigid = gp_Trsf()
    rigid.SetValues(*transform[:3].ravel().tolist())
    shape = shape.transformShape(cq.Matrix(rigid))
    owner, identity = "synthetic", {"synthetic_original_source": kind,
        "finished_raw_file_path": "synthetic-source.brep", "finished_raw_file_sha256": "synthetic"}
    geometry = smooth.reference.ReferenceSolidDistance(shape, owner_id=owner, source_identity=identity)
    storage = Rotation.from_rotvec([-.07, .04, .12]).as_matrix()
    chart = {"kind": "timber", "reference_start_xyz_mm": start.tolist(), "reference_axis_xyz": rotation[:, 0].tolist(),
        "reference_stations_mm": [0., 100.], "node_reference_centers_xyz_mm": [start.tolist(), (start+100.*rotation[:, 0]).tolist()],
        "node_dof_indices": np.arange(12).reshape(2, 6).tolist(), "storage_basis_columns_xyz": storage.tolist()}
    bounds = shape.BoundingBox()
    world_box = np.array([[bounds.xmin, bounds.xmax], [bounds.ymin, bounds.ymax], [bounds.zmin, bounds.zmax]])
    extent = {"schema": "thin_bolted_finite_reference_domain_box/v1", "owner_id": owner,
        "bounds_xyz_mm": (world_box+[-100., 100.]).tolist(),
        "source_identity": {**identity, "topology_sha256": geometry.topology_sha256, "genuine_cached_solid_bounds_xyz_mm": world_box.tolist()}}
    guard = neighbors.inverse.TrialDomain(owner, chart, extent, 12, method)
    timber = bedding.TimberSpatialMap(chart, owner_id=owner, ndof=12, domain_guard=guard.guard)
    return chart, extent, geometry, guard, timber, smooth, rotation, start, original_box


@pytest.mark.parametrize("kind", ["box", "bored", "cylinder"])
def test_genuine_rigid_source_box_matches_independent_polyhedral_or_circular_extrema(kernels, kind):
    chart, extent, geometry, _guard, _timber, smooth, rotation, start, original = source_fixture(kernels, kind=kind, rotated=True)
    record = neighbors.local_reference_box("synthetic", chart, extent, geometry, smooth)
    basis = np.asarray(record["chart_basis_columns_xyz"])
    if kind == "cylinder": expected = np.array([[-15., 125.], [-5., 5.], [-5., 5.]])
    else:
        world = start+np.asarray(list(product(*original.tolist())))@rotation.T
        points = (world-start)@basis
        expected = np.column_stack((points.min(axis=0), points.max(axis=0)))
    np.testing.assert_allclose(record["native_local_bounds_mm"], expected, rtol=0., atol=1e-6)
    error = np.asarray(record["coordinate_reexpression_error_bound_mm"])
    np.testing.assert_allclose(record["padded_local_bounds_mm"], np.asarray(record["native_local_bounds_mm"])+np.column_stack((-error-1e-6, error+1e-6)), rtol=0., atol=1e-14)
    assert record["native_use_triangulation"] is False and record["native_use_shape_tolerance"] is True
    assert smooth.reference.brep_sha(geometry.shape) == geometry.shape_sha256
    assert record["record_canonical_sha256"] == neighbors.canonical_sha({k: v for k, v in record.items() if k != "record_canonical_sha256"})


@pytest.mark.parametrize("motion", ["rigid", "twist", "endpoint_tilt", "translation"])
@pytest.mark.parametrize("rotated", [False, True])
def test_piece_cover_encloses_independent_motion_interior_stations_and_both_extensions(kernels, motion, rotated):
    chart, extent, geometry, guard, timber, smooth, rotation_source, start_source, original_source = source_fixture(kernels, rotated=rotated)
    record = neighbors.local_reference_box("synthetic", chart, extent, geometry, smooth)
    storage, q = np.asarray(chart["storage_basis_columns_xyz"]), np.zeros((2, 6))
    centers = np.asarray(chart["node_reference_centers_xyz_mm"])
    if motion == "rigid":
        theta, shift = np.array([.03, -.04, .02]), np.array([2., -3., 1.])
        rotation = Rotation.from_rotvec(theta).as_matrix()
        q[:, :3] = (centers@rotation.T+shift-centers)@storage
        q[:, 3:] = 1000.*(theta@storage)
    elif motion == "twist":
        q[:, 3:] = 1000.*np.array([[.1, 0., 0.], [-.1, 0., 0.]])@storage
    elif motion == "endpoint_tilt":
        q[:, 3:] = 1000.*(np.array([0., .12, 0.])@storage)
    else:
        q[:, :3] = np.array([[1., -3., 2.], [-2., 7., -1.]])@storage
    q = q.ravel()
    bound = guard.bound(q)
    cover = neighbors.piece_enclosures(chart, q, extent, bound, record)
    assert [p["branch"] for p in cover["pieces"]] == ["first", "segment", "last"]
    intervals = [p["source_axial_interval_mm"] for p in cover["pieces"]]
    assert intervals[0][0] == record["padded_local_bounds_mm"][0][0] and intervals[-1][1] == record["padded_local_bounds_mm"][0][1]
    assert intervals[0][1] == intervals[1][0] == 0. and intervals[1][1] == intervals[2][0] == 100.
    start = np.asarray(chart["reference_start_xyz_mm"])
    samples = list(product([-15., 0., 20., 31., 100., 125.], *[[lo, (lo+hi)/2., hi] for lo, hi in original_source[1:]]))
    boxes = [np.asarray(p["bounds_xyz_mm"]) for p in cover["pieces"]]
    for local in samples:
        point = start_source+rotation_source@local
        axial = (point-start)@np.asarray(chart["reference_axis_xyz"])
        fraction = np.clip(axial/100., 0., 1.)
        u = ((1.-fraction)*q[:3]+fraction*q[6:9])@storage.T
        if motion == "twist": theta = np.array([.1-.2*fraction, 0., 0.])
        elif motion == "endpoint_tilt": theta = np.array([0., .12, 0.])
        elif motion == "translation": theta = np.zeros(3)
        else: theta = np.array([.03, -.04, .02])
        center = centers[0]+np.clip(axial, 0., 100.)*np.asarray(chart["reference_axis_xyz"])
        mapped = center+u+Rotation.from_rotvec(theta).as_matrix()@(point-center)
        np.testing.assert_allclose(timber.point_field(q, point, tangent=False)["value_xyz"], mapped, rtol=0., atol=2e-12)
        assert any(np.all(mapped >= box[:, 0]) and np.all(mapped <= box[:, 1]) for box in boxes)
    assert cover["complete_reference_axial_box_covered"] is True
    assert cover["q_canonical_sha256"] == neighbors.canonical_sha(q.tolist())


def test_nonuniform_station_cover_uses_each_interior_translation_and_clipped_interval(kernels):
    chart, extent, geometry, _guard, _timber, smooth, _rotation, _start, _original = source_fixture(kernels)
    chart["reference_stations_mm"] = [0., 25., 75., 100.]
    chart["node_reference_centers_xyz_mm"] = [[x, 0., 0.] for x in chart["reference_stations_mm"]]
    chart["node_dof_indices"] = np.arange(24).reshape(4, 6).tolist()
    storage = np.asarray(chart["storage_basis_columns_xyz"])
    translations = np.array([[0., 0., 0.], [1., 10., -2.], [-3., -8., 4.], [0., 0., 0.]])
    q = np.zeros((4, 6))
    q[:, :3] = translations@storage
    q = q.ravel()
    guard = neighbors.inverse.TrialDomain("synthetic", chart, extent, 24, kernels[1])
    box = neighbors.local_reference_box("synthetic", chart, extent, geometry, smooth)
    cover = neighbors.piece_enclosures(chart, q, extent, guard.bound(q), box)
    assert [p["branch"] for p in cover["pieces"]] == ["first", "segment", "segment", "segment", "last"]
    np.testing.assert_allclose([p["source_axial_interval_mm"] for p in cover["pieces"]],
        [[box["padded_local_bounds_mm"][0][0], 0.], [0., 25.], [25., 75.], [75., 100.], [100., box["padded_local_bounds_mm"][0][1]]], rtol=0., atol=0.)
    for index, piece in enumerate(cover["pieces"][1:-1]):
        np.testing.assert_allclose(piece["translation_component_min_mm"], translations[index:index+2].min(axis=0), atol=1e-14)
        np.testing.assert_allclose(piece["translation_component_max_mm"], translations[index:index+2].max(axis=0), atol=1e-14)
    boxes = [np.asarray(p["bounds_xyz_mm"]) for p in cover["pieces"]]
    for x in [-15., 0., 12., 25., 50., 75., 90., 100., 125.]:
        u = np.array([np.interp(x, chart["reference_stations_mm"], translations[:, j]) for j in range(3)])
        for y, z in product([-5., 5.], [-6., 6.]):
            mapped = np.array([x, y, z])+u
            assert any(np.all(mapped >= box[:, 0]) and np.all(mapped <= box[:, 1]) for box in boxes)


def test_distinct_segment_and_endpoint_rotation_bounds_keep_material_and_nearby_neighbor(kernels):
    chart, extent, geometry, _guard, _timber, smooth, *_ = source_fixture(kernels)
    chart["reference_stations_mm"] = [0., 25., 75., 100.]
    chart["node_reference_centers_xyz_mm"] = [[x, 0., 0.] for x in chart["reference_stations_mm"]]
    chart["node_dof_indices"] = np.arange(24).reshape(4, 6).tolist()
    q = np.zeros((4, 6))
    angles = np.array([0., 0., .1, .1])
    q[:, 3:] = 1000.*np.column_stack((angles, np.zeros((4, 2))))@np.asarray(chart["storage_basis_columns_xyz"])
    q = q.ravel()
    guard = neighbors.inverse.TrialDomain("synthetic", chart, extent, 24, kernels[1])
    local = neighbors.local_reference_box("synthetic", chart, extent, geometry, smooth)
    bound = guard.bound(q)
    cover = neighbors.piece_enclosures(chart, q, extent, bound, local)
    factors = [p["rotation_factor_bound"] for p in cover["pieces"]]
    expected = [bound["rigid_endpoint_extensions"][0]["rigid_endpoint_extension_L"],
        *(r["absolute_geodesic_angle_upper_rad"] for r in bound["segments"]),
        bound["rigid_endpoint_extensions"][1]["rigid_endpoint_extension_L"]]
    expected[1:4] = [2.*np.sin(a/2.) for a in expected[1:4]]
    np.testing.assert_allclose(factors, expected, rtol=0., atol=0.)
    assert factors[0] == factors[1] == 0. and factors[3] > .09 and factors[4] > .09
    for x in [50., 90., 125.]:
        angle = np.interp(x, chart["reference_stations_mm"], angles)
        mapped = np.array([x, 0., 0.])+Rotation.from_rotvec([angle, 0., 0.]).apply([0., -5., -6.])
        assert mapped[2] < -6.
        assert any(np.all(mapped >= np.asarray(p["bounds_xyz_mm"])[:, 0]) and np.all(mapped <= np.asarray(p["bounds_xyz_mm"])[:, 1]) for p in cover["pieces"])
        neighbor = {"owner_id": "nearby", "q_canonical_sha256": cover["q_canonical_sha256"],
            "complete_reference_axial_box_covered": True, "pieces": [{"bounds_xyz_mm": np.column_stack((mapped-1e-4, mapped+1e-4)).tolist()}]}
        assert not neighbors.separate_piece_covers(cover, neighbor)["excluded_by_strict_separation_of_every_covering_piece_pair"]


def test_intersected_native_source_box_removes_virtual_corners_below_real_horizontal_cut(kernels):
    chart, extent, geometry, _guard, _timber, smooth, *_ = source_fixture(kernels, rotated=True)
    reference, cq = smooth.reference, smooth.reference.cq
    cut = geometry.shape.intersect(cq.Solid.makeBox(1000., 1000., 1000., cq.Vector(-500., -500., 0.)))
    cut, _ = kernels[4].strict_solid(cut, reference)
    geometry = reference.ReferenceSolidDistance(cut, owner_id="synthetic", source_identity=geometry.source_identity)
    native = cut.BoundingBox()
    world_box = np.array([[native.xmin, native.xmax], [native.ymin, native.ymax], [native.zmin, native.zmax]])
    extent["bounds_xyz_mm"] = (world_box+[-100., 100.]).tolist()
    extent["source_identity"].update({"topology_sha256": geometry.topology_sha256, "genuine_cached_solid_bounds_xyz_mm": world_box.tolist()})
    local = neighbors.local_reference_box("synthetic", chart, extent, geometry, smooth)
    q = np.zeros(12)
    guard = neighbors.inverse.TrialDomain("synthetic", chart, extent, 12, kernels[1])
    cover = neighbors.piece_enclosures(chart, q, extent, guard.bound(q), local)
    assert world_box[2, 0] == pytest.approx(0., abs=1e-8)
    start, basis = np.asarray(chart["reference_start_xyz_mm"]), np.asarray(local["chart_basis_columns_xyz"])
    uncut_minimum = min((start+np.asarray(list(product(*p["source_local_piece_bounds_mm"])))@basis.T)[:, 2].min() for p in cover["pieces"])
    assert uncut_minimum < -.1
    assert min(p["reference_piece_world_bounds_xyz_mm"][2][0] for p in cover["pieces"]) >= -1.01e-6
    for vertex in cut.Vertices():
        point = np.array(vertex.toTuple())
        assert any(np.all(point >= np.asarray(p["bounds_xyz_mm"])[:, 0]) and np.all(point <= np.asarray(p["bounds_xyz_mm"])[:, 1]) for p in cover["pieces"])


def distance_fixture(kernels, kind="separated"):
    smooth = kernels[3]
    cq, reference = smooth.reference.cq, smooth.reference
    first = cq.Solid.makeBox(1., 1., 1.)
    if kind == "contained": second = cq.Solid.makeBox(.1, .1, .1, cq.Vector(.2, .2, .2))
    elif kind == "overlap": second = cq.Solid.makeBox(1., 1., 1., cq.Vector(.5, .5, .5))
    elif kind == "touch": second = cq.Solid.makeBox(1., 1., 1., cq.Vector(1., 0., 0.))
    elif kind == "curved":
        first = cq.Solid.makeCylinder(1., 1.)
        second = cq.Solid.makeCylinder(2., 1., cq.Vector(6., 8., 0.))
    else: second = cq.Solid.makeBox(1., 1., 1., cq.Vector(4., 5., 0.))
    geometries = [reference.ReferenceSolidDistance(shape, owner_id=owner,
        source_identity={"finished_raw_file_path": owner+".brep", "finished_raw_file_sha256": "source-"+owner})
        for owner, shape in [("first", first), ("second", second)]]
    return geometries, smooth


@pytest.mark.parametrize("kind,expected", [("separated", 5.), ("contained", 0.), ("overlap", 0.), ("touch", 0.), ("curved", 7.)])
def test_genuine_native_reference_pair_minimum_matches_independent_analytic_solids(kernels, kind, expected):
    geometries, smooth = distance_fixture(kernels, kind)
    result = neighbors.reference_pair_distance(*geometries, smooth)
    assert result["minimum_reference_distance_mm"] == pytest.approx(expected, abs=1e-7)
    assert result["native_deflection_mm"] == 1e-7 and result["numerical_padding_mm"] == 1e-6
    assert result["formal_interval_or_roundoff_certificate"] is False and result["minimum_witnesses"]
    for side, geometry in zip(["first", "second"], geometries, strict=True):
        assert result[side] == geometry.owner_id
        assert result[side+"_source_geometry"] == {**geometry.source_identity, "topology_sha256": geometry.topology_sha256}
        assert smooth.reference.brep_sha(geometry.shape) == geometry.shape_sha256
    assert result["record_canonical_sha256"] == neighbors.canonical_sha({k: v for k, v in result.items() if k != "record_canonical_sha256"})


@pytest.mark.parametrize("failure", ["type", "owner", "topology", "shape", "padding"])
def test_reference_minimum_rejects_foreign_or_changed_native_sources(kernels, failure):
    geometries, smooth = distance_fixture(kernels)
    if failure == "type": geometries[1] = geometries[1].shape
    if failure == "owner": geometries[1].owner_id = "first"
    if failure == "topology": geometries[1].topology["changed"] = True
    if failure == "shape": geometries[1].shape = smooth.reference.cq.Solid.makeBox(3., 4., 5.)
    with pytest.raises(ValueError): neighbors.reference_pair_distance(*geometries, smooth, numerical_padding_mm=0. if failure == "padding" else 1e-6)


def motion_fixture(distance, side, translation, *, rotation=0., padding=1e-6):
    return {"owner_id": distance[side], "q_canonical_sha256": "same-state", "complete_reference_axial_box_covered": True,
        "coarse_enclosure": {"source_geometry": distance[side+"_source_geometry"]},
        "pieces": [{"translation_component_min_mm": translation, "translation_component_max_mm": translation,
            "rotation_displacement_norm_bound_mm": rotation, "numerical_padding_mm": padding}]}


def test_whole_material_motion_bound_uses_norm_and_worst_piece_not_signed_components(kernels):
    geometries, smooth = distance_fixture(kernels)
    distance = neighbors.reference_pair_distance(*geometries, smooth)
    cover = motion_fixture(distance, "first", [-3., 4., 0.], rotation=2.)
    cover["pieces"].append({"translation_component_min_mm": [-.1, -.2, -.3], "translation_component_max_mm": [.1, .2, .3],
        "rotation_displacement_norm_bound_mm": .5, "numerical_padding_mm": 1e-6})
    result = neighbors.cover_motion_bound(cover)
    assert result["maximum_material_displacement_bound_mm"] == pytest.approx(7.000001, abs=1e-14)
    assert result["witness_piece_index"] == 0
    assert result["all_piece_displacement_bounds_mm"] == pytest.approx([7.000001, np.sqrt(.14)+.500001])
    cover["pieces"].reverse()
    assert neighbors.cover_motion_bound(cover)["witness_piece_index"] == 1


@pytest.mark.parametrize("lo,hi", [([-1., -4., -6.], [3., 2., 5.]),
    ([-6., -1., -4.], [5., 3., 2.]), ([-3., -2., -5.], [1., 4., 6.])])
def test_motion_norm_keeps_asymmetric_mixed_sign_worst_corner_in_every_axis(kernels, lo, hi):
    geometries, smooth = distance_fixture(kernels)
    distance = neighbors.reference_pair_distance(*geometries, smooth)
    cover = motion_fixture(distance, "first", lo)
    cover["pieces"][0]["translation_component_max_mm"] = hi
    result = neighbors.cover_motion_bound(cover)
    assert result["maximum_material_displacement_bound_mm"] == pytest.approx(np.sqrt(61.)+1e-6, abs=1e-14)
    assert result["witness_piece_index"] == 0


def test_asymmetric_translation_interval_keeps_genuine_diagonal_gap_closed_by_upper_motion(kernels):
    geometries, smooth = distance_fixture(kernels)
    distance = neighbors.reference_pair_distance(*geometries, smooth)
    first = motion_fixture(distance, "first", [-1., -2., 0.])
    first["pieces"][0]["translation_component_max_mm"] = [3., 4., 0.]
    second = motion_fixture(distance, "second", [0., 0., 0.])
    result = neighbors.distance_motion_screen(distance, first, second)
    np.testing.assert_array_equal(np.array([1., 1., 0.])+[3., 4., 0.], [4., 5., 0.])
    assert result["own_motion_bounds"][0]["maximum_material_displacement_bound_mm"] == 5.+1e-6
    assert result["minimum_reference_distance_minus_padding_and_both_motion_bounds_mm"] == pytest.approx(-3e-6, abs=1e-14)
    assert result["excluded_by_strict_reference_distance_minus_motion"] is False


@pytest.mark.parametrize("offset", [-1., 0., 1.])
def test_triangle_screen_keeps_exact_touch_and_negative_margin_and_requires_both_motion_bounds(kernels, offset):
    geometries, smooth = distance_fixture(kernels)
    padding = 1./1024.
    distance = neighbors.reference_pair_distance(*geometries, smooth, numerical_padding_mm=padding)
    first = motion_fixture(distance, "first", [1., 0., 0.], padding=padding)
    second = motion_fixture(distance, "second", [4.-3.*padding+offset*padding, 0., 0.], padding=padding)
    result = neighbors.distance_motion_screen(distance, first, second)
    assert result["minimum_reference_distance_minus_padding_and_both_motion_bounds_mm"] == -offset*padding
    assert result["excluded_by_strict_reference_distance_minus_motion"] is (offset < 0.)
    assert result["reference_distance_record_canonical_sha256"] == neighbors.canonical_sha(distance)


@pytest.mark.parametrize("failure", ["seal", "owner", "source", "state", "incomplete", "empty", "translation", "rotation", "padding"])
def test_distance_motion_screen_rejects_wrong_sources_state_and_invalid_motion(kernels, failure):
    geometries, smooth = distance_fixture(kernels)
    distance = neighbors.reference_pair_distance(*geometries, smooth)
    first = motion_fixture(distance, "first", [0., 0., 0.])
    second = copy.deepcopy(motion_fixture(distance, "second", [0., 0., 0.]))
    if failure == "seal": distance["minimum_reference_distance_mm"] += 1.
    if failure == "owner": second["owner_id"] = "foreign"
    if failure == "source": second["coarse_enclosure"]["source_geometry"]["finished_raw_file_sha256"] = "foreign"
    if failure == "state": second["q_canonical_sha256"] = "foreign"
    if failure == "incomplete": second["complete_reference_axial_box_covered"] = False
    if failure == "empty": second["pieces"] = []
    if failure == "translation": second["pieces"][0]["translation_component_max_mm"] = [-1., 0., 0.]
    if failure == "rotation": second["pieces"][0]["rotation_displacement_norm_bound_mm"] = -1.
    if failure == "padding": second["pieces"][0]["numerical_padding_mm"] = 0.
    with pytest.raises(ValueError): neighbors.distance_motion_screen(distance, first, second)


def cover_fixture(owner, x_intervals, *, axis=0):
    pieces = []
    for interval in x_intervals:
        box = [[-1., 1.] for _ in range(3)]
        box[axis] = list(interval)
        pieces.append({"bounds_xyz_mm": box})
    return {"owner_id": owner, "q_canonical_sha256": "same-state", "complete_reference_axial_box_covered": True, "pieces": pieces}


@pytest.mark.parametrize("second,expected_gap,expected_count", [([(4., 5.), (6., 7.)], 3., 0),
    ([(4., 5.), (10.5, 12.)], -.5, 1), ([(1., 2.)], 0., 1), ([(1.+1e-9, 2.)], 1e-9, 0)])
@pytest.mark.parametrize("axis", [0, 1, 2])
def test_whole_union_pair_requires_strict_separation_of_every_piece_pair(second, expected_gap, expected_count, axis):
    first = cover_fixture("first", [(0., 1.), (10., 11.)], axis=axis)
    result = neighbors.separate_piece_covers(first, cover_fixture("second", second, axis=axis))
    assert result["cover_piece_pair_count"] == 2*len(second)
    assert result["minimum_over_piece_pairs_of_maximum_axis_separation_mm"] == pytest.approx(expected_gap, abs=1e-15)
    assert result["nonseparated_piece_pair_count"] == expected_count
    assert result["excluded_by_strict_separation_of_every_covering_piece_pair"] is (expected_count == 0)
    assert result["minimum_witness_piece_indices"] == ([1, 1] if expected_count == 1 and len(second) == 2 else [0, 0])
    witness = [-2., -2., -2.]
    witness[axis] = expected_gap
    assert result["minimum_witness_axis_separation_mm"] == pytest.approx(witness, abs=1e-15)
    assert result["overlap_is_not_detected_contact_or_collision"]


@pytest.mark.parametrize("failure", ["same_owner", "foreign_q", "incomplete", "empty", "nonfinite", "backwards", "wrong_shape"])
def test_pair_screen_rejects_unbound_or_invalid_piece_covers(failure):
    first, second = cover_fixture("first", [(0., 1.)]), cover_fixture("second", [(3., 4.)])
    if failure == "same_owner": second["owner_id"] = "first"
    if failure == "foreign_q": second["q_canonical_sha256"] = "foreign"
    if failure == "incomplete": second["complete_reference_axial_box_covered"] = False
    if failure == "empty": second["pieces"] = []
    if failure == "nonfinite": second["pieces"][0]["bounds_xyz_mm"][0][0] = np.nan
    if failure == "backwards": second["pieces"][0]["bounds_xyz_mm"][0] = [4., 3.]
    if failure == "wrong_shape": second["pieces"][0]["bounds_xyz_mm"] = [[3., 4.]]
    with pytest.raises(ValueError): neighbors.separate_piece_covers(first, second)


@pytest.mark.parametrize("failure", ["seal", "local_owner", "local_chart", "local_extent", "local_basis", "local_nonfinite",
    "local_backwards", "foreign_bound", "foreign_q", "changed_chart", "changed_extent", "piece_padding"])
def test_piece_cover_rejects_source_domain_state_and_native_record_mismatches(kernels, failure):
    chart, extent, geometry, guard, _timber, smooth, *_ = source_fixture(kernels)
    local = neighbors.local_reference_box("synthetic", chart, extent, geometry, smooth)
    q = np.zeros(12)
    bound = guard.bound(q)
    if failure == "seal": local["native_local_bounds_mm"][0][0] -= 1.
    if failure == "local_owner": local["owner_id"] = "foreign"
    if failure == "local_chart": local["row_canonical_sha256"] = "foreign"
    if failure == "local_extent": local["extent_canonical_sha256"] = "foreign"
    if failure == "local_basis": local["chart_basis_columns_xyz"][1][1] += 1.
    if failure == "local_nonfinite": local["padded_local_bounds_mm"][0][0] = np.nan
    if failure == "local_backwards": local["padded_local_bounds_mm"][0] = [100., 0.]
    if failure.startswith("local_") and failure != "local_nonfinite":
        local["record_canonical_sha256"] = neighbors.canonical_sha({k: v for k, v in local.items() if k != "record_canonical_sha256"})
    if failure == "foreign_bound": bound["owner_id"] = "foreign"
    if failure == "foreign_q": q[0] += 1.
    if failure == "changed_chart": chart["reference_start_xyz_mm"][0] += 1.
    if failure == "changed_extent": extent["bounds_xyz_mm"][0][0] -= 1.
    with pytest.raises(ValueError):
        neighbors.piece_enclosures(chart, q, extent, bound, local, numerical_padding_mm=0. if failure == "piece_padding" else 1e-6)


@pytest.mark.parametrize("failure", ["type", "owner", "topology", "source", "padding", "axis"])
def test_native_reference_box_rejects_foreign_sources_and_invalid_rigid_queries(kernels, failure):
    chart, extent, geometry, _guard, _timber, smooth, *_ = source_fixture(kernels)
    if failure == "type": geometry = geometry.shape
    if failure == "owner": extent["owner_id"] = "foreign"
    if failure == "topology": extent["source_identity"]["topology_sha256"] = "foreign"
    if failure == "source": extent["source_identity"]["finished_raw_file_sha256"] = "foreign"
    if failure == "axis": chart["reference_axis_xyz"] = [2., 0., 0.]
    with pytest.raises(ValueError):
        neighbors.local_reference_box("synthetic", chart, extent, geometry, smooth,
            numerical_padding_mm=0. if failure == "padding" else 1e-6)


@pytest.mark.parametrize("failure", [None, "intake_before", "method_before", "method_after", "producer_after", "case", "q", "order", "version"])
@pytest.mark.parametrize("neighbor_mode", ["distance", "piece"])
def test_current_neighbor_run_binds_all_sources_and_132_own_covers_with_all1386_pair_decisions(monkeypatch, tmp_path, kernels, failure, neighbor_mode):
    cases, _measure, domains, record, _bridge = current_fixture(monkeypatch, tmp_path, kernels,
        diagonal_neighbor=neighbor_mode == "distance", piece_neighbor=neighbor_mode == "piece")
    producer = tmp_path/"neighbor.py"
    producer.write_text("current neighbor producer\n")
    monkeypatch.setattr(neighbors, "OWN", producer)
    monkeypatch.setattr(neighbors, "LOADED_SHA", neighbors.current.sha(producer))
    expected = {p.name: neighbors.current.sha(p) for p in tmp_path.iterdir() if p.is_file()}
    expected[neighbors.scope.DOMAIN_SNAPSHOT] = neighbors.current.sha(tmp_path/neighbors.scope.DOMAIN_SNAPSHOT)
    if failure == "intake_before": (tmp_path/"intake-only.py").write_text("changed before queries\n")
    if failure == "method_before": (tmp_path/"method-only.py").write_text("changed before queries\n")
    if failure == "case": cases[4][0]["state_id"] = "foreign"
    if failure == "q": cases[4][1]["response"]["q"][0] += 1.
    if failure == "order": cases.reverse()
    if failure == "version": monkeypatch.setattr(neighbors, "version", lambda _name: "foreign")
    boxes, covers, pairs, verifies = [], [], [], []
    local_original, cover_original, pair_original, verify_original = neighbors.local_reference_box, neighbors.piece_enclosures, neighbors.separate_piece_covers, neighbors.current.verify
    def local_box(*args, **kwargs):
        result = local_original(*args, **kwargs)
        boxes.append((copy.deepcopy(args[1]), copy.deepcopy(args[2]), result))
        return result
    def cover(chart, q, extent, bound, local, **kwargs):
        result = cover_original(chart, q, extent, bound, local, **kwargs)
        covers.append((extent["owner_id"], q.copy(), result))
        return result
    def pair(first, second):
        result = pair_original(first, second)
        pairs.append((first, second, result))
        if len(pairs) == 1386 and failure in ["method_after", "producer_after"]:
            (tmp_path/("method-only.py" if failure == "method_after" else "neighbor.py")).write_text("changed during final screen\n")
        return result
    def verify(pins):
        verifies.append(copy.deepcopy(pins))
        verify_original(pins)
    monkeypatch.setattr(neighbors, "local_reference_box", local_box)
    monkeypatch.setattr(neighbors, "piece_enclosures", cover)
    monkeypatch.setattr(neighbors, "separate_piece_covers", pair)
    monkeypatch.setattr(neighbors.current, "verify", verify)
    if failure:
        with pytest.raises(ValueError): neighbors.run()
        if failure.endswith("_after"): assert len(pairs) == 1386
        else: assert not boxes and not covers and not pairs
        return
    result = neighbors.run()
    assert len(result["possible_pair_reference_distances"]) == 1
    native_distance = result["possible_pair_reference_distances"][0]
    assert (native_distance["first"], native_distance["second"]) == ("own-20", "own-21")
    assert native_distance["minimum_reference_distance_mm"] == pytest.approx(np.sqrt(.08) if neighbor_mode == "distance" else 10., abs=1e-8)
    assert result["source_sha256"] == expected == verifies[-1] == verifies[-2]
    assert len(boxes) == len(result["source_local_reference_boxes"]) == 22
    assert len(covers) == result["fresh_current_bound_count"] == 132
    assert len(pairs) == 1386
    assert result["source_local_reference_boxes"] == [r for _, _, r in boxes]
    saved = domains["current_diagnostic_ambient_injectivity"]
    assert {r["owner_id"] for r in result["source_local_reference_boxes"]} == set(saved["charts"])
    for chart, extent, local in boxes:
        assert chart == saved["charts"][local["owner_id"]] and extent == saved["extents"][local["owner_id"]]
    for case_index, row in enumerate(result["cases"]):
        q = np.r_[cases[case_index][1]["response"]["q"], np.zeros(100)]
        own_covers = covers[22*case_index:22*(case_index+1)]
        assert row["case_id"] == neighbors.inverse.component.SEQUENCE[case_index] and row["state_id"] == f"state-{case_index}"
        assert row["own_piece_covers"] == [r for _, _, r in own_covers]
        assert row["full_diagnostic_q_canonical_sha256"] == neighbors.canonical_sha(q.tolist())
        for owner, observed_q, value in own_covers:
            np.testing.assert_array_equal(observed_q, q)
            assert value["owner_id"] == owner and value["row_canonical_sha256"] == neighbors.canonical_sha(saved["charts"][owner])
        assert [r["coarse_enclosure"] for _, _, r in own_covers] == record["cases"][case_index]["containing_deformed_boxes"]
        expected_remaining, expected_new = 0, 0
        for screen, old, (first, second, observed) in zip(row["all231_pair_screens"], record["cases"][case_index]["all231_pair_screens"], pairs[231*case_index:231*(case_index+1)], strict=True):
            assert (screen["first"], screen["second"]) == (first["owner_id"], second["owner_id"]) == (old["first"], old["second"])
            scores = [max(max(a[0]-b[1], b[0]-a[1]) for a, b in zip(pa["bounds_xyz_mm"], pb["bounds_xyz_mm"], strict=True))
                for pa, pb in product(first["pieces"], second["pieces"])]
            assert observed["minimum_over_piece_pairs_of_maximum_axis_separation_mm"] == min(scores)
            assert observed["excluded_by_strict_separation_of_every_covering_piece_pair"] is all(s > 0. for s in scores)
            assert screen["registered_source_pair"] == old["registered_source_pair"]
            excluded = old["excluded_by_strict_containing_box_separation"] or all(s > 0. for s in scores)
            if (screen["first"], screen["second"]) == ("own-20", "own-21"):
                assert not old["excluded_by_strict_containing_box_separation"]
                assert old["possible_new_neighbor_requiring_own_feature_coverage"]
                angle = .09 if neighbor_mode == "distance" else .1
                expected_motion = (0. if neighbor_mode == "distance" else 10.)+2.*np.sin(angle/2.)*np.sqrt(2.)+1e-6
                expected_gap = (np.sqrt(.08) if neighbor_mode == "distance" else 10.)-1e-6-2.*expected_motion
                motion = screen["source_distance_motion_screen"]
                assert motion["minimum_reference_distance_minus_padding_and_both_motion_bounds_mm"] == pytest.approx(expected_gap, abs=1e-5)
                assert motion["excluded_by_strict_reference_distance_minus_motion"] is (neighbor_mode == "distance")
                assert motion["reference_distance_record_canonical_sha256"] == neighbors.canonical_sha(native_distance)
                if neighbor_mode == "distance":
                    assert not excluded and expected_gap > .02
                else:
                    assert expected_gap < -10. and all(s > 5.3 for s in scores)
                    assert observed["excluded_by_strict_separation_of_every_covering_piece_pair"] is True
                excluded = True
            else: assert screen["source_distance_motion_screen"] is None
            assert screen["excluded_by_any_source_bound_screen"] is excluded
            remaining = not excluded and not old["registered_source_pair"]
            assert screen["remaining_possible_new_neighbor"] is remaining
            expected_remaining += remaining
            expected_new += old["possible_new_neighbor_requiring_own_feature_coverage"] and excluded
        assert row["remaining_possible_new_neighbor_count"] == expected_remaining
        assert row["newly_excluded_possible_neighbor_count"] == expected_new
    assert result["tool_versions"] == neighbors.TOOL_VERSIONS
    assert result["saved_poses_only_not_trial_state_neighbor_coverage"] is True
    assert result["contact_force_or_frame_equilibrium_or_native_FEA_performed"] is False
    assert result["physical_stiffness_or_demand_or_strength_qualified"] is False
    assert result["structural_acceptance"] is False
