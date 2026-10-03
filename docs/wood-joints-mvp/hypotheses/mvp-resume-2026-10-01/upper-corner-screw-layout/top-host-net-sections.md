# Top host net sections at the current corner bores

Status: parent completed the finite original-frame section and compatible-face comparisons in `attempt02` and `attempt03`. The top rail's equivalent point-load field exceeds both declared shear references; the two side hosts' nominal component bounds stay below them. The deciding cut lies inside the joint transfer footprint, so these results do **not** establish an exceedance under the current redistributed physical host loading. Local host-action replacement and finite pressure placement are required before that interpretation. All existing HOLD, physical-release and 47-criterion authority boundaries remain unchanged.

## Decision this check supports

The existing member screen excludes every bore interval from its rectangular stress comparisons. The corner host-cut packet preserves external balances but does not compare the retained host ligaments under the complete member cut. This producer fills that specific gap for `base_rail_top`, `base_side_left` and `base_side_right` at the eight current top-corner structural bores. It does not change any force state or geometry.

The parent should inspect the largest same-state normal and shear reference indices, their host, case, station and before/after limit. A nominal index above one identifies a section/reference sensitivity under the **original integrated-frame point allocation**. A physical interpretation inside a joint footprint additionally requires the current local host action distribution. Indices below one do not establish splitting resistance, local bore stresses or joint compatibility.

## Frozen geometry and scope

| Host | Actual structural openings used | Saved stations | Signed traces across six cases |
| --- | --- | ---: | ---: |
| Top rail | Four unchanged 7.5 mm full-width bores, two pairs | 12 | 144 |
| Left side | Two corrected 9 mm full-width replacement bores | 13 | 156 |
| Right side | Two corrected 9 mm full-width replacement bores | 13 | 156 |
| Total | Eight bores | 38 | 456 |

Rail bore centers are at 45.45 and 2211.975 mm along its grain. Each pair leaves three nominal rectangular ligaments at its center section. The side centers are at 2397.892606 and 2465.742606 mm along each side's grain; each center section leaves two ligaments. Existing saved centers, tangencies and intervening recorded stations are used, without a new station search or continuous-maximum claim. Before/after traces preserve the source point-action partition; they are not additional frame cases.

The unchanged rail cylinders are matched to proposal lines and checked for full 38.1 mm width, complete angular trim and 7.5 mm diameter. Each corrected side cylinder replaces an explicitly removed original feature (`facet004` for `side_1`, `facet002` for `side_2`). The new line and 9 mm diameter are bound to the proposal, corrected STEP hash, saved interval and recorded full-width void volume through 88.9 mm of timber. The old cylinders are excluded. Corrected side hosts have no matching saved exact CAD sections; old side sections remain non-applicable. Two unchanged rail center sections crosscheck nominal area and centroid against saved exact geometry. The centroid crosscheck uses saved GLOBAL coordinates translated to the beam cut datum; the source's `centroid_relative_uv_mm` belongs to a different section-plane origin and is retained only as provenance.

The source's finite outward planes supply the outer rectangle. The producer extracts only `basis` and `rectangle_at` from authenticated `member_screen.py`; it does not import the frame producer or load CAD. Any unsupported outer profile, additional overlapping opening, partial bore, missing saved station or changed source raises `STOP` with the affected fact. Geometric agreement uses 0.00001 mm for saved-coordinate transformations and 0.001 mm²/mm³ for area/volume checks; action partitions retain the source's 0.000001 mm tolerance. These are bookkeeping tolerances, not fabrication tolerances or measured accuracy.

## Complete signed source actions

The frozen source is `member-screen-attempt02/four-screw-layout01`, bound to `operators-attempt02` and `frame-250-attempt02`. It retains six cases, the original 100 mm hold lever, a 250 lb climber with the declared dynamic multiplier and the saved simultaneous accessory, gravity and lateral actions. Its nonunique motion/stability boundary is preserved.

For every selected trace the producer independently reconstructs the complete negative-half internal wrench in GLOBAL coordinates from **all** saved host point forces, their actual moment arms and their free couples. The datum is `start + station * grain`. It rotates this wrench into the host's actual grain/u/v frame and checks agreement with the saved full member trace. The opposite half checks whole-member balance. No local bolt-shaft or corner first-order host field supplies these member loads. Therefore this exact replay retains the original equivalent point allocation, including its inside-footprint limitation; it does not replace it with current physical host pressures.

`corner-timber-sections.section` gives the actual chord slots and retained rectangles. `corner-net-section.nominal_section` retains the net centroid, translates moments to it, and recovers all six original signed force/couple components after regional sharing. Its existing assumptions remain explicit:

