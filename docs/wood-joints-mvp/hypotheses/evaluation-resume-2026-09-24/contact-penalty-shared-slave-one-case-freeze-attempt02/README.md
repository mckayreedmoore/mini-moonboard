# Shared-slave penalty coupon: one-case freeze candidate, attempt02

## Status and scope

This immutable candidate contains one method coupon: `shared_slave_penalty`.
Its frozen `readiness.json` and `parent-readiness.json` remain false, and the
packet contains no external authorization record. Parent readiness and native
execution authorization therefore remain false. Preparation made no native
execution and no Docker or solver call; offline tests exercise only the
fail-closed runner path and pure authorization check.

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

`source-snapshot.json` preserves those lineage pins. `input-freeze.json`
hashes every candidate input, including the false readiness snapshots,
authorization schema, runner, verifier, tests, README, oracle, source snapshot,
and deck. It also fixes the one-case scope, solver identity, and resource
limits. Its exact SHA-256 is recorded in `terminal-hashes.json`.

## Authorization lifecycle

Attempt01 froze the pending false readiness records and then required those
same files to become true, which made an authorized transition impossible.
Attempt02 keeps both readiness records immutable and false. After independent
review, the parent can provide a separate authorization JSON outside this
packet. That record must name the exact `input-freeze.json` hash, the exact
`readiness.json` and `parent-readiness.json` hashes, the sole case and source
pins, and explicit parent-readiness and native-execution authorization gates.
The field contract is documented in
`external-authorization.schema.json`; `run.py` checks it with the pure
`check_external_authorization()` function before any Docker or process call.

The external record is not present here and the current false snapshots are
not approval. The code checks the declared fields and their hash bindings; it
does not authenticate the reviewer's identity or provide a digital signature.
The record must come from the authorized parent-review channel. A review or
authorization of this packet would still authorize only the bounded one-case
method coupon, not a physical joint, a design, or climbing use.

The execution gate accepts a parent authorization file outside the packet:

```sh
python3 run.py run --freeze-sha <exact-freeze-sha256> \
  --authorization-json /path/outside/packet/parent-authorization.json
```

The one-case freeze allows at most one run and one active native process, with
fixed CPU, memory, wall-time, process-count, log-size, and total-output caps.
The runner stops at the first failure, refuses existing output, and checks the
frozen input hashes before and after execution. No execution output exists.

## Offline validation

Run the offline suite from this directory:

```sh
python3 -m unittest discover -s tests -v
```

It checks the exact source and freeze pins, confirms the candidate readiness
files remain false, proves the runner stops before any Docker/process call in
that state, and proves a correctly bound external authorization passes the
pure gate without Docker/process calls. Mismatched hashes and false external
gates fail closed. These checks do not execute a solver or establish a
mechanical result. Results and terminal file hashes are recorded in
`validation.json` and `terminal-hashes.json`.
