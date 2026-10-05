"""Publish and authenticate a desktop decision review, without mechanics runs.

The legacy numerical extension remains open. A reviewed unresolved decision is
allowed here; an unreviewed duty, invented signed load, or strength claim is not.
Authentication and receipt output ownership reuse the numerical checker API.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.machinery
import importlib.util
import json
import math
import re
from collections import Counter
from pathlib import Path

SELECTION_SHA = "6f2e8238c9d49a569b62b91e9802f2fd191a0bb9e48366804894040d5607043b"
CHECKER_SHA = "97d88a85ab590907e6080f94c016819bdd1ba560a54453fbd4ce81c8af8e50cf"
SCHEMA = "reduced_desktop_decision_assessment/v1"
STATUS = "COMPLETE_REDUCED_DESKTOP_DECISION_REVIEW"
CLAIM = "conditional_desktop_layout_decisions_not_strength_qualification"
SHARD_SCHEMAS = {"reduced_desktop_joint_shard/v1", "reduced_desktop_retained_joint_dispositions/v1",
                 "reduced_desktop_assessment_outer_shard/v1", "reduced_desktop_joint_assessment_shard/v1",
                 "reduced-desktop-joint-assessment-shard/v1"}
FALSE_FLAGS = {
    "complete_joint_acceptance", "physical_release", "structural_acceptance",
    "fabrication_release", "actual_inspection_claimed",
    "capacity_from_average_or_nominal_stress", "original_inventory_completed",
    "legacy_numerical_extension_completed",
}
SIGNED_FIELD = re.compile(r"signed|full_signed_wrench|(?:^|/)(?:force_n|free_moment_nmm|lateral_components_n)$")
SOURCE_INPUT_NAMES = {"material-inputs.json", "model-inputs.json", "geometry.json", "geometry-bindings.json"}


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def pointer(value, address):
    require(isinstance(address, str) and (address == "" or address.startswith("/")),
            "invalid desktop record pointer")
    if not address:
        return value
    for token in address[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            require(re.fullmatch(r"0|[1-9][0-9]*", token), "invalid desktop array index")
            value = value[int(token)]
        else:
            require(isinstance(value, dict) and token in value, "desktop pointer does not exist")
            value = value[token]
    return value


def references(value):
    """Yield literal file references; strings inside a source pin map are pins."""
    if isinstance(value, dict):
        if "path" in value and "sha256" in value:
            yield value
        for key, item in value.items():
            if key not in {"source_sha256", "copied_values"}:
                yield from references(item)
    elif isinstance(value, list):
        for item in value:
            yield from references(item)


def source_records(value):
    if isinstance(value, dict):
        if isinstance(value.get("source_record"), dict):
            yield value["source_record"]
        for key, item in value.items():
            if key not in {"source_sha256", "copied_values"}:
                yield from source_records(item)
    elif isinstance(value, list):
        for item in value:
            yield from source_records(item)


def decision_claims(value):
    forbidden = FALSE_FLAGS | {"physical_or_strength_acceptance", "strength_pass", "joint_capacity_claim",
        "receiver_strength_or_fracture_acceptance", "complete_receiver_resistance_qualified",
        "local_splitting_capacity_from_nominal_cut_or_section_pass", "proposal108_geometry_adopted",
        "proposal_108_adopted", "mirrored_force_or_geometry_acceptance_transferred",
        "reference_exceeds_are_physical_failure", "baseline_300_certificate_transferred"}
    if isinstance(value, dict):
        for key, item in value.items():
            if key in forbidden:
                require(item is False, "desktop decision asserts strength/release or historical transfer")
            if key not in {"source_sha256", "copied_values"}:
                decision_claims(item)
    elif isinstance(value, list):
        for item in value:
            decision_claims(item)


def numeric(value):
    return (type(value) in (int, float) and math.isfinite(value)
            or isinstance(value, list) and bool(value) and all(numeric(item) for item in value))


class Evidence:
    """Authenticate each consumed owner in its own snapshot namespace."""

    def __init__(self, root, api, maintained, cache):
        self.root, self.api, self.maintained, self.cache = root, api, maintained, cache
        self.pins, self.owners, self.current_outputs, self.candidates = {}, {}, set(), {}
        self.json_records = {}
        self.consulted = {}
        self.body_action_binding = None

    def pin(self, path, digest):
        name = str(path) if not path.is_relative_to(self.root) else path.relative_to(self.root).as_posix()
        require(name not in self.pins or self.pins[name] == digest, "conflicting resolved desktop source")
        self.pins[name] = digest

    def file(self, ref):
        require(isinstance(ref, dict), "desktop artifact reference required")
        path = self.api.authenticate(self.root, ref.get("path"), ref.get("sha256"), {}, self.cache)
        self.pin(path, ref["sha256"])
        return path

    def owner(self, ref, *, current=False):
        path = self.file(ref)
        if path in self.owners:
            require(self.owners[path][0] == ref["sha256"], "conflicting desktop receipt digest")
            outputs = self.owners[path][1]
        else:
            receipt = self.api.read_json(path)
            sources, raw_outputs = receipt.get("source_sha256"), receipt.get("output_sha256")
            require(isinstance(sources, dict) and sources and isinstance(raw_outputs, dict) and raw_outputs,
                    "desktop evidence owner lacks source/output bindings")
            redirects = self.api.projected_receipt_resolutions(self.root, receipt, self.maintained)
            for name, digest in sources.items():
                resolved = self.api.authenticate(self.root, name, digest, redirects, self.cache)
                self.pin(resolved, digest)
                if name.endswith(".json") and "receipt" in Path(name).name.lower():
                    self.candidates[resolved] = {"path": self.name(resolved), "sha256": digest}
            for field in ("source_before_sha256", "source_after_sha256"):
                if field in receipt:
                    require(receipt[field] == sources, "desktop evidence owner source-set changed")
            outputs = {}
            for name, digest in raw_outputs.items():
                target = self.api.output_path(self.root, path.parent, name)
                self.api.authenticate(self.root, self.name(target), digest, {}, self.cache)
                self.pin(target, digest)
                outputs[target] = digest
            self.owners[path] = ref["sha256"], outputs
        if current:
            self.current_outputs.update(outputs.items())
        return outputs

    def name(self, path):
        return str(path) if not path.is_relative_to(self.root) else path.relative_to(self.root).as_posix()

    def output(self, ref, *, current=False):
        path = self.file(ref)
        identity = path, ref["sha256"]
        if current:
            require(identity in self.current_outputs, "signed desktop witness lacks a current output owner")
        elif not any(outputs.get(path) == ref["sha256"] for _, outputs in self.owners.values()):
            # Only receipts already source-bound by consulted evidence can add
            # supporting output authority. They never become current witnesses.
            for candidate in list(self.candidates.values()):
                owner_path = self.file(candidate)
                metadata = self.api.read_json(owner_path)
                advertised = metadata.get("output_sha256", {})
                if any(self.api.output_path(self.root, owner_path.parent, name) == path and digest == ref["sha256"]
                       for name, digest in advertised.items()):
                    self.owner(candidate)
                    break
            require(any(outputs.get(path) == ref["sha256"] for _, outputs in self.owners.values()),
                    "desktop referenced record lacks its source-bound output owner")
        return path

    def record(self, ref, *, current=False, owned=True):
        path = self.output(ref, current=current) if owned else self.file(ref)
        address = ref.get("pointer", "")
        if path.name.endswith((".jsonl", ".jsonl.gz")):
            require(isinstance(address, str) and address.startswith("/"), "JSONL line pointer required")
            line_token, _, suffix = address[1:].partition("/")
            require(re.fullmatch(r"0|[1-9][0-9]*", line_token), "invalid JSONL line pointer")
            number = int(line_token)
            require(all(key not in ref or type(ref[key]) is int and ref[key] == number
                        for key in ("jsonl_line_zero_based", "line_index")), "JSONL line and pointer disagree")
            key = path, number
            if key not in self.json_records:
                opener = gzip.open if path.name.endswith(".gz") else open
                with opener(path, "rt", encoding="utf-8") as stream:
                    for index, line in enumerate(stream):
                        if index == number:
                            self.json_records[key] = json.loads(line)
                            break
                require(key in self.json_records, "JSONL desktop line missing")
            value = self.json_records[key]
            value = pointer(value, "/" + suffix if suffix else "")
        else:
            require("jsonl_line_zero_based" not in ref, "JSONL line metadata on JSON source")
            if path not in self.json_records:
                self.json_records[path] = json.loads(path.read_text(encoding="utf-8"))
            value = pointer(self.json_records[path], address)
        return value

    def prime_lines(self, rows):
        """Read each referenced JSONL once, retaining only requested records."""
        wanted = {}
        for ref in references(rows):
            path = self.api.file_path(self.root, ref["path"], absolute=True)
            if not path.name.endswith((".jsonl", ".jsonl.gz")) or "pointer" not in ref:
                continue
            number = ref["pointer"].split("/")[1]
            require(re.fullmatch(r"0|[1-9][0-9]*", number), "invalid JSONL line pointer")
            if (path, int(number)) not in self.json_records:
                wanted.setdefault(path, set()).add(int(number))
            self.file(ref)
        for path, numbers in wanted.items():
            opener = gzip.open if path.name.endswith(".gz") else open
            with opener(path, "rt", encoding="utf-8") as stream:
                for index, line in enumerate(stream):
                    if index in numbers:
                        self.json_records[path, index] = json.loads(line)
                        numbers.remove(index)
                    if not numbers:
                        break
            require(not numbers, "referenced JSONL desktop line missing")

    def context_resolutions(self, refs):
        require(isinstance(refs, list), "desktop consulted resolution ledger list required")
        for ref in refs:
            ledger = self.api.read_json(self.file(ref))
            require(ledger.get("schema") == "reduced_consulted_context_resolution/v1"
                    and ledger.get("live_context_restored_or_changed") is False
                    and ledger.get("original_artifact_changed") is False, "invalid desktop consulted resolution ledger")
            artifact = ledger["artifact"]
            source = self.api.read_json(self.file(artifact)).get("source_sha256", {})
            redirects = ledger.get("source_resolution")
            require(isinstance(redirects, dict) and redirects and set(redirects) <= set(source),
                    "consulted redirects are outside their exact artifact")
            for name, redirect in redirects.items():
                require(redirect.get("sha256") == source[name], "consulted redirect changed its artifact source hash")
                resolved = self.api.authenticate(self.root, name, source[name], redirects, self.cache)
                self.pin(resolved, source[name])
            key = artifact["path"], artifact["sha256"]
            require(key not in self.consulted, "duplicate consulted source authority")
            self.consulted[key] = redirects

    def sources(self, document, artifact=None):
        sources = document.get("source_sha256")
        require(isinstance(sources, dict) and sources, "desktop shard lacks consulted source hashes")
        scoped = self.consulted.get((artifact["path"], artifact["sha256"]), {}) if artifact else {}
        redirects = self.api.projected_receipt_resolutions(self.root, document, {**self.maintained, **scoped})
        for name, digest in sources.items():
            resolved = self.api.authenticate(self.root, name, digest, redirects, self.cache)
            self.pin(resolved, digest)
            if name.endswith(".json") and "receipt" in Path(name).name.lower():
                self.candidates[resolved] = {"path": self.name(resolved), "sha256": digest}


def current_basis(selection, evidence):
    selected = selection.get("selected_results", {})
    basis = selection.get("selected_coupled_force_basis", {})
    names = {basis.get("frame_result"), basis.get("action_result"), *basis.get("consumer_results", [])}
    require(len(selected) == len(names) == 10 and len(basis.get("consumer_results", [])) == 8,
            "desktop current frame/action/eight-consumer selection incomplete")
    entries = {}
    for key, item in selected.items():
        outputs = evidence.owner(item["receipt"], current=True)
        result_path = evidence.file(item["result"])
        require(outputs.get(result_path) == item["result"]["sha256"], "desktop selected result lacks its owner")
        entries[key] = {"result": item["result"]["path"], "result_sha256": item["result"]["sha256"],
                        "receipt": item["receipt"]["path"], "receipt_sha256": item["receipt"]["sha256"],
                        "status": evidence.api.FINITE_DISPOSITION}
        if key == "nominal_transverse_components_wide_top_rail_profile":
            # The independent nominal audit owns its report; its source-bound
            # actual nominal producer owns the literal signed JSON records.
            expected = evidence.api.read_json(result_path).get("fresh_nominal_receipt_sha256")
            candidates = [ref for ref in evidence.candidates.values() if ref["sha256"] == expected]
            require(len(candidates) == 1, "desktop raw nominal output owner missing or ambiguous")
            evidence.owner(candidates[0], current=True)
    evidence.api.coupled_basis_check(evidence.root, {"status": "in_progress", "selected_coupled_force_basis": basis},
                                    entries, {"current": list(entries)})
    evidence.output(selection["action_body_records"], current=True)
    evidence.body_action_binding = selection["action_body_records"]
    frame = evidence.api.read_json(evidence.file(selected[basis["frame_result"]]["result"]))
    require(selection.get("baseline_state_dispositions") == frame.get("case_dispositions"),
            "desktop baseline dispositions differ from current frame")
    states = selection.get("accepted_states")
    require(isinstance(states, list) and len(states) == len(frame.get("states", [])) == 12,
            "desktop accepted source inventory incomplete")
    for item in states:
        source = evidence.record(item["source_state_record"], current=True)
        require(evidence.api.state_tag(evidence.api.state_key(source)) == item.get("state_tag")
                and source.get("case_id") == item.get("case_id") and source.get("gap_scale") == item.get("gap_scale"),
                "desktop accepted state pointer identifies another state")
        evidence.api.accepted_audit(source)


def witness_check(witness, accepted, evidence, duty=None):
    require(isinstance(witness, dict), "desktop signed witness object required")
    tag = witness.get("state_tag")
    require(tag in accepted and witness.get("source_state_record") == accepted[tag]["source_state_record"],
            "desktop signed witness uses a stale or unavailable state")
    source = evidence.record(witness.get("source_record"), current=True)
    require(isinstance(source, dict), "desktop signed source pointer must select one record")
    context = source
    ref = witness["source_record"]
    binding = evidence.body_action_binding
    nested = re.fullmatch(r"/(0|[1-9][0-9]*)/actions/(0|[1-9][0-9]*)", ref.get("pointer", ""))
    if binding and {"path": ref["path"], "sha256": ref["sha256"]} == binding and nested:
        # An action owns its literal values; its enclosing authenticated body
        # row owns state/body identity. No identity is inferred from line order.
        context = evidence.record({**ref, "pointer": "/" + nested[1]}, current=True)
        require(isinstance(context, dict) and source == pointer(context, "/actions/" + nested[2]),
                "desktop action is not part of its enclosing current body row")
    for record in (context,) if context is source else (context, source):
        identifiers = [record[key] for key in ("state_tag", "state_id") if key in record]
        if "join_key" in record:
            require(isinstance(record["join_key"], list) and len(record["join_key"]) >= 2, "invalid source join key")
            identifiers.append(record["join_key"][1])
        if record.get("case_id") == tag:
            identifiers.append(record["case_id"])
        require((identifiers or record is not context) and all(item == tag for item in identifiers),
                "mixed-state desktop signed witness")
        if "case_id" in record:
            require(record["case_id"] in {tag, accepted[tag]["case_id"]}, "desktop source case differs")
        if "gap_scale" in record:
            require(record["gap_scale"] == accepted[tag]["gap_scale"], "desktop source gap differs")
        if "source_state_record" in record:
            require(record["source_state_record"] == witness["source_state_record"], "source state binding differs")
    require(source.get("source_force_available", True) is True
            and source.get("replaced_source_row_placeholder", False) is False,
            "unavailable source force placeholder is not a signed current witness")
    if duty is not None:
        axis = source.get("axis_id", source.get("join_key", [None, None, None])[2])
        body = context.get("body", source.get("receiver"))
        require(axis in duty["physical_axis_ids"] or body in duty["timber_sides"],
                "desktop signed witness belongs to another duty/receiver")
    copied = witness.get("copied_values")
    require(isinstance(copied, dict) and copied, "literal signed source values missing")
    signed = False
    for address, value in copied.items():
        require(canonical(pointer(source, address)) == canonical(value), "desktop copied signed value differs from source")
        signed |= bool(SIGNED_FIELD.search(address)) and numeric(value)
    require(signed, "desktop witness contains no literal signed demand")


def row_inventory(selection, rows, evidence):
    require(isinstance(rows, list) and len(rows) == 30, "desktop review must contain all30 duties")
    duties = {row["joint_id"]: row for row in selection["duties"]}
    families = {family["id"]: set(family["duty_ids"]) for family in selection["families"]}
    require(len(duties) == selection.get("duty_count") == 30 and len(families) == selection.get("family_count") == 8,
            "desktop selected duty/family partition changed")
    accepted = {item["state_tag"]: item for item in selection["accepted_states"]}
    seen, receiver_duties, decisions = set(), {}, Counter()
    for row in rows:
        require(isinstance(row, dict), "desktop duty row required")
        joint = row.get("joint_id")
        require(joint in duties and joint not in seen, "missing/duplicate/unknown desktop duty")
        seen.add(joint)
        duty = duties[joint]
        require(row.get("family_id") == duty["family_id"], "desktop family identity differs: " + joint)
        for key in ("timber_sides", "physical_axis_ids"):
            actual = row.get(key)
            require(isinstance(actual, list) and len(actual) == len(set(actual)) == len(duty[key])
                    and set(actual) == set(duty[key]), "desktop geometry/duty identity differs: " + joint + "/" + key)
        require(joint in families.get(row["family_id"], set()), "desktop family allocation differs")
        disposition = row.get("disposition", {})
        require(isinstance(disposition, dict) and disposition.get("decision") in {"retain", "revise", "unresolved"}
                and isinstance(disposition.get("reason"), str) and disposition["reason"].strip(),
                "desktop decision or reason missing")
        decisions[disposition["decision"]] += 1
        require(row.get("physical_or_strength_acceptance") is False
                and all(row.get(flag, False) is False for flag in FALSE_FLAGS), "desktop layout decision asserts strength/release")
        decision_claims(row)
        for key in ("joint_load_path", "governing_demands", "geometry_detail", "reference_findings", "next_action"):
            require(bool(row.get(key)), "desktop decision context missing: " + key)
        require(isinstance(row.get("unresolved_inputs"), list), "desktop unresolved input list missing")
        require(disposition["decision"] != "unresolved" or row["unresolved_inputs"], "unresolved desktop decision has no exact missing input")
        require(row.get("diagnostic_proposal") is None, "unselected desktop diagnostic proposal cannot execute")
        findings = row.get("receiver_findings")
        require(isinstance(findings, list) and all(isinstance(item, dict) and item.get("timber") for item in findings)
                and len(findings) == len(duty["timber_sides"])
                and {item["timber"] for item in findings} == set(duty["timber_sides"]),
                "desktop duty lacks its exact receiver contexts")
        for item in findings:
            receiver_duties.setdefault(item["timber"], []).append(joint)
        witnesses = row.get("signed_current_witnesses")
        require(isinstance(witnesses, list) and witnesses, "desktop duty has no signed current-source witness")
        for witness in witnesses:
            witness_check(witness, accepted, evidence, duty)
        for finding in findings:
            for witness in finding.get("signed_current_witnesses", []):
                witness_check(witness, accepted, evidence, duty)
        evidence.sources(row)
        for ref in references(row):
            evidence.file(ref)
            if "pointer" in ref and ref not in [w["source_state_record"] for w in witnesses]:
                evidence.record(ref, owned=False)
        for ref in source_records(row):
            if Path(ref["path"]).name in SOURCE_INPUT_NAMES:
                require(row["source_sha256"].get(ref["path"]) == ref["sha256"],
                        "desktop immutable input record absent from consulted source hashes")
                evidence.record(ref, owned=False)
            else:
                evidence.record(ref)
    require(set(receiver_duties) == set(selection["canonical_timber_names"])
            and len(receiver_duties) == selection.get("timber_count") == 44, "desktop44 timber receiver coverage incomplete")
    return [{"timber": name, "duty_ids": sorted(ids)} for name, ids in sorted(receiver_duties.items())], dict(decisions)


def shard_check(shard, selection_ref):
    require(shard.get("schema") in SHARD_SCHEMAS, "unsupported desktop shard schema")
    bindings = [shard[key] for key in ("selection_binding", "common_selection", "selection") if key in shard]
    require(bindings and all(item == selection_ref for item in bindings), "desktop shard selection differs")


def parent_validation(selection, reference, evidence):
    audit = evidence.api.read_json(evidence.file(reference))
    require(audit.get("schema") == "reduced_parent_saved_arithmetic_audit/v1"
            and audit.get("status") == "PASS_SAVED_ARITHMETIC_AND_SOURCE_JOINS"
            and audit.get("selection") == selection and audit.get("current_states") == 12
            and audit.get("new_native_solves") == 0 and audit.get("physical_release") is False
            and audit.get("complete_joint_acceptance") is False, "desktop parent arithmetic validation differs")
    evidence.sources(audit)
    selected = evidence.api.read_json(evidence.file(selection))["selected_results"]
    require(all(audit["source_sha256"].get(ref["path"]) == ref["sha256"]
                for item in selected.values() for ref in item.values()), "parent audit uses another current source basis")
    plate, cuts, knees = audit.get("plate", {}), audit.get("member_cuts", {}), audit.get("continuous_knee_transfer", {})
    require(plate.get("finite") == 2400 and plate.get("null") == 96 and plate.get("wide_fields") == 96
            and plate.get("Fy250_exceeds") == 18 and plate.get("wide_exceeds") == 4
            and math.isclose(plate.get("wide_maximum_index", math.nan), 1.222753450664422, rel_tol=1e-12)
            and cuts.get("finite") == 49344 and cuts.get("analytic_endpoints") == 240
            and cuts.get("normal_CD1_0_exceeds") == 200 and cuts.get("shear_CD1_0_exceeds") == 414
            and knees.get("axis_states") == 48 and 0 <= knees.get("maximum_force_residual_n", math.inf) < 1e-9
            and 0 <= knees.get("maximum_origin_moment_residual_nmm", math.inf) < 1e-7,
            "parent current arithmetic census/limits differ")


def receipt_covers(evidence, reference):
    """Every consumed byte must occur in this aggregate's declared closure."""
    path = evidence.file(reference)
    receipt = evidence.api.read_json(path)
    redirects = evidence.api.projected_receipt_resolutions(evidence.root, receipt, evidence.maintained)
    declared = {}
    for name, digest in receipt["source_sha256"].items():
        resolved = evidence.api.authenticate(evidence.root, name, digest, redirects, evidence.cache)
        declared[evidence.name(resolved)] = digest
    exempt = {evidence.name(path), *(evidence.name(evidence.api.output_path(evidence.root, path.parent, name))
                                    for name in receipt["output_sha256"])}
    require(all(name in exempt or declared.get(name) == digest for name, digest in evidence.pins.items()),
            "desktop aggregate receipt omits consumed source/output evidence")


