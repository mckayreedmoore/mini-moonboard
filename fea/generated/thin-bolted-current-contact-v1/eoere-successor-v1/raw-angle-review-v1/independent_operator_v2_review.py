"""Read source identities and replay a two-coordinate CSR codec in memory."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
import platform
import sys
from pathlib import Path

import numpy as np
import scipy
from scipy.sparse import csr_matrix

OWN = Path(__file__).resolve()
ROOT = OWN.parents[5]
LEAF = OWN.parent.parent / "four-port-method-v1"
PRIOR_SHA = "1c506aa23cb76ba13934462deedb016c03113a1d683bd805967531d120ca58ca"
EXPECTED = {
    "operator_bundle.py": "534356acc914bd9fb81f24e67311fe40123d70754224a6466fe0da1d7f1426a9",
    "test_operator_bundle.py": "359a4a39df9c096cbcd693b4866c2b9bbcaea3fb3bd2bbb7b94f388c5d6ca1e3",
    "run_first_order_v2.py": "750dd24733c101c98c06d135e9c5c88a5b33a610d09e79736ee4500171685f32",
    "test_run_first_order_v2.py": "28538f20257734ca0190985491f6dac60a7552509ef78e9a43c309c9d150eb6b",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def verify(pins):
    require(all(sha(ROOT / p) == digest for p, digest in pins.items()), "reviewed source identity differs")


def review():
    prior_path = OWN.parent / "independent-guarded-factory-method-review.json"
    require(sha(prior_path) == PRIOR_SHA, "prior reviewed method record differs")
    prior = json.loads(prior_path.read_bytes())
    pins = dict(prior["source_sha256"])
    pins[str(prior_path.relative_to(ROOT))] = PRIOR_SHA
    for name, digest in EXPECTED.items():
        pins[str((LEAF / name).relative_to(ROOT))] = digest
    verify(pins)
    before = canonical(pins)
    spec = importlib.util.spec_from_file_location("independent_v2_operator_codec", LEAF / "run_first_order_v2.py")
    method = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(method)
    for path, digest in method.runtime_pins().items():
        require(path not in pins or pins[path] == digest, "runtime source join differs")
        pins[path] = digest
    verify(pins)
    before = canonical(pins)

    # Generic codec fixture only. This is not a physical stiffness, coordinate
    # chart, candidate coefficient vector or equilibrium field.
    matrix = csr_matrix((2, 2), dtype=np.float64)
    matrix.data = np.array([2., 1., 3., 4.], dtype="<f8")
    matrix.indices = np.array([1, 0, 1, 0], dtype="<i8")
    matrix.indptr = np.array([0, 3, 4], dtype="<i8")
    raw_before = {key: getattr(matrix, key).tobytes() for key in ("data", "indices", "indptr")}
    arrays = {}
    record = method.bundle._put_csr(arrays, "unsorted-codec", matrix)
    stream = io.BytesIO()
    np.savez_compressed(stream, **arrays)
    encoded = stream.getvalue()
    with np.load(io.BytesIO(encoded), allow_pickle=False) as bank:
        restored_arrays = {key: bank[key].copy() for key in bank.files}
    restored = method.bundle._get_csr(restored_arrays, record)
    require(all(getattr(restored, key).tobytes() == raw_before[key] and
                getattr(matrix, key).tobytes() == raw_before[key] for key in raw_before), "raw CSR bytes reordered/merged")
    require(restored.indices.dtype == matrix.indices.dtype and restored.indptr.dtype == matrix.indptr.dtype,
            "int64 indices downcast")
    # Row0=x0+5*x1, row1=4*x0; duplicate column1 retained as2+3.
    observed = restored @ np.array([.3, -.2])
    expected = np.array([-.7, 1.2])
    error = float(np.max(abs(observed-expected)))
    require(error < 1e-14 and not restored.has_sorted_indices and len(restored.data) == 4,
            "independent unsorted/duplicate CSR arithmetic differs")
    verify(pins)
    return {
        "schema": "independent_eoere_operator_bundle_v2_method_review/v1",
        "disposition": "READY_BOUNDED_V2_OPERATOR_EXPORT_METHOD_ONLY",
        "source_sha256": pins, "source_count": len(pins), "source_manifest_before_after_sha256": [before, canonical(pins)],
        "all_pinned_bytes_unchanged": True,
        "review_producer": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
        "execution": {"sys_argv": sys.argv.copy(), "sys_orig_argv": sys.orig_argv.copy(), "cwd": str(Path.cwd()),
            "environment": {k: os.environ.get(k) for k in ("PYTHONPATH", "OPENBLAS_NUM_THREADS", "PYTHONDONTWRITEBYTECODE")}},
        "tools": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "focused_verification": {"result": "14 passed in 2.80s", "ruff": "all four new frozen source/test paths passed",
            "test_paths": [str((LEAF / name).relative_to(ROOT)) for name in ("test_operator_bundle.py", "test_run_first_order_v2.py")],
            "environment": "PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 PYTHONPATH=/home/mckay-linux/repos/mini-moonboard",
            "invocation": ".venv/bin/python -m pytest -q -p no:cacheprovider <both test_paths>"},
        "independent_codec": {"scope": "Two-coordinate algebraic CSR codec only",
            "shape": [2, 2], "data": matrix.data.tolist(), "indices": matrix.indices.tolist(), "indptr": matrix.indptr.tolist(),
            "data_dtype": matrix.data.dtype.str, "indices_dtype": matrix.indices.dtype.str,
            "all_raw_bytes_and_duplicate_columns_preserved": True, "sorted_indices": False,
            "input": [.3, -.2], "hand_output": expected.tolist(), "observed_output": observed.tolist(),
            "hand_arithmetic_max_error": error, "in_memory_npz_bytes": len(encoded),
            "in_memory_npz_sha256": hashlib.sha256(encoded).hexdigest()},
        "reviewed_contract": [
            "Snapshot copies exact native CSR data/indices/indptr, applied RHS and full rigid-mode matrix; no sort, duplicate-column merge, format conversion or new operator assembly.",
            "Reader verifies both raw artifact SHAs, every array dtype/shape/content, complete key inventory, CSR bounds/row dimensions, source-order interaction IDs and reproduced original operator fingerprint; allow_pickle=False.",
            "Coordinate map includes every timber station/index/source row, panel coefficients/basis/knots, continuous-shaft station/index/owner/surface/end row and all four-port fitting descriptors. Pre-shaft fitting embedding is explicitly recorded; unused legacy fitting indices remain empty.",
            "V2 writes exclusive NPZ and manifest before captured frozen28ce execution, joins both raw hashes plus new loaded producer identities into source pins before state identity, and compares field fingerprint to reimported pre-solve operators.",
            "The captured frozen core retains one preparation and one fresh search. Only execute/runtime_pins/write_exclusive callbacks are scoped and restored for success, returned failure, raised error or timeout.",
            "Failure/timeout records carry truthful attempted artifact paths and completed pointer when available; outside-preparation interruption pointer is null and accepted coefficients/actions remain null.",
            "Successful panel coefficient export selects the exact final q indices from the recorded source chart; schema is distinct and independent field admission remains pending."],
        "confirmed_blockers": [],
        "limits": ["Only source checks, 14 tiny fixtures and a generic in-memory codec executed. No candidate input reader/preparation/q/K/CAD/native/global solve or panel operator rehydration invoked by this reproducer.",
            "Snapshot authority authenticates the actual original prepared operators; physical source-chart ownership and their current source laws still require the distinct independent field gate.",
            "Partial artifact creation on a snapshot interruption is retained; a null completed pointer does not assert no attempted file exists.",
            "First-order gross-stock/four-strip/reference-point spring and unmeasured material/contact limits are unchanged. No candidate response, physical contact, strength, fabrication or climbing acceptance transferred."],
        "release": {"bounded_operator_export_method_ready": True, "candidate_prepared_or_evaluated": False,
            "independent_field_admitted": False, "capacity": False, "fabrication": False, "climbing": False},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = review()
    data = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False)+"\n").encode()
    with args.out.open("xb") as stream:
        stream.write(data)
    print(json.dumps({"path": str(args.out), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                      "source_count": result["source_count"], "disposition": result["disposition"]}))


if __name__ == "__main__":
    main()
