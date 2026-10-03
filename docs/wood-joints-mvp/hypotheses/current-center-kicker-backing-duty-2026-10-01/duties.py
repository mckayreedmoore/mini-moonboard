"""Pure source join for current center-kicker receiver and frame duties.

The caller supplies already-loaded source reports.  This module performs no
file access, CAD import, source replay, or mechanics calculation.
"""

from copy import deepcopy
from math import isclose

CANDIDATE = "compact-floor-flush-wood-joints-development"
GEOMETRY_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
SCHEMA = "current_center_kicker_backing_duties/v1"

CENTER_SCREWS = {
    "round_kicker_left_center_1": {
        "panel": "kicker_left",
        "post": "base_post_center_left",
        "previous": "inner_kicker_backer_left",
        "facet": "base_post_center_left/facet009",
        "z_mm": 60.0,
    },
    "round_kicker_left_center_2": {
        "panel": "kicker_left",
        "post": "base_post_center_left",
        "previous": "inner_kicker_backer_left",
        "facet": "base_post_center_left/facet010",
        "z_mm": 192.0,
    },
    "round_kicker_right_center_1": {
        "panel": "kicker_right",
        "post": "base_post_center_right",
        "previous": "inner_kicker_backer_right",
        "facet": "base_post_center_right/facet009",
        "z_mm": 60.0,
    },
    "round_kicker_right_center_2": {
        "panel": "kicker_right",
        "post": "base_post_center_right",
        "previous": "inner_kicker_backer_right",
        "facet": "base_post_center_right/facet010",
        "z_mm": 192.0,
    },
}

MOVED_LOWER_AXES = {
    "round_panel_lower_left_edge_1": (
        "base_rail_bottom_left",
        "base_rail_bottom_left/facet004",
    ),
    "round_panel_lower_left_edge_2": (
        "base_rail_bottom_left",
        "base_rail_bottom_left/facet006",
    ),
    "round_panel_lower_right_edge_1": (
        "base_rail_bottom_right",
        "base_rail_bottom_right/facet016",
    ),
    "round_panel_lower_right_edge_2": (
        "base_rail_bottom_right",
        "base_rail_bottom_right/facet014",
    ),
}

SIDES = {
    "left": {
        "post": "base_post_center_left",
        "cleat": "center_post_cleat_left",
        "post_cleat_axes": ("center_post_left_1", "center_post_left_2"),
        "header_cleat_axes": ("center_post_header_left_1", "center_post_header_left_2"),
        "duty": "clip_split_header_center_left",
    },
    "right": {
        "post": "base_post_center_right",
        "cleat": "center_post_cleat_right",
        "post_cleat_axes": ("center_post_right_1", "center_post_right_2"),
        "header_cleat_axes": (
            "center_post_header_right_1",
            "center_post_header_right_2",
        ),
        "duty": "clip_split_header_center_right",
    },
}

EXPECTED_ACTION_CASES = {"a12-rear", "a1-rear", "k12-rear"}
EXPECTED_INCREMENT_INDEXES = set(range(7))
EXPECTED_INCREMENT_FACTORS = {
    0: 0.1,
    1: 0.2,
    2: 0.3,
    3: 0.45,
    4: 0.675,
    5: 0.925,
    6: 1.0,
}
_OLD_BACKERS = {"inner_kicker_backer_left", "inner_kicker_backer_right"}


class DutiesInputError(ValueError):
    """Raised when source identities or frozen coverage do not reconcile."""


def _need(condition, message):
    if not condition:
        raise DutiesInputError(message)


def _mapping(value, where):
    _need(isinstance(value, dict), f"{where} must be an object")
    return value


def _list(value, where):
    _need(isinstance(value, list), f"{where} must be a list")
    return value


def _rows_by(rows, key, where):
    indexed = {}
    for row in _list(rows, where):
        _mapping(row, f"{where} row")
        identity = row.get(key)
        _need(isinstance(identity, str) and identity, f"{where} row lacks {key}")
        _need(identity not in indexed, f"duplicate {key} {identity!r} in {where}")
        indexed[identity] = row
    return indexed


def _same_number(left, right, where, tolerance=1e-8):
    _need(
        isinstance(left, (int, float))
        and isinstance(right, (int, float))
        and isclose(float(left), float(right), rel_tol=0.0, abs_tol=tolerance),
        f"{where} does not match: {left!r} != {right!r}",
    )


def _same_vector(left, right, where, tolerance=1e-8):
    _need(
        isinstance(left, (list, tuple))
        and isinstance(right, (list, tuple))
        and len(left) == len(right),
        f"{where} has incompatible vector dimensions",
    )
    for index, (a, b) in enumerate(zip(left, right)):
        _same_number(a, b, f"{where}[{index}]", tolerance=tolerance)


def _pair_key(members, where):
    _need(
        isinstance(members, (list, tuple)) and len(members) == 2,
        f"{where} must name two members",
    )
    _need(
        all(isinstance(member, str) and member for member in members),
        f"{where} has an invalid member",
    )
    _need(members[0] != members[1], f"{where} repeats a member")
    return tuple(sorted(members))


def _assert_current_source(source, where, *, revision_key="geometry_revision_id"):
    _mapping(source, where)
    _need(source.get("candidate") == CANDIDATE, f"{where} candidate mismatch")
    _need(
        source.get(revision_key) == GEOMETRY_REVISION,
        f"{where} geometry revision mismatch",
    )


def _assert_graph_revision(graph):
    _mapping(graph, "contact graph")
    _need(
        graph.get("revision_id") == GEOMETRY_REVISION,
        "contact graph geometry revision mismatch",
    )


def _index_surface_members(surfaces):
    rows = _rows_by(surfaces.get("records"), "member_id", "surface register records")
    return rows


def _index_edges(graph):
    result = {}
    for edge in _list(graph.get("edges"), "contact graph edges"):
        _mapping(edge, "contact graph edge")
        key = _pair_key(edge.get("member_ids"), "contact graph edge member_ids")
        _need(key not in result, f"duplicate contact graph edge {key!r}")
        result[key] = edge
    return result