- A common longitudinal strain plane and intact grain-end bridges relate disconnected regions.
- Regional transverse forces share by retained area, retaining their centroid-offset moments.
- Equal longitudinal shear moduli, common twist and nominal free warping share torque by rectangular Saint-Venant `J`.
- The same-region shear comparison is `1.5*hypot(Vu,Vv)/A + tau_T`, compared with the saved parallel-grain `Fv` reference.

These assumptions do not supply solved contact, clamp preload, end-bridge strength, exact perforated-body torsion or a new torsion allowable. No balancing free couple is added. The existing translated-rectangle known-answer arithmetic is included once in the parent's build, alongside force, moment and regional-recovery checks.

## Two explicit timber references

All three hosts retain their **saved member-specific** DF-L No. 2 factors: `CF(Fb)=1.3`, `CF(Ft)=1.3`, `CF(Fc)=1.1`. They do not inherit the cleats' material factors. The original dry, unincised, normal-temperature assumptions, `Cfu=Cr=1`, and absence of credited `CL`/`CP` remain visible.

| Parallel-grain reference | Original `CD=1`, MPa | Conditional peak `CD=1.25`, MPa |
| --- | ---: | ---: |
| Bending `Fb` | 8.066866 | 10.083583 |
| Tension `Ft` | 5.153831 | 6.442289 |
| Compression `Fc` | 10.238715 | 12.798393 |
| Shear `Fv` | 1.241056 | 1.551320 |

The second column of results applies the parent's existing hypothetical cumulative peak exposure of no more than seven days, supported by the pinned [NDS Chapter 2 source](../../upper-block-strength-2026-10-01/source-cache/chapter2-2024-awc.pdf). It multiplies only these timber stress references. It does not alter forces, geometry, stiffness, duration assumptions of other components or the original `CD=1` comparison. It does not replace the parent's separate permanent-load check.

Each scenario reports same-state total tension, total compression, absolute bending, the diagnostic mean-axial-plus-bending reference sum, transverse shear, torsional shear and their same-state nominal shear sum. The diagnostic normal sum is not a newly adopted interaction equation. The 456 source traces produce 912 duration comparisons, with global, per-host and per-case witnesses retained.

## Parent execution and receipt

API: `build(output: str | Path) -> dict` in [top-host-net-sections.py](top-host-net-sections.py). Use a fresh child of `rawlocal/top-host-net-sections`; existing output children are refused.

