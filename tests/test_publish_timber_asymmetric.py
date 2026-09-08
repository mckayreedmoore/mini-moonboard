import pytest

from fea import publish_timber_asymmetric as publisher


def test_compliance_reciprocity_and_positive_response():
    basis = [{"loaded_displacement_mm": [1., .2, .3]},
             {"loaded_displacement_mm": [.2, 2., .4]},
             {"loaded_displacement_mm": [-.3, -.4, -3.]}]
    assert min(publisher.compliance(basis)["symmetric_eigenvalues_mm_per_n"]) > 0
    basis[0]["loaded_displacement_mm"][1] = .5
    with pytest.raises(ValueError, match="reciprocity"):
        publisher.compliance(basis)
    with pytest.raises(ValueError, match="positive"):
        publisher.compliance([{"loaded_displacement_mm": [0., 0., 0.]}]*3)


def test_existing_publication_untouched(tmp_path, monkeypatch):
    monkeypatch.setattr(publisher, "OUTPUT", tmp_path)
    with pytest.raises(FileExistsError):
        publisher.publish()
