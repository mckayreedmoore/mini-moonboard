import hashlib
import json
import math
import tarfile
from pathlib import Path

import pytest

from fea.independent_ply_control import (
    LENGTH,
    E,
    audit,
    comparisons,
    deck,
    verify_serialized,
)


@pytest.mark.parametrize("n", [2,4])
@pytest.mark.parametrize("independent", [False,True])
def test_pure_bending_control(n,independent):
    text,context = deck(n,independent)
    verify_serialized(text,context)
    if independent:
        a,b = [set(p["nodes"]) for p in context["plies"]]
        assert not a & b
        assert {context["nodes"][n] for n in a} & {context["nodes"][n] for n in b}
    for case in context["cases"]:
        for ply,exact in zip(context["plies"],case["exact"],strict=True):
            k = exact["moment_nmm"]/(E*exact["inertia_mm4"])
            # Exact quadratic axial field; the same traction integration must
            # reproduce exact half-work independent of face triangulation.
            work = sum(case["loads"].get(n,0.)*k*(context["nodes"][n][case["axis"]]-(ply["center_x"] if case["axis"]==0 else 0.))*LENGTH/2
                       for n in ply["nodes"] if context["nodes"][n][2]==LENGTH)
            assert math.isclose(work,exact["energy_nmm"],rel_tol=1e-12,abs_tol=1e-12)
    with pytest.raises(ValueError):
        verify_serialized(text+"*TIE\n",context)
    with pytest.raises(ValueError):
        verify_serialized(text.replace("*CLOAD,OP=NEW","*CLOAD",1),context)
    with pytest.raises(ValueError):
        audit("",context)


def test_archived_control_evidence():
    archive = Path(__file__).resolve().parents[1]/"fea/results/independent_ply_control/evidence.tar.gz"
    with tarfile.open(archive) as bundle:
        def read(name):
            return bundle.extractfile("./"+name).read()
        manifest = json.loads(read("manifest.json"))
        assert manifest["pass"]
        for source,digest in manifest["source_sha256"].items():
            assert hashlib.sha256(read("launch_sources/"+Path(source).name)).hexdigest()==digest
        results = {}
        for n in (2,4):
            for independent in (False,True):
                name = f"{'independent' if independent else 'composite'}{n}"
                record = json.loads(read(name+".json"))
                text,context = deck(n,independent)
                assert text.encode()==read(name+".inp")
                assert hashlib.sha256(text.encode()).hexdigest()==record["deck_sha256"]
                for output,digest in record["output_sha256"].items():
                    assert hashlib.sha256(read(output)).hexdigest()==digest
                actual = audit(read(name+".dat").decode(),context)
                assert actual==record["results"]
                assert all(p["pass"] for c in actual for p in c["plies"])
                results[name] = actual
        assert comparisons(results)==manifest["comparisons"]
