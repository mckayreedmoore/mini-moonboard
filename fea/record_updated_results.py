"""Recheck raw completed updated-board runs and publish small evidence records."""
import hashlib
import json
import math
from pathlib import Path

from .box_results import parse_results
from .joint_math import parse_joint_results
from .record_joint_results import read_deck


def verify_hashes(record, directory):
    for name, digest in record["evidence_sha256"].items():
        if hashlib.sha256((directory/name).read_bytes()).hexdigest()!=digest:
            raise ValueError(f"Changed solver evidence: {name}")


def main():
    directory=Path("fea/generated")
    output=Path("fea/results")
    for size in (60,40):
        stem=f"box_audited_{size}_7000"
        record=json.loads((directory/f"{stem}.json").read_text())
        verify_hashes(record,directory)
        cases=[(c["name"],tuple(v/1200 for v in c["force_n"])) for c in record["load_basis"]]
        data=(directory/f"{stem}.dat").read_text()
        maxima,reactions=parse_results(data,cases)
        if maxima!=record["max_top_displacement_mm"] or reactions!=record["reaction_totals_n"]:
            raise ValueError("Bulk summary differs from DAT")
        (output/f"{stem}.json").write_text(json.dumps(record,indent=2)+"\n")
        (output/f"{stem}.dat").write_text(data)
    for size in (20,15):
        records=[]
        for panel,targets in (("main_upper_left",("C10","C12")),("kicker_left",("3",))):
            for target in targets:
                stem=directory/f"panel_{panel}_{size}_{target}"
                record=json.loads(stem.with_suffix(".json").read_text())
                verify_hashes(record,directory)
                nodes,force,moment,elements=read_deck(stem.with_suffix(".inp").read_text())
                actual=parse_joint_results(stem.with_suffix(".dat").read_text(),force,nodes,moment,elements)
                for key in ("max_displacement_mm","peak_equivalent_stress_mpa","p95_equivalent_stress_mpa"):
                    if not math.isclose(actual[key],record[key],rel_tol=1e-10):
                        raise ValueError("Panel summary differs from DAT")
                record.update(actual)
                records.append(record)
        (output/f"panel_screen_{size}.json").write_text(json.dumps(records,indent=2)+"\n")
    # Export snapshots, not a claim that today's working tree generated them.
    for name in ("panels.json","box_frame_bulk.json"):
        (output/f"updated_{name}").write_text((directory/name).read_text())


if __name__=="__main__":
    main()
