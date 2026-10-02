# Six-case top outer corner action and section checks

The current priority remains the two top outer corner cleats. This packet
advances their complete action accounting and section screens under the
[simple static frame scenario](simple-model.md). It uses the reviewed
`led-clearance-2x6-runner-seated-blocks-v1` geometry, self-weight, the 25 kg
distributed planning allowance and all six recorded climber cases.

The reviewed model and all hardware axes are unchanged. These are conditional
engineering screens; complete joint resistance and all 47 formal criterion
dispositions remain open. The existing upper-left **service** joint owner
has a separate scope. No independent agent review round is scheduled.

## Complete load transfer and bolt sharing

[top_corner_actions.py](top_corner_actions.py) reconstructs physical actions
directly from the existing connector projection: restoring body wrench is
`-D_row_body * f`, with rotational columns multiplied by 1,000 mm. Every
discrete nodal gravity/climber load is independently recomposed and compared
with the source `W` wrench. This avoids inferring physical signs from row names.

The output contains 24 complete receiver-interface states and 30 whole-body
balances: both cleats, both side hosts and the shared top rail in six cases.
Each interface retains four contact cells, four lateral scalar channels for
two bolts, and two outer-seat ties. The rail and side wrenches on each cleat
balance its external load in both force and moment. Maximum body residuals
are 1.21e-9 N and 1.32e-6 N·mm.

The side-bolt forces are substantially opposed, rather than equal shares of
one resultant:

| Side pair | Angle between signed bolt forces over six cases | Largest lateral couple about pair center | Controlling case |
| --- | ---: | ---: | --- |
| Left | 152.7–175.5° | 20.68 kN·mm | A12-left |
| Right | 153.3–179.9° | 24.44 kN·mm | K12-rear |

In those controlling states, the left pair carries 160.1 and 1,102.2 N;
the right pair carries 210.3 and 1,280.6 N. Replacing either pair with half
its net force would hide the controlling bolt demand and its couple.

The side-pair pitch transverse to its net resultant is 32.36–33.00 mm,
while the along-resultant pitch is 0.06–6.44 mm. This retains the earlier
two-singleton-row geometric interpretation for these side pairs, including
the failure of the staggered-row merger condition. It supplies no additional
group splitting capacity. The rail-pair projections differ and remain
separate; a side-pair factor is not transferred to them.

## Host shear and splitting characteristic references

Whole-host cuts bracket the complete finite transfer footprint. Their
equilibrium includes all other connectors and discrete nodal loads on that
host, rather than only the two target bolts. The cut locations reproduce
the existing saved finished-STEP section locations and dimensions.

