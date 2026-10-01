#!/usr/bin/env python3
"""Read-only source and eight-pair crosswalk verification; no solver execution."""
import hashlib
import json
from pathlib import Path
import tarfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
EXPECTED_RECORD_SHA = "73ed00e9a2e0643bfbbc8bc764249ef0dd3e1a35b1d23cdccf987fb3534c4eac"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    record_path = HERE / "source-review.json"
    assert digest(record_path) == EXPECTED_RECORD_SHA, "Review record changed"
    data = json.loads(record_path.read_text())
    for relative, expected in data["sources_sha256"].items():
        assert digest(REPO / relative) == expected, relative
    archive = next(REPO / p for p in data["sources_sha256"] if p.endswith("source.tar.bz2"))
    with tarfile.open(archive, "r:bz2") as source:
        for name, expected in data["pinned_2_23_source_members_sha256"].items():
            member = source.extractfile("./CalculiX/ccx_2.23/src/" + name)
            assert member is not None
            assert hashlib.sha256(member.read()).hexdigest() == expected, name
    joint = HERE.parent / "ordinary-port-motion-attempt09-common-map"
    manifest = json.loads((joint / "contact-manifest.json").read_text())
    fragment = (joint / "contact-fragment.inc").read_text()
    deck = (joint / "port_motion_n_plus.inp").read_text()
    assert len(manifest["pairs"]) == data["pair_count"] == 35
    rows = []
    for index, pair in enumerate(manifest["pairs"], 1):
        token = f"WJCP_{index:03d}"
        assert f"{token}_S,{token}_M\n" in fragment
        assert f"*CONTACT PRINT,SLAVE={token}_S,MASTER={token}_M,FREQUENCY=1\nCF,CFN,CFS\n" in deck
        if pair["category"] == "open_bolt_shank_to_wood_bore":
            rows.append({"index": index, "slave_set": token + "_S", "master_set": token + "_M", **pair})
    assert rows == data["wood_bore_pairs"]
    assert [row["index"] for row in rows] == list(range(20, 28))
    assert len(rows) == data["bore_pair_count"] == 8
    for flag in ("native_output_qualified", "current_joint_ready", "geometry_changed", "joint_acceptance", "release"):
        assert data[flag] is False, flag
    return {"status": "PASS_SOURCE_BINDING_AND_PAIR_CROSSWALK", "native_output_qualified": False,
            "review_sha256": EXPECTED_RECORD_SHA, "pair_count": 35, "wood_bore_pair_count": 8}


if __name__ == "__main__":
    print(json.dumps(verify(), sort_keys=True))
