# Attempt07 architecture and integration review

Reviewed 2026-09-28. Scope is the frozen candidate packet's runner/verifier
boundaries, freeze and metadata hash binding, authorization/audit lifecycle,
one-run controls, parent trust assumptions, and offline validation. This review
does not assess contact mechanics or native solver results.

## Executive assessment

No candidate-level gate or hash/parse defect was found in this review. Attempt07
closes the attempt05 oracle snapshot gap: the runner and verifier parse frozen
JSON metadata from one byte snapshot and compare that digest with the exact
freeze map before relying on the parsed values. The freeze and terminal
manifests bind consistently, all 12 frozen artifacts match, the lineage pins
match their referenced source artifacts, and the 15-test offline suite passes.

The remaining execution-once boundary is explicit and parent-owned. The local
runner prevents a repeat while `execution.json` or `output/` remains, but that
guard can be reset by deleting those artifacts or using a copy. Parent
authorization and a durable serialized-run ledger must therefore be handled
outside this packet before any native launch. The candidate and parent gates
remain false; this review is not execution authorization.

## Architecture scores

| Area | Score | Basis |
|---|---:|---|
| Scope and module ownership | 4/5 | A one-case packet separates frozen inputs, the runner, shared authorization contract, and verifier. |
| Freeze and hash binding | 5/5 | Freeze, static metadata, readiness records, and authorization use same-byte parse/hash checks with freeze-map comparison. |
| Authorization and audit lifecycle | 4/5 | Exact authorization bytes are receipted and bound by root and case records; reviewer identity is an explicit external trust assumption. |
| Operational enforcement | 3/5 | Per-container/time/output limits and local repeat guard are explicit; cross-copy total-once control remains with the parent. |
| Offline testability | 4/5 | Fifteen deterministic gate, race, schema, and receipt tests run without Docker or solver setup. |

## Findings

1. **No internal gate or same-byte binding finding.** Runner static metadata
   validation reads `expected.json`, `source-snapshot.json`, `readiness.json`,
   and `parent-readiness.json` through `read_json_snapshot()` and checks each
   digest against the supplied freeze map before semantic use
   (`run.py:96-169`). Freeze creation stores those exact snapshot digests
   (`run.py:178-218`), and `verify_freeze()` reuses the same metadata check
   against the parsed freeze (`run.py:222-257`). The verifier follows the same
   pattern for its oracle and readiness metadata (`verifier.py:1164-1182`),
   then uses those captured digests when checking the complete frozen file map
   (`verifier.py:1241-1246`). Replacement-race tests cover both runner and
   verifier oracle snapshots, as well as freeze parsing
   (`tests/test_candidate.py:204-239, 266-298, 529-571`).

2. **Parent-owned condition — serialize and consume the total-run ledger.**
   The runner checks for existing root execution/output evidence and creates
   the output directory exclusively before starting the solver
   (`run.py:362-399`). This blocks repeat launches within a retained packet.
   Authorization is reusable, though, and deletion or a packet copy bypasses
   that guard. The README and freeze assign cross-deletion/copy tracking to
   the parent. Before future authorization, the parent coordinator must
   reserve and consume a durable ledger entry keyed to the exact freeze and
   authorization digest, including failed or interrupted attempts. This
   packet does not establish that an external ledger entry exists.

## Strengths and boundaries

- `authorization_contract.py` is shared by runner and verifier. Strict JSON
  parsing rejects duplicate keys and non-finite values, and the schema/runtime
  parity test checks the same authorization fixtures.
- The runner requires both candidate readiness snapshots to remain false,
  binds each exact snapshot to the freeze, and requires an external
  authorization file outside the packet. It hashes and parses those exact
  authorization bytes, then stores the same bytes exclusively as the receipt
  (`run.py:278-333`).
- The verifier rejects missing or symlinked receipts, hashes and parses the
  receipt once, validates all freeze/readiness/source/case bindings, and
  requires agreement between root and case records
  (`verifier.py:1111-1161`). Coupon pass output keeps mechanical acceptance,
  joint acceptance, and release false (`verifier.py:1290-1296`).
- The freeze limits the candidate to one case and one total run. It records
  one active native process, one CPU, 1 GiB memory and memory-plus-swap, 128
  container PIDs, a 60-second wall limit, 100 MiB total output, and 5 MiB per
  captured stream. The Docker command uses the pinned image, disables network
  access, applies the CPU/memory/PID caps, and sets solver thread counts to one
  (`input-freeze.json`, `run.py:392-429`). These are packet-level controls;
  global serialization remains parent-owned.
- Reviewer identity is trusted through the external parent authorization
  channel. The packet expressly makes no cryptographic-signature claim. The
  frozen scope is one static shared-slave penalty coupon only; it does not
  qualify full-joint or dynamic behavior, MORTAR, pointwise contact pressure,
  capacity, or release.

At review time, candidate and parent readiness, native execution
authorization, native solver launch, mechanical or joint acceptance, and
release are false. There is no external authorization, `execution.json`, or
`output/` in the candidate. No runner CLI, Docker command, or solver was
launched for this review.

## Offline verification

From the candidate directory, ran:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
```

Result: **15 passed**. The fail-closed test enters the runner gate with
`subprocess.run` and `subprocess.Popen` patched; other replacement probes use
temporary packet copies. No Docker or solver process was started.

The terminal and freeze binding check was run from the repository root:

```sh
python3 - <<'PY'
import hashlib, json, pathlib
b = pathlib.Path("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/contact-penalty-shared-slave-one-case-freeze-attempt07")
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
freeze = json.loads((b / "input-freeze.json").read_bytes())
terminal = json.loads((b / "terminal-hashes.json").read_bytes())
validation = json.loads((b / "validation.json").read_bytes())
actual = {name: sha(b / name) for name in freeze["files_sha256"]}
assert actual == freeze["files_sha256"]
assert terminal["input_freeze_sha256"] == sha(b / "input-freeze.json")
assert terminal["validation_sha256"] == sha(b / "validation.json")
assert validation["input_freeze_sha256"] == sha(b / "input-freeze.json")
print("12 frozen files match; terminal freeze/validation bindings match")
PY
```

The companion `integrity-manifest.json` records the resulting freeze,
terminal, validation, frozen-file, source-pin, and report hashes.
