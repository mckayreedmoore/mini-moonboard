"""Member-specific nominal thread exposure; no bolt resistance assigned."""
import json
import math
from pathlib import Path

from fea.prepare_easy_structural import digest
from mini_moonboard import wide_frame as frame
from mini_moonboard.selected_hardware import BoltSpec

SOURCE = Path("docs/wide-machining/metadata.json")
OUTPUT = Path("fea/results/bolt-thread-bearing.json")


def exposure(entry, exit, length, thread_length):
    if (not all(math.isfinite(v) for v in (entry, exit, length, thread_length))
            or not 0 <= entry < exit <= length or not 0 < thread_length <= length):
        raise ValueError("Require ordered material interval inside bolt and positive thread length")
    overlap = max(0., exit-max(entry, length-thread_length))
    return {"bearing_length_mm": exit-entry, "threaded_bearing_mm": overlap,
            "threaded_fraction": overlap/(exit-entry),
            "nominal_quarter_length_condition": overlap <= .25*(exit-entry)+1e-8}


def build():
    source = json.loads(SOURCE.read_text())
    hashes = source["source_sha256"]
    if source["candidate"] != frame.KEY or not hashes or any(digest(p) != h for p, h in hashes.items()):
        raise ValueError("Require unchanged current machining source closure")
    bolts = {c.name: c for c in frame.connections()
             if c.name.startswith(("leg_stitch_", "timber_base_"))}
    if len(bolts) != 14:
        raise ValueError("Expected six stitches and eight gusset bolts")
    rows = []
    for row in source["connections"]:
        if row["connection"] not in bolts:
            continue
        c = bolts[row["connection"]]
        intervals = row["signed_raw_intervals_from_hardware_origin_mm"]
        if row["part"] not in c.members or row["operation"] != "bolt_clearance" or len(intervals) != 1:
            raise ValueError("Require single raw bearing interval for intended member")
        entry, exit = intervals[0]
        spec = BoltSpec("Selected dimensional family", c.length, c.grip, 0.)
        rows.append({"connection": c.name, "member": row["part"],
                     "interval_mm": [entry, exit], "bolt_length_mm": c.length,
                     "reference_thread_length_mm": spec.thread_length_reference_mm,
                     **exposure(entry, exit, c.length, spec.thread_length_reference_mm)})
    if len(rows) != 28 or len({(r["connection"], r["member"]) for r in rows}) != 28:
        raise ValueError("Incomplete or duplicate two-member inventory")
    return {"candidate": frame.KEY, "source_sha256": {
        **hashes, str(SOURCE): digest(SOURCE),
        "fea/bolt_thread_bearing.py": digest("fea/bolt_thread_bearing.py")},
        "limits": "Nominal reference thread length and modeled raw member intervals only. "
        "No thread-length/runout tolerance, material tolerance or installed measurement. "
        "Quarter-length condition alone does not establish NDS diameter exception or resistance. "
        "Selected members have no axial counterbore; backing and three-member leg/rim excluded.",
        "rows": rows}


if __name__ == "__main__":
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite thread-bearing evidence")
    OUTPUT.write_text(json.dumps(build(), indent=2)+"\n")