From the repository root:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/top-host-net-sections.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/top-host-net-sections/attempt01
```

The parent owns serialized execution. The worker prepared the producer and note, authenticated the fixed source pins, parsed the source and checked formatting/lint. It did not execute the producer, frame/CAD/native mechanics, software tests or an agent review loop.

The producer authenticates fixed inputs, original/current STEP bindings and its own bytes before and after calculation. It writes ignored `checks.json`, `receipt.json` and `producer.py.snapshot`. The receipt records all source and output hashes. The returned compact result includes the 38-section/456-trace/912-comparison census, both duration scenarios' deciding witnesses and accounting residuals. A successful arithmetic status means only that this finite calculation completed; every qualification/release flag stays false.

## Completed section result and preserved STOP

Parent completed `rawlocal/top-host-net-sections/attempt02`: eight bores, 38 recorded sections, 456 full signed traces and 912 duration comparisons. Its 21 source pins match. Full action reconstruction differs from the saved cuts by at most `1.60e-12 N` and `2.97e-9 N mm`; regional recovery differs by at most `3.13e-13 N` and `5.83e-11 N mm`. The unchanged rail's saved exact area and GLOBAL-centroid crosschecks complete without changed tolerances.

| Finite comparison | Original `CD=1` | Conditional peak `CD=1.25` |
| --- | ---: | ---: |
| All-host normal reference-sum peak | 0.164346 | 0.131477 |
| All-host total tension reference peak | 0.169918 | 0.135934 |
| Top rail scalar transverse-plus-torsion bound | **1.480491** | **1.184392** |
| Left-side scalar shear bound | 0.691579 | 0.553263 |
| Right-side scalar shear bound | 0.682531 | 0.546025 |

The deciding rail bound is **K12-right, right bore center at 2211.975 mm, before the station**. The first retained region is approximately 38.1 × 59.6 mm. Its `CD=1.25` transverse magnitude bound is **0.349944 MPa**, its nominal torsional peak is **1.487428 MPa**, and their scalar sum is **1.837372 MPa** against **1.551320 MPa**. The signed cut is `[-995.353594, -406.265451, 1031.266899, -50562.536778, -23299.418604, 22818.154236]` in grain/u/v N and N mm; the net-centroid torque is `-50073.845378 N mm`. Torque alone compares at 0.958814; the scalar sum compares at 1.184392. An exceeded upper bound does **not** establish that a point in the declared field exceeds the reference.

| Artifact | SHA-256 |
| --- | --- |
| Executed section producer snapshot | `c8c6e3c23bfe5e7d6999160546bc8f6ad106c178219307aa1d984367fcd80364` |
| `attempt02/checks.json` | `7e0977645a79d11b3456ff82cc987f2466becd135f192e6aca3c4c53875487a9` |
| `attempt02/receipt.json` | `486b7d5f5da12e78e94b0deb0c2ab8631f27c1992ee9b49f32c0554249eeff29` |

Parent's first invocation stopped because the initial producer compared the source's section-relative centroid with the beam-relative nominal centroid. The source section plane origin differs from the beam cut datum. The corrected implementation uses the existing saved GLOBAL centroid, translates it to the beam cut datum and rotates into the actual frame. Geometry, forces and tolerances are unchanged. The exact failed producer `68364d54972a389f6e34a74b3690d84128628d01c19ffbd4d9d7e1f9d4d1badd` and STOP description remain in ignored `stop-attempt01/`. The completed parent receipt and executed snapshot preserve the corrected calculation independently of later live-producer changes.

## Completed bounded check: compatible face vectors

`build_faces(output: str | Path) -> dict` reads the frozen `attempt02` receipt, report and executed snapshot. It retains every saved regional force, torque, rectangle, material reference and original scalar bound. The existing `member_stability.shear_check` method and `nominal_section` rectangle coefficients supply four **signed face-midpoint vectors** for each region, state and duration reference. No field solve or geometry reconstruction runs.

At a u-face midpoint the parabolic transverse u component vanishes, while transverse v is `1.5*Vv/A`; torsion adds `side_u*T*cv` in v. At a v-face midpoint transverse v vanishes, while transverse u is `1.5*Vu/A`; torsion adds `-side_v*T*cu` in u. Both opposite faces are evaluated, retaining additions and cancellations in the same vector at the same face. The saved equal-modulus rectangular coefficients and common-twist sharing remain the existing assumptions; no orthotropic reinterpretation or material change is introduced.

The face maximum is a **lower bound** on the maximum of the declared nominal field. A face value above one demonstrates an exceedance of that working reference. Faces below one alone leave the interior unresolved when sufficient bounds remain above one. The report preserves the original scalar bound and separately reports the existing directional component bound `hypot(abs(su)+abs(T*cu), abs(sv)+abs(T*cv))/Fv`; either sufficient bound below one covers the nominal rectangle under the same assumptions. No interior sampling or exact perforated-body stress claim is supplied.

Parent command, using a fresh child:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/top-host-net-sections.py --faces --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/top-host-net-sections/attempt03
```

Parent completed `attempt03`. It keeps both duration scenarios, the original component bounds, all deciding signed face vectors and global/host/case witnesses. It distinguishes a declared face exceedance, a sufficient nominal rectangle bound below one, and an unresolved interior. This refinement does not certify splitting, bore concentrations, physical wood or the complete joint.

| Original point-allocation compatible-face result | `CD=1` | `CD=1.25` |
| --- | ---: | ---: |
| Peak signed same-face shear/reference | **1.460867** | **1.168694** |
| Traces with a declared face exceedance | 18 | 8 |
| Faces below reference but interior unresolved | 2 | 1 |

The peak remains **K12-right, right rail bore center, before 2211.975 mm**, in region 0 on its `u-` face. Transverse v shear **0.325590 MPa** and torsion v shear **1.487428 MPa** add at that same midpoint, giving **1.813018 MPa**. The global point is approximately `[1081.675, 1488.266175, 2146.461725]` mm. This confirms the original nominal field's exceedance is not merely an addition of peaks at different faces. It does not resolve whether the current local physical loading produces that cut.

| Artifact | SHA-256 |
| --- | --- |
| Executed compatible-face producer snapshot | `bfa6a1716908efdb83b3ebf07b0def1bd9114d448dbdf294057b832749d8b3e8` |
| `attempt03/checks.json` | `3a9a3c357bd419ae3264429c5c02135c9f52b13e5dbbae0970861fc6c9c309f9` |
| `attempt03/receipt.json` | `3b0a965a50baba8d452cc9eb94202b4f95c1df787a05ecab593c1a92705afee9` |

## Deciding cut's load-allocation scope

The read-only inventory at `rawlocal/top-host-net-sections/scope-attempt01/action-inventory.json` records the exact original rows, stored global forces/free couples and points, current physical host actions and their source hashes. SHA-256: `6c2cb242bb153179323a49e01b3e1e3acfceae2ea68b8c6759f65ad76e3d576f`. No cut, mechanical solution or pressure map was recomputed for this inventory.

