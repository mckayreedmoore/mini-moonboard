# V1 fixed-foot frame FEA screen

This is a reproducible **screening analysis**, not structural approval and not
an unanchored-stability result. It was run because the user requested a
pre-redesign FEA investigation of the current V1 concept. It deliberately
fixes both feet, so it can identify frame flexibility and likely critical
members but cannot show the uplift/overturning mechanism already found by the
[unanchored stability screen](../exports/mini_moonboard_v1_stability_screen.md).

## Model and solver

- Solver: CalculiX 2.16 in pinned Docker image
  `calculix/ccx@sha256:b18b56fec00ad965d85e091454f26195d62115ee9a05feb4c130fa15406b6f7a`.
- Generator: [`generate_v1_fixed_foot_frame.py`](../fea/generate_v1_fixed_foot_frame.py).
  It derives five support-side rail centre-lines, cross ties, and both
  hockey-stick legs from the current CadQuery dimensions.
- Elements: 45 B31 beams, all a provisional 36 x 180 mm rectangle.
- Material: isotropic screening plywood, `E = 7000 MPa`, `nu = 0.30`.
  This is not a manufacturer or received-stock property.
- Boundary: both foot nodes fixed in translations and rotations. This is a
  structural upper-bound idealization, not a claim that the unanchored floor
  interface can provide those reactions.
- Load: a 1.2 kN static point-load screen, distributed equally over the five
  top rail nodes. It is solved in two face-normal directions, board-down,
  lateral, and combined lateral-plus-normal cases.

Run it from the repository root; generated solver files remain ignored:

```bash
uv run python -m fea.generate_v1_fixed_foot_frame
docker run --rm -v "$PWD/fea/generated:/out" \
  calculix/ccx@sha256:b18b56fec00ad965d85e091454f26195d62115ee9a05feb4c130fa15406b6f7a \
  bash -lc 'cd /out && ccx -i v1_fixed_foot_frame'
```

## Solved results

The table records the largest displacement among the five top-rail nodes and
the largest isotropic von Mises value from the beam section output. Stress is
reported only to locate demand; it is **not** compared with a plywood
allowable, because no valid received-stock strength basis has been supplied.

| 1.2 kN case | Max top-node displacement | Max screen stress | Governing member |
| --- | ---: | ---: | --- |
| Face-normal toward support | 350.952 mm | 11.063 MPa | left lower leg |
| Face-normal toward climbing side | 350.952 mm | 11.063 MPa | left lower leg |
| Board-parallel downward | 168.860 mm | 5.522 MPa | left lower leg |
| Lateral left | 174.729 mm | 6.246 MPa | left lower leg |
| Combined lateral + face-normal | 350.965 mm | 11.276 MPa | right lower leg |

For scale only, the 2150.8 mm full V1 assembly height divided by 100 is about
21.5 mm. The 351 mm displacement is over sixteen times that value. `l/100`
is not adopted here as an approved frame criterion—the cited EN panel
criterion applies between surface fixations—but the comparison makes the
global-rigidity problem unambiguous.

## Issues found

1. **Global frame flexibility is unacceptable as currently idealized.** The
   fixed-foot model alone permits 169–351 mm top displacement under the
   screen load. Real unanchored feet, slip, joint clearance, and plywood
   variability can only add mechanisms; they cannot turn this into a pass.
2. **Lower legs govern every solved case.** They need a redesigned load path,
   section/stiffness strategy, and buckling check before a material-strength
   calculation is meaningful.
3. **The fixed-foot result does not cure the primary safety failure.** The
   separate rigid-body screen still predicts floor uplift in both face-normal
   directions. A larger/repositioned base or reviewed ballast strategy must
   be modelled before any unanchored claim.
4. **Connections are not validated.** The screen represents every joint as a
   perfect beam connection. It cannot validate the face-installed screws,
   bolt bearing, washer stacks, glue, rail splices, kicker/main load transfer,
   or plywood tear-out. Those may be more flexible or fail earlier.
5. **Panels and holes are excluded.** The model does not assess panel
   deflection, T-nut pull-out, LED bores, hold/fastener interference, local
   bearing, or the missing reviewer-approved kicker/main connection.

The sensible redesign order is: resolve the unanchored base/ballast strategy,
make a continuous kicker-to-main and leg-to-rail load path, choose actual
material/joint data, then rerun a model with floor contact and connection
stiffness. Do not build, proof-load, or climb from this screen.
> Historical rail-and-spacer revision. For the current box frame, use
> [box-frame-revision.md](box-frame-revision.md) and regenerated schedules.
> The dimensions and analysis below do not describe the current assembly.
