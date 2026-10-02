# Same-state six-case timber member screens

The six NOMINAL-GAP cases in `frame-250-attempt02/response.npz` have been screened using the corrected physical operators and loads in `corner-frame-attempt01/`. This packet supplies complete signed member actions and elementary stress references for the conditional shop model. It does not establish finished-member, local wood, stability, or complete-joint acceptance.

**Result:** 264 whole-member balances across 20 frame timbers and 24 connector blocks; 55,176 two-sided section traces. All source SHA-256 bindings and whole-member action closures meet the recorded arithmetic limits.

The largest absolute whole-member residuals are **1.09424e-11 N** and **7.06268e-09 N·mm**; limits are 0.1 N and 2 N·mm. Both cut halves, every point force and free couple, contact footprints, and the source zero-force rows are retained in the saved arrays.

## Six-case results

These are dimensionless conditional reference sums. The normal sum includes signed axial force and both bending components in the same cut. The shear sum includes both transverse components. A value below one is an elementary arithmetic result; it does not clear buckling, torsion, notches, bores, or connection-zone failure.

| Case | Governing gross normal / member | Governing gross shear / member | Governing bore-free normal / member | Governing bore-free shear / member |
| --- | --- | --- | --- | --- |
| a12-rear | 0.5178 / `base_rail_top` | 0.3108 / `base_rail_top` | 0.5148 / `base_rail_top` | 0.3108 / `base_rail_top` |
| a12-forward | 0.4155 / `base_rail_top` | 0.2815 / `base_post_outer_left` | 0.4132 / `base_rail_top` | 0.2815 / `base_post_outer_left` |
| a12-left | 0.4963 / `base_rail_top` | 0.2999 / `base_rail_top` | 0.4936 / `base_rail_top` | 0.2999 / `base_rail_top` |
| k12-right | 0.5736 / `base_rail_top` | 0.3264 / `base_rail_top` | 0.5715 / `base_rail_top` | 0.3264 / `base_rail_top` |
| k12-rear | 0.5912 / `base_rail_top` | 0.3562 / `base_rail_top` | 0.5890 / `base_rail_top` | 0.3562 / `base_rail_top` |
| a1-rear | 0.1719 / `base_rail_top` | 0.2381 / `base_header` | 0.1719 / `base_rail_top` | 0.2381 / `base_header` |

The governing applicable normal reference is **0.588956**, `base_rail_top` in `k12-rear` at **1963.304 mm**. The governing transverse reference is **0.356218**, `base_rail_top` in `k12-rear` at **2201.863 mm**. These locate the first member checks to integrate; their bore/connector-zone, torque and restraint checks remain open.

## Member envelope across the six cases

Every envelope entry points to one simultaneous case and cut; component maxima from different states are not added. The JSON preserves the signed force/couple vector, section dimensions, centroid shift and contact footprints for each governing cut.