def _validate_panel_screw_sources(panel_report, manifest, graph, axis_features):
    inventory = _mapping(panel_report.get("inventory"), "panel report inventory")
    _assert_current_source(inventory, "panel report inventory")

    panel_axes = _rows_by(
        inventory.get("axes"), "axis_id", "panel report inventory axes"
    )
    manifest_axes = _rows_by(
        manifest.get("panel_kicker_screw_axes"), "axis_id", "manifest panel/kicker axes"
    )
    graph_axes = _rows_by(
        _mapping(graph.get("inventories"), "contact graph inventories").get(
            "current_panel_screw_axes"
        ),
        "axis_id",
        "contact graph panel/kicker axes",
    )
    feature_group = _mapping(
        _mapping(axis_features.get("source_axis_groups"), "axis feature groups").get(
            "panel_kicker_screw_axes"
        ),
        "axis feature panel/kicker group",
    )
    feature_axes = _rows_by(
        feature_group.get("axes"), "axis_id", "axis feature panel/kicker axes"
    )

    expected_ids = set(panel_axes)
    _need(
        len(expected_ids) == 66,
        "panel report does not contain exactly 66 unique screw axes",
    )
    for name, index in (
        ("manifest", manifest_axes),
        ("contact graph", graph_axes),
        ("axis feature register", feature_axes),
    ):
        _need(
            set(index) == expected_ids,
            f"{name} panel/kicker axis IDs do not match the panel report",
        )

    moved = {
        axis_id
        for axis_id, row in panel_axes.items()
        if row.get("current_location_status") == "moved"
    }
    unchanged = {
        axis_id
        for axis_id, row in panel_axes.items()
        if row.get("current_location_status") == "source_station_retained"
    }
    _need(
        len(moved) == 8 and len(unchanged) == 58 and len(moved | unchanged) == 66,
        "panel move census is not 58 retained plus 8 moved",
    )
    counts = _mapping(inventory.get("counts"), "panel report inventory counts")
    _need(
        counts.get("panel_kicker_axes_total") == 66,
        "panel inventory count does not state 66 axes",
    )
    _need(
        counts.get("moved_axes") == 8
        and counts.get("unchanged_source_station_axes") == 58,
        "panel inventory move counts do not reconcile",
    )
    manifest_counts = _mapping(
        manifest.get("inventory_counts"), "manifest inventory counts"
    )
    _need(
        manifest_counts.get("panel_kicker_screw_axes") == 66,
        "manifest panel/kicker count mismatch",
    )
    _need(
        manifest_counts.get("panel_axes_owner_moved") == 8
        and manifest_counts.get("panel_axes_unchanged") == 58,
        "manifest move counts mismatch",
    )
    _need(
        feature_group.get("axis_count") == 66,
        "axis feature panel/kicker count mismatch",
    )
    _need(
        set(feature_group.get("axis_ids", [])) == expected_ids,
        "axis feature panel/kicker declared IDs mismatch",
    )

    for axis_id, panel_axis in panel_axes.items():
        manifest_axis = manifest_axes[axis_id]
        graph_axis = graph_axes[axis_id]
        feature_axis = feature_axes[axis_id]
        for source_name, source_axis in (
            ("manifest", manifest_axis),
            ("contact graph", graph_axis),
        ):
            _need(
                source_axis.get("current_location_status")
                == panel_axis.get("current_location_status"),
                f"{source_name} move status mismatch for {axis_id}",
            )
            for field in (
                "panel_member",
                "receiver_member",
                "previous_receiver_member",
            ):
                _need(
                    source_axis.get(field) == panel_axis.get(field),
                    f"{source_name} {field} mismatch for {axis_id}",
                )
            _same_vector(
                source_axis.get("origin_global_xyz_mm"),
                panel_axis.get("origin_global_xyz_mm"),
                f"{source_name} origin for {axis_id}",
            )
            _same_vector(
                source_axis.get("axis_global_xyz"),
                panel_axis.get("axis_global_xyz"),
                f"{source_name} direction for {axis_id}",
            )
        _need(
            feature_axis.get("axis_group") == "panel_kicker_screw_axes",
            f"axis feature group mismatch for {axis_id}",
        )
        station = _mapping(
            feature_axis.get("panel_axis_station_reconciliation"),
            f"axis feature station {axis_id}",
        )
        _need(
            station.get("current_location_status")
            == panel_axis.get("current_location_status"),
            f"axis feature move status mismatch for {axis_id}",
        )
        _need(
            station.get("current_receiver_member") == panel_axis.get("receiver_member"),
            f"axis feature receiver mismatch for {axis_id}",
        )
        _same_vector(
            station.get("current_axis_origin_global_xyz_mm"),
            panel_axis.get("origin_global_xyz_mm"),
            f"axis feature origin for {axis_id}",
        )
        _same_vector(
            station.get("current_axis_direction_global_xyz"),
            panel_axis.get("axis_global_xyz"),
            f"axis feature direction for {axis_id}",
        )

    _need(
        set(CENTER_SCREWS).issubset(moved),
        "one or more current center screws are not recorded as moved",
    )
    _need(
        set(MOVED_LOWER_AXES).issubset(moved),
        "the four lower-edge moved screw IDs do not reconcile",
    )
    _need(
        moved == set(CENTER_SCREWS) | set(MOVED_LOWER_AXES),
        "the eight moved screw IDs differ from the reviewed move set",
    )

    for axis_id, expected in CENTER_SCREWS.items():
        panel_axis = panel_axes[axis_id]
        sources = (panel_axis, manifest_axes[axis_id], graph_axes[axis_id])
        feature_axis = feature_axes[axis_id]
        for source in sources:
            _need(
                source.get("panel_member") == expected["panel"],
                f"wrong panel for {axis_id}",
            )
            _need(
                source.get("receiver_member") == expected["post"],
                f"wrong current receiver for {axis_id}",
            )
            _need(
                source.get("previous_receiver_member") == expected["previous"],
                f"old receiver provenance missing for {axis_id}",
            )
            _need(
                source.get("current_location_status") == "moved",
                f"{axis_id} must remain an owner-directed move",
            )
            policy = source.get(
                "purchased_product_policy", source.get("purchased_policy")
            )
            if policy is not None:
                _need(
                    "Hillman 42605" in policy,
                    f"Hillman 42605 policy mismatch for {axis_id}",
                )
        _need(
            manifest_axes[axis_id].get("purchased_nominal_length_mm") == 63.5,
            f"manifest Hillman length mismatch for {axis_id}",
        )
        _need(
            panel_axis.get("nominal_embedment_envelope", {}).get(
                "purchased_nominal_length_mm"
            )
            == 63.5,
            f"panel report Hillman length mismatch for {axis_id}",
        )
        _same_number(
            panel_axis.get("origin_global_xyz_mm", [None, None, None])[2],
            expected["z_mm"],
            f"center station Z for {axis_id}",
        )
        _same_vector(
            panel_axis.get("axis_global_xyz"),
            [0.0, -1.0, 0.0],
            f"center screw direction for {axis_id}",
        )

        report_features = _list(
            panel_axis.get("features"), f"panel report finished features for {axis_id}"
        )
        _need(
            len(report_features) == 1,
            f"{axis_id} must map to exactly one finished bore patch",
        )
        report_feature = report_features[0]
        _need(
            report_feature.get("feature_id") == expected["facet"],
            f"finished feature mismatch for {axis_id}",
        )
        _need(
            report_feature.get("match_status") == "matched_bore_patch",
            f"finished bore match status mismatch for {axis_id}",
        )
        bore = _mapping(
            report_feature.get("bore_patch"), f"finished bore patch {axis_id}"
        )
        _need(
            bore.get("surface_kind") == "CYLINDER"
            and bore.get("material_side_geometry") == "bore_like",
            f"finished face is not the recorded bore-like cylinder for {axis_id}",
        )
        _need(
            bore.get("finite_interval_status") == "contained_in_source_finite_interval",
            f"finished bore interval mismatch for {axis_id}",
        )
        _same_number(
            bore.get("axial_overlap_length_mm"),
            45.24375,
            f"finished bore overlap for {axis_id}",
            tolerance=1e-6,
        )
        _same_vector(
            bore.get("patch_interval_projected_from_axis_datum_mm"),
            [18.25625, 63.5],
            f"finished bore interval for {axis_id}",
            tolerance=1e-6,
        )

        nominal = _mapping(
            panel_axis.get("nominal_embedment_envelope"), f"nominal envelope {axis_id}"
        )
        _need(
            nominal.get("status")
            == "modeled receiver overlap only; not actual screw embedment or installed engagement",
            f"nominal envelope claim boundary mismatch for {axis_id}",
        )
        _same_number(
            nominal.get("source_historical_occupied_length_mm"),
            50.8,
            f"historical occupied-length provenance for {axis_id}",
        )
        _need(
            nominal.get("purchased_nominal_length_mm") == 63.5,
            f"nominal purchase envelope mismatch for {axis_id}",
        )
        provenance = _mapping(
            panel_axis.get("source_provenance"), f"source provenance for {axis_id}"
        )
        _need(
            provenance.get("receiver_to_frame_path_complete") is False,
            f"receiver-to-frame path is marked complete for {axis_id}",
        )

        _need(
            feature_axis.get("source_hardware_policy", {}).get(
                "purchased_nominal_length_mm"
            )
            == 63.5,
            f"feature register Hillman length mismatch for {axis_id}",
        )
        memberships = _list(
            feature_axis.get("receiver_memberships"),
            f"axis feature receiver memberships for {axis_id}",
        )
        _need(
            len(memberships) == 1,
            f"{axis_id} must have exactly one current finished receiver membership",
        )
        membership = memberships[0]
        _need(
            membership.get("receiver_member_id") == expected["post"],
            f"axis feature receiver mismatch for {axis_id}",
        )
        _need(
            membership.get("match_status") == "matched_bore_patch",
            f"axis feature match status mismatch for {axis_id}",
        )
        _need(
            membership.get("matched_feature_ids") == [expected["facet"]],
            f"axis feature ID mismatch for {axis_id}",
        )
        candidates = [
            candidate
            for candidate in _list(
                membership.get("cylinder_surface_candidates"),
                f"axis feature candidates for {axis_id}",
            )
            if candidate.get("association_status") == "eligible_bore_patch"
        ]
        _need(
            len(candidates) == 1
            and candidates[0].get("feature_id") == expected["facet"],
            f"axis feature bore candidate mismatch for {axis_id}",
        )
        _need(
            feature_axis.get("source_axis_fields", {}).get("axis_length_mm") == 63.5,
            f"axis feature finite length mismatch for {axis_id}",
        )

        binding = _mapping(
            report_feature.get("finished_step_binding"),
            f"panel finished STEP binding for {axis_id}",
        )
        member_binding = _mapping(
            membership.get("current_finished_step_binding"),
            f"feature register finished STEP binding for {axis_id}",
        )
        _need(
            binding.get("sha256") == member_binding.get("file_sha256"),
            f"finished STEP byte identity mismatch for {axis_id}",
        )
        _need(
            binding.get("path") == member_binding.get("path"),
            f"finished STEP path mismatch for {axis_id}",
        )
        _same_number(
            binding.get("size_bytes"),
            member_binding.get("size_bytes"),
            f"finished STEP size for {axis_id}",
        )

    for axis_id, (receiver, feature_id) in MOVED_LOWER_AXES.items():
        axis = panel_axes[axis_id]
        _need(
            axis.get("receiver_member") == receiver,
            f"lower-edge moved receiver mismatch for {axis_id}",
        )
        features = _list(
            axis.get("features"), f"lower-edge finished features for {axis_id}"
        )
        _need(
            len(features) == 1 and features[0].get("feature_id") == feature_id,
            f"lower-edge moved feature mismatch for {axis_id}",
        )

    return panel_axes, manifest_axes, graph_axes, feature_axes, moved, unchanged


