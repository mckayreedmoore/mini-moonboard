# Independent test-coverage review: attempt02

## Scope and result

Reviewed `contact-penalty-shared-slave-one-case-freeze-attempt02` read-only. I did not open prior review reports. Referenced lineage files were checked by digest only. No authorization record was created, no candidate file was changed, and no Docker or native solver command was invoked.

Every recorded frozen-file hash matched both `input-freeze.json` and `terminal-hashes.json`. The freeze SHA-256 is `5bc91ad9f4ef2027609263752fd0d6e68f29284acd3f40e2f8bd541579c5499f`; the recorded validation SHA-256 is `107c15d8f09ba3c55488634c460222acb607f2b34f1e8331bda34f8d2b3603a9`. The selected deck, upstream expected contract, one-case parent oracle, and route-review parent digests also matched their pins. The packet currently has no external authorization JSON, `execution.json`, or `output/` directory.

The documented offline suite passed all four tests with `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v`. The runner's unauthorized path was stopped before either `subprocess.run` or `subprocess.Popen`, as the tests claim.

## Finding: root verifier does not require authorization evidence

The runner gates execution on an external authorization record and stores its digest in the run record (`run.py`, lines 346–354 and 455–458). `verifier.audit_root()` checks the freeze, source pins, execution status, limits, and output audit, then returns `PASS_SHARED_SLAVE_PENALTY_COUPON` (`verifier.py`, lines 1120–1207). It never checks `external_authorization_sha256`, requires it to be non-null, or verifies a supplied authorization record against the freeze and readiness hashes.

I reproduced this seam in a disposable `/tmp` copy: a synthetic root execution record with no authorization hash and no external authorization file reached `PASS_SHARED_SLAVE_PENALTY_COUPON` when `audit_case` was stubbed to pass. The stub isolated the root-level authorization gate; this did not simulate solver output validation or run a solver. The production result therefore is not independently bound by the verifier to the authorization that the runner was meant to require.

The offline tests do not import or call `verifier.py`. Before treating a verifier pass as evidence from an authorized run, add a verifier precondition that checks the parent authorization against the frozen candidate, with a regression case for a missing record/hash and mismatched authorization. The record can remain outside the candidate packet as required by the README; the verifier needs an explicit external input or another auditable binding.

## Coverage details

The current four tests cover false candidate readiness, a positive in-memory authorization gate, readiness/freeze hash mismatches in the authorization payload, and false external gates. A separate pure-function probe exercised 17 additional authorization rejection variants; all 17 were rejected. Those variants covered non-object input, schema/status/extraneous-field errors, record paths, case and source pins, empty reviewer/timestamp, invalid or non-UTC timestamps, and forbidden execution/acceptance/release claims. These checks currently lack dedicated tests.

The suite also does not exercise `verify_freeze()` rejection for a wrong caller-supplied freeze digest, rejection when a frozen artifact digest differs, or `load_external_authorization()` rejecting a path inside the packet. I exercised those three branches read-only; each rejected as intended. The verifier's input-only deck audit passed independently for the frozen 81-node, 18-element deck. The native-output parsers and known-answer checks remain untested here because this packet correctly has no run outputs.

## Verification record

- Candidate frozen files: all hashes matched the candidate freeze and terminal manifest.
- Lineage pins: selected input `d7e517bca0a63fc02bbb77bae8116bc2b014b3545a5c40566e64cdaac47668e7`; upstream expected contract `29ce26d69e94579fb49af86b8608e0b001310f670a294eb596997a3ce2b538b0`; one-case parent oracle `16c1df001392376d084d8c2d021ce8a884bfb96ea56bbdf528275b476f974c45`; route-review parent `64feedb7f3746d6ebba0dc15d8cc0472ba8d2958bd564c7c25708b6d30d2e840`.
- Offline suite: 4 passed, 0 failed.
- Additional authorization negatives: 17 rejected, 0 unexpectedly accepted.
- No-run boundary: no authorization file, execution record, or output directory; Docker and native solver not invoked.
- Review scope limitation: the post-run output contract was not exercised against real or synthetic solver outputs.
