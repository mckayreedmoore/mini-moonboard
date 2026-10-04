# Local plywood and perforated-section numerical completion

## Result and disposition

**The local/net numerical comparisons are completed for the stated geometry, material and local resistance hypotheses.** The frozen [attempt05 result](rawlocal/panel-local-net-completion/attempt05/summary.json), status `COMPLETED_CONDITIONAL_LOCAL_NET_NUMERICAL_COMPARISON`, covers original reviewed104 live actions and the preserved proposal live/permanent actions. The separately completed [original104 permanent result](rawlocal/panel-local-net-completion/original104-permanent-attempt01/summary.json) adds the saved original-mass nominal gravity state; its status is `COMPLETED_CONDITIONAL_ORIGINAL104_PERMANENT_LOCAL_NET_NUMERICAL_COMPARISON`. Existing reference exceedances remain recorded; repairs remain deferred.

The calculation retains 104 structural axes and all 66 Hillman axes. It numerically removes the four obsolete STEP screw cavities and substitutes cavities at their current moved stations. Source STEP bytes, global response, connector stiffness, hardware and load sharing remain frozen. It integrates remaining plywood through actual circular openings and the declared countersink profiles, then computes elastic net-section strain, bending and transverse shear. Local head contact, punching and directional ligament models use the simultaneous saved screw actions. These finite local calculations supplement [N14](panel-reference-completion.md) and [permanent applicability](panel-permanent-applicability.md).

The principal original104 live results at CD1.0 are local punching **14.899856514012553**, directional ligament shear **2.671851446866125**, and net rolling shear **1.5589697441508572**. Original104 permanent local punching is **1.160825031647565** at CD0.9; proposal permanent local punching remains **1.160697196047701**. Each is a demand/reference ratio under the hypotheses below; values above 1.0 are retained exceedances. Numerical completion does not change panel, joint, N14 or fabrication acceptance flags. Independently, the existing favorable Hillman head references of **930.222–984.128 N** remain below the roughly **1,871 N** live head demand; the new local plywood scenarios do not replace that comparison or supply a Hillman product capacity.

## Four distinct action sets

| Action set | Frozen source and scope | Modeled mass / gravity multiplier | Numerical coverage |
| --- | --- | --- | --- |
| Original reviewed104 live | `frame-250-attempt02/response.npz`, nominal `*_gap_raw_force_n`, recovered with `operators-attempt02` | 224.9499553141194 kg / 1.1111358300342407 | 396 screw states, 36 panel balances, 2,256 recovered gross source cuts; 5,880 net-section duration records |
| Original reviewed104 gravity only | `rawlocal/dead-load-check/parent-attempt06/response.npz`, nominal `dead-only_gap_raw_force_n`, recovered with `operators-attempt02` | 224.9499553141194 kg / 1.1111358300342407 | 66 screw states, six panel balances, 376 recovered gross source cuts; 490 net-section records at CD0.9 |
| Proposal live | Existing `rawlocal/panel-reference-completion/attempt01` screw/cut outputs | 225.19791414318078 kg / 1.1110134616260479 | 396 screw states; 5,880 net-section duration records |
| Proposal gravity only | Existing `rawlocal/panel-permanent-completion/attempt01`, `permanent-only_gap`, gap scale 1.0 | 225.19791414318078 kg / 1.1110134616260479 | 66 screw states; 490 net-section records at CD0.9 |

The proposal source uses unchanged 104-axis stiffness/connector rows with the unadopted 108-axis knee-bridge proposal's planning mass/actions. Its net mass increment is 0.24795882906138145 kg. It is not relabeled as original104 physics. Both gravity multipliers include proportional 25 kg equipment once. Original live contains original104 gravity plus the individual live case. The separate original104 permanent calculation consumes the existing original-mass gravity-only response directly. Proposal gravity retains its separate label and is not scaled into the original104 state.

All six Mini2025 cases are alternatives: `a12-rear`, `a12-forward`, `a12-left`, `k12-right`, `k12-rear`, `a1-rear`. Each has 250 lb × 2 = 2,224.11080763025 N downward, one signed 300 N horizontal force and the existing 100 mm hold offset. Support remains the recorded no-slip assumption. Live resistance is reported at CD1.0 and CD1.25; permanent resistance uses CD0.9. The dynamic factor acts on demand once; no extra impact resistance multiplier is introduced. Face-bearing comparisons have no CD multiplier.