def assessment_check(selection, result, evidence):
    require(selection.get("schema") == "reduced_desktop_selection/v1" and selection.get("owner_adopted") is True,
            "desktop selection is not adopted")
    require(selection.get("reviewed_geometry") == {"block_bodies": 24, "bolt_axes": 104, "geometry_changed": False,
            "hillman_axes": 66, "proposal_108_adopted": False, "timber_bodies": 44}, "104-axis desktop geometry changed or108 transferred")
    require(result.get("schema") == SCHEMA and result.get("status") == STATUS and result.get("claim") == CLAIM,
            "desktop endpoint falsely claims numerical/strength completion")
    require(all(result.get(flag) is False for flag in FALSE_FLAGS), "desktop acceptance or historical completion inferred")
    require(result.get("selected_results") == selection["selected_results"]
            and result.get("selected_coupled_force_basis") == selection["selected_coupled_force_basis"], "desktop current force basis differs")
    require(result.get("preserved_studies") == selection["preserved_studies"]
            and result.get("reviewed_geometry") == selection["reviewed_geometry"]
            and result.get("release_flags") == selection["release_flags"]
            and all(value is False for value in result["release_flags"].values()), "desktop preserved scope/release flags differ")
    budget = selection.get("diagnostic_budget")
    require(budget == {"default_new_native_solves": 0, "maximum_diagnostics": 2,
        "maximum_native_minutes_per_diagnostic": 30, "maximum_retries_per_diagnostic": 1,
        "maximum_total_solution_attempts_including_failed": 12, "selected_diagnostics": []}
        and result.get("diagnostic_budget") == budget and result.get("executed_diagnostics") == [],
        "unfrozen/unbudgeted desktop diagnostic or hidden failed attempt")
    current_basis(selection, evidence)
    code_basis = evidence.api.read_json(evidence.file(selection["code_detail_basis"]))
    evidence.sources(code_basis, selection["code_detail_basis"])
    parent_validation(result["selection_binding"], result.get("parent_validation_evidence"), evidence)
    evidence.prime_lines(result.get("rows"))
    receivers, decisions = row_inventory(selection, result.get("rows"), evidence)
    require(result.get("receiver_contexts") == receivers and result.get("decision_counts") == decisions
            and result.get("counts") == {"duties": 30, "families": 8, "timber_receiver_contexts": 44,
                                         "signed_current_witnesses": sum(len(row["signed_current_witnesses"]) for row in result["rows"]),
                                         "new_native_solution_attempts_including_failed": 0}, "desktop decision census differs")


