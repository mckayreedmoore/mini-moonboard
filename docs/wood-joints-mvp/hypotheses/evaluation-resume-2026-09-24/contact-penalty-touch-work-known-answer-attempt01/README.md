# Exact-touch work quadrature known-answer fixture — preparation

## Status and scope

This is a parent-review packet for a small penalty-contact C3D10 method fixture.
It is not frozen and has not been run. `prepare.py` binds the new deck to the
passing penalty case from
[`contact-energy-known-answer-attempt01`](../contact-energy-known-answer-attempt01/RESULTS.md).
The parent owns readiness, freeze and any later serial native run.

The fixture keeps the two 2 mm bodies, `E = 100,000 N/mm²`, frictionless
surface-to-surface penalty law, `K = 100,000 N/mm³`, area `A = 4 mm²`, mesh,
contact surfaces, constraints, and `*STATIC,DIRECT` full steps. It expands the
prescribed top-motion path to five endpoints and adds only one output request:
the selected pair's `CF`, `CFN`, and `CFS` values. Existing `U`, `RF`, body
`ELSE`, and global `CELS` requests remain in every step. No material,
geometry, contact, load-law, or restraint tuning is proposed.

## Exact-touch path and independent work calculation

The full-step endpoints are:

| State | Prescribed top `U3` (mm) | Expected total stored energy (N·mm) | Expected segment work from prior state (N·mm) |
| --- | ---: | ---: | ---: |
| Initial reference | 0 | 0 | 0 |
| Open | +0.001 | 0 | 0 |
| Touch after opening | 0 | 0 | 0 |
| Compression | −0.005 | 1.0 | +1.0 |
| Touch after compression | 0 | 0 | −1.0 |
| Reopen | +0.001 | 0 | 0 |

The initial reference is the deck's initial top boundary at `U3=0`, with zero
force and energy. For each later adjacent pair, independently sum the printed
top-set `RF3` values into `Q_i` and compute
`W_i = 0.5 * (Q_i + Q_(i+1)) * (u_(i+1) - u_i)`. The pinned penalty known-answer
reports negative top `RF3` during negative compression motion, so loading has
positive work and unloading has negative returned work. This sign is checked
against the frozen output, not inferred from `CELS`.

The analytical normal compliance is
`C = L_upper/E + L_lower/E + 1/K = 5e−5 mm³/N`. For the prescribed top
coordinate `u`, the signed top reaction is `Q(u) = A*u/C` for `u < 0`, and zero
for `u >= 0`; the expected compression endpoint is `−400 N`. At compression,
each body stores `0.5 * (E*A/L) * (0.002 mm)^2 = 0.4 N·mm`; the contact spring
stores `0.5 * K * A * (0.001 mm)^2 = 0.2 N·mm`. Their independent sum is
`1.0 N·mm`.

The previous open-to-compression endpoint chord uses `Δu=−0.006 mm` across the
force-free gap and gives `1.1985597 N·mm` from the pinned penalty endpoint
reactions. The exact-touch path splits off the zero-force 0.001 mm opening
segment; touch-to-compression predicts `+0.99879975 N·mm` from the pinned
nonlinear compression reaction, close to the observed stored energy
`0.9991998 N·mm`. The touch endpoint is the needed breakpoint at the
force-law kink; this is a method check, not a joint work estimate.

## Proposed checks and tolerances

Keep endpoint `ELSE`/`CELS` known-answer checks at the already reviewed
1% relative plus `1e−6 N·mm` component tolerance. Separately evaluate each
segment's trapezoidal work against (a) the observed change in
`ELSE_UPPER + ELSE_LOWER + CELS` and (b) its analytical work. For each
comparison, propose
`abs(error) <= max(3e−6 N·mm, 5% * max(abs(observed), abs(reference)))`.
Also compare cumulative work from the initial reference with the analytical
state energy. The 5% relative term is the pre-existing attempt09 numerical
screen; this fixture does not select it as an engineering limit.

The proposed absolute floor is `3e−6 N·mm`. At the 1 N·mm reference scale,
`E13.6` gives a `1e−6` last-place unit; a deliberately conservative budget for
three independently printed channels across a two-state difference is six
half-units, or `3e−6`. The actual `.4/.2 N·mm` terms and near-zero values use
smaller scientific-notation exponents, so their output quantization is
tighter. For the pinned compression RF distribution, per-node `E13.6` rounding
bounds the nine-node top reaction sum by `7e−5 N`; even treating both endpoints
of the maximum `0.005 mm` interval at that bound gives `3.5e−7 N·mm` work
rounding. The floor is therefore conservative for this small output format and
1 N·mm fixture scale. It is a numerical reading allowance, not physical
uncertainty, an allowable, or the unresolved absolute floor for the current
joint.

The selected contact pair is `SLAVE`/`MASTER`, matching the deck's sole
`*CONTACT PAIR`. The source-supported compression oracle is `CFN = (0,0,+400)
N` on the upper slave; its projection on the downward mean slave normal is
`−400 N` (tension-positive scalar convention). With no friction, `CFS=0` and
`CF=CFN`. For the unchanged square interface centered at `(1,1,0) mm`, the
compression origin moment is `(400,−400,0) N·mm` for both `CF` and `CFN`, and
zero for `CFS`; all three origin moments are zero at open and exact-touch
states. Use the inherited section-force scale: compression moment-vector
error norm `<= 0.01*400 + 0.001 = 4.001 N·mm`, and zero-resultant states
`<= 0.001 N·mm`. Report all force and moment components independently. Require finite force and moment
channels and the expected CFN on/off/sign; do not reject an otherwise finite
zero-area force result because the writer's centroid/mean-normal diagnostics
divide by area and can be undefined at open contact.

The inherited profile, force, compliance, direct-step history, full-mesh
DISP/FORC/STRESS, and section-output checks are bound to the passing penalty
case in `contact-section-force-known-answer-attempt02`, with its exact
predeclared tolerances and frozen DAT/STA/CVG evidence recorded in
`expected.json`. The touch-work verifier must keep those mechanics checks
separate from energy/work and pair-output checks. A method-fixture pass cannot
be read as mechanical or joint acceptance.

The prefreeze amendment and original preparation hashes are recorded in
[`prefreeze-amendment.md`](prefreeze-amendment.md).

Pinned 2.23 support: `statics.f:95–97` parses `DIRECT`; `contactprints.f:131–170`
selects the pair by slave/master names and `:176–222` accepts `CF`, `CFN`,
`CFS`; `printoutcontact.f:76–91` selects the pair's slave-face range,
`:181–205` computes force and moment, and `:218–255` writes resultants and
area-derived diagnostics. The latter zero-area diagnostics are not the force
channels. `printout.f:205–212` writes nodal `RF` in `E13.6`, `:556–559` writes
total body `ELSE`, and `:617–623` writes total contact spring `CELS`.
The pinned manual is `fea/generated/ccx_2.23.pdf`, SHA-256
`a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`; its
`*STATIC` entry is §7.122. Source archive SHA-256 is
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.

The MORTAR channel is out of scope: its CELS source path remains unsupported.
This packet does not alter the inherited mechanical/energy results, validate
MORTAR, authorize a joint run, or select an absolute work floor for attempt09.

## Reproduction

From this directory, `python3 prepare.py` verifies the frozen source packet and
creates `input/penalty_touch_work.inp`, `expected.json`, and
`preparation.json`. It refuses to overwrite any of those files. It does not
create a freeze or execute CalculiX.