The original adapter reads saved arrays; it solves no new system. It reuses N14's definition loader, `comparison_row` and `panel_sections`, the existing physical DOF parser, and `top_corner_actions.wrench`. With saved CSR `B`, it recovers connector physical forces as `-B.T @ raw_force`; prescribed live panel actions use `F_gravity * dead_factor + F_live`. Permanent panel actions use only `F[:,0] * dead_factor` and generalized equilibrium uses only `W[:,0] * dead_factor`. Saved `D` supplies force directions and component ownership. All 36 live and six permanent panel force/moment balances satisfy the inherited 1e-5 N / 0.01 Nmm limits. The permanent maximum body force residual is **3.538502824085299e-12 N**, body moment residual **2.6590817331572904e-9 Nmm**, and point-datum screw moment join error **9.395080269314349e-9 Nmm**. No withdrawal stiffness was adjusted.

The original104 nominal permanent source retains four bounded seating freedoms, `fixed_force_unique=false` and no strict active-tangent stability acceptance. These local calculations use its saved force tuple; they supply no force envelope over alternative seating states. The separately saved zero-gap state remains a sensitivity and is not substituted into the nominal comparison.

## Current cavity substitution and remaining plywood

Six pinned source panel STEPs contain elementary planes, cylinders and cones. The producer reads their STEP entities as text and joins duplicate surfaces by axis; it runs no CAD kernel. Rectangular bounds, thickness and orthotropic directions come from the frozen physical nodes/material binding. All main panels are 1,217.6125 × 1,219.2 mm; whole kickers are 1,217.6125 × 277 mm. Thickness is 18.25625 mm. Main-panel direction 1 is global X; direction 2 is `(0, -0.6427876096867989, -0.7660444431187603)`. Kicker direction 2 is global −Z. The original frozen material directions are retained.

| Panel | Screw cavities | Hold/T-nut openings, Ø11.1125 mm | LED openings, Ø13 mm |
| --- | ---: | ---: | ---: |
| main_lower_left | 12 | 36 | 42 |
| main_lower_right | 12 | 30 | 35 |
| main_upper_left | 12 | 36 | 30 |
| main_upper_right | 12 | 30 | 25 |
| kicker_left | 9 | 5 | 0 |
| kicker_right | 9 | 5 | 0 |
| Total | **66** | **142** | **132** |

The four substitutions below are **moves**, not four extra physical holes. Coordinates are dot products of global position with the two recorded panel directions, in mm. All move 65.950000000073 mm in negative direction 2. The remaining 62 screw cavities coincide with current force stations.

| Axis suffix after `round_panel_upper_` | Panel | Original local (1,2) | Current local (1,2) | Frozen bore Ø |
| --- | --- | --- | --- | ---: |
| left_center_4 | main_upper_left | (−70, −2554.0241337694615) | (−70, −2619.9741337695345) | 2.921 |
| left_rim_4 | main_upper_left | (−1200.15, −2554.0241337694615) | (−1200.15, −2619.9741337695345) | 2.921 |
| right_center_4 | main_upper_right | (70, −2554.0241337694615) | (70, −2619.974133769535) | 7 |
| right_rim_4 | main_upper_right | (1196.975, −2554.0241337694615) | (1196.975, −2619.974133769535) | 7 |

The frozen cone diameter is 8.128 mm with 90° included angle. The **current local-model hypothesis** is a flush 9.017 mm nominal Hillman head, generic #10 Ø4.826 mm bore and 82° included cone. Where the frozen bore is Ø7 mm, that larger bore is retained. The envelope is the union of the frozen cone and the declared current cone at each current station. These are analysis dimensions, not bit sizes, drill instructions or measured delivered screw dimensions. No historical extra-hole sensitivity is adopted and no monotone stress-bound claim is made.

| Bore hypothesis | Countersink depth envelope | Remaining local thickness | Projected head annulus |
| --- | ---: | ---: | ---: |
| Ø4.826 mm | 2.4105969973316252 mm | 15.845653002668376 mm | 45.56567005784248 mm² |
| Ø7 mm | 1.1601465386823877 mm | 17.096103461317615 mm | 25.37330004678718 mm² |

The minimum head-edge ligament is approximately 14.5414999954 mm; minimum head-to-other-void ligament is approximately 28.0215008000 mm. [geometry.json](rawlocal/panel-local-net-completion/attempt05/geometry.json) records every opening, source STEP surface ID, frozen/current dimensions, bounds, axes and the explicit substitution map. For each cut and thickness coordinate, circular chord intervals are clipped to the actual panel bounds and their **union** is removed. Overlap is not double-counted.

## Primary references and material hypothesis