def check_reduced_assessment(root, document, api, cache):
    """Optional index section; never closes the legacy numerical extension."""
    entry = document.get("reduced_assessment")
    if entry is None:
        return {}
    require(isinstance(entry, dict) and entry.get("schema") == SCHEMA
            and entry.get("status") == "complete_desktop_decision_review"
            and entry.get("parent_final_validation", {}).get("confirmed") is True,
            "desktop review lacks typed endpoint/parent final validation")
    extension = document["numerical_acceptance_extension"]
    require(extension.get("status") == "in_progress", "desktop review must not complete the old numerical extension")
    evidence = Evidence(Path(root).resolve(), api, document.get("maintained_source_resolution", {}), cache)
    require(entry["selection"].get("sha256") == SELECTION_SHA, "frozen desktop selection changed")
    selection = api.read_json(evidence.file(entry["selection"]))
    outputs = evidence.owner(entry["receipt"])
    for key in ("result", "preserved_producer_snapshot"):
        require(outputs.get(evidence.file(entry[key])) == entry[key]["sha256"], "desktop result/producer lacks its exact owner")
    result = api.read_json(evidence.file(entry["result"]))
    evidence.context_resolutions(result.get("consulted_source_resolution", []))
    require(result.get("selection_binding") == entry["selection"], "desktop result selection differs")
    require(extension.get("selected_coupled_force_basis") == selection["selected_coupled_force_basis"], "desktop selected force basis stale")
    for key, item in selection["selected_results"].items():
        registered = extension.get("results", {}).get(key, {})
        require(item == {"receipt": {"path": registered.get("receipt"), "sha256": registered.get("receipt_sha256")},
                         "result": {"path": registered.get("result"), "sha256": registered.get("result_sha256")}},
                "desktop selected packet differs from registered current evidence: " + key)
    shards = []
    require(isinstance(result.get("shard_bindings"), list) and len(result["shard_bindings"]) == 5,
            "desktop frozen five-shard input set missing")
    for ref in result.get("shard_bindings", []):
        shard = api.read_json(evidence.file(ref))
        shard_check(shard, entry["selection"])
        evidence.sources(shard, ref)
        shards.extend(shard.get("rows", []))
    require(canonical(sorted(shards, key=lambda row: row["joint_id"])) == canonical(result.get("rows")),
            "desktop aggregate differs from its frozen duty shards")
    assessment_check(selection, result, evidence)
    receipt_covers(evidence, entry["receipt"])
    return {"reduced_desktop_duties": 30, "reduced_desktop_receiver_contexts": 44,
            "reduced_desktop_decisions": result["decision_counts"], "reduced_desktop_native_attempts": 0}


