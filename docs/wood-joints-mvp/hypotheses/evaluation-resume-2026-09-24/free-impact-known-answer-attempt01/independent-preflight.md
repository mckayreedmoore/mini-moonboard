# Independent preflight: free-impact C3D10 known-answer fixture

Date: 2026-09-27. This is a read-only review of the prepared deck, analytical
contract, offline verifier, and parent runner. No native solver, build, freeze,
or source/geometry edit was performed.

## Prepared input and analytical oracle

The prepared input is SHA-256
`2b253f63f9e8cee1bcb471ba3fb6b8150e72df781432bcfe6a1019e66d44caea` and
preserves the source coupon's 54 physical coordinates and twelve C3D10
tetrahedra (upper elements 1–6, lower elements 8–13). Its source geometry deck
is SHA-256
`e9d0ec2252201fdaa249b5e884c9290a128fb31c135afff6e08c566cb504c61b`. The
input audit independently confirms all midside nodes are exact straight-edge
midpoints, both six-tet bodies have exact volume 8 mm³, and their initially
coincident triangular contact faces have exact area 4 mm² and normals −Z
(slave) and +Z (master). The old disconnected C3D4 witness is absent.

Every one of the 27 upper-body U3 DOFs is a dependent term in a separate
homogeneous equation to node 8001 U3. Lower U1/U2/U3 and upper/controller U1/U2
are fixed; only controller U3 is free. The initial velocity is −0.1 mm/s on
all 27 dependent U3 terms and on the independent controller term, so the
initial condition is kinematically consistent. The controller has no element
mass. With density 0.125 tonne/mm³, each 8 mm³ body has mass 1 tonne; the
projected moving mode therefore has mass 1 tonne and initial kinetic energy
0.005 N·mm. The audit reports 137 fixed DOFs, 27 dependent DOFs, and exactly
one free DOF. These are fixture algebra checks, not a general MPC-mass claim.

For the flat frictionless interface, the linear pressure slope
100,000 N/mm³ over 4 mm² gives scalar stiffness `k = 400,000 N/mm`. With
`*DYNAMIC,DIRECT,ALPHA=0`, the pinned source computes Newmark
`beta=1/4`, `gamma=1/2`. For the single rigid-translation coordinate, the
source-only fixed-step recurrence is:

```text
p = u_n + dt*v_n + dt^2*a_n/4
if p < 0: u_(n+1) = p / (1 + k*dt^2/(4*m)); a_(n+1) = -k*u_(n+1)/m
else:     u_(n+1) = p;                         a_(n+1) = 0
v_(n+1) = v_n + dt*(a_n + a_(n+1))/2
```

The pinned 70-state reference has `dt=0.0001 s`; its most compressed state is
increment 25 at −0.00015810626598070757 mm. Increment 49 remains compressed
at −0.000006890465832962967 mm; the first open state is increment 50 at
+0.0000031069244162852196 mm and +0.10004280715081149 mm/s. Removing the
remaining unilateral spring at that endpoint raises discrete total energy by
4.2816313072023434e−6 N·mm, 0.0008563262614455847 of the initial energy.
Thereafter the free coordinate advances at constant velocity to
+0.00020319253871790824 mm at 0.007 s. These are analytical reference values;
native outputs still need to match them.

Uniform translation creates no body strain, so the body `ELSE` oracle is zero;
the upper body carries the scalar kinetic energy, while the fixed lower body
has zero kinetic energy. `EMAS`/`EVOL` should report 1 tonne/8 mm³ per body.
The contact energy oracle is `0.5*k*min(u,0)^2`, zero after accepted
separation. The verifier checks all 70 accepted states, DAT U/V coverage on
all 55 nodes including controller 8001, FRD U/V coverage on all 54
element-connected nodes, actual output times, body totals, CELS, pair force,
and the trace case's point-law and generated-set records.

The pair-output sign is supported by the pinned face orientation and source.
For compression, `springforc_f2f.f` reports positive pressure magnitude along
the master normal. `printoutcontact.f` reverses that normal before its CFN
calculation, so CFN is +Z on this upper slave face. Its centroid is
`(1,1,0) mm`; the expected origin moment is `(Fz,-Fz,0) N·mm`. The source
member hash for `printoutcontact.f` is recorded below; the complete archive
hash also pins it.

## Release trace interpretation

The source order permits a first-iteration stale-set observation. At a new
increment `nonlingeo.c` advances the increment and calls contact generation
from accepted `vold` before the predictor (lines 1524–1546 and 1738–1895).
For this fixture, accepted increment 49 is still compressed. The predictor
and initial results then update `vold` to the predicted state (lines
2063–2075 and 2157–2180). A retained old spring can therefore yield a
positive-gap, tensile TRIAL in iteration 1. It is recorded if present, but is
not required. Re-generation in later iterations occurs from the updated state
(lines 2307–2327); `gencontelem_f2f.f` sets `isol=0` for a strictly positive
dynamic clearance before spring creation (lines 554–560 and 672–685).

The acceptance's iteration-1-only rule is deliberately limited to this
one-coordinate, constant-mass, constant-linear-stiffness fixture. With a
positive predictor `p`, its still-active linear contact correction is
`q=p/(1+k*dt^2/(4*m))`; the positive denominator preserves the sign. The
later generated set should therefore remove positive-gap points. The
verifier rejects a positive corrected-gap TRIAL in iteration 2 or later. This
does not establish that sign behavior for another model or contact law.

