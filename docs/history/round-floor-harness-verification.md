# Floor and intact-harness verification boundaries

This assessment separates the current `round-insert-development` results from
the historical ordinary-screw `round-bore-service-development` results. No
physical floor, harness-feed or removal test has been performed.

## Current insert candidate

The [current floor screen](../fea/results/round-insert-floor-v1.json.gz) and
[recomputed floor/harness summary](../fea/results/round-insert-floor-harness-v1.json)
use the insert candidate's exported routing. The summary verifies its candidate
identity and routing bytes against the export manifest, verifies the measurement
reference hash and recomputes force/hull bounds from the saved raw wrenches.
It records input hashes but does not revalidate every transitive source file.

| Quantity | Current insert candidate |
| --- | ---: |
| Modeled mass | 167.598 kg |
| 80% mass case | 134.079 kg |
| Maximum necessary resultant-force friction ratio | 0.151355 |
| Governing horizontal / normal force | 300 / 1,982.095 N |
| Minimum sampled normal-resultant distance inside the support hull | 86.381 mm |
| Feasible witnesses at assumed μ = 0.10 / 0.20 / 0.40 | 533 / 1,296 / 1,296 |
| μ = 0.10 failures proven by the circular force bound | 720 |
| Additional μ = 0.10 polygon-only infeasibilities | 43 |

The governing friction-bound case remains a 150 lb, factor-one climber at A1,
80% frame mass and 300 N horizontal load. The minimum hull margin remains the
300 lb factor-two A12 case at 80% mass with a 90-degree horizontal force. Mass
includes simplified zinc insert envelopes at an assumed 6,700 kg/m³, steel at
7,850 kg/m³ and wood/plywood at 600 kg/m³. Actual alloy, product mass and delivered
material density remain unverified; holds and electrical mass are omitted.
Neither the small mass increase nor these feasible witnesses qualifies contact,
friction, dynamics or strength.

The current [insert-candidate routing](../exports/round-insert-development/wiring.json)
retains 131 links, 32 passages and the dimensions discussed below: longest link
268.004 mm, 36.796 mm remaining against approximate pitch, 6.35 mm nominal radial
passage gap and 38.1 mm maximum timber traverse. These are computations, not a
successful physical feeding or removal trial.

Reproduce the current arithmetic without CAD or a new solver run:

```sh
uv run python -m fea.round_floor_harness_assessment \
  --floor fea/results/round-insert-floor-v1.json.gz \
  --wiring exports/round-insert-development/wiring.json
uv run pytest -q tests/test_round_floor_harness_assessment.py
```

Omitting both path arguments reproduces the historical ordinary-screw study.
Use `--output` only with a new destination; existing reports are not overwritten.

See also the [new mat, hardwood and carpet scenarios](round-floor-surface-assumptions.md)
for separately assumed interfaces, layer elevations and rear-foot contact loss.

## Historical ordinary-screw floor comparison

The [saved floor screen](../fea/results/round-service-floor-v1.json.gz) integrates
167.079 kg of modeled wood and hardware; lighting and holds are excluded.
Its lower mass case uses 133.663 kg (80%) at the same center of gravity. Four
posts and two leg feet receive support credit. Coplanar kicker edges do not.

| Assumed friction coefficient | Feasible rigid-equilibrium witnesses | Other outcomes, out of 1,296 cases |
| --- | ---: | --- |
| 0.10 | 533 | 720 provably fail the circular resultant-force bound; another 43 fail only the inscribed polygon calculation |
| 0.20 | 1,296 | No sampled infeasibility |
| 0.40 | 1,296 | No sampled infeasibility |

A necessary force-only condition is `μ ≥ horizontal force / total normal force`.
The largest required ratio is **0.151667**, from 300 N horizontal force and
1,978.021 N normal force: a 150 lb, factor-one climber with 80% frame mass.
This is a lower bound, not a sufficient friction specification: yaw balance,
contact location, compliance and load history still matter. Increasing climber
weight can improve this particular sliding bound while increasing other demands;
the lightest case must therefore remain in the matrix.

