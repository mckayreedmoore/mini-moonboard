# Directional stress demands in the reduced frame

The new postprocessor reports signed normal and shear stresses from the current
reduced C3D20/S8 model. It does not assign wood or plywood capacities, produce a
von Mises strength verdict, or turn solver convergence into member adequacy.

The native deck requests `S,COORD` with `*EL PRINT,ELSET=...,GLOBAL=YES` separately
for every physical member and panel group. Springs are excluded. The reader
requires all 27 integration points for each C3D20 element and each expanded S8
shell element, with matching coordinate records and element-set ownership.
Missing, duplicate, nonfinite and incorrectly owned output is rejected.
CalculiX documents integration-point output and shell expansion in its
[user manual](https://www.dhondt.de/ccx_2.19.pdf), under *EL PRINT, C3D20 and S8.

For lumber, the global stress tensor is rotated into the recorded grain and
two section directions. For plywood, it is rotated into geometric panel X/Y
and normal directions. Those geometric directions are not a claim about the
purchased plywood's strength axis or veneer layup. Stress components are true
tensor shear components; no engineering-strain factor of two is introduced.
Every minimum and maximum includes its element, integration point, coordinates
and full simultaneous tensor. The shear-vector magnitude on the first local
plane is calculated at each point before taking the maximum; independent
component peaks are not combined from different locations.

These are sampled integration-point demands. Surface stresses can be larger,
and concentrated attachment springs or clamped ends can produce mesh-sensitive
peaks. Constant retained timber sections omit actual service-pocket transitions,
bolt holes, local splitting and bearing damage. Isotropic plywood omits veneer
orientation, directional bending/rolling shear and actual hold/fastener contact.
The stiffness assumptions, closed-contact status and numerical gates of the
parent solve remain applicable to every stress report.

No grade value is applied automatically. A future resistance check needs the
actual lumber species/grade/service basis and member-specific adjustments,
separate axial/bending/shear and stability treatment, and verified load demands.
A maximum longitudinal point stress cannot simply be divided by a bending
allowable when it also contains axial or local effects. Plywood needs its own
directional product capacities and a compatible laminate/section formulation.

The useful next decisions are to identify which members and load cases attract
high directional demand, check whether peaks occur at artificial point
connections or real member spans, and refine the governing load path before
selectively enlarging timber. This output narrows that investigation; it is not
a construction release.

```sh
uv run pytest tests/test_horizontal_frame_stress.py -q
uv run python -m fea.horizontal_frame_stress /path/to/native/cycle \
  --output /tmp/directional-stress.json
```

The standalone reader authenticates the saved input/deck/output and source
snapshots against the native report. A report whose equilibrium, interpolation
or closed-bearing gates fail retains that failed status alongside the stress
demands; those demands are not an accepted current-frame response.

## Ten-case batch: stress sensitivity remains open

The completed `horizontal-frame-batch-v2` working evidence contains ten cases
with passing equilibrium, interpolation and active-contact checks. Eight apply
the load through the panels; two are matched framing-load controls. The following
values are sampled demands from the eight coupled cases, not material ratings.
Panel shear below is the largest individual tensor shear component, which occurs
in the geometric panel-Y/normal plane. It is distinct from the smaller shear
vector on the panel-X plane reported elsewhere in the JSON.

| Coupled case | Maximum timber grain-normal magnitude, MPa | Maximum panel normal magnitude, MPa | Maximum panel shear component magnitude, MPa |
| --- | ---: | ---: | ---: |
| C10, 250 lb, 100 N/mm | 5.202 | 24.433 | 13.139 |
| C10, 250 lb, 1000 N/mm | 4.352 | 24.324 | 13.138 |
| C10, 250 lb, 10000 N/mm | 3.750 | 24.317 | 13.137 |
| C10, 300 lb, 1000 N/mm | 4.978 | 29.270 | 16.075 |
| F10, 250 lb, 1000 N/mm | 7.705 | 30.607 | 14.451 |
| C6, 250 lb, 1000 N/mm | 4.841 | 19.717 | 13.782 |
| C7, 250 lb, 1000 N/mm | 3.655 | 23.267 | 13.622 |
| C10, 250 lb, refined mesh | 4.349 | 26.207 | 14.060 |

All cases retain the specified doubled vertical climber load and 300 N
horizontal component. The stiffness column describes assumed individual
attachment springs, not measured product stiffness. The refined case changes
member/panel mesh targets from 100/80 mm to 75/50 mm, increasing sampled stress
points from 68,958 to 126,954.

Refinement changes panel displacement by only **0.074%**, but panel normal stress
increases **7.74%** and the largest panel shear component increases **7.01%**.
The panel-X-plane shear-vector maximum increases **15.82%**, from 4.951 to
5.734 MPa. In contrast, the top-rail grain-normal peak changes by −0.072%.
Consequently, the near-identical displacement does **not** demonstrate converged
panel stress, and two meshes do not establish a strength-convergence criterion.
The C10 panel extrema occur near the loaded patch and its imposed couple; they
need a more representative hold/attachment load-introduction model before a
local plywood resistance comparison.

F10 warrants further attention despite its center location: it produces the
largest panel normal stress and top-rail grain-normal demand among these
coupled cases. Its largest panel-screw resultant is approximately 1,111 N and
its largest individual angle-screw resultant approximately 1,068 N, at a center
top connection. Those individual forces are not whole-bracket directional
ratings. C6/C7 exercise opposite sides of the horizontal seam and move the
highest timber normal demand into the left center principal.

Connection stiffness is also consequential. At C10, the maximum panel-screw
resultant changes from approximately 448 N at 100 N/mm to 1,504 N at 10000 N/mm;
the corresponding maximum leg-bolt resultant changes from 596 N to 1,416 N.
This is a sensitivity result, not proof that stiffer attachments are safer.
The matched controls' approximately 37.5% reduction in timber displacement
shows a panel-stiffness contribution under their common framing loads. It does
not assign the physical coupled case a strength benefit or validate a panel
attachment schedule.

Priorities are therefore the F10 top-rail/center connection, credible local
panel load introduction and directional material assessment, and attachment
stiffness/demand sensitivity. The selected DF-L No. 2 dry lumber and APA PS 1
Structural I 23/32 48/24 panel procurement basis should inform that next model;
they do not make these homogeneous isotropic point stresses directly comparable
to published member or panel design capacities. Actual grain/strength-axis
orientation, delivered product identification and the governing resistance
formulation still matter. No automatic timber enlargement or construction
release follows from this batch.

The large panel-Y/normal shear was checked against the raw global tensor and
actual panel axes. At the C10 reference witness, rotation gives approximately
−13.138 MPa shear while the panel-normal stress is only 0.0038 MPa; this is not
a double rotation of local output. `GLOBAL=YES` is the documented native output
setting, and the DAT component order agrees with the parser. The witness lies
inside the 20 ×20 mm load-patch element. Its imposed 164,885 N·mm standoff couple
has an approximately 8.24 kN force-pair scale across 20 mm, and individual saved
patch nodal force components reach approximately 4.31 kN (maximum nodal resultant
6.07 kN). Large local shear is consequently
plausible for this concentrated diagnostic load introduction. It must not be
presented as measured hold-seat pressure or a validated plywood rolling-shear
failure prediction.

## Completed load-patch sensitivity

The additional `horizontal-coupled-c10-patch80-v1` calculation passed its force,
moment, interpolation and compression-only bearing checks. It applies precisely
the reference C10 force `[0, 300, -2224.1108]` N and panel-midplane couple
`[-164885.1153, 0, 0]` N·mm through an assumed 80 ×80 mm patch. All other load,
material and connector-stiffness parameters retain the reference values. The
mesh contains the new patch boundaries, so this comparison changes both the
load footprint and its local discretization; it is not a stress-convergence test.

| C10 quantity | 20 ×20 mm reference | 80 ×80 mm sensitivity |
| --- | ---: | ---: |
| Maximum panel displacement, mm | 16.2731 | 16.2142 |
| Applied-load work, N·mm | 33450.5 | 32008.3 |
| Upper-left panel geometric-Y normal magnitude, MPa | 24.3239 | 12.0723 |
| Upper-left panel Y/normal tensor shear magnitude, MPa | 13.1381 | 1.5750 |
| Maximum timber grain-normal magnitude, MPa | 4.35172 | 4.35168 |
| Largest connector resultant, N | 736.166 | 736.165 |
| Largest patch-node resultant, N | 6070.25 | 1991.91 |

Panel displacement changed only −0.362%, while the listed local normal stress
fell 50.4% and local Y/normal shear fell 88.0%. The top-rail grain-normal demand
and governing leg-bolt resultant were essentially unchanged. This supports a
specific interpretation: the very large local stress from the 20 mm reference
is strongly sensitive to how the hold force and offset couple enter the panel.
It is not sufficient evidence to declare plywood failure or select thicker
panels. The work change, −4.31%, also shows a local-compliance effect despite the
small change in maximum global displacement.

The 80 mm footprint is a diagnostic assumption, not a verified physical hold
seat or a recommendation for hold dimensions. Actual hold contact, bolt/T-nut
load transfer and plywood directional behavior remain to be modeled. No panel
strength result follows from either patch. The C10 patch is wholly within one
panel; the same 80 mm square at F10 would cross a seam and is rejected until an
explicit separate-panel load allocation is defined.
