# C3D10 section and nodal-stress output coupon

## Status and scope

Prepared for parent review. No solver was launched for this packet. It starts
from the frozen SECTION attempt01 pair and adds only one element-file output
request to each of its three steps. Mesh, materials, contact, supports, motion,
static schedule, and the inherited SOF and mechanical gates are unchanged.

The preserved [attempt01](../contact-section-force-known-answer-attempt01/README.md)
completed both cases with native exit code zero, exact DAT U/RF and STA/CVG
parity, and passing SOF checks. Its verifier records `FAIL` with the error
`Baseline mechanical/provenance gates fail`. The accompanying output audit
found incomplete penalty stress coverage: 14 of 54 nodal records at compression
and none at opening or reopening. Its freeze, execution, verifier source and
failed result hashes are pinned in `expected.json`.

This is an output-method fixture only. It does not qualify the contact law,
wood joint, or full joint model. Nodal stress is a completeness/finite-value
gate; values are not interpreted as contact traction or a joint capacity.

## Output-only change and source basis

Immediately before each `*END STEP`, both decks now request:

```text
*EL FILE,FREQUENCY=1
S
```

With one accepted increment per fixed step, frequency 1 requests the three
accepted step-end states. The pinned CalculiX 2.23 parser maps `FREQUENCY=` to
the output interval and `S` to element stress. It extrapolates stress to nodes
and writes six `STRESS` components: `SXX`, `SYY`, `SZZ`, `SXY`, `SYZ`, and
`SZX`. Version 2.23 also enables `ERR` when `S` is requested; this incidental
field is not an acceptance gate.

The manual and source archive hashes, plus the `noelfiles.f`,
`resultsprint.f`, and `frd.c` member hashes, are recorded in `expected.json`.
The input producer verifies those members against the frozen source archive.
The referenced [official 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf)
describes `*EL FILE` in §7.

## Predeclared output gates

For both MORTAR and matched surface-to-surface penalty cases, each of the
three accepted step-end `STRESS` datasets must contain every one of the 54
model node IDs exactly once. All six components at every node must be finite.

All attempt01 section-resultant and mechanical gates remain unchanged,
including the two SOF face reports per step, section force/moment/area checks,
endpoint force and compliance, displacement profile, exact DAT U/RF and STA/CVG
parity, one accepted increment per step, and the MORTAR iteration cap of 14.

## Records and next action

`prepare.py` verifies the passed fullstep baseline and failed section attempt01
freezes, executions, verifier artifacts, outputs, source archive, manual, and
source-member pins. It inserts only the EL FILE/S block before each existing
section-output block's `*END STEP`. Removing those three blocks must restore
the attempt01 inputs byte-for-byte; removing both output-only blocks must
restore the passed fullstep inputs byte-for-byte.

The parent owns review, input freeze, runner/verifier, bounded serial execution,
and result audit. Do not launch the decks before the parent freezes them.