The smallest sampled normal-resultant distance inside the credited support hull
is **85.606 mm**, at A12 with the 300 lb factor-two case, 80% mass and a 300 N
90-degree horizontal force. That is a static resultant location, not a permitted
floor-level error or a dynamic tipping margin. The calculation allows point
reactions; it does not predict local pressure or guarantee all six members touch.

To reuse these results, establish the actual foot/floor pair, any pads or mats,
surface condition, floor flatness, support footprints, delivered assembly mass
and center of gravity. Contact compatibility, floor/subfloor bearing and a
justified lower-bound friction value require a separately reviewed assessment
for that material pair and condition. An assumed rubber coefficient, a person
holding the frame, or a hanging-person slip trial cannot supply that evidence.
The 0.20 result covers nine hold positions and eight horizontal directions at
specified loads, not every possible motion, azimuth or airborne catch.

## Harness: shared route, measurements and physical limits

The displayed wiring covers the **132 active bulbs and 131 links only**. It
omits the unused factory tail, A1 input lead, supplementary power-feed branch,
extensions, controller and supply. Connector cylinders at 50/51 and 100/101
are provisional envelopes, not verified complete branch geometry. The
[material and LED verification note](round-material-led-verification.md#active-route-scope-and-the-rest-of-the-physical-kit)
records the official-kit discrepancy and retained active-route scope. The
feed/removal gate applies to the complete physical kit, including these omitted
components, not only the displayed active links.

The owner reports a maximum component diameter of **12.7 mm** and approximately
**304.8 mm bulb-base pitch**. The [historical routing schedule](../exports/round-bore-service-development/wiring.json)
contains 131 links and 32 nominal 25.4 mm passages. Straight, centered passage
clearance is therefore nominally **6.35 mm radially**. Each current timber
traverse is about 38.1 mm; CAD cutting cylinders extend beyond the wood and must
not be mistaken for physical traverse length.

The longest modeled link is A7–A8 (other row-7/8 links tie): **268.004 mm** with
8 mm modeled corner radii, leaving **36.796 mm** against the approximate pitch.
Its unsmoothed polyline is 270.089 mm, leaving 34.711 mm. Neither remainder is
verified usable slack. Rigid bodies, strain relief, the shortest delivered
segment, required bend radius and deviations during feeding consume space in
ways that the centerline comparison does not establish.

The reference still assumes 30 mm connector length, 12 mm rear projection and
4 mm cable diameter. Those are not owner measurements. Nominal round clearance
does not prove a long connector can align with a passage when adjacent panels,
timber or a branch limit its turning room. The modeled 8 mm radius is not a
manufacturer-approved bend limit. Loose surplus cable, strain relief and the
external controller/extension arrangement are not fully modeled.

Before installation approval, record the shortest actual bulb-base interval,
maximum rigid connector length including strain relief, rear bulb projection,
cable diameter, permitted bend radius and actual connectors/branches. Then check
a representative, independently supported assembly or nonstructural mockup with
panels already in place: feed the intact strand through the most constrained
passages before seating bulbs, demonstrate joins and supplementary power access,
and demonstrate reverse removal without forcing, cutting or splicing the harness.
The longest row-7/8 link and the two factory string joins deserve explicit
witnesses. Record the actual route, available slack and obstructions. This is a
fit/handling demonstration, not a structural proof test. Use the
[disassembly support requirements](disassembly-guide.md) for any actual frame.

## Decisions still requiring measured input

- Identify the actual floor and every intervening contact layer, its condition
  and supported contact geometry; establish the delivered assembly mass/CG.
- Measure the harness dimensions above and obtain its bend/handling limits.
- Demonstrate intact lights-last feeding and removal with those components.

These are concrete missing inputs. Geometry and finite static witnesses cannot
turn them into completed physical verification.
