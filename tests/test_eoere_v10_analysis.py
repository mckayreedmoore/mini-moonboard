"""Focused controls for versioned v10 census and physical hole routing."""
import ast

import pytest

from scripts import eoere_v10_analysis as method


def axis(row='far', identity='bolt', x=65.0875):
    return {'id': identity,'point_xyz_mm': [x,0,0],'direction_xyz': [0,0,1],'grip_mm': 38.1,
                'receivers': ['wood'],'attachments': [{'angle_id': 'angle','flange': 'beam','row': row,
                    'transverse': -1,'installed_bolt_axis_id': identity,'point': [x,0,38.1]}]}


def test_near_and_far_route_to_distinct_factory_degrees_of_freedom():
    assert method.row_port('beam',-1,'near')=='arm-x/near-plus'
    assert method.row_port('beam',-1,'far')=='arm-x/far-plus'
    assert method.row_port('post',1,'near')=='arm-z/near-minus'


def test_same_strip_near_and_far_are_distinct_installed_holes():
    method.verify_attachment_axes([axis(),axis('near','second',23.8125)],2)


def test_duplicate_factory_hole_is_rejected():
    with pytest.raises(ValueError,match='bound twice'):
        method.verify_attachment_axes([axis(),axis('far','second')],2)


def test_attachment_must_lie_on_shaft_and_external_face():
    value=axis();value['attachments'][0]['point'][0]+=1
    with pytest.raises(ValueError,match='off physical shaft'):
        method.verify_attachment_axes([value],1)


def test_unknown_factory_row_is_rejected():
    with pytest.raises(ValueError):method.row_port('beam',1,'middle')


def test_load_helper_is_explicitly_frozen():
    assert method.FROZEN_METHODS['scripts/eoere_load_parameters.py']=='83edcc05b778fc677204d1cc39597cd3e2a739f32de4b0f67ce0c2a051bf2772'
    method.verify_frozen_methods()


def test_changed_frozen_dependency_is_rejected(monkeypatch):
    monkeypatch.setattr(method,'sha',lambda _: 'changed')
    with pytest.raises(ValueError,match='frozen method changed'):
        method.verify_frozen_methods({'scripts/eoere_load_parameters.py':'expected'})


def test_generalized_source_retains_row_metadata_and_contact_laws():
    count={'shafts': 114,'ports': 108,'wood': 24,'fittings': 24,'walls': 140,'roles': 600,'bodies': 168}
    source=method.generalized_preparation_source(count)
    ast.parse(source)
    assert "r['source_row'] == hole['row']" in source
    assert "'installed_bolt_axis_id': binding[0]['axis_id'] if binding else None" in source
    assert 'ex.contact_bank(bodies, sorted(gross), panel_ids, q, p[\'parameters\'])' in source
    assert 'V10_SHAFTS' in source


def test_missing_or_ambiguous_source_hook_stops_transformation():
    with pytest.raises(ValueError):method.replace_once('same same','same','new')
