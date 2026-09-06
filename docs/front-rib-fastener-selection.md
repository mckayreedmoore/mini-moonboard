# Front rib screw: SDWS16312 product screen

2026-09-06. **One product candidate for further detailing: Simpson Strong-Drive
SDWS16312 Framing screw, Quik Guard, T25 (retail SDWS16312QR50). Not selected
for construction.** The current twelve `rib_*_front` screws remain generic
4.826 × 88.9 mm envelopes. This screen changes no CAD or capacity assumptions.

## Published dimensions and unresolved seating

The [U.S. 2025 catalog, p. 58](https://ssttoolbox.widen.net/content/07il60awb7/pdf/C-F-2025.pdf)
lists these nominal inch dimensions; metric numbers below are exact conversions,
not manufacturing tolerances:

| Quantity | Inches | mm |
| --- | ---: | ---: |
| Length | 3.5 | 88.9 |
| Thread length | 2 | 50.8 |
| Major thread diameter | .215 | 5.461 |
| Unthreaded shank diameter | .160 | 4.064 |
| Head diameter | .450 | 11.43 |

The catalog describes a washer head with underhead nibs that can countersink
flush. It supplies no axial head thickness, underside angle, nib height,
countersink depth, or dimensioned manufacturing head profile. Those dimensions
must not be inferred from the existing generic 10 mm diameter × 3 mm cone.

[IAPMO ER-192, revised February 10, 2026](https://forms.iapmo.org/ues_reports/reports/er_0192.pdf),
Table 1/p. 5, instead lists shank/thread/root/head diameters
.159/.216/.145/.435 in (4.0386/5.4864/3.683/11.049 mm). Length is measured
underhead to point; thread length includes the point. Figure 6 is a publisher
screw illustration, not a dimensioned head profile. Section 4.2 permits
installation without pilot holes using a low-speed drill and specifies the
head underside flush to the member. Section 5.1 makes the stricter requirement
govern conflicts. Resolve the catalog/report seating difference with Simpson
before recessing the head beneath the climbing panel. No exact publisher
CAD/head drawing was located in this bounded search.

For preliminary interference work use at least the larger published thread/head
envelopes, 5.4864/11.43 mm, pending tolerances. The existing 5.2 mm batten hole
does not freely pass that thread; a screw may cut wood during driving, but this
is not the model's assumed clearance hole. Its 3.2 mm rib pilot is likewise
not a verified product instruction. The
[SDWS16 regional installation sheet](https://strongtie.com.au/sites/default/files/technical_data/T-F-SDWS16-AU23_11.12.23_0.pdf)
notes that predrilling/countersinking may be necessary near ends, butt joints
or in denser timber, without specifying a pilot diameter. Obtain the instruction
for the purchased U.S. product and chosen species; do not borrow SDWS22 drills
or assume generic wood-screw countersink angles.

## Geometry and spacing basis

The [2025 technical guide, pp. 46–47](https://ssttoolbox.widen.net/content/zpm9nibpvz/pdf/C-F-2025TECHSUP.pdf)
requires its spacing screen in **both** members. For SDWS16312:

| Load relative to each member's grain | End | Edge | In-row spacing | Between rows | Stagger |
| --- | ---: | ---: | ---: | ---: | ---: |
| Lateral parallel | 76.2 (3 in) | 25.4 (1 in) | 50.8 (2 in) | 25.4 (1 in)* | 11.1125 (7/16 in) |
| Lateral perpendicular | 101.6 (4 in) | 25.4 (1 in) | 50.8 (2 in) | 25.4 (1 in)* | 11.1125 (7/16 in) |
| Axial only | 57.15 (2.25 in) | 22.225 (.875 in) | 41.275 (parallel grain) | 22.225 (perpendicular grain) | — |

*The indicated row arrangement carries a 0.91 shear-load factor. Read the
publisher's diagram when assigning rows/stagger; these are not interchangeable
radial-distance limits. The guide's 38.1 mm side-member/50.8 mm penetration
case matches the nominal thicknesses here. Its withdrawal maximum incorporates
head pull-through of a 38.1 mm side member and requires all threads in the main
member. Removing wood for a recess is not automatically that tested detail.

ER-192 §5.4 directs combined lateral/withdrawal design to NDS §12.4.1;
§4.1.3 limits axial-only spacing to connections without lateral loading.
Do not use the axial-only minima for this joint's unknown mixed demand.
The same report requires checks against splitting and local member stresses.
No capacity is assigned here.

## All twelve current positions

Measured from `joint_frame.connections()` and undrilled CAD member vertices,
projected into board coordinates X/S. S follows rib grain; row-1/3 battens also
have S grain, while the row-2 horizontal batten has X grain. Thus row-2 batten
end/edge distances exchange X/S roles. All numbers are millimetres.
Relief distance is screw axis to the nearest modelled 40 mm relief boundary;
it is a project screen, not a manufacturer-approved notch rule.

| Rib | X | S | Batten end / edge | Rib end / outside edge | Relief | Nearest parallel screw axis in same batten |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 seam left | -54 | 430 | 341.1 / 28.55 | 120 / 31.75 | 40.9183 | 8.0044, panel_11 |
| 1 seam right | 54 | 400 | 311.1 / 28.55 | 150 / 31.75 | 55.8831 | 23.4109, panel_21 |
| 1 mid left | -519.2 | 400 | 311.1 / 44.45 | 150 / 31.75 | 81.9804 | 150, panel_49 |
| 1 mid right | 680.8 | 400 | 311.1 / 44.45 | 150 / 31.75 | 81.9804 | 150, panel_53 |
| 2 seam left | -54 | 1219.2 | 1165.2 / 69.85 | 150 / 31.75 | 32.4183 | 50.1597, panel_28 |
| 2 seam right | 54 | 1219.2 | 1165.2 / 69.85 | 150 / 31.75 | 63.0354 | 50.1597, panel_37 |
| 2 mid left | -519.2 | 1219.2 | 700 / 69.85 | 150 / 31.75 | 87.4088 | 89.4190, panel_27 |
| 2 mid right | 680.8 | 1219.2 | 538.4 / 69.85 | 150 / 31.75 | 87.4088 | 135.8680, panel_39 |
| 3 seam left | -54 | 2030 | 319.5 / 28.55 | 120 / 31.75 | 40.9183 | 15.2023, panel_36 |
| 3 seam right | 54 | 2000 | 349.5 / 28.55 | 150 / 31.75 | 55.8831 | 15.8465, panel_46 |
| 3 mid left | -519.2 | 2000 | 349.5 / 44.45 | 150 / 31.75 | 81.9804 | 69.2, panel_59 |
| 3 mid right | 680.8 | 2000 | 349.5 / 44.45 | 150 / 31.75 | 81.9804 | 69.2, panel_63 |

The rectangular outside end/edge dimensions clear the stronger lateral screen.
**The full layout is not spacing-qualified.** For example, `panel_11` is at
X/S = -50/423.0667 versus -54/430 for the rib screw: offsets are only
4/6.9333 mm. Both shafts occupy batten depths N = 0–32.8 mm. The existing
panel screw is a different, still generic product; no published mixed-fastener
spacing exception was established. Row-3 seam locations and other neighbouring
fasteners also require joint group/splitting checks, not a claim that non-overlap
establishes spacing compliance.

At the three left seam ribs, the chase is only 27.3 mm from the screw axis and
removes front bearing wood through N = 56 mm. The nearest crossed rear bolt
bore has a nominal 27.2568 mm remaining ligament when screened with a 5 mm bore
radius and the larger 5.4864 mm screw diameter; this is merely geometry.
Neither the chase nor relief is an intact exterior edge, and neither obtains
a resistance allowance from passing a 25.4 mm distance check.

For an **underhead-flush, unrecessed** position at N = 0, all twelve candidate
5.4864 mm cylindrical thread envelopes from N = 38.1 to 88.9 lie within their
actual undrilled rib shapes: CadQuery intersection volume divided by cylinder
area yields 50.8 mm at each station. Rib rear N = 128.05 leaves 39.15 mm past
the nominal point. This confirms an available wood envelope, not full-profile
thread engagement or installed head fit. The underhead-flush head would project
toward the overlying panel; recessing it changes that placement and the side
member's net section.

## Decision still needed

Keep SDWS16312 as the single candidate. Before replacing the generic model,
resolve publisher dimensions/head seating and the nearby panel fasteners;
select actual solid-lumber species, grade and moisture; establish installation
holes and tolerances; assess the notched/relieved net sections, both members'
combined loads, and head pull-through. Product resistance and the candidate's
structural validation remain unestablished.
