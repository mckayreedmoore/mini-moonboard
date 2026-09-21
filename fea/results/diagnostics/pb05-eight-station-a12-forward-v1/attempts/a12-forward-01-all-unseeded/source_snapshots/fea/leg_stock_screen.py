"""Gross-section leg stock comparison, NOT a frame solve or allowable load.

Equal E isolates geometry. Straight-strip surrogates omit the plywood knee,
holes, joint slip, shear deformation and grain-dependent material properties.
"""
import json
import math

STOCK_MM = {"2x6": 139.7, "2x8": 184.15, "2x10": 234.95, "2x12": 285.75}


def straight_layout(bolt_yz, foot_y, width_mm, bore_diameter_mm=11.1125):
    """Aim a straight strip from the floor centre through the bolt centroid.

    Side-edge fit only: not end distances, washer fit or connection resistance.
    Top cut must be designed separately. Width lies in the world YZ plane.
    """
    if (not bolt_yz or not all(len(p) == 2 for p in bolt_yz)
            or not all(math.isfinite(v) for p in bolt_yz for v in p)
            or not math.isfinite(foot_y)
            or not all(math.isfinite(v) and v > 0 for v in (width_mm, bore_diameter_mm))):
        raise ValueError("Finite bolt pairs/foot and positive width/bore required")
    y, z = (sum(p[i] for p in bolt_yz)/len(bolt_yz) for i in (0, 1))
    if z <= 0 or any(p[1] <= 0 for p in bolt_yz):
        raise ValueError("Bolt group must be above the floor")
    length = math.hypot(y-foot_y, z)
    uy, uz = (y-foot_y)/length, z/length
    offsets = [(py-foot_y)*uz-pz*uy for py, pz in bolt_yz]
    margins = [width_mm/2-abs(offset) for offset in offsets]
    return {"floor_to_bolt_centroid_mm": length,
            "angle_from_vertical_deg": math.degrees(math.atan2(abs(uy), uz)),
            "bolt_cross_grain_offsets_mm": offsets,
            "bolt_center_side_margins_mm": margins,
            "minimum_bore_side_ligament_mm": min(margins)-bore_diameter_mm/2,
            "full_bores_inside_side_edges": min(margins) >= bore_diameter_mm/2,
            "centered_width_for_bores_only_mm": 2*max(map(abs, offsets))+bore_diameter_mm,
            "level_foot_depth_mm": width_mm/uz}


def section(thickness_mm, width_mm, independent_layers=1):
    """Uncoupled layers share force equally; no parallel-axis/glue credit."""
    if (not all(math.isfinite(v) and v > 0 for v in (thickness_mm, width_mm))
            or type(independent_layers) is not int or independent_layers < 1):
        raise ValueError("Positive dimensions and a positive integer layer count required")
    t, w, n = thickness_mm, width_mm, independent_layers
    return {"area_mm2": n*t*w, "out_of_plane_I_mm4": n*w*t**3/12,
            "in_plane_I_mm4": n*t*w**3/12,
            "out_of_plane_S_mm3": n*w*t**2/6, "in_plane_S_mm3": n*t*w**2/6}


def strip_response(properties, length_mm, e_mpa=7000., effective_length_factor=1.):
    """Unit transverse cantilever response and separate ideal Euler columns.

Euler K is explicit, not inferred from the cantilever fixture. Values are
elastic mathematical references, not NDS adjusted column resistances.
"""
    if not all(math.isfinite(v) and v > 0 for v in
               (*properties.values(), length_mm, e_mpa, effective_length_factor)):
        raise ValueError("Positive finite properties, length, E and K required")
    result = {"length_mm": length_mm, "e_mpa": e_mpa,
              "euler_effective_length_factor": effective_length_factor}
    for axis in ("out_of_plane", "in_plane"):
        ei = e_mpa*properties[axis+"_I_mm4"]
        result[axis+"_unit_cantilever_compliance_mm_per_n"] = length_mm**3/(3*ei)
        result[axis+"_ideal_euler_n"] = math.pi**2*ei/(effective_length_factor*length_mm)**2
    return result


def report():
    from fea.prepare_easy_structural import digest
    from mini_moonboard import box_frame as b
    from mini_moonboard import footprint_frame as footprint
    from mini_moonboard import hybrid, timber_connections

    bend = b.point(0, 1480., hybrid.leg_normal("2x8"))
    foot = footprint.foot_center(100.)
    stocks = {"plywood_bonded_reference": section(38.1, 180.),
              "plywood_independent_equal_share": section(19.05, 180., 2),
              **{name: section(38.1, width) for name, width in STOCK_MM.items()}}
    reference = stocks["plywood_bonded_reference"]
    bolts = [c for c in timber_connections.leg_connections()
             if c.name.startswith("analysis_leg_wall_bolt_right_")]
    if len(bolts) != 4:
        raise ValueError("Expected the current four right rim bolts")
    bolt_yz = [(c.start.y, c.start.z) for c in bolts]
    rows = []
    for extension in (0., 150., 300.):
        length = math.hypot(foot.y+extension-bend.y, bend.z)
        for name, properties in stocks.items():
            row = {"stock": name, "foot_extension_from_current_mm": extension,
                "section": properties,
                "section_ratio_to_bonded_plywood": {key: value/reference[key]
                                                    for key, value in properties.items()},
                "straight_strip": strip_response(properties, length)}
            if name in STOCK_MM:
                row["direct_straight_attachment_geometry"] = straight_layout(
                    bolt_yz, foot.y+extension, STOCK_MM[name])
            rows.append(row)
    sources = ("fea/leg_stock_screen.py", "mini_moonboard/box_frame.py",
               "mini_moonboard/footprint_frame.py", "mini_moonboard/hybrid.py",
               "mini_moonboard/model.py", "mini_moonboard/timber_connections.py")
    return {"qualified_for_design": False,
            "scope": "Equal-E gross-section straight-strip screen only; not actual bent-leg or frame FEA. "
                     "E=7000 MPa for every stock is a numerical comparison, not assigned lumber/plywood properties. "
                     "K=1 Euler reference is separate from the unit cantilever response; neither represents actual fixtures. "
                     "No holes, knee, net section, shear deformation, joints, contact, gravity or load rating.",
            "dimensions_source": "https://alsc.org/uploaded/PS%2020-25%20Final.pdf",
            "bend_xyz_mm": bend.toTuple(), "current_foot_xyz_mm": foot.toTuple(),
            "rim_bolts_yz_mm": bolt_yz,
            "source_sha256": {path: digest(path) for path in sources}, "rows": rows}


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, allow_nan=False))