def _validate_no_old_shapes(manifest, graph, surfaces, envelopes, inventory):
    center_check = _mapping(
        inventory.get("current_center_kicker_receiver_check"),
        "current center receiver check",
    )
    _need(
        center_check.get("current_receiver_map")
        == {axis_id: expected["post"] for axis_id, expected in CENTER_SCREWS.items()},
        "current center-kicker receiver map mismatch",
    )
    _need(
        center_check.get("previous_backer_shapes_present_in_current_composition")
        is False,
        "former center backer shapes are marked present",
    )
    _need(
        center_check.get("previous_backer_shape_ids_present") == [],
        "former center backer shape IDs are present",
    )

    current_member_ids = {
        row.get("member_id")
        for row in _list(manifest.get("physical_members"), "manifest physical members")
    }
    graph_member_ids = {
        row.get("member_id")
        for row in _list(
            _mapping(graph.get("inventories"), "graph inventories").get(
                "physical_members"
            ),
            "graph physical members",
        )
    }
    surface_member_ids = set(_index_surface_members(surfaces))
    stock_member_ids = {
        row.get("member_id")
        for row in _list(envelopes.get("records"), "stock envelope records")
    }
    for name, identifiers in (
        ("manifest", current_member_ids),
        ("contact graph", graph_member_ids),
        ("surface register", surface_member_ids),
        ("stock envelope register", stock_member_ids),
    ):
        _need(
            not (_OLD_BACKERS & identifiers),
            f"former center backer shape identity appears in current {name}",
        )


def _candidate_bolt_expected_pairs():
    result = {}
    for side, spec in SIDES.items():
        for axis_id in spec["post_cleat_axes"]:
            result[axis_id] = (spec["post"], spec["cleat"], "post_to_cleat", side)
        for axis_id in spec["header_cleat_axes"]:
            result[axis_id] = ("base_header", spec["cleat"], "cleat_to_header", side)
    return result


