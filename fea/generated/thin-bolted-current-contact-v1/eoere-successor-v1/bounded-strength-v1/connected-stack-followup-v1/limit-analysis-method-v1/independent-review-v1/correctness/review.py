"""Independent synthetic-only arithmetic and source-authentication review."""

from __future__ import annotations

import contextlib
import copy
import decimal
import hashlib
import importlib.abc
import importlib.util
import io
import json
import math
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path.cwd()
OUT = Path(__file__).resolve().parent
DOC = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1"
RAW = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1"
PINS = {}


def need(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path, digest=None):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    actual = sha(path)
    need(digest is None or actual == digest, "source mismatch: " + str(path))
    key = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    need(key not in PINS or PINS[key] == actual, "conflicting source pin")
    PINS[key] = actual
    return path


def read(path, digest=None):
    return json.loads(pin(path, digest).read_bytes())


class BlockCAD(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "cadquery" or fullname.startswith("cadquery.") or fullname == "OCP" or fullname.startswith("OCP."):
            raise RuntimeError("No genuine CAD import authorized")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


sys.meta_path.insert(0, BlockCAD())
frozen = read(RAW / "attempt03/frozen-packet.json")
need(len(frozen) == 6, "six-file target required")
for path, record in frozen.items():
    need(pin(path, record["sha256"]).stat().st_size == record["bytes"], "frozen byte count")
inputs = read(DOC / "inputs.json")
result = read(DOC / "result.json")
verification = read(DOC / "verification.json")
for ref in inputs["references"]:
    pin(ref["path"], ref["sha256"])
for record in verification["run_files"].values():
    pin(record["path"], record["sha256"])
details = read(RAW / "attempt03/details.json")
for name in ("result.json", "details.json"):
    need((RAW / "attempt03" / name).read_bytes() == (RAW / "replay" / name).read_bytes(), "issued replay mismatch")
    pin(RAW / "replay" / name)
a = load(DOC / "analyze.py", "independent_synthetic_limit_producer")
v = load(DOC / "verify.py", "independent_synthetic_limit_checker")
a.check_pins(inputs)
pin(a.highs_wrapper.__file__, inputs["environment"]["scipy_highs_wrapper_sha256"])
cases = {case["id"]: case for case in inputs["published_cases"] + inputs["synthetic_cases"]}
need(len(cases) == 15 and len(details) == 45, "coupon/field census")
need(result["candidate_inputs_used"] is False and result["candidate_joint_capacity"] is None and result["capacity_or_pass_claim"] is False, "candidate capacity overclaim")
need(inputs["candidate_inputs_used"] is False and verification["candidate_inputs_used"] is False and verification["capacity_or_pass_claim"] is False, "claim boundary")

decimal.getcontext().prec = 50
D = lambda value: decimal.Decimal(str(value))
max_raw_relative_error = max_published_error = 0.0
for row in result["cases"]:
    case = cases[row["id"]]
    lm, ls, qm, qs, moment, gap = (D(case[key]) for key in ("main_length_in", "side_length_in", "main_bearing_lb_in", "side_bearing_lb_in", "yield_moment_lb_in", "gap_in"))
    coefficients = {
        "II": (1/(4*qs)+1/(4*qm), ls/2+gap+lm/2, -qs*ls*ls/4-qm*lm*lm/4),
        "IIIm": (1/(2*qs)+1/(4*qm), gap+lm/2, -moment-qm*lm*lm/4),
        "IIIs": (1/(4*qs)+1/(2*qm), ls/2+gap, -qs*ls*ls/4-moment),
        "IV": (1/(2*qs)+1/(2*qm), gap, -2*moment),
    }
    raw = {"Im": qm*lm, "Is": qs*ls}
    for mode, (aa, bb, cc) in coefficients.items():
        raw[mode] = ((bb*bb-4*aa*cc).sqrt()-bb)/(2*aa)
    for mode, exact in raw.items():
        error = abs(float(exact)-row["analytic_all_raw_modes_lbf"][mode])/float(exact)
        max_raw_relative_error = max(max_raw_relative_error, error)
        need(error < 1e-14, "raw analytic mode differs from independent decimal equation")
    need(min(raw, key=raw.get) == row["raw_governing_mode"], "raw governing mode")
    need(abs(float(min(raw.values()))-row["analytic_raw_yield_lbf"]) < 1e-10, "raw/design mixing")
    if "published_reference_values_lbf" in case:
        k = case["k_theta"]
        references = [float(raw[mode])/rd for mode, rd in zip(a.MODES, [4*k, 4*k, 3.6*k, 3.2*k, 3.2*k, 3.2*k])]
        error = max(abs(x-y) for x,y in zip(references, case["published_reference_values_lbf"]))
        max_published_error = max(max_published_error, error)
        need(error <= .51, "published rounded design references differ")

max_force_error = max_end_moment = max_peak_error = 0.0
for key, field in details.items():
    identity, grid = key.rsplit("/", 1)
    case, cells = cases[identity], int(grid)
    rows = list(zip(field["a_in"], field["b_in"], field["bearing_density_lb_in"]))
    need(len(rows) == 2*cells, "field cell dimension")
    def shear(x):
        return math.fsum(q*max(0., min(x, hi)-lo) for lo,hi,q in rows if x > lo)
    def moment(x):
        terms = []
        for lo,hi,q in rows:
            stop = min(x,hi)
            if stop > lo:
                terms.append(q*(stop-lo)*(x-(lo+stop)/2))
        return math.fsum(terms)
    peaks = [lo for lo,hi,q in rows] + [hi for lo,hi,q in rows]
    for lo,hi,q in rows:
        need(lo < hi and math.isfinite(q), "valid finite intervals")
        if q:
            critical = lo-shear(lo)/q
            if lo < critical < hi:
                peaks.append(critical)
    side = math.fsum(q*(hi-lo) for lo,hi,q in rows[:cells])
    main = math.fsum(q*(hi-lo) for lo,hi,q in rows[cells:])
    force_error = max(abs(side-field["statics_load_lbf"]), abs(main+field["statics_load_lbf"]))
    end_moment = abs(moment(case["side_length_in"]+case["gap_in"]+case["main_length_in"]))
    maximum = max(abs(moment(point)) for point in peaks)
    need(force_error < 1e-8 and end_moment < 1e-8, "independent force/end moment equilibrium")
    need(maximum <= case["yield_moment_lb_in"]*(1+1e-9), "interior moment cap exceeded")
    need(max(abs(q)/cap for q,cap in zip(field["bearing_density_lb_in"], field["bearing_bounds_lb_in"])) <= 1+1e-10, "bearing cap exceeded")
    row = next(row for row in result["cases"] if row["id"] == identity)
    own_grid = next(row for row in row["grids"] if row["cells_per_member"] == cells)
    max_peak_error = max(max_peak_error, abs(maximum-own_grid["maximum_exact_moment_lb_in"]))
    need(field["statics_load_lbf"] == own_grid["scaled_statics_load_lbf"], "stored load mismatch")
    max_force_error = max(max_force_error, force_error)
    max_end_moment = max(max_end_moment, end_moment)
need(v.check(result, details, inputs) == verification["independent_checks"], "retained dimensional checker receipt differs")

certificate_count = 0
max_independent_kkt_residual = 0.0
actual_linprog = a.linprog
def reviewed_linprog(c, **kwargs):
    global certificate_count, max_independent_kkt_residual
    out = actual_linprog(c, **kwargs)
    if out.status != 0:
        return out
    np = a.np
    c = np.asarray(c)
    n = len(c)
    ae = np.asarray(kwargs.get("A_eq", np.zeros((0,n))))
    be = np.asarray(kwargs.get("b_eq", np.zeros(len(ae))))
    au = np.asarray(kwargs.get("A_ub", np.zeros((0,n))))
    bu = np.asarray(kwargs.get("b_ub", np.zeros(len(au))))
    bounds = kwargs.get("bounds", [(0,None)]*n)
    lower = np.array([-np.inf if lo is None else lo for lo,hi in bounds])
    upper = np.array([np.inf if hi is None else hi for lo,hi in bounds])
    need(np.isfinite(out.x).all() and math.isfinite(out.fun), "nonfinite optimum")
    dual_objective = be@out.eqlin.marginals + bu@out.ineqlin.marginals
    dual_objective += lower[np.isfinite(lower)]@out.lower.marginals[np.isfinite(lower)]
    dual_objective += upper[np.isfinite(upper)]@out.upper.marginals[np.isfinite(upper)]
    gradient = c - ae.T@out.eqlin.marginals - au.T@out.ineqlin.marginals - out.lower.marginals - out.upper.marginals
    residual = max(float(abs(gradient).max()), abs(out.fun-dual_objective), float(abs(ae@out.x-be).max(initial=0)), float((au@out.x-bu).max(initial=0)), float((lower-out.x).max(initial=0)), float((out.x-upper).max(initial=0)), float(out.ineqlin.marginals.max(initial=0)), float((-out.lower.marginals).max(initial=0)), float(out.upper.marginals.max(initial=0)))
    need(math.isfinite(residual) and residual <= 1e-8, "independent KKT/primal/dual check")
    max_independent_kkt_residual = max(max_independent_kkt_residual, residual)
    certificate_count += 1
    return out
with patch.object(a, "linprog", reviewed_linprog):
    fresh_result, fresh_details = a.run(inputs)
need(encoded(fresh_result) == (DOC / "result.json").read_bytes() and encoded(fresh_details) == (RAW / "attempt03/details.json").read_bytes(), "fresh in-memory synthetic replay differs")

with tempfile.TemporaryDirectory(prefix="synthetic-provenance-review-") as directory:
    fixture = Path(directory)
    input_path = fixture / "inputs.json"
    input_path.write_bytes((DOC / "inputs.json").read_bytes())
    original_digest = sha(input_path)
    real_run = a.run
    def changed_run(snapshot):
        changed = copy.deepcopy(snapshot)
        changed["published_cases"][0]["main_bearing_lb_in"] *= 1.1
        input_path.write_bytes(encoded(changed))
        return real_run(snapshot)
    with patch.object(a, "PACKET", fixture), patch.object(a, "run", changed_run), patch.object(sys, "argv", ["analyze.py", "--out", str(fixture / "fresh-out")]), contextlib.redirect_stdout(io.StringIO()):
        a.main()
    emitted = json.loads((fixture / "fresh-out/result.json").read_bytes())
    changed_digest = sha(input_path)
    need(emitted["inputs_sha256"] == changed_digest != original_digest, "input change provenance reproduction")
    need(emitted["cases"][0]["analytic_all_raw_modes_lbf"]["Im"] == 3600.0, "old input computation not reproduced")
    provenance_failure = {"original_input_sha256": original_digest, "changed_input_sha256": changed_digest, "emitted_input_sha256": emitted["inputs_sha256"], "computed_Im_lbf": 3600.0, "changed_source_expected_Im_lbf": 3960.0, "published_without_source_change_error": True, "only_temp_fixture_modified": True}
    # Existing lexical outputs, including dangling links, reject before run().
    old_run = a.run
    def forbidden(*_):
        raise AssertionError("existing output reached synthetic run")
    rejected_outputs = []
    for name, kind in (("existing-dir", "directory"), ("existing-file", "file"), ("existing-link", "dangling_symlink")):
        output = fixture / name
        if kind == "directory": output.mkdir()
        elif kind == "file": output.write_text("preserve")
        else: output.symlink_to(fixture / "missing-link-target")
        with patch.object(a, "run", forbidden), patch.object(sys, "argv", ["analyze.py", "--out", str(output)]), contextlib.redirect_stderr(io.StringIO()):
            try: a.main()
            except SystemExit as error: need(error.code == 2, "output rejection status")
            else: raise ValueError("existing output accepted")
        rejected_outputs.append(kind)
    with patch.object(a, "linprog", lambda *_args, **_kwargs: SimpleNamespace(success=False, status=2, message="synthetic status control")):
        try: a.solve(inputs["synthetic_cases"][0], 32, inputs)
        except RuntimeError as error: need("Synthetic LP failed: 2" in str(error), "failed-LP error handling")
        else: raise ValueError("failed LP accepted")

a.check_pins(inputs)
for path,digest in PINS.items():
    need(sha(ROOT / path) == digest, "frozen source changed during review")
need("cadquery" not in sys.modules and not any(name == "OCP" or name.startswith("OCP.") for name in sys.modules), "CAD imported")
pin(__file__)
finding = {"severity": "medium", "file": str((DOC / "analyze.py").relative_to(ROOT)), "line": 353,
    "title": "Bind the result to the input bytes actually read before solving",
    "impact": "The result hashes inputs.json only after solving, while before/after check_pins authenticates only the five external references. A changing input file can therefore publish the old numeric results with the new input digest. A temp-copy real synthetic run emitted new-source SHA with Im3600lbf although that changed source requires3960lbf. The current issued frozen results remain unchanged and reproduce correctly.",
    "fix": "Capture the input bytes/digest and analyzer digest before computation, bind the output to that captured snapshot, and verify both own files after computation and before publishing. Include them with the external source closure; reject a changed-source attempt without successful result publication. Add an isolated temp-copy mutation control."}
receipt = {
    "schema": "independent_synthetic_limit_analysis_correctness_review/v1",
    "status": "ONE_CONFIRMED_PROVENANCE_FINDING_NUMERICAL_REPLAY_PASSES",
    "substantial_findings": [finding],
    "checks": {"frozen_target_files": 6, "synthetic_cases": 15, "independently_integrated_fields": 45,
        "six_raw_modes_decimal_equation_checks": 90, "maximum_raw_mode_relative_error": max_raw_relative_error,
        "maximum_published_rounded_design_reference_error_lbf": max_published_error,
        "maximum_member_force_error_lbf": max_force_error, "maximum_end_moment_error_lb_in": max_end_moment,
        "maximum_interior_peak_difference_lb_in": max_peak_error,
        "fresh_synthetic_replay_byte_identical": True, "independent_actual_LP_KKT_certificates": certificate_count,
        "maximum_independent_KKT_residual": max_independent_kkt_residual,
        "source_change_failure_reproduction": provenance_failure, "existing_outputs_rejected_before_run": rejected_outputs,
        "failed_LP_status_rejected": True, "source_pins_before_after_unchanged": True,
        "candidate_joint_capacity_remains_null": True, "genuine_CAD_imported": False},
    "primary_source_checks": [
        {"url": "https://awc.org/wp-content/uploads/2021/12/AWC-TR12-1510.pdf", "verified": "2012 edition/copyright2015, Table1-1 raw equations, Section1.3 minimum mode-specific P/Rd, Part2 ideal-plastic statics/end-fixity exclusion, Example3.1 rounded reference values"},
        {"url": "https://github.com/scipy/scipy/blob/v1.18.1/scipy/optimize/_linprog_highs.py", "verified": "Pinned v1.18.1 source exists; installed wrapper byte hash and environment match inputs"},
        {"url": "https://docs.scipy.org/doc/scipy/reference/optimize.linprog-highs-ds.html", "verified": "Live manual identifies1.18.0; signed bounds/status/marginal conventions agree for used features; no claim of1.18.1 web manual"}],
    "limits": ["All computations are inexpensive synthetic scalar LPs and dimensional/decimal arithmetic; no actual candidate forces, materials or geometry were used.", "No CAD/BRep query, current bank/frame/native/global case/browser/geometry operation.", "The source-change reproduction mutates only a temporary input copy; all six frozen target files and issued attempts remain byte-identical.", "Raw scalar statics benchmarks do not establish compatibility, an ASD design value, candidate joint resistance, or release."],
    "mechanics_acceptance": False, "physical_release": False,
    "command": [".venv/bin/python", "-B", str(Path(__file__).relative_to(ROOT))],
    "source_sha256": PINS}
with (OUT / "receipt.json").open("x") as stream:
    json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
    stream.write("\n")
print(json.dumps({"status": receipt["status"], "receipt_sha256": sha(OUT / "receipt.json"), "source_pin_count": len(PINS)}))
