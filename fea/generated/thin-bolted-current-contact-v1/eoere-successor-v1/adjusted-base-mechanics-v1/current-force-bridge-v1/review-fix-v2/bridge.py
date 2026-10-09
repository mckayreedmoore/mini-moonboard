"""Reviewed boundary corrections around the unchanged current force bridge.

Reserve output before loading the frozen implementation. Authenticate the raw
and selected independent input review before any panel-bank callback. Verify
all reused source pins at runtime and the exact bytes immediately before each
private AST parse. The original preparation, solve and replay arithmetic stays
unchanged; this file supplies neither production readiness nor acceptance.
"""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import os
import sys
from contextlib import ExitStack, contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

OWN = Path(__file__).resolve()
FROZEN = OWN.parent.parent / "bridge.py"
FROZEN_SHA = "ddc85386050d97145597dc720bef78634c9b326f0878aced8c02c8df4710c05b"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
_loaded = None
RELEASE = {"candidate_accepted": False, "complete_joint_acceptance": False, "capacity_established": False,
           "fabrication_released": False, "structural_released": False, "climbing_released": False}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked_bytes(path, expected):
    raw = Path(path).read_bytes()
    require(digest(raw) == expected, "exact compiler/source bytes changed: " + str(path))
    return raw


def frozen():
    global _loaded
    checked_bytes(OWN, LOADED_SHA)
    checked_bytes(FROZEN, FROZEN_SHA)
    if _loaded is None:
        spec = importlib.util.spec_from_file_location("eoere_current_force_bridge_frozen_v1_for_review_fix", FROZEN)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        module.review_fix_original_source_pins = module.source_pins
        module.review_fix_original_compile_function = module.compile_function
        module.review_fix_compiler_sources = {
            FROZEN.resolve(): FROZEN_SHA,
            **{(module.PACKET / name).resolve(): sha for name, sha in module.REUSED.items()},
            module.bundle.CORE.resolve(): module.bundle.CORE_SHA,
            module.base.OWN.resolve(): module.base.LOADED_SHA,
        }
        _loaded = module
    return _loaded


def runtime_source_pins(b, extra=None, *, method=None):
    pins = b.review_fix_original_source_pins(extra, method=method)
    sources = {**{(b.PACKET / name).resolve(): sha for name, sha in b.REUSED.items()},
               FROZEN: FROZEN_SHA, OWN: LOADED_SHA}
    for path, sha in sources.items():
        checked_bytes(path, sha)
        name = b.bundle.artifact_path(path)
        require(name not in pins or pins[name] == sha, "review-fix runtime source pin conflict")
        pins[name] = sha
    return b.base.verify_pins(pins)


def source_pins(extra=None, *, method=None):
    return runtime_source_pins(frozen(), extra, method=method)


def checked_ast(expected, *, literal_expressions=()):
    def parse(raw, *args, **kwargs):
        if isinstance(raw, str):
            require(raw in literal_expressions and not args and kwargs == {"mode": "eval"},
                    "unreviewed literal AST expression")
        else:
            require(isinstance(raw, bytes) and digest(raw) == expected, "exact compiler bytes changed immediately before AST parse")
        return ast.parse(raw, *args, **kwargs)
    return SimpleNamespace(**{**vars(ast), "parse": parse})


def compile_function(b, path, name, context, **kwargs):
    path = Path(path).resolve()
    expected = b.review_fix_compiler_sources.get(path)
    require(expected is not None, "compiler source is not a reviewed original")
    checked_bytes(path, expected)
    context = dict(context)
    if path == (b.PACKET / "floor-practical-resolution-v1/runner.py").resolve() and name == "compile_execute":
        # This returned function performs a second, nested parse of CORE.
        # Its private ast namespace verifies the exact second-read bytes too.
        context["ast"] = checked_ast(b.bundle.CORE_SHA)
    with patch.object(b, "ast", checked_ast(expected)):
        return b.review_fix_original_compile_function(path, name, context, **kwargs)


@contextmanager
def corrected_context(b):
    require(b.OWN == FROZEN and b.LOADED_SHA == FROZEN_SHA, "review-fix context must be unnested and serialized")
    runtime_source_pins(b)
    try:
        with ExitStack() as stack:
            for name, value in {"OWN": OWN, "LOADED_SHA": LOADED_SHA,
                                "source_pins": lambda extra=None, *, method=None: runtime_source_pins(b, extra, method=method),
                                "compile_function": lambda path, name, context, **kw: compile_function(b, path, name, context, **kw)}.items():
                stack.enter_context(patch.object(b, name, value))
            # The frozen independent force auditor has its own nested AST read.
            stack.enter_context(patch.object(b.old_gate, "ast", checked_ast(b.base.LOADED_SHA,
                literal_expressions=("set(RESTRAINED_HOSTS)",))))
            yield b
    finally:
        runtime_source_pins(b)


