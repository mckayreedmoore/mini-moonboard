"""Screen an unadopted Y-axis cleat tie using saved actions and cached geometry.

The assigned normal-force field is a statics construction, not a physical bolt
load bound or complete joint capacity. No current geometry or response changes.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import platform
from pathlib import Path

from scripts import eoere_current_response as current
from scripts import eoere_current_shop_followup as shop
from scripts import eoere_nominal_access as access

ROOT = current.ROOT
OWN = Path(__file__).resolve()
PACKET = current.DOC / "selected-hardware-v1/current-response-v1/joint-closure-v1/cleat-cross-tie-proposal-v1"
MEMBERS = ("eoere_cleat_left", "eoere_cleat_right")


def normal_trial(wrench, origin_z, tie_z, half_x=15.875, half_z=38.1,
                 patch_area=161.29, centroid_fraction=.8):
    """Four finite uniform compression patches plus one central axial tie.

    Right-handed source basis is normal Y / in-plane Z / in-plane X.
    Both normal moments are preserved. Tangential forces/torque are returned
    explicitly as unallocated duties. No friction or transverse wood tension.
    """
    current.require(len(wrench) == 6 and all(math.isfinite(v) for v in wrench)
                    and all(math.isfinite(v) for v in (origin_z, tie_z, half_x, half_z,
                                                       patch_area, centroid_fraction))
                    and min(half_x, half_z, patch_area) > 0 and 0 < centroid_fraction < 1,
                    "finite six-component wrench and positive patch geometry required")
    n, _, _, _, mz, mx = wrench
    mx_tie = mx + (tie_z-origin_z)*n
    c = max(abs(mz)/half_x, abs(mx_tie)/half_z, max(0., -n))/centroid_fraction
    tension = n+c
    patches = []
    for sx in (-1, 1):
        for sz in (-1, 1):
            force = c/4*(1-sx*mz/(c*half_x))*(1+sz*mx_tie/(c*half_z)) if c else 0.
            patches.append({"x_offset_mm": sx*half_x, "z_mm": tie_z+sz*half_z,
                            "compression_n": force, "uniform_pressure_mpa": force/patch_area})
    recovered = [tension-sum(p["compression_n"] for p in patches),
                 -sum(p["x_offset_mm"]*p["compression_n"] for p in patches),
                 -(tie_z-origin_z)*tension
                 + sum((p["z_mm"]-origin_z)*p["compression_n"] for p in patches)]
    current.require(tension >= -1e-8 and min(p["compression_n"] for p in patches) >= -1e-8
                    and max(abs(a-b) for a, b in zip(recovered, (n, mz, mx), strict=True)) < 1e-7,
                    "normal-force and both-moment equilibrium failed")
    return {"assigned_tie_tension_n": tension, "compression_patches": patches,
            "recovered_N_Mz_Mx": recovered,
            "unallocated_Z_X_shear_and_Y_torque": [wrench[i] for i in (1, 2, 3)],
            "physical_tie_load_upper_bound_or_complete_capacity": None}


def overlapping(bounds, other):
    return all(bounds[i] <= other[i+1]+1e-5 and other[i] <= bounds[i+1]+1e-5
               for i in (0, 2, 4))


def build(inputs_path):
    inputs_ref = current.ref(inputs_path)
    inputs = current.read(inputs_ref)
    current.require(inputs["schema"] == "eoere_cleat_cross_tie_proposal_inputs/v1"
                    and inputs["producer"] == current.ref(OWN)
                    and inputs["adopted"] is False, "exact unadopted proposal inputs required")
    source = current.read(inputs["cleat_demand"])
    pins = dict(source["source_sha256"])
    direct = [inputs_ref, inputs["producer"], inputs["test_source"], inputs["cleat_demand"],
              current.ref(Path(shop.__file__)), current.ref(Path(access.__file__))]

    def read(ref):
        nonlocal pins
        value = current.read(ref)
        pins = current.join(pins, {ref["path"]: ref["sha256"]})
        return value

    def asset(name):
        nonlocal pins
        ref = current.ref(ROOT/"site"/name)
        pins = current.join(pins, {ref["path"]: ref["sha256"]})
        raw = (ROOT/ref["path"]).read_bytes()
        return json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)

    pins = current.join(pins, {r["path"]: r["sha256"] for r in direct})
    current.verify(pins)
    current.require(source["geometry_revision"] == "eoere-raised-kicker-screws-v1"
                    and source["hardware_revision"] == "eoere-selected-purchase-hardware-v1"
                    and source["extra_grid"] is False and len(source["cases"]) == 12
                    and not any(source["release"].values()), "current saved cleat evidence required")
    field = read(source["cases"][0]["field"])
    profiles = {r["name"]: r["raw_profile_source"] for r in field["source_inputs"]["timber_rows"]}
    shop_inputs = read(inputs["shop_inputs"])
    helper_ref = shop_inputs["sources"]["bounds_helper"]
    current.require(current.sha(ROOT/helper_ref["path"]) == helper_ref["sha256"], "bounds helper drift")
    pins[helper_ref["path"]] = helper_ref["sha256"]
    helper = shop.module(helper_ref["path"], "cleat_tie_saved_bounds")
    native = read(shop_inputs["sources"]["native"])
    scenes = [asset(n) for n in ("eoere-bottom-rail-scene.json.gz", "eoere-cleat-trim-scene.json",
              "eoere-aligned-wire-scene.json.gz", "eoere-adjusted-base-v3-scene.json.gz",
              "eoere-cleat-extension-scene.json.gz")]
    channels = asset("eoere-uniform-channels-scene.json.gz")
    bank = helper.compose_bounds(native, [*scenes, {"replacements":
            channels["common_replacements"]+channels["base_replacements"]}])
    geometry, hardware = read(inputs["geometry"]), read(inputs["hardware"])
    catalog = next(r for r in hardware["selected_stacks"] if r["axis_id"] == "eoere_bolt_067")
    current.require(catalog["selected_underhead_length_mm"] == 165.1
                    and catalog["minimum_length_mm"] == 160.528, "retained 6.5-inch catalog window required")
    for row in geometry["changed_finished_solids"]+hardware["changed_finished_solids"]:
        bank[row["id"]] = {"kind": row["kind"], "bounds": row["bounds_xyz_mm"]}
    current.require(len(bank) == 1029, "complete current extra-off bounds bank required")
    h = next(s["source_axis"]["hardware_scenario"] for s in field["source_inputs"]["shafts"]
             if s["axis_id"] == "eoere_bolt_067")
    current.require(h["washer_od_mm"] == 26.162 and h["washer_thickness_mm"] == 2.6416
                    and h["nut_height_mm"] == 8.5598, "retained nominal 3/8 hardware differs")
    length, diameter, bore, z = (inputs[k] for k in
                               ("underhead_length_mm", "diameter_mm", "bore_mm", "tie_z_mm"))
    current.require((length, diameter, bore, z) == (165.1, 9.525, 10.31875, 260.),
                    "this proposal has exactly two fixed Y-axis ties")
    fc = inputs["conditional_unincreased_Fc_perp_psi"]*.006894757293168
    current.require(inputs["conditional_unincreased_Fc_perp_psi"] == 625., "existing conditional reference required")
    rows = []
    for case in source["cases"]:
        member = case["member"]
        current.require(member in MEMBERS and len(case["traces"]) == 2, "both own cleat traces required")
        for trace in case["traces"]:
            q = trace["required_cut_on_low_portion_n_nmm"]
            trial = normal_trial(q, source["geometry"][member]["origin_xyz_mm"][2], z)
            trial["maximum_patch_mean_reference_index"] = max(p["uniform_pressure_mpa"] for p in trial["compression_patches"])/fc
            trial["adverse_washer_net_area_mm2"] = math.pi/4*((.993*25.4)**2-(.453*25.4)**2)
            trial["adverse_washer_mean_reference_index"] = trial["assigned_tie_tension_n"]/trial["adverse_washer_net_area_mm2"]/fc
            rows.append({"case_id": case["case_id"], "state_id": case["state_id"], "member": member,
                         "boundary_point_actions_in_high_trace": trace["boundary_point_actions_in_high_trace"],
                         "source_wrench_n_nmm": q, **trial})
    require = current.require
    import cadquery as cq

    from scripts import eoere_current_components as component
    from scripts import eoere_current_washer_lands as washer
    probe = component.load(washer.PROBE, "cleat_tie_existing_annular_probe")
    query_results, layouts = [], []
    for member in MEMBERS:
        profile = profiles[member]
        host_ref = source["geometry"][member]["observation"]["source"]
        pins[host_ref["path"]] = host_ref["sha256"]
        require(current.sha(ROOT/host_ref["path"]) == host_ref["sha256"], "own cached cleat changed")
        host = cq.Shape.importBrep(str(ROOT/host_ref["path"]))
        x = profile["datum_xyz_mm"][0]+19.05
        low, high = -175.7, -36.
        cylinder = cq.Solid.makeCylinder(bore/2, high-low, cq.Vector(x, low, z), cq.Vector(0, 1, 0))
        missing = cylinder.cut(host).Volume()
        require(host.isValid() and len(host.Solids()) == 1 and missing < 1e-4,
                "proposed full-depth bore must lie inside cached finished wood")
        seats = [probe.annular_probe(host, [x, y, z], inward, h["washer_od_mm"], .433*25.4)
                 for y, inward in ((low, [0, 1, 0]), (high, [0, -1, 0]))]
        require(all(s["full_modeled_support"] for s in seats), "both bounding washer annuli need wood support")
        underhead, nutseat = low-h["washer_thickness_mm"], high+h["washer_thickness_mm"]
        tip, hex_radius = underhead+length, h["hex_across_flats_mm"]/math.sqrt(3)
        def box(radius, a, b, x=x):
            return [x-radius, x+radius, min(a, b), max(a, b), z-radius, z+radius]
        envelopes = [("shaft", box(diameter/2, underhead, tip)),
                     ("head", box(hex_radius, underhead-h["head_height_mm"], underhead)),
                     ("head_washer", box(h["washer_od_mm"]/2, underhead, low)),
                     ("nut_washer", box(h["washer_od_mm"]/2, high, nutseat)),
                     ("nut", box(hex_radius, nutseat, nutseat+h["nut_height_mm"])),
                     ("full_shaft_withdrawal", box(diameter/2, underhead-length, tip)),
                     ("head_withdrawal", box(hex_radius, underhead-length-h["head_height_mm"], underhead)),
                     ("nut_removal", box(hex_radius, nutseat, tip+h["nut_height_mm"]))]
        hand = -1 if member.endswith("left") else 1
        for end, y, outward, thickness, entry in (("head", underhead, -1, 6., 6.),
                ("nut", nutseat, 1, 6.35, tip-nutseat)):
            polygon = access.swept_handle_polygon()
            xs = [x+hand*u for u, _ in polygon]+[x-10.2, x+10.2]
            zs = [z+v for _, v in polygon]+[z-10.2, z+10.2]
            for operation, axial in (("wrench_60deg", thickness), ("full_wrench_entry", thickness+entry)):
                envelopes.append((end+"/"+operation, [min(xs), max(xs), min(y, y+outward*axial),
                                  max(y, y+outward*axial), min(zs), max(zs)]))
        for role, bounds in envelopes:
            # Host overlap is intentional only for the shaft passing through
            # its proposed hole or hardware seated against its own wood face.
            excluded = {member} if "/" not in role else set()
            obstacles = [name for name, row in bank.items() if name not in excluded
                         and overlapping(bounds, row["bounds"])]
            query_results.append({"member": member, "operation": role, "bounds_xyz_mm": bounds,
                                  "positive_AABB_obstacles": obstacles,
                                  "nominal_envelope_clear": not obstacles})
        layouts.append({"member": member, "axis_id": "proposal_tie_"+member,
                        "entry_xyz_mm": [x, low, z], "exit_xyz_mm": [x, high, z],
                        "entry_luv_mm": [120.3, 19.05, 0.], "exit_luv_mm": [120.3, 19.05, 139.7],
                        "bore_missing_wood_volume_mm3": missing, "removed_wood_volume_mm3": cylinder.Volume(),
                        "washer_annuli": seats,
                        "minimum_grain_end_distance_mm": 334.398105944-z,
                        "new_to_existing_bore_minimum_surface_gap_mm": 60.-bore,
                        "outer_X_axis_distance_mm": 19.05,
                        "minimum_two_pitch_tip_margin_at_short_length_mm":
                        catalog["minimum_length_mm"]-(high-low+2*h["washer_thickness_mm"]+h["nut_height_mm"])-2*25.4/16,
                        "minimum_nut_seating_margin_mm": high-low+2*.064*25.4-catalog["maximum_grip_gaging_mm"],
                        "reused_catalog_bolt_product": catalog["selected_product"],
                        "minimum_usable_drill_projection_mm": 139.7+19.05+6.35})
    # Rehash all frozen parent sources and all newly consumed repository code.
    for module in (component, washer):
        pins.update({str(Path(module.__file__).resolve().relative_to(ROOT)): current.sha(module.__file__)})
    current.verify(pins)
    require(len(rows) == 24 and len(query_results) == 24, "complete two-trace/side proposal coverage required")
    return {"schema": "eoere_cleat_cross_tie_proposal/v1", "inputs": inputs_ref,
            "revision": "eoere-cleat-normal-cross-ties-proposal-v1", "adopted": False,
            "current_geometry_or_hardware_changed": False, "structural_acceptance": False,
            "physical_demand_bound_established": False, "complete_resistance": None,
            "release": source["release"], "source_pin_count": len(pins),
            "source_bindings": {"parent_demand": inputs["cleat_demand"],
                                "additional_sources": {p: sha for p, sha in pins.items() if p not in source["source_sha256"]}},
            "all_frozen_sources_unchanged": True, "runtime_python": platform.python_version(),
            "placement": layouts, "normal_allocations": rows, "envelope_checks": query_results,
            "current_extra_off_parts_screened": len(bank),
            "all_new_nominal_envelopes_clear": all(q["nominal_envelope_clear"] for q in query_results),
            "proposed_inventory_changes": {"bolts": [100, 102], "nuts": [100, 102],
                                           "washers": [200, 204], "receiver_holes": [120, 122],
                                           "timbers": [22, 22], "Hillman_screws": [66, 66]},
            "limits": ["Assigned normal statics at the existing Y=-105.85 cut only; this is not an upper bound on physical bolt force or every possible split plane.",
                       "The four finite compression patches avoid using a perpendicular-tension allowable. Their pressure is a conditional mean reference, not a compatible 3D stress/fracture proof.",
                       "Existing tangential shear and cut-normal torque are retained unallocated duties; this proposal does not waive their transfer or resistance.",
                       "Washer metal bending, axial anchorage/plug/block failure, net-section and new-hole interaction, combined bolt loading and physical sharing require qualification.",
                       "The new axis has only19.05-mm narrow-side edge distance. No lateral NDS edge/group pass is inferred from this axial-duty proposal.",
                       "The current six frame responses cannot transfer to changed holes, mass and axial coupling. Any adopted revision needs its own response/applicability and installation checks.",
                       "Generic wrench envelopes clear catalog/nominal part bounds only; actual tools/supports, preload and delivered parts remain unobserved."]}


def drawing(result):
    """Dimensioned proposal schematic; geometry/strength authority stays separate."""
    governing = max(result["normal_allocations"], key=lambda r: r["assigned_tie_tension_n"])
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 980 650" role="img" aria-labelledby="title desc">',
           '<title id="title">Unadopted cleat cross-tie proposal</title>',
           '<desc id="desc">A Y-axis bolt through each cleat at L120.3 and U19.05. Existing X-axis bolts remain. Four compression patches illustrate one normal-force equilibrium allocation only.</desc>',
           '<style>text{font:15px sans-serif;fill:#183444}.small{font-size:12px}.wood{fill:#eed6ae;stroke:#6d522a;stroke-width:2}</style>',
           '<rect width="980" height="650" fill="#fafafa"/>',
           '<text x="30" y="32" font-weight="bold">UNADOPTED PROPOSAL — no cutting/drilling instruction or structural release</text>',
           '<text x="30" y="63">Side view: Y horizontal, grain / L vertical; X bolts seen end-on</text>']
    def yz(v, l):
        return 90+v*1.15, 520-l*1.15
    points = ' '.join(f'{x:.3f},{y:.3f}' for x,y in [yz(0,0),yz(139.7,0),yz(139.7,361.1860828293809),yz(0,194.698105944)])
    svg.append(f'<polygon class="wood" points="{points}"/>')
    for l in (60.3, 202.3875):
        for v in (44.45, 95.25):
            x,y=yz(v,l); svg.append(f'<circle cx="{x}" cy="{y}" r="5.933" fill="#396b97"/>')
    _,ty=yz(0,120.3)
    svg.extend([f'<path d="M86.96216,{ty} H276.82716" stroke="#087c70" stroke-width="10.95375"/>',
                f'<rect x="80.06216" y="{ty-8.2153125}" width="6.9" height="16.430625" fill="#087c70"/>',
                f'<rect x="86.96216" y="{ty-15.04315}" width="3.03784" height="30.0863" fill="#087c70"/>',
                f'<rect x="250.655" y="{ty-15.04315}" width="3.03784" height="30.0863" fill="#087c70"/>',
                f'<rect x="253.69284" y="{ty-8.2153125}" width="9.84377" height="16.430625" fill="#087c70"/>',
                '<text x="300" y="360">New Y-axis tie</text>',
                '<text x="300" y="384">3/8–16 × 6½ in; nut + two USS washers</text>',
                '<text x="300" y="408">L120.3, U19.05 mm; full depth 139.7 mm</text>',
                '<text x="90" y="550">Existing four X-axis bores retained</text>',
                '<text x="570" y="63">Cut normal Y: X / Z view</text>'])
    def xz(x,z):
        return 610+(x+19.05)*2.5, 520-(z-139.7)*1.35
    top=520-277.9420943866906*1.35
    svg.append(f'<rect class="wood" x="610" y="{top}" width="95.25" height="{277.9420943866906*1.35}"/>')
    for p in governing["compression_patches"]:
        x,y=xz(p["x_offset_mm"]-3.175,p["z_mm"]+12.7)
        svg.append(f'<rect x="{x}" y="{y}" width="15.875" height="34.29" fill="#c9863a"/>')
    cx,cy=xz(0,260.)
    svg.extend([f'<ellipse cx="{cx}" cy="{cy}" rx="12.8984375" ry="6.96515625" fill="#087c70"/>',
                '<text x="720" y="240">38.1-mm section width</text>',
                '<text x="720" y="266">Four assigned compression patches</text>',
                '<text x="720" y="289">6.35 × 25.4 mm each</text>',
                f'<text x="570" y="550">Governing assigned tie force: {governing["assigned_tie_tension_n"]:.3f} N</text>',
                '<text x="30" y="592">One added tie per cleat: proposed totals 102 bolts / 102 nuts / 204 washers.</text>',
                '<text x="30" y="616" class="small">Normal statics at one saved cut only. Shear, torque, anchorage, local strength, physical sharing and revised-frame behavior remain to qualify.</text>',
                '</svg>'])
    return '\n'.join(svg)+'\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=PACKET/"inputs.json")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--drawing", type=Path)
    args = parser.parse_args()
    current.require(not args.out.exists(), "preserve existing results; choose a fresh output")
    current.require(args.drawing is None or (args.drawing != args.out and not args.drawing.exists()),
                    "preserve existing drawing and keep output paths separate")
    result = build(args.inputs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as handle:
        json.dump(result, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    if args.drawing:
        args.drawing.parent.mkdir(parents=True, exist_ok=True)
        with args.drawing.open("x") as handle:
            handle.write(drawing(result))
    print(json.dumps({"out": str(args.out), "maximum_assigned_tie_n":
                      max(r["assigned_tie_tension_n"] for r in result["normal_allocations"]),
                      "all_new_nominal_envelopes_clear": result["all_new_nominal_envelopes_clear"]}))


if __name__ == "__main__":
    main()
