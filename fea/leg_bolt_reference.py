"""Actual leg stack inventory and conditional bonded-laminate lateral reference.

Not a three-member joint rating, adjusted allowable, or adhesive qualification.
"""
import json
from itertools import pairwise

from fea.bolt_thread_bearing import SOURCE, exposure
from fea.dowel_yield import single_shear
from fea.prepare_easy_structural import digest
from mini_moonboard import wide_frame as frame
from mini_moonboard.selected_hardware import BoltSpec


def build():
    source = json.loads(SOURCE.read_text())
    hashes = source["source_sha256"]
    if source["candidate"] != frame.KEY or not hashes or any(
        digest(p) != h for p, h in hashes.items()
    ):
        raise ValueError("Require unchanged current machining source closure")
    bolts = [c for c in frame.connections() if c.name.startswith("analysis_leg_wall_bolt_")]
    if len(bolts) != 8:
        raise ValueError("Expected eight leg bolts")
    results = []
    for bolt in bolts:
        rows = [r for r in source["connections"] if r["connection"] == bolt.name]
        if len(rows) != 3 or {r["part"] for r in rows} != set(bolt.members):
            raise ValueError("Require exactly three intended members")
        members = []
        thread = BoltSpec("Selected dimensional family", bolt.length, bolt.grip, 0.).thread_length_reference_mm
        for row in rows:
            intervals = row["signed_raw_intervals_from_hardware_origin_mm"]
            if row["operation"] != "bolt_clearance" or len(intervals) != 1:
                raise ValueError("Require one raw bolt bearing interval per member")
            entry, end = intervals[0]
            members.append({"member": row["part"], "interval_mm": [entry, end],
                            **exposure(entry, end, bolt.length, thread)})
        members.sort(key=lambda m: m["interval_mm"][0])
        side = "left" if "_left_" in bolt.name else "right"
        if [m["member"] for m in members] != [f"base_side_{side}", f"leg_{side}_inner", f"leg_{side}_outer"]:
            raise ValueError("Expected rim followed by both same-side leg plies")
        if any(abs(a["interval_mm"][1]-b["interval_mm"][0]) > 1e-7
               for a, b in pairwise(members)):
            raise ValueError("Require contiguous bearing stack")
        inputs = {
            "main_length_in": members[0]["bearing_length_mm"]/25.4,
            "side_length_in": sum(m["bearing_length_mm"] for m in members[1:])/25.4,
            "main_bearing_lb_in": 3650*.298,
            "side_bearing_lb_in": 5600*.298,
            "main_yield_moment_lb_in": 45000*.298**3/6,
            "side_yield_moment_lb_in": 45000*.298**3/6,
            "gap_in": 0.,
            "reduction_terms": {"Im": 5., "Is": 5., "II": 4.5, "IIIm": 4., "IIIs": 4., "IV": 4.},
        }
        answer = single_shear(**inputs)
        results.append({"connection": bolt.name, "members": members,
                        "bolt_length_mm": bolt.length, "reference_thread_length_mm": thread,
                        "conditional_bonded_laminate_inputs": inputs, **answer,
                        "conditional_reference_lateral_n": answer["reference_lateral_lbf"]*4.4482216152605})
    return {"candidate": frame.KEY, "limits": "Perfectly bonded leg plies treated as one side member. "
            "No adhesive qualification, adjusted allowable, axial/group resistance or safety factor. "
            "Nominal thread geometry only; root diameter retained throughout.",
            "source_sha256": {**hashes, str(SOURCE): digest(SOURCE)}, "rows": results}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
