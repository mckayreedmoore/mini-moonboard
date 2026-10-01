"""Necessary projected bearing peaks from receiver force and first moment.

No constitutive law, independent shear-plane capacity, or native solve.
"""
from pathlib import Path
import hashlib
import json
import math
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
INPUT = HERE.parent / "current-bg003-compatible-elastic-method-inputs-attempt01/inputs.json"
INPUT_SHA = "008d9b1d790d7994e0d72d6002baa479f82bb80143e936f6d328f334fdcd37d9"


def bound(force, first_moment, length):
    return (2*abs(first_moment) + math.hypot(2*first_moment, length*force)) / length**2


def scalar_oracles():
    # Exact integrations of admissible uniform and two-flank bang-bang fields.
    for p, length, switch in ((2.,6.,1.), (5.,10.,-2.), (3.,8.,0.)):
        force = -2*p*switch
        moment = p*(length**2/4-switch**2)
        assert abs(bound(force,moment,length)-p) < 1e-12
        assert abs(bound(-force,-moment,length)-p) < 1e-12
    assert bound(30,0,10) == 3
    assert bound(0,75,10) == 3
    return "PASS_UNIFORM_AND_SIGN_REVERSING_EXACT_INTEGRATION_ORACLES"


def produce():
    if hashlib.sha256(INPUT.read_bytes()).hexdigest() != INPUT_SHA:
        raise ValueError("Pinned receiver input changed")
    data = json.loads(INPUT.read_text())
    sources = {str(INPUT.relative_to(ROOT)):INPUT_SHA}
    for source in data["source_pins"]["case_reports"].values():
        path = ROOT / source["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != source["sha256"]:
            raise ValueError("Authenticated case report changed")
        sources[source["path"]] = source["sha256"]
    geometry = data["geometry_and_available_conditional_scenarios"]
    diameter = geometry["diameter_mm"]
    rows = []
    for case in data["cases"]:
        for increment in case["increments"]:
            for bolt in increment["BG003_bolts"]:
                for member, wrench in bolt["derived_member_wrenches_at_receiver_interval_midpoints"].items():
                    length = geometry["raw_modeled_bearing_lengths_mm"][member]
                    force = wrench["force_xyz_n"][1:]
                    moment = wrench["moment_xyz_nmm"]
                    first_moment = [moment[2], -moment[1]]
                    directions = [[math.cos(math.pi*i/180),math.sin(math.pi*i/180)] for i in range(180)]
                    for vector in (force,first_moment):
                        norm = math.hypot(*vector)
                        if norm:
                            directions.append([v/norm for v in vector])
                    certificates = []
                    for direction in directions:
                        f = sum(a*b for a,b in zip(direction,force))
                        j = sum(a*b for a,b in zip(direction,first_moment))
                        p = bound(f,j,length)
                        certificates.append({"direction_global_YZ":direction,
                                             "projected_force_n":f,"projected_first_moment_nmm":j,
                                             "necessary_peak_line_force_n_per_mm":p})
                    controlling = max(certificates,key=lambda c:c["necessary_peak_line_force_n_per_mm"])
                    grain = geometry["proposed_grain_vectors_global_xyz"][member]
                    cosine = abs(sum(a*b for a,b in zip(controlling["direction_global_YZ"],grain[1:])))
                    rows.append({"case_id":case["case_id"],"load_factor":increment["load_factor"],
                                 "increment_ordinal":increment["increment_ordinal"],"axis_id":bolt["axis_id"],
                                 "member":member,"receiver_length_mm":length,"diameter_mm":diameter,
                                 "receiver_midpoint_global_xyz_mm":wrench["reference_global_xyz_mm"],
                                 "source_transverse_force_YZ_n":force,"source_first_moment_YZ_nmm":first_moment,
                                 "force_only_lower_bound_n_per_mm":math.hypot(*force)/length,
                                 "moment_only_lower_bound_n_per_mm":4*math.hypot(*first_moment)/length**2,
                                 "projection_certificate":controlling,
                                 "proposed_grain_global_xyz":grain,
                                 "certificate_angle_to_proposed_grain_degrees":math.degrees(math.acos(min(1.,cosine))),
                                 "necessary_projected_peak_bearing_mpa":controlling["necessary_peak_line_force_n_per_mm"]/diameter,
                                 "direction_count":len(directions)})
    assert len(rows) == 126
    maxima = {}
    for member in geometry["raw_modeled_bearing_lengths_mm"]:
        maxima[member] = max((r for r in rows if r["member"]==member),key=lambda r:r["necessary_projected_peak_bearing_mpa"])
    return {"schema":"bg003_necessary_bearing_lower_bounds/v1","source_sha256":sources,
            "oracle":scalar_oracles(),"receiver_state_count":len(rows),"rows":rows,"sampled_maxima_by_member":maxima,
            "formula":"P >= (2*abs(J)+sqrt(4*J^2+L^2*F^2))/L^2 for every unit transverse projection; projected pressure=P/d",
            "claim":"Necessary lower bound for the stored rounded source wrenches under the declared sole-bore, distributed transverse-traction proxy; not an upper demand bound, resistance, constitutive solution or acceptance.",
            "limits":["No native-output rounding uncertainty propagation; source geometry and stored wrench centers are conditional inputs.",
                      "Finite directional projections give valid lower-bound certificates, not a proven sharp biaxial optimum.",
                      "Full modeled member lengths are available in this idealization; actual reduced engagement or thread-root diameter changes the calculation.",
                      "Radial bore bearing only; washer friction or other lateral-transfer mechanisms are not assigned.",
                      "No two-bolt shared wood, splitting, steel bending/yield, axial/thread/washer or complete-joint capacity is established."]}


if __name__ == "__main__":
    text = json.dumps(produce(),indent=2,allow_nan=False)+"\n"
    output = HERE / "bounds.json"
    if "--verify" in sys.argv:
        if output.read_text() != text:
            raise ValueError("Bounds differ from fresh replay")
        print("PASS_SOURCE_BOUND_NECESSARY_BEARING_CERTIFICATES:126 receiver states")
    else:
        output.write_text(text)
        print("Wrote126 receiver bounds; no solve, resistance or acceptance")