def _validate_frame_duties(manifest, graph, axis_features, surfaces, envelopes):
    manifest_bolts = _rows_by(
        manifest.get("candidate_bolt_axes"), "axis_id", "manifest candidate bolt axes"
    )
    graph_bolts = _rows_by(
        _mapping(graph.get("inventories"), "contact graph inventories").get(
            "candidate_bolt_axes"
        ),
        "axis_id",
        "contact graph candidate bolt axes",
    )
    feature_group = _mapping(
        _mapping(axis_features.get("source_axis_groups"), "axis feature groups").get(
            "candidate_bolt_axes"
        ),
        "axis feature candidate bolt group",
    )
    feature_bolts = _rows_by(
        feature_group.get("axes"), "axis_id", "axis feature candidate bolt axes"
    )
    expected = _candidate_bolt_expected_pairs()
    _need(
        len(manifest_bolts) == 92,
        "manifest does not contain exactly 92 candidate bolt axes",
    )
    for name, index in (
        ("contact graph", graph_bolts),
        ("axis feature register", feature_bolts),
    ):
        _need(
            set(index) == set(manifest_bolts),
            f"{name} candidate bolt IDs do not match the manifest",
        )
    _need(
        feature_group.get("axis_count") == 92,
        "axis feature candidate bolt count mismatch",
    )
    _need(
        set(feature_group.get("axis_ids", [])) == set(manifest_bolts),
        "axis feature declared candidate bolt IDs mismatch",
    )
    _need(
        set(expected).issubset(manifest_bolts),
        "one or more reviewed center post/cleat bolt axes are absent",
    )

    target_duties = set(_list(manifest.get("target_duties"), "manifest target duties"))
    surface_members = _index_surface_members(surfaces)
    stock_members = _rows_by(
        envelopes.get("records"), "member_id", "stock envelope records"
    )
    manifest_finished = _rows_by(
        manifest.get("finished_member_step_bindings"),
        "member_id",
        "manifest finished member STEP bindings",
    )
    edge_by_pair = _index_edges(graph)
    header = "base_header"
    edge_contract = {}

    for side, spec in SIDES.items():
        _need(
            spec["duty"] in target_duties,
            f"center structural duty {spec['duty']} is absent from the manifest",
        )
        for pair_name, pair in (
            ("post_header", (header, spec["post"])),
            ("post_cleat", (spec["post"], spec["cleat"])),
            ("cleat_header", (header, spec["cleat"])),
        ):
            key = _pair_key(pair, f"{side} {pair_name} pair")
            edge = edge_by_pair.get(key)
            _need(edge is not None, f"contact graph lacks {side} {pair_name} edge")
            _need(
                edge.get("interface_geometry_state") == "finite_planar_face_contact",
                f"{side} {pair_name} is not recorded as finite face contact",
            )
            _need(
                edge.get("geometry_state") == "finite_opposed_planar_touch",
                f"{side} {pair_name} contact classification mismatch",
            )
            _need(
                edge.get("common_volume_mm3") == 0.0,
                f"{side} {pair_name} has unexpected common volume",
            )
            _need(
                edge.get("finite_shared_planar_face_area_mm2", 0) > 0,
                f"{side} {pair_name} lacks a finite shared-face area record",
            )
            edge_contract[(side, pair_name)] = edge

        post_header_edge = edge_contract[(side, "post_header")]
        _need(
            post_header_edge.get("candidate_bolt_associations") == [],
            f"{side} post/header seat unexpectedly has candidate bolt membership",
        )
        _need(
            post_header_edge.get("retained_frame_bolt_source_membership") == [],
            f"{side} post/header seat unexpectedly has retained bolt membership",
        )

    relevant_member_ids = {"base_header"}
    for spec in SIDES.values():
        relevant_member_ids.update((spec["post"], spec["cleat"]))
    stock_records = {}
    for member_id in sorted(relevant_member_ids):
        _need(
            member_id in stock_members and member_id in surface_members,
            f"stock/surface register lacks current member {member_id}",
        )
        stock = stock_members[member_id]
        surface = surface_members[member_id]
        binding = _mapping(
            surface.get("step_binding"), f"surface STEP binding for {member_id}"
        )
        manifest_binding = manifest_finished.get(member_id)
        _need(
            manifest_binding is not None,
            f"manifest lacks finished STEP binding for {member_id}",
        )
        _need(
            manifest_binding.get("file_sha256") == binding.get("file_sha256"),
            f"manifest/surface STEP SHA mismatch for {member_id}",
        )
        _need(
            manifest_binding.get("path") == binding.get("path"),
            f"manifest/surface STEP path mismatch for {member_id}",
        )
        _need(
            manifest_binding.get("size_bytes") == binding.get("size_bytes"),
            f"manifest/surface STEP size mismatch for {member_id}",
        )
        _need(
            binding.get("file_sha256") == stock.get("current_finished_step_sha256"),
            f"stock/surface STEP binding mismatch for {member_id}",
        )
        _need(
            binding.get("path") == stock.get("current_finished_step_path"),
            f"stock/surface STEP path mismatch for {member_id}",
        )
        stock_records[member_id] = {
            "member_id": member_id,
            "member_kind": stock.get("member_kind"),
            "stock_class": stock.get("stock_class"),
            "stock_blank_length_mm": stock.get("stock_blank_length_mm"),
            "original_stock_section_mm": deepcopy(
                stock.get("original_stock_section_mm")
            ),
            "finished_oriented_spans_g_q_r_mm": deepcopy(
                stock.get("original_stock_containment", {}).get(
                    "finished_oriented_spans_g_q_r_mm"
                )
            ),
            "grade_assignment_status": stock.get("grade_assignment_status"),
            "conditional_grain_axis_global_xyz": deepcopy(
                stock.get("conditional_grain_axis_global_xyz")
            ),
            "proposed_frame": deepcopy(stock.get("proposed_frame")),
            "containment_status": stock.get("containment_status"),
            "current_finished_step_path": stock.get("current_finished_step_path"),
            "current_finished_step_sha256": stock.get("current_finished_step_sha256"),
            "surface_step_binding": deepcopy(binding),
            "proposal_limits": deepcopy(stock.get("proposal_limits", [])),
        }

    candidate_bolts = []
    side_paths = {side: {"post_cleat": [], "cleat_header": []} for side in SIDES}
    for axis_id, (member_a, member_b, role, side) in expected.items():
        manifest_axis = manifest_bolts[axis_id]
        graph_axis = graph_bolts[axis_id]
        feature_axis = feature_bolts[axis_id]
        pair = (member_a, member_b)
        pair_key = _pair_key(pair, f"bolt {axis_id} receiver pair")
        association_rows = _list(
            manifest_axis.get("geometric_member_pair_associations"),
            f"manifest associations for {axis_id}",
        )
        _need(
            len(association_rows) == 1,
            f"{axis_id} must have one manifest receiver-pair association",
        )
        _need(
            _pair_key(
                association_rows[0].get("member_pair"), f"manifest pair for {axis_id}"
            )
            == pair_key,
            f"manifest receiver pair mismatch for {axis_id}",
        )
        _need(
            association_rows[0].get("physical_head_to_nut_order_established") is False,
            f"physical stack order was inferred for {axis_id}",
        )
        _need(
            _pair_key(
                manifest_axis.get("receiver_member_ids"),
                f"manifest receiver IDs for {axis_id}",
            )
            == pair_key,
            f"manifest receiver IDs mismatch for {axis_id}",
        )
        _need(
            manifest_axis.get("station_id") == SIDES[side]["duty"],
            f"candidate duty/station mismatch for {axis_id}",
        )
        _need(
            manifest_axis.get("trial_id") == "wj05-center-node-posts-x190-outward-v1",
            f"candidate trial mismatch for {axis_id}",
        )
        _need(
            manifest_axis.get("family") == "wj05_center_x190",
            f"candidate family mismatch for {axis_id}",
        )
        _need(
            "unselected" in manifest_axis.get("hardware_status", ""),
            f"hardware selection status changed for {axis_id}",
        )
        _need(
            "not a purchase length" in manifest_axis.get("length_status", ""),
            f"length claim boundary changed for {axis_id}",
        )

        graph_pairs = _list(
            graph_axis.get("member_pair_associations"),
            f"graph associations for {axis_id}",
        )
        _need(
            len(graph_pairs) == 1,
            f"{axis_id} must have one graph receiver-pair association",
        )
        _need(
            _pair_key(graph_pairs[0].get("member_pair"), f"graph pair for {axis_id}")
            == pair_key,
            f"graph receiver pair mismatch for {axis_id}",
        )
        _need(
            graph_pairs[0].get("physical_head_to_nut_order_established") is False,
            f"graph infers stack order for {axis_id}",
        )
        _need(
            _pair_key(
                graph_axis.get("receiver_member_ids_as_recorded"),
                f"graph receiver IDs for {axis_id}",
            )
            == pair_key,
            f"graph receiver IDs mismatch for {axis_id}",
        )
        _need(
            "not interpreted as physical head-to-nut order"
            in graph_axis.get("receiver_member_order_semantics", ""),
            f"graph receiver order semantics changed for {axis_id}",
        )

        feature_fields = _mapping(
            feature_axis.get("source_axis_fields"),
            f"feature source axis fields for {axis_id}",
        )
        geometry = _mapping(
            manifest_axis.get("geometry"), f"manifest geometry for {axis_id}"
        )
        _same_vector(
            feature_fields.get("datum_global_xyz_mm"),
            geometry.get("shaft_center_global_xyz_mm"),
            f"candidate bolt datum for {axis_id}",
        )
        _same_vector(
            feature_fields.get("direction_global_xyz"),
            geometry.get("axis_head_to_nut_global"),
            f"candidate bolt direction for {axis_id}",
        )
        _same_number(
            feature_fields.get("axis_length_mm"),
            geometry.get("modeled_shaft_occupied_length_mm"),
            f"candidate bolt length for {axis_id}",
        )
        _same_number(
            feature_fields.get("occupied_diameter_mm"),
            geometry.get("modeled_shaft_diameter_mm"),
            f"candidate bolt diameter for {axis_id}",
        )
        finite_interval = feature_fields.get("finite_interval_from_datum_mm")
        expected_half = float(geometry["modeled_shaft_occupied_length_mm"]) / 2.0
        _same_vector(
            finite_interval,
            [-expected_half, expected_half],
            f"candidate bolt finite interval for {axis_id}",
        )

        memberships = _list(
            feature_axis.get("receiver_memberships"),
            f"candidate receiver features for {axis_id}",
        )
        _need(
            len(memberships) == 2,
            f"{axis_id} must have two finished receiver memberships",
        )
        feature_member_ids = set()
        feature_pairs = []
        for membership in memberships:
            _need(
                membership.get("match_status") == "matched_bore_patch",
                f"candidate bore match status mismatch for {axis_id}",
            )
            member_id = membership.get("receiver_member_id")
            feature_member_ids.add(member_id)
            ids = _list(
                membership.get("matched_feature_ids"),
                f"matched features for {axis_id}/{member_id}",
            )
            _need(
                len(ids) == 1,
                f"{axis_id}/{member_id} must have exactly one finished bore feature",
            )
            feature_id = ids[0]
            members = surface_members.get(member_id)
            _need(
                members is not None,
                f"surface register lacks candidate receiver {member_id}",
            )
            finished_binding = _mapping(
                membership.get("current_finished_step_binding"),
                f"candidate finished binding for {axis_id}/{member_id}",
            )
            _need(
                finished_binding.get("file_sha256")
                == members.get("step_binding", {}).get("file_sha256"),
                f"candidate surface STEP SHA mismatch for {axis_id}/{member_id}",
            )
            surface_features = _rows_by(
                members.get("features"),
                "feature_id",
                f"surface features for {member_id}",
            )
            surface_feature = surface_features.get(feature_id)
            _need(
                surface_feature is not None,
                f"finished surface register lacks {feature_id}",
            )
            _need(
                surface_feature.get("surface_kind") == "CYLINDER",
                f"candidate feature {feature_id} is not cylindrical",
            )
            cylinder = _mapping(
                surface_feature.get("cylinder"), f"surface cylinder {feature_id}"
            )
            _need(
                cylinder.get("material_side_geometry") == "bore_like",
                f"candidate surface {feature_id} is not the registered bore-like side",
            )
            feature_pairs.append(
                {
                    "receiver_member_id": member_id,
                    "feature_id": feature_id,
                    "match_status": membership.get("match_status"),
                    "step_binding": deepcopy(finished_binding),
                    "axis_in_stock_frame": deepcopy(
                        membership.get("axis_in_stock_frame")
                    ),
                    "surface_feature": deepcopy(surface_feature),
                }
            )
        _need(
            feature_member_ids == set(pair),
            f"feature receiver pair mismatch for {axis_id}",
        )

        graph_edge = edge_contract[
            (side, "post_cleat" if role == "post_to_cleat" else "cleat_header")
        ]
        edge_axis_ids = [
            row.get("axis_id")
            for row in graph_edge.get("candidate_bolt_associations", [])
        ]
        expected_edge_ids = list(
            SIDES[side]["post_cleat_axes"]
            if role == "post_to_cleat"
            else SIDES[side]["header_cleat_axes"]
        )
        _need(
            set(edge_axis_ids) == set(expected_edge_ids)
            and len(edge_axis_ids) == len(expected_edge_ids),
            f"contact graph bolt duties mismatch for {side} {role}",
        )
        graph_assoc = [
            row
            for row in graph_edge["candidate_bolt_associations"]
            if row.get("axis_id") == axis_id
        ]
        _need(
            len(graph_assoc) == 1,
            f"contact graph does not uniquely associate {axis_id}",
        )
        _need(
            _pair_key(graph_assoc[0].get("member_pair"), f"edge pair for {axis_id}")
            == pair_key,
            f"contact graph edge pair mismatch for {axis_id}",
        )
        _need(
            graph_assoc[0].get("physical_head_to_nut_order_established") is False,
            f"contact graph edge infers stack order for {axis_id}",
        )

        source_record = {
            "axis_id": axis_id,
            "side": side,
            "attachment_role": role,
            "receiver_pair_as_recorded": deepcopy(
                association_rows[0].get("receiver_pair_as_recorded")
            ),
            "member_pair": list(pair),
            "station_id": manifest_axis.get("station_id"),
            "trial_id": manifest_axis.get("trial_id"),
            "family": manifest_axis.get("family"),
            "manifest_axis": deepcopy(manifest_axis),
            "contact_graph_axis": deepcopy(graph_axis),
            "feature_memberships": feature_pairs,
            "physical_head_to_nut_order_established": False,
            "capacity_or_resistance_established": False,
        }
        candidate_bolts.append(source_record)
        side_paths[side][
            "post_cleat" if role == "post_to_cleat" else "cleat_header"
        ].append(axis_id)

    duties = []
    for side, spec in SIDES.items():
        duties.append(
            {
                "side": side,
                "target_duty": spec["duty"],
                "panel_receiver_post": spec["post"],
                "direct_post_header_seat": {
                    "member_pair": [spec["post"], header],
                    "contact_graph_edge": deepcopy(
                        edge_contract[(side, "post_header")]
                    ),
                    "candidate_bolt_axes": [],
                    "retained_frame_bolt_membership": [],
                    "status": "finite contact geometry only; no active contact action or support qualification",
                },
                "post_to_cleat_attachment": {
                    "member_pair": [spec["post"], spec["cleat"]],
                    "contact_graph_edge": deepcopy(edge_contract[(side, "post_cleat")]),
                    "candidate_bolt_axes": list(side_paths[side]["post_cleat"]),
                },
                "cleat_to_header_attachment": {
                    "member_pair": [spec["cleat"], header],
                    "contact_graph_edge": deepcopy(
                        edge_contract[(side, "cleat_header")]
                    ),
                    "candidate_bolt_axes": list(side_paths[side]["cleat_header"]),
                },
                "geometric_route": [spec["post"], spec["cleat"], header],
                "complete_mechanical_load_path_established": False,
                "force_split_calculated": False,
            }
        )

    return candidate_bolts, duties, stock_records, edge_contract


