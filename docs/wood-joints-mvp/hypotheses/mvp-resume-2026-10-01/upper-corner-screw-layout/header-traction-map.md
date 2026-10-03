# Header supported boundary mapping

## Decision

The saved header actions have a simple, explicit route onto supported wood:
retain the contact centroids, distribute each axial tie over its supported
washer annulus, and account for the two nonzero lateral states at the bore walls.
The lateral construction requires opposite-wall contact and remains an
unverified compatibility hypothesis. No free balancing couple is introduced.

This packet records that conditional boundary construction. The coordinator
executed the finite arithmetic once; all six states and 36 interface mappings
preserve their saved force and moment balance within the accounting tolerances.
It does not establish a timber stress field or complete joint acceptance.
All joint/release HOLD boundaries, the 47-criterion authority, and native
readiness remain unchanged.

## Frozen scope

The input is the existing [header local-transfer contract](header-local-transfer.md),
using the original 100 mm load lever and six simultaneous nominal-gap force
states. No frame solve, geometry edit, screw-policy change or resistance is added.

| Direct artifact | SHA-256 |
| --- | --- |
| `rawlocal/header-local-transfer/attempt01/inputs.json` | `cccd8969132c30e996fe5d3509069dbe851720786cec92a46a064cc0f7c0758b` |
| Same packet, `model.json` | `eae4fc005cdd079f90f527be611e45a137aa275b129e16eebf964c422d69ae52` |
| Same packet, `header-sections.csv` | `f32ab4731eb4cb12fbdc400f81a0fb9ba8d8065eabbccc378483ecd0b36e5953` |
| Same packet, `receipt.json` | `3b3afc6924dee426c4f0073077e119d906efddcb5ed03a683ec4a3f16fc189a8` |

The producer also authenticates the three existing washer-seat reports, the
saved header STEP binding and the contact-sampler source. Inherited frame
producer hashes remain provenance; this task consumes the frozen contract.

## Practical assumptions and physical actions

### Normal contacts

All 116 header contact-cell centroids lie in their saved occupied patches,
outside every bore. The 18 incident patches are rectangles minus 22 distinct,
complete circular holes. The minimum saved centroid-to-hole clearance is
2.462 mm; the minimum outer-edge margin is 9.492 mm. No point relocation,
new contact grid or CAD run is needed.

The existing sampler represents each exact trimmed cell by its area centroid.
Uniform compressive traction over that cell is the declared normal-pressure
hypothesis. Its centroid action preserves force and first moments. This
does not determine actual pressure peaks, tilt or contact stiffness. The
frozen builder uses 100 mm cells with at least two divisions; the sampler's
80 mm default is overridden. This packet reuses the saved areas and points.

### Header washer seats

All twelve header seats have completed geometric support evidence. Post seats
are on Z = 277 mm, with force into the header along −Z. Principal and knee
seats are on Z = 238.9 mm, with force along +Z. The right principal block's
partial seat is on a different member and remains separate.

Assume a washer concentric with the nominal bore and uniform annular pressure.
Reuse the declared minimum-area plain-washer envelope: inner radius 4.1529 mm,
outer radius 9.2329 mm, area 213.627873 mm². Eight symmetric supported points
give an exact force/first-moment quadrature of that uniform annulus. They are
an accounting representation, not eight physical contact spots or a pressure
peak prediction. Delivered hardware, washer flexure and seating positions
remain unqualified here.

Some axial ties have a shared analytical point outside the header bearing face.
Moving such a force along its own axis preserves its complete wrench. The
producer checks every tie, all 36 simultaneous interfaces and the full header
body against the saved signed actions.

### The two lateral states

Only these saved header lateral states exceed 1e−7 N:

| Case / axis | Header force Fx | Source load plane |
| --- | ---: | ---: |
| A12-left / `center_principal_header_left_2` | −26.392082 N | Z = 277 mm |
| K12-right / `center_principal_header_right_2` | +29.886721 N | Z = 277 mm |

A uniform same-wall bearing force at the 38.1 mm header's mid-depth,
Z = 257.95 mm, leaves approximately 0.503 and 0.569 N·m of the respective
source moment unrepresented. Assigning that difference as a free couple
would hide the load path.

