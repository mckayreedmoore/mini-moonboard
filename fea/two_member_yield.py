"""Current two-member bolt reference values with explicit conservative assumptions."""
from collections import defaultdict

from fea.bolt_thread_bearing import build as thread_geometry
from fea.dowel_yield import single_shear


def build():
    geometry = thread_geometry()
    groups = defaultdict(list)
    for row in geometry["rows"]:
        groups[row["connection"]].append(row)
    result = []
    for name, members in groups.items():
        main, side = sorted(members, key=lambda r: r["interval_mm"][0])
        if len(members) != 2 or abs(main["interval_mm"][1]-side["interval_mm"][0]) > 1e-7:
            raise ValueError("Require two adjacent modeled members")
        inputs = {"main_length_in": main["bearing_length_mm"]/25.4,
                  "side_length_in": side["bearing_length_mm"]/25.4,
                  "main_bearing_lb_in": (5600 if name.startswith("leg_stitch_") else 3650)*.298,
                  "side_bearing_lb_in": 5600*.298,
                  "main_yield_moment_lb_in": 45000*.298**3/6,
                  "side_yield_moment_lb_in": 45000*.298**3/6,
                  "gap_in": 0., "reduction_terms": {
                      "Im": 5., "Is": 5., "II": 4.5, "IIIm": 4., "IIIs": 4., "IV": 4.}}
        answer = single_shear(**inputs)
        result.append({"connection": name, "members": [main["member"], side["member"]],
                       "inputs": inputs, **answer,
                       "reference_lateral_n": answer["reference_lateral_lbf"]*4.4482216152605})
    return result
