"""Conditional APA axial-compression reference for a bottom-supported kicker.

A uniform full-thickness edge resultant is required. This is not local hold,
partial-contact, stability, combined-load or floor resistance qualification.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

LBF_N = 4.4482216152605
PRIMARY = 'https://wood.tcaup.umich.edu/lectures/2021/D510.pdf'
PRIMARY_SHA256 = 'b09fca5c358f16a598ed289cff46e7b515b783af4e5fb82919cc1af22155960a'
# APA D510F 2020, Table 10, printed pp28–29, 23/32 A-A/A-C, Group 1.
REFERENCES = {
    'parallel': {'compression_lbf_per_ft': 4800., 'bending_lbf_in_per_ft': 775.,
                 'bending_stiffness_lbf_in2_per_ft': 320000.},
    'perpendicular': {'compression_lbf_per_ft': 2900., 'bending_lbf_in_per_ft': 455.,
                      'bending_stiffness_lbf_in2_per_ft': 90500.},
}
# Table 11 A-A/A-C compression and bending factors; no Structural I increase.
GROUP_FACTORS = {1: (1., 1.), 2: (.73, .70), 3: (.65, .70), 4: (.61, .67)}


def reference(vertical_n, *, panel_dead_n, axis='perpendicular', species_group=1):
    """Return required uniformly compressed width, not an approved contact length."""
    if (axis not in REFERENCES or species_group not in GROUP_FACTORS
            or not all(math.isfinite(v) and v >= 0 for v in (vertical_n, panel_dead_n))):
        raise ValueError('Require finite nonnegative loads and a supported axis/species group')
    compression_factor, bending_factor = GROUP_FACTORS[species_group]
    row = REFERENCES[axis]
    axial = row['compression_lbf_per_ft']*compression_factor*LBF_N/304.8
    bending = row['bending_lbf_in_per_ft']*bending_factor*LBF_N*25.4/304.8
    return {'species_group': species_group, 'stress_relative_to_strength_axis': axis,
            'vertical_applied_n': vertical_n, 'panel_dead_n': panel_dead_n,
            'total_vertical_n': vertical_n+panel_dead_n,
            'axial_compression_reference_n_per_mm_width': axial,
            'flatwise_bending_reference_nmm_per_mm_width': bending,
            'minimum_uniform_axial_width_mm': (vertical_n+panel_dead_n)/axial,
            'qualified_contact_length': False, 'qualified_for_design': False}


def report():
    # Gross panel, before holes, at the project's assumed 600 kg/m³ density.
    dead = 1219.2*225.*18.25625/1e9*600.*9.80665
    return {'candidate': 'round-structural-development',
            'scope': 'Nominal panel arithmetic; no current CAD geometry-match gate',
            'current_geometry_authenticated': False,
            'nominal_panel_mm': [1219.2, 225., 18.25625],
            'assumed_density_kg_m3': 600.,
            'dead_weight_scope': 'One gross plywood panel; hold/bolt/accessory weight excluded',
            'primary_source': PRIMARY, 'primary_pdf_sha256': PRIMARY_SHA256,
            'source_sha256': {str(Path(__file__).resolve().relative_to(Path.cwd())):
                hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
            'cases': [reference(2669., panel_dead_n=dead, axis=axis, species_group=group)
                      for group in GROUP_FACTORS for axis in REFERENCES],
            'reference_conditions': 'APA-marked A-C 23/32 category with selected species group; '
                'dry service below16% moisture, ordinary temperature, CD=1.0. No impact or '
                'Structural I increase. Gross uniform full-thickness axial compression only.',
            'kicker_resistance_qualified': False,
            'limits': 'Required axial width is a necessary reference under uniform stress, not '
                'proof of actual floor contact width or load spread from a hold. Local edge '
                'crushing/damage, gaps, eccentric contact, hold/T-nut transfer, holes, panel '
                'buckling, combined compression/bending and floor capacity remain separate.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.output.open('x') as stream:
        json.dump(report(), stream, indent=2, allow_nan=False)
        stream.write('\n')
