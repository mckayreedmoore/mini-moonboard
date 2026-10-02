# Same-state six-case timber member screens

The six NOMINAL-GAP cases in `top-and-service-frame-attempt02/response.npz` have been screened using the corrected physical operators and loads in `corner-frame-attempt01/`. This packet supplies complete signed member actions and elementary stress references for the conditional shop model. It does not establish finished-member, local wood, stability, or complete-joint acceptance.

**Result:** 264 whole-member balances across 20 frame timbers and 24 connector blocks; 54,888 two-sided section traces. All source SHA-256 bindings and whole-member action closures meet the recorded arithmetic limits.

The largest absolute whole-member residuals are **9.92628e-12 N** and **1.28956e-08 N·mm**; limits are 0.1 N and 2 N·mm. Both cut halves, every point force and free couple, contact footprints, and the source zero-force rows are retained in the saved arrays.

## Six-case results

These are dimensionless conditional reference sums. The normal sum includes signed axial force and both bending components in the same cut. The shear sum includes both transverse components. A value below one is an elementary arithmetic result; it does not clear buckling, torsion, notches, bores, or connection-zone failure.

| Case | Governing gross normal / member | Governing gross shear / member | Governing bore-free normal / member | Governing bore-free shear / member |
| --- | --- | --- | --- | --- |
| a12-rear | 0.4739 / `base_rail_top` | 0.3243 / `base_rail_top` | 0.4713 / `base_rail_top` | 0.3243 / `base_rail_top` |
| a12-forward | 0.3861 / `base_rail_top` | 0.2688 / `base_rail_top` | 0.3840 / `base_rail_top` | 0.2688 / `base_rail_top` |
| a12-left | 0.4596 / `base_rail_top` | 0.3227 / `base_rail_top` | 0.4572 / `base_rail_top` | 0.3227 / `base_rail_top` |
| k12-right | 0.5222 / `base_rail_top` | 0.3634 / `base_rail_top` | 0.5205 / `base_rail_top` | 0.3634 / `base_rail_top` |
| k12-rear | 0.5434 / `base_rail_top` | 0.3735 / `base_rail_top` | 0.5415 / `base_rail_top` | 0.3735 / `base_rail_top` |
| a1-rear | 0.2370 / `base_rail_bottom_left` | 0.1825 / `base_header` | 0.2355 / `base_rail_bottom_left` | 0.1825 / `base_header` |

The governing applicable normal reference is **0.541501**, `base_rail_top` in `k12-rear` at **1963.304 mm**. The governing transverse reference is **0.373502**, `base_rail_top` in `k12-rear` at **2201.863 mm**. These locate the first member checks to integrate; their bore/connector-zone, torque and restraint checks remain open.

## Member envelope across the six cases

Every envelope entry points to one simultaneous case and cut; component maxima from different states are not added. The JSON preserves the signed force/couple vector, section dimensions, centroid shift and contact footprints for each governing cut.