| Member | Gross normal | Gross shear | Bore-free normal | Bore-free shear | Governing bore-free case and station (normal / shear) |
| --- | ---: | ---: | ---: | ---: | --- |
| `base_floor_left` | 0.2247 | 0.1475 | 0.2223 | 0.1475 | a12-left, 103.660 mm / a12-left, 75.729 mm |
| `base_floor_right` | 0.2235 | 0.1470 | 0.2212 | 0.1470 | k12-right, 103.660 mm / k12-right, 75.729 mm |
| `base_header` | 0.1515 | 0.2381 | 0.1515 | 0.2381 | k12-rear, 1417.129 mm / a1-rear, 22.225 mm |
| `base_post_center_left` | 0.0370 | 0.0738 | 0.0363 | 0.0718 | a12-forward, 57.929 mm / a12-forward, 198.651 mm |
| `base_post_center_right` | 0.0226 | 0.0433 | 0.0222 | 0.0433 | k12-right, 57.929 mm / k12-right, 198.651 mm |
| `base_post_outer_left` | 0.1247 | 0.2815 | 0.1123 | 0.2815 | a12-left, 103.660 mm / a12-forward, 194.071 mm |
| `base_post_outer_right` | 0.1240 | 0.2651 | 0.1116 | 0.2651 | k12-right, 103.660 mm / k12-right, 103.660 mm |
| `base_principal_center_left` | 0.1234 | 0.0485 | 0.1233 | 0.0485 | a1-rear, 1242.138 mm / a1-rear, 162.846 mm |
| `base_principal_center_right` | 0.0968 | 0.0418 | 0.0968 | 0.0418 | k12-rear, 1249.592 mm / k12-right, 162.846 mm |
| `base_rail_bottom_left` | 0.1442 | 0.1774 | 0.1425 | 0.1774 | a1-rear, 297.296 mm / a1-rear, 297.500 mm |
| `base_rail_bottom_right` | 0.0228 | 0.0329 | 0.0224 | 0.0329 | k12-rear, 343.954 mm / k12-rear, 340.801 mm |
| `base_rail_service_lower_left` | 0.0319 | 0.0280 | 0.0317 | 0.0280 | a1-rear, 693.154 mm / k12-right, 697.296 mm |
| `base_rail_service_lower_right` | 0.0196 | 0.0277 | 0.0193 | 0.0277 | a12-left, 348.096 mm / a12-left, 340.801 mm |
| `base_rail_service_upper_left` | 0.0235 | 0.0286 | 0.0234 | 0.0286 | k12-right, 693.154 mm / k12-rear, 697.296 mm |
| `base_rail_service_upper_right` | 0.0233 | 0.0298 | 0.0232 | 0.0298 | a12-left, 348.096 mm / a12-rear, 340.801 mm |
| `base_rail_top` | 0.5912 | 0.3562 | 0.5890 | 0.3562 | k12-rear, 1963.304 mm / k12-rear, 2201.863 mm |
| `base_side_left` | 0.3806 | 0.2012 | 0.3763 | 0.2012 | a12-rear, 2012.455 mm / a12-rear, 2091.573 mm |
| `base_side_right` | 0.3765 | 0.2027 | 0.3725 | 0.2027 | k12-rear, 2012.455 mm / k12-rear, 2414.355 mm |
| `bottom_center_left_cleat` | 0.0004 | 0.0030 | 0.0004 | 0.0030 | a12-left, 63.601 mm / a1-rear, 39.599 mm |
| `bottom_center_right_cleat` | 0.0004 | 0.0021 | 0.0004 | 0.0021 | k12-right, 63.601 mm / k12-right, 39.599 mm |
| `bottom_outer_left_cleat` | 0.0146 | 0.0784 | 0.0139 | 0.0784 | a1-rear, 56.099 mm / a1-rear, 56.099 mm |
| `bottom_outer_right_cleat` | 0.0004 | 0.0035 | 0.0004 | 0.0035 | a12-left, 63.601 mm / a12-left, 39.599 mm |
| `center_post_cleat_left` | 0.0007 | 0.0017 | N/A | N/A | N/A / N/A |
| `center_post_cleat_right` | 0.0009 | 0.0018 | N/A | N/A | N/A / N/A |
| `center_principal_cleat_left` | 0.0025 | 0.0029 | N/A | N/A | N/A / N/A |
| `center_principal_cleat_right` | 0.0026 | 0.0031 | N/A | N/A | N/A / N/A |
| `knee_outer_left_inner_frame_block` | 0.0174 | 0.0313 | N/A | N/A | N/A / N/A |
| `knee_outer_left_spine` | 0.0920 | 0.1551 | 0.0863 | 0.1551 | a12-left, 195.367 mm / a12-left, 195.367 mm |
| `knee_outer_right_inner_frame_block` | 0.0171 | 0.0313 | N/A | N/A | N/A / N/A |
| `knee_outer_right_spine` | 0.0922 | 0.1559 | 0.0873 | 0.1559 | k12-right, 171.876 mm / k12-right, 195.367 mm |
| `left_service_inner_lower_cleat` | 0.0004 | 0.0021 | 0.0003 | 0.0021 | a1-rear, 56.099 mm / a1-rear, 39.599 mm |
| `left_service_inner_upper_cleat` | 0.0004 | 0.0034 | 0.0004 | 0.0034 | a12-left, 56.099 mm / a12-left, 90.012 mm |
| `left_service_outer_lower_cleat` | 0.0003 | 0.0025 | 0.0003 | 0.0025 | k12-right, 63.601 mm / k12-right, 89.849 mm |
| `left_service_outer_upper_cleat` | 0.0004 | 0.0030 | 0.0004 | 0.0030 | k12-right, 56.099 mm / k12-right, 39.599 mm |
| `lumber_leg_left` | 0.1657 | 0.1381 | 0.1657 | 0.1912 | a12-left, 1723.373 mm / a12-forward, 34.408 mm |
| `lumber_leg_right` | 0.1669 | 0.1409 | 0.1669 | 0.1891 | k12-right, 1723.373 mm / k12-right, 34.408 mm |
| `top_center_left_cleat` | 0.0011 | 0.0082 | 0.0011 | 0.0082 | a12-left, 63.601 mm / a12-left, 89.926 mm |
| `top_center_right_cleat` | 0.0016 | 0.0116 | 0.0013 | 0.0116 | k12-rear, 56.099 mm / k12-rear, 72.599 mm |
| `top_outer_left_cleat` | 0.0450 | 0.1546 | 0.0435 | 0.1546 | a12-left, 55.349 mm / a12-left, 47.101 mm |
| `top_outer_right_cleat` | 0.0504 | 0.1747 | 0.0487 | 0.1747 | k12-rear, 64.351 mm / k12-right, 64.351 mm |
| `wj04_lower_full_stock_cleat` | 0.0003 | 0.0017 | 0.0002 | 0.0017 | a12-left, 63.601 mm / k12-right, 89.849 mm |
| `wj04_upper_g7_crosscut_full_stock_cleat` | 0.0002 | 0.0034 | 0.0002 | 0.0034 | k12-right, 47.201 mm / k12-right, 23.199 mm |
| `wj06_outer_lower_right_cleat` | 0.0003 | 0.0025 | 0.0003 | 0.0025 | a12-left, 63.601 mm / a12-left, 89.849 mm |
| `wj06_outer_upper_right_cleat` | 0.0004 | 0.0031 | 0.0004 | 0.0031 | a12-left, 63.601 mm / a12-left, 89.926 mm |

