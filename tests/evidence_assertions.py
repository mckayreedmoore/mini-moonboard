"""Compare archived replay values without weakening engineering acceptance gates."""
import math


def assert_replay_value(expected, actual, key):
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
