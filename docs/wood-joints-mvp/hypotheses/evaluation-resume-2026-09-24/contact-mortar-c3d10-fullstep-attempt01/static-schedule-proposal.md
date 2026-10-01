# Proposed static port-motion schedule

## Status and decision

This is a bounded candidate for parent choice, not a frozen input, readiness
pass, native run, or response result. It proposes one mathematical positive-N
port-motion path for the bottom-center-right ordinary patch. It makes no claim
about physical loading, demand, capacity, or first-bearing displacement.

The 1.0 mm endpoint is retained solely to keep the previously declared `n_plus`
coordinate as a traceable bounded mathematical scenario. Its earlier
clearance-based rationale is withdrawn. The current force-frame audit says N is
radial to both bolt groups; do not infer a 1.15 mm first-touch point or use
0.575 mm as a predicted port-motion threshold. Determine contact onset only
from accepted, source-mapped bolt-to-wood contact output.

## Candidate path

Use the independently audited attempt09 full-cap work-dual motion equations:
all 43 rail-cap and 43 principal-cap nodes define their respective port
coordinates. Preserve its positive-N relative translation and zero rotations.
For step `i = 1...10`, prescribe:

| Port coordinate | Target at step `i` |
| --- | --- |
| Relative joint `q_N` | `+0.1 i mm` |
| Rail local port translation along N | `+0.05 i mm` |
| Principal local port translation along N | `-0.05 i mm` |
| All other translations and rotations | `0` |

This gives ten `+0.1 mm` relative increments ending at `q_N=+1.0 mm`. Use
ten separate nonlinear static steps, each with the coupon's pinned 2.23 form:

```text
*STEP,NLGEOM,INC=100
*STATIC,DIRECT
1,1
```

Set each step's boundary targets to the cumulative table values. A successful
step is one fixed full increment; a failed step ends the candidate rather than
being cut back. The increment count and displacement spacing are a proposed
screening grid, not a behavior validated by the small coupon. The coupon
validated its own opening/compression/reopening endpoints only.

Run separate, version-matched CalculiX 2.23 penalty-control and MORTAR-candidate
decks with the same schedule and all other frozen joint inputs identical.
Contact formulation is the comparison variable. Do not compare this path to
the historical 2.21 attempt09 result. Do not change geometry, contact law,
clearance, friction, preload, nut engagement, material scenario, or restraints.

## Required interpretation and gates

- This is static mathematical continuation in ten load steps. Step time is a
  solver parameter, not elapsed physical time. Do not call it a transient or a
  frame demand. No source-bound full-frame port histories are available.
- Keep the cleat free. Add no global gauge, pin, local restraint, spring, or
  stabilization. Retain its complete 9,369-node displacement output. If a free
  mode prevents a unique accepted equilibrium, report that obstruction; do not
  suppress it to obtain a result.
- Require accepted equilibrium at every step. Count the first positive
  bolt-to-wood bearing from the applicable local contact channel, then require
  at least two accepted states after it. Under this ten-step cap, first bearing
  must occur by step 8 to meet that count. This is only arithmetic on the
  acceptance gate, not a predicted contact location. If it occurs later, is
  unobservable, or is absent, the candidate does not pass.
- Use full-cap U and native `SOF` on both port sections. Independently align
  section signs and translate moments to the common joint datum. Keep attempt09
  diagnostic closure checks: force residual no greater than
  `max(0.01 N, 1% of the larger port-force norm)`; moment residual no greater
  than 1% of the larger port moment or force-times-port-arm scale, with a
  `10 N mm` floor. These are numerical diagnostics, not allowables.
- Audit incremental prescribed-boundary work against the change in elastic and
  formulation-appropriate frictionless-contact energy at each accepted state.
  The existing attempt09 contract sets a 5% relative work/energy difference,
  but describes its absolute work floor only as “from the same unit-wrench
  scale” without giving a number. Resolve and freeze that floor before launch;
  do not guess it. Verify MORTAR energy-output semantics before using any
  field as a contact-energy total.
- For MORTAR, preserve the source gate
  `ndiverg = max(14, floor(nhelp/100) + ntie)`. An accepted iteration count at
  or below 14 cannot reach the override. Above 14, determine the threshold from
  the pinned source before calling the result override-free.
- Keep the known-answer limits: coupon interface-node RF sums are diagnostics,
  not validated MORTAR contact resultants. Do not substitute penalty `CF`,
  `CFN`, `CFS`, or `CDIS` meanings for MORTAR. Pair-local actions require a
  separately validated force/moment-closed output channel; without one, the
  MORTAR result is method/path-only.

## Readiness and next action

Do not launch from this proposal. First receive the pending shared-node and
cross-role contact eligibility result, then settle the independent output
contract, including whether pair-local MORTAR actions can be recovered. Parent
must choose whether this bounded path is useful, resolve the work-floor gap,
and freeze matched decks, acceptance checks, stop rules, and output identities.
If those gates pass, execute only the chosen 2.23 comparison serially. No
schedule, freeze, or native execution is created by this note.

## Source basis

- [`next-static-method-route.md`](next-static-method-route.md): full-cap U and
  SOF port method, known-answer limits, comparison and readiness gates.
- [attempt09 record][a09]: port map, free-cleat contract, diagnostic closure
  limits, and failed 2.21 static run. Its original 1 mm clearance rationale is
  superseded by the correction below.
- [attempt09 input audit][a09audit]: independent full-cap map, virtual-work,
  constraint-collision, and no-gauge input checks. This is input verification
  only.
- [completion ledger][ledger]: source-bound correction that N is radial to
  both bolt groups and withdraws the 1.15 mm first-touch explanation.
- [`README.md`](README.md) and [`RESULTS.md`](RESULTS.md): pinned known-answer
  fixture; each coupon step uses `*STATIC,DIRECT` with `1,1`. Passing endpoints
  do not validate a joint trajectory or smaller-increment sensitivity.
- [CalculiX 2.23 User's Manual, §7.122](https://www.dhondt.de/ccx_2.23.pdf):
  `DIRECT` disables automatic incrementation for nonlinear static steps.

[a09]: ../ordinary-port-motion-attempt09-common-map/README.md
[a09audit]: ../ordinary-port-motion-attempt09-common-map/port-motion_n_plus-audit.json
[ledger]: ../../../completion-ledger.md#september-27-mvp-e-goal-reset-and-next-execution
