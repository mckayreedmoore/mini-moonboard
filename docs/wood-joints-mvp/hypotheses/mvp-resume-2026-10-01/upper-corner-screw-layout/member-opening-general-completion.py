"""Actual finite blind/partial/clipped sections on the reviewed 104-axis geometry.

build(output) is lightweight saved-action postprocessing. build(output, elastic=True)
also solves whole connected section warping problems and is parent-only serialized
work. Neither entry point invokes CAD, a frame solve, tests, or a source producer.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import inspect
import json
import math
import platform
import time
from collections import Counter
from pathlib import Path

# ruff: noqa: RUF007
# Keep consecutive-coordinate loops byte-identical to the frozen Q1 field
# method. Changing their source for style alone invalidates accepted cache keys.

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/member-opening-general-completion"
CACHE = RAW / "field-cache-v1"
CACHE_AUDIT = {}
RUN_OUTPUT = None
BASELINE = HERE.parent / "member-screen-attempt02/four-screw-layout01"
REMAINDER_SHA = "5db858b30a69f393f46b493bc06c46ca2b786e85ed4ac520475d29cf51b25e62"
BASELINE_REPORT_SHA = "54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5"
REGISTER_SHA = "c34745395481038e32c7474de1798882263de7e54a7cc494949948b4a5e3464c"
RESPONSE_SHA = "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7"
PACKETS = {
    "member-opening-remainder/attempt02": "db5a48bc43ab7d953da9fa57df99ddac507dfe0b389f0d1907c5c946a93e6931",
    "side-host-opening-completion/attempt01": "14df990be586554ab89257311c406f49c77190ee94fdaa8f206f426cfcb85320",
    "permanent-opening-completion/attempt02": "82e9e61545dad1404b73147721b17b470c5956339f30729a5bee2d90d5f5d0cf",
}
SPECIAL = {"outer_cleat_pressure_accounting", "six_bore_spine_accounting"}
ORIGINAL_GRAVITY = HERE / "rawlocal/dead-load-check/parent-attempt06"
ORIGINAL_GRAVITY_SHA = "20802196776a89ea8b041832b413ef8d8613493b1bf36f89a3810807c5166e75"
GROUP = HERE / "rawlocal/corner-group-finish/attempt03/checks.json"
GROUP_SHA = "2ae3a84f273823dc6ca751e6fdddab8e0d70425ee7b34e1e38ebc79d5b672f23"
TOL = 1e-6
TANGENCY_HELPER = Path(__file__).with_name("member-opening-tangent-certification.py")
TANGENCY_HELPER_SHA = "d8d3eacdccbc71ae99af47cab7cd0918e40536bb2a41b4cabdffd15515ab1d76"


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def lines(path):
    with gzip.open(path, "rt") as stream:
        for line in stream:
            yield json.loads(line)


def sources():
    # Reuse the inert loader and the existing frozen geometry/material closure.
    import importlib.util
    import sys

    path = HERE / "member-opening-remainder.py"
    require(sha(path) == REMAINDER_SHA, "remainder producer changed")
    spec = importlib.util.spec_from_file_location("actual_opening_remainder", path)
    remainder = importlib.util.module_from_spec(spec)
    old = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(remainder)
    finally:
        sys.dont_write_bytecode = old
    api, pins, plan, members, surfaces = remainder.sources()
    pins[Path(__file__).resolve()] = sha(__file__)
    api.bind(pins, TANGENCY_HELPER, TANGENCY_HELPER_SHA)
    for name in ("side-host-opening-completion.py", "permanent-opening-completion.py"):
        pins[HERE / name] = sha(HERE / name)
    for path, expected in (
        (BASELINE / "member-results.json", BASELINE_REPORT_SHA),
        (HERE / "rawlocal/working-joint-register/attempt03/register.json", REGISTER_SHA),
        (HERE / "frame-250-attempt02/response.npz", RESPONSE_SHA),
    ):
        api.bind(pins, path, expected)
    original = read(BASELINE / "member-results.json")
    require(original["source_sha256"][str((HERE / "frame-250-attempt02/response.npz").relative_to(ROOT))]
            == RESPONSE_SHA, "reviewed response/extraction binding differs")
    require(original["output_sha256"]["geometry.json"] == pins[api.GEOMETRY],
            "baseline and fresh geometry differ")
    for name in ("action-section-arrays.npz", "inputs.json", "geometry.json"):
        api.bind(pins, BASELINE / name, original["output_sha256"][name])
    register = read(HERE / "rawlocal/working-joint-register/attempt03/register.json")
    require(register["accounting"]["total_unique_frame_bolt_axes"] == 104
            and register["accounting"]["hillman_panel_kicker_axes_separate"] == 66,
            "reviewed 104/66 census differs")
    for relative, receipt_sha in PACKETS.items():
        directory = HERE / "rawlocal" / relative
        api.bind(pins, directory / "receipt.json", receipt_sha)
        receipt = read(directory / "receipt.json")
        names = (("residual-cuts.json", "section-recipes.json") if relative.startswith("permanent") else
                 ("section-recipes.json", "cuts.jsonl.gz", "action-audits.json"))
        for name in names:
            api.bind(pins, directory / name, receipt["output_sha256"][name])
    permanent_path = HERE / "rawlocal/knee-bridge-permanent-resolve/attempt02"
    permanent = read(permanent_path / "comparison.json")
    # These actions remain a separately labeled conditional proposal-gravity
    # comparison. Do not import its changed six-bore geometry.
    permanent_api = remainder.module(HERE / "permanent-opening-completion.py",
                                      pins[HERE / "permanent-opening-completion.py"])
    api.bind(pins, permanent_path / "comparison.json", permanent_api.PINS[permanent_path / "comparison.json"])
    api.bind(pins, permanent_path / "member-actions.npz", permanent["output_sha256"]["member-actions.npz"])
    api.bind(pins, permanent_path / "geometry.json", permanent["output_sha256"]["geometry.json"])
    api.bind(pins, ORIGINAL_GRAVITY / "comparison.json", ORIGINAL_GRAVITY_SHA)
    original_gravity = read(ORIGINAL_GRAVITY / "comparison.json")
    require(original_gravity["wood_strength_CD"] == .9
            and all(original_gravity[k] == 0 for k in
                    ("live_gravity_scale", "live_horizontal_scale", "live_moment_scale"))
            and not original_gravity["geometry_changed"], "reviewed permanent basis differs")
    require(original_gravity["source_sha256"][str((BASELINE / "geometry.json").relative_to(ROOT))]
            == pins[BASELINE / "geometry.json"], "reviewed permanent geometry differs")
    for name in ("response.npz", "member-actions.npz", "body-balances.json"):
        api.bind(pins, ORIGINAL_GRAVITY / name, original_gravity["output_sha256"][name])
    for relative, digest in original_gravity["source_sha256"].items():
        api.bind(pins, ROOT / relative, digest)
    api.bind(pins, GROUP, GROUP_SHA)
    live = []
    for relative in list(PACKETS)[:2]:
        for cut in lines(HERE / "rawlocal" / relative / "cuts.jsonl.gz"):
            if cut["recipe_status"] != "SUPPORTED_EXACT_TRANSVERSE_SLOT_RECIPE":
                live.append(cut)
    residual = read(HERE / "rawlocal/permanent-opening-completion/attempt02/residual-cuts.json")
    require(len(live) == 4344 and len(residual) == 2552, "4344/2552 residual census differs")
    require(Counter(c["category"] for c in residual if c["category"] in SPECIAL)
            == {"outer_cleat_pressure_accounting": 336, "six_bore_spine_accounting": 288},
            "special pressure/proposal duties differ")
    # Include the separate original terminal and unmachined-envelope traces.
    # They are disjoint from the 4,344 finished-opening method-limit cuts.
    coverage = read(remainder.COVERAGE / 'coverage.json')
    extra = coverage['inapplicable_terminal_stations'] + [
        s for s in coverage['uncalculated_fresh_opening_stations']
        if s['opening_identity_kind'] != 'finished_geometry_interval']
    existing = {(c['body'],c['saved_station_index'],c['case'],c['limit']) for c in live}
    for target in extra:
        for case in plan['case_ids']:
            for before in (True,False):
                limit = 'before' if before else 'after'
                identity = target['body'],target['station_index'],case,limit
                require(identity not in existing,'terminal/envelope overlaps finished-opening target')
                existing.add(identity)
                live.append({'body':target['body'],'saved_station_index':target['station_index'],
                    'saved_trace_index':2*target['station_index']+int(not before),
                    'case':case,'limit':limit,'station_mm':target['station_mm'],
                    'reason':('ORIGINAL_TERMINAL_PROFILE' if target in coverage['inapplicable_terminal_stations']
                              else 'UNMACHINED_STATION_ENVELOPE_NOT_A_VOID')})
    require(len(live)==5784,'4344+1176+264 live target partition differs')
    profile_dir = HERE/'rawlocal/profile-method-completion/attempt02'
    profile_receipt = read(profile_dir/'receipt.json')
    require(sha(profile_dir/'receipt.json')=='15236a2a44955ba63aba7075c491debee651a48dd083e4affb72cba07fedd36b',
            'existing profile receipt differs')
    api.bind(pins,profile_dir/'receipt.json','15236a2a44955ba63aba7075c491debee651a48dd083e4affb72cba07fedd36b')
    api.bind(pins,profile_dir/'checks.json',profile_receipt['output_sha256']['checks.json'])
    api.bind(pins,profile_dir/'preparation.json',profile_receipt['output_sha256']['preparation.json'])
    api.authenticate(pins)
    return remainder, api, pins, plan, members, surfaces, original, permanent, live, residual, original_gravity


def actual_section(member, surface, station, outer_at, np):
    """Subtract the union of finite shaft chords, including all overlapping holes.

    A transverse finite circular cylinder intersects the grain plane in a
    rectangle: its chord in one section direction and its actual finite shaft
    interval in the other. A blind bore never removes the whole shaft width.
    """
    g = member["geometry"]
    frame = np.array([g[k] for k in ("axis", "section_u", "section_v")])
    features = {f["feature_id"]: f for f in surface["features"]}
    caps = {fid for fid, f in features.items() if f["surface_kind"] == "PLANE"
            and len(f["trim"]["wires"]) == 1 and f["trim"]["wires"][0]["edge_count"] == 1
            and f["trim"]["wires"][0]["edges"][0]["curve_kind"] == "CIRCLE"}
    planes = [p for p in member["profile_planes"] if p["id"] not in caps]
    outer = outer_at(station, g, planes, [])
    # The existing helper intentionally refuses clipped-end mechanics. Its
    # retained bounds are still geometry; this model assigns its own mechanics.
    low = np.array([-g["width_mm"] / 2, -g["depth_mm"] / 2])
    high = -low.copy()
    sides, plane_ids = set(), []
    point_global = np.array(g["start"]) + station * frame[0]
    for plane in planes:
        if not plane["lo"] - TOL <= station <= plane["hi"] + TOL:
            continue
        n = frame @ np.array(plane["normal"])
        rhs = plane["offset"] - np.dot(plane["normal"], point_global)
        if max(abs(n[1:])) < 1e-7:
            require(rhs >= -TOL, "section lies outside finished plane")
            continue
        require(min(abs(n[1:])) < 1e-7, "nonrectilinear outer section needs exact CAD section")
        i = int(np.argmax(abs(n[1:])))
        x = float(rhs / n[i + 1])
        if n[i + 1] > 0:
            high[i] = min(high[i], x)
            sides.add((i, 1))
        else:
            low[i] = max(low[i], x)
            sides.add((i, -1))
        plane_ids.append(plane["id"])
    if min(high - low) <= TOL or len(sides) != 4:
        return {"status": "TERMINAL_SECTION_NEEDS_ONE_SIDED_DOMAIN_OR_TRACTION",
                "bounds_low_high_uv_mm": [low.tolist(), high.tolist()],
                "finite_outer_plane_ids": plane_ids, "side_count": len(sides),
                "outer_source": outer, "regions": None}
    voids, certificates = [], []
    for interval in member["bore_or_passage_intervals"]:
        if not interval["lo"] - TOL <= station <= interval["hi"] + TOL:
            continue
        if interval["id"].endswith("/owner_authorized_station_exclusion"):
            continue  # An exclusion envelope is not a finished material void.
        feature = features[interval["id"]]
        require(feature["surface_kind"] == "CYLINDER", "opening needs a noncylindrical section recipe")
        cylinder = feature["cylinder"]
        p = frame @ (np.array(cylinder["axis_origin_global_xyz_mm"]) - g["start"])
        d = frame @ np.array(cylinder["axis_unit_global_xyz"])
        shaft = int(np.argmax(abs(d)))
        require(shaft in (1, 2) and abs(abs(d[shaft]) - 1) < 1e-7
                and max(abs(np.delete(d, shaft))) < 1e-7,
                "longitudinal/oblique bore needs curved-domain model")
        radius = cylinder["radius_mm"]
        angular = feature["trim"]["surface_parameter_bounds"]["u"]
        axial = cylinder["axis_parameter_interval_mm"]
        # Clipped ends can trim cylinder walls; their finite shaft envelope is
        # clipped by the independently authenticated outer profile at this cut.
        require(cylinder["material_side_geometry"] == "bore_like"
                and abs(angular[1] - angular[0] - 2 * math.pi) < 1e-5,
                "no whole-angular bore certificate")
        ends = np.sort(p[shaft] + d[shaft] * np.array(axial))
        distance = abs(station - p[0])
        chord = math.sqrt(max(0.0, radius * radius - distance * distance))
        other = 3 - shaft
        removed_low, removed_high = low.copy(), high.copy()
        removed_low[shaft - 1] = max(low[shaft - 1], ends[0])
        removed_high[shaft - 1] = min(high[shaft - 1], ends[1])
        removed_low[other - 1] = max(low[other - 1], p[other] - chord)
        removed_high[other - 1] = min(high[other - 1], p[other] + chord)
        certificates.append({"feature_id": interval["id"], "radius_mm": radius,
                             "grain_center_mm": float(p[0]), "shaft_axis": shaft,
                             "actual_shaft_ends_mm": ends.tolist(), "chord_halfwidth_mm": chord,
                             "removed_bounds_low_high_uv_mm": [removed_low.tolist(), removed_high.tolist()]})
        if min(removed_high - removed_low) > 1e-10:
            voids.append((removed_low, removed_high))
    # Exact coordinate arrangement of all void edges. Cells are integration
    # tiles of the complete real domain; no artificial retained subset is used.
    axes = [sorted({float(low[i]), float(high[i]),
                    *(float(b[i]) for v in voids for b in v)}) for i in (0, 1)]
    regions = []
    for a, b in zip(axes[0][:-1], axes[0][1:]):
        for c, d in zip(axes[1][:-1], axes[1][1:]):
            mid = np.array([(a + b) / 2, (c + d) / 2])
            if b - a <= 1e-10 or d - c <= 1e-10 or any(np.all(mid >= lo) and np.all(mid <= hi) for lo, hi in voids):
                continue
            regions.append({"bounds_uv_mm": [[a, b], [c, d]]})
    require(regions, "finished opening leaves no positive section")
    return {"status": "ACTUAL_FINITE_RECTANGLE_UNION", "regions": regions,
            "bounds_low_high_uv_mm": [low.tolist(), high.tolist()],
            "finite_outer_plane_ids": plane_ids, "excluded_cap_plane_ids": sorted(caps),
            "bore_certificates": certificates, "outer_source": outer}


def normal_stress(q, regions, refs, net, np):
    props = net.area_properties(regions)
    area = props["area_mm2"]
    center = np.array(props["centroid_uv_mm"])
    moment = q[3:] - np.cross(np.r_[0., center], q[:3])
    inertia = np.array(props["central_integral_u2_uv_v2_matrix_mm4"])
    slope = np.linalg.solve(inertia, [-moment[2], moment[1]])
    mean = float(q[0] / area)
    values = []
    recovered = np.zeros(3)
    for r in props["regions"]:
        own_center = np.array(r["centroid_uv_mm"])
        force = r["area_mm2"] * (mean + slope @ (own_center - center))
        own_moment = [slope[1] * r["local_integral_u2_v2_mm4"][1] + own_center[1] * force,
                      -slope[0] * r["local_integral_u2_v2_mm4"][0] - own_center[0] * force]
        recovered += np.r_[force, own_moment]
        for u in r["bounds_uv_mm"][0]:
            for v in r["bounds_uv_mm"][1]:
                bending = float(slope @ (np.array([u, v]) - center))
                stress = mean + bending
                comparison = net.normal_comparisons(mean, bending, stress, refs)
                values.append({"uv_mm": [u, v], "sigma_parallel_mpa": stress,
                               "bending_mpa": bending,
                               "normal_reference_sum": comparison['axial_plus_bending_reference_sum'],
                               **comparison})
    error = recovered - q[[0, 4, 5]]
    require(max(abs(error)) < 1e-6, "exact longitudinal force/moment recovery failed")
    return {"properties": {k: v for k, v in props.items() if k != "regions"},
            "wrench_at_net_centroid_n_nmm": np.r_[q[:3], moment].tolist(),
            "sigma_mean_mpa": mean, "sigma_slopes_uv_mpa_per_mm": slope.tolist(),
            "sigma_parallel_min_max_mpa": [min(v["sigma_parallel_mpa"] for v in values),
                                           max(v["sigma_parallel_mpa"] for v in values)],
            "recovered_N_Mu_Mv_n_nmm": recovered.tolist(),
            "recovery_error_n_nmm": error.tolist(),
            "maximum_reference_witness": max(values, key=lambda v: v["normal_reference_sum"]),
            "total_tension_over_Ft": max(v['total_tension_over_Ft'] for v in values),
            "total_compression_over_Fc": max(v['total_compression_over_Fc'] for v in values),
            "absolute_bending_over_Fb": max(v['absolute_bending_over_Fb'] for v in values),
            "normal_reference_sum": max(v["normal_reference_sum"] for v in values)}


def circular_area_properties(regions, disks, net, np):
    base = net.area_properties(regions)
    area = base['area_mm2']
    center = np.array(base['centroid_uv_mm'])
    first = area*center
    second = np.array(base['central_integral_u2_uv_v2_matrix_mm4'])+area*np.outer(center,center)
    for disk in disks:
        own = np.array(disk['disk_center_uv_mm'])
        radius = disk['radius_mm']
        disk_area = math.pi*radius**2
        area -= disk_area
        first -= disk_area*own
        second -= np.eye(2)*(math.pi*radius**4/4)+disk_area*np.outer(own,own)
    center = first/area
    inertia = second-area*np.outer(center,center)
    assert area > 0 and np.min(np.linalg.eigvalsh(inertia)) > 0
    return {'area_mm2':float(area),'centroid_uv_mm':center.tolist(),
            'central_integral_u2_uv_v2_matrix_mm4':inertia.tolist(),
            'first_integrals_u_v_mm3':first.tolist(),'raw_second_integrals_u2_uv_v2_mm4':second.tolist()}


def circular_normal_stress(q, regions, disks, refs, net, np):
    props = circular_area_properties(regions,disks,net,np)
    area, center = props['area_mm2'],np.array(props['centroid_uv_mm'])
    moment = q[3:]-np.cross(np.r_[0.,center],q[:3])
    slope = np.linalg.solve(props['central_integral_u2_uv_v2_matrix_mm4'],[-moment[2],moment[1]])
    mean = q[0]/area
    first, second = np.array(props['first_integrals_u_v_mm3']),np.array(props['raw_second_integrals_u2_uv_v2_mm4'])
    force = mean*area+slope@(first-area*center)
    integrated_u_v = mean*first+(second-np.outer(first,center))@slope
    recovered = np.r_[force,integrated_u_v[1],-integrated_u_v[0]]
    assert np.max(abs(recovered-q[[0,4,5]])) < 1e-6
    witnesses = []
    for region in regions:
        for u in region['bounds_uv_mm'][0]:
            for v in region['bounds_uv_mm'][1]:
                point = np.array([u,v])
                assert all(np.linalg.norm(point-np.array(d['disk_center_uv_mm'])) >= d['radius_mm']-1e-6 for d in disks)
                bending = float(slope@(point-center))
                witnesses.append({'uv_mm':[u,v],'sigma_parallel_mpa':float(mean+bending),
                                  **net.normal_comparisons(float(mean),bending,float(mean+bending),refs)})
    return {'properties':props,'sigma_mean_mpa':float(mean),'sigma_slopes_uv_mpa_per_mm':slope.tolist(),
            'recovered_N_Mu_Mv_n_nmm':recovered.tolist(),'recovery_error_n_nmm':(recovered-q[[0,4,5]]).tolist(),
            'normal_reference_sum':max(w['axial_plus_bending_reference_sum'] for w in witnesses),
            'total_tension_over_Ft':max(w['total_tension_over_Ft'] for w in witnesses),
            'total_compression_over_Fc':max(w['total_compression_over_Fc'] for w in witnesses),
            'absolute_bending_over_Fb':max(w['absolute_bending_over_Fb'] for w in witnesses),
            'maximum_reference_witness':max(witnesses,key=lambda w:w['axial_plus_bending_reference_sum']),
            'extrema_basis':'Linear strain-plane extrema lie at the intact outer corners of each transverse-slot rectangle; internal disjoint disks cannot exceed those extrema.',
            'local_bore_concentration_or_curved_domain_shear_qualified':False}


def read_accepted_section_field(regions, net, np, spacing, accepted_fields):
    """Read a source-bound accepted field; no missing-field solve fallback."""
    import scipy
    require(np.__version__=='2.5.2' and scipy.__version__=='1.18.1','pinned field runtime differs')
    method=sha_bytes((inspect.getsource(elastic_section)+inspect.getsource(coordinate_regularization)).encode())
    identity={'regions':regions,'spacing_mm':spacing,'method_sha256':method,
              'numpy':np.__version__,'scipy':scipy.__version__}
    key=sha_bytes(json.dumps(identity,sort_keys=True,separators=(',',':')).encode())
    require(key in accepted_fields,'geometry/method lacks an authenticated accepted field; no solve attempted')
    binding=accepted_fields[key]
    data,metadata=ROOT/binding['npz_path'],ROOT/binding['metadata_path']
    require(sha(data)==binding['npz_sha256'] and sha(metadata)==binding['metadata_sha256'],'accepted field binding differs')
    saved=read(metadata)
    require(saved['identity']==identity and saved['npz_sha256']==binding['npz_sha256'],'accepted field identity differs')
    with np.load(data,allow_pickle=False) as arrays:
        field={**saved['metadata'],**{name:arrays[name].copy() for name in ('field','points','weights')}}
    points=field['points']-np.array(field['centroid_uv_mm'])
    recovered=np.vstack([np.einsum('n,nij->ij',field['weights'],field['field']),
        np.einsum('n,nj->j',field['weights'],points[:,0,None]*field['field'][:,1,:]-points[:,1,None]*field['field'][:,0,:])])
    require(np.max(abs(recovered-np.eye(3)))<1e-7 and field['weak_equilibrium_residual']<1e-6,
            'accepted field signed-resultant or weak-residual gate failed')
    CACHE_AUDIT[key]={**binding,'reused_from_accepted_checkpoint':True}
    return {**field,'accepted_checkpoint_key':key,'accepted_checkpoint_npz_sha256':binding['npz_sha256'],
            'accepted_checkpoint_metadata_sha256':binding['metadata_sha256']}


def coordinate_regularization(regions, net, np):
    """Coalesce sub-tolerance coordinates at outer mouths; retain every delta.

    This is a numerical section idealization within the recorded 1e-6 mm
    coordinate tolerance. Original longitudinal arithmetic stays unsnapped.
    A removed tiny bridge never becomes an exact finished-CAD stress claim.
    """
    borders=[sorted({x for r in regions for x in r['bounds_uv_mm'][i]}) for i in (0,1)]
    mappings=[]
    changes=[]
    for i,values in enumerate(borders):
        lo,hi=values[0],values[-1]
        mapping={x:(lo if 0<x-lo<TOL else hi if 0<hi-x<TOL else x) for x in values}
        changes.extend({'section_axis':i,'original_mm':x,'regularized_mm':y,'delta_mm':y-x}
                       for x,y in mapping.items() if x!=y)
        mappings.append(mapping)
    result=[]
    for region in regions:
        bounds=[[mappings[i][x] for x in region['bounds_uv_mm'][i]] for i in (0,1)]
        if all(b-a>1e-12 for a,b in bounds):
            result.append({'bounds_uv_mm':bounds})
    require(result,'coordinate regularization removed the whole section')
    original=net.area_properties(regions)
    adjusted=net.area_properties(result)
    def count(values):
        groups=[]
        for r in values:
            touching=[]
            for i,group in enumerate(groups):
                for other in group:
                    overlaps=[min(r['bounds_uv_mm'][k][1],other['bounds_uv_mm'][k][1])-
                              max(r['bounds_uv_mm'][k][0],other['bounds_uv_mm'][k][0]) for k in (0,1)]
                    if max(overlaps)>0 and min(overlaps)>=-1e-13:
                        touching.append(i);break
            merged=[r]
            for i in reversed(touching):merged.extend(groups.pop(i))
            groups.append(merged)
        return len(groups)
    before,after=count(regions),count(result)
    return result,{'coordinate_tolerance_mm':TOL,'coordinate_changes':changes,
        'maximum_coordinate_delta_mm':max((abs(c['delta_mm']) for c in changes),default=0.),
        'original_minimum_arrangement_interval_mm':min(b-a for v in borders for a,b in zip(v[:-1],v[1:])),
        'regularized_minimum_region_width_mm':min(b-a for r in result for a,b in r['bounds_uv_mm']),
        'original_area_mm2':original['area_mm2'],'regularized_area_mm2':adjusted['area_mm2'],
        'area_delta_mm2':adjusted['area_mm2']-original['area_mm2'],
        'original_centroid_uv_mm':original['centroid_uv_mm'],
        'regularized_centroid_uv_mm':adjusted['centroid_uv_mm'],
        'original_connected_components':before,'regularized_connected_components':after,
        'topology_changed':before!=after,
        'exact_unsnapped_finished_geometry_stress_claimed':not changes,
        'scope':'Conditional coalesced-coordinate section; every topology change remains an explicit physical applicability limit.'}


def checkpoint_section(regions, net, np, spacing=3.0):
    """Reuse accepted unit fields by exact shape/method/runtime hash."""
    import scipy
    require(scipy.__version__=='1.18.1','pinned SciPy runtime differs')
    method=sha_bytes((inspect.getsource(elastic_section)+inspect.getsource(coordinate_regularization)).encode())
    identity={'regions':regions,'spacing_mm':spacing,'method_sha256':method,
              'numpy':np.__version__,'scipy':scipy.__version__}
    key=sha_bytes(json.dumps(identity,sort_keys=True,separators=(',',':')).encode())
    data=CACHE/(key+'.npz');metadata=CACHE/(key+'.json')
    if data.exists() or metadata.exists():
        require(data.exists() and metadata.exists(),'incomplete field checkpoint')
        saved=read(metadata)
        require(saved['identity']==identity and sha(data)==saved['npz_sha256'],'field checkpoint binding differs')
        with np.load(data,allow_pickle=False) as arrays:
            value={**saved['metadata'],**{name:arrays[name].copy() for name in ('field','points','weights')}}
        reused=True
    else:
        CACHE.mkdir(parents=True,exist_ok=True)
        if RUN_OUTPUT is not None:
            write(RUN_OUTPUT/'field-progress.json',{'starting_field_key':key,'identity':identity,
                'accepted_field_count':len(CACHE_AUDIT),'accepted_cut_count':read(RUN_OUTPUT/'cut-progress.json')['cut_count']})
        value=elastic_section(regions,net,np,spacing)
        temporary=CACHE/(key+'.temporary.npz')
        np.savez_compressed(temporary,**{name:value[name] for name in ('field','points','weights')})
        temporary.replace(data)
        write(metadata,{'identity':identity,'npz_sha256':sha(data),
                        'metadata':{k:v for k,v in value.items() if k not in ('field','points','weights')}})
        reused=False
    center=np.array(value['centroid_uv_mm'])
    points=value['points']-center
    recovered=np.vstack([np.einsum('n,nij->ij',value['weights'],value['field']),
        np.einsum('n,nj->j',value['weights'],points[:,0,None]*value['field'][:,1,:]-
                                     points[:,1,None]*value['field'][:,0,:])])
    require(np.max(abs(recovered-np.eye(3)))<1e-7,'cached field full signed-resultant recovery failed')
    require(value['weak_equilibrium_residual']<1e-6,'cached field weak residual exceeds unchanged gate')
    CACHE_AUDIT[key]={'npz_path':str(data.relative_to(ROOT)),'npz_sha256':sha(data),
        'metadata_path':str(metadata.relative_to(ROOT)),'metadata_sha256':sha(metadata),
        'reused_from_accepted_checkpoint':reused}
    value['accepted_checkpoint_key']=key
    value['accepted_checkpoint_npz_sha256']=sha(data)
    value['accepted_checkpoint_metadata_sha256']=sha(metadata)
    return value


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def elastic_section(regions, net, np, spacing=3.0):
    """Q1 whole-domain shear/warping; cell edges are shared, never free seams.

    Equal grain/transverse shear moduli are an explicit conditional hypothesis.
    Solve Neumann potential for transverse shear from longitudinal equilibrium;
    solve free warping for torsion. Three right-hand sides share one factorization.
    Parent owns this heavier computation, including method validation.
    """
    from scipy.sparse import coo_matrix, diags
    from scipy.sparse.csgraph import connected_components
    from scipy.sparse.linalg import splu

    regions,regularization=coordinate_regularization(regions,net,np)
    props = net.area_properties(regions)
    center = np.array(props["centroid_uv_mm"])
    inertia = np.array(props["central_integral_u2_uv_v2_matrix_mm4"])
    inertia_inverse = np.linalg.inv(inertia)
    borders = [sorted({x for r in regions for x in r["bounds_uv_mm"][i]}) for i in (0, 1)]
    axes = [np.array(sorted({float(x) for a, b in zip(v[:-1], v[1:])
                             for x in np.linspace(a, b, max(1, math.ceil((b-a)/spacing)) + 1)})) for v in borders]
    ids, nodes, cells = {}, [], []

    def node(i, j):
        key = i, j
        if key not in ids:
            ids[key] = len(nodes)
            nodes.append([axes[0][i], axes[1][j]])
        return ids[key]

    for i in range(len(axes[0])-1):
        for j in range(len(axes[1])-1):
            mid = [(axes[0][i]+axes[0][i+1])/2, (axes[1][j]+axes[1][j+1])/2]
            if any(all(r["bounds_uv_mm"][k][0] <= mid[k] <= r["bounds_uv_mm"][k][1] for k in (0, 1)) for r in regions):
                cells.append([node(i,j),node(i+1,j),node(i+1,j+1),node(i,j+1)])
    nodes = np.array(nodes)
    rr, cc, vv, quadrature = [], [], [], []
    rhs = np.zeros((len(nodes), 3))
    for cell in cells:
        x = nodes[cell]
        width, depth = x[2]-x[0]
        local = np.zeros((4,4))
        for xi in (-1/math.sqrt(3), 1/math.sqrt(3)):
            for eta in (-1/math.sqrt(3), 1/math.sqrt(3)):
                signs = np.array([[-1,-1],[1,-1],[1,1],[-1,1]])
                N = (1+signs[:,0]*xi)*(1+signs[:,1]*eta)/4
                grad = np.c_[signs[:,0]*(1+signs[:,1]*eta)/(2*width),
                             signs[:,1]*(1+signs[:,0]*xi)/(2*depth)]
                xy = N@x-center
                rot = np.array([-xy[1], xy[0]])
                weight = width*depth/4
                local += weight * grad@grad.T
                rhs[cell,:2] += weight * np.outer(N, xy@inertia_inverse)
                rhs[cell,2] -= weight * grad@rot
                quadrature.append((cell, grad, xy, weight))
        for i in range(4):
            for j in range(4):
                rr.append(cell[i]);cc.append(cell[j]);vv.append(local[i,j])
    K = coo_matrix((vv,(rr,cc)),shape=(len(nodes),len(nodes))).tocsc()
    components, labels = connected_components(K, directed=False)
    if components != 1:
        # Explicit parallel-ligament idealization: common generalized shear
        # deformation/twist. Minimize complementary energy of the actual
        # component fields subject to the total signed section resultants.
        # This is not proof of the real longitudinal bypass/end constraints.
        grouped = [[] for _ in range(components)]
        for region in regions:
            low = [b[0] for b in region['bounds_uv_mm']]
            i,j = [int(np.searchsorted(axes[k],low[k])) for k in (0,1)]
            grouped[int(labels[ids[i,j]])].append(region)
        pieces = [checkpoint_section(r,net,np,spacing) for r in grouped]
        mappings, compliances, stiffnesses = [], [], []
        for own_regions,piece in zip(grouped,pieces,strict=True):
            own_center=np.array(net.area_properties(own_regions)['centroid_uv_mm'])
            offset=own_center-center
            B=np.array([[1.,0,0],[0,1.,0],[-offset[1],offset[0],1.]])
            H=np.einsum('n,nij,nik->jk',piece['weights'],piece['field'],piece['field'])
            stiffness=np.linalg.inv(H)
            mappings.append(B);compliances.append(H);stiffnesses.append(stiffness)
        system=sum(B@S@B.T for B,S in zip(mappings,stiffnesses,strict=True))
        global_compliance=np.linalg.inv(system)
        allocations=[S@B.T@global_compliance for B,S in zip(mappings,stiffnesses,strict=True)]
        recovered=sum(B@A for B,A in zip(mappings,allocations,strict=True))
        require(np.max(abs(recovered-np.eye(3)))<1e-7,'parallel-ligament resultant recovery failed')
        return {'field':np.concatenate([np.einsum('nij,jk->nik',p['field'],A)
                    for p,A in zip(pieces,allocations,strict=True)]),
                'points':np.concatenate([p['points'] for p in pieces]),
                'weights':np.concatenate([p['weights'] for p in pieces]),
                'spacing_mm':spacing,'nodes':sum(p['nodes'] for p in pieces),
                'cells':sum(p['cells'] for p in pieces),
                'torsion_J_mm4':float(1/global_compliance[2,2]),
                'unit_resultant_error':float(np.max(abs(recovered-np.eye(3)))),
                'weak_equilibrium_residual':max(p['weak_equilibrium_residual'] for p in pieces),
                'actual_component_count':int(components),
                'centroid_uv_mm':center.tolist(),'coordinate_regularization':regularization,
                'component_allocation_matrix':np.array(allocations).tolist(),
                'component_complementary_energy_matrix':np.array(compliances).tolist(),
                'component_resultant_to_global_matrix':np.array(mappings).tolist(),
                'allocation_assumption':'Conditional parallel prismatic ligaments with common generalized shear/twist; minimum complementary energy, not an area share. Real longitudinal bypass/end compatibility is not established.'}
    free = np.arange(1,len(nodes))
    solution = np.zeros_like(rhs)
    active=K[free][:,free]
    scaling=1/np.sqrt(active.diagonal())
    factor=splu(diags(scaling)@active@diags(scaling))
    solution[free]=scaling[:,None]*factor.solve(scaling[:,None]*rhs[free])
    refinement_count=0
    for _ in range(5):
        defect=rhs-K@solution
        if np.max(abs(defect))<1e-9:break
        solution[free]+=scaling[:,None]*factor.solve(scaling[:,None]*defect[free])
        refinement_count+=1
    residual = K@solution-rhs
    require(np.max(abs(residual)) < 1e-6, "section potential equilibrium residual too large")
    field, xy_all, weights = [], [], []
    for cell, grad, xy, weight in quadrature:
        t = grad.T@solution[cell]
        t[:,2] += [-xy[1],xy[0]]
        field.append(t);xy_all.append(xy);weights.append(weight)
    field, xy_all, weights = np.array(field), np.array(xy_all), np.array(weights)
    torque = np.einsum('n,nj->j',weights,xy_all[:,0,None]*field[:,1,:]-xy_all[:,1,None]*field[:,0,:])
    require(torque[2] > 0, "nonpositive whole-domain torsion constant")
    # Normalize discrete resultants rather than postulating force sharing.
    resultants = np.vstack([np.einsum('n,nij->ij',weights,field),torque])
    normalized = np.einsum('nij,jk->nik',field,np.linalg.inv(resultants))
    recovered = np.vstack([np.einsum('n,nij->ij',weights,normalized),
        np.einsum('n,nj->j',weights,xy_all[:,0,None]*normalized[:,1,:]-xy_all[:,1,None]*normalized[:,0,:])])
    require(np.max(abs(recovered-np.eye(3))) < 1e-7, "whole-domain shear/torque recovery failed")
    return {"field":normalized,"points":xy_all+center,"weights":weights,
            'centroid_uv_mm':center.tolist(),'coordinate_regularization':regularization,
            'linear_solver':'Jacobi-scaled sparse LU with residual correction',
            'linear_solver_refinement_count':refinement_count,
            'gauge_fixed_diagonal_condition_indicator':float(max(active.diagonal())/min(active.diagonal())),
            "spacing_mm":spacing,"nodes":len(nodes),"cells":len(cells),
            "torsion_J_mm4":float(torque[2]),"unit_resultant_error":float(np.max(abs(recovered-np.eye(3)))),
            "weak_equilibrium_residual":float(np.max(abs(residual)))}


def certified_tangent_field(recipe, member, surface, station, net, np, spacing):
    """Keep original normal regions; solve only a certified shear idealization."""
    import importlib.util
    require(sha(TANGENCY_HELPER)==TANGENCY_HELPER_SHA,'tangency certificate helper changed')
    spec=importlib.util.spec_from_file_location('saved_tangent_certification',TANGENCY_HELPER)
    tangent=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tangent)
    certificates=tangent.certificates(recipe,member,surface,station,np,TOL)
    if not certificates:
        return checkpoint_section(recipe['regions'],net,np,spacing)
    projected=tangent.apply(recipe['regions'],certificates)
    original=net.area_properties(recipe['regions'])
    _,before_audit=coordinate_regularization(recipe['regions'],net,np)
    adjusted,after_audit=coordinate_regularization(projected,net,np)
    changed=net.area_properties(adjusted)
    field=checkpoint_section(projected,net,np,spacing)
    field['certified_tangent_geometry']={
        'certificates':certificates,'original_unsnapped_regions':recipe['regions'],
        'shear_solver_input_regions':projected,'final_coalesced_shear_regions':adjusted,
        'original_area_mm2':original['area_mm2'],'final_shear_area_mm2':changed['area_mm2'],
        'area_delta_mm2':changed['area_mm2']-original['area_mm2'],
        'original_centroid_uv_mm':original['centroid_uv_mm'],
        'final_shear_centroid_uv_mm':changed['centroid_uv_mm'],
        'original_connected_components':before_audit['original_connected_components'],
        'final_shear_connected_components':after_audit['regularized_connected_components'],
        'topology_changed':before_audit['original_connected_components']!=after_audit['regularized_connected_components'],
        'exact_original_normal_regions_preserved':True,'exact_unsnapped_CAD_shear_stress_claimed':False,
        'scope':'Certified zero-chord tangent-coordinate shear idealization; topology changes are explicit physical applicability limits.'}
    return field


def elastic_stress(q, normal, field, fv, np):
    if 'field' not in field:
        return field.copy()
    moment = np.array(normal["wrench_at_net_centroid_n_nmm"])[3:]
    center_shift=np.array(field['centroid_uv_mm'])-np.array(normal['properties']['centroid_uv_mm'])
    moment-=np.cross(np.r_[0.,center_shift],q[:3])
    shear = np.einsum('nij,j->ni',field['field'],[q[1],q[2],moment[0]])
    norms = np.linalg.norm(shear,axis=1)
    index = int(np.argmax(norms))
    return {"section_model":("whole-connected-domain equal-shear-modulus elastic potential"
                if field.get('actual_component_count',1)==1 else
                "conditional disconnected parallel-ligament complementary-energy allocation"),
            "peak_quadrature_shear_mpa":float(norms[index]),"peak_reference_ratio":float(norms[index]/fv),
            "peak_point_uv_mm":field['points'][index].tolist(),
            'rms_shear_mpa':float(np.sqrt(np.dot(field['weights'],norms**2)/sum(field['weights']))),
            'sample_is_rigorous_upper_bound':False,
            'regularized_domain_centroid_torque_nmm':float(moment[0]),
            **{k:v for k,v in field.items() if k not in ('field','points','weights')}}


def endpoint_limit(q,member,surface,station,refs,outer_at,net,np):
    """Analytic one-sided vanishing-rectangle limit, with numerical witnesses.

    Saved endpoint profile roundoff below 1e-6 mm is interpreted as the exact
    tangent plane. Retain the exact cut and transport its moment to inward
    planes; no finite contact area or load smoothing is invented.
    """
    direction=1. if station<member['stations_mm'][-1]/2 else -1.
    geometry=member['geometry']
    sample=actual_section(member,surface,station+direction*.01,outer_at,np)
    require(sample['regions'] is not None,'no positive one-sided terminal domain')
    low,high=np.array(sample['bounds_low_high_uv_mm'])
    frame=np.array([geometry[k] for k in ('axis','section_u','section_v')])
    gradients=np.zeros((2,2))
    point=np.array(geometry['start'])+(station+direction*.01)*frame[0]
    active=set(sample['finite_outer_plane_ids'])
    for side,bounds in enumerate((low,high)):
        for axis in (0,1):
            matching=[]
            for plane in member['profile_planes']:
                if plane['id'] not in active:continue
                n=frame@np.array(plane['normal'])
                if abs(n[axis+1])<1e-7:continue
                coordinate=(plane['offset']-np.dot(plane['normal'],point))/n[axis+1]
                if abs(coordinate-bounds[axis])<1e-6:
                    matching.append(direction*(-n[0]/n[axis+1]))
            require(matching,'terminal boundary lacks an exact finite-plane derivative')
            gradients[side,axis]=matching[0]
    width_slopes=gradients[1]-gradients[0]
    widths_at_zero=(high-low)-.01*width_slopes
    thin=int(np.argmin(abs(widths_at_zero)))
    other=1-thin
    require(abs(widths_at_zero[thin])<TOL and width_slopes[thin]>0,
            'terminal does not have an authenticated linearly vanishing width')
    L=float(widths_at_zero[other]);k=float(width_slopes[thin])
    centroid0=(low+high)/2-.01*gradients.mean(axis=0)
    centroid_moment=q[3:]-np.cross(np.r_[0.,centroid0],q[:3])
    strong_moment=float(centroid_moment[2] if thin==0 else centroid_moment[1])
    balanced=bool(max(abs(q[:3]))<1e-7 and max(abs(q[3:]))<1e-5)
    coefficient2=6*abs(strong_moment)/(L*k*k)
    evidence=[]
    for epsilon in (.1,.01,.001,.0001,.00001):
        section=actual_section(member,surface,station+direction*epsilon,outer_at,np)
        require(section['regions'] is not None,'positive one-sided example missing')
        shifted=q.copy()
        shifted[3:]-=np.cross([direction*epsilon,0.,0.],shifted[:3])
        if balanced:shifted[:]=0.
        result=normal_stress(shifted,section['regions'],refs,net,np)
        evidence.append({'epsilon_mm':epsilon,'area_mm2':result['properties']['area_mm2'],
            'transported_signed_cut_n_nmm':shifted.tolist(),
            'sigma_min_max_mpa':result['sigma_parallel_min_max_mpa'],
            'normal_reference_sum':result['normal_reference_sum']})
    if balanced:
        status='FINITE_ZERO_ONE_SIDED_EQUILIBRIUM_LIMIT'
    else:
        require(coefficient2>1e-7 or np.linalg.norm(q[:3])>1e-7,
                'nonzero terminal moment requires another exact asymptotic coefficient')
        status='DIVERGENT_ONE_SIDED_SOURCE_POINT_ACTION_LIMIT'
    return {'status':status,'numerical_limit_resolved':True,'inward_grain_sign':direction,
        'area_asymptote_mm2_per_epsilon_mm':L*k,'thin_section_axis':thin,
        'vanishing_width_slope':k,'centroid_at_limit_uv_mm':centroid0.tolist(),
        'strong_bending_stress_absolute_epsilon_minus2_coefficient':0. if balanced else coefficient2,
        'force_mean_necessary_stress_absolute_epsilon_minus1_coefficient':0. if balanced else float(np.linalg.norm(q[:3])/(L*k)),
        'maximum_absolute_normal_stress_limit_mpa':0. if balanced else '+infinity',
        'normal_reference_limit':0. if balanced else '+infinity',
        'zero_uses_exact_equilibrium_within_source_tolerances':balanced,
        'source_force_precision_n':1e-7,'source_moment_precision_nmm':1e-5,
        'profile_roundoff_tangent_tolerance_mm':TOL,'numerical_one_sided_witnesses':evidence,
        'scope':'Prescribed signed point-action beam-section limit, not delivered timber failure or a smoothed physical contact field.'}


def method_example(output):
    """Parent-only known-answer validation, before expensive section runs."""
    started=time.monotonic()
    remainder,api,pins,*_ = sources()
    import numpy as np
    import scipy

    net = remainder.module(HERE/'corner-net-section.py',pins[HERE/'corner-net-section.py'])
    regions=[{'bounds_uv_mm':[[-10.,10.],[-5.,5.]]}]
    exact=net.rectangle_torsion(20.,10.)
    results=[]
    for spacing in (2.,1.,.5):
        field=elastic_section(regions,net,np,spacing)
        torsion_peak=float(np.max(np.linalg.norm(field['field'][:,:,2],axis=1)))
        shear_peak=float(np.max(np.linalg.norm(field['field'][:,:,0],axis=1)))
        results.append({'spacing_mm':spacing,'J_mm4':field['torsion_J_mm4'],
            'J_relative_error':abs(field['torsion_J_mm4']/exact['J_mm4']-1),
            'torsion_peak_coefficient_per_mm3':torsion_peak,
            'torsion_peak_relative_error':abs(torsion_peak/exact['peak_shear_coefficient_per_mm3']-1),
            'transverse_shear_peak_mpa_per_N':shear_peak,
            'transverse_shear_peak_relative_error':abs(shear_peak/(1.5/200.)-1),
            **{k:v for k,v in field.items() if k not in ('field','points','weights')}})
    parallel_regions=[{'bounds_uv_mm':[[-15.,-5.],[-5.,5.]]},
                      {'bounds_uv_mm':[[5.,15.],[-5.,5.]]}]
    parallel=elastic_section(parallel_regions,net,np,.5)
    allocations=np.array(parallel['component_allocation_matrix'])
    allocation_error=float(np.max(abs(allocations[:,:,0]-[[.5,0.,0.],[.5,0.,0.]])))
    parallel_peak=float(np.max(np.linalg.norm(parallel['field'][:,:,0],axis=1)))
    sliver_regions=[{'bounds_uv_mm':[[-10.,10.],[-5.,0.]]},
                    {'bounds_uv_mm':[[-10.,10.],[0.,5.-1e-10]]},
                    {'bounds_uv_mm':[[-10.,10.],[5.-1e-10,5.]]}]
    sliver=elastic_section(sliver_regions,net,np,.5)
    regular=elastic_section(regions,net,np,.5)
    sliver_peak=float(np.max(np.linalg.norm(sliver['field'][:,:,0],axis=1)))
    sliver_error=float(abs(sliver_peak/(1.5/200.)-1))
    result={'schema':'actual_section_elastic_known_answer/v2','runtime':{'numpy':np.__version__,'scipy':scipy.__version__,
        'elapsed_seconds':time.monotonic()-started},
        'exact_rectangle_torsion':exact,'exact_unit_shear_peak_mpa':1.5/200.,'mesh_results':results,
        'symmetric_parallel_ligament_example':{'unit_Vu_component_allocation':allocations[:,:,0].tolist(),
            'exact_unit_Vu_component_allocation':[[.5,0.,0.],[.5,0.,0.]],'allocation_error':allocation_error,
            'peak_shear_mpa_per_N':parallel_peak,'exact_peak_shear_mpa_per_N':1.5/200.,
            'peak_relative_error':abs(parallel_peak/(1.5/200.)-1)},
        'known_rectangle_with_coordinate_sliver':{
            'coordinate_regularization':sliver['coordinate_regularization'],
            'J_difference_from_unsplit_rectangle_mm4':sliver['torsion_J_mm4']-regular['torsion_J_mm4'],
            'unit_shear_peak_mpa_per_N':sliver_peak,'exact_unit_shear_peak_mpa_per_N':1.5/200.,
            'unit_shear_peak_relative_error':sliver_error,
            'unit_wrench_recovery_error':sliver['unit_resultant_error'],
            'weak_equilibrium_residual':sliver['weak_equilibrium_residual'],
            'mesh_nodes_cells':[sliver['nodes'],sliver['cells']],
            'gauge_fixed_diagonal_condition_indicator':sliver['gauge_fixed_diagonal_condition_indicator'],
            'physical_domain_change':'None: an internal integration seam was removed from the same full rectangle.'},
        'method_ready':results[-1]['J_relative_error']<.01
            and results[-1]['torsion_peak_relative_error']<.05
            and results[-1]['transverse_shear_peak_relative_error']<.01
            and allocation_error<1e-7 and abs(parallel_peak/(1.5/200.)-1)<.01,
        'assumptions':'Unrestrained Saint-Venant warping; equal two grain/transverse shear moduli; zero Poisson coupling; long prismatic section. Mesh peaks are numerical samples, not rigorous physical stress bounds.'}
    result['method_ready']=bool(result['method_ready'] and sliver_error<.01
        and abs(sliver['torsion_J_mm4']-regular['torsion_J_mm4'])<1e-7
        and not sliver['coordinate_regularization']['topology_changed'])
    output=Path(output).resolve()
    require(output.parent==RAW.resolve() and not output.exists(),'fresh immediate owned child required')
    output.mkdir(parents=True)
    (output/'producer.py.snapshot').write_bytes(Path(__file__).read_bytes())
    write(output/'method-example.json',result)
    api.authenticate(pins)
    write(output/'receipt.json',{'source_sha256':api.source_map(pins),
        'output_sha256':{p.name:sha(p) for p in sorted(output.iterdir())}})
    return result


def build(output, *, elastic=False, spacing=3.0, refinement=2.0, resume=None):
    global RUN_OUTPUT
    started=time.monotonic()
    remainder, api, pins, plan, members, surfaces, _original, permanent, live, residual, original_gravity = sources()
    import numpy as np

    require(np.__version__ == "2.5.2", "pinned NumPy runtime differs")
    net = remainder.module(HERE / "corner-net-section.py", pins[HERE / "corner-net-section.py"])
    sections = remainder.module(HERE / "corner-timber-sections.py", pins[HERE / "corner-timber-sections.py"])
    previous = remainder.module(HERE / "top-host-net-sections.py", pins[HERE / "top-host-net-sections.py"])
    outer_at = previous.outer_rectangle_function()
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh immediate owned output child required")
    output.mkdir(parents=True)
    RUN_OUTPUT=output
    CACHE_AUDIT.clear()
    write(output/'cut-progress.json',{'cut_count':0})
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    write(output / "sources-before.json", api.source_map(pins))
    resumed={}
    if resume is not None:
        resume=Path(resume).resolve()
        require(resume.parent==RAW.resolve() and sha(resume/'producer.py.snapshot') in (sha(__file__),'bd860ad0bc6708f3f2e56c22fab17a06b6ce94c6e25f85c18909c25cbc97bd07'),
                'row resume requires a supported immutable producer with unchanged normal/solver methods')
        if sha(resume/'producer.py.snapshot')!=sha(__file__):
            require(sha(resume/'stop.json')=='abf7194ff71b16c7b023439316fcd9dda64c12680d2a2f71ecb271a5753cc197',
                    'specific accepted100-row stopped source differs')
        for relative,digest in read(resume/'sources-before.json').items():
            api.bind(pins,ROOT/relative,digest)
        for name in ('producer.py.snapshot','sources-before.json','checkpoint-cuts.jsonl.gz','stop.json'):
            api.bind(pins,resume/name,sha(resume/name))
        api.authenticate(pins)
        write(output/'sources-before.json',api.source_map(pins))
        for row in lines(resume/'checkpoint-cuts.jsonl.gz'):
            identity=tuple(row[k] for k in ('force_basis','state','geometry_basis','body','station_index','limit'))
            require(identity not in resumed,'duplicate resumed cut')
            resumed[identity]=row
    material = {}
    for relative in list(PACKETS)[:2]:
        for audit in read(HERE / "rawlocal" / relative / "action-audits.json")["audits"]:
            refs = audit["conditional_material"]["CF_only_reference_mpa"]
            require(audit["body"] not in material or material[audit["body"]] == refs, "material reference changed across cases")
            material[audit["body"]] = refs
    refs_permanent = {r["member"]:{"Fb":r["references_cd0_9"]["Fb_star_mpa"],
        "Ft_parallel":r["references_cd0_9"]["Ft_mpa"], "Fc_parallel":r["references_cd0_9"]["Fc_star_mpa"],
        "Fv_parallel":r["references_cd0_9"]["Fv_mpa"]} for r in permanent["members"]}
    original_refs = {r["member"]:{"Fb":r["references_cd0_9"]["Fb_star_mpa"],
        "Ft_parallel":r["references_cd0_9"]["Ft_mpa"], "Fc_parallel":r["references_cd0_9"]["Fc_star_mpa"],
        "Fv_parallel":r["references_cd0_9"]["Fv_mpa"]} for r in original_gravity["members"]}
    reused = {(r['body'],r['station_index']):r for r in
        read(HERE/'rawlocal/permanent-opening-completion/attempt02/section-recipes.json')['recipes']}
    group = read(GROUP)
    for body, geometry in group['geometries'].items():
        require(group['source_sha256'][members[body]['current_finished_step']]
                == members[body]['current_finished_step_sha256'], 'corner geometry STEP binding differs')
        require(max(abs(np.array(geometry['start_xyz_mm'])-members[body]['geometry']['start']))<1e-6,
                'corner start datum differs')
    proposal_members = read(HERE/'rawlocal/knee-bridge-permanent-resolve/attempt02/geometry.json')['members']
    profile_targets = [r for r in read(HERE/'rawlocal/profile-method-completion/attempt02/preparation.json')['targets']
                       if r['source_section_status'].startswith('BORE_FREE_')]
    require(len(profile_targets)==104,'existing finite bore-free recess target census differs')
    live_identities={(r['body'],r['saved_station_index']) for r in live}
    require(all((r['body'],r['station_index']) not in live_identities for r in profile_targets),
            'recess target overlaps an opening/terminal target')
    recipes, fields, rows_out, accounting, audits = {}, {}, [], [], []
    # Primary mechanical method validation: a real blind rectangle, with exact
    # manually integrated area. This is not a software test or review loop.
    example_regions = [{"bounds_uv_mm":[[-10,0],[-5,5]]}, {"bounds_uv_mm":[[0,10],[-5,0]]}]
    example = normal_stress(np.array([150.,0,0,0,-125.,250.]),example_regions,
                           {"Fb":10.,"Ft_parallel":10.,"Fc_parallel":10.,"Fv_parallel":10.},net,np)
    require(abs(example['properties']['area_mm2']-150)<1e-12
            and abs(example['sigma_parallel_min_max_mpa'][0]-1)<1e-12,
            "blind-section known-answer method example failed")
    write(output/'method-example.json',example)
    with (gzip.open(output/'checkpoint-cuts.jsonl.gz','wt') as cut_checkpoint,
          np.load(BASELINE / 'action-section-arrays.npz',allow_pickle=False) as baseline,
          np.load(api.ARRAYS,allow_pickle=False) as fresh,
          np.load(HERE/'rawlocal/knee-bridge-permanent-resolve/attempt02/member-actions.npz',allow_pickle=False) as gravity,
          np.load(ORIGINAL_GRAVITY/'member-actions.npz',allow_pickle=False) as reviewed_gravity):
        def evaluate(b,si,station,before,state,values,points,point_stations,refs,label,category,
                     override=None, geometry_basis='reviewed104', duration=1.):
            g = members[b]['geometry']
            frame = np.array([g[k] for k in ('axis','section_u','section_v')])
            recipe_key = geometry_basis,b,si
            if recipe_key not in recipes:
                recipes[recipe_key] = override if override is not None else actual_section(members[b],surfaces[b],station,outer_at,np)
            recipe = recipes[recipe_key]
            cut,datum = previous.global_cut(values,points,point_stations,g,station,before)
            q = np.r_[frame@cut[:3],frame@cut[3:]]
            result = {'body':b,'station_index':si,'station_mm':station,'limit':'before' if before else 'after',
                      'state':state,'force_basis':label,'category':category,'full_signed_wrench_n_nmm':q.tolist(),
                      'cut_datum_xyz_mm':datum.tolist(),'references_mpa':refs,'section_status':recipe['status'],
                      'geometry_basis':geometry_basis,'duration_CD':duration}
            identity=label,state,geometry_basis,b,si,result['limit']
            prior=resumed.get(identity)
            if prior is not None:
                require(all(prior[k]==v for k,v in result.items()),'resumed cut input/geometry/reference differs')
                if elastic:
                    require('elastic_shear' in prior or 'endpoint_limit' in prior,'resumed cut lacks elastic arithmetic')
                    if 'mesh_refinement' in prior:
                        require(prior['mesh_refinement']['spacings_mm']==[spacing,spacing/refinement],
                                'resumed mesh spacings differ')
            if recipe['regions'] is None:
                result['endpoint_limit']=endpoint_limit(q,members[b],surfaces[b],station,refs,outer_at,net,np)
            else:
                section_datum=np.array(recipe.get('datum_xyz_mm',datum))
                section_q=q.copy()
                section_q[3:]-=np.cross(frame@(section_datum-datum),section_q[:3])
                normal = prior['normal'] if prior is not None else normal_stress(section_q,recipe['regions'],refs,net,np)
                result['section_datum_xyz_mm']=section_datum.tolist()
                result['signed_wrench_at_section_datum_n_nmm']=section_q.tolist()
                result['normal']=normal
                if duration == 1.:
                    result['normal_reference_CD1_25']={k:normal[k]/1.25 for k in
                        ('normal_reference_sum','total_tension_over_Ft','total_compression_over_Fc','absolute_bending_over_Fb')}
                if elastic:
                    key = json.dumps(recipe['regions'],sort_keys=True)
                    if key not in fields:
                        write(output/'current-cut.json',{'recipe':recipe,'cut':result,'normal':normal})
                        fields[key]=[certified_tangent_field(recipe,members[b],surfaces[b],station,net,np,spacing),
                                     certified_tangent_field(recipe,members[b],surfaces[b],station,net,np,spacing/refinement)]
                    if prior is not None:
                        require(all(old['accepted_checkpoint_key']==new['accepted_checkpoint_key'] for old,new in
                            zip((prior['elastic_shear_coarse'],prior['elastic_shear']),fields[key],strict=True)),
                            'resumed shear geometry/method field identity changed')
                    coarse,fine=([prior['elastic_shear_coarse'],prior['elastic_shear']] if prior is not None else
                                 [elastic_stress(q,normal,f,refs['Fv_parallel'],np) for f in fields[key]])
                    result['elastic_shear']=fine
                    result['elastic_shear_coarse']=coarse
                    if duration == 1.:
                        result['elastic_shear']['peak_reference_ratio_CD1_25']=fine['peak_reference_ratio']/1.25
                    result['mesh_refinement']={
                        'spacings_mm':[spacing,spacing/refinement],
                        'peak_absolute_difference_mpa':abs(fine['peak_quadrature_shear_mpa']-coarse['peak_quadrature_shear_mpa']),
                        'peak_relative_difference':abs(fine['peak_quadrature_shear_mpa']-coarse['peak_quadrature_shear_mpa'])/max(fine['peak_quadrature_shear_mpa'],1e-30),
                        'rms_relative_difference':abs(fine['rms_shear_mpa']-coarse['rms_shear_mpa'])/max(fine['rms_shear_mpa'],1e-30),
                        'J_relative_difference':abs(fine['torsion_J_mm4']-coarse['torsion_J_mm4'])/fine['torsion_J_mm4'],
                        'rigorous_peak_error_bound':False}
            rows_out.append(result)
            cut_checkpoint.write(json.dumps(result,separators=(',',':'),allow_nan=False)+'\n')
            cut_checkpoint.flush()
            write(output/'cut-progress.json',{'cut_count':len(rows_out)})
            return q

        for cut in live:
            b,si,state = cut['body'],cut['saved_station_index'],cut['case']
            before = cut['limit']=='before'
            for label,array in [('reviewed104_original_frame250',baseline),('conditional_proposal_gravity_global104',fresh)]:
                prefix = state+'__'+b
                q = evaluate(b,si,cut['station_mm'],before,state,array[prefix+'__point_force_free_couple_xyz'],
                    array[b+'__point_xyz_mm'],array[b+'__point_stations_mm'],material[b],label,cut['reason'])
                saved = array[prefix+'__internal_negative_grain_u_v'][cut['saved_trace_index']]
                require(max(abs(q-saved))<1e-5,'full signed live wrench restoration differs')
        for cut in residual:
            if cut['category'] in SPECIAL:
                accounting.append(cut)
            b,si,state = cut['member'],cut['station_index'],cut['state']
            prefix = state+'__'+b
            override=None
            geometry_basis='reviewed104'
            if cut['category'] in SPECIAL:
                if cut['category']=='six_bore_spine_accounting':
                    geometry=proposal_members[b]['permanent_proposal_geometry']
                    geometry_basis='unadopted108_six_bore_spine'
                else:
                    geometry=group['geometries'][b]
                section=sections.section(geometry,cut['station_mm'])
                override={'status':'EXACT_SOURCE_BOUND_TRANSVERSE_THROUGH_CYLINDER_REGIONS',
                    'regions':section['regions'],'saved_geometry':geometry,
                    'physical_pressure_or_distributed_gravity_equivalence_claimed':False}
            q = evaluate(b,si,cut['station_mm'],cut['trace']=='before',state,
                gravity[prefix+'__point_force_free_couple_xyz'],fresh[b+'__point_xyz_mm'],fresh[b+'__point_stations_mm'],
                refs_permanent[b],('conditional_proposal_permanent_special_point_model' if cut['category'] in SPECIAL else
                    'conditional_proposal_gravity_on_unchanged_reviewed_member'),cut['category'],
                override,geometry_basis,.9)
            require(max(abs(q-np.array(cut['signed_cut_grain_u_v_n_nmm'])))<1e-5,
                    'full signed permanent wrench restoration differs')
        # Replay every original104 saved null local cut, including the original
        # four-bore spines. Artificial subsets keep their explicit method label.
        for b,member in members.items():
            for si,(station,description) in enumerate(zip(member['stations_mm'],member['rectangle_at_station'],strict=True)):
                if description['status'].startswith('BORE_FREE_'):
                    continue
                override=None
                if (b,si) in reused:
                    recipe=reused[b,si]
                    override={'status':('ARTIFICIAL_RETAINED_SUBSET_REFERENCE' if recipe['tier']=='artificial_retained_subset'
                        else 'REUSED_EXACT_SOURCE_BOUND_OPENING_REGIONS'),
                        'regions':recipe['section']['regions'],'recipe_source':recipe['source'],
                        'recipe_source_sha256':recipe['source_sha256'],'tier':recipe['tier'],
                        'physical_concentration_upper_bound':False}
                    if 'datum_xyz_mm' in recipe['section']:
                        override['datum_xyz_mm']=recipe['section']['datum_xyz_mm']
                elif b in group['geometries']:
                    section=sections.section(group['geometries'][b],station)
                    override={'status':'EXACT_SOURCE_BOUND_TRANSVERSE_THROUGH_CYLINDER_REGIONS',
                        'regions':section['regions'],'saved_geometry':group['geometries'][b]}
                for state in ('dead-only_zero','dead-only_gap'):
                    prefix=state+'__'+b
                    for before in (True,False):
                        q=evaluate(b,si,station,before,state,reviewed_gravity[prefix+'__point_force_free_couple_xyz'],
                            baseline[b+'__point_xyz_mm'],baseline[b+'__point_stations_mm'],original_refs[b],
                            'reviewed104_original_permanent','saved_original_null_opening_or_terminal',
                            override,'reviewed104_original_permanent_recipes',.9)
                        saved=reviewed_gravity[prefix+'__internal_negative_grain_u_v'][2*si+int(not before)]
                        require(max(abs(q-saved))<1e-5,'original104 permanent full signed cut restoration differs')
        # Preserve the peer's 104 authentic bore-free recess targets. Their
        # original live/dead arithmetic is separate from proposal-force reuse.
        for target in profile_targets:
            b,si,station=target['body'],target['station_index'],target['station_mm']
            require(abs(members[b]['stations_mm'][si]-station)<TOL,'recess station binding differs')
            for state in plan['case_ids']+['dead-only_zero','dead-only_gap']:
                dead=state.startswith('dead-only')
                array=reviewed_gravity if dead else baseline
                refs=original_refs[b] if dead else material[b]
                label='reviewed104_original_permanent' if dead else 'reviewed104_original_frame250'
                prefix=state+'__'+b
                for before in (True,False):
                    q=evaluate(b,si,station,before,state,array[prefix+'__point_force_free_couple_xyz'],
                        baseline[b+'__point_xyz_mm'],baseline[b+'__point_stations_mm'],refs,label,
                        'BORE_FREE_DEEP_REAR_RECESS',duration=.9 if dead else 1.)
                    saved=array[prefix+'__internal_negative_grain_u_v'][2*si+int(not before)]
                    require(max(abs(q-saved))<1e-5,'full signed recess wrench restoration differs')
        for label,array,states in [('reviewed104_original_frame250',baseline,plan['case_ids']),
                                   ('conditional_proposal_gravity_global104',fresh,plan['case_ids']),
                                   ('reviewed104_original_permanent',reviewed_gravity,['dead-only_zero','dead-only_gap']),
                                   ('conditional_proposal_gravity_on_unchanged_reviewed_member',gravity,['permanent-only_zero','permanent-only_gap'])]:
            for b in sorted({c['body'] for c in live}):
                point_array=baseline if label.startswith('reviewed104') else fresh
                points = point_array[b+'__point_xyz_mm']
                for state in states:
                    values = array[state+'__'+b+'__point_force_free_couple_xyz']
                    balance = np.r_[values[:,:3].sum(axis=0),
                        (values[:,3:]+np.cross(points,values[:,:3])).sum(axis=0)]
                    require(max(abs(balance[:3]))<1e-7 and max(abs(balance[3:]))<1e-5,
                            'whole-body force/moment balance failed')
                    audits.append({'body':b,'state':state,'force_basis':label,'whole_body_balance_n_nmm':balance.tolist()})
    with gzip.open(output/'cuts.jsonl.gz','wt') as stream:
        for row in rows_out:
            stream.write(json.dumps(row,separators=(',',':'),allow_nan=False)+'\n')
    write(output/'section-recipes.json',{'recipes':[{'geometry_basis':basis,'body':b,'station_index':si,**r}
        for (basis,b,si),r in recipes.items()]})
    write(output/'special-pressure-accounting.json',accounting)
    write(output/'action-audits.json',audits)
    write(output/'field-checkpoints.json',{'accepted_fields':CACHE_AUDIT,
        'cache_root':str(CACHE.relative_to(ROOT)),'cache_count':len(CACHE_AUDIT)})
    profile=read(HERE/'rawlocal/profile-method-completion/attempt02/checks.json')
    write(output/'reused-rear-recess-references.json',{
        'source':'rawlocal/profile-method-completion/attempt02/checks.json',
        'source_sha256':pins[HERE/'rawlocal/profile-method-completion/attempt02/checks.json'],
        'force_basis':'conditional_proposal_gravity_global104',
        'finite_signed_cuts':profile['finite_profile_signed_limit_count'],
        'comparison_summary':profile['comparison_summary'],
        'recess_endpoint_coverage':profile['recess_endpoint_coverage'],
        'applicability':'Existing actual full-depth 1:12 rear-recess sections; no NDS end-notch-depth-route acceptance inferred.'})
    require(group['source_sha256'][str((HERE/'frame-250-attempt02/response.npz').relative_to(ROOT))]
            == RESPONSE_SHA,'existing outer-cleat physical-pressure force basis differs')
    write(output/'reused-outer-cleat-live-references.json',{
        'source':str(GROUP.relative_to(HERE)),'source_sha256':pins[GROUP],
        'force_basis':'reviewed104_original_frame250','block_count':group['block_count'],
        'state_count':group['state_count'],'finite_cut_limit_count':group['finite_cut_limit_count'],
        'peak_witnesses':group['peak_witnesses'],
        'applicability':'Existing full signed half-cosine bore-pressure accounting and finished cuts on four outer cleats. Applies to original live states only; not permanent pressure closure.'})
    comparisons = {}
    for label in sorted({r['force_basis'] for r in rows_out}):
        own = [r for r in rows_out if r['force_basis']==label]
        finite = [r for r in own if 'normal' in r]
        comparisons[label] = {'target_cuts':len(own),'finite_normal_cuts':len(finite),
            'normal_reference_exceedances':sum(int(r['normal']['normal_reference_sum']>1) for r in finite),
            'peak_normal_witness':max(finite,key=lambda r:r['normal']['normal_reference_sum']) if finite else None,
            'resolved_one_sided_terminal_count':len(own)-len(finite),
            'one_sided_zero_limits':sum(int(r.get('endpoint_limit',{}).get('status')=='FINITE_ZERO_ONE_SIDED_EQUILIBRIUM_LIMIT') for r in own),
            'one_sided_divergent_limits':sum(int(r.get('endpoint_limit',{}).get('status')=='DIVERGENT_ONE_SIDED_SOURCE_POINT_ACTION_LIMIT') for r in own),
            'unresolved_endpoint_input_count':0}
        comparisons[label]['retained_subset_cuts']=sum(r['section_status']=='ARTIFICIAL_RETAINED_SUBSET_REFERENCE' for r in own)
        comparisons[label]['normal_metrics']={name:{
            'finite_count':len(finite),'above_one':sum(int(r['normal'][name]>1) for r in finite),
            'maximum_witness':max(finite,key=lambda r:r['normal'][name]) if finite else None}
            for name in ('normal_reference_sum','total_tension_over_Ft','total_compression_over_Fc','absolute_bending_over_Fb')}
        comparisons[label]['category_partition']={category:{
            'target_cuts':sum(r['category']==category for r in own),
            'finite_normal_cuts':sum(r['category']==category for r in finite),
            'normal_reference_exceedances':sum(int(r['normal']['normal_reference_sum']>1) for r in finite if r['category']==category),
            'peak_normal_reference':max((r['normal']['normal_reference_sum'] for r in finite if r['category']==category),default=None)}
            for category in sorted({r['category'] for r in own})}
        if elastic:
            shear_finite=[r for r in finite if 'peak_reference_ratio' in r['elastic_shear']]
            comparisons[label]['finite_elastic_shear_cuts']=len(shear_finite)
            comparisons[label]['elastic_shear_reference_exceedances']=sum(r['elastic_shear']['peak_reference_ratio']>1 for r in shear_finite)
            comparisons[label]['coupled_ligament_input_count']=len(finite)-len(shear_finite)
            comparisons[label]['peak_elastic_shear_witness']=max(shear_finite,key=lambda r:r['elastic_shear']['peak_reference_ratio']) if shear_finite else None
            comparisons[label]['mesh_sensitive_peak_count']=sum(int(r['mesh_refinement']['peak_relative_difference']>.05) for r in shear_finite)
            comparisons[label]['maximum_mesh_peak_relative_difference']=max(r['mesh_refinement']['peak_relative_difference'] for r in shear_finite)
    summary = {'schema':'member_opening_general_completion/v1','status':'ACTUAL_SECTION_LONGITUDINAL_REFERENCES_COMPLETE_WITH_EXPLICIT_REMAINING_DUTIES',
        'runtime':{'python':platform.python_version(),'numpy':np.__version__,
            'elapsed_seconds':time.monotonic()-started},'source_sha256':api.source_map(pins),
        'reviewed_structural_axes':104,'hillman_axes':66,'changed_geometry':False,'added_internal_v_ties_used':False,
        'six_bore_spine_geometry_used_in_separate_proposal_point_comparison_only':True,
        'comparison':comparisons,'section_recipe_count':len(recipes),
        'special_permanent_pressure_duties':dict(Counter(c['category'] for c in accounting)),
        'special_permanent_pressure_duties_point_model_compared':624,
        'physical_special_pressure_gravity_or_internal_bridge_allocation_qualified':False,
        'elastic_whole_domain_shear_executed':elastic,'section_spacings_mm':[spacing,spacing/refinement] if elastic else None,
        'unique_elastic_domains':len(fields),'native_CAD_or_frame_run':False,'tests_run':False,'review_run':False,
        'accepted_unit_field_checkpoint_count':len(CACHE_AUDIT),
        'resumed_exact_state_row_count':len(resumed),
        'coalesced_geometry_used_for_shear_only':elastic,'exact_unsnapped_longitudinal_arithmetic_preserved':True,
        'certified_tangent_state_cuts':sum('certified_tangent_geometry' in r.get('elastic_shear',{}) for r in rows_out),
        'tangent_topology_changed_state_cuts':sum(r.get('elastic_shear',{}).get('certified_tangent_geometry',{}).get('topology_changed',False) for r in rows_out),
        'complete_numerical_qualification':False,'complete_joint_acceptance':False,'physical_release':False}
    api.authenticate(pins)
    for checkpoint in CACHE_AUDIT.values():
        require(sha(ROOT/checkpoint['npz_path'])==checkpoint['npz_sha256']
                and sha(ROOT/checkpoint['metadata_path'])==checkpoint['metadata_sha256'],
                'accepted field checkpoint changed during execution')
    write(output/'summary.json',summary)
    write(output/'sources-after.json',api.source_map(pins))
    outputs={p.name:sha(p) for p in sorted(output.iterdir()) if p.is_file()}
    write(output/'receipt.json',{'source_sha256':api.source_map(pins),'output_sha256':outputs})
    api.authenticate(pins)
    return summary


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--elastic',action='store_true',help='parent serialized whole-section 2D numerical solve')
    parser.add_argument('--method-example',action='store_true',help='parent known-answer validation before whole-section runs')
    parser.add_argument('--spacing',type=float,default=3.0)
    parser.add_argument('--refinement',type=float,default=2.0,help='actual-section fine spacing = spacing/refinement')
    parser.add_argument('--resume',type=Path,help='reuse checkpoint rows from the same frozen producer and inputs')
    args=parser.parse_args()
    if args.method_example:
        result=method_example(args.output)
        print(json.dumps(result))
    else:
        require(args.spacing>0 and args.refinement>1,'positive mesh spacing and refinement>1 required')
        try:
            result=build(args.output,elastic=args.elastic,spacing=args.spacing,refinement=args.refinement,resume=args.resume)
        except Exception as error:
            if RUN_OUTPUT is not None:
                write(RUN_OUTPUT/'stop.json',{'status':'STOP_INCOMPLETE_NOT_ACCEPTANCE','error':str(error),
                    'producer_sha256':sha(__file__),'field_cache_count':len(CACHE_AUDIT),
                    'last_cut_progress':read(RUN_OUTPUT/'cut-progress.json'),
                    'field_checkpoints':CACHE_AUDIT,'physical_release':False})
            raise
        print(json.dumps({'status':result['status'],'comparison':{k:{a:b for a,b in v.items() if isinstance(b,(int,float))} for k,v in result['comparison'].items()},
                          'summary_sha256':sha(args.output/'summary.json'),'receipt_sha256':sha(args.output/'receipt.json')}))