## Geometry applicability and open checks

160 prior exact section planes still match the current finished STEP bytes; 131 planes have a changed STEP binding and are explicitly non-applicable. Earlier three-case forces and accepted-state labels are never imported. Matching saved net sections retain their actual area, centroid, covariance and disconnected-ligament flag without assigning a common strain, invented resistance, or force division to disconnected regions.

The finite surface register supplies every cylinder/passages interval and outward planar face. Bore-free full rectangles and the source-bound full-depth rear-leg 1:12 recess are screened with their calculated width, depth and centroid. An intersecting bore or passage makes the rectangular stress screen non-applicable. Clipped end profiles retain their geometry and signed cuts, but have no stress ratio: the source lumped end loads do not define the local traction field through a section tending to zero area. The two corrected top blocks and two side hosts use only their hash-bound correction geometry; former bore slices on those bodies are not transferred.

The first saved runs in `member-screen-attempt01/` (top corners only) and `member-screen-attempt02/` (four joints) are preserved. They included mechanically inapplicable terminal-profile ratios; use the corrected child packet linked below for integration. Its changed applicability interpretation is explicit and does not change the frozen response or physical model.

The exact remaining checks are:

- At every listed bore/passages interval, recover the finished connected section and its load transfer, including the 32 preserved LED/service patches and the revised top-corner bores. `geometry.json` identifies each member, feature and station interval. The signed six-case cuts are available; bore concentrations, ligament sharing, net normal resistance and local shear are not supplied by a gross rectangle.
- At rear-leg recess/runout cuts, use the actual cut profile and centroid with the signed six-case actions, then apply the connection/notch shear and local splitting provisions. The bore-free profile arithmetic does not accept the notch or its stress concentration.
- At clipped runner ends, inclined side/principal bases and rear-leg tips, replace the lumped point-load beam interpretation with an applicable local end/load-transfer description. Their exact station lists are in `open_checks_by_member`; terminal-profile arithmetic is excluded rather than reported as a wood-resistance failure.
- Resolve simultaneous orthotropic shear/torque and short-block connection-zone disturbance. All torques and interface free couples are retained; no torsional resistance or local wood qualification is inferred.
- Specify member unsupported lengths and effective restraint for compression and bending stability, including the header, inclined sides/principals and rear legs. No CL, CP or buckling acceptance is calculated from these gross beam proxies.
- Keep the four remanufactured blocks on the existing hypothetical final-piece DF-L No.2, CF=1 study scenario until their final-product grade/size-factor basis is supplied. No source grade transfers. Conditional Hillman spring laws, proportional accessory placement and unverified no-slip support remain inherited model assumptions.

