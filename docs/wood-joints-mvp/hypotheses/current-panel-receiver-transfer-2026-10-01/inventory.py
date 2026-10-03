"""Join the saved Hillman panel axes to their current timber receivers.

This module reads pinned JSON/source bytes only. It does not import or replay
CAD geometry and does not infer installed screw geometry or mechanics.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]

SOURCE_INVENTORY = "docs/wood-joints-mvp/source-inventory.json"
MANIFEST03 = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-full-frame-input-manifest-attempt03/current-full-frame-input-manifest.json"
)
MANIFEST04 = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
)
RECEIVER_SCREEN = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "receiver-screen-attempt04.json"
)
CONTACT_GRAPH = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "complete-contact-graph-attempt02.json"
)
FEATURE_REGISTER = (
    "docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/"
    "axis-features.json"
)
FEATURE_SOURCE_PINS = (
    "docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/"
    "axis-source-pins.json"
)
FEATURE_CLOSURE_PINS = (
    "docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/"
    "source-pins.json"
)

CANDIDATE = "compact-floor-flush-wood-joints-development"
GEOMETRY_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
AXIS_COUNT = 66
STATUS_COUNTS = {"source_station_retained": 58, "moved": 8}
TOLERANCE_MM = 1.0e-6

CENTER_KICKER_CURRENT_RECEIVERS = {
    "round_kicker_left_center_1": "base_post_center_left",
    "round_kicker_left_center_2": "base_post_center_left",
    "round_kicker_right_center_1": "base_post_center_right",
    "round_kicker_right_center_2": "base_post_center_right",
}

LIMITS = [
    "Current receivers are model identities from the attempt04 manifest and matched finished-timber features, not observations of delivered or installed screws.",
    "The 50.8 mm source occupied length is a historical SPAX analysis envelope. Hillman 42605 has a 63.5 mm nominal purchase policy; modeled axis and receiver-overlap lengths do not establish actual screw engagement or embedment.",
    "Bore-like patches, receiver-envelope intersections, face-contact areas, and receiver-to-frame graph edges describe saved geometry only. They establish no holes, fit, installation, active contact, support adequacy, load transfer, force sharing, resistance, stiffness, or acceptance.",
    "The contact graph associates each panel screw axis with its current panel/receiver pair. It assigns no action or force to a screw and establishes no continuous supported panel edge or complete receiver-to-frame path.",
    "The four moved center-kicker axes currently enter base_post_center_left/right. The former inner-kicker-backer names are historical; no such backer shape is present in the current composition.",
]


class _Pins:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.rows: dict[str, dict[str, Any]] = {}

    def add(
        self,
        path: str,
        expected_sha256: str | None = None,
        expected_size_bytes: int | None = None,
    ) -> bytes:
        relative = Path(path)
        if relative.is_absolute() or not relative.parts or ".." in relative.parts:
            raise ValueError(f"source path must be repository-relative: {path}")
        try:
            raw = (self.root / relative).read_bytes()
        except OSError as error:
            raise ValueError(f"pinned source is unavailable: {path}") from error
        digest = hashlib.sha256(raw).hexdigest()
        size = len(raw)
        if expected_sha256 is not None and digest != expected_sha256:
            raise ValueError(f"pinned source hash changed: {path}")
        if expected_size_bytes is not None and size != expected_size_bytes:
            raise ValueError(f"pinned source size changed: {path}")
        record = {"path": relative.as_posix(), "sha256": digest, "size_bytes": size}
        prior = self.rows.get(record["path"])
        if prior is not None and prior != record:
            raise ValueError(f"conflicting source pin: {path}")
        self.rows[record["path"]] = record
        return raw

    def records(self) -> list[dict[str, Any]]:
        return [self.rows[path] for path in sorted(self.rows)]


def _load(pins: _Pins, path: str, schema: str) -> dict[str, Any]:
    try:
        value = json.loads(pins.add(path))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid JSON source: {path}") from error
    if not isinstance(value, dict) or value.get("schema") != schema:
        raise ValueError(f"{path} must use schema {schema!r}")
    return value


def _map(rows: Any, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list):
        raise TypeError(f"{label} must be a list")
    result: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise TypeError(f"{label}[{index}] must be an object")
        axis_id = row.get("axis_id")
        if not isinstance(axis_id, str) or not axis_id:
            raise ValueError(f"{label}[{index}] has no axis_id")
        if axis_id in result:
            raise ValueError(f"{label} contains duplicate axis_id {axis_id!r}")
        result[axis_id] = dict(row)
    return result


def _vec3(value: Any, label: str) -> tuple[float, float, float]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or len(value) != 3
    ):
        raise ValueError(f"{label} must contain three coordinates")
    result = tuple(float(component) for component in value)
    if not all(math.isfinite(component) for component in result):
        raise ValueError(f"{label} must contain finite coordinates")
    return result  # type: ignore[return-value]


def _same_vec3(first: Any, second: Any, label: str) -> None:
    a, b = _vec3(first, label), _vec3(second, label)
    if any(abs(x - y) > TOLERANCE_MM for x, y in zip(a, b, strict=True)):
        raise ValueError(f"{label} differs between saved sources")


def _same_number(first: Any, second: Any, label: str) -> None:
    if not math.isclose(float(first), float(second), rel_tol=0.0, abs_tol=TOLERANCE_MM):
        raise ValueError(f"{label} differs between saved sources")


def _source_pin(pins: _Pins, raw: Any, label: str) -> None:
    if not isinstance(raw, Mapping):
        raise TypeError(f"{label} must be an object")
    path, digest = raw.get("path"), raw.get("sha256")
    size = raw.get("size_bytes")
    if not isinstance(path, str) or not isinstance(digest, str):
        raise TypeError(f"{label} lacks a source path or SHA-256 string")
    if size is not None and (not isinstance(size, int) or size < 0):
        raise TypeError(f"{label} has an invalid size type or value")
    pins.add(path, digest, size)


def _verify_closures(
    pins: _Pins,
    *,
    source_inventory: Mapping[str, Any],
    manifest03: Mapping[str, Any],
    manifest04: Mapping[str, Any],
    graph: Mapping[str, Any],
    feature: Mapping[str, Any],
    axis_pins: Mapping[str, Any],
    feature_pins: Mapping[str, Any],
) -> None:
    output = axis_pins.get("outputs", {}).get("axis_features")
    if not isinstance(output, Mapping) or output.get("path") != FEATURE_REGISTER:
        raise ValueError("axis source pins do not bind the finished-feature report")
    if hashlib.sha256(pins.add(FEATURE_REGISTER)).hexdigest() != output.get("sha256"):
        raise ValueError("finished-feature report does not match its output pin")

    source_records = axis_pins.get("sources")
    if not isinstance(source_records, Mapping):
        raise TypeError("axis source pins lack a source map")
    required = {
        "current_full_frame_input_manifest": MANIFEST04,
        "current_screw_source_inventory": SOURCE_INVENTORY,
        "finished_surfaces_source_pins": FEATURE_CLOSURE_PINS,
    }
    for name, path in required.items():
        pin = source_records.get(name)
        if not isinstance(pin, Mapping) or pin.get("path") != path:
            raise ValueError(
                f"axis source pin {name} does not bind the required source"
            )
        _source_pin(pins, pin, f"axis source pin {name}")

    hashes = {row["path"]: row["sha256"] for row in pins.records()}
    manifest_hash = hashes[MANIFEST04]
    inventory_hash = hashes[SOURCE_INVENTORY]
    closure_hash = hashes[FEATURE_CLOSURE_PINS]
    feature_hashes = feature.get("source_hashes", {})
    if feature_hashes.get("manifest_sha256") != manifest_hash:
        raise ValueError(
            "finished-feature report references a different attempt04 manifest"
        )
    if feature_hashes.get("source_inventory_sha256") != inventory_hash:
        raise ValueError(
            "finished-feature report references a different source inventory"
        )
    if feature_hashes.get("surfaces_source_pins_sha256") != closure_hash:
        raise ValueError(
            "finished-feature report references a different feature closure"
        )
    if feature_pins.get("current_manifest04_sha256") != manifest_hash:
        raise ValueError(
            "feature source closure references a different attempt04 manifest"
        )

    closure = feature_pins.get("pins")
    if not isinstance(closure, Mapping) or not closure:
        raise ValueError("feature source closure has no pins")
    for name, pin in closure.items():
        _source_pin(pins, pin, f"feature source pin {name}")

    attempt04_inputs = manifest04.get("attempt04_input_source_pins")
    if not isinstance(attempt04_inputs, Mapping) or not attempt04_inputs:
        raise ValueError("attempt04 manifest has no source pins")
    for path, digest in attempt04_inputs.items():
        if not isinstance(path, str) or not isinstance(digest, str):
            raise TypeError("attempt04 source pin path and SHA-256 must be strings")
        pins.add(path, digest)

    base = manifest04.get("attempt03_base_manifest")
    if not isinstance(base, Mapping) or base.get("path") != MANIFEST03:
        raise ValueError("attempt04 manifest does not preserve the attempt03 manifest")
    base_size = len(pins.add(MANIFEST03, base.get("file_sha256")))
    if base.get("size_bytes") != base_size:
        raise ValueError("attempt03 manifest size differs from attempt04's pin")

    # Validate and return the entire axis-feature source closure by hashing bytes
    # only; the member STEP files are never opened as geometry.
    for name, pin in source_records.items():
        _source_pin(pins, pin, f"axis feature source pin {name}")

    graph_hashes = graph.get("source_sha256", {})
    if not isinstance(graph_hashes, Mapping):
        raise TypeError("contact graph source hashes must be an object")
    graph_inputs = graph_hashes.get("geometry_source_inputs_sha256", {})
    if (
        not isinstance(graph_inputs, Mapping)
        or not graph_inputs
        or graph_inputs.get(SOURCE_INVENTORY) != inventory_hash
    ):
        raise ValueError("contact graph references a different source inventory")
    for path, digest in graph_inputs.items():
        if not isinstance(path, str) or not isinstance(digest, str):
            raise TypeError(
                "contact graph geometry input paths and hashes must be strings"
            )
        pins.add(path, digest)
    if source_inventory.get("candidate") != CANDIDATE:
        raise ValueError(
            "source inventory candidate does not match this development lane"
        )
    if manifest03.get("schema") != "wood_joint_current_full_frame_input_manifest/v2":
        raise ValueError("attempt03 manifest schema changed")
    if manifest04.get("schema") != "wood_joint_current_full_frame_input_manifest/v3":
        raise ValueError("attempt04 manifest schema changed")


def _screen_pairs(
    screen: Mapping[str, Any],
) -> tuple[dict[tuple[str, str], dict], dict[str, tuple[str, str]]]:
    interfaces = screen.get("panel_to_receiver_interfaces", {}).get("interfaces")
    if not isinstance(interfaces, list):
        raise TypeError("receiver screen lacks panel/receiver interfaces")
    pairs: dict[tuple[str, str], dict] = {}
    axis_pairs: dict[str, tuple[str, str]] = {}
    for row in interfaces:
        if not isinstance(row, Mapping):
            raise TypeError("receiver screen interface must be an object")
        pair = (row.get("panel_member"), row.get("receiver_member"))
        if not all(isinstance(member, str) for member in pair) or pair in pairs:
            raise ValueError("receiver screen has an invalid or duplicate pair")
        pairs[pair] = dict(row)
        for axis_id in row.get("fixed_hillman_axis_ids", []):
            if not isinstance(axis_id, str) or axis_id in axis_pairs:
                raise ValueError(
                    "receiver screen has an invalid or repeated axis membership"
                )
            axis_pairs[axis_id] = pair
    return pairs, axis_pairs


def _graph_indexes(
    graph: Mapping[str, Any],
) -> tuple[dict[str, dict], dict[str, list[dict]], dict[str, list[dict]]]:
    inventories = graph.get("inventories", {})
    axis_rows = _map(
        inventories.get("current_panel_screw_axes"), "contact graph panel screws"
    )
    members = {
        row["member_id"]: row.get("member_kind")
        for row in inventories.get("physical_members", [])
    }
    associations: dict[str, list[dict]] = defaultdict(list)
    timber_contacts: dict[str, list[dict]] = defaultdict(list)
    for edge in graph.get("edges", []):
        ids = edge.get("member_ids", [])
        if len(ids) != 2:
            raise ValueError("contact graph edge must name two members")
        for association in edge.get("current_panel_screw_associations", []):
            associations[association["axis_id"]].append(
                {
                    "member_ids": list(ids),
                    "association": dict(association),
                    "geometry": {
                        key: edge.get(key)
                        for key in (
                            "geometry_state",
                            "interface_geometry_state",
                            "contact_measurement_basis",
                            "finite_shared_planar_face_area_mm2",
                            "opposed_planar_face_contact_area_mm2",
                            "cooriented_planar_face_contact_area_mm2",
                            "common_volume_mm3",
                            "minimum_separation_mm",
                        )
                    },
                }
            )
        if edge.get("geometry_state") == "separated" or any(
            members.get(member) != "timber" for member in ids
        ):
            continue
        for owner, other in (ids, ids[::-1]):
            timber_contacts[owner].append(
                {
                    "other_member_id": other,
                    "geometry_state": edge.get("geometry_state"),
                    "interface_geometry_state": edge.get("interface_geometry_state"),
                    "contact_measurement_basis": edge.get("contact_measurement_basis"),
                    "finite_shared_planar_face_area_mm2": edge.get(
                        "finite_shared_planar_face_area_mm2"
                    ),
                    "opposed_planar_face_contact_area_mm2": edge.get(
                        "opposed_planar_face_contact_area_mm2"
                    ),
                    "common_volume_mm3": edge.get("common_volume_mm3"),
                    "minimum_separation_mm": edge.get("minimum_separation_mm"),
                }
            )
    for rows in timber_contacts.values():
        rows.sort(key=lambda row: row["other_member_id"])
    return axis_rows, dict(associations), dict(timber_contacts)


def _feature_membership(
    row: Mapping[str, Any], receiver: str, bindings: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    memberships = row.get("receiver_memberships")
    if not isinstance(memberships, list) or len(memberships) != 1:
        raise ValueError(f"{row.get('axis_id')} must have one current receiver feature")
    membership = memberships[0]
    if not isinstance(membership, Mapping):
        raise TypeError("receiver feature membership must be an object")
    if membership.get("receiver_member_id") != receiver:
        raise ValueError(
            f"{row.get('axis_id')} feature receiver differs from current map"
        )
    ids = membership.get("matched_feature_ids")
    if (
        membership.get("match_status") != "matched_bore_patch"
        or not isinstance(ids, list)
        or len(ids) != 1
    ):
        raise ValueError(f"{row.get('axis_id')} lacks one matched bore-like patch")
    candidates = membership.get("cylinder_surface_candidates", [])
    eligible = [
        c for c in candidates if c.get("association_status") == "eligible_bore_patch"
    ]
    if len(eligible) != 1 or eligible[0].get("feature_id") != ids[0]:
        raise ValueError(f"{row.get('axis_id')} bore-patch match is not unique")
    cylinder = eligible[0]
    if (
        cylinder.get("surface_kind") != "CYLINDER"
        or cylinder.get("material_side_geometry") != "bore_like"
        or cylinder.get("finite_interval_status")
        != "contained_in_source_finite_interval"
    ):
        raise ValueError(f"{row.get('axis_id')} matched patch is not a contained bore")
    binding = membership.get("current_finished_step_binding", {})
    expected = bindings.get(receiver)
    if expected is None or any(
        binding.get(source) != expected.get(target)
        for source, target in (
            ("path", "path"),
            ("file_sha256", "file_sha256"),
            ("size_bytes", "size_bytes"),
        )
    ):
        raise ValueError(
            f"{row.get('axis_id')} finished STEP binding differs from manifest"
        )
    return {
        "receiver_member_id": receiver,
        "match_status": membership["match_status"],
        "feature_id": ids[0],
        "finished_step_binding": {
            "path": binding.get("path"),
            "sha256": binding.get("file_sha256"),
            "size_bytes": binding.get("size_bytes"),
        },
        "modeled_axis_interval_from_datum_mm": membership.get(
            "axis_in_stock_frame", {}
        ).get("axis_interval_from_datum_mm"),
        "bore_patch": {
            key: cylinder.get(key)
            for key in (
                "surface_kind",
                "material_side_geometry",
                "finite_interval_status",
                "patch_interval_projected_from_axis_datum_mm",
                "axial_overlap_length_mm",
                "cylinder_radius_mm",
                "line_distance_mm",
                "axis_direction_sine_error",
            )
        },
    }


def _build_report(
    source_inventory: Mapping[str, Any],
    manifest03: Mapping[str, Any],
    manifest04: Mapping[str, Any],
    screen: Mapping[str, Any],
    graph: Mapping[str, Any],
    feature: Mapping[str, Any],
) -> dict[str, Any]:
    for label, doc in (
        ("attempt03", manifest03),
        ("attempt04", manifest04),
        ("screen", screen),
        ("graph", graph),
        ("features", feature),
    ):
        revision = doc.get("geometry_revision_id", doc.get("revision_id"))
        if revision != GEOMETRY_REVISION:
            raise ValueError(f"{label} geometry revision differs from current model")
    for label, doc in (("manifest04", manifest04), ("features", feature)):
        if doc.get("candidate") != CANDIDATE:
            raise ValueError(f"{label} candidate differs from current development lane")

    sources = _map(
        source_inventory.get("fixed_panel_kicker_screws"), "source panel screws"
    )
    axes03 = _map(manifest03.get("panel_kicker_screw_axes"), "attempt03 panel screws")
    axes04 = _map(manifest04.get("panel_kicker_screw_axes"), "attempt04 panel screws")
    screen_axes = _map(screen.get("axes"), "receiver screen axes")
    graph_axes, associations, timber_contacts = _graph_indexes(graph)
    group = feature.get("source_axis_groups", {}).get("panel_kicker_screw_axes", {})
    feature_axes = _map(group.get("axes"), "feature panel screws")
    axis_ids = set(sources)
    if len(axis_ids) != AXIS_COUNT or group.get("axis_count") != AXIS_COUNT:
        raise ValueError(
            "source inventory and feature report must contain 66 panel axes"
        )
    for label, rows in (
        ("attempt03", axes03),
        ("attempt04", axes04),
        ("receiver screen", screen_axes),
        ("contact graph", graph_axes),
        ("feature report", feature_axes),
    ):
        if set(rows) != axis_ids:
            raise ValueError(f"{label} axis IDs differ from the 66 source axes")
    if set(group.get("axis_ids", [])) != axis_ids:
        raise ValueError("feature axis ID list differs from its 66 rows")

    pairs, screen_axis_pairs = _screen_pairs(screen)
    if set(screen_axis_pairs) != axis_ids or set(associations) != axis_ids:
        raise ValueError(
            "receiver screen or contact graph does not associate all 66 axes"
        )
    bindings = {
        row["member_id"]: row
        for row in manifest04.get("finished_member_step_bindings", [])
    }
    axes: list[dict[str, Any]] = []
    statuses: Counter[str] = Counter()
    receivers: Counter[str] = Counter()
    for axis_id in sorted(axis_ids):
        source, current = sources[axis_id], axes04[axis_id]
        previous = axes03[axis_id]
        screen_row, graph_row, feature_row = (
            screen_axes[axis_id],
            graph_axes[axis_id],
            feature_axes[axis_id],
        )
        panel, receiver = current.get("panel_member"), current.get("receiver_member")
        if not isinstance(panel, str) or not isinstance(receiver, str):
            raise TypeError(
                f"{axis_id} current panel/receiver identity must be strings"
            )
        if (
            source.get("shop_opening_kind") != "hillman_panel"
            or source.get("panel_member") != panel
        ):
            raise ValueError(f"{axis_id} is not the same Hillman panel axis")
        if source.get("candidate_finished_receiver_member") != current.get(
            "previous_receiver_member"
        ):
            raise ValueError(
                f"{axis_id} previous receiver differs from source provenance"
            )
        status = current.get("current_location_status")
        if status not in STATUS_COUNTS:
            raise ValueError(f"{axis_id} has unsupported station status")
        statuses[status] += 1
        receivers[receiver] += 1
        origin, direction = (
            current.get("origin_global_xyz_mm"),
            current.get("axis_global_xyz"),
        )
        translation = current.get("translation_from_source_xyz_mm")
        source_origin, source_direction = (
            source.get("origin_global_xyz_mm"),
            source.get("axis_global_xyz"),
        )
        _same_vec3(
            [
                float(a) + float(b)
                for a, b in zip(source_origin, translation, strict=True)
            ],
            origin,
            f"{axis_id} translated source station",
        )
        _same_vec3(source_direction, direction, f"{axis_id} axis direction")
        for label, row in (
            ("attempt03", previous),
            ("screen", screen_row),
            ("graph", graph_row),
        ):
            if (
                row.get("panel_member") != panel
                or row.get("receiver_member") != receiver
            ):
                phrase = (
                    "current pair differs in receiver screen"
                    if label == "screen"
                    else f"current pair differs in {label}"
                )
                raise ValueError(f"{axis_id} {phrase}")
            if row.get("current_location_status") != status:
                raise ValueError(f"{axis_id} current status differs in {label}")
            _same_vec3(
                row.get("origin_global_xyz_mm"), origin, f"{axis_id} {label} origin"
            )
            _same_vec3(
                row.get("axis_global_xyz"), direction, f"{axis_id} {label} direction"
            )
        if previous.get("previous_receiver_member") != current.get(
            "previous_receiver_member"
        ):
            raise ValueError(f"{axis_id} previous receiver differs in attempt03/04")

        move = current.get("owner_moved_axis_record")
        if status == "moved":
            if not isinstance(move, Mapping) or move.get("axis_id") != axis_id:
                raise ValueError(f"{axis_id} lacks its moved-axis record")
            _same_vec3(
                move.get("old_start_global_xyz_mm"),
                source_origin,
                f"{axis_id} old station",
            )
            _same_vec3(
                move.get("new_start_global_xyz_mm"), origin, f"{axis_id} new station"
            )
            _same_vec3(
                move.get("translation_global_xyz_mm"), translation, f"{axis_id} move"
            )
        elif move is not None or any(
            abs(float(value)) > TOLERANCE_MM for value in translation
        ):
            raise ValueError(
                f"{axis_id} retained station has a move record or translation"
            )

        reconciliation = feature_row.get("panel_axis_station_reconciliation", {})
        if any(
            reconciliation.get(key) != expected
            for key, expected in (
                ("current_location_status", status),
                ("current_receiver_member", receiver),
                ("previous_receiver_member", current.get("previous_receiver_member")),
            )
        ):
            raise ValueError(f"{axis_id} feature station reconciliation differs")
        _same_vec3(
            reconciliation.get("current_axis_origin_global_xyz_mm"),
            origin,
            f"{axis_id} feature origin",
        )
        _same_vec3(
            reconciliation.get("current_axis_direction_global_xyz"),
            direction,
            f"{axis_id} feature direction",
        )

        if axis_id in CENTER_KICKER_CURRENT_RECEIVERS and (
            status != "moved" or receiver != CENTER_KICKER_CURRENT_RECEIVERS[axis_id]
        ):
            raise ValueError(f"{axis_id} must use its current center-post receiver")
        membership = _feature_membership(feature_row, receiver, bindings)
        pair = (panel, receiver)
        interface = pairs.get(pair)
        if interface is None or screen_axis_pairs.get(axis_id) != pair:
            raise ValueError(
                f"{axis_id} has no current panel/receiver screen interface"
            )
        edge_rows = associations[axis_id]
        if len(edge_rows) != 1:
            raise ValueError(
                f"{axis_id} must have one current contact-graph association"
            )
        edge = edge_rows[0]
        association = edge["association"]
        if set(edge["member_ids"]) != set(pair) or any(
            association.get(key) != value
            for key, value in (
                ("axis_id", axis_id),
                ("panel_member", panel),
                ("receiver_member", receiver),
                ("current_location_status", status),
            )
        ):
            raise ValueError(
                f"{axis_id} graph association metadata differs from current pair"
            )
        _same_number(
            edge["geometry"].get("finite_shared_planar_face_area_mm2"),
            interface.get("finite_shared_planar_face_area_mm2"),
            f"{axis_id} panel/receiver face area",
        )

        source_path = {
            "source_candidate_receiver_member": source.get(
                "candidate_finished_receiver_member"
            ),
            "source_finished_receiver_member": source.get(
                "source_finished_receiver_member"
            ),
            "receiver_to_frame_path": source.get("receiver_to_frame_path"),
            "receiver_to_frame_path_complete": source.get(
                "receiver_to_frame_path_complete"
            ),
        }
        envelope = screen_row.get("materialized_axis_envelope", {})
        nominal_axis = envelope.get("axial_bounds_from_reported_origin_mm", [])
        if len(nominal_axis) != 2:
            raise ValueError(f"{axis_id} nominal axis envelope is malformed")
        nominal_length = float(current.get("purchased_nominal_length_mm"))
        _same_number(nominal_axis[0], 0.0, f"{axis_id} nominal axis start")
        _same_number(nominal_axis[1], nominal_length, f"{axis_id} nominal axis end")
        _same_number(
            source.get("shop_purchased_length_mm"),
            nominal_length,
            f"{axis_id} purchase length",
        )
        if "Hillman 42605" not in str(current.get("purchased_policy", "")):
            raise ValueError(f"{axis_id} does not retain Hillman 42605 purchase policy")

        axes.append(
            {
                "axis_id": axis_id,
                "panel_member": panel,
                "receiver_member": receiver,
                "origin_global_xyz_mm": list(_vec3(origin, f"{axis_id} origin")),
                "axis_global_xyz": list(_vec3(direction, f"{axis_id} direction")),
                "previous_receiver_member": current.get("previous_receiver_member"),
                "current_location_status": status,
                "translation_from_source_xyz_mm": list(
                    _vec3(translation, f"{axis_id} translation")
                ),
                "owner_moved_axis_record": dict(move)
                if isinstance(move, Mapping)
                else None,
                "source_provenance": {
                    **source_path,
                    "source_origin_global_xyz_mm": source_origin,
                    "source_axis_global_xyz": source_direction,
                    "source_occupied_length_mm": source.get(
                        "source_occupied_length_mm"
                    ),
                    "source_occupied_diameter_mm": source.get(
                        "source_occupied_diameter_mm"
                    ),
                    "purchased_nominal_length_mm": nominal_length,
                    "purchased_product_policy": current.get("purchased_policy"),
                },
                "nominal_embedment_envelope": {
                    "status": "modeled receiver overlap only; not actual screw embedment or installed engagement",
                    "axis_interval_from_reported_origin_mm": nominal_axis,
                    "raw_receiver_intersection_axial_bounds_from_axis_start_mm": screen_row.get(
                        "raw_receiver_intersection_axial_bounds_from_axis_start_mm"
                    ),
                    "raw_receiver_full_section_equivalent_length_mm": screen_row.get(
                        "raw_receiver_full_section_equivalent_length_mm"
                    ),
                    "matched_bore_patch_interval_from_axis_datum_mm": membership[
                        "bore_patch"
                    ].get("patch_interval_projected_from_axis_datum_mm"),
                    "matched_bore_patch_overlap_length_mm": membership[
                        "bore_patch"
                    ].get("axial_overlap_length_mm"),
                    "finished_receiver_axis_envelope_clear": screen_row.get(
                        "finished_receiver_axis_envelope_clear"
                    ),
                    "source_historical_occupied_length_mm": source.get(
                        "source_occupied_length_mm"
                    ),
                    "purchased_nominal_length_mm": nominal_length,
                },
                "features": [membership],
                "panel_receiver_contact": {
                    "screen_interface": {
                        key: interface.get(key)
                        for key in (
                            "panel_member",
                            "receiver_member",
                            "fixed_hillman_axis_ids",
                            "geometry_state",
                            "finite_shared_planar_face_area_mm2",
                            "common_volume_mm3",
                            "minimum_separation_mm",
                        )
                    },
                    "contact_graph_association": edge,
                    "status": "finite model face-contact geometry only",
                },
                "support_edge_evidence": {
                    "status": "timber-neighbor geometry only; no complete load-transfer path or support adequacy is established",
                    "receiver_to_frame_path_complete_in_source_inventory": source_path[
                        "receiver_to_frame_path_complete"
                    ],
                    "current_receiver_timber_neighbor_contacts": timber_contacts.get(
                        receiver, []
                    ),
                },
            }
        )

    if dict(statuses) != STATUS_COUNTS:
        raise ValueError("panel axes must be 58 retained and 8 moved")
    counts = screen.get("counts", {})
    if (
        counts.get("panel_kicker_axes_total") != AXIS_COUNT
        or counts.get("unchanged_source_station_axes")
        != STATUS_COUNTS["source_station_retained"]
        or counts.get("moved_axes") != STATUS_COUNTS["moved"]
        or counts.get("current_receiver_member_counts") != dict(receivers)
    ):
        raise ValueError("receiver-screen counts disagree with the 66 current axes")

    center = screen.get("four_moved_kicker_center_receiver_check", {})
    if center.get("current_receiver_map") != CENTER_KICKER_CURRENT_RECEIVERS:
        raise ValueError(
            "current center-kicker receiver map differs from the center posts"
        )
    if center.get("previous_backer_shapes_present_in_current_composition") is not False:
        raise ValueError("historical inner backers appear in the current composition")
    member_ids = {
        row.get("member_id")
        for row in graph.get("inventories", {}).get("physical_members", [])
    }
    if member_ids & {"inner_kicker_backer_left", "inner_kicker_backer_right"}:
        raise ValueError("historical inner backer appears in the current contact graph")
    seam = screen.get("panel_to_receiver_interfaces", {}).get("kicker_center_seam", {})

    return {
        "schema": "wood_joint_current_panel_receiver_transfer_inventory/v1",
        "candidate": CANDIDATE,
        "geometry_revision_id": GEOMETRY_REVISION,
        "status": "saved nominal geometry inventory; no screw action or joint acceptance",
        "counts": {
            "panel_kicker_axes_total": len(axes),
            "unchanged_source_station_axes": statuses["source_station_retained"],
            "moved_axes": statuses["moved"],
            "current_receiver_member_counts": dict(sorted(receivers.items())),
            "current_panel_receiver_pairs": len(pairs),
            "axes_with_one_finished_bore_patch": len(axes),
        },
        "axes": axes,
        "current_center_kicker_receiver_check": {
            "current_receiver_map": dict(center["current_receiver_map"]),
            "previous_backer_shapes_present_in_current_composition": False,
            "previous_backer_shape_ids_present": [],
            "side_to_side_center_post_bbox_gap_x_mm": center.get(
                "side_to_side_center_post_bbox_gap_x_mm"
            ),
            "center_seam": {
                key: seam.get(key)
                for key in (
                    "panel_edge_to_edge_x_gap_mm",
                    "panel_edge_planes_touch_by_x_extent",
                    "left_panel_edge_to_left_center_post_inner_face_x_mm",
                    "right_center_post_inner_face_to_right_panel_edge_x_mm",
                    "nearest_moved_kicker_axis_to_panel_seam_center_x_mm",
                    "panel_to_panel_interface",
                    "limits",
                )
                if key in seam
            },
            "limits": [
                "The center posts are current model receivers; former inner backers are absent.",
                "Post margins and panel-edge geometry do not evaluate panel bending, continuous seam support, or capacity.",
            ],
        },
        "limits": LIMITS,
    }


def build_report(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build a sorted 66-axis inventory and its source-byte pins."""
    pins = _Pins(Path(root))
    inventory = _load(pins, SOURCE_INVENTORY, "wood_joint_source_inventory/v1")
    manifest03 = _load(
        pins, MANIFEST03, "wood_joint_current_full_frame_input_manifest/v2"
    )
    manifest04 = _load(
        pins, MANIFEST04, "wood_joint_current_full_frame_input_manifest/v3"
    )
    screen = _load(pins, RECEIVER_SCREEN, "wood_joint_current_receiver_screen/v1")
    graph = _load(pins, CONTACT_GRAPH, "wood_joint_current_contact_graph/v1")
    feature = _load(
        pins, FEATURE_REGISTER, "wood_joint_axis_finished_feature_register/v1"
    )
    axis_pins = _load(pins, FEATURE_SOURCE_PINS, "wood_joint_axis_source_pins/v1")
    feature_pins = _load(
        pins,
        FEATURE_CLOSURE_PINS,
        "wood_joint_current_finished_feature_register_source_pins/v1",
    )
    _verify_closures(
        pins,
        source_inventory=inventory,
        manifest03=manifest03,
        manifest04=manifest04,
        graph=graph,
        feature=feature,
        axis_pins=axis_pins,
        feature_pins=feature_pins,
    )
    return (
        _build_report(inventory, manifest03, manifest04, screen, graph, feature),
        {"sources": pins.records()},
    )
