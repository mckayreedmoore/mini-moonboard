"""Generate exact receiver geometry for selected spliced flush-top candidate."""
import argparse
import hashlib
import json
from pathlib import Path

from mini_moonboard import compact_spliced_flush_top as candidate
from scripts.compact_thick_geometry import build

HARDWARE_REFERENCE = Path('fea/results/compact-splice-study/a12-rear/geometry.json')


def resistance_bounds(current_hardware, reference):
    """Reuse a bound only when the complete same-name hardware record is unchanged."""
    reference_hardware = reference['hardware_by_name']
    reference_bounds = reference['hardware_resistance_bounds_by_name']
    if set(current_hardware) != set(reference_hardware) or set(current_hardware) != set(reference_bounds):
        raise ValueError('Historical resistance basis does not cover the current bolt set')
    for name, dimensions in current_hardware.items():
        if dimensions != reference_hardware[name]:
            raise ValueError(f'Historical hardware metadata differs for {name}')
    return {name: reference_bounds[name] for name in current_hardware}


def generate(output):
    """Build candidate CAD and record this thin adapter in source closure."""
    result = build(candidate)
    if result.get('candidate') != candidate.KEY:
        raise ValueError('Geometry builder returned wrong candidate')
    bolts = [connection for connection in candidate.connections() if connection.kind == 'bolt']
    result['hardware_by_name'] = {
        connection.name: candidate.bolt_dimensions(connection) for connection in bolts
    }
    reference = json.loads(HARDWARE_REFERENCE.read_text())
    result['hardware_resistance_bounds_by_name'] = resistance_bounds(
        result['hardware_by_name'], reference)
    for row in result['geometries_by_bolt_name'].values():
        row['bending_yield_psi'] = 90000.
    result['bolt_material_basis'] = {
        'specified_grade': 'SAE J429 Grade 5',
        'bending_yield_psi': 90000.,
        'references': ['docs/compact-half-inch-hardware.md', 'docs/compact-splice-hardware.md'],
    }
    result['splice_contact_datums'] = candidate.overlap_contact_datums()
    result['source_sha256'][str(HARDWARE_REFERENCE)] = hashlib.sha256(
        HARDWARE_REFERENCE.read_bytes()).hexdigest()
    source = Path(__file__).resolve()
    relative = str(source.relative_to(Path.cwd()))
    result['source_sha256'][relative] = hashlib.sha256(source.read_bytes()).hexdigest()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = generate(args.output)
    print({key: result[key] for key in ('candidate', 'receiver_fit_pass', 'header_depth_mm')})


if __name__ == '__main__':
    main()