## Source and artifact pins

The pinned CalculiX 2.23 source archive SHA-256 is
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`; the
manual PDF SHA-256 is
`a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`. The
preparation producer verifies the listed member hashes before writing/checking
the expected contract. Relevant member hashes and anchors are:

| Source member | SHA-256 | Audited behavior/lines |
| --- | --- | --- |
| `contactpairs.f` | `e2b7e8176adc70f02f5140308a0c6a591fc9f7f620026867708e6345a9d9c488` | Surface-pair mode mapping, 111–118 |
| `dynamics.f` | `d861c936c204853e84e7647b4164e78556c11b6eb0a532b623d4a75622f53e5e` | DIRECT/alpha control, 70–78, 98–119, 134–139, 248–270 |
| `initialconditionss.f` | `25c721d40c071e31baea9c4e7cf8bcc226bbdd0e65cccb327981b31e0c174b2c` | Velocity IC parsing, 474–501 |
| `nonlingeo.c` | `8684bb6d7fa7097c0a854db5a45eb9e2d11adfde574e688184ecbbbad56ff83f` | Newmark parameters, predictor and contact order, 904–907, 1524–1546, 1738–1895, 2063–2180, 2307–2327 |
| `e_c3d.f` | `d009650b48e5ca150080aed9e19d1b65d2b2cf4869ab6d7f2b1a5cd55e2df3fc` | C3D10 mass integration, 986–1005 |
| `mafillsm.f` | `d6073d5bfd9ad56a03a25b8c79ad1bb2dd178e48e3db3b9dd951f612b0197602` | Element mass assembly and MPC transformation path, 285–300, 338–355, 406–430 |
| `mafillsmmatrix.f` | `5790af603df9ba61699bb67aa6552d6e89057202dd0c3b50637cf478ec4899a3` | MPC mass-matrix transformation |
| `gencontelem_f2f.f` | `853e2159f37666bc1430516bb4e5c65b6ba484ef1866454930e66cf317fb8afe` | Dynamic positive-gap filtering and spring creation, 550–560, 617–629, 672–685 |
| `springforc_f2f.f` | `3be67688eb16a95739e09990c34ae0d2614acff216b254ea474bbf7c4d9e1ba4` | Signed gap, linear pressure/energy, internal spring resultant, 155–164, 186–201, 248–253 |
| `checkimpacts.f` | `30b2e0c7ca03f741852dfc93b67657291f91acfc3b3db8c1b36ec9589733fd66` | Energy residual and impact/rebound step-size logic, 90–108, 112–180 |
| `printoutcontact.f` | `4e1f5452d5fd268d7e4f1ab702de4804bb8f34a429b5e2c14ff9af3df9a9a055` | Master-normal reversal and CFN/resultant moment, 144–205 |

The scalar reference SHA-256 is
`fc63b21a5c9947f04dd1326339ba0201a2c251a465f41350fd35c46874198d61`. The
parent trace patch is output instrumentation; the runner pins its patch,
build, and execution records separately from the unmodified 2.23 baseline.

Reviewed packet artifact hashes are:

| Artifact | SHA-256 |
| --- | --- |
| `prepare.py` | `947252af6ea7278cf5637713e4718267f282105d3a06629e2ab337c518219e64` |
| `fixture-design.md` | `22b4dcab78e5da576ff987bbe3a81514b00cd06eae81c135c5c43334f73c7fd0` |
| `expected.json` | `d9364226a70cd3085b2b23eb7234ddaccfa6d33c57eccb5084cb0a73adc7a72d` |
| `acceptance.json` | `23a64040d040927ee8e95866f810f5f28dfac4eca37cf6bb4f15269311d1f59d` |
| `verifier.py` | `774a1d95b49c58752c5ee29956b65116e13759e0d99522c4a413f713d751f9e7` |
| `run.py` | `8239af8c29027a2c9addde4c96bf85689230aadc133a100d9ad0f02020fa0a3c` |
| `parent-input-audit.json` | `573ffe440bceb0ce15725798a755323802afcd2cf899bd079e538c977d915786` |

## Offline checks and bounded verdict

Read-only checks passed against the bytes above: `prepare.py --check`,
`audit-input.py`, the scalar reference's producer check, and
`verifier.py --self-test`. Synthetic controls accept positive baseline/trace
captures and reject wrong motion, missing TRIAL/CVG coverage, wrong point
pressure, wrong pair force, and changed measured baseline/trace controller
motion. No native result is represented by those controls.

The parent runner freezes the input, acceptance, verifier, audit and review
files; pins external source/build/parser dependencies; runs the unmodified
2.23 baseline before the output-trace build; and captures each case serially
with no network, one CPU, 1 GiB memory/no swap, 60 s wall time, and a 16 MiB
aggregate output limit. It checks normal exit, completion marker, file hashes,
and output cap. The verifier binds accepted states across STA/CVG/events and
FRD/DAT, uses all-node DAT versus physical-node FRD coverage, compares both
cases against the pinned scalar recurrence and each other, and keeps all
acceptance/release flags false.

No input, source, or analytical contradiction remains in this bounded
preflight. Parent review and the serialized native execution are still
required to determine whether the pinned binaries produce the expected
70-state record set and output values. Even a passing fixture remains a
method-check only; it does not establish current-map applicability, a wood
joint response, capacity, mechanical acceptance, work/energy acceptance,
or release.
