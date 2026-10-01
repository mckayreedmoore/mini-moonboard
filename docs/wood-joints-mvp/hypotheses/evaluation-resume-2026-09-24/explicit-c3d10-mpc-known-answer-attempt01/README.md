# Explicit C3D10 MPC mass-coordinate known-answer, attempt 01

Status: preparation only. No native job or input freeze has been created.
Parent owns readiness review, verifier, freeze, and any serialized execution.

## Question and scope

This two-deck method fixture asks whether pinned CalculiX 2.23 explicit
structural dynamics preserves physical motion when the same free straight
C3D10 tetrahedron is expressed in either direct physical displacement
coordinates or an equivalent homogeneous MPC coordinate map. It specifically
checks the inertia/mass-bearing path through one dependent physical DOF and a
free controller DOF. It adds no physical restraint: the mapped form is an
invertible coordinate substitution and the controller is not prescribed.

Both decks use one unit tetrahedron, `E=1 N/mm²`, `nu=0`, and
`rho=6 tonne/mm³`; all physical U1 DOFs are free and physical U2/U3 are fixed.
The mapped deck adds only
`u1 + u2 + u3 + u4 - 4*q11 = 0`, with physical node 1 U1 dependent. The
constant physical nodal loads are `f_i = m_i * 1 mm/s²` for all ten nodes,
using the source-derived CalculiX C3D10 explicit lumped mass. Loads have no
amplitude and therefore start at full strength in the dynamic step.

The invariant analytical solution is rigid translation:
`U1(t)=0.5*t² mm`, `V1(t)=t mm/s` at each physical node, and the same motion
for mapped coordinate `q11`. There is zero strain, `ELSE=0`, body mass is
`EMAS=1 tonne`, and total `ELKE=0.5*t² N·mm`. At the requested final time
0.1 s, the values are 0.005 mm, 0.1 mm/s, 0.005 N·mm, and 1 tonne. This checks
the *declared explicit lumped-mass system*, not consistent-mass equivalence.

## Time integration and output

The cards use `*DYNAMIC,EXPLICIT=2,ALPHA=0`, initial/max increment 0.001 s,
period 0.1 s, no `DIRECT`, and a blank minimum-increment field. The pinned
manual states that explicit structural dynamics uses lumped mass and one
iteration per increment; leaving minimum increment blank avoids requesting
selective mass scaling or spring-stiffness reduction. No mass/stiffness scaling
is authorized. The pinned `nonlingeo.c` initialization computes beta=0.25 and
gamma=0.5 at alpha=0, the undamped constant-acceleration coefficients used by
this trajectory oracle. Actual accepted times and increments must be read from
native output rather than assuming 100 increments.

Physical `U,RF,V` are requested in DAT and FRD for nodes 1–10. The mapped
controller `U` is requested in DAT only. Element `ELSE,ELKE,EMAS,EVOL` totals
are requested in DAT; `ENER` is requested in FRD as a nodally averaged
zero-strain energy-density diagnostic, not as the kinetic-energy oracle. The
pinned manual documents that output identity, but the exact zero-valued native
field block remains unobserved until parent-owned execution. Require full
finite physical node coverage. Use the FRD step/increment/time headers to key
frames and match DAT blocks by reported time for this single-step model; FRD
supplies increment identity, while DAT increment identity is not required.
`FREQUENCY=1` requests output at every accepted increment; require emitted FRD
frames through normal terminal completion. The explicit branch does not call the
STA/CVG writers or print the implicit increment trace, so these may be absent or
header-only and stdout is diagnostic/terminal evidence, not a state source. RF
is captured diagnostically with no reaction-magnitude gate.

For U, V, energies, mass, and ENER, the frozen comparison rule is
`abs(actual-expected) <= 1e-9 + 1e-4*abs(expected)`. The analytical oracle is
checked at the actual native-reported accepted times. The separate diagonal-
only initial-acceleration signature in `preflight.json` is a failure
diagnostic, never an alternative pass criterion.

## Pinned primary sources

- Official CalculiX 2.23 source archive SHA-256:
  `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`.
- `e_c3d.f` SHA-256
  `d009650b48e5ca150080aed9e19d1b65d2b2cf4869ab6d7f2b1a5cd55e2df3fc`,
  lines 1921–1975: explicit C3D10 mass lumping, with the 10-node factor
  `alp=0.1203`.
- `nonlingeo.c` SHA-256
  `8684bb6d7fa7097c0a854db5a45eb9e2d11adfde574e688184ecbbbad56ff83f`,
  lines 899–1052, 1260–1444 and 1607–1615: dynamic initialization,
  stable-step selection, explicit initial acceleration from net force divided
  by lumped mass, and the implicit-only stdout increment-trace guard.
- `tempload.f` SHA-256
  `8933ca0a5bb9fa3db2b55b4ec9344be9dca1297763f5ea28f6ef7c9074ea84aa`,
  lines 356–373: an unamplified load remains at full reference value in a
  non-static step.
- Official 2.23 manual PDF SHA-256: `a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`.
  Relevant HTML manual pages and recorded digests are in `source-snapshot.json`:
  node180 (explicit integration/scaling), node273 (`*DYNAMIC`), node279 (`*EL FILE`
  and `ENER`), and node283 (`*EQUATION` first-term elimination).

The packet is reproducible against the pinned source archive and solver
profile. Input hashes are `direct=5929594f1e415d82d392990ce26c63944a685a6a9fe27ae2cc1aeecfee20cbc4` and `mapped=7de9a6fa810bba7a3ce8676d4d4fa1322527df1949fe6501de2cdbd44585a286`; the shared
mesh digest is `3baeb35817ce1d9477edf213ba148c8e626659e979f75fa672755b387711d3dd`.

## Limits

A pass would qualify only this single-element method question: whether this
homogeneous MPC coordinate substitution preserves a known force-driven
acceleration and energy response under the pinned explicit implementation.
It does not qualify contact, wood, bolts, joint bearing, the current joint,
service demand histories, or a quasi-static interpretation. It creates no
physical load history and makes no structural acceptance claim.
