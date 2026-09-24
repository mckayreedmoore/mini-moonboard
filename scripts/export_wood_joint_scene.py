"""Export independent WJ-03/WJ-04/WJ-05 trial geometry for owner review."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from mini_moonboard.wood_joint_frame import (
    build_outer_nodes,
    installed_stack_shapes,
    validate_source_binding,
)
from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts import wood_joints_wj05_center_backer_transfer_probe as wj05
from scripts.simple_owner_duty_ledger import selected_duties
from scripts.wood_joint_clearance import build_clearance_report
from scripts.wood_joint_wj04_probe import materialize_trial_geometry

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "site/owner-wood-joints-layout-scene.json"
BASELINE_MANIFEST = ROOT / "site/hybrid/compact-floor-flush-kerf-right/parts.json"
SOURCE_INVENTORY = ROOT / "docs/wood-joints-mvp/source-inventory.json"
WJ04_REPORT = ROOT / "docs/wood-joints-mvp/wj04-probe.json"
WJ05_REPORT = ROOT / "docs/wood-joints-mvp/wj05-center-backer-transfer.json"
WJ05_RECEIVER_AUDIT = ROOT / "docs/wood-joints-mvp/wj05-receiver-audit.json"

RELEASE_FLAGS = (
    "layout_accepted",
    "geometry_accepted",
    "drilling_released",
    "fabrication_released",
    "structural_released",
    "climbing_released",
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _mesh(shape):
    # OCCT may cache/normalize face bounds while meshing. Never tessellate a
    # source-bound object directly; source fingerprints use live face bounds.
    vertices, triangles = shape.copy().tessellate(0.5)
    return {
        "vertices_mm": [list(vertex.toTuple()) for vertex in vertices],
        "triangles": [list(triangle) for triangle in triangles],
    }


def _solid(
    name: str,
    role: str,
    shape,
    side: str,
    owner: str,
    family: str,
    trial_id: str,
):
    box = shape.BoundingBox()
    return {
        "name": name,
        "role": role,
        "side": side,
        "replacement_owner": owner,
        "family": family,
        "trial_id": trial_id,
        "bounds_xyz_mm": [
            box.xmin,
            box.xmax,
            box.ymin,
            box.ymax,
            box.zmin,
            box.zmax,
        ],
        "mesh": _mesh(shape),
    }


def _fingerprint_freshness(recorded: dict[str, str]) -> dict[str, Any]:
    stale = []
    for relative_path, expected in recorded.items():
        path = ROOT / relative_path
        if not path.is_file() or _sha(path) != expected:
            stale.append(relative_path)
    return {"fresh": not stale, "stale_paths": sorted(stale)}


def _duty_sds(duties: dict[str, dict], stations: set[str]) -> set[str]:
    return {
        axis
        for station in stations
        for axis in duties[station]["sds_axes"]
    }


def _binding_record(binding) -> dict[str, Any]:
    return asdict(binding)


def _source_binding_identity(binding: dict[str, Any]) -> dict[str, Any]:
    """Normalize both dataclass and serialized clearance source bindings."""
    return {
        "inventory_sha256": binding.get(
            "inventory_sha256", binding.get("source_inventory_sha256")
        ),
        "runtime_module_sha256": binding.get("runtime_module_sha256"),
        "uncut_part_shapes_sha256": binding.get("uncut_part_shapes_sha256"),
        "uncut_host_shape_sha256": binding.get("uncut_host_shape_sha256"),
        "fixed_screw_axes_sha256": binding.get("fixed_screw_axes_sha256"),
        "frame_bolt_axes_sha256": binding.get("frame_bolt_axes_sha256"),
    }


def _stack_hardware_record(stack_id: str, stack) -> dict[str, Any]:
    hardware = stack.hardware
    return {
        "stack_id": stack_id,
        "candidate_id": getattr(hardware, "candidate_id", None),
        "sku": getattr(hardware, "candidate_sku", None),
        "nominal_under_head_length_mm": hardware.under_head_length_mm,
        "steel_diameter_mm": hardware.steel_diameter_mm,
        "cad_occupied_diameter_mm": hardware.cad_occupied_diameter_mm,
        "bore_occupancy_diameter_mm": hardware.drill_diameter_mm,
        "washer_outer_diameter_mm": hardware.washer_od_mm,
        "washer_thickness_mm": hardware.washer_thickness_mm,
        "nut_diameter_mm": hardware.nut_diameter_mm,
        "nut_height_mm": hardware.nut_height_mm,
        "sku_or_dimensions_accepted": False,
    }


def _hardware_summary(materialized) -> list[dict[str, Any]]:
    config = materialized.config.as_dict()
    stacks = {row["stack_id"]: row for row in config["stacks"]}
    return [
        {
            "stack_id": configured.stack_id,
            "candidate_id": configured.hardware_candidate.candidate_id,
            "sku": configured.hardware_candidate.sku,
            "nominal_under_head_length_mm": configured.hardware_candidate.nominal_length_mm,
            "cad_envelope": stacks[configured.stack_id]["cad_envelope"],
            "candidate_only": True,
        }
        for configured in sorted(
            materialized.config.stacks, key=lambda row: row.stack_id
        )
    ]


def _csv_axis_counts(path: Path) -> tuple[int, int]:
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    screws = sum(row["shop_opening_kind"] == "hillman_panel" for row in rows)
    frame_bolts = sum(row["kind"] == "bolt" for row in rows)
    return screws, frame_bolts


def _source_host_cut_count(parts: dict[str, Any]) -> int:
    return sum(
        cut.kind == "bore"
        for part in parts.values()
        for cut in part.modifications
    )


def _append_solid(
    solids: list[dict[str, Any]],
    name: str,
    role: str,
    shape,
    *,
    family: str,
    trial_id: str,
    side: str = "shared",
    owner: str | None = None,
) -> None:
    solids.append(
        _solid(
            name,
            role,
            shape,
            side,
            owner or trial_id,
            family,
            trial_id,
        )
    )


def build_scene(nodes=None, clearance=None):
    nodes = build_outer_nodes() if nodes is None else nodes
    clearance = build_clearance_report(nodes) if clearance is None else clearance
    wj04 = materialize_trial_geometry(config=WJ04_TRIAL)
    wj05_result = json.loads(WJ05_REPORT.read_text())
    wj05_receiver = json.loads(WJ05_RECEIVER_AUDIT.read_text())
    wj05_model, _wj05_source_wood, wj05_wood, wj05_backers, wj05_bolts, wj05_bores, wj05_stacks, wj05_tools, wj05_counterbores = (
        wj05._source_and_candidate()
    )
    # Bind WJ-05 before any display tessellation can touch shared OCCT caches.
    wj05_binding = _binding_record(validate_source_binding(wj05_model))

    duties = selected_duties()
    wj03_duties = {station for node in nodes.values() for station in node.duties}
    wj04_duties = {WJ04_TRIAL.station_id}
    trial_duties = wj03_duties | wj04_duties
    remaining_duties = set(duties) - trial_duties
    wj03_sds = _duty_sds(duties, wj03_duties)
    wj04_sds = _duty_sds(duties, wj04_duties)

    source_hosts = {
        name: part
        for node in nodes.values()
        for name, part in node.source_host_parts.items()
    }
    wj04_host_names = {
        member.source_part_id
        for member in WJ04_TRIAL.members
        if member.source_part_id is not None
    }
    moved_center_posts = {
        f"base_post_center_{side}": wj05_wood[f"base_post_center_{side}"]
        for side in ("left", "right")
    }
    hidden = sorted(
        wj03_duties
        | wj04_duties
        | {f"fastener_{axis}" for axis in wj03_sds | wj04_sds}
        | set(source_hosts)
        | wj04_host_names
        | set(moved_center_posts)
    )

    solids: list[dict[str, Any]] = []
    axes: list[dict[str, Any]] = []
    for name, part in sorted(source_hosts.items()):
        if name == "base_header":
            continue
        _append_solid(
            solids,
            name,
            "candidate_source_host",
            part.finished_shape,
            family="wj03",
            trial_id="wj03_outer_nodes",
            owner="source_host",
        )

    # The shared header shows WJ-03 and WJ-05 bores together. This is a
    # display-only superposition; no cross-trial clash or joint check is run.
    header = source_hosts["base_header"].finished_shape
    for name, bore in wj05_bores.items():
        header = header.cut(bore)
        header = header.cut(wj05_counterbores[name])
    _append_solid(
        solids,
        "base_header/shared_WJ03_WJ05_trial_bores",
        "candidate_source_host",
        header,
        family="shared",
        trial_id="wj03_wj05_shared_header",
        owner="source_host",
    )

    wj03_hardware = []
    for node in nodes.values():
        for part in node.parts.values():
            _append_solid(
                solids,
                part.id,
                "wood_connector",
                part.finished_shape,
                family="wj03",
                trial_id="wj03_outer_nodes",
                side=node.side,
                owner=node.owner_id,
            )
        for bolt_id, stack in node.stacks.items():
            wj03_hardware.append(_stack_hardware_record(bolt_id, stack))
            for role, shape in installed_stack_shapes(stack).items():
                _append_solid(
                    solids,
                    f"{bolt_id}/{role}",
                    f"provisional_bolt_{role}",
                    shape,
                    family="wj03",
                    trial_id="wj03_outer_nodes",
                    side=node.side,
                    owner=node.owner_id,
                )
            axes.append(
                {
                    "family": "wj03",
                    "trial_id": "wj03_outer_nodes",
                    "name": bolt_id,
                    "start_mm": list(stack.under_head_origin.toTuple()),
                    "axis": list(stack.direction.toTuple()),
                    "full_nominal_length_mm": stack.hardware.under_head_length_mm,
                    "steel_diameter_mm": stack.hardware.steel_diameter_mm,
                    "provisional_only": True,
                }
            )

    wj04_members = {member.member_id: member for member in WJ04_TRIAL.members}
    wj04_members[WJ04_TRIAL.cleat.member_id] = WJ04_TRIAL.cleat
    wj04_hardware = _hardware_summary(wj04)
    wj04_candidate_parts = 0
    for name, shape in wj04.finished.items():
        member = wj04_members[name]
        role = "wood_connector" if member.role == "cleat" else "candidate_source_host"
        _append_solid(
            solids,
            name,
            role,
            shape,
            family="wj04",
            trial_id=WJ04_TRIAL.trial_id,
            owner=member.role,
        )
        if member.role == "cleat":
            wj04_candidate_parts += 1
    for stack_id, shape in sorted(wj04.installed.items()):
        _append_solid(
            solids,
            stack_id,
            "provisional_bolt_component",
            shape,
            family="wj04",
            trial_id=WJ04_TRIAL.trial_id,
        )
    for stack_id, stack in sorted(wj04.stacks.items()):
        axes.append(
            {
                "family": "wj04",
                "trial_id": WJ04_TRIAL.trial_id,
                "name": stack_id,
                "start_mm": list(stack.under_head_origin.toTuple()),
                "axis": list(stack.direction.toTuple()),
                "full_nominal_length_mm": stack.hardware.under_head_length_mm,
                "steel_diameter_mm": stack.hardware.steel_diameter_mm,
                "provisional_only": True,
            }
        )

    for name, shape in sorted(moved_center_posts.items()):
        _append_solid(
            solids,
            name,
            "candidate_source_host",
            shape,
            family="wj05",
            trial_id=wj05_result["candidate_id"],
            owner="moved_center_post_trial",
        )
    for name, shape in sorted(wj05_backers.items()):
        _append_solid(
            solids,
            name,
            "wood_connector",
            wj05_wood[name],
            family="wj05",
            trial_id=wj05_result["candidate_id"],
            side=name.rsplit("_", 1)[-1],
            owner="center_backer_transfer_trial",
        )
    for name, shape in sorted(wj05_bolts.items()):
        side = name.split("_")[2]
        _append_solid(
            solids,
            f"bolt/{name}",
            "provisional_wj05_bolt",
            shape,
            family="wj05",
            trial_id=wj05_result["candidate_id"],
            side=side,
        )
        for role, component in wj05_stacks[name].items():
            _append_solid(
                solids,
                f"{name}/{role}",
                f"provisional_wj05_hardware_{role}",
                component,
                family="wj05",
                trial_id=wj05_result["candidate_id"],
                side=side,
            )
        # Show seated socket body envelopes only; these are exterior occupancy
        # proxies, not tool-fit or access qualification.
        for role in ("top_seated", "bottom_seated"):
            _append_solid(
                solids,
                f"{name}/{role}",
                "trial_tool_envelope",
                wj05_tools[name][role],
                family="wj05",
                trial_id=wj05_result["candidate_id"],
                side=side,
            )
        station = wj05.BACKER_BOLT_STATIONS[side][int(name.rsplit("_", 1)[1]) - 1]
        axes.append(
            {
                "family": "wj05",
                "trial_id": wj05_result["candidate_id"],
                "name": name,
                "start_mm": [station[0], station[1], wj05.BOLT_UNDERHEAD_Z_MM],
                "axis": [0, 0, 1],
                "full_nominal_length_mm": wj05.NOMINAL_BOLT_LENGTH_MM,
                "steel_diameter_mm": wj05.BOLT_DIAMETER_MM,
                "provisional_only": True,
            }
        )

    baseline_parts = json.loads(BASELINE_MANIFEST.read_text())["parts"]
    baseline_asset_hashes = {
        part["path"]: _sha(ROOT / "site" / part["path"])
        for part in baseline_parts
    }
    baseline_asset_tree_hash = _canonical_sha256(baseline_asset_hashes)
    source_inventory = json.loads(SOURCE_INVENTORY.read_text())
    source_inventory_sha = _sha(SOURCE_INVENTORY)
    source_commit = source_inventory["source_commit"]
    source_binding = clearance["source_binding"]
    wj04_binding = _binding_record(wj04.source_binding)
    source_identity = _source_binding_identity(source_binding)
    if (
        wj04_binding["inventory_sha256"] != source_inventory_sha
        or wj05_binding["inventory_sha256"] != source_inventory_sha
        or source_binding["source_inventory_sha256"] != source_inventory_sha
        or WJ04_TRIAL.source_commit != source_commit
        or _source_binding_identity(wj04_binding) != source_identity
        or _source_binding_identity(wj05_binding) != source_identity
    ):
        raise ValueError(
            "WJ-03/WJ-04/WJ-05 source commit, inventory, source geometry, or axis hashes differ"
        )
    post_mesh_binding = _binding_record(validate_source_binding())
    if _source_binding_identity(post_mesh_binding) != source_identity:
        raise ValueError("Scene tessellation changed a source-bound geometry or axis fingerprint")

    wj04_report = json.loads(WJ04_REPORT.read_text())
    wj04_freshness = _fingerprint_freshness(wj04_report.get("dependency_sha256", {}))
    if wj04_report.get("producer_sha256") != _sha(ROOT / "scripts/wood_joint_wj04_probe.py"):
        wj04_freshness["stale_paths"].append("scripts/wood_joint_wj04_probe.py")
        wj04_freshness["stale_paths"] = sorted(set(wj04_freshness["stale_paths"]))
        wj04_freshness["fresh"] = False
    if wj04_report.get("source_inventory_sha256") != source_inventory_sha:
        wj04_freshness["stale_paths"].append("docs/wood-joints-mvp/source-inventory.json")
        wj04_freshness["stale_paths"] = sorted(set(wj04_freshness["stale_paths"]))
        wj04_freshness["fresh"] = False
    for field, expected in (
        ("trial_id", WJ04_TRIAL.trial_id),
        ("trial_config_sha256", WJ04_TRIAL.canonical_sha256),
        ("source_commit", source_commit),
    ):
        if wj04_report.get(field) != expected:
            wj04_freshness["stale_paths"].append(f"wj04-report:{field}")
            wj04_freshness["stale_paths"] = sorted(
                set(wj04_freshness["stale_paths"])
            )
            wj04_freshness["fresh"] = False
    if wj04_report.get("station") != WJ04_TRIAL.station_id:
        wj04_freshness["stale_paths"].append("wj04-report:station")
        wj04_freshness["stale_paths"] = sorted(set(wj04_freshness["stale_paths"]))
        wj04_freshness["fresh"] = False

    wj05_transfer_freshness = _fingerprint_freshness(
        wj05_result.get("source_fingerprints_sha256", {})
    )
    wj05_receiver_freshness = _fingerprint_freshness(
        wj05_receiver.get("source_fingerprints_sha256", {})
    )
    if source_binding["source_inventory_sha256"] != source_inventory_sha:
        raise ValueError("WJ-03 clearance report source hash differs from current source inventory")

    wj03_hardware = sorted(wj03_hardware, key=lambda row: row["stack_id"])
    wj04_config = WJ04_TRIAL.as_dict()
    wj05_socket = wj05_receiver["center_receiver_trial"]["socket_outer_envelope_basis"]
    wj05_hardware = {
        "candidate_id": wj05_result["candidate_id"],
        "bolt": {
            "thread": "1/4-20 UNC",
            "nominal_length_mm": wj05.NOMINAL_BOLT_LENGTH_MM,
            "diameter_mm": wj05.BOLT_DIAMETER_MM,
            "selected_sku": False,
        },
        "nut": {
            "across_corners_max_mm": wj05.NUT_DIAMETER_ENVELOPE_MM,
            "height_mm": wj05.NUT_HEIGHT_MM,
            "selected_sku": False,
        },
        "washer": {
            "outer_diameter_mm": wj05.WASHER_DIAMETER_MM,
            "thickness_range_mm": [
                wj05.WASHER_MIN_THICKNESS_MM,
                wj05.WASHER_MAX_THICKNESS_MM,
            ],
            "selected_sku": False,
        },
        "socket_envelope": wj05_socket,
    }
    screw_axis_count, frame_bolt_axis_count = _csv_axis_counts(
        ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
    )

    wj03_clearance_summary = {
        "original_six_clashes_absent": clearance["original_six_clashes_absent"],
        "replacement_nominal_interference_free": clearance[
            "replacement_nominal_interference_free"
        ],
        "decision": clearance["decision"],
        "named_constraint_revisions": clearance["named_constraint_revisions"],
        "rear_projection_summary_mm": clearance["rear_projection_summary_mm"],
        "detached_hardware_path_failures": {
            side: row["failure_groups"]["detached_hardware_geometry"]
            for side, row in clearance["nodes"].items()
        },
        "panel_on_detached_path_hits": {
            side: row["panel_on_detached_path_hits"]
            for side, row in clearance["nodes"].items()
        },
        "kicker_panel_removal_sequence_verified": False,
    }
    trials = {
        "wj03": {
            "label": "WJ-03 mirrored outer-node trial",
            "trial_id": "wj03_outer_nodes",
            "status": f"panel_off_{'nominal_clear' if clearance['replacement_nominal_interference_free'] else 'nominal_interference'}_{clearance['decision']}",
            "source_commit": source_commit,
            "source_inventory_sha256": source_inventory_sha,
            "source_geometry_fingerprint_sha256": clearance["geometry_fingerprint_sha256"],
            "legacy_duty_ids": sorted(wj03_duties),
            "hardware_configuration": wj03_hardware,
            "local_clearance": wj03_clearance_summary,
            "report_freshness": {"fresh": True, "stale_paths": []},
            "gates": {
                "local_panel_off_nominal_interference_free": clearance[
                    "replacement_nominal_interference_free"
                ],
                "layout_accepted": False,
                "geometry_accepted": False,
                "drilling_released": False,
                "fabrication_released": False,
                "structural_released": False,
                "climbing_released": False,
            },
        },
        "wj04": {
            "label": "WJ-04 ordinary rail-to-cleat trial",
            "trial_id": WJ04_TRIAL.trial_id,
            "status": "materialized_component_trial",
            "source_commit": source_commit,
            "source_inventory_sha256": source_inventory_sha,
            "config_schema": wj04_config["schema"],
            "config_sha256": WJ04_TRIAL.canonical_sha256,
            "station_id": WJ04_TRIAL.station_id,
            "legacy_duty_ids": sorted(wj04_duties),
            "hardware_configuration": wj04_hardware,
            "last_recorded_report_status": wj04_report.get("status"),
            "report_freshness": wj04_freshness,
            "local_screen": {
                "cleat_hits": wj04.cleat_hits,
                "contact_area_mm2": wj04.contact_area_mm2,
                "full_candidate_clearance": "not_run",
            },
            "gates": {
                "layout_accepted": False,
                "geometry_accepted": False,
                "drilling_released": False,
                "fabrication_released": False,
                "structural_released": False,
                "climbing_released": False,
            },
        },
        "wj05": {
            "label": "WJ-05 center backer-to-header transfer trial",
            "trial_id": wj05_result["candidate_id"],
            "status": wj05_result["status"],
            "source_commit": source_commit,
            "source_inventory_sha256": source_inventory_sha,
            "legacy_duty_ids": [],
            "hardware_configuration": wj05_hardware,
            "geometry_clear_for_this_probe": wj05_result[
                "geometry_clear_for_this_probe"
            ],
            "report_freshness": wj05_transfer_freshness,
            "receiver_status": wj05_receiver["status"],
            "receiver_axis_ids": wj05_receiver["center_receiver_trial"][
                "center_axis_ids"
            ],
            "receiver_report_freshness": wj05_receiver_freshness,
            "gates": {
                "receiver_path_resolved": False,
                "retained_frame_bolt_holes_reconciled": False,
                "layout_accepted": False,
                "geometry_accepted": False,
                "drilling_released": False,
                "fabrication_released": False,
                "structural_released": False,
                "climbing_released": False,
            },
        },
    }
    for family in ("wj03", "wj04", "wj05"):
        trials[family]["geometry_solid_count"] = sum(
            solid["family"] == family for solid in solids
        )
    baseline_asset_paths = {part["path"] for part in baseline_parts}
    installed_hardware_count = sum(
        solid["role"].startswith("provisional_bolt")
        or solid["role"].startswith("provisional_wj05")
        for solid in solids
    )
    source_host_names = set(source_hosts) | wj04_host_names | set(moved_center_posts)
    return {
        "schema": "owner_wood_joints_layout_scene/v2",
        "status": "independent_WJ03_WJ04_WJ05_trial_overlay_integrated_clearance_not_run",
        "candidate": "compact-floor-flush-wood-joints-development",
        "baseline": "compact-floor-flush-kerf-right",
        "scope": (
            "Independent WJ-03, WJ-04, and WJ-05 trial geometry is shown in selected-baseline coordinates. "
            "The overlay is for review only; cross-trial interference, complete candidate clearance, "
            "and integrated joint acceptance have not been run."
        ),
        "hidden_baseline_visual_names": hidden,
        "solids": solids,
        "provisional_bolt_axes": axes,
        "trials": trials,
        "integrated_clearance": {
            "status": "not_run",
            "cross_trial_interference_checked": False,
            "full_candidate_clearance_checked": False,
            "integrated_joint_acceptance": False,
        },
        "legacy_duty_summary": {
            "total": len(duties),
            "trial_geometry_duty_ids": sorted(trial_duties),
            "trial_geometry_duties": len(trial_duties),
            "remaining_legacy_duty_ids": sorted(remaining_duties),
            "remaining_legacy_duties": len(remaining_duties),
            "wj05_receiver_trial_maps_structural_duty": False,
        },
        "source_binding": source_binding,
        "wj04_source_binding": wj04_binding,
        "wj05_source_binding": wj05_binding,
        "baseline_manifest_sha256": _sha(BASELINE_MANIFEST),
        "baseline_asset_sha256": baseline_asset_hashes,
        "baseline_asset_tree_sha256": baseline_asset_tree_hash,
        "geometry_fingerprint_sha256": clearance["geometry_fingerprint_sha256"],
        "producer": {
            "command": "uv run python -m scripts.export_wood_joint_scene",
            "dependency_sha256": {
                name: _sha(ROOT / name)
                for name in (
                    "scripts/export_wood_joint_scene.py",
                    "scripts/wood_joint_clearance.py",
                    "mini_moonboard/wood_joint_frame.py",
                    "mini_moonboard/wood_joint_geometry.py",
                    "mini_moonboard/wood_joint_wj04_config.py",
                    "scripts/wood_joint_wj04_probe.py",
                    "scripts/wood_joints_wj05_center_backer_transfer_probe.py",
                    "mini_moonboard/wood_joint_wj05_socket.py",
                    "scripts/owner_layout_protected.py",
                    "docs/wood-joints-mvp/source-inventory.json",
                    "docs/wood-joints-mvp/wj04-probe.json",
                    "docs/wood-joints-mvp/wj05-center-backer-transfer.json",
                    "docs/wood-joints-mvp/wj05-receiver-audit.json",
                    "site/hybrid/compact-floor-flush-kerf-right/parts.json",
                )
            },
        },
        "inventory": {
            "mapped_legacy_duties": len(trial_duties),
            "removed_legacy_sds_visuals": len(wj03_sds | wj04_sds),
            "outer_nodes": len(nodes),
            "connector_cut_parts": sum(len(node.parts) for node in nodes.values())
            + wj04_candidate_parts,
            "changed_source_hosts": len(source_host_names),
            "source_host_bores": _source_host_cut_count(source_hosts)
            + len(wj04.bores)
            + len(wj05_bores),
            "provisional_bolts": len(axes),
            "installed_hardware_component_solids": installed_hardware_count,
            "fixed_panel_kicker_screw_axes": screw_axis_count,
            "retained_frame_bolt_axes": frame_bolt_axis_count,
            "trial_geometry_solids": len(solids),
            "baseline_assets": len(baseline_asset_paths),
        },
        "limits": [
            "WJ-03, WJ-04, and WJ-05 are separate diagnostics shown together; their cross-trial fit and complete frame clearance are not checked.",
            "WJ-04 probe report freshness is shown separately from materialized trial geometry; stale report findings are not current proof.",
            "WJ-05 geometry-clear status applies only to its local transfer probe; the center receiver audit remains blocked and does not map a structural duty.",
            "WJ-05 shifted center posts are uncut trial shapes; retained frame-bolt holes have not been reconciled to the shifted positions.",
            "Bolt, washer, nut, and socket shapes are occupancy or trial envelopes, not purchase, drilling, tool-fit, or installation instructions.",
            "Selected-baseline context remains conditional documentation; physical stock, delivered hardware, fabrication, resistance, and climbing release remain unverified.",
        ],
        "layout_accepted": False,
        "geometry_accepted": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
        "climbing_released": False,
    }


def main() -> None:
    OUTPUT.write_text(json.dumps(build_scene(), indent=2) + "\n")


if __name__ == "__main__":
    main()
