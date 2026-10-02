# Coupled normal transfer at the two proposed top outer corners

Status: **local contact/compliance calculation complete; both joints remain
unaccepted**. The isolated 4×6-cleat proposal is separate from the reviewed
scene. The upper-left service joint remains with its existing agent.

## Calculation and results

[Producer](top_corner_contact.py), [finished-face geometry and axial laws](top-corner-contact-geometry.json)
and [six-case results](top-corner-contact-results.json) reproduce the calculation.
The producer reuses the existing physical-action accounting, orthotropic
washer-seat/steel compliance law and static quadratic solver.

Each cleat has two fixed host faces, one rigid-body motion and five restrained
modes. Both faces and all four bolt tensions solve together. Contact is
compression-only; bolts are tension-only; no preload or timber-face friction
is assumed. Each finished contact face has sixteen cells with exact STEP
areas and centroids, including bore voids. The contact penalty is the existing
100 N/mm³ scenario. Proposed grips are 177.8 mm.

The six simultaneous original frame states supply the lateral actions and
original nodal self-weight. The proposed side-axis movements retain their
complete lateral wrench. Translation along N is restrained by those held
lateral actions; its full force balance is checked independently of the five
normal modes. This is a coupled normal-transfer calculation, not a new frame
solution or a complete six-direction joint constitutive law.

| Result across all six cases | Left corner | Right corner |
| --- | ---: | ---: |
| States meeting equilibrium and spring-law tolerances | 6/6 | 6/6 |
| Peak bolt tension | 348.223 N, A12-left, rail 1 | 385.839 N, K12-right, rail 1 |
| Peak affine contact pressure at a face edge | 2.63295 MPa | 2.89535 MPa |
| Pressure / unadjusted DF-L No. 2 Fc⊥ reference, 625 psi | 0.6110 | 0.6719 |
| Peak ideal nominal-annulus washer wood pressure | 1.56346 MPa | 1.73235 MPa |
| Peak modeled bolt extension including both seat springs | 0.09283 mm | 0.10285 mm |
| Peak rigid-cleat rotation magnitude | 0.001774 rad | 0.002007 rad |

Maximum force residual is 3.45×10⁻⁸ N; maximum moment residual is
2.19×10⁻¹¹ N·mm; maximum spring-law residual is 0.001214 N. The declared
calculation tolerances remain 0.1 N and 2 N·mm. All twelve states satisfy
unilateral signs. Ruff passes. No software tests, native solve or independent
review round were run for this calculation.

The quoted edge pressure comes from the affine face motion, extrapolated to
the actual rectangular face edges. It is more informative than quoting only
cell mean pressure. It remains an approximation with rigid hosts and centroid
quadrature, rather than a bound on local timber stress. Nominal washer areas
are 222.726 mm² for the quarter-inch rail bolts and 316.692 mm² for the
5/16-inch side bolts. Actual washer support and metal bending are separate.

## Bolt-property requirement narrowed

The unchanged [fixed-demand proposal](top-corner-correction.md) already records
the six-mode lateral calculation and diameter-specific wood bearing. Holding
those same demands and all other inputs fixed, monotonic bisection of the
existing yield helper gives these minimum Fyb inputs for a lateral ratio of
one before additional end-use/group adjustments:

| Corner | Governing state | Minimum Fyb input | Ratio at an explicit 92 ksi input |
| --- | --- | ---: | ---: |
| Left | A12-left, side 2 | 69.663 ksi | 0.87017 |
| Right | K12-rear, side 2 | 91.746 ksi | 0.99862 |

These are required inputs, not measured or adopted product properties. The
right corner has only about 0.14% arithmetic margin at 92 ksi before the
remaining adjustments and redistribution. The previously calculated 106 ksi
estimate remains unadopted. This calculation therefore does not close the
side-bolt strength requirement.

The pinned 2024 NDS Chapter 12, printed page 95 (§12.3.6.2), permits a
bending-yield basis derived through ASTM F1575 or tensile yield derived
through ASTM F606. The cached chapter SHA-256 is
`53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f`.
[STS Industrial's SAE J429 table](https://www.stsindustrial.com/services-resources/fastener-specifications/sae-j429-technical-data)
lists 92 ksi minimum tensile yield for Grade 5 in the relevant diameter range;
that catalog table alone does not authenticate this proposal's delivered
bolt or its NDS bending-yield input. No property pass is transferred from the
grade name.

## Remaining corner work

1. Recompute the frame with the proposed cleat stiffness, extra self-weight,
   side-bolt diameter/stations and longer rail grips. Original host motion and
   lateral demand are held fixed in this local calculation.
2. Finish side-bolt property/adjustment and simultaneous tension/shear/bending
   resistance, actual threaded bearing, washer/head/nut transfer, and applicable
   splitting/finished-section checks. The motion results are demands, not an
   adopted allowable slip or rotation.
3. Integrate compatible hardware and complete installation/removal checks
   before selecting the proposal. Existing sixteen straight tool approaches
   retain their narrower geometric scope.

The separate [no-Hillman-withdrawal frame calculation](no-withdrawal-frame-checks.md)
now stops in all six cases on upper-panel normal equilibrium. Its representative
A12-rear statics check is infeasible. The original frame demands used here
therefore retain their unsupported parametric screw-withdrawal assumption.
They are conditional demands, rather than accepted panel-joint behavior.
Every source input and proposal STEP
used here is checked against the recorded hashes. Reviewed geometry, old
failures and physical release flags are unchanged. No joint or MVP criterion
is closed by this note.