def _validate_action_state(state, expected_axis_receivers):
    case_id = state.get("case")
    increment_index = state.get("increment_index")
    load_factor = state.get("load_factor")
    _need(case_id in EXPECTED_ACTION_CASES, f"unexpected saved action case {case_id!r}")
    _need(
        increment_index in EXPECTED_INCREMENT_INDEXES,
        f"unexpected increment index for {case_id}",
    )
    _need(
        isinstance(load_factor, (int, float)) and 0.0 < float(load_factor) <= 1.0,
        f"invalid load factor for {case_id}/{increment_index}",
    )
    _same_number(
        load_factor,
        EXPECTED_INCREMENT_FACTORS[increment_index],
        f"saved action factor for {case_id}/{increment_index}",
    )

    screw_rows = _rows_by(
        state.get("screw_states"),
        "axis_id",
        f"saved screw states {case_id}/{increment_index}",
    )
    _need(
        set(expected_axis_receivers).issubset(screw_rows),
        f"saved action state dropped one or more center screw axes at {case_id}/{increment_index}",
    )
    selected = []
    for axis_id, receiver in expected_axis_receivers.items():
        row = screw_rows[axis_id]
        expected = CENTER_SCREWS[axis_id]
        _need(
            row.get("panel_member") == expected["panel"],
            f"saved action panel mismatch for {axis_id}",
        )
        _need(
            row.get("receiver_member") == receiver,
            f"saved action receiver mismatch for {axis_id}",
        )
        _same_number(
            row.get("load_factor"),
            load_factor,
            f"saved screw/action state load factor for {axis_id}",
        )
        lateral = _list(
            row.get("lateral_scalar_components"),
            f"lateral action components for {axis_id}",
        )
        _need(len(lateral) == 2, f"{axis_id} must retain two lateral source scalars")
        for component in lateral:
            _need(
                "signed_force_on_first_local_n" in component
                and "force_rounding_radius_local_n" in component,
                f"{axis_id} lateral scalar/sign/radius missing",
            )
            _need(
                "source_row_id" in component and "local_dof" in component,
                f"{axis_id} lateral scalar source identity missing",
            )
        withdrawal = _mapping(
            row.get("withdrawal_scalar_component"),
            f"withdrawal source scalar for {axis_id}",
        )
        _need(
            "native_internal_force_n" in withdrawal
            and "native_internal_radius_n" in withdrawal,
            f"{axis_id} withdrawal force/radius missing",
        )
        for name in (
            "same_state_panel_screw_wrench_at_panel_centroid",
            "same_state_receiver_screw_wrench_at_receiver_centroid",
        ):
            wrench = _mapping(row.get(name), f"{name} for {axis_id}")
            for field in (
                "force_n",
                "force_rounding_radius_n",
                "moment_nmm",
                "moment_rounding_radius_nmm",
            ):
                _need(field in wrench, f"{axis_id} {name} lacks {field}")
        _need(
            row.get("receiver_wrench_preserves_both_lateral_and_withdrawal") is True,
            f"{axis_id} receiver action no longer preserves lateral and withdrawal sources",
        )
        _need(
            len(
                _list(
                    row.get("source_connections"), f"source connections for {axis_id}"
                )
            )
            == 2,
            f"{axis_id} source endpoint connections missing",
        )
        datum_differences = _mapping(
            row.get("geometry_application_datum_differences"),
            f"source application datums for {axis_id}",
        )
        for point_role in (
            "lateral_model_point",
            "lateral_response_point",
            "withdrawal_model_point",
            "withdrawal_response_point",
        ):
            point = _mapping(
                datum_differences.get(point_role), f"{axis_id} {point_role}"
            )
            _need(
                "native_application_point_xyz_mm" in point,
                f"{axis_id} {point_role} application point missing",
            )
            _need(
                "signed_axial_offset_mm" in point and "transverse_offset_mm" in point,
                f"{axis_id} {point_role} application offsets missing",
            )
        selected.append(deepcopy(row))
    return selected


