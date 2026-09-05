import pytest

from fea.solve_connection import final_block


def test_final_block_rejects_partial_solve_and_accepts_numeric_final_time():
    first="displacements for set ALLN and time 0.1000000E+00\n\n 1 0. 0. -0.1\n"
    last="displacements for set ALLN and time 0.1000000E+01\n\n 1 0. 0. -1.0\n"
    with pytest.raises(ValueError,match="final-time"):
        final_block(first,"displacements")
    assert "-1.0" in final_block(first+"\n"+last,"displacements")
    with pytest.raises(ValueError,match="final-time"):
        final_block(last.replace("0.1000000E+01","NaN"),"displacements")
