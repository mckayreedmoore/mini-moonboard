"""Known-answer checks for the explicit laminate beam modes."""

import json

import numpy as np
import pytest

from scripts import thin_bolted_frame_mechanics as frame
from scripts.eoere_leg_header_mechanics import MATERIAL, ROOT, plywood_local


@pytest.mark.parametrize('length', [30.7875, 168.275, 609.6])
def test_six_cantilever_modes(length):
    material = json.loads((ROOT/MATERIAL).read_bytes())
    p = material['properties']
    assert material['physical_qualification'] is False
    k = plywood_local(frame, length, p)
    assert np.allclose(k, k.T, rtol=1e-13, atol=1e-10)
    expected = [length/p['EA_N'],
                length**3/(3*p['EI_z_Nmm2'])+length/(p['shear_factor']*p['GA_u_N']),
                length**3/(3*p['EI_y_Nmm2'])+length/(p['shear_factor']*p['GA_v_N']),
                length/p['GJ_Nmm2'], length/p['EI_y_Nmm2'], length/p['EI_z_Nmm2']]
    flexibility = np.linalg.solve(k[6:, 6:], np.eye(6))
    assert flexibility.diagonal() == pytest.approx(expected, rel=1e-11, abs=1e-16)
    assert flexibility[1, 5] == pytest.approx(length**2/(2*p['EI_z_Nmm2']), rel=1e-11)
    assert flexibility[2, 4] == pytest.approx(-length**2/(2*p['EI_y_Nmm2']), rel=1e-11)