The deciding cut is **inside** the top-right cleat/rail transfer footprint `[2168.525, 2257.425]` mm and both rail bore intervals `[2208.225, 2215.725]` mm. The original source applies 22 incident corner rows as equivalent point actions:

| Original rows | Exact source identities | Saved grain stations / footprints, mm |
| --- | --- | --- |
| 1808, 1809 | `top_outer/clip_single_top_right_2/rail_1/plane-77` | Point at 2211.975 |
| 1810, 1811 | `top_outer/clip_single_top_right_2/rail_2/plane-78` | Point at 2211.975 |
| 1886 | `top_outer/clip_single_top_right_2/rail_1/outer-seat-axial-tie` | Point at 2211.975 |
| 1887 | `top_outer/clip_single_top_right_2/rail_2/outer-seat-axial-tie` | Point at 2211.975 |
| 1870–1885 | `top_outer_right_cleat/contact-cell-18` through `contact-cell-33` | Point groups at 2179.6375, 2201.8625, 2224.0875 and 2246.3125; each saved patch footprint is `[2168.525, 2257.425]` |

The source's **before** partition places all six coincident bolt-plane/tie rows in the positive grain half. Each contact row is placed wholly according to its saved point station; its footprint metadata is not integrated across the cut. `top_corner_actions.host_cut` explicitly describes this as equilibrium of point actions, not integrated solid traction.

The current compatible local host source is `rawlocal/corner-first-order/attempt01/checks.json`, SHA-256 `b15b57d3879fdca2dac607d11a2ad127acd1008f6c2a6f546333a1b26c754cfe`, under its K12-right/right state's `hosts/base_rail_top`. That record contains **48 host bore-station resultants, 512 host washer pressure quadrature actions and 16 face-cell actions**. It retains the original whole-interface wrench to its recorded residual but changes local placement and sharing. For example, original face row 1873 (`contact-cell-21`) has zero force while the current physical source activates it; rows 1877/1881/1885 (`contact-cell-25/29/33`) also change their forces. Original `contact-cell-25` global Y force is `27.403276 N`; current physical Y force is `81.305198 N`. Whole-wrench conservation consequently does not authenticate an internal cut inside the footprint.

The joined current working register (`rawlocal/working-joint-register/attempt02/register.json`, SHA-256 `d6fbabe799e77ca199a8054eed85378db8284f05bb965687d47fbd3e72a4ff44`) explicitly distinguishes corrected local allocation from `integrated_frame_allocation` comparison evidence. Its member evidence does not transfer a redistributed local bolt/contact stress field. This top-host worksheet uses the latter original-frame allocation deliberately, so its completed status must keep that limitation.

The existing `corner-bore-wall.py` provides finite radial pressure half-cut integration, but its current `profiles()` selects **`receiver == cleat`** and `physical_cleat_actions`; its saved wall packet does not map these host bores. Host bore-axis resultants alone also do not specify how their cylindrical pressures lie on each grain half. The finite host washer quadrature already supplies pressure placement; host bore-wall mapping and appropriate face-cell partition must accompany the local replacement rather than applying original axial ties again.

Other active source contacts `contact_83_7/9/13/15/21/23` (rows 935/937/941/943/949/951, `main_upper_right`) retain saved patch bounds `[1128.7125, 2257.425]` mm that also cross the cut. Their point stations are farther left. These whole-patch bounds are metadata, not proof that each individual quadrature cell spans the deciding plane; this inventory does not invent their pressure distribution or transfer a panel acceptance.

## Decision after face postprocessing

The next single check most likely to change the decision is a **current physical-host half-cut replacement** at the deciding rail bore, before selecting a geometry/material correction. Replace the 22 original incident corner rows once with the saved compatible host bore/washer/face actions; retain every other simultaneous host action and free couple. Preserve the whole-host wrench, map finite host bore-wall and washer pressures across the grain cut, and use the actual face-cell extent rather than its lumped point where it crosses that plane. The existing cleat wall helper is reusable, but its host adaptation is not yet completed here. This is a bounded saved-data postprocessing proposal; it does not require a new frame/native/CAD solve.

Recompare the same nominal ligament hypotheses only after that complete cut is available. Until then the 1.168694 face result is an original-point-load sensitivity, not a demonstrated current physical host failure. Preserve it and the original bounds; do not reinterpret whole-host equilibrium as local-cut equality. Splitting/local concentrations and the separately recorded panel head/withdrawal deficits remain unresolved and unchanged.
