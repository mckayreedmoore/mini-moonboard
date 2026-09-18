# Actual-foot contact convergence diagnosis

## Reduced actual-leg experiment

The unchanged actual left leg converges under an explicitly supported coupon
boundary condition. This narrows the numerical question; it does **not** establish
an unanchored board solution, connection capacity, or local contact validity.

The minimum test extracts the complete `Volume8` from the frozen 60 mm
`2x8-foot100` frame mesh: 968 C3D10 elements, 2,147 nodes, and 16 actual floor
faces. No mesh is regenerated. Its original quadratic midside positions remain.
An independent CAD comparison identifies the volume as the actual undrilled
`leg_left`, rather than relying on the volume label:

| Check | Frozen extracted mesh | Actual leg CAD |
|---|---:|---:|
| Volume, mm³ | 13,134,215.2807 | 13,134,223.7342 |
| Centre x, mm | -1,276.3500000 | -1,276.3500000 |
| Centre y, mm | 1,103.0952502 | 1,103.0950409 |
| Centre z, mm | 888.4518361 | 888.4521861 |

Bounding coordinates agree within 0.052 mm; integrated mass is 7.880529 kg
at 600 kg/m³. All floor faces have an outward normal exactly opposite the
upward ground normal. The maximum midside departure from a straight element
edge anywhere in the leg is 3.157915 mm.

The upper 60 mm patch (46 nodes) is permanently restrained in x and y, with z
free. This explicitly represents the missing frame's lateral support and avoids
claiming that an isolated leaning leg is statically balanced without it. The
fixed ground remains the same C3D8 master floor; timber uses E=7,000 N/mm²,
ν=0.3, normal penalty 10,000 N/mm³, tangential penalty 100 N/mm³, and μ=0.3.
Step 1 applies gravity; step 2 adds 1,200 N downward distributed over the upper
patch. This coupon restraint must never be treated as an accepted full-board
anchor or a removable full-board initialization guide.

The hypotheses were ranked before running: a defect intrinsic to the actual
quadratic foot geometry or face orientation might also fail the unchanged
coupon; unconstrained startup of the assembled frame could instead fail only the full frame; an
isolated freely tipping leg would be a different physical problem and is excluded
by the explicit upper support. Because the original coupon converged, no
straight-midside comparison or contact-parameter sweep was needed.

CalculiX 2.21 completed both steps with 12 accepted increments per step.
The audit requires complete displacement output for every timber node and
complete reaction output for all ground and upper-guide nodes. It balances
gravity and applied loads with ground and guide reactions about the **deformed**
configuration. Upper z is unconstrained, so its nodal force output is not counted
as a support reaction.

| Endpoint | Gravity | Gravity + 1,200 N |
|---|---:|---:|
| Floor reaction y, N | -11.515169 | -253.504770 |
| Floor reaction z, N | 77.281590 | 1,277.281700 |
| Upper guide reaction y, N | 11.515173 | 253.504540 |
| Maximum force residual, N | 0.000004 | 0.000230 |
| Maximum moment residual, Nmm | 0.010421 | 0.507651 |
| Maximum nodal displacement, mm | 0.008445 | 0.294770 |

Necessary aggregate compression/friction bounds pass. The result rules out the
actual leg floor-face geometry, face identification, and curved C3D10 elements
as a sufficient explanation of the original zero-accepted-increment failure.
It does not eliminate effects involving other floor patches or assembly freedom.
An independent connectivity check of the complete frozen mesh finds one
connected component containing all 62,020 nodes and 32,511 elements, including
610 floor nodes. Disconnected free timber bodies therefore do not explain the
original failure; this topological check is not a structural validation.

## Local contact qualification

Read-only examination of the 43 actual foot nodes gives:

| Nodal diagnostic | Gravity | Gravity + 1,200 N |
|---|---:|---:|
| Physical vertical gap range, mm | [-0.000013372, 0.000619346] | [-0.000325019, 0.027450910] |
| Reported COPEN range, mm | [-0.000010617, 0] | [-0.000242448, 0] |
| Reported CPRESS range, N/mm² | [0, 0.106171] | [0, 2.424480] |
| Maximum reported shear magnitude − μ·max(pressure,0), N/mm² | 0.000508366 | 0.031925041 |

The reported nodal CONTACT fields are not an integration-point complementarity
audit. In particular, the positive nodal friction excess above prevents treating
these recovered fields as proof of local Coulomb compliance. Physical gaps and
reported COPEN also differ. The retained result is therefore **two complete,
equilibrium-audited conditional coupon steps; local contact audit still required**.
No broad physical stability conclusion follows from solver completion.

## Reproduction and evidence

From the repository root, prepare CAD provenance on the host and solve in the
existing pinned Docker build:

```sh
uv run python -m fea.foot_contact_repro --prepare
docker run --rm --user "$(id -u):$(id -g)" -e OMP_NUM_THREADS=2 \
  -v "$PWD:/work" mini-moonboard-fea:box-v1 \
  python3 -m fea.foot_contact_repro --max-seconds 120
uv run pytest -q tests/test_foot_contact_repro.py
```

The harness refuses to overwrite an existing CAD reference or result record.
Source mesh, frozen CAD digests, generator code, intended deck, and output hashes
are recorded before/after launch under
`fea/generated/foot-contact-diagnosis/actual_leg/actual_leg.json`; the corresponding
`.inp`, `.dat`, `.sta`, `.cvg`, `.log`, and `.frd` remain alongside it. Historical
CAD and prior solver results are unchanged.

Published evidence is retained in
[the coupon report](../fea/results/foot_contact_diagnosis/actual_leg/actual_leg.json),
[CAD reference](../fea/results/foot_contact_diagnosis/actual_leg/actual_leg_cad.json),
and [compressed solver evidence](../fea/results/foot_contact_diagnosis/actual_leg/solver_evidence.tar.gz).
The [exact launch generator](../fea/results/foot_contact_diagnosis/actual_leg/foot_contact_repro.launch.py)
matches the recorded launch hash. Subsequent harness checks reject invalid
gravity contexts, changed decks, and orphan prior output files; these changes
do not rewrite the historical launch hash. The final auditor was replayed
successfully against the saved DAT and exact regenerated deck.

Frozen mesh SHA-256:
`684cc4ecc2fc2f1d15ad19fcae2a01e5cb24b990591176009cf86469ec2cdeac`.
Coupon deck SHA-256:
`7738f7fba3d00ae51c749eecef7f121457bbce00dc2abb2a7a842f6524385e01`.
Coupon DAT SHA-256:
`ab0271d8d247599fa06ab768bbd18848b6b55619a01f35134f287c6a336cc4ff`.
Coupon FRD SHA-256:
`adcfbbe8a566146de90b90407000ab479ee3d71ba10952528b488a340c3eb9a9`.
Evidence archive SHA-256:
`cfb7303d628a8d53677cebf38ac4171238a39269244becd4942ad13034194a7f`.

Focused regression checks now pass 22 tests; one optional Gmsh replay test is
skipped outside the solver environment. The equivalent archived-DAT replay
was also run successfully in the pinned Docker image. Checks cover unchanged
volume extraction, explicit conditional x/y support with z free, face normals,
successful equilibrium, force and moment perturbations, missing/duplicate
output, invalid coordinates and gravity contexts, arithmetic overflow, and
the published archive hashes and exact intended deck.

Independent correctness, testing and architecture review found an invalid-input
acceptance gap and missing successful-audit/replay coverage. Both were fixed;
the recorded physical inputs and numerical results were unchanged.
