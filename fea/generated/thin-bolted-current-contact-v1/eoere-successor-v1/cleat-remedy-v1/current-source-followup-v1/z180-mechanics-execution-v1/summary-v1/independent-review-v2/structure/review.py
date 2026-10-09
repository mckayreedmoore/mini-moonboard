"""Bounded review of the summary directory-fd output wrapper; source/mocks only."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import stat
import subprocess
import sys
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = OWN.parents[2]
CORRECTION = PACKET / "review-fix-v2"
TARGETS = {
    "summarize.py": "15dd2c60a1b6db3eeae6e98b0267268a4460c9a6efc86cb711aa8376fb82046f",
    "test_summarize.py": "94cde283b30a6e935992771ab0a1a3d25e7364a5ee1938ff687675e1c3243645",
    "verification.json": "9c279b0e2cbf65bd2b62472c06dd8eb9a694d38dcfa9cadffda3b2e10e5385a5",
}
PREVIOUS = {
    "independent-review-v1/structure/review.py": "1305e1de8bcafab736a1fcdb3d1a64056de5821458a4b1b1d8cab34b5517f6fe",
    "independent-review-v1/structure/receipt.json": "c35e1d0b22f9869541c96fcb76ee879a2c3aa66f1ab5c7a9ec0f868a4dda0d57",
}


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def rejects(callback, text):
    try:
        callback()
    except ValueError as error:
        require(text in str(error), "unexpected rejection: " + str(error))
    else:
        raise AssertionError("expected rejection: " + text)


class InertStream(io.StringIO):
    def fileno(self):
        return 42

    def close(self):
        self.saved = self.getvalue()
        super().close()


def inert_output(c, mode):
    """No OS mutations: model only held parent/leaf identities and callbacks."""
    bound = PACKET / "runs-v1/never-created-structure/output.json"
    parent = SimpleNamespace(st_dev=1, st_ino=2, st_mode=stat.S_IFDIR)
    leaf = SimpleNamespace(st_dev=1, st_ino=3, st_mode=stat.S_IFREG)
    replaced = SimpleNamespace(st_dev=1, st_ino=4, st_mode=stat.S_IFDIR)
    current_parent = parent
    events, closes = [], []
    stream = InertStream()
    manifest = {"source_sha256": {str(c.OWN.relative_to(ROOT)): c.LOADED_SHA}}
    result = {"schema": "inert-summary", "cases": ["inert"], "release": c.RELEASE}
    if mode == "missing_self_pin":
        manifest["source_sha256"].clear()
    def directory_stat(_path):
        return current_parent
    def opened_stat(fd):
        require(fd in (41, 42), "foreign fd accessed")
        return replaced if mode == "parent_before_handle" and fd == 41 else parent if fd == 41 else leaf
    def open_fd(path, flags, *args, **kwargs):
        nonlocal current_parent
        if flags & c.os.O_DIRECTORY:
            events.append("directory-open")
            require(path == bound.parent and flags & c.os.O_NOFOLLOW and not kwargs, "directory open escaped bound parent")
            return 41
        events.append("exclusive-leaf")
        require(path == bound.name and kwargs == {"dir_fd": 41}
                and flags & c.os.O_EXCL and flags & c.os.O_NOFOLLOW, "leaf not exclusive and anchored")
        if mode == "occupied":
            raise FileExistsError("synthetic occupied leaf")
        if mode == "parent_after_leaf":
            current_parent = replaced
        return 42
    def leaf_stat(path, *, dir_fd, follow_symlinks):
        require(path == bound.name and dir_fd == 41 and follow_symlinks is False, "leaf check followed unowned path")
        return replaced if mode == "leaf_replaced" else leaf
    def build(*_args):
        events.append("build")
        if mode == "build_failure":
            raise RuntimeError("synthetic build failure")
        return result
    def original():
        nonlocal current_parent
        require(json.loads(stream.getvalue())["status"] == "STARTED", "original loaded before STARTED receipt")
        events.append("original")
        if mode == "parent_after_started":
            current_parent = replaced
        return SimpleNamespace(ROOT=ROOT, decode=json.loads, checked=lambda *_: json.dumps(manifest).encode(), build=build)
    with ExitStack() as stack:
        stack.enter_context(patch.object(c, "bind_output", return_value=bound))
        stack.enter_context(patch.object(Path, "mkdir"))
        stack.enter_context(patch.object(Path, "lstat", directory_stat))
        stack.enter_context(patch.object(c.os, "open", open_fd))
        stack.enter_context(patch.object(c.os, "fstat", opened_stat))
        stack.enter_context(patch.object(c.os, "stat", leaf_stat))
        stack.enter_context(patch.object(c.os, "fdopen", return_value=stream))
        stack.enter_context(patch.object(c.os, "close", side_effect=closes.append))
        stack.enter_context(patch.object(c.os, "fsync"))
        stack.enter_context(patch.object(c, "original", side_effect=original))
        try:
            actual = c.write_to_file({"path": "synthetic-unread-manifest.json", "sha256": "a" * 64}, bound)
        except (ValueError, RuntimeError, FileExistsError) as error:
            actual = error
    raw = stream.saved if hasattr(stream, "saved") else stream.getvalue()
    require(closes == [41], "directory fd leaked or unexpected fd close")
    if mode == "positive":
        require(actual is result and json.loads(raw) == result and events == ["directory-open", "exclusive-leaf", "original", "build"],
                "positive delegation/order/result differs")
    elif mode == "occupied":
        require(isinstance(actual, FileExistsError) and events == ["directory-open", "exclusive-leaf"] and not raw,
                "occupied leaf reached source or payload")
    elif mode == "parent_before_handle":
        require(isinstance(actual, ValueError) and "opened parent identity" in str(actual)
                and events == ["directory-open"] and not raw, "changed parent handle admitted")
    elif mode == "leaf_replaced":
        require(isinstance(actual, ValueError) and "reserved summary inode" in str(actual)
                and "original" not in events and not raw, "changed leaf accepted or foreign leaf written")
    else:
        failed = json.loads(raw)
        require(isinstance(actual, (ValueError, RuntimeError)) and failed["status"] == "FAILED"
                and failed["directory_fd_anchored"] is True and failed["output_adapter_sha256"] == c.LOADED_SHA
                and not any(failed["release"].values()), "anchored FAILED receipt lost or promoted")
        if mode == "parent_after_leaf":
            require("original" not in events, "changed canonical parent reached source callback")
        elif mode == "missing_self_pin":
            require("build" not in events, "missing output source pin reached build")
        elif mode == "parent_after_started":
            require("canonical parent identity changed" in str(actual), "late parent change not detected")
    if not stream.closed:
        stream.close()


def review():
    pins = {str((CORRECTION / n).relative_to(ROOT)): h for n, h in TARGETS.items()}
    require(all(sha(ROOT / n) == h for n, h in pins.items()), "three corrected target bytes differ")
    verification = read(CORRECTION / "verification.json")
    for mapping in (verification["preserved_method_and_review_sources"],
                    {str((PACKET / n).relative_to(ROOT)): h for n, h in PREVIOUS.items()}):
        for name, digest in mapping.items():
            require(name not in pins or pins[name] == digest, "contradictory retained source pin")
            pins[name] = digest
    for ref in verification["frozen_original_files"].values():
        require(pins[ref["path"]] == ref["sha256"], "original source record differs")
    before = {n: sha(ROOT / n) for n in pins}
    require(before == pins, "source/history target closure differs")
    contexts = ("AGENTS.md", "docs/wood-joints-mvp/README.md", "docs/wood-joints-mvp/completion-ledger.md")
    context_before = {n: sha(ROOT / n) for n in contexts}
    spec = importlib.util.spec_from_file_location("z180_structure_summary_output_v2", CORRECTION / "summarize.py")
    c = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c)
    require(c.OWN == CORRECTION / "summarize.py" and c.LOADED_SHA == TARGETS["summarize.py"], "wrapper source identity differs")
    a = c.original()
    require(a.OWN == c.FROZEN == PACKET / "summarize.py" and a.LOADED_SHA == c.FROZEN_SHA
            and a.build.__code__.co_filename == str(c.FROZEN)
            and a.SELECTORS["sha256"] == "0547b984f150bb9bbd4dbe25b50825a12c047de70bcb1d86a267abd58a935735",
            "frozen build or selector owner changed")
    require(c.RELEASE == a.RELEASE and not any(c.RELEASE.values()), "release boundary changed")
    with patch.object(c, "FROZEN_SHA", "0" * 64):
        rejects(c.original, "summary/output adapter bytes changed")
    rejects(lambda: c.bind_output(PACKET / "runs-v1/attempt/../out.json"), "parent traversal")
    rejects(lambda: c.bind_output(OWN.parent / "foreign.json"), "own runs-v1")
    for mode in ("positive", "occupied", "parent_before_handle", "parent_after_leaf", "parent_after_started",
                 "leaf_replaced", "missing_self_pin", "build_failure"):
        inert_output(c, mode)

    # Both public writer and CLI route to the same guarded operation. The CLI
    # receives only a synthetic path and delegates to a private callback.
    ref = {"path": "synthetic-unread-manifest.json", "sha256": "a" * 64}
    out = PACKET / "runs-v1/never-created-structure/output.json"
    with patch.object(c, "write_to_file", return_value={"schema": "inert", "cases": []}) as writer, redirect_stdout(io.StringIO()):
        c.main(["--manifest", ref["path"], "--manifest-sha256", ref["sha256"], "--out", str(out)])
    writer.assert_called_once_with(ref, out)
    # The original source pin is enforced by its unchanged early build guard,
    # before any manifest artifact read or six-case record load can occur.
    manifest = {"schema": a.INPUT_SCHEMA, "geometry": a.GEOMETRY, "release": a.RELEASE,
                "cases": [{"case_id": case} for case in a.CASES],
                "source_sha256": {str(c.OWN.relative_to(ROOT)): c.LOADED_SHA}}
    with patch.object(a, "checked", side_effect=AssertionError("candidate artifact read before original self pin")):
        rejects(lambda: a.build(manifest, ref), "exact summary source required")
    require(verification["scope"] == {
        "candidate_JSON_or_manifest_read": False,
        "frozen_build_source_join_selectors_classifier_equations_or_tolerances_changed": False,
        "gate_consumer_reducer_CAD_native_global_operator_or_solve_called": False,
        "genuine_summary_output_generated": False,
        "only_output_reservation_and_corrected_self_provenance_changed": True,
    } and verification["unadopted_proposal"] is True and verification["complete_joint_resistance"] is None
        and verification["release"] == c.RELEASE, "inert output proof implies mechanics, strength or adoption")
    require({n: sha(ROOT / n) for n in pins} == before, "corrected/original source/history drift")
    require(not any(n in ("cadquery", "OCP", "numpy", "scipy") or n.startswith("OCP.") for n in sys.modules),
            "native/scientific module imported")
    ruff = subprocess.run([str(ROOT / ".venv/bin/ruff"), "check", "--no-cache", str(OWN)], cwd=ROOT,
                          capture_output=True, text=True, check=False)
    require(ruff.returncode == 0, "own Ruff failed: " + ruff.stdout + ruff.stderr)
    return {
        "schema": "eoere_z180_summary_output_wrapper_structure_review/v2", "findings": [],
        "review_helper_sha256": sha(OWN), "frozen_target_sha256": TARGETS,
        "reused_immutable_v1_structure_review_sha256": PREVIOUS,
        "integrity": {"target_source_history_union": len(pins), "all_bound_bytes_unchanged_before_after": True,
                      "union_sha256": hashlib.sha256(json.dumps(pins, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                      "three_new_target_bytes": sum((CORRECTION / n).stat().st_size for n in TARGETS)},
        "architecture": {"frozen_99_build_source_joins_selectors_schemas_math_untouched": True,
                         "wrapper_owns_only_reservation_failed_receipt_and_added_self_pin": True,
                         "held_directory_fd_nofollow_exclusive_relative_leaf": True,
                         "parent_inode_before_open_and_both_parent_leaf_handle_identities_checked": True,
                         "canonical_parent_replacement_fails_and_failure_write_stays_anchored": True,
                         "STARTED_before_original_load_and_no_candidate_work_on_import": True,
                         "original_and_corrected_manifest_source_pins_required_before_saved_case_selection": True,
                         "API_and_CLI_share_guarded_writer_and_return_original_result": True,
                         "frozen_v1_source_and_receipts_preserved_no_reissue_or_relabelling": True,
                         "six_case_original_scope_exceedances_null_strength_seat_split_and_snapshot_caveat_inherited": True,
                         "current_Z200_authority_HOLD_and_fields_unchanged_Z180_unadopted_no_physical_or_panel_release": True},
        "inert_checks": {"exact_original_load_and_source_drift_rejection": True,
                         "positive_reservation_STARTED_load_build_order_and_exact_result": True,
                         "occupied_leaf_and_changed_parent_handle_stop_before_callbacks": True,
                         "parent_replaced_at_leaf_or_after_STARTED_retains_anchored_FAILED": True,
                         "changed_leaf_inode_stops_all_payload_writes": True,
                         "missing_new_source_pin_stops_build_missing_original_pin_stops_artifact_reads": True,
                         "build_failure_records_unreleased_anchored_FAILED_and_closes_directory": True,
                         "CLI_exact_ref_and_destination_forwarding_traversal_scope_rejection": True},
        "context": {"before_sha256": context_before, "after_sha256": {n: sha(ROOT / n) for n in contexts},
                    "parent_owns_maintained_prose": True},
        "ruff": {"command": ".venv/bin/ruff check --no-cache " + str(OWN.relative_to(ROOT)),
                 "exit_code": ruff.returncode, "output": ruff.stdout.strip()},
        "limits": ["Only frozen source/proof/review records and current instruction/prose context were read. Peer review files are hash-bound retention records only. No candidate descriptors, raw fields, configs, actual roster/manifest or production summary was consumed.",
                   "All directory/leaf creation, metadata and output stream operations in this review are private mocks/in-memory streams. No probe directories or files are written. Producer's 16 real inert filesystem controls remain authenticated evidence, not reissued.",
                   "Original source-only build/joins/selector mathematics review is reused unchanged. The real original module is loaded only for definitions and an early synthetic missing-self-pin rejection, never actual saved-case selection or gate/consumer/reducer/CAD/native/global work.",
                   "Only this new helper/receipt are written; target/history/shared docs/site/index, Git/staging and archive/prune remain untouched. No new physical, capacity, adoption or blanket acceptance gates."],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    receipt = review()
    destination = OWN.with_name("receipt.json")
    if args.write:
        with destination.open("x") as stream:
            stream.write(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n")
        print(json.dumps({"receipt_sha256": sha(destination), "review_helper_sha256": sha(OWN), "findings": len(receipt["findings"])}))
    else:
        print(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