def publish(root, request_path, request_sha, output):
    """Pure JSON/hash publication; no solver, factor, mesh or native module."""
    root, request_path, output = Path(root).resolve(), Path(request_path).resolve(), Path(output).resolve()
    require(output.is_relative_to(root) and not output.exists(), "fresh repository desktop output required")
    require(hashlib.sha256(request_path.read_bytes()).hexdigest() == request_sha, "desktop publication request changed")
    request = json.loads(request_path.read_text())
    require(request.get("schema") == "reduced_desktop_publication_request/v1", "desktop publication request schema differs")
    binding = request["checker_binding"]
    require(binding.get("sha256") == CHECKER_SHA, "desktop frozen source-ownership helper changed")
    checker_path = root / binding["path"]
    require(hashlib.sha256(checker_path.read_bytes()).hexdigest() == CHECKER_SHA, "desktop helper digest differs")
    loader = importlib.machinery.SourceFileLoader("reduced_desktop_original_checker", str(checker_path))
    api = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
    loader.exec_module(api)
    maintained = request.get("maintained_source_resolution", {})
    consulted = request.get("consulted_source_resolution", [])
    require(isinstance(maintained, dict), "invalid desktop source redirects")
    evidence = Evidence(root, api, maintained, {})
    evidence.context_resolutions(consulted)
    evidence.file({"path": evidence.name(request_path), "sha256": request_sha})
    evidence.file(binding)
    selection_ref = request["selection_binding"]
    require(selection_ref.get("sha256") == SELECTION_SHA, "desktop frozen selection differs")
    selection = api.read_json(evidence.file(selection_ref))
    rows = []
    require(isinstance(request.get("shards"), list) and len(request["shards"]) == 5,
            "desktop publication requires the frozen five-shard set")
    for ref in request["shards"]:
        shard = api.read_json(evidence.file(ref))
        shard_check(shard, selection_ref)
        evidence.sources(shard, ref)
        rows.extend(shard.get("rows", []))
    for ref in request.get("artifact_receipts", []):
        evidence.owner(ref)
    current_basis(selection, evidence)
    # Explicit paired diagnostic references can provide supporting output
    # authority; they never promote changed/rejected forces to current witnesses.
    for ref in references(rows):
        if Path(ref["path"]).name.endswith("receipt.json"):
            evidence.owner(ref)
    rows.sort(key=lambda row: row["joint_id"])
    evidence.prime_lines(rows)
    receivers, decisions = row_inventory(selection, rows, evidence)
    result = {"schema": SCHEMA, "status": STATUS, "claim": CLAIM, "selection_binding": selection_ref,
        "shard_bindings": request["shards"], "rows": rows, "receiver_contexts": receivers, "decision_counts": decisions,
        "parent_validation_evidence": request["parent_validation_evidence"],
        "consulted_source_resolution": consulted,
        "counts": {"duties": 30, "families": 8, "timber_receiver_contexts": 44,
                   "signed_current_witnesses": sum(len(row["signed_current_witnesses"]) for row in rows),
                   "new_native_solution_attempts_including_failed": 0},
        **{key: selection[key] for key in ("selected_results", "selected_coupled_force_basis", "preserved_studies",
                                         "reviewed_geometry", "release_flags", "diagnostic_budget")},
        "executed_diagnostics": [], **dict.fromkeys(FALSE_FLAGS, False)}
    assessment_check(selection, result, evidence)
    own_source = Path(__file__).resolve()
    own_sha = hashlib.sha256(own_source.read_bytes()).hexdigest()
    evidence.file({"path": evidence.name(own_source), "sha256": own_sha})
    for name, digest in evidence.pins.items():
        api.authenticate(root, name, digest, {}, {})
    output.mkdir()
    snapshot = output / "producer.py.snapshot"
    snapshot.write_bytes(own_source.read_bytes())
    (output / "summary.json").write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n")
    receipt = {"schema": "reduced_desktop_decision_receipt/v1", "status": STATUS,
        "source_sha256": evidence.pins, "source_before_sha256": evidence.pins, "source_after_sha256": evidence.pins,
        "source_resolution": {evidence.name(own_source): {"original_path": evidence.name(own_source), "sha256": own_sha,
            "snapshot_path": evidence.name(snapshot)}},
        "output_sha256": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in (snapshot, output / "summary.json")},
        "native_or_CAD_or_factor_or_optimizer_executed": False, **dict.fromkeys(FALSE_FLAGS, False)}
    (output / "receipt.json").write_text(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n")
    return {"status": STATUS, "result": evidence.name(output / "summary.json"),
            "result_sha256": receipt["output_sha256"]["summary.json"], "receipt": evidence.name(output / "receipt.json"),
            "receipt_sha256": hashlib.sha256((output / "receipt.json").read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--expected-request-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(canonical(publish(args.root, args.request, args.expected_request_sha256, args.output)))


if __name__ == "__main__":
    main()
