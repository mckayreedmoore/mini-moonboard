# Upper-right whole-block integration

## Completed finite calculation

This packet combines the completed [rail pair](upper-right-rail-pair.md)
and [side pair](upper-right-side-pair.md) at the current cleat's node-mean
datum `[1082.675, 1405.0269362284803, 2125.1250400802173]` mm. Both use
one fixed rigid cleat, two beams and one compatible host pose per interface.
All four bolts and 32 existing face cells are retained in each of the six
nominal-clearance cases. No new mechanics or geometry solve was required.

The current frame's 44 incident rows comprise the two host interfaces only.
Its mapped dead-load wrench, including assigned hardware, is retained once:
`[0, 0, -10.530841; -38.512329, 7.883119, 0]` N/Nmm. The moment is the
existing mapped couple about the common datum; it is not replaced by a
bare-timber weight at an invented centre. No additional gravity is applied
to the frozen host drives.

For each host, the calculation adds its two bolt wrenches and face-contact
wrench, reverses their sign, and shifts the result to the common cleat datum.
Those are the energy-dual reactions of the same rigid-cleat model. All six
combined force/moment residuals remain within the original pair tolerances;
maximum component residuals are 0.000010480 N and 0.000488616 Nmm.
The original current-frame cleat balance is independently retained through
its `D` rows and `W` load. The opposite host-reaction sum is not an independent
recovery of elastic timber tractions.

## Same-state component results

Each reference below uses the changed individual bolt response, not an old
ratio or an average of the two bolts. The single-shear function, grain axes,
139.7/38.1 mm rail and 88.9/88.9 mm side bearing lengths, finished bore-tangent
paths and supported washer annuli are reused unchanged. Conditional Grade 5
`Fyb = 92 ksi` and the recorded DF-L No. 2 references remain explicit.

| Component screen | Maximum index | Governing state / axis |
| --- | ---: | --- |
| Single-shear lateral / adjusted reference | 0.813949 | K12-rear, side 2 |
| Parallel component / declared finished tangent path | 0.160367 | K12-rear, side 2 |
| Full-annulus mean washer pressure / `Fc_perp` | 0.770232 | K12-right, rail 1 |
| Smooth-shank beam VM / conditional 92 ksi | 0.313740 | K12-right, side 2 |

The mean-pressure result improves from the original source allocation's
0.822681 because the compatible rail pair redistributes tension. It does not
assert that tilted-seat peak pressure is uniform or within a qualified local
wood contact law. The pair packets retain their sampled spring pressures.
Bolt steel recovery includes the local beam bending already calculated by
the pair, unlike a direct axial-plus-shank-shear screen.

The current host splitting geometry and original complete-host cut demands
are included for traceability. Their EN 1995 characteristic references are
not adopted design resistances. A preserved group net wrench does not prove
that every cut inside a redistributed group retains its old demand. This
packet therefore does not transfer the old splitting ratios to the new
individual bolt allocations.

## Meaning and remaining scope

The four-bolt rigid-block model has a simultaneous, balanced response in all
six current cases. Host translations and rotations are shifted to the same
datum with one zero-pose cleat gauge. Where the pair tangent has neutral
modes, these remain representative positions, not a unique motion envelope.

Elastic cleat deformation, combined oblique-group/splitting resistance and
actual washer/head/nut properties remain explicit limits. The
[washer edge calculation](upper-right-washer-edge.md) addresses the numerical
stress defect in the earlier washer approximation separately; its assumed
steel properties do not become delivered product properties. These limits
do not restart the completed bolt-fit, annulus-support or hardware-length
checks and do not add a blanket external approval requirement.

Joint qualification and physical release remain HOLD. No source geometry,
hardware selection, full-frame law, formal criterion or authority flag changes.

## Reproduction and receipts

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
uv run --no-sync python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/upper-right-block.py \
  --output /tmp/upper-right-block-fresh
```

Use a new output path. The maintained producer authenticates both complete
pair source closures, current operators, force response and component
geometry before arithmetic, then again before writing its receipt. It calls
the frozen existing single-shear function; no CAD operation, native/frame
solve, software test or review loop occurs.

- Result: `rawlocal/upper-right-block/attempt01/checks.json`, SHA-256
  `0b0b392b9e5e411173395671878c09e0be303abd4885f48d1e7e7b61d8f6a89b`.
- Rail pair: `e0cccb56abb94ed16c322da888cd64a9904c4e49d1e34f573a6903c8b8b98d3d`.
- Side pair: `b507a5a501737c89814a471eee6a12749a3c54224f5444b2c5d583020e875ba7`.
- Full-frame comparison: `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca`.
- Full-frame response: `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7`.

Raw files are ignored; the receipt pins the producer snapshot and result.
