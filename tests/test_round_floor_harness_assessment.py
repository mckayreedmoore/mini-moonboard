"""A force-only necessary bound must reject invalid loads, not certify contact."""
import math

import pytest

from fea.round_floor_harness_assessment import necessary_friction


def test_resultant_bound_scales_with_available_normal_force():
    assert necessary_friction(300, 2000) == pytest.approx(.15)
    assert necessary_friction(300, 1000) == pytest.approx(.30)
    assert necessary_friction(0, 1000) == 0
    for horizontal, normal in ((-1, 1), (1, 0), (1, -1), (math.nan, 1), (1, math.inf)):
        with pytest.raises(ValueError):
            necessary_friction(horizontal, normal)


def test_routing_must_match_candidate_and_manifest_bytes(tmp_path):
    import hashlib

    from fea.round_floor_harness_assessment import bind_candidate

    path = tmp_path/'wiring.json'
    path.write_text('recorded routing')
    wiring = {'round_bores': [{}]*32, 'segments': [{}]*131}
    floor = {'candidate': 'round-insert-development'}
    manifest = {'candidate': floor['candidate'], 'artifact_sha256': {
        'wiring.json': hashlib.sha256(path.read_bytes()).hexdigest()}}
    assert bind_candidate(floor, wiring, path, manifest) == floor['candidate']
    manifest['candidate'] = 'historical'
    with pytest.raises(ValueError, match='candidates differ'):
        bind_candidate(floor, wiring, path, manifest)
    manifest['candidate'] = floor['candidate']
    path.write_text('changed routing')
    with pytest.raises(ValueError, match='differs from candidate manifest'):
        bind_candidate(floor, wiring, path, manifest)
