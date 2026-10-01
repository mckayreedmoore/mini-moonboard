# Free scalar contact impact coupon design

Date: 2026-09-27. This is a source-bound design assessment only. It creates no
input deck, changes no solver behavior, and reports no native run.

## Finding

A free one-coordinate impact coupon is a better bounded method fixture than the
prescribed-motion coupon for testing the implicit contact impact-energy path.
It begins with a known nonzero kinetic-energy inventory and transfers that
energy into a linear penalty spring before reopening, with no applied force or
prescribed motion doing work. The fixed-step scalar reference is finite and
includes the unilateral release event. This is a suitable candidate for a
separate known-answer attempt, subject to a native check of initial-velocity
handling through the homogeneous MPCs, mass condensation, contact activation,
and energy capture. None of those solver behaviors is qualified here.

## Proposed model

Use the same two 2 mm × 2 mm × 2 mm solid blocks and 4 mm² planar interface as
the small contact coupon. Mesh both with C3D10 solids and keep the lower block
fixed. Fix the upper block's physical U1 and U2 coordinates; for every upper
physical node add a separate homogeneous equation `U3(node) - q3 = 0`, where
`q3` is an otherwise free controller node. There is no prescribed U3 history.
With density `1/8 tonne/mm³`, the upper 8 mm³ body has total mass 1 tonne; the
lower mass is fixed. Set the initial gap to zero and initialize U3 velocity to
`−0.1 mm/s` consistently on the upper physical nodes and `q3`. Apply no external
load and add no damping.

Use linear normal pressure-overclosure `K=100000 N/mm³`. If the full 4 mm²
interface remains engaged, its scalar stiffness is `k=K A=400000 N/mm`. The
sign convention is `u<0` for penetration, so the body force is
`F=−k min(u,0)`. The C3D10 consistent-mass and MPC-assembly source paths make
this a meaningful test of the free reduced coordinate, but do not establish
that its native projected mass equals the intended 1 tonne; verify that from
the run.

For a deterministic reference, the candidate procedure is implicit
`*DYNAMIC,DIRECT,ALPHA=0`, `Δt=0.0001 s`, period `0.007 s` (70 increments).
Pinned 2.23 source sets the direct-step minimum and maximum equal to the input
increment. `ALPHA=0` gives `β=(1−α)²/4=1/4`, `γ=1/2`; with zero initial contact
force and no other force, the expected initial acceleration is zero. The
2.23 parser accepts velocity initial conditions by node/set, global DOF, and
magnitude. Applying the same velocity to every equation participant makes
the input velocity field kinematically consistent, but native first-state
output must still verify that the solver carries it through the MPC reduction.

## Discrete known answer

The initial energy is `0.005 N·mm`. Let `p = u_n + Δt v_n + Δt² a_n/4`. The
average-acceleration Newmark recurrence with unilateral endpoint contact is:

- If `p < 0`, `u_(n+1)=p/(1+k Δt²/(4m))` and
  `a_(n+1)=−k u_(n+1)/m`.
- If `p ≥ 0`, `u_(n+1)=p` and `a_(n+1)=0`.
- In either branch, `v_(n+1)=v_n + Δt (a_n+a_(n+1))/2`.

Start from `u_0=0`, `v_0=−0.1 mm/s`, `a_0=0`. The independently reproducible
70-state calculation is recorded in
[`parent-reference.py`](parent-reference.py) and
[`parent-reference.json`](parent-reference.json); these are scalar design
artifacts, not solver evidence. Its JSON SHA-256 is
`fc63b21a5c9947f04dd1326339ba0201a2c251a465f41350fd35c46874198d61`.

The continuous ideal oscillator has `ω=sqrt(k/m)=632.4555320 rad/s`, maximum
compression `0.000158113883 mm`, and its first zero-gap crossing at
`π/ω=0.00496729413 s`; thereafter it separates at `+0.1 mm/s`. The fixed-step
discrete answer reaches maximum compression `0.000158106266 mm` at increment
25. It first opens at increment 50 (`t=0.005 s`, `u=3.10692442e−6 mm`,
`v=0.100042807 mm/s`) and ends at `t=0.007 s`,
`u=0.000203192539 mm`. The continuous event time is only a comparison; the
discrete recurrence is the strict oracle.

During active compression, the discrete kinetic plus contact-spring energy is
`0.005 N·mm` to floating-point precision. The endpoint unilateral switch at
increment 50 produces the explicit jump
`ΔH=−k u_49 u_50/2=4.28163131e−6 N·mm`, a `0.0856326%` increase. Preserve this
small, predicted discretization effect in the oracle; do not demand exact
energy conservation across the release step. The increase is below the
nominal `0.25%` rebound threshold in the pinned face-to-face `checkimpacts`
branch, but source thresholds alone cannot prove the solver's actual energy
classification or completion.