def _join_actions(panel_report):
    actions = _mapping(panel_report.get("actions"), "panel report actions")
    _assert_current_source(actions, "panel action report")
    _need(
        actions.get("schema") == "current_panel_receiver_actions/v1",
        "panel action schema mismatch",
    )
    claim_boundary = _mapping(
        actions.get("claim_boundary"), "panel action claim boundary"
    )
    _need(
        claim_boundary.get("hillman_physical_stiffness_established") is False,
        "panel action source now claims Hillman physical stiffness",
    )
    _need(
        claim_boundary.get("native_solve_executed_by_this_packet") is False,
        "panel action packet native-solve boundary changed",
    )
    _need(
        claim_boundary.get("hillman_resistance_established") is False,
        "panel action source now claims Hillman resistance",
    )
    _need(
        claim_boundary.get("complete_joint_accepted") is False,
        "panel action source now claims complete-joint acceptance",
    )
    _need(
        actions.get("panel_receiver_mpc_transfer_status") == "REFUSED",
        "panel receiver recursive transfer boundary changed",
    )
    _need(
        actions.get("recursive_reduced_free_dof_mpc_transfer_status") == "REFUSED",
        "recursive reduced-DOF transfer boundary changed",
    )

    states = _list(actions.get("states"), "saved panel action states")
    _need(len(states) == 21, "saved panel action report must contain 21 states")
    expected_receivers = {
        axis_id: expected["post"] for axis_id, expected in CENTER_SCREWS.items()
    }
    observed = {}
    output_states = []
    for state in states:
        _mapping(state, "saved action state")
        selected = _validate_action_state(state, expected_receivers)
        identity = (state.get("case"), state.get("increment_index"))
        _need(identity not in observed, f"duplicate saved action state {identity!r}")
        observed[identity] = state.get("load_factor")
        receiver_summaries = [
            deepcopy(summary)
            for summary in _list(
                state.get("panel_receiver_mpc_transfer_summaries"),
                f"MPC transfer summaries {identity}",
            )
            if summary.get("body") in {spec["post"] for spec in SIDES.values()}
        ]
        physical_summaries = [
            deepcopy(summary)
            for summary in _list(
                state.get("physical_body_endpoint_projection_summaries"),
                f"physical projection summaries {identity}",
            )
            if summary.get("body") in {spec["post"] for spec in SIDES.values()}
        ]
        panel_contact_summaries = [
            deepcopy(summary)
            for summary in _list(
                state.get("panel_contact_receiver_summaries"),
                f"panel contact summaries {identity}",
            )
            if summary.get("receiver_member")
            in {spec["post"] for spec in SIDES.values()}
        ]
        expected_contact_pairs = {
            (spec["panel"], spec["post"]) for spec in CENTER_SCREWS.values()
        }
        observed_contact_pairs = {
            (summary.get("panel_member"), summary.get("receiver_member"))
            for summary in panel_contact_summaries
        }
        _need(
            observed_contact_pairs == expected_contact_pairs
            and len(panel_contact_summaries) == 2,
            f"center panel/post contact summary coverage mismatch at {identity}",
        )
        _need(
            all(
                summary.get("physical_contact_pressure_established") is False
                for summary in panel_contact_summaries
            ),
            f"center panel/post contact pressure boundary changed at {identity}",
        )
        for summary in panel_contact_summaries:
            for side in (
                "modeled_contact_actions_on_panel",
                "modeled_contact_actions_on_receiver",
            ):
                wrench = _mapping(summary.get(side), f"{side} at {identity}")
                for field in (
                    "force_n",
                    "force_rounding_radius_n",
                    "moment_nmm",
                    "moment_rounding_radius_nmm",
                ):
                    _need(
                        field in wrench,
                        f"center contact summary at {identity} lacks {field}",
                    )
        expected_summary_keys = {
            (spec["post"], role)
            for spec in SIDES.values()
            for role in (
                "panel_screw_lateral_plane",
                "non_qualifying_parametric_screw_withdrawal",
            )
        }
        observed_mpc_summary_keys = {
            (summary.get("body"), summary.get("source_role"))
            for summary in receiver_summaries
        }
        observed_projection_keys = {
            (summary.get("body"), summary.get("source_role"))
            for summary in physical_summaries
        }
        _need(
            observed_mpc_summary_keys == expected_summary_keys
            and len(receiver_summaries) == 4,
            f"center post MPC summary coverage mismatch at {identity}",
        )
        _need(
            observed_projection_keys == expected_summary_keys
            and len(physical_summaries) == 4,
            f"center post physical projection coverage mismatch at {identity}",
        )
        _need(
            all(
                summary.get("not_a_qualified_receiver_or_support_reaction") is True
                for summary in physical_summaries
            ),
            f"center post physical projection claim boundary changed at {identity}",
        )
        output_states.append(
            {
                "case": state.get("case"),
                "increment_index": state.get("increment_index"),
                "load_factor": state.get("load_factor"),
                "panel_receiver_mpc_transfer_status": state.get(
                    "panel_receiver_mpc_transfer_status"
                ),
                "source_hillman_scenario": deepcopy(
                    state.get("source_hillman_scenario")
                ),
                "center_screw_states": selected,
                "center_panel_contact_receiver_summaries": panel_contact_summaries,
                "center_post_mpc_transfer_summaries": receiver_summaries,
                "center_post_physical_body_endpoint_projection_summaries": physical_summaries,
            }
        )

    _need(
        {case for case, _index in observed} == EXPECTED_ACTION_CASES,
        "saved panel action case coverage mismatch",
    )
    _need(
        {index for _case, index in observed} == EXPECTED_INCREMENT_INDEXES,
        "saved panel action increment coverage mismatch",
    )
    for case in EXPECTED_ACTION_CASES:
        case_rows = {
            index: factor
            for (case_id, index), factor in observed.items()
            if case_id == case
        }
        _need(
            set(case_rows) == EXPECTED_INCREMENT_INDEXES,
            f"saved action increments incomplete for {case}",
        )
        factors = list(case_rows.values())
        _need(
            len(set(factors)) == 7 and factors == sorted(factors),
            f"saved action factors are duplicated or unordered for {case}",
        )
    return output_states


