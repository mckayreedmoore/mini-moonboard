"""Bind the narrowed browser-helper scope to the unchanged architecture review."""

import hashlib
import json
import sys
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


own = Path(__file__).resolve().relative_to(Path.cwd())
prior_path = own.parent / "receipt.json"
prior_bytes = prior_path.read_bytes()
assert sha(prior_bytes) == "a27fef5eddad323464a7c4960019284b37ac367097a8deb63a4c8e242e811b4e"
prior = json.loads(prior_bytes)
browser_path = Path("scripts/check_eoere_cleat_extension_browser.cjs")
browser_bytes = browser_path.read_bytes()
assert sha(browser_bytes) == "7295c57ed3d06d3587e1de7a95da747a0bb8e3f0ae37b87bb95bc3b1a793c3ba"
unchanged = {path: digest for path, digest in prior["source_sha256"].items() if path != str(browser_path)}
for path, digest in unchanged.items():
    assert sha(Path(path).read_bytes()) == digest, "prior architecture source changed: " + path
production = [
    "site/index.html", "site/eoere-cleat-extension-overlay.mjs", "site/eoere-cleat-extension-scene.json.gz",
    "docs/wood-joints-mvp/README.md", "docs/wood-joints-mvp/completion-ledger.md",
    "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-extended-cleats-v1.json",
]
pins = {path: prior["source_sha256"][path] for path in production}
pins.update({str(prior_path): sha(prior_bytes), str(browser_path): sha(browser_bytes), str(own): sha(own.read_bytes())})
receipt = {
    "schema": "eoere_extended_cleats_architecture_supplement/v1",
    "status": "NO_SUBSTANTIAL_ARCHITECTURE_FINDINGS",
    "source_sha256": pins,
    "unchanged_prior_source_bindings_verified": len(unchanged),
    "prior_architecture_assessment_remains_applicable": True,
    "browser_helper_boundary": {
        "source": "scripts/check_eoere_cleat_extension_browser.cjs:34",
        "actual_declared_scope": "Load the new base model from the rear; check current navigation, provisional label, preserved option presence and display census; capture base and checkbox-enabled extra mode; return to base; check errors and failed requests.",
        "claims_source": "scripts/check_eoere_cleat_extension_browser.cjs:57",
        "assessment": "Result fields describe the new pair's off/on/off transition and preserved option presence. They do not claim a repeated historical toggle sweep, front capture or structural acceptance. Shared screenshot tooling remains the only runner operation.",
    },
    "findings": [],
    "limits": [
        "Static review of the narrowed helper and source preservation only; this receipt does not assert browser-v3 success or reproduce screenshots.",
        "Existing review helper and receipt remain frozen. Parent retains failed/stopped browser evidence and owns final browser validation and publication.",
        "No browser/CAD/BRep/native/full-suite run, shared edit, staging, mechanics transfer or physical release."
    ],
    "reproduction_command": [sys.executable, str(own)],
}
assert browser_path.read_bytes() == browser_bytes
assert prior_path.read_bytes() == prior_bytes
out = own.with_suffix(".json")
assert not out.exists(), "preserve previous supplements"
out.write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps({"receipt": str(out), "sha256": sha(out.read_bytes()), "unchanged_sources": len(unchanged), "findings": 0}))
