# PB02 native whole-frame diagnostic contract

This diagnostic prepares the `pb02-kerf-right-native-development-only`
candidate in the current-response whole-frame model. It preserves the six
kerf-right panel solids and all 66 panel/kicker screw axes. Two right-center
kicker receivers move to the backer without moving their axes. The model keeps
22 unchanged legacy connector stations as response proxies.

The connected PB02 joint inventory is exactly:

- 10 tension-only axial bolt rows;
- 20 lateral bolt rows;
- 28 canonical compression-contact rows; and
- four additional samples across the direct shifted-post/base-header face.

The four direct samples divide the selected total face-normal stiffness equally
and do not credit backer/post contact. Automatic principal/header bearing from
the current-response model remains present. The preparation also includes floor
bearing for the shifted right post, backer, and rear cleat.

## Trial stiffness boundary

Every run must supply positive finite values for bolt axial stiffness, bolt
lateral stiffness, and total face-normal stiffness per interface. The published
stiffness-basis record supports sensitivity selection; it does not qualify a
complete joint. Washer/contact compliance and a qualified axial joint stiffness
remain unresolved. These inputs are numerical trial parameters, not strengths,
capacities, or accepted design properties.

## Six-case runner

The runner uses this fixed order:

1. `a12-forward`
2. `a12-rear`
3. `a12-left`
4. `k12-right`
5. `k12-rear`
6. `a1-rear`

It first tries `a12-forward` with the unseeded `all` contact update. Only
active-set nonconvergence permits an unseeded `one_at_a_time` retry. If both
fail, the runner authenticates `a12-rear`, trying those same two strategies in
order, and may then seed one final `a12-forward` `one_at_a_time` attempt from
the accepted rear-case normal-contact set. Other cases use the two unseeded
strategies in the same order. A rejected attempt contributes no forces to the
suite summary.

Before and after solving, the runner checks geometry, topology, candidate and
load identity, selected stiffnesses, source hashes, active-set convergence, and
global/member equilibrium. Accepted here means numerically authenticated only.

## Artifacts

Each attempt is written below `attempts/` with the native model artifacts. A
numerically authenticated case also receives `diagnostic-scope.json` and an
updated `report.json`. The suite-level
`pb02-six-case-diagnostic.json` records the deterministic input fingerprint,
stiffness selection, attempt history, validations, and paths and hashes for the
six accepted case reports. It does not copy rejected-run forces.

No PB02 six-case run is claimed by this document. The preparation and runner
are developmental tooling only: no joint strength or resistance is established,
and no design acceptance, drilling, or fabrication is released.