The material hypothesis is dry Group 1 A-C 23/32 plywood at ordinary temperature, with the source material axes and equivalent three-layer fit. It is not an observation of sheet grade or veneer construction. Values come from [APA Panel Design Specification, D510C (2012)](https://design.medeek.com/resources/structural/D510C_2012.pdf), Table 9 and §§4.4–4.6. These tables distinguish bending, axial, rolling/interlaminar shear, membrane shear and face bearing. Section 4.6 permits corresponding equivalent stresses using section properties. The 360 psi face-bearing reference corresponds to 0.04 in deformation; 210 psi corresponds to 0.02 in. These are deformation references, not delivered Hillman head ratings.

| Reference property | Parallel to strength axis | Perpendicular |
| --- | ---: | ---: |
| EA, lbf/ft | 5,100,000 | 3,150,000 |
| EI, lbf in²/ft | 320,000 | 90,500 |
| FtA, lbf/ft | 5,100 | 3,400 |
| FcA, lbf/ft | 4,800 | 2,900 |
| FbS, lbf in/ft | 775 | 455 |
| Fs(Ib/Q), lbf/ft | 350 | 350 |
| Fvtv, lbf/in | 105 | 105 |

The model uses `Fs(Ib/Q) = 5.107866028022227 N/mm` at CD1.0 and face bearing `Fc⊥ = 2.48211262554061 MPa`. Existing `size_factor` is reused: Cs = 1 at widths ≥24 in, 0.5 at widths ≤8 in, and `0.25 + 0.0313 * width_in` between. It applies to tension and bending. Membrane shear assumes that existing panel/receiver restraint prevents the unsupported deep-web buckling limitation described in APA §4.4.5; the component comparison does not establish a new global buckling result.

The unchanged `equivalent_layers` helper fits both directional EA and EI with outer/core/outer thicknesses 4.5640625 / 9.128125 / 4.5640625 mm. Directional moduli are:

| Layer | E1, MPa | E2, MPa |
| --- | ---: | ---: |
| Each outer layer | 1401.2815489919956 | 6563.75000870337 |
| Core | 3634.8889955831546 | 1590.049920608777 |

The source assumes zero Poisson coupling. Gross targets are EA `(45970.794252200045, 74428.90497975245) N/mm`, EI `(852093.9189166091, 3012928.774069778) Nmm` and membrane GA `8843.905179947058 N/mm`. The complete unchanged constants are in the frozen summary. A real veneer failure distribution is not invented from these equivalent constants.

The separate circular-hole membrane sensitivity uses [NASA CR-179435 (1988)](https://ntrs.nasa.gov/api/citations/19880017310/downloads/19880017310.pdf), printed pp. 2–3, equations 1–6. Its orthotropic infinite thin-plate hole solution is used only for an isolated, unloaded circular hole under principal membrane loading. It is not applied to bending, rolling shear, loaded hole contact, neighboring-hole interaction or edge effects.

## Implemented resistance calculations

### Elastic net section

For each cut station, let `w(z)` be the actual remaining width after the union of all hole/countersink chords. The producer integrates:

```text
A = integral w(z) dz
EA = integral E_axis(z) w(z) dz
EB = integral E_axis(z) w(z) z dz
EI = integral E_axis(z) w(z) z² dz

[EA EB; EB EI] [epsilon0; kappa] = [N; M]
epsilon(z) = epsilon0 + kappa*z
D_net = EI - EB²/EA
z_E = EB/EA
Q_E(z) = integral from back face to z of E_axis(u)*w(u)*(u-z_E) du
tau(z) = V_normal*Q_E(z) / (D_net*w(z))
```

This closed 2×2 section calculation introduces no frame solve. Axial tension/compression strain limits are calibrated to `FtA/EA_gross` and `FcA/EA_gross`; bending strain is calibrated to `FbS*(t/2)/EI_gross`. Each uses its applicable Cs and CD. The shear reference is calibrated using APA's rolling-shear line capacity and the **same equivalent-layer gross shear coefficient**. Thus `net_planar_shear_ratio` compares the actual net-section peak elastic shear, including thickness-dependent countersink loss, with the corresponding equivalent-material reference. It is not a whole-panel mean comparison. Membrane shear uses net area. The separately labeled axial-plus-bending sum is an explicit linear allocation hypothesis, not an asserted codified interaction equation.

There are 490 distinct geometric sections per action set: all inherited before/after action cuts plus the actual hole-center cuts inside load-free intervals. Saved signed wrench transport supplies each additional cut; neither interpolation of independent maxima nor action redistribution is used. These are the declared section stations, not a claim of a continuous three-dimensional peak-stress search. Uniform section strain and the width-averaged shear solution do not resolve crack-tip, conical-seat or between-ligament stress concentrations.

The isolated membrane sensitivity is `Kt = 1 + sqrt(2*sqrt(E1/E2) - 2*nu12 + E1/G12)`, with the source zero Poisson coupling and directional equivalent membrane moduli. Its largest original104 ratio is 0.11798554188466322 at CD1.0. It is retained as a sensitivity within the NASA applicability above, not multiplied into the bending/shear resistance.

### Local screw head and ligaments

Each local record retains the **same-state** tension and signed lateral force. The declared head-contact model is uniform pressure over the projected cone annulus `π(R_head²−R_bore²)`; pressure is compared with the 360 psi face-bearing reference. Pressure is not spread beyond the nominal head.

The simplest local punching model unrolls the head perimeter into a strip, assigns uniform tension per circumference and parabolic shear through the remaining thickness:

```text
punching peak shear = 1.5*T / (2*pi*R_head*t_remaining)
rolling reference stress = 1.5*Fs(Ib/Q)*CD / t_gross
```

This is an explicit elastic strip/resistance hypothesis calibrated to the primary-source rolling-shear reference. It is not an APA punching table or a tested screw pull-through capacity.

The lateral component uses two directional shear paths from a square circumscribing the head, parallel to the **saved signed in-plane force**. Each ray ends at the actual panel edge or first intervening circular void. Its capacity hypothesis is `sum(path_lengths)*t_remaining/t_gross*Fvtv*CD`. Every endpoint is recorded. A separate shortest two-ligament allocation sensitivity is retained; it assigns the entire lateral force to twice the shortest edge/void ligament. The summed punching-plus-directional ratio is a declared shared shear budget. A path ending at an opening does not itself establish a complete block-shear fracture mechanism. Neither hypothesis supplies an invented Hillman steel strength, delivered screw profile or timber withdrawal qualification.

### Loaded hold/T-nut opening

The existing `hold_demand` equilibrium helper supplies T-nut tension for each recorded six-case force, the 100 mm offset and assumed front-contact arms 25/50/100 mm. The declared flange is Ø25.4 mm; the plywood opening is Ø11.1125 mm. Three Ø3.2 mm retention holes belong to the **metal flange**, not three invented through-holes in the plywood. The added local strip calculation uses `T_hold/(pi*25.4*Fs(Ib/Q)*CD)` through full local plywood thickness. No T-nut countersink is invented.

At a 50 mm front-contact arm, `a12-forward` requires 4,993.025552722737 N T-nut tension; local punching ratios are **12.250130112588375 / 9.800104090070699** at CD1.0 / 1.25. Its existing uniform flange-bearing ratio is approximately 5.21690689424. The 25 mm arm produces the largest local punching ratios **21.556569915220205 / 17.245255932176164**. The actual hold contact arm/footprint is a missing physical input. These explicit alternatives preserve the existing local bearing exceedances. The live hold action is identical across the original/proposal comparisons; it is not a second global load. Permanent-only has no climber/loaded-hold force, while all hold/T-nut openings remain in its net section and their existing gravity remains in the saved actions.

## Frozen numerical envelopes

All values below are maxima over the stated simultaneous records. CD columns report resistance adjustments, not extra live load cases. Counts are finite record comparisons; duplicate before/after or added section stations are not counted as distinct physical failures.

### Original reviewed104 live

| Component | CD1.0 maximum | CD1.25 maximum | Records >1 at CD1.0 / 1.25 |
| --- | ---: | ---: | ---: |
| Local projected head bearing | 25.459793499855582 | 25.459793499855582 | 154 / 154 of 396 |
| Local punching strip | 14.899856514012553 | 11.919885211210042 | 71 / 56 of 396 |
| Directional two-ligament shear | 2.671851446866125 | 2.1374811574929 | 5 / 5 of 396 |
| Punching + directional allocation | 14.922512843044451 | 11.93801027443556 | 81 / 59 of 396 |
| Net axial | 0.02737044492609445 | 0.021896355940875557 | 0 / 0 of 2,940 |
| Net bending | 0.6798361148801696 | 0.5438688919041357 | 0 / 0 of 2,940 |
| Net axial + bending allocation | 0.6937003540325835 | 0.5549602832260667 | 0 / 0 of 2,940 |
| Net rolling/transverse shear | **1.5589697441508572** | **1.247175795320686** | **30 / 11 of 2,940** |
| Net membrane shear | 0.11873104445474307 | 0.09498483556379445 | 0 / 0 of 2,940 |

Original104 local punching witness: `round_panel_upper_left_edge_2`, `a12-rear`, simultaneous tension **1,871.2512062195326 N** and lateral force **726.6105292217607 N**. With Ø4.826 mm bore and 15.845653002668376 mm remaining thickness, calculated punching shear is **6.253184874522183 MPa**, reference **0.4196808787145958 MPa** at CD1.0. The projected-head bearing maximum is at `round_panel_upper_right_edge_2`, `k12-rear`: 1,603.4422233541854 N tension, 25.37330004678718 mm² annulus and 63.19407488964829 MPa uniform pressure.

Original104 net rolling-shear witness: `main_upper_left`, `a12-forward`, axis 1, after source station, absolute local coordinate **−2519.824123868214 mm**. Normal shear is **−9,164.9252046506 N**. The local cut intersects the six Ø11.1125 mm hold openings: gross width **1,217.6125 mm**, remaining width **1,150.9375000001055 mm**, net area **21,011.802734376928 mm²**, EA **85,663,017.82514167 N**, EI **3,467,692,710.906256 Nmm²**. Peak transformed-section shear is **0.5858138600387346 MPa** at `z=0`, versus **0.3757698712477687 MPa** at CD1.0 and **0.4697123390597109 MPa** at CD1.25. This is the numerical net-wood loss missed by the gross-width comparison.

### Original reviewed104 permanent

The completed separate nominal original-mass state uses CD0.9 once for strength; deformation-limited head face bearing receives no duration increase.

| Component | CD0.9 maximum | Records >1 |
| --- | ---: | ---: |
| Local projected head bearing | **2.10352287715372** | 15 of 66 |
| Local punching strip | **1.160825031647565** | 4 of 66 |
| Directional two-ligament shear | 0.39171881324958546 | 0 of 66 |
| Shortest two-ligament sensitivity | 0.398572460188942 | 0 of 66 |
| Punching + directional allocation | **1.5525438448971505** | 4 of 66 |
| Net axial | 0.00390822732051415 | 0 of 490 |
| Net bending | 0.10394825103687465 | 0 of 490 |
| Net axial + bending allocation | 0.10637992629648607 | 0 of 490 |
| Net rolling/transverse shear | 0.03844558782210303 | 0 of 490 |
| Net membrane shear | 0.020709058353624268 | 0 of 490 |
| Isolated-hole membrane sensitivity | 0.016847161946559733 | 0 of 490 |

Original104 permanent punching and additive-allocation witness: `round_panel_upper_left_rim_4`, simultaneous tension **131.20768745482516 N** and lateral force **166.5058764491114 N**. Original104 projected-bearing witness: `round_panel_upper_right_service_1`, simultaneous tension **132.478584283839 N** and lateral **23.699859200644838 N**. These are the independently recovered original-mass permanent actions. They preserve local reference exceedances despite all declared net-section component ratios remaining below one.

### Preserved proposal live and proposal-gravity permanent

| Component | Proposal live CD1.0 | Proposal live CD1.25 | Proposal permanent CD0.9 | Permanent records >1 |
| --- | ---: | ---: | ---: | ---: |
| Local projected head bearing | 25.460715486538334 | 25.460715486538334 | **2.1033110072112096** | 15 of 66 |
| Local punching strip | 14.899817084285372 | 11.919853667428297 | **1.160697196047701** | 4 of 66 |
| Directional two-ligament shear | 2.6714975844368363 | 2.1371980675494693 | 0.39163865572065065 | 0 of 66 |
| Punching + directional allocation | 14.9224773285302 | 11.93798186282416 | **1.5523358517683516** | 4 of 66 |
| Net axial | 0.02737040630298923 | 0.021896325042391383 | 0.003907804946249011 | 0 of 490 |
| Net bending | 0.6798336160580496 | 0.5438668928464396 | 0.10393914944064539 | 0 of 490 |
| Net axial + bending allocation | 0.6936969327075827 | 0.5549575461660662 | 0.10637077111253672 | 0 of 490 |
| Net rolling/transverse shear | **1.5589701068070554** | **1.2471760854456444** | 0.038441340425560556 | 0 of 490 |
| Net membrane shear | 0.11873149734470509 | 0.09498519787576407 | 0.020708771310086034 | 0 of 490 |

Proposal live exceeded counts equal the original104 counts in the preceding table. The separate shortest-path lateral sensitivity is **2.6803108613023974 / 2.144248689041918** live (10 of 396 records exceed at each duration), and **0.3984898180596286** permanent. It is not used to claim a physical monotone bound.

Proposal permanent local punching witness: `round_panel_upper_left_rim_4`, simultaneous tension **131.19323823726415 N** and lateral **166.47135223696083 N**, after the current cavity substitution. Proposal permanent projected-bearing witness: `round_panel_upper_right_service_1`, simultaneous tension **132.46524084443982 N** and lateral **23.698355888597337 N**. These are actual saved permanent actions, not reduced live peaks. The reported permanent net bending uses Group 1; the older **0.15513305886663492** gross result is the preserved Group 4 sensitivity, not a contradictory Group 1 value.

## Known-answer numerical method observations

[method-validation.json](rawlocal/panel-local-net-completion/attempt05/method-validation.json) records small analytical examples evaluated during calculation. These are numerical method validation, not added software tests or a review loop.

| Method example | Exact answer | Observed result |
| --- | --- | --- |
| 100 mm rectangular strip, central Ø20 mm through-hole at center cut, t=18.25625 mm | A=1,460.5 mm²; EA=3,677,663.5401760037 N; EI=68,167,513.51332873 Nmm² | Maximum relative error 2.220446049250313e-16 |
| Same symmetric net section, N=800 N, M=1,600 Nmm | epsilon=N/EA; kappa=M/EI | epsilon=0.00021752941541838648; kappa=2.3471591048823477e-5/mm |
| Homogeneous perforated strip shear | tau_peak/V=1.5/A | 0.0010270455323519343 MPa/N, equal to exact result; peak z=0 |
| NASA isotropic circular hole, E=7,000 MPa, nu=0.3, G=E/[2(1+nu)] | Kt=3 | 3.0 |

Composite Simpson integration uses 32 subdivisions per equivalent layer, then 64 at each opening-intersecting cut. All 160 such geometric cuts are retained at the finer value. Largest relative change among A, EA, EI and peak elastic shear coefficient is **5.095782427799733e-6**, at `main_lower_right`, axis 0, station 66.05764899543055 mm. The same geometry observations apply to all four action sets. They establish calculation accuracy within the section model; they do not validate unmeasured material or three-dimensional contact physics.

## Reproduction and supplementary parent API

Executed lightweight command from repository root, Python **3.12.3**, existing NumPy **2.5.2**:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/panel-local-net-completion.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/panel-local-net-completion/attempt05
```

The separate original104 permanent invocation, also using existing Python 3.12.3 and NumPy 2.5.2, was:

```sh
PYTHONDONTWRITEBYTECODE=1 uv run --no-sync python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/panel-local-net-completion.py --original104-permanent --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/panel-local-net-completion/original104-permanent-attempt01
```

`build_original_permanent(output)` authenticates the original permanent comparison/response, reuses pinned attempt05 geometry and numerical method evidence, checks the unchanged 66 force/cavity stations and material axes, then recovers only the saved nominal permanent actions. It emits 66 screw actions/local rows, six balances, 376 signed gross source cuts and 490 local net cuts. It never executes the dead-load producer or its clearance solve. Its receipt authenticates 43 sources and nine output files. Attempt05 retains its original executed snapshot; its old `original104_permanent_actions` missing-input entry is historical and is superseded by this separate numerical result.

Targeted Ruff and syntax compilation pass on the maintained producer. After the permanent run, `re.S` was expanded to the identical `re.DOTALL` constant and the authenticated AST loader received a comment-only S102 annotation. Historical producer pins resolve through each packet's executed `producer.py.snapshot`. The maintained source SHA is `7096fe079b43267f4ead3954d69c1a390ece7b044e877533cc6cfaefee86a249`; the permanent executed snapshot SHA is `8034adfee0f052aebf3f51aecfaf07a82e9cdcee5264e3de0c5f79b84b6f93cd`. Complete source syntax trees match after normalizing the regex alias. No numerical rerun followed those style edits. Rechecking both packet receipts against their executed snapshots authenticated all 38/43 sources and 14/9 output files, respectively.

`build(output)` requires a **fresh** immediate child of `rawlocal/panel-local-net-completion/`; an existing frozen output is never overwritten. Reproduction uses the same command with a new owned child. Source hashes are authenticated before and after execution. Dependencies are reused in place, pure function definitions loaded by the existing helper; no helper installations are copied. No native/CAD/global solve, tests, review, staging or commit ran.

For a parent-supplied supplementary current compatible action set, the reusable numerical API is:

- `local_screw(screw, geometry_panel, CD)` requires `case_id`, `axis_id`, `panel`, simultaneous `tension_n`, `lateral_n` and `signed_force_on_panel_n`. Axis/point ownership must match the unchanged 66-station geometry. The signed force supplies the actual directional ligament paths.
- `net_rows(cuts, geometry, model, layers, panel_helper, CDs)` requires N14-compatible cuts: `case_id`, `panel`, `cut_axis`, `datum_mm`, signed `signed_cut_force_xyz_n`, signed `signed_cut_moment_xyz_nmm`, `family`, `side`, and `station_from_panel_datum_mm`. The cut source must include all physical load stations before hole-center wrench transport is applicable. Global compatibility/contact effects must already be included in those signed actions.
- `geometry(...)` and the retained equivalent layers may be reused unchanged. A new compatible source must carry its own exact receipt/model/action hashes and explicit original104 or proposal scope. Append a supplementary packet; retain both completed local/net packets and the proposal comparisons. Parent owns any changed coupling source.

The original104-only gravity response and its signed 66-screw actions and balanced six-panel cuts are now available and numerically compared. Exact **physical inputs** not observed are installed bore/head/countersink profile, sheet grade/grain/layup/defects, conical-seat pressure/perimeter distribution, and each hold's front-contact footprint/arm. Conical-seat radial thrust, loaded-hole/neighbor/edge stress fields, local veneer failure and combined plate buckling are outside the strip/plane-section hypotheses. The packet supplies finite numerical results under the declared hypotheses. A complete fracture/contact solution would need those distributions and actual veneer behavior; the isolated-hole sensitivity supplies no finite edge/loaded-hole capacity. Local net stiffness is used only in resistance postprocessing; it does not redistribute the frozen global forces.

## Exact frozen pins

All SHA-256 values are full byte hashes. [sources.json](rawlocal/panel-local-net-completion/attempt05/sources.json) and [receipt.json](rawlocal/panel-local-net-completion/attempt05/receipt.json) contain the complete consumed source/output map; the pinned upstream receipts retain their historical dependency maps.

| Source | SHA-256 |
| --- | --- |
| Original104 `frame-250-attempt02/response.npz` | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| Original104 `frame-250-attempt02/comparison.json` | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| Original104 `operators-attempt02/operators.npz` | `c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3` |
| Original104 `operators-attempt02/model.json` | `b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626` |
| Original104 `operators-attempt02/model-inputs.json` | `e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc` |
| Original104 `operators-attempt02/B.npz` | `d109f7db25cb05619e26560e501e7e82f3608fdbb3580f76e64f9beae916128a` |
| Proposal live N14 receipt | `5b42272f49c1924546abab3bd4d036a0a95f7afb2700055fb2e769ab56a3db91` |
| Proposal permanent receipt | `7aa5d81d425ce46006943cb37cc44f78fea569b5c0cff454cd8eeb8dc75ea69d` |
| Reused `panel-reference-completion.py` | `1943198db40ed6729f6c93c3a1196e1642d3a3843fb2bbf5e826aa6b35a116b1` |
| Reused `panel-permanent-applicability.md` | `e019b8ae2e635dd903c3bb3a4a7db7a0942250083f7183bd0291ddf8f2a93492` |
| Reused `fea/current_response_materials.py` | `72af0456272d91282928014d8fde557d347e36df6b7bdf23bcc41ef923d0d135` |
| Reused `fea/reinforced_panel_checks.py` | `1cf47584c36ab5c513ee74072f66782b0aa3907cca6b0ee940218d84693d634d` |
| Hillman nominal dimensions JSON | `d6c3c3ce8d27a02a98a4d9cdca7dce66d2cc5c982cb73b6fb3731ce80d70e72c` |
| APA D510C (2012), cached primary PDF | `6141e0fe02ad0db8ddec20becf2ec25c85accd21c9796e51411d19448e5762ca` |
| NASA CR-179435 (1988), cached primary PDF | `b7fa67627be473b748953795a546711a484c51fe5da9d0f66bc27255a027f811` |

Panel STEP bindings use `evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/`:

| Unchanged STEP | SHA-256 |
| --- | --- |
| kicker_left.step | `4740a18f46b8e8ecc2c01c80f7966228c498e35a09f10d7ccb32b08ea3cd8691` |
| kicker_right.step | `d70c1fedf1c18304818a0f3adefdef0f64204f055a18d941ecd2b91a8dfe32b5` |
| main_lower_left.step | `78e2bd7b3a3f4cb6f70a1a2156ae3143cb936b29e5560dd6fd0cf6142aac6270` |
| main_lower_right.step | `408d8ed97edf27954fa63221096af25da56a5aab02d53f77ecccbcfafb5b5d90` |
| main_upper_left.step | `4be26c61e59ca3c74f370989097f4bff9edf337fa4de1a30d7e5de9eb7ef52f7` |
| main_upper_right.step | `2791dca8f42b86a49b9e685f0f85d896642cbe9975a89bf1524bed89eddfea8f` |

The following outputs are relative to `rawlocal/panel-local-net-completion/attempt05/`:

| Frozen output | SHA-256 |
| --- | --- |
| Attempt05 executed producer snapshot | `595225593819cecbcbe865e6c90e98b043e585a72891cd1a3fcdc19b53ae46b7` |
| summary.json | `61223ff7ffae4a4cc7bca567c0d3a2aac1fc69674795a7cfe0f1f06c303bf4b3` |
| receipt.json | `cc0913beefa78e9cb146f257049b45a6388eedcd29fc483b2b1ab5351b171073` |
| sources.json | `7c0169a84e4b518976b98f68f5a7990416baa600155206744f405dc90acc276a` |
| geometry.json | `758b5156f0d5ce9d0c46a0fd7f29b47d59fe408a122c6eec7e4d7de34fc0dd4c` |
| method-validation.json | `7575cf1af8ee9342d8992cfc26e8f39c3eb6da90173bf1620d03bf1c9f51e49c` |
| original104-screw-actions.jsonl | `46f3269b111b40235cfdf0f1f08b51241fb43d0dc97dd0df6bd8b202a2475f46` |
| original104-panel-cut-actions.jsonl | `098bc14538cd1b806714a4ac66a00408e1bc0302af72672f5d9574bbac992bcb` |
| original104-panel-balances.jsonl | `9fff26073c76d8b9882b611994e8e3f6ae2d08218915ee7a12d67d4f6d8a3cff` |
| original104-screw-local.jsonl | `f3b670850e6b34c7497bae15caf953fd2a147cd24ec7caba2b94bc013d6c1329` |
| original104-net-sections.jsonl | `f9a54d37c45abd13748f767247f5b16a78c127da3a34801b8b966a72cbaa7b50` |
| screw-local.jsonl, proposal live/permanent | `22c318ba3d7922094a0acb0503242d18be63a425a97ef9e87c9d559ba77f0bfb` |
| net-sections.jsonl, proposal live/permanent | `34158ab3b3c3021f108e041e33deadb064c7482278c36eb565ba87dc6c5f4c22` |
| hold-local.jsonl | `6183259404dabbd88443145bc438f29117937e286de5a2b6f9223b32c5d050b6` |

Supplementary original104 permanent inputs are relative to `rawlocal/dead-load-check/parent-attempt06/`; outputs are relative to `rawlocal/panel-local-net-completion/original104-permanent-attempt01/`. The current producer includes the supplementary permanent adapter; attempt05 retains its earlier producer snapshot and unchanged hashes.

| Supplementary input/output | SHA-256 |
| --- | --- |
| Source comparison.json | `20802196776a89ea8b041832b413ef8d8613493b1bf36f89a3810807c5166e75` |
| Source response.npz | `9ff6f4ca177029b2c03acfb5425be9f943ad34679c8ab59013eb36764dd92f14` |
| Supplementary executed producer.py.snapshot | `8034adfee0f052aebf3f51aecfaf07a82e9cdcee5264e3de0c5f79b84b6f93cd` |
| summary.json | `73229dc9fdaa70a0ce1daeab20131b7a1515ed306da26027fc4ce65383a8daa5` |
| receipt.json | `488eeb467fbc0c1fa54fda68565ea94800ab1c667e27a44e88bcb3b66d92e6bd` |
| sources.json | `cf6c071a2270e471e12646bbd98d3f565fc5771f09fbdc2b2416729153173fcf` |
| screw-actions.jsonl | `fd0d614eddb57bf54a3932fe4f52d6d84758b125303db32390f24cda25e500ed` |
| panel-cut-actions.jsonl | `ddefee2d0884d51c84a8808e690e443edc5a7e1796ea3581d4192974795c7137` |
| panel-balances.jsonl | `f8b2a63f7e522633b4ce2af7f3a29dbe0787df754f7d488bee5c0fa819adeae3` |
| screw-local.jsonl | `0827c8fddd77918ff1ee775b78b4990c37a24c7b27639c83069edce207c6288f` |
| net-sections.jsonl | `9a69681aa9bfd25af56a353f3b184dc9c3757209748865671904f2b9795ca9fa` |

## Owned changes and retention

Only the new [producer](panel-local-net-completion.py), this note and ignored `rawlocal/panel-local-net-completion/` outputs are owned by this worker. Attempt05 is 27,427,258 bytes, including detailed actions, local/net comparisons and snapshots; primary PDFs are shared once in this owned `source-cache/`. Earlier owned attempts 01–04 remain recoverable. All source/frozen evidence, owners' work and `/tmp` are preserved. An initial inert helper import emitted an ignored `__pycache__/panel-reference-completion.cpython-312.pyc`; that incidental cache is preserved and was reported to parent. Subsequent execution uses pure definition extraction and `-B`.

The supplementary original104 permanent output is a further 1,796,226 bytes and remains in the ignored owned area. It reuses attempt05 geometry/method evidence and creates no mesh, native output, copied dependency or copied primary PDF. The local/net numerical inventory is complete for the declared source states and resistance hypotheses. Active follow-up is the parent's disposition of retained exceedances and any changed joint/frame coupling actions, with material/contact and loaded-hole/fracture applicability limits kept distinct. No geometry redesign or hardware repair is performed here. Both numerical packets and their source cache stay active reproduction evidence. No raw attempt is pruned or proposed for deletion; archive/retention decisions stay with parent and the existing repository process.

The preexisting 29,582-byte version of this leaf was preserved before the permanent amendment at `source-cache/panel-local-net-completion.before-original104-permanent.md.snapshot`, SHA `0e095b8ef99e330abd3ed2fb746bced5a504a93a6496c65c4dae4ce295a3af37`. Its original104 permanent missing-input statement remains recoverable; the maintained note records the completed numerical branch.