| Member | Gross normal | Gross shear | Bore-free normal | Bore-free shear | Governing bore-free case and station (normal / shear) |
| --- | ---: | ---: | ---: | ---: | --- |
| `base_floor_left` | 0.1221 | 0.1261 | 0.1203 | 0.1261 | a12-forward, 103.660 mm / a12-left, 75.729 mm |
| `base_floor_right` | 0.1114 | 0.1170 | 0.1078 | 0.1170 | k12-right, 103.660 mm / k12-right, 75.729 mm |
| `base_header` | 0.1597 | 0.1825 | 0.1562 | 0.1825 | k12-rear, 1106.851 mm / a1-rear, 22.225 mm |
| `base_post_center_left` | 0.0438 | 0.1031 | 0.0431 | 0.0837 | a12-forward, 189.929 mm / a12-forward, 119.450 mm |
| `base_post_center_right` | 0.0513 | 0.0702 | 0.0498 | 0.0691 | a12-forward, 141.349 mm / a12-forward, 0.000 mm |
| `base_post_outer_left` | 0.1464 | 0.2890 | 0.1414 | 0.2890 | a12-left, 103.660 mm / a12-left, 194.071 mm |
| `base_post_outer_right` | 0.1417 | 0.2879 | 0.1372 | 0.2879 | k12-right, 103.660 mm / k12-right, 194.071 mm |
| `base_principal_center_left` | 0.1083 | 0.0754 | 0.1083 | 0.0754 | a1-rear, 1154.295 mm / a1-rear, 285.116 mm |
| `base_principal_center_right` | 0.0800 | 0.0573 | 0.0800 | 0.0573 | k12-rear, 1374.592 mm / k12-rear, 2457.196 mm |
| `base_rail_bottom_left` | 0.2370 | 0.1536 | 0.2355 | 0.1536 | a1-rear, 297.296 mm / a1-rear, 49.201 mm |
| `base_rail_bottom_right` | 0.0331 | 0.0156 | 0.0331 | 0.0156 | k12-rear, 741.482 mm / k12-rear, 49.201 mm |
| `base_rail_service_lower_left` | 0.0241 | 0.0232 | 0.0239 | 0.0232 | a1-rear, 697.296 mm / a1-rear, 697.296 mm |
| `base_rail_service_lower_right` | 0.0218 | 0.0155 | 0.0213 | 0.0155 | a12-rear, 988.874 mm / a12-rear, 748.096 mm |
| `base_rail_service_upper_left` | 0.0189 | 0.0151 | 0.0189 | 0.0151 | k12-right, 693.154 mm / k12-right, 49.201 mm |
| `base_rail_service_upper_right` | 0.0223 | 0.0149 | 0.0219 | 0.0149 | a12-rear, 988.874 mm / k12-rear, 963.927 mm |
| `base_rail_top` | 0.5434 | 0.3735 | 0.5415 | 0.3735 | k12-rear, 1963.304 mm / k12-rear, 2201.863 mm |
| `base_side_left` | 0.3778 | 0.1985 | 0.3753 | 0.1985 | a12-rear, 1945.970 mm / a12-rear, 2016.874 mm |
| `base_side_right` | 0.3632 | 0.2015 | 0.3609 | 0.2015 | k12-rear, 1970.928 mm / k12-rear, 2016.874 mm |
| `bottom_center_left_cleat` | 0.0052 | 0.0219 | 0.0047 | 0.0219 | a1-rear, 56.099 mm / a1-rear, 72.599 mm |
| `bottom_center_right_cleat` | 0.0015 | 0.0115 | 0.0013 | 0.0115 | a12-rear, 56.099 mm / a12-rear, 72.599 mm |
| `bottom_outer_left_cleat` | 0.0307 | 0.1394 | 0.0292 | 0.1394 | a1-rear, 56.099 mm / a1-rear, 56.099 mm |
| `bottom_outer_right_cleat` | 0.0013 | 0.0144 | 0.0012 | 0.0144 | a1-rear, 56.099 mm / k12-rear, 56.099 mm |
| `center_post_cleat_left` | 0.0181 | 0.0428 | N/A | N/A | N/A / N/A |
| `center_post_cleat_right` | 0.0129 | 0.0379 | N/A | N/A | N/A / N/A |
| `center_principal_cleat_left` | 0.0136 | 0.0241 | N/A | N/A | N/A / N/A |
| `center_principal_cleat_right` | 0.0124 | 0.0236 | N/A | N/A | N/A / N/A |
| `knee_outer_left_inner_frame_block` | 0.0154 | 0.0201 | N/A | N/A | N/A / N/A |
| `knee_outer_left_spine` | 0.0557 | 0.0978 | 0.0538 | 0.0978 | a12-left, 187.865 mm / a12-left, 195.367 mm |
| `knee_outer_right_inner_frame_block` | 0.0145 | 0.0187 | N/A | N/A | N/A / N/A |
| `knee_outer_right_spine` | 0.0514 | 0.0923 | 0.0506 | 0.0861 | k12-rear, 187.865 mm / k12-right, 195.367 mm |
| `left_service_inner_lower_cleat` | 0.0032 | 0.0126 | 0.0031 | 0.0126 | a1-rear, 56.099 mm / a1-rear, 56.099 mm |
| `left_service_inner_upper_cleat` | 0.0013 | 0.0076 | 0.0011 | 0.0076 | k12-right, 63.601 mm / a12-forward, 56.099 mm |
| `left_service_outer_lower_cleat` | 0.0005 | 0.0035 | 0.0004 | 0.0035 | k12-right, 63.601 mm / k12-right, 89.849 mm |
| `left_service_outer_upper_cleat` | 0.0005 | 0.0036 | 0.0004 | 0.0036 | k12-right, 56.099 mm / k12-right, 39.599 mm |
| `lumber_leg_left` | 0.1530 | 0.1145 | 0.1530 | 0.1415 | a12-left, 1723.373 mm / a12-left, 34.408 mm |
| `lumber_leg_right` | 0.1613 | 0.1340 | 0.1613 | 0.1384 | k12-right, 1723.373 mm / k12-right, 34.408 mm |
| `top_center_left_cleat` | 0.0063 | 0.0690 | 0.0054 | 0.0690 | a1-rear, 63.601 mm / a12-rear, 72.599 mm |
| `top_center_right_cleat` | 0.0076 | 0.0797 | 0.0058 | 0.0797 | k12-rear, 56.099 mm / k12-rear, 56.099 mm |
| `top_outer_left_cleat` | 0.0449 | 0.1442 | 0.0433 | 0.1442 | a12-rear, 55.349 mm / a12-left, 47.101 mm |
| `top_outer_right_cleat` | 0.0509 | 0.1649 | 0.0490 | 0.1649 | k12-rear, 64.351 mm / k12-rear, 64.351 mm |
| `wj04_lower_full_stock_cleat` | 0.0016 | 0.0098 | 0.0015 | 0.0098 | a12-left, 63.601 mm / a12-left, 72.599 mm |
| `wj04_upper_g7_crosscut_full_stock_cleat` | 0.0010 | 0.0096 | 0.0008 | 0.0096 | a12-rear, 47.201 mm / a12-rear, 56.199 mm |
| `wj06_outer_lower_right_cleat` | 0.0052 | 0.0238 | 0.0048 | 0.0238 | a12-rear, 63.601 mm / a12-rear, 72.599 mm |
| `wj06_outer_upper_right_cleat` | 0.0043 | 0.0303 | 0.0040 | 0.0303 | a12-rear, 63.601 mm / a12-rear, 72.599 mm |