def build_duties(panel_report, manifest04, graph, axis_features, surfaces, envelopes):
    """Join frozen screw, finished-feature, stock, contact, bolt, and action rows.

    The function is deliberately source-only.  It validates IDs and copies the
    recorded fields needed for downstream review; it does not derive capacity,
    screw sharing, candidate-bolt actions, or a mechanical acceptance result.
    """
    _assert_current_source(panel_report, "panel report")
    _assert_current_source(manifest04, "attempt04 manifest")
    _assert_graph_revision(graph)
    _assert_current_source(axis_features, "finished axis-feature register")
    _assert_current_source(surfaces, "finished surface register")
    _assert_current_source(envelopes, "stock envelope register")
    _need(
        manifest04.get("manifest_id") == "current-full-frame-input-manifest-attempt04",
        "unexpected current source manifest",
    )
    _need(
        panel_report.get("schema") == "current_panel_receiver_transfer/v1",
        "panel receiver report schema mismatch",
    )
    _need(
        manifest04.get("schema") == "wood_joint_current_full_frame_input_manifest/v3",
        "attempt04 manifest schema mismatch",
    )
    _need(
        graph.get("schema") == "wood_joint_current_contact_graph/v1",
        "contact graph schema mismatch",
    )
    _need(
        axis_features.get("schema") == "wood_joint_axis_finished_feature_register/v1",
        "axis feature register schema mismatch",
    )
    _need(
        surfaces.get("schema") == "wood_joint_current_finished_feature_register/v1",
        "surface register schema mismatch",
    )
    _need(
        envelopes.get("schema") == "wood_joint_proposed_starting_stock_envelopes/v1",
        "stock envelope register schema mismatch",
    )
    _need(
        surfaces.get("record_count") == 44 and len(surfaces.get("records", [])) == 44,
        "finished timber surface register does not contain 44 members",
    )
    _need(
        envelopes.get("record_count") == 44 and len(envelopes.get("records", [])) == 44,
        "current stock envelope register does not contain 44 timber members",
    )
    _need(
        manifest04.get("inventory_counts", {}).get("full_physical_member_nodes") == 50
        and len(manifest04.get("physical_members", [])) == 50,
        "current manifest physical-member count mismatch",
    )
    _need(
        graph.get("counts", {}).get("physical_member_nodes") == 50
        and len(graph.get("inventories", {}).get("physical_members", [])) == 50,
        "contact graph physical-member count mismatch",
    )
    feature_hashes = _mapping(
        axis_features.get("source_hashes"), "axis feature source hashes"
    )
    feature_manifest = _mapping(
        axis_features.get("source_manifest"), "axis feature source manifest"
    )
    _need(
        feature_manifest.get("manifest_sha256_field")
        == manifest04.get("manifest_sha256"),
        "axis feature source manifest digest mismatch",
    )
    _need(
        feature_hashes.get("manifest_sha256")
        == surfaces.get("source_manifest_sha256")
        == envelopes.get("source_manifest_sha256"),
        "feature/surface/stock sources do not pin the same current manifest bytes",
    )
    _need(
        manifest04.get("inventory_counts", {}).get("retained_starting_frame_bolt_axes")
        == 12,
        "manifest retained frame-bolt count mismatch",
    )
    _need(
        len(manifest04.get("retained_frame_bolt_axes", [])) == 12,
        "manifest retained frame-bolt axes mismatch",
    )

    panel_axes, manifest_screws, _graph_screws, feature_screws, moved, unchanged = (
        _validate_panel_screw_sources(panel_report, manifest04, graph, axis_features)
    )
    _validate_no_old_shapes(
        manifest04, graph, surfaces, envelopes, panel_report["inventory"]
    )

    # Bind each report-level screw membership to the axis-feature and exact STEP surface record.
    surface_members = _index_surface_members(surfaces)
    center_screws = []
    for axis_id, expected in CENTER_SCREWS.items():
        report_axis = panel_axes[axis_id]
        feature_axis = feature_screws[axis_id]
        membership = feature_axis["receiver_memberships"][0]
        feature_id = expected["facet"]
        member = surface_members[expected["post"]]
        surface_feature = _rows_by(
            member.get("features"),
            "feature_id",
            f"surface features for {expected['post']}",
        )[feature_id]
        report_binding = _mapping(
            report_axis["features"][0].get("finished_step_binding"),
            f"panel report STEP binding for {axis_id}",
        )
        feature_binding = _mapping(
            membership.get("current_finished_step_binding"),
            f"axis-feature STEP binding for {axis_id}",
        )
        surface_binding = _mapping(
            member.get("step_binding"),
            f"surface STEP binding for {expected['post']}",
        )
        for source_name, binding in (
            ("axis feature register", feature_binding),
            ("surface register", surface_binding),
        ):
            _need(
                report_binding.get("path") == binding.get("path")
                and report_binding.get("sha256") == binding.get("file_sha256"),
                f"{source_name} current center receiver STEP identity mismatch for {axis_id}",
            )
            _same_number(
                report_binding.get("size_bytes"),
                binding.get("size_bytes"),
                f"{source_name} current center receiver STEP size for {axis_id}",
            )
        stock = next(
            row
            for row in envelopes["records"]
            if row.get("member_id") == expected["post"]
        )
        center_screws.append(
            {
                "axis_id": axis_id,
                "panel_member": report_axis["panel_member"],
                "receiver_member": report_axis["receiver_member"],
                "previous_receiver_member": report_axis["previous_receiver_member"],
                "current_location_status": report_axis["current_location_status"],
                "origin_global_xyz_mm": deepcopy(report_axis["origin_global_xyz_mm"]),
                "axis_global_xyz": deepcopy(report_axis["axis_global_xyz"]),
                "translation_from_source_xyz_mm": deepcopy(
                    report_axis["translation_from_source_xyz_mm"]
                ),
                "purchased_nominal_length_mm": manifest_screws[axis_id][
                    "purchased_nominal_length_mm"
                ],
                "purchased_policy": manifest_screws[axis_id]["purchased_policy"],
                "owner_moved_axis_record": deepcopy(
                    report_axis.get("owner_moved_axis_record")
                ),
                "source_provenance": deepcopy(report_axis.get("source_provenance")),
                "panel_receiver_contact": deepcopy(
                    report_axis.get("panel_receiver_contact")
                ),
                "support_edge_evidence": deepcopy(
                    report_axis.get("support_edge_evidence")
                ),
                "nominal_receiver_envelope": deepcopy(
                    report_axis["nominal_embedment_envelope"]
                ),
                "finished_receiver_membership": {
                    "feature_id": feature_id,
                    "match_status": membership.get("match_status"),
                    "axis_feature_record": deepcopy(membership),
                    "panel_report_record": deepcopy(report_axis["features"][0]),
                    "surface_record": deepcopy(surface_feature),
                    "surface_step_binding": deepcopy(surface_binding),
                    "stock_record": {
                        "member_id": stock.get("member_id"),
                        "stock_class": stock.get("stock_class"),
                        "stock_blank_length_mm": stock.get("stock_blank_length_mm"),
                        "original_stock_section_mm": deepcopy(
                            stock.get("original_stock_section_mm")
                        ),
                        "finished_oriented_spans_g_q_r_mm": deepcopy(
                            stock.get("original_stock_containment", {}).get(
                                "finished_oriented_spans_g_q_r_mm"
                            )
                        ),
                        "grade_assignment_status": stock.get("grade_assignment_status"),
                        "current_finished_step_sha256": stock.get(
                            "current_finished_step_sha256"
                        ),
                    },
                },
                "receiver_to_frame_path_complete_in_source_inventory": False,
                "screw_resistance_established": False,
            }
        )

    candidate_bolts, frame_duties, stock_members, _edge_contract = (
        _validate_frame_duties(manifest04, graph, axis_features, surfaces, envelopes)
    )
    # Include the header and center cleats/posts used by the frame route.  The
    # screw receivers already carry their own stock records above.
    actions = _join_actions(panel_report)

    center_check = deepcopy(
        panel_report["inventory"]["current_center_kicker_receiver_check"]
    )
    center_seam = center_check.get("center_seam", {})
    return {
        "schema": SCHEMA,
        "candidate": CANDIDATE,
        "geometry_revision_id": GEOMETRY_REVISION,
        "status": "SOURCE_BOUND_DUTY_INVENTORY_ONLY",
        "source_identity": {
            "panel_report_schema": panel_report.get("schema"),
            "panel_report_source_pins_sha256": panel_report.get("source_pins_sha256"),
            "panel_action_producer_sha256": panel_report["actions"].get(
                "producer_sha256"
            ),
            "panel_action_inventory_report_sha256": panel_report["actions"].get(
                "inventory_report_sha256"
            ),
            "attempt04_manifest_id": manifest04.get("manifest_id"),
            "attempt04_manifest_declared_sha256": manifest04.get("manifest_sha256"),
            "contact_graph_collector_sha256": graph.get("parent_run", {}).get(
                "collector_sha256"
            ),
            "contact_graph_source_sha256": deepcopy(graph.get("source_sha256")),
            "axis_feature_manifest_sha256": axis_features.get("source_hashes", {}).get(
                "manifest_sha256"
            ),
            "axis_feature_surface_report_sha256": axis_features.get(
                "source_hashes", {}
            ).get("surfaces_report_sha256"),
            "surface_register_producer_sha256": surfaces.get("producer_sha256"),
            "surface_register_source_pins_sha256": surfaces.get("source_pins_sha256"),
            "stock_envelope_producer_sha256": envelopes.get("producer_sha256"),
            "stock_envelope_source_pins_sha256": envelopes.get("source_pins_sha256"),
        },
        "counts": {
            "panel_kicker_axes": 66,
            "unchanged_source_stations": len(unchanged),
            "owner_moved_axes": len(moved),
            "center_kicker_screws": len(center_screws),
            "other_moved_lower_panel_screws": len(MOVED_LOWER_AXES),
            "saved_cases": len(EXPECTED_ACTION_CASES),
            "saved_increments_per_case": len(EXPECTED_INCREMENT_INDEXES),
            "center_screw_action_states": sum(
                len(state["center_screw_states"]) for state in actions
            ),
            "center_screw_scalar_components": sum(
                len(row["lateral_scalar_components"]) + 1
                for state in actions
                for row in state["center_screw_states"]
            ),
            "center_candidate_bolt_axes": len(candidate_bolts),
            "direct_post_header_seats": 2,
            "post_to_cleat_candidate_bolts": 4,
            "cleat_to_header_candidate_bolts": 4,
        },
        "panel_screw_policy": {
            "product": "Hillman 42605",
            "total_axes": 66,
            "purchased_policy_retained": True,
            "moved_axes": sorted(moved),
            "unchanged_axis_count": len(unchanged),
            "historical_50p8_mm_proxy_is_installed_engagement": False,
        },
        "center_screws": center_screws,
        "center_screw_action_states": actions,
        "action_transfer_boundary": {
            "recursive_reduced_free_dof_mpc_transfer_status": panel_report[
                "actions"
            ].get("recursive_reduced_free_dof_mpc_transfer_status"),
            "physical_body_endpoint_projection_status": "DIAGNOSTIC_ONLY",
            "physical_body_endpoint_projection_qualifies_receiver_or_support": False,
        },
        "stock_members": list(stock_members.values()),
        "candidate_frame_bolts": candidate_bolts,
        "frame_duties": frame_duties,
        "center_receiver_check": center_check,
        "open_edge_obligation": {
            "continuous_direct_inner_edge_backing_is_adopted_criterion": False,
            "panel_edge_support_and_load_transfer_open": True,
            "center_seam_gap_mm": center_seam.get("panel_edge_to_edge_x_gap_mm"),
            "center_seam_panel_contact_area_mm2": center_seam.get(
                "panel_to_panel_interface", {}
            ).get("finite_shared_planar_face_area_mm2"),
            "geometry_failure_asserted": False,
            "interpretation": "The present records do not resolve inner-edge support or load transfer; a gap is not an adopted geometry failure.",
        },
        "missing_paths": [
            "No force split or active contact law is supplied for the direct post/header seat and the post/cleat/header route.",
            "No current candidate-bolt demands, joint resistance, or complete receiver-to-frame mechanical path is supplied.",
            "The saved panel-screw actions cover three diagnostic cases; the six current case inputs do not include frame reactions or joint demands.",
            "Inner-edge contact-patch projections are reported separately; no plywood bearing/splitting assessment or complete kicker support result is supplied.",
        ],
        "qualification": {
            "hillman_physical_stiffness_established": False,
            "hillman_resistance_established": False,
            "capacity_calculated": False,
            "force_split_calculated": False,
            "candidate_bolt_capacity_or_resistance_established": False,
            "physical_bolt_stack_order_established": False,
            "physical_contact_pressure_established": False,
            "complete_receiver_to_frame_load_path_established": False,
            "continuous_direct_inner_edge_backing_required": False,
            "geometry_failure_asserted": False,
            "complete_joint_accepted": False,
            "native_solve_executed_by_this_packet": False,
            "fabrication_or_climbing_release": False,
        },
    }
