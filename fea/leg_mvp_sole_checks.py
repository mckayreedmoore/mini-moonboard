"""Conditional relieved-foot contact and short-neck screens from native forces.

References retain dry Douglas Fir-Larch No. 2 base values used by the repository:
Fc-perpendicular 625 psi, Fb 900 psi and Fv 180 psi, without duration/size uplift.
A horizontal neck cuts oblique grain. These scalar reference comparisons do not
qualify notch concentration, rolling shear or perpendicular-to-grain tension.
"""
import numpy as np

PSI_MPA = 0.006894757293168361
REFERENCES = {'compression_mpa': 625*PSI_MPA, 'bending_mpa': 900*PSI_MPA,
              'shear_mpa': 180*PSI_MPA, 'off_grain_modulus_proxy_mpa': 80000*PSI_MPA}


def assess(report, sole_geometry):
    """Fit actual sampled opening, check clearance, and recover each neck wrench."""
    forces = report['physical_connection_forces']
    bearings = {row['name']: row for row in report['bearings']}
    stiffness = 4.*report['parameters']['stiffnesses']['floor']
    tolerance = sole_geometry.get('tolerance_mm', 1.)
    if not np.isfinite(stiffness) or stiffness <= 0 or tolerance < 0:
        raise ValueError('Require positive floor stiffness and nonnegative cut tolerance')
    results = {}
    for leg, geometry in sole_geometry['feet'].items():
        xmin, xmax, ymin, ymax = geometry['land_bounds_mm']
        relief = geometry['relief_mm']
        width, depth = xmax-xmin, ymax-ymin
        if min(width, depth, relief) <= 0:
            raise ValueError('Require positive land dimensions and relief')
        centre = np.array([(xmin+xmax)/2., (ymin+ymax)/2., relief])
        samples = [(name, row) for name, row in forces.items()
                   if row['first'] == leg and row['second'] == 'floor'
                   and 'scalar_normal' in row]
        if len(samples) < 3:
            raise ValueError('Need at least three noncollinear normal foot samples')
        coordinates = np.array([row['point'] for _, row in samples])
        if (np.any(coordinates[:, 0] < xmin-1.e-6) or np.any(coordinates[:, 0] > xmax+1.e-6)
                or np.any(coordinates[:, 1] < ymin-1.e-6) or np.any(coordinates[:, 1] > ymax+1.e-6)
                or np.any(abs(coordinates[:, 2]) > 1.e-6)):
            raise ValueError('Normal contacts must lie within the floor-level land')
        matrix = np.column_stack([np.ones(len(samples)), coordinates[:, :2]-centre[:2]])
        opening = np.array([bearings[name]['opening_mm'] for name, _ in samples])
        coefficients, _, rank, _ = np.linalg.lstsq(matrix, opening, rcond=None)
        if rank != 3 or not np.all(np.isfinite(coefficients)):
            raise ValueError('Foot opening plane needs finite noncollinear samples')
        residual = float(max(abs(matrix@coefficients-opening)))
        corners = np.array([[x, y, relief] for x in (xmin, xmax) for y in (ymin, ymax)])
        def extrapolate(points, coefficients=coefficients, centre=centre):
            return coefficients[0]+(points[:, :2]-centre[:2])@coefficients[1:]
        relief_corners = np.asarray(geometry['relieved_corners_xyz_mm'], dtype=float)
        if relief_corners.ndim != 2 or relief_corners.shape[1] != 3 or len(relief_corners) < 2 or not np.all(np.isfinite(relief_corners)):
            raise ValueError('Require finite relieved corner coordinates')
        if np.max(abs(relief_corners[:, 2]-relief)) > 1.e-6:
            raise ValueError('Relieved corners must use actual relief height')
        remaining_gap = relief_corners[:, 2]+extrapolate(relief_corners)-tolerance
        area = width*depth
        pressure = np.maximum(0., -extrapolate(corners))*stiffness/area
        resultant, moment = np.zeros(3), np.zeros(3)
        for row in forces.values():
            if row['first'] == leg and row['second'] == 'floor':
                force = np.array(row['force_on_first_xyz_n'])
                resultant += force
                moment += np.cross(np.array(row['point'])-centre, force)
        axial_stress = resultant[2]/area
        bending_stress = abs(moment[0])/(width*depth**2/6.)+abs(moment[1])/(depth*width**2/6.)
        shear_stress = 1.5*float(np.linalg.norm(resultant[:2]))/area
        # Conservative rectangular torsional stress estimate; not notch analysis.
        torsion_stress = 3.*abs(moment[2])/(min(width, depth)**2*max(width, depth))
        compression_peak = max(0., axial_stress+bending_stress)
        tension_peak = max(0., bending_stress-axial_stress)
        ratios = {
            'land_pressure': float(max(pressure))/REFERENCES['compression_mpa'],
            'neck_compression_envelope': compression_peak/REFERENCES['compression_mpa'],
            'neck_bending_reference': bending_stress/REFERENCES['bending_mpa'],
            'neck_shear_plus_torsion_reference': (shear_stress+torsion_stress)/REFERENCES['shear_mpa']}
        clearance_pass = bool(min(remaining_gap) > 0 and residual <= 1.e-5)
        results[leg] = {
            'land_area_mm2': area, 'normal_stiffness_n_per_mm': stiffness,
            'opening_plane_at_land_center_mm_and_slopes': coefficients.tolist(),
            'opening_fit_maximum_residual_mm': residual, 'opening_fit_passed': residual <= 1.e-5,
            'relieved_corner_remaining_gaps_mm': remaining_gap.tolist(),
            'relief_clearance_with_cut_tolerance_passed': clearance_pass,
            'land_corner_pressure_mpa': pressure.tolist(),
            'floor_resultant_xyz_n': resultant.tolist(), 'neck_top_moment_xyz_nmm': moment.tolist(),
            'neck_top_reference_xyz_mm': centre.tolist(),
            'neck_axial_compression_mpa': float(axial_stress),
            'neck_bending_stress_envelope_mpa': float(bending_stress),
            'neck_tension_envelope_mpa': float(tension_peak),
            'neck_shear_mpa': shear_stress, 'neck_torsion_estimate_mpa': float(torsion_stress),
            'conditional_reference_ratios': {k: float(v) for k, v in ratios.items()},
            'short_neck_compression_displacement_proxy_mm': float(compression_peak*relief/REFERENCES['off_grain_modulus_proxy_mpa']),
            'scalar_screen_passed': bool(clearance_pass and max(ratios.values()) <= 1. and tension_peak <= 1.e-9),
            'qualified_for_design': False}
    return {'candidate': report.get('candidate'), 'feet': results, 'references': REFERENCES,
            'numerically_accepted': report.get('numerically_accepted', False),
            'conditional_screen_passed': bool(results and report.get('numerically_accepted', False)
                                             and all(row['scalar_screen_passed'] for row in results.values())),
            'limits': [__doc__, 'Opening extrapolation assumes a rigid planar gross foot section. Finite-area pressure is the specified Winkler law, not measured contact.',
                       'The compression displacement uses 0.05E as an off-grain elastic proxy, not a proven upper bound for the oblique notched neck.',
                       'Horizontal cut stresses are scalar screens; no perpendicular tension resistance is assumed. Notch stress concentrations and rolling shear are not represented.'],
            'qualified_for_design': False}
