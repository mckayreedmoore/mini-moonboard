# Eight connected stacks: prescribed-action bearing statics

All eight unresolved bolt stacks now have a continuous bearing **equilibrium
trial**, covering their 48 original shaft/case combinations and 144 own member
wrenches. Each trial preserves the three members' individual forces and
moments, plus the shaft's original axial captures and metal gravity. Maximum
whole-shaft residuals are 0.000009893 N and 0.000170773 N·mm. This closes a
bounded statics-method step; **complete joint resistance remains unresolved**.

The [result](result.json) uses the six authenticated
`eoere-bottom-rail-tnut-clearance-v1` fields. It supplies no response for
`eoere-midpoint-ready-frame-v3`, no deformation compatibility, no nonlinear
yield model and no adjusted NDS design value. Shafts 079/080 moved in base v3;
their old actions remain attached to the old geometry. The preceding
[revised-base audit](../revised-base-audit-v1/README.md) remains frozen.

## Question and method

The previous eight-stack gap was not a missing continuous shaft in the old
frame model: its admitted fields already have common elastic shafts,
independent bore contacts, axial captures and own metal gravity. The missing
result is complete resistance for their asymmetric material/loading stacks.
This followup asks whether a continuous bearing distribution can reproduce
each stack's prescribed forces and moments without assuming equal outer loads
or adding isolated single-shear capacities.

First move each own port wrench to the center of its bearing interval:
`C_center = C_port + (p_port - p_center) × F`. For unit shaft direction `g`,
the lateral bearing first moment is `S = -g × C_center`. Axial capture forces
are retained separately. No shaft-axis torque is allowed through this lateral
method; a nonzero torque requires another path.

For a centered full bearing interval of length `L`, the affine trial is
`q(x) = F/L + 12 S x/L³`. Its integrals reproduce the own lateral force and
first moment exactly. The largest vector magnitude occurs at an endpoint.
Signed density permits opposite bore-wall actions along the interval; whether
the actual shaft and wood can deform compatibly to produce it is unproved.
The trial assumes the full recorded nominal interval is available for bearing.

For any chosen lateral direction, a separate exact scalar bound gives the
least possible peak signed line density:

```text
q_min = [2 |S_direction| + sqrt(4 S_direction² + F_direction² L²)] / L²
```

This follows from the largest attainable first moment at fixed force and
bounded density, `|S| <= q L²/4 - F²/(4q)`. A signed step distribution attains
that scalar limit. The largest bound among the shaft tangents and the own
force/first-moment directions is necessary for the vector problem; it is not
a sufficient vector solution or a connection capacity. The affine trial
supplies an equilibrated upper value for the minimum required peak density.

The existing admitted-field intake and thread-window helper are reused. No
new frame operator, force solve, CAD query or geometry is introduced.

## Usable results

The largest wood trial occurs in the left cleat on shaft 067, A12-forward.
Its own force is 743.400 N and its centered moment is 2.351 Nm. A force-only
average misses the additional bearing needed to carry that moment.

| Own member, shaft 067 / A12-forward | Necessary directional peak density | Affine trial peak density | Affine projected bearing parameter |
| --- | ---: | ---: | ---: |
| Left cleat, 38.1-mm interval | 23.001 N/mm | 29.199 N/mm | 3.990 MPa |
| Left base-angle steel, 6.35-mm interval | 122.523 N/mm | 133.164 N/mm | 18.197 MPa |

The cleat's force-only mean is 19.512 N/mm. Its affine peak is about 1.50
times that mean. The recorded constant bearing-screen diameter is
7.31774 mm, following the existing NDS component root-floor route. The
existing DF-L helper returns a perpendicular-grain `Fe` material parameter of
28.613 MPa for this diameter; the largest wood affine comparison is
**0.139453**. `Fe` is a dowel-bearing material input to a yield calculation,
not an ASD allowable local pressure. This comparison does not establish a
joint utilization, reserve factor, maximum climber weight or strength pass.

The same steel port's reported moment is 2.470669 Nm at its original face
datum. Recentered to the plate interval, it is 0.147875 Nm. The removed part
is the force lever arm, not a waived moment. The remaining centered moment
is retained in its nonuniform bearing trial. No product-specific eoere
hole-bearing resistance is assigned to the 18.197-MPa required parameter.

All eight per-shaft results, including the own original shaft markers, are in
the compact result. Their greatest reused same-cut first-yield marker is
0.514158 on shaft 067 / A12-forward. It keeps the original partially threaded
shaft, catalog dimensions, root-floor and material limits; it is not a newly
calculated bolt capacity or an ASD acceptance.