class ReservedOutput:
    """One open('x') ownership token; writes use the original open inode."""
    def __init__(self, path):
        self.path = Path(os.path.abspath(path))
        self.stream = self.path.open("x+")  # Includes dangling-symlink/race refusal.
        self.identity = os.fstat(self.stream.fileno())
        self.write({"schema": "eoere_current_force_bridge_attempt/v2", "status": "STARTED",
                    "command": list(sys.orig_argv), "wrapper_path": str(OWN), "wrapper_sha256": LOADED_SHA,
                    "accepted_q": None, "accepted_actions": None, "release": RELEASE})

    def owned(self):
        current = self.path.lstat()
        require((current.st_dev, current.st_ino) == (self.identity.st_dev, self.identity.st_ino),
                "reserved output pathname no longer names the owned inode")

    def write(self, result):
        self.owned()
        raw = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
        self.stream.seek(0)
        self.stream.write(raw)
        self.stream.truncate()
        self.stream.flush()
        os.fsync(self.stream.fileno())

    def failed(self, error):
        self.write({"schema": "eoere_current_force_bridge_attempt/v2", "status": "FAILED",
                    "command": list(sys.orig_argv), "wrapper_path": str(OWN), "wrapper_sha256": LOADED_SHA,
                    "error_type": type(error).__name__, "error": str(error),
                    "accepted_q": None, "accepted_actions": None, "release": RELEASE})

    def close(self):
        self.stream.close()


@contextmanager
def reserve(path):
    output = ReservedOutput(path)
    try:
        yield output
    except BaseException as error:
        output.failed(error)
        raise
    finally:
        output.close()


def preauthenticate(b, args, method):
    """Real raw/selected review gate, before methods() touches the bank."""
    with b.factory_boundary():
        raw, pins = b.factory.read_inputs(args.inputs, args.inputs_sha256)
    selected, selection = b.driver.select_case(raw, args.case_id)
    review = {"path": b.bundle.artifact_path(args.input_review.resolve()), "sha256": args.input_review_sha256}
    b.authenticate_review(review, selected, b.source_pins(pins, method=method), raw_data=raw, selection=selection)


def corrected_run_function(b, output):
    raw = checked_bytes(FROZEN, FROZEN_SHA)
    tree = checked_ast(FROZEN_SHA).parse(raw)
    node = copy.deepcopy(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run_case"))
    fresh = ast.parse('require(not any(p.exists() for p in paths), "preserve every existing current field/operator/failure")').body[0]
    bank = ast.parse("centroidal, bank = methods(method)").body[0]
    counts = {"reserved_output_guard": 0, "review_before_bank": 0}
    body = []
    for item in node.body:
        if ast.dump(item) == ast.dump(fresh):
            body.append(ast.parse("verify_reserved_outputs(paths)").body[0])
            counts["reserved_output_guard"] += 1
        else:
            if ast.dump(item) == ast.dump(bank):
                body.append(ast.parse("preauthenticate(args, method)").body[0])
                counts["review_before_bank"] += 1
            body.append(item)
    require(counts == {"reserved_output_guard": 1, "review_before_bank": 1}, "exact reviewed run orchestration hooks differ")
    node.body = body
    def verify_reserved_outputs(paths):
        output.owned()
        require(paths[0] == output.path.resolve() and not any(os.path.lexists(p) for p in paths[1:]),
                "preserve every existing current field/operator/failure")
    context = {**vars(b), "verify_reserved_outputs": verify_reserved_outputs,
               "preauthenticate": lambda args, method: preauthenticate(b, args, method)}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(OWN), "exec"), context)  # noqa: S102
    return context["run_case"]


def run_reserved(args, output, b):
    original_write = b.core.write_exclusive
    def write(path, payload):
        if Path(path).resolve() == output.path.resolve():
            output.write(b.core.serial(payload))
        else:
            original_write(path, payload)
    with patch.object(b.core, "write_exclusive", write):
        return corrected_run_function(b, output)(args)


def run_case(args):
    with reserve(args.out) as output:
        b = frozen()
        with corrected_context(b):
            return run_reserved(args, output, b)


def build_inputs(export_ref, manifest_ref, bank_ref):
    """Pure deferred input join API; no panel K or whole-frame construction."""
    b = frozen()
    with corrected_context(b):
        return b.build_inputs(export_ref, manifest_ref, bank_ref)


def audit(path):
    b = frozen()
    with corrected_context(b):
        return b.audit(path)


def require_admitted_payload(field_bytes, receipt, *, admission_sha256):
    b = frozen()
    with corrected_context(b):
        return b.require_admitted_payload(field_bytes, receipt, admission_sha256=admission_sha256)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    early = argparse.ArgumentParser(description=__doc__, add_help=False)
    early.add_argument("--out", type=Path, required=True)
    early_args, _ = early.parse_known_args(argv)
    with reserve(early_args.out) as output:
        b = frozen()
        with corrected_context(b):
            args = b.parse_args(argv)
            if args.mode == "run":
                return run_reserved(args, output, b)
            if args.mode == "admit":
                require(args.field is not None, "actual current field required for admission")
                result = b.audit(args.field)
            elif args.mode == "build-inputs":
                def ref(name):
                    path, sha = getattr(args, name), getattr(args, name + "_sha256")
                    require(path is not None and sha is not None, "exact " + name + " reference required")
                    return {"path": b.bundle.artifact_path(path.resolve()), "sha256": sha}
                result = b.build_inputs(ref("source_export"), ref("source_manifest"), ref("panel_bank"))
            else:
                result = b.preflight(args)
            output.write(b.core.serial(result))
            print(json.dumps({"schema": result["schema"], "output": str(output.path), "sha256": digest(output.path.read_bytes())}))
            return 0


if __name__ == "__main__":
    raise SystemExit(main())
