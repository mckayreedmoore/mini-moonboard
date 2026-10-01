# Next static method route

## Status

The C3D10 fixed-full-step coupon passed as a small method fixture for both
separate, unpatched CalculiX 2.23 decks: MORTAR and surface-to-surface penalty.
Each deck accepted one increment in each of three steps: open, compress, and
reopen. All three analytical endpoint states passed; each took three
iterations, with no rejected attempts or cutbacks. This validates that coupon
schedule and endpoints. It does not validate the intervening path, small
increments, the current joint, or a physical transient. See [the result](RESULTS.md)
and [the passing audit](verifier.json).

## Bounded candidate method

The plan permits mathematical unit-response characterization before
full-frame demands. A prescribed external-port displacement in separate static
steps is a candidate route: each step would advance the same full-cap port
coordinate by one fixed increment and seek equilibrium. `*STATIC,DIRECT`
fixes the increment size in pinned 2.23; with a step length of one, the coupon
accepted one increment per step. These are static load-path states, not physical
time samples or port-history demands.

No loading pattern, endpoint, increment size, step count, or input freeze has
been selected for the joint. The old attempt09 `n_plus` endpoint of 1 mm may be
used only if explicitly retained as a bounded mathematical scenario. Its former
clearance/onset rationale is superseded: the current force-frame audit places
both bolt groups radial to port N. Do not predict first bearing from the old
0.575 mm or 1.15 mm explanations.

Any candidate must preserve the reviewed geometry and the 43-node full-cap
port motion/force dual from [attempt09](../ordinary-port-motion-attempt09-common-map/README.md).
Keep the cleat free and leave contact, clearance, friction, preload, engagement,
and restraints unchanged. Preserve the current inventory: 24 blocks, 92
candidate bolt axes, 12 retained frame bolts, and 66 panel/kicker axes.

## Comparison and output gates

If the pending shared-boundary and cross-role contact eligibility review passes,
the minimum formulation comparison is two separate, version-matched 2.23
models: a surface-to-surface penalty control and a MORTAR candidate. Keep all
other frozen joint inputs and the chosen static displacement path identical;
contact formulation is the only comparison variable. Do not compare a 2.23
candidate with the historical 2.21 attempt09 run, and do not mix contact types
within either deck.

Use full-cap nodal U and native `SOF` at both port sections for the work-dual
motion and port wrench. This is the existing audited port-output method;
control-node RF is not a generalized port reaction. Record all cleat-node U,
accepted `.sta`/`.cvg` states, and formulation-appropriate contact and energy
outputs. Require accepted equilibrium after first *observed* positive
bolt-to-wood bearing, at least two accepted states after that event, force and
moment closure at the common datum, and the attempt09 5% incremental
work/energy gate. Retain its 1% force and moment closure checks with the
documented 0.01 N and 10 N·mm floors. Compare matched-state wrench and secant
compliance under the declared increment and other required sensitivities; 5%
is a numerical stability threshold, not an allowable.

The C3D10 result verifies top/bottom support reactions against the coupon
oracle. It records interface-node RF sums only as diagnostics; the verifier does
not validate them as contact resultants. Therefore MORTAR pair-local RF remains
unverified. Do not claim penalty `CF`, `CFN`, `CFS`, or other contact fields as
equivalent MORTAR outputs. The MORTAR `CDIS`/`CSTR` fields are diagnostics, not
pointwise force or law checks. Use interface RF for local actions only if the
pending topology review permits unambiguous per-pair sums and an independent
resultant/moment check validates that channel. Otherwise a MORTAR run is
method/path-only and cannot establish local joint transfer.

For MORTAR, retain the native source gate
`ndiverg = max(14, floor(nhelp/100) + ntie)`; the source clears convergence
when `iit > ndiverg`. Standard output does not expose `nhelp`, so accepted
iterations above 14 need a source-bound threshold determination before they can
be called override-free. An accepted iteration count at or below 14 cannot
reach the override.

## Remaining readiness

The joint is not ready to launch. First receive the already planned
shared-node/contact-role eligibility result. Then freeze the bounded static
path, selected step size and endpoint, matched formulation decks, the separate
output contracts, stop rules, and the acceptance audit. The fullstep coupon
does not supply those joint inputs or validate small-increment sensitivity.
No joint freeze or native joint run is recorded here.