The source-corrected characteristic expression is
`F90,Rk = 14 b sqrt(he / (1 - he/h))`, with ordinary bolts `w=1`.
The equation and two-sided shear definition come from
[CEN EN 1995-1-1:2004/AC:2006](https://cms.sia.ch/en/api/getMedia/559),
PDF page 4; the Figure 8.1 mapping is corroborated by the official
[JRC Dietsch workshop slides](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1995_3_Dietsch.pdf),
slides 29–30. Both cached PDFs are hash-checked by the producer. The
[existing source/applicability note](../upper-outer-load-path-2026-10-01/splitting.md)
records their editions and limits.

The rail plane is X–N, with `h=139.7 mm`, `b=38.1 mm`. Each side-host
plane is T–N, with `h=139.7 mm`, `b=88.9 mm`. Both potential loaded
N-edges are carried because the bolt group has a force couple; no favorable
edge is selected from the net force alone.

| Host interface | Largest absolute section shear along N | Case | Characteristic references for the two possible edges |
| --- | ---: | --- | ---: |
| Rail / left cleat | 0.943 kN | A12-rear | 6.921 / 9.399 kN |
| Left side / left cleat | 1.731 kN | A12-rear | 12.736 / 16.992 kN |
| Rail / right cleat | 1.069 kN | K12-rear | 6.921 / 9.399 kN |
| Right side / right cleat | 1.680 kN | K12-rear | 12.736 / 16.992 kN |

These are section demands and characteristic references, without a design
action/resistance conversion or utilization. They support prioritizing the
side-bolt/local-cleat problem in the next correction. They do not qualify
off-plane splitting or the combined two-face cleat. Other contact footprints
crossing a cut are explicitly listed: the calculation balances source point
actions and does not integrate a solid stress field.

## Cleat cuts and bearing screens

The producer now assigns all six force/moment components to both one-sided
traces at each of the five existing exact cuts per cleat: 120 traces total.
The three bore stations retain their two/three separate wood regions. No
common strain or equal regional stress is assigned across those regions.

At the two intact interstation cuts, the saved area is the full
88.9 × 88.9 mm rectangle. Forty-eight trace records add elementary axial,
biaxial bending and transverse shear screens. The torsion term is an
explicit homogeneous isotropic square proxy, `|T|/(0.208 a³)`, from
[MIT 1.050 Solid Mechanics, Problem Set 8 solutions](https://ocw.mit.edu/courses/1-050-solid-mechanics-fall-2004/731b245ebecfef588f5002a94cbf667f_pset04_8soln.pdf),
PDF page 3. It is not an established orthotropic timber torsion field.

| Cleat | Largest intact-cut absolute parallel normal-stress envelope | Largest intact-cut transverse-plus-torsion shear proxy |
| --- | ---: | ---: |
| Left | 0.429 MPa, A12-rear | 0.462 MPa, A12-left |
| Right | 0.485 MPa, K12-rear | 0.536 MPa, K12-right |

For scale, the pinned [dry DF-L No. 2 material scenario](../hardware-material-specification-2026-09-30/materials.md)
has base inputs `Ft=3.964 MPa`,
`Fb=6.205 MPa` and `Fv=1.241 MPa`, before size or other check-specific
adjustments. These intact-cut screens leave bore stress concentrations,
perpendicular-grain tension, short-block disturbance and local crack paths
unresolved. Their small values do not establish a complete cleat pass.

The largest side-interface contact-cell reaction densities are 0.376 MPa
left and 0.418 MPa right. The largest rail-interface densities are 0.139
and 0.137 MPa. These are spring-cell force divided by assigned cell area,
not resolved maximum pressure. The largest corner outer tie is 542.4 N,
right `rail_1` in K12-rear. Local washer metal/contact behavior remains
distinct from this tie and from wood face bearing.

## Decision and next work

The [individual-bolt reference](simple-lateral-reference-summary.json)
still exceeds unity at both top outer `side_2` bolts: 1.19 left and 1.38
right under the unadopted 106 ksi bending-yield hypothesis. Complete action
accounting preserves those demands and shows their physical couple. The
host shear and intact-cleat screens identify no stronger competing concern
within their stated scope.

The subsequent [local checks](top-corner-local-checks.md) now query 32 actual
bore shear-plane areas, apply the six-case parallel component references,
carry rail-pair group/end-factor scenarios and update all sixteen corner
washer wood-pressure references. They preserve the side-bolt concern.
Prepare the smallest local correction with ordinary hardware and installation
access, carrying the remaining splitting and washer-transfer limits. Report
changed stock, bores or axes before changing the reviewed model, then
recalculate affected sharing and the six frame cases.

Precision-export investigations, production washer meshes and recurring
review rounds remain parked. Physical release flags remain false.

## Reproduction and artifacts

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/top_corner_actions.py
```

- [top-corner-actions.json](top-corner-actions.json): source hashes, signed
  receiver actions, whole-body balances, bolt pairs, host cuts and cleat traces.
- [top-corner-case-summary.csv](top-corner-case-summary.csv): 24 same-state
  interface summaries.

The calculation takes about 1.3 seconds, launches no native solver, changes
no geometry and writes only this packet's results. Scoped Ruff passes. No
software test suite or independent agent review was run for this addition.
