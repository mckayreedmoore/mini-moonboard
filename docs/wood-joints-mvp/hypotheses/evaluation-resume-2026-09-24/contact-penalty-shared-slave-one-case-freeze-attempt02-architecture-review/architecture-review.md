# Attempt02 one-case authorization architecture review

## Executive assessment

Attempt02 fixes the earlier transition dead end: both readiness snapshots stay false and immutable, while an external record must bind the exact freeze and both snapshots before the runner reaches Docker. The current hash chain is internally consistent, and the runner separates the pure authorization check from native execution. The remaining integration gap is at the audit boundary: `verifier.py` does not require or validate the authorization receipt, so its coupon `PASS` does not establish that the reviewed authorization path was followed. Parent identity is also an explicit external trust assumption, and the JSON Schema does not describe all runtime gate constraints.

## Scope and evidence

Reviewed the attempt02 package at `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/contact-penalty-shared-slave-one-case-freeze-attempt02/`, including its README, snapshots, freeze, authorization schema, runner, verifier, tests, validation record, and terminal hashes. This review was read-only except for this sibling report. No tests, Docker commands, or solver commands were run. No prior review report contents were opened; their referenced digests were not independently recomputed.

The freeze digest is `5bc91ad9f4ef2027609263752fd0d6e68f29284acd3f40e2f8bd541579c5499f`. All 10 files listed in `input-freeze.json` match their recorded SHA-256 values. The freeze and validation digests match `terminal-hashes.json`; its frozen-file inventory agrees with the freeze, and all five recorded gate values are false. The selected input, upstream expected contract, and projection-parent oracle each match the digest in `source-snapshot.json`. The route-review-parent and attempt01-audit digests are references to prior reviews and were not rehashed under this review's scope.

## Scores

| Area | Score | Evidence |
| --- | ---: | --- |
| Candidate and authorization separation | 4/5 | Frozen false snapshots remain unchanged; external authorization is outside the packet and binds the freeze and snapshots. |
| Run gate and operational limits | 4/5 | `assert_execution_ready()` precedes process calls; the run is limited to one case with fixed container limits. |
| Parent identity assurance | 1/5 | `reviewer` is a nonempty string; the package explicitly relies on an external authorized channel. |
| Verifier integration | 2/5 | Solver and frozen-input evidence are checked, but authorization receipt fields are not checked. |
| Authorization contract maintenance | 2/5 | Runtime checks are stricter than the published schema and duplicate-key parsing behavior is inconsistent. |

## Findings

### 1. The verifier does not carry the authorization gate through to its result — medium

The runner records `external_authorization_sha256` and the readiness snapshot hashes in its execution records (`run.py`, lines 451–476). The verifier's `audit_root()` checks the freeze, frozen files, solver identity, execution status, and case outputs (`verifier.py`, lines 1120–1207), but it never checks those authorization fields or opens a matching external authorization record. It can therefore emit `PASS_SHARED_SLAVE_PENALTY_COUPON` without demonstrating that the required parent authorization was supplied and matched the execution. This is an audit-chain gap, even though the normal runner path itself fails closed.

**Recommendation:** Make the verifier require the external authorization receipt (or an auditable receipt copied into the execution record), verify its exact bytes against the recorded digest, and check its freeze/readiness/source bindings before returning coupon `PASS`. Keep the result scoped to the coupon as it is now.

### 2. The JSON Schema accepts records that the runner rejects — low

The schema declares both authorization gates as arbitrary booleans and the UTC review time as any nonempty string (`external-authorization.schema.json`, lines 27–44). The runner instead requires both gates to be `true`, parses the timestamp, and requires UTC (`run.py`, lines 240–272). A schema-valid record can therefore fail at runtime, while two separately maintained definitions can drift. The runner also uses default `json.loads()` for authorization input (`run.py`, lines 79–80), which accepts duplicate object keys; the verifier's JSON parser rejects duplicate keys (`verifier.py`, lines 56–76), so the boundary does not use one consistent interpretation rule.

**Recommendation:** Align schema and runtime requirements, use one strict JSON loader that rejects duplicate keys, and add an offline contract check that proves the schema and runner accept the same authorization fixture. Because these files are frozen, any such change belongs in a newly frozen attempt.

### 3. The recorded reviewer field is not identity evidence — documented boundary

The gate only checks that `reviewer` is a nonempty string (`run.py`, lines 258–260). It does not authenticate the writer, verify a signature, or constrain the authorization file to a particular parent identity. The README explicitly discloses this and requires the file to come from the authorized parent-review channel (`README.md`, lines 52–57). That disclosure is accurate: the file's existence outside the candidate and its hash bindings establish content and scope, not who supplied it.

**Operational implication:** Treat parent-channel provenance as a required external control. Do not interpret the `reviewer` field or a successful pure gate check as proof of reviewer identity.

### 4. The authorization bytes are parsed and hashed in separate reads — low

`load_external_authorization()` returns `read_json(resolved)` and then `sha(resolved)` (`run.py`, lines 307–317). If the external file changes between those reads, the gate can validate one JSON object while recording the digest of different bytes. This undermines the receipt hash's audit meaning under concurrent modification.

**Recommendation:** Read the file once into bytes, calculate the digest from those bytes, and parse that same byte string. Apply the same snapshot pattern to any evidence whose parsed meaning and digest must identify one exact version.

## Strengths

- The immutable candidate retains false readiness snapshots and freezes the runner, verifier, schema, test, source manifest, oracle, and deck.
- The external authorization binds the exact freeze, false readiness snapshots, one-case scope, and source input/oracle pins; acceptance and release claims are explicitly required to remain false.
- The execution path invokes the pure gate before Docker/process calls, refuses an existing output path, and records bounded one-case resource limits.
- The code and documentation correctly state that this authorization covers only the coupon and does not prove a joint, capacity, or release result.

## Next actions

1. Close the verifier-to-authorization evidence gap before treating a verifier `PASS` as proof of an authorized run.
2. Align and test the schema, runtime parser, and duplicate-key behavior in a new freeze.
3. Preserve the parent-review channel as an explicit trust boundary unless the workflow adds an identity-verifiable receipt.
