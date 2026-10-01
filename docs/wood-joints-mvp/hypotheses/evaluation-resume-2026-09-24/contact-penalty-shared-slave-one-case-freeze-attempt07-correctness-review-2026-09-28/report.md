# Attempt07 correctness review

Reviewed candidate freeze: `c4cc230277d321d5fdf5e255270291cbc5825adaa3829632a5a774240d62a775`.

## Disposition

The requested gate review passes for the current frozen bytes. I found no
blocking correctness issue in the authorization, readiness, snapshot, receipt,
root/case, or failure gates. This is an offline evidence-chain review; it does
not authorize execution or establish a mechanics result.

## Integrity and test evidence

All 12 hashes in `input-freeze.json` match the candidate and both
`terminal-hashes.json` and `validation.json`. The freeze digest is
`c4cc230277d321d5fdf5e255270291cbc5825adaa3829632a5a774240d62a775`; the
validation digest is
`c9127e0f226ea883d441f0a0a175b6754a7e19c8c749293927eedaaaa518ece6`; and the
terminal-manifest digest is
`69ceb7ff3ca8df2311328d6dfc5600f7d8934e7f97c93c930410eaf2ab99652a`.
All four external source-lineage pins match their files. The attempt06 freeze,
validation, terminal, and preserved-file links also match the attempt06
manifest; that manifest's attempt05 chain points to the recorded prior
artifacts and reports.

I ran the declared offline command from the candidate directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

It completed with 15 tests passing and no failures. The only test calling
`run.run()` is the false-readiness test, which patches both
`subprocess.run` and `subprocess.Popen` to raise if reached. The other tests
call pure gate/metadata functions or construct fixtures in temporary
directories. The suite made no Docker, solver, or native call and left no
execution record, output directory, or authorization receipt in attempt07.

For an independent strict-parser probe, the following was run with
`python3 -B` against attempt07's frozen `authorization_contract.py`:

```python
from authorization_contract import AuthorizationError, parse_json_bytes

invalid = [
    b'{"a":1,"a":2}',
    b'{"a":{"b":1,"b":2}}',
    b'{"x":NaN}', b'{"x":Infinity}', b'{"x":-Infinity}',
    b'{"x":1e999}', b'{"x":-1e999}', b'{"x":"\xff"}',
]
for raw in invalid:
    try:
        parse_json_bytes(raw)
    except AuthorizationError:
        pass
    else:
        raise AssertionError(f"accepted invalid JSON: {raw!r}")
assert parse_json_bytes(b'{"x":-1.25e2}') == {"x": -125.0}
```

All invalid inputs were rejected; the finite value was accepted.

## Gate review

`authorization_contract.read_json_snapshot()` reads a file once, then parses
and hashes those same bytes (`authorization_contract.py:71-74`). The runner
uses it for the input freeze and for all four static JSON metadata files. It
compares each metadata digest with the freeze before consuming parsed values,
uses the expected-oracle snapshot's digest against the fixed oracle pin, and
uses the captured static metadata digests when creating a freeze
(`run.py:96-169, 178-219, 222-257`). Its deterministic replacement test changes
`expected.json` after the read while restoring the path; the captured altered
bytes are rejected against the frozen digest before the parsed oracle is
accepted (`tests/test_candidate.py:204-239`).

At audit time the verifier reads and hashes the freeze and each of the four
metadata JSON files from single snapshots. It rejects a changed hash, enforces
false freeze-time gates and false readiness gates, checks the oracle's fixed
digest, and then validates the remaining frozen artifact map
(`verifier.py:1164-1193, 1235-1246`). Its altered-oracle replacement test
confirms the verifier does not parse one version and hash a later restored
version (`tests/test_candidate.py:529-571`).

Readiness remains false in both frozen snapshots. The runner compares their
same-read digests with the verified freeze and checks their false values
before requiring and validating an external authorization
(`run.py:278-309`). The external record must be outside the candidate packet;
its parsed object, original bytes, and digest come from one read. The runner
checks that digest before exclusive receipt creation
(`run.py:312-333`). The verifier independently binds false candidate and
parent readiness snapshots, false freeze-time gates, the receipt, source
hashes, and one-case scope. It reads, hashes, and parses the same receipt
bytes, requires the digest in both execution records, and validates all
authorization fields (`verifier.py:1111-1161, 1184-1193`).

The root record must name exactly the one case and contain exactly one run.
The verifier checks the root and nested-run freeze, readiness, authorization,
source, receipt, and false acceptance/release fields. During case audit it
requires the nested run record to equal the per-case `execution.json`
(`verifier.py:1045-1049, 1111-1161, 1216-1278`). The suite adds asymmetric
root/run mutations for receipt and readiness bindings and rejects a
contradictory root case list (`tests/test_candidate.py:573-662`).

The runner reaches Docker inspection only after freeze validation, readiness
and external authorization checks, output/replay guards, and one-case checks
(`run.py:362-381`). A missing authorization fails while readiness is false,
before any subprocess call; the suite patches and checks both subprocess
entry points for this path (`tests/test_candidate.py:300-309`). Failures in
the coupon launch/capture path and timeout or resource-limit stops are
recorded as `failed_or_stopped` or `capture_exception`; the verifier accepts
only a completed run with successful terminal state and within-limit evidence
(`run.py:405-475`; `verifier.py:1045-1083, 1255-1304`). Earlier Docker
image/binary pin-probe failures abort before the coupon process starts.
Exceptions at the root audit boundary become `FAIL` with mechanical
acceptance, joint acceptance, and release false.

## Boundaries

The local one-run guard depends on retaining `execution.json` or `output/`;
deletion and packet copies permit reuse, so parent-owned serialized run
tracking remains required. Reviewer identity is trusted through the external
parent channel; no cryptographic signature is claimed. Candidate readiness,
parent readiness, native authorization, native launch, mechanical/joint
acceptance, and release remain false. No native runner launch, Docker call,
solver, or native process occurred. The offline suite invoked `run.run()` only
for its false-readiness test, with both subprocess entry points patched, and
used pure gate functions and temporary fixtures for its other runner paths.

See `review-manifest.json` for the report digest and complete frozen-file
hash map.
