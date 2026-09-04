import pytest

from fea.box_results import parse_results


def test_solver_results_require_complete_cases_and_force_balance():
    data="displacements for set TOP\n\n"+"\n".join(f"{i} 0 3 4" for i in range(1,6))+"\n\n total force for set FEET\n\n -1200 0 0\n"
    maxima,reactions=parse_results(data,[("lateral",(1,0,0))])
    assert maxima=={"lateral":5}
    assert reactions==[[-1200,0,0]]
    with pytest.raises(ValueError,match="Unbalanced"):
        parse_results(data.replace("-1200","-1000"),[("lateral",(1,0,0))])
    with pytest.raises(ValueError,match="five finite"):
        parse_results(data.replace("5 0 3 4","5 nan 3 4"),[("lateral",(1,0,0))])
    with pytest.raises(ValueError,match="Missing"):
        parse_results(data,[("first",(1,0,0)),("second",(1,0,0))])