## Material and arithmetic

The current conditional material packet provides DF-L No.2 base values: Fb=900 psi, Ft=575 psi, Fc=1350 psi and Fv=180 psi. Standard 2×6/4×6 sections use CF=(1.3, 1.3, 1.1) for Fb/Ft/Fc; standard 4×4 blocks use (1.5, 1.5, 1.15). The two corrected 88.9×139.7 mm (3½×5½ in.) top cleats use 4×6 factors. The four ripped blocks retain the source CF=1 hypothetical study. Normal duration, dry service, unincised wood and normal temperature are declared; Cfu=Cr=1. The references include no CL or CP stability credit and are not fully adjusted NDS design resistances.

On the negative half's outward +grain cut, N>0 is tension. A rectangular section uses σ=N/A + Mu·v/Iu − Mv·u/Iv; the four corner stresses bound its linear normal field. The reported normal sum is max(Nt/(A·Ft), Nc/(A·Fc)) + (|Mu|/Su+|Mv|/Sv)/Fb. The transverse screen is 1.5(|Vu|+|Vv|)/(A·Fv), a component-sum proxy. Neither is adopted as an NDS combined-load or local connection criterion.

All actions remain the source point actions, including the corrected F load operator and dead-load factor 1.111135830034241. The old beam-selfweight producer's line-resultant/first-moment convention is reused only as a load diagnostic. Its `member-beam-selfweight.json` is absent locally; the saved 20-member finite-bin profile and exact member-solid packet remain bound as geometry/self-weight evidence. Their older 600 kg/m³ distribution is not substituted into this model or counted twice. No OBB extraction, CAD rebuilding, test, review, frame solve or native run is performed.

## Files and reproduction

- [member-results.json](member-screen-attempt02/four-screw-layout01/member-results.json): 264 member results, complete transfer wrenches and governing stress cuts, source/output hashes and claim limits.
- [member-results.csv](member-screen-attempt02/four-screw-layout01/member-results.csv): all six cases and 44 members in a compact integration table.
- [geometry.json](member-screen-attempt02/four-screw-layout01/geometry.json): actual bore/profile applicability, matching and refused saved section planes, source member/STEP bindings and point-action identities.
- [action-section-arrays.npz](member-screen-attempt02/four-screw-layout01/action-section-arrays.npz): signed point forces/free couples and both cut-half wrenches; units and indexing are in the result JSON.
- [inputs.json](member-screen-attempt02/four-screw-layout01/inputs.json) and [producer.py.snapshot](member-screen-attempt02/four-screw-layout01/producer.py.snapshot): frozen source bindings, force keys and executed producer.

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/member_screen.py \
  --clearance docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/frame-250-attempt02 \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/member-screen-attempt02/four-screw-layout01
```

The producer accepts `--clearance` (alias `--input-dir`) for a saved response directory and preserves an existing attempt. A changed calculation may use a new child under `member-screen-attempt01/` or `member-screen-attempt02/`. These small outputs remain active for parent integration. Earlier failed/frozen inputs and `/tmp` are preserved; no archive or prune operation is performed. Authority, other owners' files, staging and commits are outside this packet.
