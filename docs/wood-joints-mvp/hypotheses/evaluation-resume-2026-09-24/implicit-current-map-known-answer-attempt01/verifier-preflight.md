# Independent verifier and runner preflight

Review date: 2026-09-27. Read-only review of the verifier, acceptance contract,
prepared inputs, and parent runner. No freeze or native solve was performed.
This is bounded method evidence for one current-map coefficient set; it is not
joint acceptance or release. At review time `acceptance.ready_for_native` was
false. The parent retains execution ownership and the current handoff hold.

## Snapshot and checks

The reviewed bytes were:

| Artifact | SHA-256 |
|---|---|
| `verifier.py` | `864ed594c7f324706c2308637e5cf4b25de8910ca6b4a54199fc55ec8b546e4a` |
| `run.py` | `28f0d0221fb10e8e864b0c7c4fbb85e758586bfaf6bc4230d98650b1c215ae91` |
| `acceptance.json` (pre-readiness flag) | `415d3a8ee6b9252ed63e85823de0890b2bc5415f6607eed7838eaead7a222ac2` |
| `expected.json` | `88521d8367b2ea33c170c3c82a1a417b2fa481cf2afd7afc01558b0b7053172a` |
| `prepare.py` | `17d327a9372c4476ce0d7fd97e2f681df5e99b95f849892080b5c3ab7ed81009` |
| `parent-input-audit.json` | `b3e2241be363ce8c42e375c797f1a11ccd676ddf5c994590e28fdfa2b1bece26` |
| Pinned CalculiX source archive | `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7` |
| Parser helper `explicit-c3d10-mpc-known-answer-attempt01/verifier.py` | `e42c5e0b9ced533b461bc984e39d7a0d5081c45ddb1022206251bf7fbe909620` |

Read-only checks passed: `.venv/bin/python -B prepare.py --check` reproduced
the expected SHA and all three deck hashes; `.venv/bin/python -B verifier.py
--self-test` returned `PASS_SYNTHETIC_CONTROLS` with `native_run_performed:
false`; and `parent-input-audit.py` returned `PASS_OFFLINE`. The independent
input audit verified 22,696 CLOAD rows per case, with maximum component
difference `1.3962808739895107e-21 N`, and confirmed the original six mapped
equations and M03 output card. The independent mass reference and rigid-mode
deviation checks ran without native execution. The runner's `--check` was not
run because it requires the parent readiness record and this preflight file;
the parent can run it after binding the completed review. No `--freeze` or
`--run` command was invoked.

## Verifier findings

The final verifier closes the defects found in the draft review. Its Decimal
precision and accumulation reserve are checked against the numeric acceptance
fields in `load_contract()` (`verifier.py:126-139`). DAT synthetic records use
the pinned `E13.6` precision; FRD synthetic records use `E12.5`. The FRD gate
checks the `DISP` D1/D2/D3/ALL and `VELO` V1/V2/V3/ALL component labels, and
negative controls exercise changed labels, wrong axis, duplicate and
non-finite output. The source-shaped M03 zero-mass auxiliary inertia and
centroid rows may contain NaNs; required ELPRINT and nodal channels remain
strictly finite, and the negative required-energy control is rejected.

Accepted-state evidence is complete and fail-closed for this fixed schedule.
`parse_sta()` requires the header, ten unique step-1 increments in order,
attempt 1, positive iteration count, and scheduled times/dt; it now rejects
malformed numeric rows instead of skipping them (`verifier.py:1157-1199`).
Synthetic negatives cover missing and duplicate accepted rows, retry marker
`1U`, wrong time/dt, and an extra truncated numeric row. DAT and FRD frames
must map to those accepted times. FRD identities must identify the same step
and increment.

The native audit requires exact, complete per-state node and field inventories:
11348 physical nodes; two free control nodes in DAT; and, in the carrier case,
all 1107 carrier nodes. The expected DAT counts are 11348, 11350, and 12457;
expected FRD counts are 11348, 11348, and 12455 because the two unmeshed
controls do not appear in FRD. U/V, energy sets, duplicate records, unexpected
fields, DAT/STA/FRD times, and output hashes all fail closed. The synthetic
test deliberately reduces physical coverage to the full 251-node fit and
equation nodes and the carrier to four nodes; it tests parsing and gates, not
full mesh coverage. The native-path audit still requires every expected node
at all ten states.

