"""Source-pinned validator for the one declared A12-rear BG001 sensitivity input.

This module validates input differences only. It does not read DAT output,
recover forces, or launch a native solver.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
HERE = Path(__file__).resolve().parent
BASELINE_PACKET = SERIES / "current-springa-selected-floor-a12-rear-attempt03"
VARIANT_PACKET = HERE
AUDIT_SOURCE = SERIES / "current-springa-selected-floor-response-audit-attempt03/response_audit.py"
STABLE_RECOVERY_SOURCE = SERIES / "current-springa-frame-response-audit-attempt01/response_audit.py"
PRECISION_RESPONSE_SOURCE = SERIES / "current-springa-zero-u-token-response-audit-attempt01/response_audit.py"
PRECISION_RECOVERY_SOURCE = SERIES / "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py"
RESPONSE_CORE_FORK = HERE / "sensitivity_response_core.py"

BASELINE_MODEL_SHA256 = "8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8"
BASELINE_DECK_SHA256 = "e8f7376817daa1e3ac0b7d5f85c52b16115c2cef39291486d1800e0e847e0aff"
BASELINE_RESPONSE_SHA256 = "892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274"
VARIANT_MODEL_SHA256 = "ddb65e7630eb0f6f5f44ae762eb00c61a53642122a62376f46959ccc7b1eccbb"
VARIANT_DECK_SHA256 = "dd38c90d0aef23e109449992061e885cc79278b26bc42ab1dd1e63d58cf5383c"
VARIANT_MANIFEST_SHA256 = "ba9d632f61ed218dca8d8ad503270ad516d6881a458f06925566b635856e57b2"
PREPARER_SHA256 = "6ba100b0b8afdb360eb125883053c732071239c1747a198959523761d68af724"
AUDIT_SOURCE_SHA256 = "41536568057101155290880e1d6228ea9eda8fc283678cd06ee3acb5945797ed"
STABLE_RECOVERY_SHA256 = "b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c"
PRECISION_RESPONSE_SHA256 = "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0"
PRECISION_RECOVERY_SHA256 = "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d"
RESPONSE_CORE_FORK_SHA256 = "44e2fa9cda9d286ae991a022f894e5ea2dea8693e0be3042cd46a3fdf868566b"
SENSITIVITY_SOURCE_SHA256 = "0994ae3f5a54c6eb985141c54eb3d38d455678482ed2ac5a6205e2a84096a9c0"
PROPERTY_SOURCE_SHA256 = "26b6e8bf8800208bfb867439694afa705558ac63ca338778e9210e940a55d9a1"
SOURCE_LOAD_REGISTER = SERIES / "current-six-case-source-load-register-attempt01/register.json"
SOURCE_LOAD_REGISTER_SHA256 = "7a638a49fc5086b4d5fed52148286a300b8b271f7d380b1a131ea8e17b094508"

OLD_K = 4670.054188242363
NEW_K = 2401.714359616974
TARGETS = {
    "knee_outer_left_post_1/outer-seat-axial-tie": {
        "name": "knee_outer_left_post_1/outer-seat-axial-tie",
        "group": "SPR1771", "index": 1770, "element": 3674,
        "native_binding_index": 1222, "axis_id": "knee_outer_left_post_1",
    },
    "knee_outer_left_post_2/outer-seat-axial-tie": {
        "name": "knee_outer_left_post_2/outer-seat-axial-tie",
        "group": "SPR1772", "index": 1771, "element": 3675,
        "native_binding_index": 1223, "axis_id": "knee_outer_left_post_2",
    },
}


class SensitivityInputError(ValueError):
    """Input is not the exact pinned variant or contains an unapproved change."""


_CONTRACT_SEAL = object()


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def _canonical_sha(value: Any) -> str:
    return _sha_bytes(_canonical(value))


def _require_hash(path: Path, expected: str, label: str) -> None:
    if not path.is_file():
        raise SensitivityInputError(f"Missing pinned {label}: {path}")
    actual = _sha(path)
    if actual != expected:
        raise SensitivityInputError(f"Pinned {label} changed: {actual} != {expected}")


def _load_auditor():
    _require_hash(AUDIT_SOURCE, AUDIT_SOURCE_SHA256, "selected-floor audit source")
    _require_hash(STABLE_RECOVERY_SOURCE, STABLE_RECOVERY_SHA256, "stable recovery source")
    spec = importlib.util.spec_from_file_location("pinned_selected_floor_audit_for_sensitivity", AUDIT_SOURCE)
    if spec is None or spec.loader is None:
        raise SensitivityInputError("Cannot load the pinned selected-floor response auditor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if getattr(module, "STABLE_AUDIT_SHA256", None) != STABLE_RECOVERY_SHA256:
        raise SensitivityInputError("Selected-floor auditor names a different recovery kernel")
    return module


def _load_precision_auditor():
    _require_hash(PRECISION_RESPONSE_SOURCE, PRECISION_RESPONSE_SHA256,
                  "pinned 711 zero-U response wrapper")
    _require_hash(PRECISION_RECOVERY_SOURCE, PRECISION_RECOVERY_SHA256,
                  "pinned 711 zero-U recovery kernel")
    spec = importlib.util.spec_from_file_location(
        "pinned_zero_u_response_audit_for_sensitivity", PRECISION_RESPONSE_SOURCE,
    )
    if spec is None or spec.loader is None:
        raise SensitivityInputError("Cannot load the pinned 711 response wrapper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if getattr(module, "STABLE_AUDIT_SHA256", None) != PRECISION_RECOVERY_SHA256:
        raise SensitivityInputError("Pinned 711 wrapper names a different recovery kernel")
    return module


def _diff_paths(left: Any, right: Any, path: str = "") -> list[str]:
    if type(left) is not type(right):
        return [path or "/"]
    if isinstance(left, dict):
        if left.keys() != right.keys():
            return [path + "/<keys>"]
        changed: list[str] = []
        for key in left:
            changed.extend(_diff_paths(left[key], right[key], f"{path}/{key}"))
        return changed
    if isinstance(left, list):
        if len(left) != len(right):
            return [path + "/<length>"]
        changed = []
        for i, (a, b) in enumerate(zip(left, right, strict=True)):
            changed.extend(_diff_paths(a, b, f"{path}/{i}"))
        return changed
    return [] if left == right else [path or "/"]


def _expected_model_paths(baseline: dict[str, Any]) -> set[str]:
    expected = set()
    for field_name in ("nonlinear_native_carrier_bindings", "unilateral_springa_bindings"):
        rows = baseline[field_name]
        for name, target in TARGETS.items():
            matches = [(i, row) for i, row in enumerate(rows)
                       if row.get("name") == name and row.get("group") == target["group"]]
            if len(matches) != 1:
                raise SensitivityInputError(f"Baseline must contain exactly one {name}")
            i, row = matches[0]
            if i != target["native_binding_index"]:
                raise SensitivityInputError(f"Unexpected {field_name} index for {name}: {i}")
            prefix = f"/{field_name}/{i}"
            expected.update((prefix + "/stiffness_n_per_mm",
                             prefix + "/force_vs_elongation_table_N_mm/2/0"))
    return expected


def _spring_table(deck: str, group: str) -> tuple[list[list[float]], list[int]]:
    lines = deck.splitlines()
    header = f"*SPRING,ELSET={group},NONLINEAR"
    headers = [i for i, line in enumerate(lines) if line.strip().upper() == header.upper()]
    if len(headers) != 1:
        raise SensitivityInputError(f"Expected one exact nonlinear table for {group}")
    records: list[list[float]] = []
    indices: list[int] = []
    for i in range(headers[0] + 1, len(lines)):
        line = lines[i].strip()
        if not line:
            continue
        if line.startswith("*"):
            break
        try:
            record = [float(value.strip()) for value in line.split(",")]
        except ValueError as error:
            raise SensitivityInputError(f"Malformed table row for {group}: {line}") from error
        records.append(record)
        indices.append(i)
    if len(records) != 3 or any(len(row) != 2 for row in records):
        raise SensitivityInputError(f"{group} must retain exactly three (force,elongation) points")
    return records, indices


def _assert_tie_record(row: dict[str, Any], *, expected_k: float, target: dict[str, Any], label: str) -> None:
    if row.get("group") != target["group"] or row.get("name") != target["name"]:
        raise SensitivityInputError(f"{label}: tie identity changed")
    if int(row.get("source_inventory_row_index", -1)) != target["index"]:
        raise SensitivityInputError(f"{label}: source inventory index changed")
    if int(row.get("source_element", -1)) != target["element"]:
        raise SensitivityInputError(f"{label}: source element changed")
    if not abs(float(row.get("stiffness_n_per_mm", float("nan"))) - expected_k) <= 1.0e-10:
        raise SensitivityInputError(f"{label}: stiffness differs from the declared override")
    if row.get("force_law") != "k * max(q_mm, 0)":
        raise SensitivityInputError(f"{label}: tension-only law changed")
    if row.get("table_domain_mm") != [-10.0, 10.0] or row.get("initial_span_mm") != 100.0:
        raise SensitivityInputError(f"{label}: table domain or numerical span changed")
    if row.get("force_vs_elongation_table_N_mm") != [[0.0, -10.0], [0.0, 0.0], [expected_k * 10.0, 10.0]]:
        raise SensitivityInputError(f"{label}: force table does not match declared stiffness")
    owner = row.get("physical_owner", {})
    if (owner.get("role") != "physical_bolt_outer_seat_tension"
            or owner.get("axis_id") != target["axis_id"]
            or owner.get("first") != "knee_outer_left_spine"
            or owner.get("second") != "base_post_outer_left"):
        raise SensitivityInputError(f"{label}: physical owner changed")
    axis = owner.get("axis", [])
    if (len(axis) != 3 or abs(float(axis[0]) - 1.0) > 1.0e-12
            or abs(float(axis[1])) > 1.0e-12 or abs(float(axis[2])) > 1.0e-12):
        raise SensitivityInputError(f"{label}: owner axis is not the preserved global-X axis")


def _validate_pair_content(
    baseline: dict[str, Any], baseline_deck: str,
    variant: dict[str, Any], variant_deck: str,
) -> dict[str, Any]:
    """Validate an exact baseline/variant content pair; private test seam."""
    if variant.get("schema") != "current_springa_selected_floor_input_model/v1":
        raise SensitivityInputError("Variant schema changed")
    if (variant.get("candidate") != baseline.get("candidate")
            or variant.get("geometry_revision_id") != baseline.get("geometry_revision_id")
            or variant.get("case_id") != baseline.get("case_id")):
        raise SensitivityInputError("Variant changed candidate, case, or geometry revision")
    expected_paths = _expected_model_paths(baseline)
    actual_paths = set(_diff_paths(baseline, variant))
    if actual_paths != expected_paths:
        raise SensitivityInputError(
            "Variant model contains an unapproved difference: "
            f"extra={sorted(actual_paths - expected_paths)!r}; "
            f"missing={sorted(expected_paths - actual_paths)!r}"
        )

    source_rows = baseline["raw_source_carrier_law_inventory_rows"]
    for name, target in TARGETS.items():
        raw = source_rows[target["index"]]
        if (raw.get("name") != name or raw.get("group") != target["group"]
                or int(raw.get("element", -1)) != target["element"]
                or raw.get("intended_law") != "tension_only"):
            raise SensitivityInputError(f"Raw source inventory does not bind {name}")
        if abs(float(raw.get("stiffness_n_per_mm", float("nan"))) - OLD_K) > 1.0e-10:
            raise SensitivityInputError(f"Raw baseline source stiffness changed at {name}")
        binding_versions = []
        for field_name in ("nonlinear_native_carrier_bindings", "unilateral_springa_bindings"):
            before_matches = [row for row in baseline[field_name]
                              if row.get("name") == name and row.get("group") == target["group"]]
            after_matches = [row for row in variant[field_name]
                             if row.get("name") == name and row.get("group") == target["group"]]
            if len(before_matches) != 1 or len(after_matches) != 1:
                raise SensitivityInputError(f"Expected one before/after runtime binding for {name}")
            _assert_tie_record(before_matches[0], expected_k=OLD_K, target=target,
                               label=f"baseline {field_name}/{name}")
            _assert_tie_record(after_matches[0], expected_k=NEW_K, target=target,
                               label=f"variant {field_name}/{name}")
            binding_versions.append(after_matches[0])
        if binding_versions[0] != binding_versions[1]:
            raise SensitivityInputError(f"Native and recovery bindings disagree at {name}")

    base_lines, variant_lines = baseline_deck.splitlines(keepends=True), variant_deck.splitlines(keepends=True)
    if len(base_lines) != len(variant_lines):
        raise SensitivityInputError("Variant deck line count changed")
    expected_line_indices: set[int] = set()
    table_checks = []
    for name, target in TARGETS.items():
        old_table, old_indices = _spring_table(baseline_deck, target["group"])
        new_table, new_indices = _spring_table(variant_deck, target["group"])
        expected_old = [[0.0, -10.0], [0.0, 0.0], [OLD_K * 10.0, 10.0]]
        expected_new = [[0.0, -10.0], [0.0, 0.0], [NEW_K * 10.0, 10.0]]
        if old_table[:2] != expected_old[:2] or old_table[2][1] != 10.0 or abs(old_table[2][0] - expected_old[2][0]) > 1.0e-8:
            raise SensitivityInputError(f"Baseline native table is not the pinned law for {name}")
        if (new_table[:2] != expected_new[:2]
                or new_table[2][1] != expected_new[2][1]
                or abs(new_table[2][0] - expected_new[2][0]) > 1.0e-8):
            raise SensitivityInputError(f"Variant native table differs from declared override for {name}")
        if old_indices != new_indices:
            raise SensitivityInputError(f"Native table layout changed at {name}")
        expected_line_indices.add(new_indices[2])
        table_checks.append({
            "name": name, "group": target["group"],
            "line_1based": new_indices[2] + 1,
            "baseline_force_N_at_10mm": old_table[2][0],
            "variant_force_N_at_10mm": new_table[2][0],
        })
    actual_line_indices = {i for i, (a, b) in enumerate(zip(base_lines, variant_lines, strict=True)) if a != b}
    if actual_line_indices != expected_line_indices:
        raise SensitivityInputError(
            "Variant deck has unapproved changed lines: "
            f"extra={sorted(actual_line_indices - expected_line_indices)!r}; "
            f"missing={sorted(expected_line_indices - actual_line_indices)!r}"
        )
    for line_index in expected_line_indices:
        old = base_lines[line_index].strip()
        new = variant_lines[line_index].strip()
        if old.split(",")[-1].strip() != new.split(",")[-1].strip():
            raise SensitivityInputError("Native spring elongation abscissa changed")

    return {
        "expected_model_diff_paths": sorted(expected_paths),
        "observed_model_diff_paths": sorted(actual_paths),
        "model_diff_is_exact_allowlist": True,
        "changed_native_table_rows": table_checks,
        "native_deck_diff_is_exact_allowlist": True,
        "source_inventory_immutable": True,
        "all_unapproved_model_or_deck_overrides_rejected": True,
    }


@dataclass(frozen=True)
class ValidatedSensitivityContract:
    """Sealed in-memory input contract for a single exact stiffness variant."""

    schema: str
    validator_path: str
    validator_sha256: str
    baseline_model_sha256: str
    baseline_deck_sha256: str
    baseline_record_canonical_sha256: str
    baseline_deck_text_sha256: str
    variant_model_sha256: str
    variant_deck_sha256: str
    variant_record_canonical_sha256: str
    variant_deck_text_sha256: str
    audit_source_path: str
    audit_source_sha256: str
    stable_recovery_source_path: str
    stable_recovery_source_sha256: str
    precision_response_source_path: str
    precision_response_source_sha256: str
    precision_recovery_source_path: str
    precision_recovery_source_sha256: str
    response_core_fork_path: str
    response_core_fork_sha256: str
    approved_overrides: tuple[tuple[str, str, int, float, float], ...]
    source_contract_summary: dict[str, Any]
    validation_summary: dict[str, Any]
    _base_response_contract: dict[str, Any] = field(repr=False, compare=False)
    _seal: object = field(repr=False, compare=False)

    def _check_live_pins(self) -> None:
        if self._seal is not _CONTRACT_SEAL or self.schema != "conditional_joint_stiffness_sensitivity_validated_contract/v1":
            raise SensitivityInputError("A validator-produced sensitivity contract is required")
        if _sha(Path(self.validator_path)) != self.validator_sha256:
            raise SensitivityInputError("Sensitivity validator source changed after validation")
        for path, digest, label in (
            (AUDIT_SOURCE, self.audit_source_sha256, "attempt03 baseline input validator"),
            (STABLE_RECOVERY_SOURCE, self.stable_recovery_source_sha256, "attempt03 recovery source"),
            (PRECISION_RESPONSE_SOURCE, self.precision_response_source_sha256, "711 response wrapper"),
            (PRECISION_RECOVERY_SOURCE, self.precision_recovery_source_sha256, "711 precision recovery source"),
            (RESPONSE_CORE_FORK, self.response_core_fork_sha256, "sensitivity response-core fork"),
            (SOURCE_LOAD_REGISTER, SOURCE_LOAD_REGISTER_SHA256, "six-case source-load register"),
        ):
            _require_hash(path, digest, label)

    def _decorate_response_contract(
        self, contract: dict[str, Any], record: dict[str, Any], *,
        selected_model_sha256: str, selected_deck_sha256: str,
        override_authority: dict[str, Any] | None,
    ) -> dict[str, Any]:
        register = json.loads(SOURCE_LOAD_REGISTER.read_text())
        matches = [row for row in register.get("cases", []) if row.get("case_id") == record.get("case_id")]
        if len(matches) != 1:
            raise SensitivityInputError("A12-rear is not unique in the pinned source-load register")
        case_row_sha256 = _canonical_sha(matches[0])
        selected_cells = contract.get("selected_cells", set())
        inactive_cells = contract.get("inactive_cells", set())
        active_rows = len(record.get("floor_reference_nodes_and_load_map", []))
        contract["case_id"] = str(record["case_id"])
        contract["case_record_sha256"] = case_row_sha256
        contract["selected_cell_count"] = len(selected_cells)
        contract["inactive_cell_count"] = len(inactive_cells)
        contract["active_tangent_row_count"] = active_rows
        contract["inactive_tangent_row_count"] = 200 - active_rows
        contract["sensitivity_input_contract_provenance"] = {
            "schema": "conditional_joint_stiffness_sensitivity_validated_contract/v1",
            "contract_mode": "approved_sensitivity_variant" if override_authority is not None else "baseline_replay",
            "case_id": str(record["case_id"]),
            "candidate": record["candidate"],
            "geometry_revision_id": record["geometry_revision_id"],
            "case_record_sha256": case_row_sha256,
            "source_case_load_register_path": str(SOURCE_LOAD_REGISTER.relative_to(ROOT)),
            "source_case_load_register_sha256": SOURCE_LOAD_REGISTER_SHA256,
            "baseline_model_json_sha256": self.baseline_model_sha256,
            "baseline_deck_sha256": self.baseline_deck_sha256,
            "selected_input_model_json_sha256": selected_model_sha256,
            "selected_input_deck_sha256": selected_deck_sha256,
            "selected_floor_branch_id": "monotone_zero_gap_first_bearing_reference_zero",
            "screen_sha256": contract["screen_sha256"],
            "attempt03_baseline_input_validator_sha256": self.audit_source_sha256,
            "711_precision_response_source_sha256": self.precision_response_source_sha256,
            "711_precision_recovery_source_sha256": self.precision_recovery_source_sha256,
            "sensitivity_response_core_fork_sha256": self.response_core_fork_sha256,
            "standard_711_case_context_validation_passed": False,
            "case_context_limit": "This A12-rear legacy selected-floor screen does not pin the exact all-bearing control model/deck required by the standard 711 case-context validator; no synthetic case context is asserted.",
        }
        if override_authority is not None:
            contract["sensitivity_override_authority"] = override_authority
        return contract

    def build_baseline_response_core_contract(
        self, record: dict[str, Any], deck: str,
        *, model_path: Path, deck_path: Path,
    ) -> dict[str, Any]:
        """Return the exact baseline contract for a byte-pinned baseline replay."""
        self._check_live_pins()
        if _canonical_sha(record) != self.baseline_record_canonical_sha256:
            raise SensitivityInputError("Response record is not the pinned baseline model")
        if _sha_bytes(deck.encode("utf-8")) != self.baseline_deck_text_sha256:
            raise SensitivityInputError("Response deck text is not the pinned baseline deck")
        if _sha(model_path) != self.baseline_model_sha256 or _sha(deck_path) != self.baseline_deck_sha256:
            raise SensitivityInputError("Response files are not the exact pinned baseline model/deck")
        contract = copy.deepcopy(self._base_response_contract)
        return self._decorate_response_contract(
            contract, record, selected_model_sha256=self.baseline_model_sha256,
            selected_deck_sha256=self.baseline_deck_sha256, override_authority=None,
        )

    def build_response_core_contract(
        self, record: dict[str, Any], deck: str,
        *, model_path: Path, deck_path: Path,
    ) -> dict[str, Any]:
        """Build the existing auditor-shaped contract for a source-forked core.

        The separate 711-derived response-core fork calls this only after checking
        its own pinned source. The frozen auditors remain unchanged and continue
        to reject the stiffness override through their exact-preservation checks.
        """
        self._check_live_pins()
        if _canonical_sha(record) != self.variant_record_canonical_sha256:
            raise SensitivityInputError("Response record is not the validated variant model")
        deck_sha = _sha_bytes(deck.encode("utf-8"))
        if deck_sha != self.variant_deck_text_sha256:
            raise SensitivityInputError("Response deck text is not the validated variant deck")
        if _sha(model_path) != self.variant_model_sha256:
            raise SensitivityInputError("Response model file is not the exact validated variant model")
        if _sha(deck_path) != self.variant_deck_sha256:
            raise SensitivityInputError("Response deck file is not the exact validated variant deck")
        contract = copy.deepcopy(self._base_response_contract)
        contract["bindings"] = copy.deepcopy(record["unilateral_springa_bindings"])
        authority = {
            "validator_sha256": self.validator_sha256,
            "variant_model_sha256": self.variant_model_sha256,
            "variant_deck_sha256": self.variant_deck_sha256,
            "precision_response_source_sha256": self.precision_response_source_sha256,
            "precision_recovery_source_sha256": self.precision_recovery_source_sha256,
            "response_core_fork_sha256": self.response_core_fork_sha256,
            "approved_overrides": [
                {"name": name, "group": group, "source_inventory_row_index": index,
                 "baseline_stiffness_n_per_mm": old_k, "variant_stiffness_n_per_mm": new_k}
                for name, group, index, old_k, new_k in self.approved_overrides
            ],
        }
        return self._decorate_response_contract(
            contract, record, selected_model_sha256=self.variant_model_sha256,
            selected_deck_sha256=self.variant_deck_sha256, override_authority=authority,
        )


def validate_prepared_variant() -> ValidatedSensitivityContract:
    """Validate pinned baseline and variant inputs and return the sealed contract."""
    baseline_model_path = BASELINE_PACKET / "model.json"
    baseline_deck_path = BASELINE_PACKET / "model.inp"
    baseline_response_path = BASELINE_PACKET / "response.json"
    variant_model_path = VARIANT_PACKET / "model.json"
    variant_deck_path = VARIANT_PACKET / "model.inp"
    variant_manifest_path = VARIANT_PACKET / "variant.json"

    for path, digest, label in (
        (baseline_model_path, BASELINE_MODEL_SHA256, "baseline A12-rear model"),
        (baseline_deck_path, BASELINE_DECK_SHA256, "baseline A12-rear deck"),
        (baseline_response_path, BASELINE_RESPONSE_SHA256, "baseline A12-rear response provenance"),
        (variant_model_path, VARIANT_MODEL_SHA256, "sensitivity variant model"),
        (variant_deck_path, VARIANT_DECK_SHA256, "sensitivity variant deck"),
        (variant_manifest_path, VARIANT_MANIFEST_SHA256, "sensitivity variant manifest"),
        (VARIANT_PACKET / "prepare.py", PREPARER_SHA256, "sensitivity variant preparer"),
        (SERIES / "current-post-spine-compliance-sensitivity-attempt01/sensitivity.json",
         SENSITIVITY_SOURCE_SHA256, "local compliance sensitivity source"),
        (ROOT / "fea/wood_joint_reduced_properties.py", PROPERTY_SOURCE_SHA256,
         "effective stiffness property source"),
        (SOURCE_LOAD_REGISTER, SOURCE_LOAD_REGISTER_SHA256,
         "six-case source-load register"),
        (PRECISION_RESPONSE_SOURCE, PRECISION_RESPONSE_SHA256,
         "pinned 711 zero-U response wrapper"),
        (PRECISION_RECOVERY_SOURCE, PRECISION_RECOVERY_SHA256,
         "pinned 711 zero-U recovery kernel"),
        (RESPONSE_CORE_FORK, RESPONSE_CORE_FORK_SHA256,
         "separate sensitivity response-core fork"),
    ):
        _require_hash(path, digest, label)

    baseline = json.loads(baseline_model_path.read_text())
    variant = json.loads(variant_model_path.read_text())
    baseline_deck = baseline_deck_path.read_text()
    variant_deck = variant_deck_path.read_text()
    manifest = json.loads(variant_manifest_path.read_text())
    if manifest.get("schema") != "conditional_frame_joint_stiffness_sensitivity_input/v1":
        raise SensitivityInputError("Variant manifest schema changed")
    if (manifest.get("status") != "PREPARED_INPUT_ONLY_NO_NATIVE_READINESS"
            or manifest.get("native_solve_executed") is not False
            or manifest.get("mechanical_acceptance") is not False
            or manifest.get("qualified_for_design") is not False):
        raise SensitivityInputError("Variant manifest overclaims readiness or acceptance")
    if manifest.get("prepared_outputs", {}).get("model_json_sha256") != VARIANT_MODEL_SHA256 or manifest.get("prepared_outputs", {}).get("model_inp_sha256") != VARIANT_DECK_SHA256:
        raise SensitivityInputError("Variant manifest does not bind exact prepared model/deck hashes")
    if manifest.get("source_sensitivity", {}).get("sensitivity_json_sha256") != SENSITIVITY_SOURCE_SHA256:
        raise SensitivityInputError("Variant does not bind its source sensitivity result")

    auditor = _load_auditor()
    precision_auditor = _load_precision_auditor()
    if (getattr(precision_auditor, "STABLE_AUDIT_SHA256", None)
            != PRECISION_RECOVERY_SHA256):
        raise SensitivityInputError("The pinned 711 response wrapper does not name the required precision kernel")
    baseline_contract = auditor._validate_model(baseline, baseline_deck)
    pair_check = _validate_pair_content(baseline, baseline_deck, variant, variant_deck)

    # Ensure the parent-selected frame conditions remain explicit and unchanged.
    for field_name in (
        "raw_source_carrier_law_inventory_rows", "source_carrier_inventory_rows",
        "source_inventory_audit", "connection_ownership", "physical_body_nodes",
        "physical_body_elements", "body_geometry", "physical_body_loads",
        "physical_external_loads", "loads", "nodes", "elements", "equations",
        "fixed_nodes", "floor_branch_metadata", "floor_selected_mask_by_original_row",
        "floor_constraint_audit", "floor_reference_nodes_and_load_map", "springs",
        "source_load_normalization_audit", "source_load_emission_audit",
        "material_binding", "material_deck_audit", "connection_scenario",
    ):
        if baseline.get(field_name) != variant.get(field_name):
            raise SensitivityInputError(f"Variant changed protected context field {field_name}")

    override_list = tuple(
        (name, target["group"], target["index"], OLD_K, NEW_K)
        for name, target in TARGETS.items()
    )
    summary = {
        "inventory_summary": baseline_contract["inventory_summary"],
        "baseline_floor_screen_sha256": baseline_contract["screen_sha256"],
        "baseline_source_constraint_reconstruction_residual": baseline_contract["source_constraint_reconstruction_residual"],
        "baseline_source_reference_transform_residual": baseline_contract["source_reference_transform_residual"],
        "baseline_source_pivot_identity_residual": baseline_contract["source_pivot_identity_residual"],
        "baseline_source_point_wrench_force_error_N": baseline_contract["source_point_wrench_force_error_N"],
        "baseline_source_point_wrench_moment_error_Nmm": baseline_contract["source_point_wrench_moment_error_Nmm"],
        "baseline_floor_load_correction_max_abs_error_N": baseline_contract["floor_load_correction_max_abs_error_N"],
        "exact_variant_pair_check": pair_check,
    }
    return ValidatedSensitivityContract(
        schema="conditional_joint_stiffness_sensitivity_validated_contract/v1",
        validator_path=str(Path(__file__).resolve()),
        validator_sha256=_sha(Path(__file__).resolve()),
        baseline_model_sha256=BASELINE_MODEL_SHA256,
        baseline_deck_sha256=BASELINE_DECK_SHA256,
        variant_model_sha256=VARIANT_MODEL_SHA256,
        variant_deck_sha256=VARIANT_DECK_SHA256,
        variant_record_canonical_sha256=_canonical_sha(variant),
        variant_deck_text_sha256=_sha_bytes(variant_deck.encode("utf-8")),
        audit_source_path=str(AUDIT_SOURCE.relative_to(ROOT)),
        audit_source_sha256=AUDIT_SOURCE_SHA256,
        stable_recovery_source_path=str(STABLE_RECOVERY_SOURCE.relative_to(ROOT)),
        stable_recovery_source_sha256=STABLE_RECOVERY_SHA256,
        precision_response_source_path=str(PRECISION_RESPONSE_SOURCE.relative_to(ROOT)),
        precision_response_source_sha256=PRECISION_RESPONSE_SHA256,
        precision_recovery_source_path=str(PRECISION_RECOVERY_SOURCE.relative_to(ROOT)),
        precision_recovery_source_sha256=PRECISION_RECOVERY_SHA256,
        response_core_fork_path=str(RESPONSE_CORE_FORK.relative_to(ROOT)),
        response_core_fork_sha256=RESPONSE_CORE_FORK_SHA256,
        baseline_record_canonical_sha256=_canonical_sha(baseline),
        baseline_deck_text_sha256=_sha_bytes(baseline_deck.encode("utf-8")),
        approved_overrides=override_list,
        source_contract_summary=copy.deepcopy(summary),
        validation_summary=copy.deepcopy(pair_check),
        _base_response_contract=copy.deepcopy(baseline_contract),
        _seal=_CONTRACT_SEAL,
    )


def validate_contract_for_paths(model_path: Path, deck_path: Path) -> ValidatedSensitivityContract:
    """Validate the exact active variant files; paths are not caller-overridable."""
    if model_path.resolve() != (VARIANT_PACKET / "model.json").resolve():
        raise SensitivityInputError("Only the pinned sensitivity variant model path is accepted")
    if deck_path.resolve() != (VARIANT_PACKET / "model.inp").resolve():
        raise SensitivityInputError("Only the pinned sensitivity variant deck path is accepted")
    contract = validate_prepared_variant()
    if _sha(model_path) != contract.variant_model_sha256 or _sha(deck_path) != contract.variant_deck_sha256:
        raise SensitivityInputError("Active model/deck file hashes differ from the validated contract")
    return contract
