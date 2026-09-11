"""Compare named recalculated float fields while keeping other evidence exact."""
import copy
import math

import pytest


def assert_roundoff_equal(actual, expected, *, paths, rel=1e-12, abs=1e-14):
    """Only explicitly selected scalar/flat-list float fields receive tolerance.

    Callers retain their physical residual gates and authenticate archived bytes
    separately. This helper never changes the report used by those checks.
    """
    normalized = copy.deepcopy(actual)
    for path in paths:
        assert path, 'Select a numeric field, not the whole report'
        actual_parent, expected_parent = normalized, expected
        for key in path[:-1]:
            actual_parent, expected_parent = actual_parent[key], expected_parent[key]
        a, e = actual_parent[path[-1]], expected_parent[path[-1]]
        assert isinstance(a, list) == isinstance(e, list), path
        aa, ee = (a, e) if isinstance(e, list) else ([a], [e])
        assert aa and len(aa) == len(ee), path
        assert all(isinstance(v, float) and math.isfinite(v) for v in [*aa, *ee]), path
        assert a == pytest.approx(e, rel=rel, abs=abs), path
        actual_parent[path[-1]] = copy.deepcopy(e)
    assert normalized == expected