Instead, the bounded construction uses compression on opposite bore walls:
upper point at Z = 267.475 mm carries 1.5 times the signed lateral force;
lower point at Z = 248.425 mm carries −0.5 times that force. Each point lies
on the actual Ø7.3 mm bore wall, with force into the adjacent wood. Their
net force and point-arm moment equal the original upper-face action.

This supplies a static boundary route. It does **not** show that the bolt
bends or seats compatibly against those walls while carrying its concurrent
axial force. The saved radial clearance is 0.475 mm. No additional bolt
bending, washer moment or timber resistance is adopted by this construction.

## Preserve the complete A1-rear witness

At the left-knee paired-hole plane, station 133.35 mm, the saved section has
three separate Y/Z ligaments. Its simultaneous signed actions are:

| Source trace | N (N) | VY (N) | VZ (N) | T (N·m) | MY (N·m) | MZ (N·m) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Before | −3.319 | +151.378 | +32.839 | −8.470 | +8.241 | −12.998 |
| After | −3.319 | +151.378 | −155.117 | −12.768 | +8.241 | −12.998 |

The producer independently restores both source traces from all concurrent
header actions at the exact saved section centroid. It retains their signed
role contributions. The four sampled left-knee normal contact forces are zero
in this case; that does not remove the full header torque. The knee-interface
moment is a separate resultant at a different datum.

Spreading a point tie over an annulus changes cuts *inside* the annulus.
Consequently, these preserved source before/after values are not adopted as
the new physical pressure-map center-plane stress. No unique distribution
among the three ligaments follows from force and moment preservation alone.

## Reproduction and remaining assumptions

Coordinator command, from the repository root:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/header-traction-map.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/header-traction-map/attempt01
```

The fresh child contains `result.json`, `receipt.json`, a producer snapshot
and a local ignore file. The producer rejects changed pins, unsupported
contact geometry, tensile normal contact, substantive source free couples
and force/moment mismatches. Tolerances are 1e−7 N and 1e−5 N·mm; they are
accounting tolerances, not physical uncertainty allowances. No software
tests, frame solve, CAD or native mechanics are run by this task.

A compatible local header/bolt/contact calculation could improve confidence
in torque transfer around the paired holes and the two opposite-wall bearing
hypotheses. This packet does not commission that calculation or make it an
automatic new MVP prerequisite. The saved three-ligament areas, means and
gross-section checks alone do not determine that sharing. Ft-perpendicular
and splitting resistance remain unavailable; this packet invents neither.
The coordinator sets the practical MVP disposition with these assumptions
explicitly retained. This bounded subtask is complete.

## Numeric receipt

The coordinator executed the frozen producer once, exit 0, using Python 3.12.3
and NumPy 2.5.2. The worker then authenticated all ten directly consumed
source pins, the three receipt-listed artifacts, and the returned result and
receipt hashes. Ruff passed; no software tests or mechanics rerun were performed.

| Artifact | SHA-256 |
| --- | --- |
| [Producer](header-traction-map.py) | `87bd3b14e6961b95e04788d89ece412334ff5cc5f4ad735433a8ced97472d34d` |
| `rawlocal/header-traction-map/attempt01/result.json` | `39d63b41dc495659b02cb4ff4fb638a19a491bc09e6ea3fd76a70314db08a837` |
| Same packet, `receipt.json` | `1d454a949640a9b43d6ae3e3cf56ca20705e12ff6ae06f9bb51c1749623d96fd` |

The returned counts are six cases, 36 interfaces, twelve supported header
seats, 72 washer states, 116 header contact cells and two nonzero lateral states.
Full-header mapping differences are below 2e−12 N and 1e−9 N·mm; interface
mapping differences are smaller. These are numerical accounting residuals.

The maximum saved header-seat axial force is 239.705 N, at
`knee_outer_left_inner_header_1`; the declared concentric uniform-annulus
mean is 1.122 MPa. This is a demand under the pressure hypothesis, not a new
washer or timber resistance result. The two same-wall mid-depth diagnostic
moment deficits are +502.769 and −569.342 N·mm; their explicit opposite-wall
point constructions preserve the source wrench.

Both A1-rear 133.35 mm source traces are restored. Its four knee contact
forces remain zero while the full source after-trace torque remains
−12.768261 N·m. Native readiness, compatibility solved, new resistance,
complete joint acceptance and physical release remain false.
