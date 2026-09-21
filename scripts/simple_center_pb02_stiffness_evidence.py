"""Build and authenticate deduplicated, non-releasing PB02 stiffness evidence."""

# ruff: noqa: SIM905 -- compact immutable field inventories keep this module bounded.

import gzip
import hashlib
import io
import json
import math
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

SCHEMA = "simple_center_pb02_stiffness_evidence/v1"
MANIFEST = "manifest.json"
MANIFEST_CHECKSUM = "manifest.sha256"
FINAL_ARTIFACTS = "input.json frame.dat frame.frd frame.12d".split()
NO_RELEASE_FIELDS = """qualified_for_design actual_joint_demands_qualified
resistance_checked acceptance drilling_released fabrication_released""".split()
FAILED_ATTEMPT_FIELDS = """case attempt contact_update_strategy
contact_active_set_converged numerically_accepted termination contact_cycle_count
report_sha256 model_sha256 source_map_sha256""".split()
SUMMARY_IDENTITY_FIELDS = """schema candidate active_geometry_fingerprint case_order
loads geometry_inventory stiffness_selection producer_source_sha256""".split()
EXPECTED_VALIDATION = dict.fromkeys(
    """geometry_inventory topology_inventory candidate_identity stiffness_inventory
producer_source_inventory six_case_load_inventory
all_accepted_case_equilibrium_audits""".split(),
    True,
)
REQUIRED_REPORT_TRUE = """contact_active_set_converged
axial_tension_active_set_converged axial_tension_assumption_passed
closed_bearing_assumption_passed global_equilibrium_passed
member_equilibrium_passed mpc_check_passed numerically_accepted""".split()
MANIFEST_FIELDS = """schema candidate geometry_fingerprint
accepted_trial_order_n_per_mm trials failed_trials source_paths source_map_sha256
producer_source_paths producer_source_map_sha256 objects source_maps_identical
producer_source_maps_identical single_variable_stiffness_comparison_eligible
developmental_only qualified_for_design drilling_released fabrication_released
structural_released"""
OBJECT_FIELDS = "path uncompressed_size gzip_size gzip_sha256"
TRIAL_FIELDS = """floor_contact_n_per_mm summary
deterministic_input_fingerprint cases accepted_case_count accepted_comparison_slot
forces_retained_only_in_accepted_reports"""
CASE_FIELDS = "accepted_path report model_identity final_cycle artifacts"
FAILED_TRIAL_FIELDS = """floor_contact_n_per_mm status
accepted_comparison_slot forces_retained reports_retained solver_artifacts_retained
accepted_case_count_before_failure case_order failure_case failure_reason candidate
source_map_sha256 attempts qualified_for_design drilling_released
fabrication_released structural_released"""


@dataclass(frozen=True)
class FailedSuiteSpec:
    root: Path
    failure_case: str
    failure_reason: str


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _canonical_bytes(value: object, *, pretty: bool = False) -> bytes:
    if pretty:
        text = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    else:
        text = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return text.encode()


def _canonical_sha256(value: object) -> str:
    return _sha256_bytes(_canonical_bytes(value))


def _gzip_bytes(data: bytes) -> bytes:
    target = io.BytesIO()
    with gzip.GzipFile(
        filename="", mode="wb", fileobj=target, compresslevel=9, mtime=0
    ) as stream:
        stream.write(data)
    return target.getvalue()


def _stiffness_key(value: float) -> str:
    value = float(value)
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError("stiffness values must be finite and positive")
    return format(value, ".15g")


def _ordered_stiffnesses(values) -> tuple[float, ...]:
    result = tuple(float(value) for value in values)
    if (
        not result
        or len(set(result)) != len(result)
        or any(not math.isfinite(value) or value <= 0.0 for value in result)
    ):
        raise ValueError("ordered stiffnesses must be nonempty and unique")
    return result


def _safe_relative(text: object, label: str) -> Path:
    if not isinstance(text, str) or not text:
        raise TypeError(f"{label} path is missing")
    pure = PurePosixPath(text)
    if "\\" in text or pure.is_absolute() or ".." in pure.parts or "." in pure.parts:
        raise ValueError(f"{label} path escapes its root")
    return Path(*pure.parts)