## Thread exposure and connected-joint limit

The existing catalog-window calculation reproduces exactly:

| Shafts | Ordered stack | Potential thread/runout exposure |
| --- | --- | --- |
| 065, 066, 079, 080 | steel / 38.1-mm header / steel | Header 4.1656 mm, 10.93%; head steel 0%; nut-side steel 100% |
| 067, 070, 071, 074 | steel / 88.9-mm side / 38.1-mm cleat | Steel and side 0%; cleat 16.8656 mm, 44.27% |

Every stack has a member exceeding the existing quarter-thread exception.
The component bearing-screen diameter therefore uses the recorded root-floor
scenario. This does not replace the actual partially threaded shaft model
with a full-thread-root model. Catalog grip and window arithmetic do not
observe delivered body, thread transition, root or seating.

The affine construction does not enforce shaft flexural compatibility or
limit its bending moment while redistributing bearing. It cannot select a
failure mechanism, establish the multi-member reduction term, resolve
interacting axial seat/washer forces or qualify member splitting. The old
shaft markers are a separate result from the old elastic contact distribution;
they must not be combined with this alternate density as a matched response.
The new equilibrium trial therefore leaves all eight complete resistances
null. A connected yield model still needs the own simultaneous actions,
material properties, actual diameter intervals and compatible contact behavior.

## Primary-source followup and priorities

The [AWC TR12 2015 report](https://awc.org/wp-content/uploads/2021/12/AWC-TR12-1510.pdf)
supports the known-answer check only: equal-length, zero-gap rigid-dowel mode
II in Example 3.1 reproduces 414.213562 lbf after its 3.6 reduction. That
example does not establish an applicable reduction or capacity for these
asymmetric three-member stacks. The complete
[2026 report](https://awc.org/wp-content/uploads/2026/06/TR-12_2026_formatted.V3.pdf)
remains unavailable in this review: web open failed and a direct public
request returned HTTP 404. Official indexed contents identify two-ply
single-shear additions, but indexed fragments are insufficient to adopt them.
The earlier [source-access limitation](../../../../../evaluation-resume-2026-09-24/current-steel-direct-screen-attempt06-tr12-2026/README.md)
is retained; no claim is made that the inaccessible edition contains no useful
method.

The live [eoere listing](https://www.amazon.com/dp/B0C7V7VS89) still states
Q235B and nominal quarter-inch thickness, without resolving the audit's
minimum thickness, bend radius or defined rating inputs. The old 0.17%
heel reference margin remains open. Another radius sweep would not supply
those missing product inputs.

The practical sequence remains geometry-specific case actions under the
parent's readiness control, connected resistance/compatibility for the eight
stacks, and qualification of the panel attachment/end-restraint path. The
four long members' potential brace stations and the old panel/screw
exceedances remain as recorded in the audit. Their paused remedies remain
paused. This followup introduces no geometry remedy, member enlargement,
new fastener, floor test, physical work or blanket sign-off prerequisite.

## Verification and retention

Verification covers all 1,126 source pins before and after, all 144 raw
own-port force/moment replays, all 48 connected free bodies and exact
thread-window reuse. Known answers cover uniform force, a pure couple,
signed-step optimality, datum invariance, exact affine quadrature and the
AWC example. Seven negative controls reject torque, altered force, foreign
host/state and invalid intervals. The replay reproduces both JSON outputs
byte-for-byte; owned-source lint and format checks pass. The independent
arithmetic in [verification.json](verification.json) is same-agent validation,
not an independent engineering review.

The five permanent files are this summary, `analyze.py`, `inputs.json`,
`result.json` and `verification.json`. Detailed member trials, connected case
records and source pins stay under the existing ignored output tree in
`connected-stack-followup-v1/attempt02/`. `attempt01/` is a superseded
reporting prototype; it preserves its first-run script and inputs. No native
solve, CAD rebuild, mesh export, archive or pruning occurred.

Reproduce from the repository root:

```bash
uv run python docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/analyze.py --out fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/replay --compare fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/attempt02
```

Keep this trial, base-v3 audit, original six fields and preceding component
packets active for their stated scopes. The earlier reporting prototype and
temporary replay may be archived after ownership/consumer checks through the
existing archive workflow; nothing is deleted here. Parent owns maintained
summary/ledger integration and shared staging/publication.