Each mapped capture checks the six measured REF/ROT controls both against the
original 251-node weighted fit and against the predeclared small-rotation
reference. The M03 carrier displacement and velocity are checked at every
carrier node using the pinned Rodrigues rotation and rotation-vector
derivative with the measured controls. The six original equation residuals
are checked at every accepted displacement state using actual DAT lexemes,
coefficient representation error, `gamma_(2n)` arithmetic allowance, and the
declared Decimal reserve. Direct-to-mapped-no-carrier and
mapped-no-carrier-to-carrier comparisons include both DAT and FRD fields plus
body energy and control parity. The two printed records' independent half-ULP
allowances are included; zero-valued scientific tokens are treated as numeric
zero, while nonzero tokens use their printed exponent and final digit.

The numerical criteria remain a pre-run qualification proposal. The all-node
rigid-versus-linear comparison bounds used to select absolute floors are
`8.30e-13 mm` and `4.89e-10 mm/s`; the respective DAT floors are `2e-12 mm`
and `1e-9 mm/s`, with 5 ppm DAT and 6 ppm FRD relative tolerances. These
compare an observed response with a rigid-mode reference and do not prove an
elastic-error bound.
The contract is limited to one M00 A00 map, one small one-axis forcing, and an
optional zero-density M03 carrier. It does not qualify the other current maps,
arbitrary inertia modes, contact behavior, joint capacity, or release.

## Runner and execution boundary

The parent runner binds local files and external dependencies, replays the
verifier self-test for `--check` and `--freeze`, checks generated inputs and
independent source references, and requires the parent review plus exact
readiness hashes. It then requires an exact freeze SHA for serialized direct,
mapped-no-carrier, and mapped-carrier cases. Its pinned execution envelope is
one CPU, one GiB memory with no swap, no network, one solver thread, 120 seconds
per case, and a 64 MiB per-case output cap. It records each file hash and
requires normal container exit and the CalculiX completion marker. The
verifier rechecks the frozen local inventory, listed external dependencies,
input/output manifests, timing order, completion status, and case ordering;
the flat native-output contract is narrower than the runner's recursive hash
capture and is consistent with these solver outputs. All acceptance, joint,
and release flags remain false.

The packet is not yet executable from this review alone: the parent must add
its readiness record and verifier self-test record, set the readiness flag
after the separate handoff decision, and run the read-only runner check before
any freeze. This review does not authorize or perform those parent-owned
actions.

## Correction to the earlier reference note

`reference-preflight.md` remains unchanged at SHA-256
`f6d026f20324bdb05eedc93fe910ebcb8e5ac9a779cabd4adb82345feb821df7`. Its
sentence at lines 55-57 saying the independent reference and input producer
both use the solver's quadrature literal is inaccurate. `prepare.py:407-408`
uses the source literal `0.041666666666667`; `parent-mass-reference.py:139-140`
uses exact mathematical `1/24`. The literal is higher by
`3.3306690738754696e-16` (relative `7.99e-15`). This produces approximately
`9.18e-15` relative difference in mass and `1.10e-14` in Iyy, not a geometry
or load-path difference. The producer and independent CLOAD audit use the
solver literal; the separate parent mass reference retains exact `1/24` and
quantifies its tiny difference. The source member `gauss.f` SHA-256 is
`aed2d48b6a63e30894e747a531f6edc32e3cd921338e370902dfb62d8e304df2`.

The zero-mass auxiliary-output interpretation is pinned to `printout.f`
SHA-256 `ae2b60b4e086846e2833a1d723c37645c0ff6701d2e28dc7e3163d0a4d136f32`;
the DAT nodal `E13.6` format is pinned to `printoutnode.f` SHA-256
`ed77454fbf771c38ebbb32f0785013dae3585eca50e5cc7b28c646dec0ce4b94`.
