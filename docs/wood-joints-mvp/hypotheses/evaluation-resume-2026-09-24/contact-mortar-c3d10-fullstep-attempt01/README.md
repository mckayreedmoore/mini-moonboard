# C3D10 fixed full-step schedule discriminator

## Status and scope

Prepared for parent review. No CalculiX run has been launched for this packet.
It reuses the prior two-block C3D10 fixture, contact law, boundary conditions,
and three target displacements. Each step now uses one fixed full-step static
increment. The two decks remain separate: one MORTAR contact pair and one
matched surface-to-surface penalty pair.

The prior monotonic attempt showed an intermediate accepted-state mismatch in
both formulations, while penalty reached the expected compression endpoint.
This packet asks whether that mismatch depends on automatically subdivided
increments. It checks the original opening, compression, and reopening target
states at their step endpoints only. It cannot establish the response within
each step or validate a full joint model.

## Pinned source and schedule

The fixture derives from the pinned input decks and expected record in
[`contact-mortar-c3d10-known-answer-attempt01`](../contact-mortar-c3d10-known-answer-attempt01/README.md).
`prepare.py` verifies those input/expected hashes and the 2.23 source archive,
then changes only these schedule lines in each of the three steps:

```text
*STATIC
0.1,1.0,1e-8,0.1
```

to:

```text
*STATIC,DIRECT
1,1
```

The pinned 2.23 manual §7.122 describes `DIRECT` as fixing the increment size.
With step time 1 and initial increment 1, a successful step has one increment.
Here `DIRECT` is the static increment control, not a direct matrix solver or a
dynamic procedure. A failed increment must fail the run; an accepted result
with a rejected attempt or cutback does not satisfy this discriminator.

The exact manual PDF is `fea/generated/ccx_2.23.pdf`, SHA-256
`a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`.
The pinned source archive hash is recorded in `expected.json`. Its
`statics.f` sets `idrct=1` for `DIRECT` (lines 95–97); `gencontelem_f2f.f`
contains the static face-to-face gap initialization and relative-time update
(lines 570–585), while `slavintmortar.f` sets `shrink=.true.` for MORTAR
contact integration (lines 90–93). This packet changes the step schedule to
test endpoint behavior with relative time 1 in each step; it does not change
the contact formulation or override those source paths.

## Frozen known-answer gates

The existing linear series-compliance reference and tolerances are unchanged.
The two 2 mm bodies use `E=100000 N/mm2`, `nu=0`, interface area `4 mm2`, and
linear frictionless normal slope `K=100000 N/mm3`. The top face targets remain:

| Step | Top `U3` target | Expected normal force |
|---|---:|---:|
| Open | `+0.001 mm` | `0 N` |
| Compression | `-0.005 mm` | `400 N` |
| Reopen | `+0.001 mm` | `0 N` |

At the compression endpoint, each body shortens `0.002 mm`, interface
overclosure is `0.001 mm`, and pressure compliance is `5e-5 mm3/N`. The force
error gate is `1% + 0.001 N`; displacement/profile/interface-gap/face-warp
error is at most `1e-5 mm`; pressure-compliance error is `1% +
1e-10 mm3/N`. Open and reopened resultant support force must be at most
`0.001 N`. All original force closure and tangential reaction gates remain.

The linear oracle is approximate for `NLGEOM`. The source-derived uniform
St Venant-Kirchhoff endpoint estimate is `399.519872 N`, `0.120032%` below
the frozen 400 N linear answer. This explains the existing tolerance; it does
not replace the acceptance oracle.

Require exactly one accepted `.sta` increment in each of steps 1–3 and no
rejected `.sta` attempts or cutbacks. For MORTAR, every captured `.cvg`
iteration must be at or below the source-derived `ndiverg=14`, and each
accepted `.sta` iteration count must equal its final `.cvg` iteration.
`COPEN` and `CPRESS` remain finite-field availability and coverage diagnostics;
MORTAR fields are weighted or transformed, not pointwise law/force gates.

## Records and next action

`expected.json` records the three preserved targets, fixed-step schedule,
source pins, requested outputs, and unchanged known-answer gates. The parent
owns static review, input freeze, serialized bounded execution, and the result
audit. Do not execute either deck before that review and freeze.
