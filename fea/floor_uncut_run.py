"""Separate full-stock response under the accepted conditional no-slip support."""
import hashlib
import math
from pathlib import Path

from fea import current_response_run as native
from fea.current_response_materials import WOOD_E, df_l_no2_post_timber
from fea.floor_flush_run import face_contacts
from fea.floor_uncut_mesh import prepare_uncut
from mini_moonboard import compact_floor_uncut_frame as candidate
from scripts.compact_rail_study import bolt_properties as uniform_bolt_properties

ORIGINAL_SOURCES = native.source_hashes
POSTS = ('base_post_outer_left', 'base_post_outer_right')


def bolt_properties(connection):
    """Retain the declared seat analogy with each timber's own compression path."""
    result = uniform_bolt_properties(connection)
    if not any(name in POSTS for name in connection.members):
        return result
    lengths = candidate.EXPECTED_BEARING_LENGTHS_MM[connection.name]
    if not math.isclose(sum(lengths.values()), connection.grip, abs_tol=1.e-7):
        raise ValueError('Bolt seat paths must equal the actual wood grip')
    post_e = df_l_no2_post_timber()['constants'][0]
    area = result['washer_net_area_mm2']
    seat_compliance = sum(length / (.05 * (post_e if name in POSTS else WOOD_E) * area)
                          for name, length in lengths.items())
    steel_compliance = connection.grip / (200000. * math.pi * connection.diameter**2 / 4)
    result.update(axial_n_per_mm=1 / (steel_compliance + seat_compliance),
                  wood_seat_paths_mm=dict(lengths),
                  wood_seat_moduli_mpa={name: post_e if name in POSTS else WOOD_E for name in lengths})
    result['basis'] += (' Separate series wood-seat paths use 0.05 times each member longitudinal E; '
                        'this remains an assumed seat-compliance model, not measured joint stiffness.')
    return result


def sources():
    result = ORIGINAL_SOURCES()
    paths = native.repository_source_closure([Path(__file__), Path(candidate.__file__)])
    # The shared closure deliberately follows only fea/mini_moonboard modules.
    # Include the actual CLI and inherited bolt-property implementation too.
    paths += [Path('scripts/floor_uncut_case.py'), Path('scripts/compact_rail_study.py'),
              Path('scripts/clear_space_batch.py')]
    for source in paths:
        result[str(source.resolve().relative_to(Path.cwd()))] = hashlib.sha256(source.read_bytes()).hexdigest()
    return result


LOADED_SOURCES = sources()


def prepare(module, **kwargs):
    post = df_l_no2_post_timber()
    materials = dict(kwargs['materials'], timber_by_name={name: post['constants'] for name in POSTS},
                     post_timber_basis=post['basis'])
    structure, metadata = prepare_uncut(module, **dict(kwargs, materials=materials))
    for name in POSTS:
        structure.members[name]['record'].update(reference_override=dict(post['reference_override']),
                                                 elastic_modulus_psi=1_300_000.)
    return structure, metadata


def run(output, *, module=candidate, contact_stiffness_per_area=100., **kwargs):
    if module.KEY != candidate.KEY:
        raise ValueError('Require the separate full-stock candidate')
    if ORIGINAL_SOURCES() != native.LOADED_SOURCE_SHA256 or sources() != LOADED_SOURCES:
        raise ValueError('Restart full-stock runner after source changes')
    if 'member_contacts' in kwargs or 'clearance_monitors' in kwargs:
        raise ValueError('Full-stock contacts cannot be silently overridden')
    contacts = face_contacts(module, stiffness_per_area=contact_stiffness_per_area)
    old = native.source_hashes, native.LOADED_SOURCE_SHA256
    try:
        native.source_hashes = sources
        native.LOADED_SOURCE_SHA256 = LOADED_SOURCES
        return native.run(output, module=module, expected_candidate=candidate.KEY,
                          prepare_factory=prepare, member_contacts=contacts,
                          clearance_monitors=(), **kwargs)
    finally:
        native.source_hashes, native.LOADED_SOURCE_SHA256 = old
