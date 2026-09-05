"""Re-audit actual decks/DAT before publishing the hybrid comparison."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from .box_results import parse_results
from .hybrid_results import deck_geometry, support_moments
from .record_updated_results import verify_hashes


def checked_record(directory,mesh):
    stem=directory/f"box_audited_{mesh}_7000"
    record=json.loads(stem.with_suffix(".json").read_text())
    verify_hashes(record,directory)
    info=json.loads((directory/"box_frame_bulk.json").read_text())
    if record["frozen_geometry"]!=info:
        raise ValueError("Geometry metadata changed after solving")
    if hashlib.sha256((directory/"box_frame_bulk.step").read_bytes()).hexdigest()!=info["step_sha256"]:
        raise ValueError("Changed frozen STEP")
    cases=[(c["name"],tuple(v/1200 for v in c["force_n"])) for c in record["load_basis"]]
    nodes,feet,top=deck_geometry(stem.with_suffix(".inp").read_text(),cases)
    if len(nodes)!=record["nodes"] or len(feet)!=record["floor_nodes"] or top!=record["load_nodes"]:
        raise ValueError("Deck sets differ from solver summary")
    dat=stem.with_suffix(".dat").read_text()
    maxima,reactions=parse_results(dat,cases)
    moments=support_moments(dat,nodes,feet,top,cases)
    same_moments=all(math.isclose(a,bb,rel_tol=0,abs_tol=1e-5)
        for row,old in zip(moments,record["reaction_moment_nmm"],strict=True)
        for a,bb in zip(row,old,strict=True))
    if maxima!=record["max_top_displacement_mm"] or reactions!=record["reaction_totals_n"] or not same_moments:
        raise ValueError("Raw outputs differ from summary")
    # Canonical audit uses rounded coordinates actually written in the deck,
    # rather than Gmsh's pre-serialization doubles. Equilibrium tolerance stays1.
    record["reaction_moment_nmm"]=moments
    record["support_node_ids"]=feet
    record["audit_node_coordinates_mm"]={str(t):nodes[t] for t in feet+top}
    record["audit_context_sha256"]={str(p):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in map(Path,("fea/solve_box_frame.py","fea/prepare_hybrid_frame.py",
                           "fea/hybrid_results.py","fea/record_hybrid_results.py"))}
    return record,dat


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--candidate",choices=("2x8","2x10","2x12"))
    args=parser.parse_args()
    destination=Path("fea/results/hybrid")
    for size in ((args.candidate,) if args.candidate else ("2x10","2x12")):
        source=Path("fea/generated/hybrid")/size
        output=destination/size
        output.mkdir(parents=True,exist_ok=True)
        for mesh in (60,40):
            record,dat=checked_record(source,mesh)
            (output/f"box_audited_{mesh}_7000.json").write_text(json.dumps(record,indent=2)+"\n")
            (output/f"box_audited_{mesh}_7000.dat").write_text(dat)
        (output/"stability.json").write_text((source/"stability.json").read_text())
        print(output)


if __name__=="__main__":
    main()
