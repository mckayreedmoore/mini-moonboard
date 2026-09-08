import pytest

from fea.frd_displacements import read


def sample():
    return "\n".join(["  100CL 101 1.000000000 2 0 1 1", " -4  DISP 4 1",
        *[" -5  "+v for v in ("D1", "D2", "D3", "ALL")],
        f" -1{1:10d}{1.23456e-3:12.5E}{-2.:12.5E}{0.:12.5E}",
        f" -1{2:10d}{-3.:12.5E}{4.:12.5E}{5.:12.5E}", " -3"])


def test_select_after_full_coverage_check():
    assert read(sample(), {1, 2}, {2}) == {1.: {2: [-3., 4., 5.]}}
    assert read(sample(), {1, 2}, {1})[1.][1] == [1.23456e-3, -2., 0.]


@pytest.mark.parametrize("change", [
    lambda t: t.replace(" -3", ""),
    lambda t: t.replace(" -5  D3", " -5  WRONG"),
    lambda t: t.replace(" -1         2", " -1         1"),
    lambda t: t.replace(" -1         2", " -1         3"),
    lambda t: t+"\n"+t,
])
def test_rejects_corrupt_records(change):
    with pytest.raises(ValueError):
        read(change(sample()), {1, 2}, {1})