def _safe_file(root: Path, relative: object, label: str) -> Path:
    path = (root / _safe_relative(relative, label)).resolve()
    resolved_root = root.resolve()
    if not path.is_relative_to(resolved_root):
        raise ValueError(f"{label} path escapes its root")
    if not path.is_file():
        raise ValueError(f"{label} file is missing")
    return path


def _no_release(record: dict, label: str) -> None:
    if record.get("developmental_only") is not True or any(
        record.get(field) is not False for field in NO_RELEASE_FIELDS
    ):
        raise ValueError(f"{label} release boundary changed")


def _store_object(root: Path, objects: dict, data: bytes) -> str:
    digest = _sha256_bytes(data)
    compressed = _gzip_bytes(data)
    relative = Path("objects") / digest[:2] / f"{digest}.gz"
    path = root / relative
    descriptor = {
        "path": relative.as_posix(),
        "uncompressed_size": len(data),
        "gzip_size": len(compressed),
        "gzip_sha256": _sha256_bytes(compressed),
    }
    existing = objects.get(digest)
    if existing is not None:
        if existing != descriptor or path.read_bytes() != compressed:
            raise ValueError("content-addressed object collision")
        return digest
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(compressed)
    objects[digest] = descriptor
    return digest


def _snapshot_bytes(snapshot_root: Path, source_map: dict) -> dict[str, bytes]:
    if not snapshot_root.is_dir() or not isinstance(source_map, dict) or not source_map:
        raise ValueError("retained source snapshot closure is missing")
    actual_paths = {
        path.relative_to(snapshot_root).as_posix(): path
        for path in snapshot_root.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    if set(actual_paths) != set(source_map):
        raise ValueError("retained source snapshot inventory changed")
    result = {}
    for relative, expected_hash in sorted(source_map.items()):
        path = actual_paths[relative]
        data = path.read_bytes()
        if _sha256_bytes(data) != expected_hash:
            raise ValueError(f"retained source snapshot changed: {relative}")
        result[relative] = data
    return result


def _trial_floor(summary: dict) -> object:
    selected = summary.get("stiffness_selection", {}).get("exact_selected_values", {})
    return selected.get("floor_contact_n_per_mm")


def _authenticate_accepted_summary(summary: dict, stiffness: float) -> None:
    try:
        identity = {field: summary[field] for field in SUMMARY_IDENTITY_FIELDS}
    except KeyError as error:
        raise ValueError("accepted suite identity is incomplete") from error
    if (
        summary.get("schema") != "simple_center_pb02_diagnostic_run/v1"
        or _trial_floor(summary) != stiffness
        or summary.get("deterministic_input_fingerprint") != _canonical_sha256(identity)
        or summary.get("validation") != EXPECTED_VALIDATION
        or summary.get("rejected_attempt_forces_included") is not False
    ):
        raise ValueError("accepted suite deterministic identity changed")
    _no_release(summary, "accepted suite summary")


def _authenticate_accepted_report(
    report: dict, summary: dict, case: str, directory: Path
) -> dict:
    scope = report.get("diagnostic_scope", {})
    selected = scope.get("stiffness_selection", {})
    load = summary["loads"].get(case, {})
    parameters = report.get("parameters", {})
    force = parameters.get("force_xyz_n")
    model = directory / "model.pkl"
    if (
        report.get("candidate") != summary.get("candidate")
        or scope.get("case") != case
        or scope.get("candidate") != summary.get("candidate")
        or scope.get("deterministic_input_fingerprint")
        != summary.get("deterministic_input_fingerprint")
        or selected != summary.get("stiffness_selection")
        or parameters.get("hold") != load.get("hold")
        or not isinstance(force, list)
        or len(force) != 3
        or force[:2] != load.get("horizontal_force_xy_n")
        or parameters.get("stiffnesses", {}).get("floor") != _trial_floor(summary)
        or any(report.get(field) is not True for field in REQUIRED_REPORT_TRUE)
        or not model.is_file()
        or report.get("pb02_model_identity") != _sha256_bytes(model.read_bytes())
        or report.get("qualified_for_design") is not False
        or report.get("actual_joint_demands_qualified") is not False
        or report.get("drilling_released") is not False
        or report.get("fabrication_released") is not False
    ):
        raise ValueError(f"{case}: accepted report identity changed")
    _no_release(scope, f"{case}: report scope")
    source_map = report.get("source_sha256")
    if not isinstance(source_map, dict) or not source_map:
        raise ValueError(f"{case}: full source map is missing")
    return source_map


def _accepted_trial(
    suite_root: Path,
    stiffness: float,
    package_root: Path,
    objects: dict,
    *,
    capture_source_closure: bool,
) -> tuple[dict, dict, dict, dict[str, bytes] | None]:
    summary_path = suite_root / "pb02-six-case-diagnostic.json"
    if not summary_path.is_file():
        raise ValueError("accepted suite summary is missing")
    summary_data = summary_path.read_bytes()
    summary = json.loads(summary_data)
    _authenticate_accepted_summary(summary, stiffness)
    case_order = summary.get("case_order")
    accepted = summary.get("accepted_cases")
    if (
        not isinstance(case_order, list)
        or not isinstance(accepted, dict)
        or case_order != list(accepted)
        or summary.get("accepted_case_count") != len(case_order)
    ):
        raise ValueError("accepted case inventory changed")

    suite_root = suite_root.resolve()
    trial_cases = {}
    source_maps = []
    snapshot_payloads = None
    for case in case_order:
        accepted_row = accepted[case]
        directory = _safe_file(
            suite_root,
            f"{accepted_row.get('path')}/report.json",
            f"{case}: accepted case",
        ).parent
        report_path = directory / "report.json"
        report_data = report_path.read_bytes()
        report_hash = _sha256_bytes(report_data)
        report = json.loads(report_data)
        if (
            report_hash != accepted_row.get("report_sha256")
            or accepted_row.get("numerically_accepted") is not True
            or accepted_row.get("forces_reported_only_in_authenticated_case_report")
            is not True
        ):
            raise ValueError(f"{case}: accepted report identity changed")
        source_map = _authenticate_accepted_report(report, summary, case, directory)
        source_maps.append(source_map)
        if capture_source_closure and snapshot_payloads is None:
            snapshot_payloads = _snapshot_bytes(
                directory / "source_snapshots", source_map
            )
        cycles = report.get("contact_cycles", [])
        if not cycles or not isinstance(cycles[-1].get("directory"), str):
            raise ValueError(f"{case}: final cycle is missing")
        cycle = cycles[-1]["directory"]
        _safe_relative(cycle, f"{case}: final cycle")
        artifact_hashes = report.get("artifact_sha256", {})
        artifacts = {}
        for filename in FINAL_ARTIFACTS:
            relative = f"{cycle}/{filename}"
            artifact_path = _safe_file(directory, relative, f"{case}: artifact")
            data = artifact_path.read_bytes()
            digest = _sha256_bytes(data)
            if digest != artifact_hashes.get(relative):
                raise ValueError(f"{case}: final-cycle artifact changed")
            artifacts[filename] = _store_object(package_root, objects, data)
        trial_cases[case] = {
            "accepted_path": accepted_row["path"],
            "report": _store_object(package_root, objects, report_data),
            "model_identity": report.get("pb02_model_identity"),
            "final_cycle": cycle,
            "artifacts": artifacts,
        }

    if any(source_map != source_maps[0] for source_map in source_maps):
        raise ValueError("full source maps must be identical among accepted reports")
    producer_map = summary.get("producer_source_sha256")
    if not isinstance(producer_map, dict) or any(
        source_maps[0].get(path) != digest for path, digest in producer_map.items()
    ):
        raise ValueError("producer source map is not an authenticated source subset")
    trial = {
        "floor_contact_n_per_mm": stiffness,
        "summary": _store_object(package_root, objects, summary_data),
        "deterministic_input_fingerprint": summary.get(
            "deterministic_input_fingerprint"
        ),
        "cases": trial_cases,
        "accepted_case_count": len(trial_cases),
        "accepted_comparison_slot": True,
        "forces_retained_only_in_accepted_reports": True,
    }
    return trial, source_maps[0], producer_map, snapshot_payloads


def _failed_trial(
    spec: FailedSuiteSpec, stiffness: float, case_order: list[str], candidate: str
) -> dict:
    if (
        spec.failure_case not in case_order
        or not isinstance(spec.failure_reason, str)
        or not spec.failure_reason.strip()
    ):
        raise ValueError("failed suite requires an explicit valid case and reason")
    attempt_root = Path(spec.root) / "attempts"
    report_paths = sorted(attempt_root.glob("*/report.json"))
    attempts = []
    source_maps = []
    accepted_cases = set()
    for report_path in report_paths:
        directory = report_path.parent
        matching = [
            case for case in case_order if directory.name.startswith(f"{case}-")
        ]
        if len(matching) != 1:
            raise ValueError("failed suite attempt case cannot be authenticated")
        case = matching[0]
        report_data = report_path.read_bytes()
        report = json.loads(report_data)
        source_map = report.get("source_sha256")
        floor = report.get("parameters", {}).get("stiffnesses", {}).get("floor")
        scope_case = report.get("diagnostic_scope", {}).get("case")
        model = directory / "model.pkl"
        if (
            report.get("candidate") != candidate
            or floor != stiffness
            or scope_case not in (None, case)
            or not isinstance(source_map, dict)
            or not source_map
            or not model.is_file()
            or report.get("qualified_for_design") is not False
            or report.get("actual_joint_demands_qualified") is not False
        ):
            raise ValueError("failed suite attempt identity changed")
        source_maps.append(source_map)
        accepted = report.get("numerically_accepted") is True
        if accepted:
            accepted_cases.add(case)
        attempts.append(
            {
                "case": case,
                "attempt": directory.name.removeprefix(f"{case}-"),
                "contact_update_strategy": report.get("contact_update_strategy"),
                "contact_active_set_converged": report.get(
                    "contact_active_set_converged"
                ),
                "numerically_accepted": accepted,
                "termination": report.get("termination"),
                "contact_cycle_count": len(report.get("contact_cycles", [])),
                "report_sha256": _sha256_bytes(report_data),
                "model_sha256": _sha256_bytes(model.read_bytes()),
                "source_map_sha256": _canonical_sha256(source_map),
            }
        )
    if (
        not attempts
        or any(source_map != source_maps[0] for source_map in source_maps)
        or not any(
            row["case"] == spec.failure_case
            and row["numerically_accepted"] is False
            and row["contact_active_set_converged"] is False
            for row in attempts
        )
    ):
        raise ValueError("failed suite has no authenticated nonconverged attempt")
    return {
        "floor_contact_n_per_mm": stiffness,
        "status": "failed_nonconverged_not_accepted",
        "accepted_comparison_slot": False,
        "forces_retained": False,
        "reports_retained": False,
        "solver_artifacts_retained": False,
        "accepted_case_count_before_failure": len(accepted_cases),
        "case_order": case_order,
        "failure_case": spec.failure_case,
        "failure_reason": spec.failure_reason.strip(),
        "candidate": candidate,
        "source_map_sha256": _canonical_sha256(source_maps[0]),
        "attempts": attempts,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


def _write_manifest(root: Path, manifest: dict) -> None:
    data = _canonical_bytes(manifest, pretty=True)
    (root / MANIFEST).write_bytes(data)
    (root / MANIFEST_CHECKSUM).write_text(f"{_sha256_bytes(data)}  {MANIFEST}\n")


def build(
    accepted_suites: dict[float, Path],
    output: Path,
    *,
    ordered_stiffnesses,
    failed_suites: dict[float, FailedSuiteSpec] | None = None,
) -> dict:
    order = _ordered_stiffnesses(ordered_stiffnesses)
    accepted = {float(key): Path(value) for key, value in accepted_suites.items()}
    if len(accepted) != len(accepted_suites):
        raise ValueError("accepted suite stiffnesses must be unique")
    if set(accepted) != set(order):
        raise ValueError("accepted suites must exactly match ordered stiffnesses")
    failed = {float(key): value for key, value in (failed_suites or {}).items()}
    if any(not isinstance(value, FailedSuiteSpec) for value in failed.values()):
        raise TypeError("failed suites must use FailedSuiteSpec")
    if set(failed) & set(order):
        raise ValueError("failed suites cannot satisfy an accepted comparison slot")
    if len(failed) != len(failed_suites or {}):
        raise ValueError("failed suite stiffnesses must be unique")

    output = Path(output)
    if output.exists():
        raise FileExistsError(f"compact package already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        objects = {}
        trials = {}
        source_maps = []
        producer_maps = []
        source_payloads = None
        candidate = None
        geometry = None
        case_order = None
        for stiffness in order:
            trial, source_map, producer_map, retained_sources = _accepted_trial(
                accepted[stiffness],
                stiffness,
                temporary,
                objects,
                capture_source_closure=source_payloads is None,
            )
            if retained_sources is not None:
                source_payloads = retained_sources
            summary_object = temporary / objects[trial["summary"]]["path"]
            summary = json.loads(gzip.decompress(summary_object.read_bytes()))
            current_candidate = summary.get("candidate")
            current_geometry = summary.get("active_geometry_fingerprint")
            current_case_order = summary.get("case_order")
            if candidate is None:
                candidate, geometry = current_candidate, current_geometry
                case_order = current_case_order
            elif (candidate, geometry, case_order) != (
                current_candidate,
                current_geometry,
                current_case_order,
            ):
                raise ValueError("accepted suite geometry identity changed")
            trials[_stiffness_key(stiffness)] = trial
            source_maps.append(source_map)
            producer_maps.append(producer_map)
        if any(source_map != source_maps[0] for source_map in source_maps):
            raise ValueError("full source maps must be identical among accepted suites")
        if any(producer_map != producer_maps[0] for producer_map in producer_maps):
            raise ValueError(
                "full producer maps must be identical among accepted suites"
            )

        if source_payloads is None:
            raise ValueError("accepted source snapshot closure was not retained")
        source_objects = {
            relative: _store_object(temporary, objects, data)
            for relative, data in source_payloads.items()
        }
        failed_trials = {
            _stiffness_key(stiffness): _failed_trial(
                spec, stiffness, list(case_order), candidate
            )
            for stiffness, spec in sorted(failed.items())
        }
        manifest = {
            "schema": SCHEMA,
            "candidate": candidate,
            "geometry_fingerprint": geometry,
            "accepted_trial_order_n_per_mm": list(order),
            "trials": trials,
            "failed_trials": failed_trials,
            "source_paths": source_objects,
            "source_map_sha256": _canonical_sha256(source_maps[0]),
            "producer_source_paths": producer_maps[0],
            "producer_source_map_sha256": _canonical_sha256(producer_maps[0]),
            "objects": dict(sorted(objects.items())),
            "source_maps_identical": True,
            "producer_source_maps_identical": True,
            "single_variable_stiffness_comparison_eligible": True,
            "developmental_only": True,
            "qualified_for_design": False,
            "drilling_released": False,
            "fabrication_released": False,
            "structural_released": False,
        }
        _write_manifest(temporary, manifest)
        authenticate(temporary)
        temporary.replace(output)
        return authenticate(output)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def _load_manifest(package: Path) -> dict:
    manifest_path = package / MANIFEST
    checksum_path = package / MANIFEST_CHECKSUM
    if not manifest_path.is_file() or not checksum_path.is_file():
        raise ValueError("compact manifest or checksum is missing")
    data = manifest_path.read_bytes()
    expected_line = f"{_sha256_bytes(data)}  {MANIFEST}\n"
    if checksum_path.read_text() != expected_line:
        raise ValueError("manifest checksum changed")
    manifest = json.loads(data)
    if _canonical_bytes(manifest, pretty=True) != data:
        raise ValueError("manifest encoding is not canonical")
    return manifest


def _authenticate_objects(package: Path, manifest: dict) -> dict[str, bytes]:
    objects = manifest.get("objects")
    if not isinstance(objects, dict):
        raise TypeError("object manifest is missing")
    expected_files = {MANIFEST, MANIFEST_CHECKSUM}
    decoded = {}
    for digest, descriptor in objects.items():
        expected_relative = f"objects/{digest[:2]}/{digest}.gz"
        if (
            not isinstance(digest, str)
            or not _is_sha256(digest)
            or not isinstance(descriptor, dict)
            or set(descriptor) != set(OBJECT_FIELDS.split())
            or descriptor.get("path") != expected_relative
        ):
            raise ValueError("object path is not content addressed")
        path = _safe_file(package, expected_relative, "object")
        expected_files.add(expected_relative)
        compressed = path.read_bytes()
        if len(compressed) != descriptor.get("gzip_size") or _sha256_bytes(
            compressed
        ) != descriptor.get("gzip_sha256"):
            raise ValueError("compressed object changed")
        try:
            data = gzip.decompress(compressed)
        except (EOFError, OSError) as error:
            raise ValueError("compressed object is invalid") from error
        if (
            len(data) != descriptor.get("uncompressed_size")
            or _sha256_bytes(data) != digest
        ):
            raise ValueError("decompressed object identity changed")
        if _gzip_bytes(data) != compressed:
            raise ValueError("object gzip encoding is not deterministic")
        decoded[digest] = data
    actual_files = {
        path.relative_to(package).as_posix()
        for path in package.rglob("*")
        if path.is_file()
    }
    if actual_files != expected_files:
        raise ValueError("object inventory changed")
    return decoded


def _referenced_objects(manifest: dict) -> set[str]:
    referenced = set(manifest.get("source_paths", {}).values())
    for trial in manifest.get("trials", {}).values():
        referenced.add(trial.get("summary"))
        for case in trial.get("cases", {}).values():
            referenced.add(case.get("report"))
            referenced.update(case.get("artifacts", {}).values())
    return referenced


def _authenticate_manifest_contract(manifest: dict, decoded: dict) -> dict:
    order = _ordered_stiffnesses(manifest.get("accepted_trial_order_n_per_mm", []))
    trial_keys = [_stiffness_key(value) for value in order]
    trials = manifest.get("trials")
    if (
        set(manifest) != set(MANIFEST_FIELDS.split())
        or manifest.get("schema") != SCHEMA
        or not isinstance(trials, dict)
        or set(trials) != set(trial_keys)
        or manifest.get("source_maps_identical") is not True
        or manifest.get("producer_source_maps_identical") is not True
        or manifest.get("single_variable_stiffness_comparison_eligible") is not True
        or manifest.get("developmental_only") is not True
        or manifest.get("qualified_for_design") is not False
        or manifest.get("drilling_released") is not False
        or manifest.get("fabrication_released") is not False
        or manifest.get("structural_released") is not False
    ):
        raise ValueError("compact manifest contract changed")
    referenced = _referenced_objects(manifest)
    if None in referenced or referenced != set(decoded):
        raise ValueError("unreferenced or missing content object")
    source_paths = manifest.get("source_paths")
    producer_paths = manifest.get("producer_source_paths")
    if (
        not isinstance(source_paths, dict)
        or not isinstance(producer_paths, dict)
        or _canonical_sha256(source_paths) != manifest.get("source_map_sha256")
        or _canonical_sha256(producer_paths)
        != manifest.get("producer_source_map_sha256")
        or any(
            source_paths.get(path) != digest for path, digest in producer_paths.items()
        )
    ):
        raise ValueError("compact source closure changed")
    for relative, digest in source_paths.items():
        _safe_relative(relative, "source manifest")
        if _sha256_bytes(decoded[digest]) != digest:
            raise ValueError("compact source object changed")

    reports_by_stiffness = {}
    common_source_map = source_paths
    for stiffness, key in zip(order, trial_keys, strict=True):
        trial = trials[key]
        if (
            not isinstance(trial, dict)
            or set(trial) != set(TRIAL_FIELDS.split())
            or trial.get("floor_contact_n_per_mm") != stiffness
            or trial.get("accepted_comparison_slot") is not True
            or trial.get("forces_retained_only_in_accepted_reports") is not True
        ):
            raise ValueError("accepted trial manifest changed")
        summary = json.loads(decoded[trial["summary"]])
        _authenticate_accepted_summary(summary, stiffness)
        if (
            _trial_floor(summary) != stiffness
            or summary.get("candidate") != manifest.get("candidate")
            or summary.get("active_geometry_fingerprint")
            != manifest.get("geometry_fingerprint")
            or summary.get("deterministic_input_fingerprint")
            != trial.get("deterministic_input_fingerprint")
            or summary.get("producer_source_sha256") != producer_paths
        ):
            raise ValueError("retained accepted summary changed")
        case_order = summary.get("case_order")
        accepted = summary.get("accepted_cases")
        cases = trial.get("cases")
        if (
            not isinstance(case_order, list)
            or not isinstance(accepted, dict)
            or not isinstance(cases, dict)
            or case_order != list(accepted)
            or set(cases) != set(case_order)
            or trial.get("accepted_case_count") != len(case_order)
            or summary.get("accepted_case_count") != len(case_order)
        ):
            raise ValueError("retained accepted case inventory changed")
        reports = {}
        for case in case_order:
            row = cases[case]
            if not isinstance(row, dict) or set(row) != set(CASE_FIELDS.split()):
                raise ValueError(f"{case}: retained case manifest changed")
            _safe_relative(row.get("accepted_path"), f"{case}: retained path")
            if row.get("accepted_path") != accepted[case].get("path"):
                raise ValueError(f"{case}: retained path identity changed")
            report_data = decoded[row["report"]]
            if _sha256_bytes(report_data) != accepted[case].get("report_sha256"):
                raise ValueError(f"{case}: retained report identity changed")
            report = json.loads(report_data)
            _no_release(
                report.get("diagnostic_scope", {}), f"{case}: retained report scope"
            )
            if (
                report.get("source_sha256") != common_source_map
                or report.get("pb02_model_identity") != row.get("model_identity")
                or report.get("diagnostic_scope", {}).get("case") != case
                or report.get("diagnostic_scope", {}).get(
                    "deterministic_input_fingerprint"
                )
                != trial.get("deterministic_input_fingerprint")
            ):
                raise ValueError(f"{case}: retained report scope changed")
            cycle = row.get("final_cycle")
            _safe_relative(cycle, f"{case}: retained final cycle")
            cycles = report.get("contact_cycles", [])
            if not cycles or cycles[-1].get("directory") != cycle:
                raise ValueError(f"{case}: retained final cycle changed")
            artifact_hashes = report.get("artifact_sha256", {})
            if set(row.get("artifacts", {})) != set(FINAL_ARTIFACTS):
                raise ValueError(f"{case}: retained artifact inventory changed")
            for filename, digest in row["artifacts"].items():
                if artifact_hashes.get(f"{cycle}/{filename}") != digest:
                    raise ValueError(f"{case}: retained artifact identity changed")
            reports[case] = report
        reports_by_stiffness[stiffness] = reports

    failed_trials = manifest.get("failed_trials")
    if not isinstance(failed_trials, dict) or set(failed_trials) & set(trial_keys):
        raise ValueError("failed trial inventory changed")
    for key, record in failed_trials.items():
        attempts = record.get("attempts") if isinstance(record, dict) else None
        attempt_rows = attempts if isinstance(attempts, list) else []
        accepted_attempt_cases = {
            attempt.get("case")
            for attempt in attempt_rows
            if attempt.get("numerically_accepted") is True
        }
        if (
            not isinstance(record, dict)
            or set(record) != set(FAILED_TRIAL_FIELDS.split())
            or not isinstance(attempts, list)
            or not attempts
            or any(
                not isinstance(attempt, dict)
                or set(attempt) != set(FAILED_ATTEMPT_FIELDS)
                or attempt.get("case") not in record.get("case_order", [])
                or not _is_sha256(attempt.get("report_sha256"))
                or not _is_sha256(attempt.get("model_sha256"))
                or not _is_sha256(attempt.get("source_map_sha256"))
                for attempt in attempt_rows
            )
            or {attempt["source_map_sha256"] for attempt in attempt_rows}
            != {record.get("source_map_sha256")}
            or len(accepted_attempt_cases)
            != record.get("accepted_case_count_before_failure")
            or _stiffness_key(record.get("floor_contact_n_per_mm")) != key
            or record.get("status") != "failed_nonconverged_not_accepted"
            or record.get("failure_case") not in record.get("case_order", [])
            or not isinstance(record.get("failure_reason"), str)
            or not record.get("failure_reason")
            or not any(
                attempt["case"] == record.get("failure_case")
                and attempt["numerically_accepted"] is False
                and attempt["contact_active_set_converged"] is False
                for attempt in attempts
            )
            or record.get("accepted_comparison_slot") is not False
            or record.get("forces_retained") is not False
            or record.get("reports_retained") is not False
            or record.get("solver_artifacts_retained") is not False
            or record.get("qualified_for_design") is not False
            or record.get("drilling_released") is not False
            or record.get("fabrication_released") is not False
            or record.get("structural_released") is not False
        ):
            raise ValueError("failed trial record changed")
    return reports_by_stiffness


def authenticate(package: Path) -> dict:
    package = Path(package).resolve()
    manifest = _load_manifest(package)
    decoded = _authenticate_objects(package, manifest)
    reports = _authenticate_manifest_contract(manifest, decoded)
    return {
        "status": "authenticated_compact_pb02_stiffness_evidence",
        "trial_floor_contact_n_per_mm": list(reports),
        "reports": reports,
        "failed_trials": manifest["failed_trials"],
        "source_maps_identical": True,
        "producer_source_maps_identical": True,
        "single_variable_stiffness_comparison_eligible": True,
        "qualified_for_design": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }
