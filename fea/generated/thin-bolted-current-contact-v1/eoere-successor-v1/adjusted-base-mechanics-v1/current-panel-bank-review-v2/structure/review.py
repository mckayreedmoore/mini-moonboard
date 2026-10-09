"""Independent source/ownership review; never import the panel or CAD methods.

The observed check outputs below were obtained in separate processes before this
receipt was written. Re-running this file verifies the frozen review inputs and
the AST ownership boundaries; it does not rerun or extend those observations.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
BASE = OWN.parents[2]
BANK = BASE / "current-panel-bank-v1"
FIX = BANK / "review-fix-v2"
PINS = {
    BANK / "panel_operators.py": "014f867eac1e9286dee188024544b5853e5cda2aa1cd11037d7aee5a2b29966b",
    BANK / "test_panel_operators.py": "dd48189121a3aef78c60a5eb5677f789ac45a91c7fc42ebb7822442a0986c0c1",
    BANK / "method-receipt.json": "72f1d047ddf567fd2053911157be02288c1357477ee3ca429223bb85f9acc0e2",
    FIX / "cli.py": "6502e109fad6365ed30a31029a24fccdc0ae44826add029fc540f3d42c9f740e",
    FIX / "test_cli.py": "f3881893d012428903af353be4ea9c4070edd8d8e16198366293848109c3f934",
    FIX / "check_source_seam.py": "e9c3359e8b3ece581014e59027ee742144455f784635edefc65803df94e5ab74",
    FIX / "method-receipt.json": "4904adf8dde8bf87c46cfc189c791cd65c6cc91a1cb3329daa28eb738320509a",
    BASE / "extended-cleat-intake-v1/export.py": "bdfa95b4da8dfcb3d183dcaf59574afdb2f42e938f8e535680739fa0637696bb",
    BASE / "parent-authority-v1/extended-cleat-manifest.json": "458a7f0220e5776fdb53b876b9815715bf278c5b22eea7699824a9919dd6bfe6",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def function(tree, name):
    return next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)


def calls(tree, name):
    return sorted(n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call)
                  and ast.unparse(n.func) == name)


def check():
    for path, expected in PINS.items():
        require(sha(path) == expected, "reviewed source differs: " + relative(path))
    bank_tree = ast.parse((BANK / "panel_operators.py").read_text())
    cli_tree = ast.parse((FIX / "cli.py").read_text())
    prepared = function(bank_tree, "prepare_panel_operators")
    require(calls(prepared, "load_projection_inputs")[0]
            < calls(prepared, "raised.prepare_panel_operators")[0]
            < calls(prepared, "refresh_bank")[0]
            < calls(prepared, "raised.verify")[0], "panel API preparation ownership order differs")
    refreshed = function(bank_tree, "refresh_bank")
    require(all(calls(refreshed, name) for name in
                ("raised.aperture_delta", "raised.refresh_screw_ports", "mass.mass_only_quadrature")),
            "frozen numerical primitive reuse differs")
    main = function(cli_tree, "main")
    reservation = next(n for n in main.body if isinstance(n, ast.With))
    require(ast.unparse(reservation.items[0].context_expr) == "args.out.open('x')",
            "corrected CLI no longer reserves a new output exclusively")
    require(calls(reservation, "load_bank") and not any(calls(n, "load_bank")
            for n in main.body if getattr(n, "lineno", 0) < reservation.lineno),
            "frozen import can precede exclusive output admission")
    require(not any(isinstance(n, (ast.Import, ast.ImportFrom))
                    and "panel_operators" in ast.unparse(n) for n in cli_tree.body),
            "corrected CLI imports the frozen bank eagerly")
    old = json.loads((BANK / "method-receipt.json").read_text())
    new = json.loads((FIX / "method-receipt.json").read_text())
    require(old["intake_seam"]["method_sha256"]
            == "7b85a7717d3f2cb06a7a1e6e7f03e556106a46f80f45ce77f9f53d907b71706f",
            "historical stale seam observation was rewritten")
    require(new["source_seam_supplement"]["verified_current_exporter_binding"]
            == PINS[BASE / "extended-cleat-intake-v1/export.py"], "supplementary seam pin differs")
    require(old["actual_current_panel_or_frame_K_built"] is False
            and new["actual_BREPs_imported_or_real_panel_frame_K_q_or_native_solves"] is False
            and not any(new["release"].values()), "bounded evidence or release claims differ")
    retained = {relative(path): {"sha256": expected, "bytes": path.stat().st_size}
                for path, expected in PINS.items()}
    retained[relative(OWN)] = {"sha256": sha(OWN), "bytes": OWN.stat().st_size}
    return {
        "schema": "eoere_current_off_panel_independent_structure_review/v2",
        "status": "NO_SUBSTANTIAL_CONFIRMED_FINDINGS_WITHIN_SOURCE_AND_SYNTHETIC_SCOPE",
        "scope": "Current OFF panel source/API, corrected CLI, current-source seam and frozen-evidence retention only.",
        "source_sha256": {p: row["sha256"] for p, row in retained.items()},
        "reviewed_bytes": sum(row["bytes"] for p, row in retained.items() if p != relative(OWN)),
        "substantial_confirmed_findings": [],
        "architecture": {
            "modularity": "Acceptable: metadata admission, deferred panel refresh and output admission have distinct entrypoints.",
            "cohesion": "Acceptable: wrapper adds output admission only; frozen production API is preserved.",
            "abstraction": "Acceptable: frozen aperture_delta, refresh_screw_ports and mass_only_quadrature are reused without copying numerical implementations.",
            "coupling": "Explicit: pinned historical loader is required for chart/K reuse. Its old contacts/q are discarded; no historical response is selected.",
            "testability": "Acceptable for the stated method scope: source seam, subprocess CLI stubs and tiny 48-DOF synthetic charts. Real bank behavior remains unobserved.",
            "repeatability": "Corrected CLI reserves with exclusive open before lazy imports, preserves failure records and pins its source. Original CLI remains a frozen witness.",
        },
        "observed_independent_verification_before_receipt_creation": [
            {"command": ["uv", "run", "python", "-m", "pytest", relative(BANK / "test_panel_operators.py"), "-q"],
             "exit_code": 0, "output": "18 passed in 2.66s", "scope": "isolated original source/tiny synthetic checks"},
            {"command": ["uv", "run", "python", "-m", "pytest", relative(FIX / "test_cli.py"), "-q"],
             "exit_code": 0, "output": "7 passed in 2.47s", "scope": "subprocess CLI stubs; external-cwd frozen import has a BREP guard"},
            {"command": ["uv", "run", "python", relative(FIX / "check_source_seam.py")],
             "exit_code": 0, "matching_panels": 6, "matching_screw_descriptors": 66,
             "matching_aperture_descriptors": 340, "cadquery_library_imported": True,
             "guarded_BREP_import_calls": 0, "actual_current_K_q_native_or_browser_run": False},
        ],
        "ownership_evidence": [
            {"path": relative(BANK / "panel_operators.py"), "lines": [111, 168, 188, 221],
             "observation": "Source closure and six current own observations precede historical-bank loading; refresh clears contact/q state and emits a non-release proof."},
            {"path": relative(FIX / "cli.py"), "lines": [23, 40, 56],
             "observation": "Exact frozen-bank pin, exclusive output admission before import, retained failure and re-raise."},
            {"path": relative(FIX / "check_source_seam.py"), "lines": [47, 50, 61],
             "observation": "Scoped BREP/K guards restore automatically and frozen inputs are checked before and after the source seam."},
            {"path": relative(BASE / "current-force-bridge-v1/bridge.py"), "lines": [46, 258, 384],
             "observation": "An existing deferred consumer pins this original bank/API; preserve its bytes and dependencies. The consumer was read only and not executed."},
        ],
        "retention": {
            "keep_active": "Current panel bank, corrected CLI/seam receipt, original receipts/tests, frozen raised-rail helpers and dependency assets, and this review.",
            "historical_boundary": "Original stale seam pin and output-admission failure remain preserved; the separate v2 supplement supplies current evidence.",
            "compactness": "Small source/JSON additions reuse shared numerical helpers and dependencies. No current BREP, mesh, operator bank or bulky run was produced.",
            "archive_or_delete": "None authorized or performed. Existing deferred bridge consumers prevent treating the original bank as disposable. Any later raw-run pruning needs the repository archive/restore verification workflow and parent-owned retention record.",
        },
        "next_actions": [
            "Use review-fix-v2/cli.py --out NEW_OUTPUT_PATH for future metadata plans; keep failed reserved outputs.",
            "Parent owns source-bound current observations, exact input artifact and method readiness before real bank construction.",
            "Run the real three-panel refresh only within that readiness scope; retain fresh-contact/load/frame-response and independent-admission obligations separately.",
        ],
        "limits": "No actual current BREP query, real panel/frame K, load/response q, native solve, browser run, acceptance, physical work or cleanup occurred in this review.",
        "release": dict(new["release"]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = check()
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(args.out), "sha256": sha(args.out),
                      "substantial_confirmed_findings": 0}))


if __name__ == "__main__":
    main()
