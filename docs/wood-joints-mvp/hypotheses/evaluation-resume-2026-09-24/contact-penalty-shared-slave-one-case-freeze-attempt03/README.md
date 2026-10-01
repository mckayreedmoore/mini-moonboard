# Shared-slave penalty coupon: one-case freeze candidate, attempt03

## Status and scope

This immutable candidate contains one method coupon: `shared_slave_penalty`.
Its frozen `readiness.json` and `parent-readiness.json` remain false, and the
packet contains no external authorization record. Parent readiness and native
execution authorization therefore remain false. Preparation made no native
execution and no Docker or solver call; offline tests exercise only gate,
receipt, schema, and verifier authorization checks.

The coupon is one small static surface-to-surface penalty topology with two
perpendicular contact pairs whose slave surfaces share an edge. A passing
result could qualify only this frozen coupon under its known-answer contract.
It would not qualify full-joint behavior, implicit-dynamic behavior, MORTAR,
pointwise contact pressure, joint capacity, or release.

## Pins and immutable input freeze

The sole deck is byte-identical to the prepared source deck:

- `input/shared_slave_penalty.inp`: SHA-256
  `d7e517bca0a63fc02bbb77bae8116bc2b014b3545a5c40566e64cdaac47668e7`.
- Upstream expected-contract pin: SHA-256
  `29ce26d69e94579fb49af86b8608e0b001310f670a294eb596997a3ce2b538b0`.
- One-case oracle: SHA-256
  `8c0344c1c7f98976cd1636532eb73925c9c896917c5110729834c816e4c0c9da`.
- Two-case projection parent oracle: SHA-256
  `16c1df001392376d084d8c2d021ce8a884bfb96ea56bbdf528275b476f974c45`.
- Route-review parent packet: SHA-256
  `64feedb7f3746d6ebba0dc15d8cc0472ba8d2958bd564c7c25708b6d30d2e840`.

`source-snapshot.json` preserves these lineage pins. `input-freeze.json`
hashes the candidate inputs, including both false readiness snapshots, the
authorization JSON Schema and shared validator, runner, verifier, tests,
validation dependency pin, README, oracle, source snapshot, and deck. It fixes
the one-case scope, solver identity, and resource limits. Its exact digest and
the validation and terminal-manifest digests are recorded in
`terminal-hashes.json`.

## Authorization, receipt, and audit lifecycle

The candidate's readiness snapshots remain immutable and false. After
independent parent review, an authorization JSON may be supplied from outside
this packet. It must bind the exact freeze, readiness snapshots, source pins,
single case, UTC review timestamp, and explicit authorization gates. The
record is not persisted in this candidate. Reviewer identity remains an
external parent-channel trust assumption; the contract does not invent or
claim a cryptographic signature.

`authorization_contract.py` provides the shared strict JSON parser and
semantic authorization validator used by both `run.py` and `verifier.py`.
The runner reads external authorization bytes once, hashes and parses that
same byte snapshot, then carries those exact bytes into
`output/shared_slave_penalty/parent-authorization.json`. Both case and root
execution records bind the receipt digest, freeze and readiness hashes,
source pins, case order, and gate values. The verifier must find the receipt,
recompute its digest from the bytes it parses, compare that digest with both
execution records, and validate every binding before it can return
`PASS_SHARED_SLAVE_PENALTY_COUPON`.

`external-authorization.schema.json` fixes the gates and prohibited claims
with `const` values and constrains `reviewed_at_utc` to RFC 3339 UTC. An
offline parity fixture checks the schema and runtime against the same valid
and invalid records; the runtime additionally binds well-formed dynamic hash
fields to this exact freeze and its readiness snapshots. Duplicate JSON keys
and non-finite numbers are rejected.
The validation suite uses the pinned `jsonschema` dependency in
`requirements-validation.txt`.

If a later parent review explicitly authorizes execution, the runner interface
is:

```sh
python3 run.py run --freeze-sha <exact-freeze-sha256> \
  --authorization-json /path/outside/packet/parent-authorization.json
```

The one-case freeze allows at most one run and one active native process, with
fixed CPU, memory, wall-time, process-count, log-size, and total-output caps.
The runner stops at the first failure, refuses existing output, and checks the
frozen input hashes before and after execution. No execution output exists.

## Offline validation

Run the offline suite from this directory in an environment with the pinned
`jsonschema==4.10.3` validation dependency:

```sh
python3 -m unittest discover -s tests -v
```

The suite verifies source and freeze pins, false readiness gates, early runner
blocking, same-byte strict authorization parsing, schema/runtime parity, and
root-verifier receipt requirements for missing and mismatched evidence. Its
synthetic root-audit fixture stubs only the per-case mechanics audit to isolate
the authorization gate; it is not solver-output evidence. These checks do not
execute a solver or establish a mechanical result. `validation.json` and
`terminal-hashes.json` record the offline results and terminal hashes.
