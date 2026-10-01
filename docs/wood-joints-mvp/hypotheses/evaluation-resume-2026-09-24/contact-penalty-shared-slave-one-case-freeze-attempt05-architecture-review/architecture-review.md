# Attempt05 architecture and integration review

Reviewed 2026-09-28. This is a read-only review of the one-case freeze,
runner, authorization lifecycle, verifier, and offline tests. It does not
evaluate contact mechanics or qualify a solver result.

## Executive assessment

The packet has a clear one-case boundary and a mostly coherent integrity and
authorization chain. All 12 files named by the freeze match their declared
SHA-256 values; the freeze, terminal-hash, validation, input, oracle, and
upstream lineage pins also agree. The runner and verifier now bind the freeze,
readiness records, and external authorization to single byte snapshots, and
the verifier requires the exact authorization receipt in both root and case
records before it can return the coupon-only pass.

One medium integrity gap remains: the verifier parses `expected.json`, later
hashes the path in a separate read, and then uses the earlier parsed object to
judge solver output. The runner has a related separate-read sequence for
frozen metadata. This matters only under concurrent file replacement, but the
packet explicitly treats read/hash races as relevant for the freeze and
readiness records. Also, the one-run total is necessarily a parent-owned
operational limit: the packet's sentinel does not survive deleting output or
running a copy. The frozen gates are false and no authorization receipt,
execution record, or native output is present, so this review does not make
the candidate ready to run.

## Findings

1. **Medium — Frozen oracle bytes are not the bytes used by the verifier.**
   `verifier.py:1165` parses `expected.json` through `read_json()`, while
   `verifier.py:1175` later hashes the path independently. The parsed
   `expected` object is then used throughout the case audit, including to set
   the expected result and tolerances. Under a concurrent replacement, the
   path can hash to the frozen digest while the verifier retains a parsed
   object from other bytes. `run.py:223-225` similarly hashes each frozen
   artifact and then `verify_static_pins()` reopens the JSON metadata for
   parsing; `run.py:97-100` reads the oracle and source snapshot without
   comparing those exact byte digests with `files_sha256`. Use the shared
   snapshot reader for frozen JSON inputs, compare each returned digest to the
   exact freeze entry, and only then use the parsed values. Add a deterministic
   replacement probe for `expected.json` to the offline suite, analogous to
   the current freeze snapshot test.

2. **Medium integration condition — Total-once enforcement belongs to the
   parent run coordinator.** The runner blocks a second launch while
   `execution.json` or `output/` remains (`run.py:347-349`), and its exclusive
   output-directory creation prevents two invocations against the same
   retained packet from both starting the native process. The authorization
   is reusable and deleting those files or using a packet copy removes that
   local guard. The README and freeze correctly assign cross-deletion and
   cross-copy tracking to the parent. Before any future authorization, the
   parent must reserve and consume a durable serialized-run ledger entry keyed
   to this exact freeze and authorization digest, including failed or
   interrupted attempts. This candidate packet does not prove that such an
   external ledger entry exists.

## Architecture scores

| Area | Score | Basis |
|---|---:|---|
| Scope and module ownership | 4/5 | One-case packet with a shared authorization contract and separate runner/verifier roles. |
| Freeze and hash binding | 3/5 | Freeze and readiness use same-byte snapshots; frozen oracle parsing still has a read/hash gap. |
| Authorization and audit lifecycle | 4/5 | External authorization is exact-byte receipted and checked against both execution records. |
| Operational enforcement | 3/5 | Container caps are explicit; total-once behavior across copies and deletion is parent-owned. |
| Offline testability | 4/5 | Ten deterministic tests cover the gate and receipt chain without Docker or solver setup. |

## Strengths

- The freeze names an exact artifact inventory, source lineage, solver identity,
  one-case order, and explicit resource limits.
- A single shared authorization contract keeps runtime and audit semantics
  aligned, while the schema/runtime parity test checks their overlap.
- The receipt lifecycle distinguishes authorization from execution and keeps
  coupon results separate from mechanical acceptance, joint acceptance, and
  release.

## Next actions

1. Make each frozen JSON contract be parsed and hashed from one byte snapshot,
   then add a deterministic `expected.json` replacement test.
2. Before any native authorization, have the parent coordinator reserve and
   consume a durable serialized-run ledger entry keyed by freeze and receipt
   digests, including failed or interrupted attempts.

## Integration checks

- **Freeze and lineage pins:** input-freeze SHA-256 is
  `115c66e25969258c8cdd183e6c0c034a4ca872c392da7d0943a2287a3d3d83e0`.
  All 12 declared frozen files match. The deck, projected one-case oracle,
  upstream expected contract, projection parent, and route-review parent
  resolve to the recorded digests. The terminal manifest records the same
  freeze and validation digests.
- **Authorization lifecycle:** readiness and parent-readiness remain false.
  The runner verifies both readiness snapshots against the frozen digests
  using single-byte reads, accepts authorization only from outside the packet,
  parses and hashes the same authorization bytes, and persists those exact
  bytes as an exclusive receipt. The shared strict parser rejects duplicate
  keys and non-finite JSON numbers. The verifier rejects a missing, symlinked,
  or digest-mismatched receipt and validates its freeze, readiness, source,
  case, and gate bindings against both root and case records. Reviewer
  identity remains a documented external trust assumption; there is no
  cryptographic-signature claim.
- **Root/case records and claims:** the verifier checks that the root case
  inventory is exactly `shared_slave_penalty`, that the case execution file
  equals the embedded root record, and that the receipt digest and exact
  case-order bindings agree. The accepted verifier status is
  `PASS_SHARED_SLAVE_PENALTY_COUPON`; mechanical acceptance, joint acceptance,
  and release remain false in the run and verifier records. The scope is one
  static shared-slave penalty coupon, not full-joint behavior, dynamic
  contact, capacity, or release.
- **Process and output limits:** the freeze and runner agree on one case,
  one total run, one active native process, one CPU, 1 GiB memory with equal
  memory-plus-swap, 128 container PIDs, 60 seconds, 100 MiB total output, and
  5 MiB per captured stream. The Docker command pins the image, disables
  networking, limits resources, and sets solver thread counts to one. The
  runner monitors elapsed time and output size; the verifier checks the
  recorded command, terminal state, elapsed time, and output sizes. The
  parent still owns serialization across packet copies and deletable state.
- **Current state:** `execution.json`, `output/`, and an authorization record
  are absent. The candidate and parent readiness gates are false. No runner
  CLI, Docker command, or solver was launched during this review.

## Offline validation

Ran `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` from
the candidate directory: **10 passed**. The suite's fail-closed test exercises
the runner API with both subprocess entry points patched to raise; no Docker
or solver process was started. The tests cover same-byte freeze and readiness
checks, authorization/receipt parity, and root case consistency, but do not
probe a replacement race on `expected.json`.

## Subject hashes

The companion `integrity-manifest.json` binds this report to the candidate's
input-freeze, terminal manifest, validation record, and every frozen file.
