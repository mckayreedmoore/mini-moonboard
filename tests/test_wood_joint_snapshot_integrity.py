import hashlib
import json
from pathlib import Path

from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts.wood_joint_snapshot_integrity import build_report

DOCS = "docs/wood-joints-mvp"
PROBE = f"{DOCS}/wj04-probe.json"
MECHANICS = f"{DOCS}/wj04-early-mechanics.json"
TOOL_ACCESS = f"{DOCS}/wj04-tool-access.json"
BOLT_TOOL = f"{DOCS}/wj04-bolt-tool-receiving-screen.json"
SPACER = f"{DOCS}/wj04-spacer-salvage-screen.json"
WIDE_TRIAL = f"{DOCS}/wj04-wide-4in-rejected.json"
WIDE_3P75_TRIAL = f"{DOCS}/wj04-wide-3p75in-rejected.json"
NARROW_HISTORICAL = f"{DOCS}/wj04-narrow-3p5in-historical.json"
VIEWER = "site/owner-wood-joints-layout-scene.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(root: Path, relative: str, value: dict) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def _refresh_manifest_hash(root: Path, relative: str) -> None:
    path = root / f"{DOCS}/artifact-manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["artifact_sha256"][relative] = _sha(root / relative)
    path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")


def _fixture(
    tmp_path: Path,
    *,
    spacer_grip: float = 76.2,
    mechanics_rail_area: float = 11401.398713,
) -> Path:
    inventory = f"{DOCS}/source-inventory.json"
    producer_probe = "scripts/wood_joint_wj04_probe.py"
    producer_mechanics = "scripts/wood_joint_wj04_early_mechanics.py"
    producer_tool_access = "scripts/wood_joint_wj04_tool_access.py"
    producer_viewer = "scripts/export_wood_joint_scene.py"
    dependency = "mini_moonboard/wood_joint_geometry.py"
    config_path = "mini_moonboard/wood_joint_wj04_config.py"
    source_root = Path(__file__).resolve().parents[1]
    for relative, content in (
        (inventory, (source_root / inventory).read_bytes()),
        (producer_probe, b"probe producer fixture\n"),
        (producer_mechanics, b"mechanics producer fixture\n"),
        (producer_tool_access, b"tool-access producer fixture\n"),
        (producer_viewer, b"combined viewer producer fixture\n"),
        (dependency, b"geometry dependency fixture\n"),
        (config_path, (source_root / config_path).read_bytes()),
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    _write_json(
        tmp_path,
        "wood-joints-candidate.json",
        {
            "candidate": "wood-joints-fixture",
            "status": "fixture_development",
            "source": {
                "repository_commit": WJ04_TRIAL.source_commit,
                "source_variant": "kerf-right",
            },
        },
    )

    config = WJ04_TRIAL.as_dict()
    cleat = next(member for member in WJ04_TRIAL.members if member.role == "cleat")
    configured_stacks = {stack.stack_id: stack for stack in WJ04_TRIAL.stacks}
    probe_stacks = {}
    for row in config["stacks"]:
        stack = configured_stacks[row["stack_id"]]
        probe_stacks[row["stack_id"]] = {
            "axis_global_xyz_mm": list(row["axis_point_global_mm"]),
            "direction_global_xyz": list(row["axis_direction_global"]),
            "grip_mm": row["grip_mm"],
            "nominal_under_head_length_mm": stack.hardware_candidate.nominal_length_mm,
            "layers": [dict(layer) for layer in row["layers"]],
            "cad_envelope": dict(row["cad_envelope"]),
            "bolt_candidate_id": stack.hardware_candidate.candidate_id,
            "bolt_sku": stack.hardware_candidate.sku,
        }
    points = {name: row["axis_global_xyz_mm"] for name, row in probe_stacks.items()}
    rail_area = round(cleat.size_x_t_n_mm[0] * cleat.size_x_t_n_mm[2], 6)
    principal_area = round(cleat.size_x_t_n_mm[1] * cleat.size_x_t_n_mm[2], 6)

    probe = {
        "candidate": "wood-joints-fixture",
        "source_commit": WJ04_TRIAL.source_commit,
        "station": WJ04_TRIAL.station_id,
        "trial_id": WJ04_TRIAL.trial_id,
        "trial_config_sha256": WJ04_TRIAL.canonical_sha256,
        "rail_nominal_partial_thread_bolt_length_mm": configured_stacks[
            "rail_1"
        ].hardware_candidate.nominal_length_mm,
        "producer_sha256": _sha(tmp_path / producer_probe),
        "dependency_sha256": {dependency: _sha(tmp_path / dependency)},
        "source_inventory_sha256": _sha(tmp_path / inventory),
        "catalog_candidate_ids": {
            "bolts": sorted(
                candidate.candidate_id for candidate in WJ04_TRIAL.fasteners.bolts
            ),
            "nut": WJ04_TRIAL.fasteners.nut.candidate_id,
            "washer": WJ04_TRIAL.fasteners.washer.candidate_id,
            "tools": sorted(
                candidate.candidate_id for candidate in WJ04_TRIAL.fasteners.tools
            ),
        },
        "stock": {
            "section_x_t_n_mm": list(cleat.size_x_t_n_mm),
            "grain_axis": cleat.grain_axis,
            "actual_stock_and_grade_verified": WJ04_TRIAL.stock_grade_verified,
        },
        "contact_area_mm2": {
            "rail_to_cleat": 11401.398713,
            "principal_to_cleat": 4560.569999,
        },
        "stacks": probe_stacks,
        "purchase_approved": WJ04_TRIAL.purchase_approved,
        "drilling_released": WJ04_TRIAL.drilling_released,
        "fabrication_released": WJ04_TRIAL.fabrication_released,
        "structural_released": WJ04_TRIAL.structural_released,
    }
    _write_json(tmp_path, PROBE, probe)

    mechanics = {
        "candidate": "wood-joints-fixture",
        "station": WJ04_TRIAL.station_id,
        "status": "diagnostic_only_no_acceptance",
        "input_sha256": {
            inventory: _sha(tmp_path / inventory),
            PROBE: _sha(tmp_path / PROBE),
            producer_mechanics: _sha(tmp_path / producer_mechanics),
        },
        "canonical_trial": {
            "trial_id": WJ04_TRIAL.trial_id,
            "trial_config_sha256": WJ04_TRIAL.canonical_sha256,
            "config_source_sha256": _sha(tmp_path / config_path),
            "source_inventory_sha256": _sha(tmp_path / inventory),
            "active_probe_trial_config_sha256": WJ04_TRIAL.canonical_sha256,
            "cleat_size_x_t_n_mm": list(cleat.size_x_t_n_mm),
            "stock_grade_verified": WJ04_TRIAL.stock_grade_verified,
            "purchase_approved": WJ04_TRIAL.purchase_approved,
            "drilling_released": WJ04_TRIAL.drilling_released,
            "fabrication_released": WJ04_TRIAL.fabrication_released,
            "structural_released": WJ04_TRIAL.structural_released,
        },
        "interface_summary": {
            "rail": {
                "group_stack_ids": ["rail_1", "rail_2"],
                "finite_probe_contact_area_mm2": mechanics_rail_area,
                "canonical_bounds_rectangle_area_mm2": rail_area,
                "finite_probe_minus_rectangle_area_mm2": round(
                    mechanics_rail_area - rail_area, 6
                ),
                "bolt_spacing_mm": 25.4,
                "centroid_global_xyz_mm": [
                    (points["rail_1"][index] + points["rail_2"][index]) / 2
                    for index in range(3)
                ],
                "contact_face_geometry": {
                    "finite_probe_contact_area_mm2": mechanics_rail_area,
                    "canonical_bounds_rectangle_area_mm2": rail_area,
                    "finite_probe_minus_rectangle_area_mm2": round(
                        mechanics_rail_area - rail_area, 6
                    ),
                    "finite_probe_to_rectangle_area_ratio": round(
                        mechanics_rail_area / rail_area, 6
                    ),
                    "finite_probe_area_measurement": {
                        "source_field": "active_probe.contact_area_mm2.rail_to_cleat",
                        "probe_producer_sha256": _sha(tmp_path / producer_probe),
                        "probe_depth_mm": 0.1,
                        "method_id": "thin_inward_intersection_volume_divided_by_probe_depth",
                    },
                    "row_span_mm": cleat.size_x_t_n_mm[0],
                },
            },
            "principal": {
                "group_stack_ids": ["upright_1", "upright_2"],
                "finite_probe_contact_area_mm2": 4560.569999,
                "canonical_bounds_rectangle_area_mm2": principal_area,
                "finite_probe_minus_rectangle_area_mm2": round(
                    4560.569999 - principal_area, 6
                ),
                "bolt_spacing_mm": 27.0,
                "centroid_global_xyz_mm": [
                    (points["upright_1"][index] + points["upright_2"][index]) / 2
                    for index in range(3)
                ],
                "contact_face_geometry": {
                    "finite_probe_contact_area_mm2": 4560.569999,
                    "canonical_bounds_rectangle_area_mm2": principal_area,
                    "finite_probe_minus_rectangle_area_mm2": round(
                        4560.569999 - principal_area, 6
                    ),
                    "finite_probe_to_rectangle_area_ratio": round(
                        4560.569999 / principal_area, 6
                    ),
                    "finite_probe_area_measurement": {
                        "source_field": "active_probe.contact_area_mm2.principal_to_cleat",
                        "probe_producer_sha256": _sha(tmp_path / producer_probe),
                        "probe_depth_mm": 0.1,
                        "method_id": "thin_inward_intersection_volume_divided_by_probe_depth",
                    },
                    "row_span_mm": cleat.size_x_t_n_mm[2],
                },
            },
        },
    }
    _write_json(tmp_path, MECHANICS, mechanics)
    _write_json(
        tmp_path,
        TOOL_ACCESS,
        {
            "schema": "wood_joint_wj04_tool_access/v1",
            "candidate": "wood-joints-fixture",
            "source_commit": WJ04_TRIAL.source_commit,
            "trial_id": WJ04_TRIAL.trial_id,
            "station_id": WJ04_TRIAL.station_id,
            "source_variant": WJ04_TRIAL.source_variant,
            "source_inventory_sha256": _sha(tmp_path / inventory),
            "trial_config_sha256": WJ04_TRIAL.canonical_sha256,
            "producer_sha256": _sha(tmp_path / producer_tool_access),
            "config_source_sha256": _sha(tmp_path / config_path),
            "dependency_sha256": {config_path: _sha(tmp_path / config_path)},
            "input_artifact_sha256": {inventory: _sha(tmp_path / inventory)},
        },
    )
    _write_json(
        tmp_path,
        VIEWER,
        {
            "schema": "owner_wood_joints_layout_scene/v2",
            "source_commit": WJ04_TRIAL.source_commit,
            "integrated_clearance": "not_run",
            "source_fingerprints_sha256": {
                inventory: _sha(tmp_path / inventory),
                config_path: _sha(tmp_path / config_path),
            },
            "producer_sha256": _sha(tmp_path / producer_viewer),
            "trials": {
                "wj04": {
                    "config_schema": "wood_joint_wj04_trial_config/v1",
                    "trial_id": WJ04_TRIAL.trial_id,
                    "config_sha256": WJ04_TRIAL.canonical_sha256,
                    "source_commit": WJ04_TRIAL.source_commit,
                    "source_inventory_sha256": _sha(tmp_path / inventory),
                    "report_freshness": {"fresh": True, "stale_paths": []},
                    "geometry_solid_count": 4,
                },
            },
        },
    )
    _write_json(
        tmp_path,
        BOLT_TOOL,
        {
            "candidate": "wood-joints-fixture",
            "station": "clip_horizontal_lower_right_1",
            "geometry_source": PROBE,
            "cleat_x_t_n_mm": [95.25, 38.1, 119.7],
            "wood_grip_mm": 76.2,
        },
    )
    _write_json(
        tmp_path,
        SPACER,
        {
            "candidate": "wood-joints-fixture",
            "station": "clip_horizontal_lower_right_1",
            "geometry_source": PROBE,
            "wood_grip_mm": spacer_grip,
            "spacer": {"length_mm": [12.573, 12.827]},
        },
    )
    _write_json(
        tmp_path,
        WIDE_TRIAL,
        {
            "candidate": "wood-joints-fixture",
            "source_commit": WJ04_TRIAL.source_commit,
            "trial_id": "wide_x101p6",
            "status": "reject_protected_wire_clash",
            "producer_sha256": "historical-producer-hash",
            "dependency_sha256": {
                "scripts/historical_probe_dependency.py": "historical-dependency-hash"
            },
            "stock": {"section_x_t_n_mm": [101.6, 38.1, 119.7]},
            "rail_nominal_partial_thread_bolt_length_mm": 101.6,
        },
    )
    _write_json(
        tmp_path,
        WIDE_3P75_TRIAL,
        {
            "candidate": "wood-joints-fixture",
            "source_commit": WJ04_TRIAL.source_commit,
            "trial_id": "wide_x95p25_historical_generic_bolt",
            "status": "historical_generic_bolt_trial",
            "stock": {"section_x_t_n_mm": [95.25, 38.1, 119.7]},
        },
    )
    _write_json(
        tmp_path,
        NARROW_HISTORICAL,
        {
            "candidate": "wood-joints-fixture",
            "source_commit": WJ04_TRIAL.source_commit,
            "trial_id": "narrow_x95p25_historical_generic_bolt",
            "status": "historical_generic_bolt_trial",
            "stock": {"section_x_t_n_mm": [95.25, 38.1, 119.7]},
        },
    )

    artifact_paths = [
        PROBE,
        MECHANICS,
        TOOL_ACCESS,
        BOLT_TOOL,
        SPACER,
        WIDE_TRIAL,
        WIDE_3P75_TRIAL,
        NARROW_HISTORICAL,
        VIEWER,
    ]
    manifest = {
        "schema": "wood_joint_artifact_manifest/v1",
        "candidate": "wood-joints-fixture",
        "source_commit": WJ04_TRIAL.source_commit,
        "artifact_sha256": {
            relative: _sha(tmp_path / relative) for relative in artifact_paths
        },
        "release": False,
    }
    _write_json(tmp_path, f"{DOCS}/artifact-manifest.json", manifest)
    return tmp_path


def test_consistent_hashes_and_wj04_dimensions_are_diagnostic_only(tmp_path):
    root = _fixture(tmp_path)

    report = build_report(root)

    assert report["snapshot_state"] == "consistent"
    assert report["candidate"] == "wood-joints-fixture"
    assert (
        report["active_configuration_and_hardware_identity"]["status"] == "consistent"
    )
    assert (
        report["active_configuration_and_hardware_identity"]["contract"]["candidate"]
        == "wood-joints-fixture"
    )
    assert report["wj04_dimensional_configuration"]["status"] == "consistent"
    assert report["active_combined_viewer"]["status"] == "consistent"
    assert all(
        row["status"] == "consistent"
        for row in report["wj04_dimensional_configuration"]["checks"]
    )
    assert "not acceptance" in report["claim_limit"]


def test_catalog_candidates_are_reported_without_accepting_hardware(tmp_path):
    report = build_report(_fixture(tmp_path))

    hardware = report["active_configuration_and_hardware_identity"][
        "active_wj04_hardware_identity"
    ]
    by_stack = hardware["stacks"]
    assert by_stack["rail_1"]["bolt_sku"] == "25C375HCS5Z"
    assert by_stack["upright_1"]["bolt_sku"] == "25C600HCS5Z"
    candidates = {row["candidate_id"]: row for row in hardware["catalog_candidates"]}
    assert candidates["kl_jack_25cnfh5z"]["sku"] == "25CNFH5Z"
    assert candidates["fastenal_type_a_wide_uss_plain_steel"]["kind"] == "washer"
    assert hardware["catalog_candidate_ids"]["tools"] == ["facom_34_7_16"]
    assert hardware["acceptance"]["accepted_hardware_established"] is False
    assert hardware["acceptance"]["purchase_approved"] is False
    assert hardware["acceptance"]["capacity_verified"] is False
    assert hardware["acceptance"]["structural_released"] is False


def test_active_wj04_trial_and_sku_drift_stale_even_with_refreshed_manifest(tmp_path):
    root = _fixture(tmp_path)
    probe_path = root / PROBE
    probe = json.loads(probe_path.read_text(encoding="utf-8"))
    probe["trial_config_sha256"] = "old-config-fingerprint"
    probe["stacks"]["rail_1"]["bolt_sku"] = "old-generic-bolt"
    _write_json(root, PROBE, probe)

    mechanics_path = root / MECHANICS
    mechanics = json.loads(mechanics_path.read_text(encoding="utf-8"))
    mechanics["input_sha256"][PROBE] = _sha(probe_path)
    _write_json(root, MECHANICS, mechanics)
    _refresh_manifest_hash(root, PROBE)
    _refresh_manifest_hash(root, MECHANICS)

    report = build_report(root)

    assert report["artifact_manifest"]["artifact_state"] == "consistent"
    assert report["producer_and_input_hashes"]["status"] == "consistent"
    assert report["wj04_dimensional_configuration"]["status"] == "stale"
    assert report["snapshot_state"] == "stale"
    checks = report["wj04_dimensional_configuration"]["checks"]
    assert (
        next(
            row
            for row in checks
            if row["check"] == "probe trial config fingerprint vs shared config"
        )["status"]
        == "stale"
    )
    assert (
        next(
            row for row in checks if row["check"] == "rail_1 bolt_sku vs shared config"
        )["status"]
        == "stale"
    )


def test_combined_viewer_config_binding_is_checked(tmp_path):
    root = _fixture(tmp_path)
    viewer_path = root / VIEWER
    viewer = json.loads(viewer_path.read_text(encoding="utf-8"))
    viewer["trials"]["wj04"]["config_sha256"] = "old-config-fingerprint"
    _write_json(root, VIEWER, viewer)
    _refresh_manifest_hash(root, VIEWER)

    report = build_report(root)

    assert report["artifact_manifest"]["artifact_state"] == "consistent"
    assert report["active_combined_viewer"]["status"] == "stale"
    assert report["snapshot_state"] == "stale"


def test_active_tool_access_report_binds_canonical_trial_and_producer(tmp_path):
    root = _fixture(tmp_path)
    report_path = root / TOOL_ACCESS
    tool_report = json.loads(report_path.read_text(encoding="utf-8"))
    tool_report["trial_config_sha256"] = "old-config-fingerprint"
    _write_json(root, TOOL_ACCESS, tool_report)
    _refresh_manifest_hash(root, TOOL_ACCESS)

    report = build_report(root)

    assert report["artifact_manifest"]["artifact_state"] == "consistent"
    assert report["active_tool_access_report"]["path"] == TOOL_ACCESS
    tool_artifact = next(
        row
        for row in report["artifact_manifest"]["artifacts"]
        if row["path"] == TOOL_ACCESS
    )
    assert tool_artifact["scope"] == "active_snapshot"
    assert report["active_tool_access_report"]["configuration_checks"]
    check = next(
        row
        for row in report["wj04_dimensional_configuration"]["checks"]
        if row["check"] == "tool-access trial config fingerprint vs shared config"
    )
    assert check["status"] == "stale"
    assert report["snapshot_state"] == "stale"


def test_active_tool_access_producer_hash_is_reported_as_changed(tmp_path):
    root = _fixture(tmp_path)
    producer = root / "scripts/wood_joint_wj04_tool_access.py"
    producer.write_text("changed tool-access producer\n", encoding="utf-8")

    report = build_report(root)

    changed = {
        row["path"]
        for row in report["producer_and_input_hashes"]["changed_dependencies"]
    }
    assert "scripts/wood_joint_wj04_tool_access.py" in changed
    assert report["snapshot_state"] == "stale"


def test_changed_producer_dependency_is_stale_and_reported(tmp_path):
    root = _fixture(tmp_path)
    dependency = root / "mini_moonboard/wood_joint_geometry.py"
    dependency.write_text("changed dependency\n", encoding="utf-8")

    report = build_report(root)

    assert report["snapshot_state"] == "stale"
    changed_paths = {
        row["path"]
        for row in report["producer_and_input_hashes"]["changed_dependencies"]
    }
    assert "mini_moonboard/wood_joint_geometry.py" in changed_paths
    assert report["wj04_dimensional_configuration"]["status"] == "consistent"


def test_mechanics_input_hashes_are_checked_even_when_manifested(tmp_path):
    root = _fixture(tmp_path)
    producer = root / "scripts/wood_joint_wj04_early_mechanics.py"
    producer.write_text("changed mechanics producer\n", encoding="utf-8")

    report = build_report(root)

    assert report["snapshot_state"] == "stale"
    changed_paths = {
        row["path"]
        for row in report["producer_and_input_hashes"]["changed_dependencies"]
    }
    assert "scripts/wood_joint_wj04_early_mechanics.py" in changed_paths
    mechanics = next(
        row
        for row in report["artifact_manifest"]["artifacts"]
        if row["path"] == MECHANICS
    )
    assert mechanics["status"] == "consistent"
    assert any(
        binding["status"] == "stale" for binding in mechanics["embedded_bindings"]
    )


def test_historical_trial_bytes_are_pinned_without_live_producer_freshness(tmp_path):
    root = _fixture(tmp_path)

    report = build_report(root)

    assert report["snapshot_state"] == "consistent"
    historical = next(
        row
        for row in report["artifact_manifest"]["artifacts"]
        if row["path"] == WIDE_TRIAL
    )
    assert historical["scope"] == "historical_manifest_only"
    assert historical["status"] == "consistent"
    assert historical["embedded_bindings"] == []
    narrow = next(
        row
        for row in report["artifact_manifest"]["artifacts"]
        if row["path"] == NARROW_HISTORICAL
    )
    assert narrow["scope"] == "historical_manifest_only"
    assert narrow["status"] == "consistent"
    assert narrow["embedded_bindings"] == []
    receiving = next(
        row
        for row in report["artifact_manifest"]["artifacts"]
        if row["path"] == BOLT_TOOL
    )
    assert receiving["scope"] == "historical_manifest_only"
    assert receiving["embedded_bindings"] == []
    assert report["producer_and_input_hashes"]["missing_dependencies"] == []


def test_historical_trial_requires_manifest_byte_identity(tmp_path):
    root = _fixture(tmp_path)
    manifest_path = root / f"{DOCS}/artifact-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    del manifest["artifact_sha256"][NARROW_HISTORICAL]
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")

    report = build_report(root)

    assert report["artifact_manifest"]["artifact_state"] == "missing"
    assert report["snapshot_state"] == "missing"
    missing = next(
        row
        for row in report["artifact_manifest"]["artifacts"]
        if row["path"] == NARROW_HISTORICAL
    )
    assert missing["manifest_entry_missing"] is True
    assert missing["current_sha256"] == _sha(root / NARROW_HISTORICAL)
    assert missing["scope"] == "historical_manifest_only"


def test_missing_diagnostic_snapshot_is_distinct_from_stale(tmp_path):
    root = _fixture(tmp_path)
    (root / PROBE).unlink()

    report = build_report(root)

    assert report["snapshot_state"] == "missing"
    assert report["wj04_dimensional_configuration"]["status"] == "missing"
    probe_artifact = next(
        row for row in report["artifact_manifest"]["artifacts"] if row["path"] == PROBE
    )
    assert probe_artifact["status"] == "missing"


def test_wj04_stack_geometry_disagreement_detected_without_hash_staleness(tmp_path):
    root = _fixture(tmp_path, spacer_grip=75.0)

    report = build_report(root)

    assert report["producer_and_input_hashes"]["status"] == "consistent"
    assert report["artifact_manifest"]["artifact_state"] == "consistent"
    assert report["snapshot_state"] == "consistent"
    dimension_report = report["wj04_dimensional_configuration"]
    assert dimension_report["status"] == "consistent"
    spacer = next(
        row
        for row in dimension_report["historical_stack_screens"]
        if row["path"] == SPACER
    )
    assert spacer["status"] == "different_historical_configuration"
    grip_comparison = next(
        row for row in spacer["comparisons"] if row["field"] == "rail_wood_grip_mm"
    )
    assert grip_comparison["recorded"] == 75.0
    assert grip_comparison["active_probe"] == 76.2
    assert "does not stale" in spacer["claim_limit"]


def test_active_mechanics_dimension_disagreement_is_stale(tmp_path):
    root = _fixture(tmp_path, mechanics_rail_area=11000.0)

    report = build_report(root)

    assert report["snapshot_state"] == "stale"
    assert report["wj04_dimensional_configuration"]["status"] == "stale"
    mismatch = next(
        row
        for row in report["wj04_dimensional_configuration"]["checks"]
        if row["check"] == "rail mechanics finite-probe area vs probe report"
    )
    assert mismatch["actual"] == 11000.0
    assert mismatch["expected"] == 11401.398713
    nominal_rectangle = next(
        row
        for row in report["wj04_dimensional_configuration"]["checks"]
        if row["check"] == "rail mechanics nominal rectangle area vs probe section"
    )
    assert nominal_rectangle["actual"] == 11401.425
    assert nominal_rectangle["expected"] == 11401.425
    assert (
        "acceptance is established"
        in report["wj04_dimensional_configuration"]["claim_limit"]
    )
