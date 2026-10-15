"""Retain exact screw datums through an objective finite panel-port map.

The original projected ring lies on the recorded panel midsurface. Source
screw datums can differ slightly from that plane. Transport that complete
offset with two existing Kirchhoff point ports, preserving all derivatives.
The frozen v1 checker and its unchanged numerical gates remain the consumer.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from types import ModuleType

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
PRODUCER = {'path': 'scripts/eoere_panel_bulk_coupling.py',
            'sha256': '8efacb2503ae09795f3f9dc2d792bb4e61264c06bfdf1a51731c573f4560e79d'}


def context(pins):
    data = (ROOT/PRODUCER['path']).read_bytes()
    if hashlib.sha256(data).hexdigest() != PRODUCER['sha256'] or pins.get(PRODUCER['path'], PRODUCER['sha256']) != PRODUCER['sha256']:
        raise ValueError('frozen panel/bulk producer changed')
    pins[PRODUCER['path']] = PRODUCER['sha256']
    module = ModuleType('_eoere_verified_panel_bulk_producer'); module.__file__ = str(ROOT/PRODUCER['path'])
    exec(compile(data, module.__file__, 'exec'), module.__dict__)  # noqa: S102 - authenticated source buffer
    remaining = module.bootstrap(pins); gravity = remaining.bootstrap(pins); contact = gravity.bootstrap(pins)
    material = contact.bootstrap(pins); prior = material.bootstrap(pins); boot = prior.bootstrap(pins)
    return module, boot.producer(pins)


def install_point_port(api, producer, inputs, base, pins):
    """Add only the already-frozen pure point-port method to the private API."""
    namespace = dict(api.adapter.screw_port.__globals__)
    point_class = producer.class_subset(inputs['panel_adapter'], 'FinitePanelAdapter', ('point_port',), namespace, base, pins)
    api.adapter.point_port = point_class.point_port


def datum_port(panel, q, screw, target, ring_port, *, tangent=True):
    """Ring(q) + point(q,target) - point(q,ring reference)."""
    raw = ring_port(panel, q, screw, tangent=tangent)
    source = panel.point_port(q, target, tangent=tangent)
    origin = panel.point_port(q, raw['reference_position_xyz_mm'], tangent=tangent)
    keys = ('normal_xyz', 'normal_J_csr', 'normal_H_xyz_csr', 'axis_id', 'panel', 'receiver')
    result = {key: raw[key] for key in keys}
    result.update(position_xyz_mm=raw['position_xyz_mm']+source['position_xyz_mm']-origin['position_xyz_mm'],
                  reference_position_xyz_mm=np.asarray(target, dtype=float),
                  J_csr=raw['J_csr']+source['J_csr']-origin['J_csr'],
                  H_xyz_csr=tuple(a+b-c for a, b, c in zip(raw['H_xyz_csr'], source['H_xyz_csr'], origin['H_xyz_csr'], strict=True)) if tangent else None,
                  original_projected_ring_reference_xyz_mm=raw['reference_position_xyz_mm'],
                  kinematics='projected ring plus complete objective source-datum point-port difference')
    return result


def run(reference):
    pins = {}; producer, base = context(pins)
    inputs = json.loads(base.captured(reference, pins))
    producer.require(inputs['consumer_schema'] == 'eoere_panel_bulk_datum_consumer/v2', 'explicit source-datum consumer required')
    base.captured(inputs['v1_inputs'], pins)
    base.captured(inputs['saved_panel_row_comparison'], pins)
    for row in inputs['consumer_execution_sources']: base.captured(row, pins)
    producer.require(pins.get(str(OWN.relative_to(ROOT))) == LOADED_SHA, 'exact executing datum consumer required')
    stopped = json.loads(base.captured(inputs['stopped_v1'], pins))
    producer.require(stopped['terminal_exit_code'] == 1 and stopped['output_issued'] is False, 'preserved original failed datum gate required')
    for row in stopped['frozen_files']+[stopped['diagnostic']]: base.captured(row, pins)
    field = json.loads(base.captured(inputs['datum_source_field'], pins))
    sources = {row['id']: row for row in field['source_inputs']['hillman_rows']}
    producer.require(len(sources) == 66, 'all current source datums required')
    mapping = {}

    def mapped_methods(old_inputs, old_base, own_pins):
        api = producer.methods(old_inputs, old_base, own_pins)
        install_point_port(api, producer, old_inputs, old_base, own_pins)
        raw = api.adapter.screw_port
        def mapped(panel, q, screw, tangent=True):
            own = sources[screw['axis_id']]
            producer.require(screw == own['source_screw_descriptor'] and screw['panel'] == panel.geometry['name'], 'same exact source axis/panel/receiver required')
            result = datum_port(panel, q, screw, own['point_xyz_mm'], raw, tangent=tangent)
            record = {'source_point_xyz_mm': own['point_xyz_mm'],
                      'projected_ring_reference_xyz_mm': result['original_projected_ring_reference_xyz_mm'].tolist()}
            producer.require(screw['axis_id'] not in mapping or mapping[screw['axis_id']] == record, 'unchanged datum map on every control required')
            mapping[screw['axis_id']] = record
            return result
        api.adapter.screw_port = mapped
        return api

    # The frozen run function is unchanged; only its private methods factory
    # supplies the explicitly declared objective datum extension above.
    loader = base.private(inputs['definition_loader'], pins)
    namespace = {**vars(producer), 'methods': mapped_methods}
    run_method = loader.definitions(PRODUCER, ('run',), (), namespace, pins)
    result = run_method.run(reference)
    producer.require(set(mapping) == set(sources), 'complete 66-axis source-datum map required')
    result['schema'] = 'eoere_panel_bulk_coupling/v2'
    result['source_datum_mapping'] = mapping
    result['stopped_v1'] = inputs['stopped_v1']
    result['saved_panel_row_comparison'] = inputs['saved_panel_row_comparison']
    result['source_sha256'].update(pins)
    for path, digest in result['source_sha256'].items(): base.captured({'path': path, 'sha256': digest}, pins)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists(): raise ValueError('preserve issued datum-consumer evidence')
    reference = {'path': str(args.inputs.resolve().relative_to(ROOT)), 'sha256': hashlib.sha256(args.inputs.read_bytes()).hexdigest()}
    result = run(reference); args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True); stream.write('\n')
    print(json.dumps({'output': str(args.out), 'interfaces': len(result['interfaces']), 'spread_scenarios': 198}))


if __name__ == '__main__':
    main()
