"""Compare archived replay values without weakening engineering acceptance gates."""
import math

import numpy as np

from fea import horizontal_panel_frame as frame


def gamma(operations):
    """Standard binary64 forward-error factor n*u/(1-n*u)."""
    nu = operations*2.**-53
    return nu/(1.-nu)


def bounded(expected, actual, radius):
    assert type(expected) is type(actual) is float
    assert math.isfinite(expected) and math.isfinite(actual)
    assert abs(expected-actual) <= radius, (expected, actual, radius)


def assert_stress_replay(expected, actual):
    """Only computed local stresses may round; native witnesses remain exact."""
    assert expected.keys() == actual.keys()
    assert {k: v for k, v in expected.items() if k != 'groups'} == {k: v for k, v in actual.items() if k != 'groups'}
    assert len(expected['groups']) == len(actual['groups'])
    for saved, replay in zip(expected['groups'], actual['groups'], strict=True):
        assert saved.keys() == replay.keys()
        computed_group = ('extrema', 'axes_xyz') if saved.get('element_type') == 'S8' else ('extrema',)
        assert {k: v for k, v in saved.items() if k not in computed_group} == {k: v for k, v in replay.items() if k not in computed_group}
        if saved.get('element_type') == 'S8':
            assert np.shape(saved['axes_xyz']) == np.shape(replay['axes_xyz']) == (3, 3)
            for saved_axis, replay_axis in zip(saved['axes_xyz'], replay['axes_xyz'], strict=True):
                for a, b in zip(saved_axis, replay_axis, strict=True):
                    bounded(a, b, 8*max(math.ulp(a), math.ulp(b)))
        assert saved['extrema'].keys() == replay['extrema'].keys()
        basis = np.abs(saved['axes_xyz'])
        basis_delta = np.abs(np.array(saved['axes_xyz'])-replay['axes_xyz'])
        largest_basis = np.maximum(basis, np.abs(replay['axes_xyz']))
        for field, extrema in saved['extrema'].items():
            assert extrema.keys() == replay['extrema'][field].keys()
            for label, witness in extrema.items():
                other = replay['extrema'][field][label]
                assert witness.keys() == other.keys()
                computed = ('value_mpa', 'local_tensor_mpa')
                assert {k: v for k, v in witness.items() if k not in computed} == {k: v for k, v in other.items() if k not in computed}
                xx, yy, zz, xy, xz, yz = witness['global_components_mpa']
                tensor = np.abs([[xx, xy, xz], [xy, yy, yz], [xz, yz, zz]])
                # Two length-three matrix products: gamma_6*|B|*|S|*|B.T|.
                # Both evaluations can round in opposite directions.
                radius = 2*gamma(6)*(largest_basis@tensor@largest_basis.T)
                # S8 axes are themselves normalized via a platform norm.
                # Propagate their verified few-ULP difference, including both
                # appearances of B; raw lumber axes still compare exactly.
                radius += basis_delta@tensor@largest_basis.T+largest_basis@tensor@basis_delta.T
                assert np.shape(witness['local_tensor_mpa']) == np.shape(other['local_tensor_mpa']) == (3, 3)
                for i in range(3):
                    for j in range(3):
                        bounded(witness['local_tensor_mpa'][i][j], other['local_tensor_mpa'][i][j], radius[i, j])
                if field.startswith('normal_'):
                    i = saved['axis_labels'].index(field.removeprefix('normal_'))
                    value_radius = radius[i, i]
                elif field in ('shear_01', 'shear_02', 'shear_12'):
                    i, j = map(int, field[-2:])
                    value_radius = radius[i, j]
                else:
                    assert field == 'shear_on_axis_0_plane_magnitude'
                    value_radius = math.hypot(radius[0, 1], radius[0, 2])+8*max(math.ulp(witness['value_mpa']), math.ulp(other['value_mpa']))
                bounded(witness['value_mpa'], other['value_mpa'], value_radius)


def assert_replay_value(expected, actual, key, record=None, data=None):
    if key == 'load_work_nmm':
        displacements = frame.panel_kernel.read_blocks(data)['displacements']
        products = [abs(f*u) for node, forces in record['loads'].items()
                    for f, u in zip(forces, displacements[int(node)], strict=True)]
        # Three-component dot products plus the outer sum, with cancellation
        # bounded by sum(abs(F_i*u_i)), not by the possibly tiny final work.
        radius = 2*gamma(len(record['loads'])+3)*math.fsum(products)
        bounded(expected, actual, radius)
        return
    if key in ('maximum_panel_displacement_mm', 'maximum_timber_displacement_mm', 'maximum_node_displacement_mm'):
        bounded(expected, actual, 8*max(math.ulp(expected), math.ulp(actual)))
        return
    if key != 'connector_forces':
        assert expected == actual, key
        return
    assert expected.keys() == actual.keys(), key
    for name, saved in expected.items():
        replay = actual[name]
        assert saved.keys() == replay.keys(), name
        for field, value in saved.items():
            if field != 'force_magnitude_n':
                assert value == replay[field], (name, field)
                continue
            other = replay[field]
            assert type(value) is type(other) is float, (name, field)
            assert math.isfinite(value) and math.isfinite(other), (name, field)
            # A 3-vector norm has three products, two additions and a sqrt.
            # Eight binary64 ULPs conservatively cover platform reduction/FMA
            # rounding across those operations. The signed components, all
            # other fields and every engineering gate remain exactly equal.
            radius = 8*max(math.ulp(value), math.ulp(other))
            assert abs(value-other) <= radius, (name, field, value, other)
