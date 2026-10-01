# Shared-slave penalty coupon: one-case freeze candidate

## Status and scope

This is an isolated candidate freeze, runner, and verifier for exactly one
method coupon: `shared_slave_penalty`. Parent readiness and native execution
authorization are both false. The runner refuses native execution in this
state. No native solver or Docker run was performed while preparing this
candidate.

The coupon contains one small static, surface-to-surface penalty topology with
two perpendicular contact pairs whose slave surfaces share an edge. A pass
would qualify only this small static shared-slave penalty topology under its
frozen known-answer contract. It would not qualify full-joint behavior,
implicit-dynamic behavior, MORTAR, pointwise contact pressure, joint capacity,
or release.

## Exact pins

The sole deck is byte-identical to the prepared source deck:

- Input: `input/shared_slave_penalty.inp`, SHA-256
  `d7e517bca0a63fc02bbb77bae8116bc2b014b3545a5c40566e64cdaac47668e7`.
- Upstream expected-contract pin recorded by the route-review parent: SHA-256
  `29ce26d69e94579fb49af86b8608e0b001310f670a294eb596997a3ce2b538b0`.
- The one-case oracle is a projection of the reviewed two-case penalty
  contract. Its own SHA-256 is
  `8c0344c1c7f98976cd1636532eb73925c9c896917c5110729834c816e4c0c9da`.
- The two-case parent-oracle artifact used to form that projection has SHA-256
  `16c1df001392376d084d8c2d021ce8a884bfb96ea56bbdf528275b476f974c45`.
- Route-review parent packet `parent-review.json` SHA-256 is
  `64feedb7f3746d6ebba0dc15d8cc0472ba8d2958bd564c7c25708b6d30d2e840`.

`source-snapshot.json`, `expected.json`, and `input-freeze.json` preserve these
source, input, and candidate-oracle pins separately. The upstream oracle pin is
lineage evidence; the projected one-case oracle has its own frozen digest.

## Execution boundary

The candidate freeze permits at most one case, one run, and one active native
process. The runner has fixed CPU, memory, wall-time, process-count, log-size,
and total-output limits; it stops at the first failure and never retries. It
creates output paths exclusively, refuses any existing run output, and checks
frozen input hashes before and after a run. Captured run artifacts are retained
for verification and are not overwritten by a rerun.

The parent readiness record is deliberately `NOT_REVIEWED`, with
`parent_readiness: false`. The runner needs a separately reviewed freeze hash
and explicit true authorization/readiness values before its guarded execution
path could proceed. Such a change requires a new reviewed candidate and
freeze; this packet itself remains a non-executable readiness candidate.

Offline checks can be run with:

```sh
python3 -m unittest discover -s tests -v
```

These checks only validate pins, one-case scope, and fail-closed behavior. They
do not execute a solver or establish a physical result.