## Evidence limits and future checks

The pinned `checkimpacts.f` computes an energy change from the solver's
internal/kinetic energy, external work, damping work, and reference values. For
face-to-face penalty contact it can request a cutback for a relative energy
drop below `−0.008`, or a rebound change above `0.0025` when the generated
contact count is no greater than its increment-start count (`ne ≤ neini`).
Initial kinetic energy gives this coupon a meaningful balance even
though external work is zero. The predicted small release jump is encouraging,
but only captured native energy/count records can establish which branch the
solver takes. Keep the direct step fixed for this oracle; do not treat an
automatic retry, changed stiffness scale, damping, or relaxed convergence gate
as equivalent evidence.

A later frozen fixture should capture all 70 actual state times; physical and
controller U3/V3; zero lateral motion; body mass, kinetic and solid strain
energy; contact count; signed contact clearance, pressure/resultant and spring
energy; terminal status; and explicit evidence that no mass or spring scaling
occurred. A 16 MiB output cap is a reasonable proposed bound for those records,
but this assessment does not authorize a native run. Check that upper physical
nodes and `q3` have the same motion, that
the integrated active-contact force/stiffness has the expected sign and
magnitude, and that release occurs at the predicted discrete state. Reactions
are diagnostics, not the inertia oracle. A missing field, unexpected active
DOF, inconsistent initial velocity, or materially different native contact
energy is a fixture failure to diagnose, not a reason to tune the model.

This coupon would qualify only the tested C3D10 free-translation/contact
path. It does not qualify the current nut's eccentric physical-pivot MPC,
general joint mechanics, wood bearing, contact onset, friction, or any
capacity. It does not rescue the failed prescribed-motion capture and does
not establish an actual joint's response. The existing
[`C3D10 free-MPC applicability review`](../implicit-c3d10-free-mpc-applicability-review-attempt01/README.md)
remains applicable: general C3D10 free-coordinate inertia is not inherited
from a C3D8 pass.

## Pinned sources

The source is the pinned CalculiX 2.23 archive
[`source.tar.bz2`](../ordinary-external-force-transient-attempt04-diagnostic/build-attempt02/source.tar.bz2),
SHA-256 `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.
The local pinned manual is
[`ccx_2.23.pdf`](../../../../../fea/generated/ccx_2.23.pdf), SHA-256
`a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`; see
`*INITIAL CONDITIONS` and `*DYNAMIC` (also available from the
[official 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf)). Relevant source
members and hashes:

- `initialconditionss.f` `25c721d40c071e31baea9c4e7cf8bcc226bbdd0e65cccb327981b31e0c174b2c`,
  lines 474–501: `TYPE=VELOCITY` reads the global DOF and assigns `veold`.
- `dynamics.f` `d861c936c204853e84e7647b4164e78556c11b6eb0a532b623d4a75622f53e5e`,
  lines 70–78, 98–119, 248–270: alpha default/clamp, `DIRECT`, and fixed-step
  bounds.
- `nonlingeo.c` `8684bb6d7fa7097c0a854db5a45eb9e2d11adfde574e688184ecbbbad56ff83f`,
  lines 904–907: implicit `beta` and `gamma` from `alpha`.
- `e_c3d.f` `d009650b48e5ca150080aed9e19d1b65d2b2cf4869ab6d7f2b1a5cd55e2df3fc`,
  lines 986–1005, and `mafillsm.f`
  `d6073d5bfd9ad56a03a25b8c79ad1bb2dd178e48e3db3b9dd951f612b0197602`,
  lines 285–300, 338–355, 406–430: consistent element mass and MPC-aware
  mass assembly.
- `springforc_f2f.f` `3be67688eb16a95739e09990c34ae0d2614acff216b254ea474bbf7c4d9e1ba4`,
  lines 186–201: linear overclosure force and stored spring energy.
- `gencontelem_f2f.f`
  `853e2159f37666bc1430516bb4e5c65b6ba484ef1866454930e66cf317fb8afe`, lines
  554–560, 617–629: for implicit dynamics, positive clearance removes the
  non-tied contact spring; negative clearance is the normal creation criterion.
- `checkimpacts.f` `30b2e0c7ca03f741852dfc93b67657291f91acfc3b3db8c1b36ec9589733fd66`,
  lines 89–108, 148–177: energy residual and face-to-face impact/rebound rules.
