# Recovered reinforced-frame fastener checks

The native F10 / 250 lb / 1,000 N/mm case supplies actual modeled reactions for
**66 SPAX screws and 22 retained ML24Z angles**. The largest panel attachment
is `round_panel_upper_left_center_3`: **1,618.184 N tension and 439.589 N shear**,
giving **3.032 head utilization and 2.618 wood interaction** under the stated
dry-service resistance assumptions. These exceedances belong to the solved
sticking-floor model; the floor condition does not pass its friction check.

[Consumer](../fea/reinforced_fastener_checks.py) ·
[Saved comparison](../fea/results/reinforced-fastener-checks-F10-k1000-v4.json) ·
[Tests](../tests/test_reinforced_fastener_checks.py)

## What the input establishes

The v3 input converged after 13 contact cycles and passes its global-equilibrium,
MPC and closed-bearing/contact gates. Its archived source snapshots match the
report's declared source hashes. The current runner subsequently changed, so the
consumer records that difference rather than presenting the archived runner as
the current source. Complete isolated replay has not been verified; the producer
archive was reported to omit an additional stress-module dependency.

The floor uses sticking tangential springs. Its per-foot friction-wrench
witnesses require coefficients **2.176 for the left center post and 3.318 for
the right center post**, exceeding the explicit 0.4 assumption. A resultant
shear/normal ratio alone is not the complete footprint-wrench test. Therefore
the saved status is `CONVERGED_STICKING_MODEL_FLOOR_NOT_ACCEPTED`; this is not
an accepted physical demand envelope. Changing floor restraint can redistribute
the same joints' demands. The gross-member, panel and rigid-connector assumptions
remain those of the native producer.

## SPAX sign, resistance and actual comparison

The native record's first body is receiver wood and its installation axis points
into that wood. Thus `T=max(0,-dot(force_on_receiver,axis))`; the opposite sign
is compression. Shear is the magnitude perpendicular to the axis. The consumer
checks member ownership, axis, application point and action/reaction before
using those values. Positive axial compression is reported separately and is
not silently accepted as screw/contact capacity.

References are **533.787 N head pull-through**, **733.601 N receiver withdrawal**
and **235.680 N lateral**. The direct SPAX head-column selection and assumed
CD=CM=Ct=1 are documented in the [applicability decision](reinforced-fastener-applicability.md).
The existing [wood interaction equation](round-structural-screw-calculation.md)
is evaluated per screw. No equal sharing or screw-count multiplier is used.
For the governing screw, the isolated steel tension/shear component ratios are
0.791 and 0.286. No published combined-steel equation was established here;
two component ratios below one do not mark combined steel action passed.

## ML24Z transfer and missing directions

For each angle, the consumer recovers the three-screw beam-flange and upright-
flange wrenches about the recorded CAD station origin. It also sums all six
screws as a free-body residual. The latter nearly cancels—maximum force residual
is 0.030 N—and must not replace the transferred flange load.

For the sixteen single/end analogies, use absolute projected forces with
595/450/450 lbf along F1/F2/F3-or-F4. Taking 450 lbf for either opposing side
avoids an unsupported assignment of the larger 750 lbf direction. The largest
force-only unity is **0.947**, at `clip_split_top_center_left`. Its loaded-flange
force is `(-350.565,-1024.420,1285.230) N`; moment is
`(-30170.362,17831.339,786.476) N·mm`. The parallel couple is **−3974.546 N·mm**,
which cannot be removed by moving the force reference point. No ML connection
is declared passing while its independent couple remains unresolved.

The six bearing-like stations have the following recovered separation demands:

| Station | Separation demand, N |
| --- | ---: |
| Header/outer post left | 18.864 |
| Header/outer post right | 2.194 |
| Center principal/header left | 0.000 |
| Center principal/header right | 85.236 |
| Header/center post left | 78.871 |
| Header/center post right | 54.605 |

Zero separation in this case does not establish zero in other cases. Rated
shear-only unity and both full flange wrenches are retained for every station;
unlisted F2 capacity remains null. Grain/mounting applicability and independent
moments remain explicit duties from the [22-station lookup](reinforced-fastener-applicability.json).

## Reproduction

```sh
uv run python -m fea.reinforced_fastener_checks \
  --demands /tmp/reinforced-F10-k1000-v4/report.json \
  --floor-friction 0.4 --output /tmp/reinforced-fastener-checks.json
uv run pytest -q tests/test_reinforced_fastener_checks.py
```

Use a fresh output path. The saved result embeds the physical input forces,
report hash, producer artifact manifest and consumer hashes, so its numerical
comparison remains inspectable. Artifact bytes and isolated native replay are
separate verification gates. Unconverged or unmatched archived-source input
requires the explicit `--allow-invalid-diagnostic` flag and remains diagnostic.

## Completed stiffness comparison

The [1,000 N/mm baseline](../fea/results/reinforced-fastener-checks-F10-k1000-v4.json)
and [10,000 N/mm sensitivity](../fea/results/reinforced-fastener-checks-F10-k10000-v5.json)
both converge numerically and both fail the stated floor-friction assumption.

| Conditional response comparison | 1,000 N/mm | 10,000 N/mm |
| --- | ---: | ---: |
| Maximum SPAX head ratio | 3.032 | 4.316 |
| Maximum SPAX wood interaction | 2.618 | 5.984 |
| Maximum single/end ML force-only unity | 0.947 | 0.921 |
| Maximum unlisted bearing-like separation demand | 85.236 N | 178.457 N |

The harder case's maximum wood interaction occurs at upper-left center screw
4 (190.451 N tension, 1414.694 N shear), whereas its maximum head ratio occurs
at screw 3 (2303.746 N tension, 877.454 N shear). Do not label the wood ratio
at the maximum-head screw as the maximum over all screws.

No ML connection receives a pass from the force-only unity: each flange's
couple remains explicit, and the six bearing-like installations still lack
a demonstrated applicable separation/couple load path. These numbers describe
the solved sticking models; they are not accepted actions for a μ=0.4 floor.
Native reproduction bundles are indexed in the [release decision](reinforced-release-checks.md).