## Geometry applicability and open checks

160 prior exact section planes still match the current finished STEP bytes; 131 planes have a changed STEP binding and are explicitly non-applicable. Earlier three-case forces and accepted-state labels are never imported. Matching saved net sections retain their actual area, centroid, covariance and disconnected-ligament flag without assigning a common strain, invented resistance, or force division to disconnected regions.

The finite surface register supplies every cylinder/passages interval and outward planar face. Bore-free full rectangles and the source-bound full-depth rear-leg 1:12 recess are screened with their calculated width, depth and centroid. An intersecting bore or passage makes the rectangular stress screen non-applicable. Clipped end profiles retain their geometry and signed cuts, but have no stress ratio: the source lumped end loads do not define the local traction field through a section tending to zero area. The two corrected top blocks and two side hosts use only their hash-bound correction geometry; former bore slices on those bodies are not transferred.

The first saved runs in `member-screen-attempt01/` (top corners only) and `member-screen-attempt02/` (four joints) are preserved. They included mechanically inapplicable terminal-profile ratios; use the corrected child packet linked below for integration. Its changed applicability interpretation is explicit and does not change the frozen response or physical model.

The repeated historical 116221.6244 normal and 8.0384 shear indices were not global envelopes assigned to every case. Each row used its own distinct nominal-gap force array. The repeated controlling tip actions came from the common mapped dead load. For example, the right principal's slice at 0.001 mm had the same signed axial force, 0.624645 N, and bending couple Mu=24.5532 N·mm in all six cases, while the clipped depth was only 0.002031 mm. Dividing those finite point actions by the vanishing section produced the singular proxy. The corrected packet refuses those slices and retains their profiles and complete signed action arrays; it reports no member-resistance failure or capacity at them.

All sampled cuts of `center_post_cleat_left/right`, `center_principal_cleat_left/right` and `knee_outer_left/right_inner_frame_block` intersect saved bore footprints. Their bore-free columns are therefore N/A, with their six-case gross proxies, exact bore intervals and signed transfer/cut arrays retained. No intact-section result is transferred into these bored blocks.

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

- [member-results.json](member-screen-attempt02/profile-applicability-correction01/member-results.json): 264 member results, complete transfer wrenches and governing stress cuts, source/output hashes and claim limits.
- [member-results.csv](member-screen-attempt02/profile-applicability-correction01/member-results.csv): all six cases and 44 members in a compact integration table.
- [geometry.json](member-screen-attempt02/profile-applicability-correction01/geometry.json): actual bore/profile applicability, matching and refused saved section planes, source member/STEP bindings and point-action identities.
- [action-section-arrays.npz](member-screen-attempt02/profile-applicability-correction01/action-section-arrays.npz): signed point forces/free couples and both cut-half wrenches; units and indexing are in the result JSON.
- [inputs.json](member-screen-attempt02/profile-applicability-correction01/inputs.json) and [producer.py.snapshot](member-screen-attempt02/profile-applicability-correction01/producer.py.snapshot): frozen source bindings, force keys and executed producer.

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/member_screen.py \
  --clearance docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/top-and-service-frame-attempt02 \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/member-screen-attempt02/profile-applicability-correction01
```

The producer accepts `--clearance` (alias `--input-dir`) for a saved response directory and preserves an existing attempt. A changed calculation may use a new child under `member-screen-attempt01/` or `member-screen-attempt02/`. These small outputs remain active for parent integration. Earlier failed/frozen inputs and `/tmp` are preserved; no archive or prune operation is performed. Authority, other owners' files, staging and commits are outside this packet.
