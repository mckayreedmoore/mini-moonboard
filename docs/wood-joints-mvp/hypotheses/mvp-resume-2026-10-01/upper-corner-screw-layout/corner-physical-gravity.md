# Bottom corner gravity: physical sub-cut applicability

## Engineering question

The [completed normal census and finite-pressure assessment](corner-split-closure.md)
found only two positive tensile lower-bound rows: bottom left / K12-rear and
bottom right / A12-rear, both on `u`-normal cuts. Their respective maxima are
0.007744996 and 0.165250430 N. Those recorded results remain preserved.

The source maps weight through MPC-expanded equivalent node forces. Some
individual node forces point upward or sideways although their complete
gravity resultant and moment are correct. Correct whole-body balance does
not establish that applying those equivalent forces as physical point loads
on arbitrary sub-cuts reproduces the physical body-force distribution.

This finite calculation asks whether the two positive rows persist with
uniform gravity on the **actual retained bottom timber**, plus the original
unexpanded allocated hardware receiver point forces/free couples. It preserves
the complete group gravity wrench, existing dead-load factor, bore-wall,
washer and contact actions. There is no new bolt force, preload, hardware
capacity, frame response or geometry change.

The owner requested extending the assessment to the remaining 20 cleats
after this current analysis. That extension is deferred until the gravity
sub-cut applicability question is settled, so an unsupported equivalent-node
interpretation is not copied to additional bodies.

## Source and input boundary

Use the frozen four-corner attempt03 cut inventory and bottom first-order
states already authenticated by the prior packet. Unexpanded member and
hardware gravity come from `gravity_load_audits.member_self_weight_rows` and
`gravity_load_audits.hardware_receiver_point_loads` in the source adapter
model, SHA `61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8`.

Source mass rows come from `current-mass-centroids-attempt01/mass-centroids.json`,
SHA `4c107b76d42d2a6f49b81c4857ba20bb236920932a7c34392c63e70d0882099a`.
The bottom source selfweight is approximately 0.558182586 kg per cleat with
a recorded density of 600 kg/m³. The producer requires the saved mass,
actual retained volume and centroid to match before using uniform body force.
It does not normalize a contradictory geometry or invent a balancing couple.

The current corrected top frame has additional wood-mass/wrench rows in
`operators-attempt02/model.json`, SHA
`b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626`.
Its `wood_mass_changes` must be combined with the older source selfweight
when reporting top applicability. The producer records that current combined
timber wrench and compares a same-mass uniform field on corrected geometry.
No top replacement is adopted; the older adapter alone is not the current
top weight authority. Existing top results remain within their recorded
mapping assumptions.

Normal-force and finite-pressure arithmetic reuse the prior executed snapshot
SHA `e090270a3bea195800ed3b04b806fe4ea0c5e221ae57faf01f602c8dba769d5e`.
Its original sources and outputs remain unchanged.

## Exact volume and load replacement

The bottom finished shape is a rectangular blank minus four disjoint full
transverse cylinders. For a half cut along a shaft, clipping simply shortens
that cylinder. For a cut across its circular cross-section, use the exact
circle-segment area and first moment. For radius `r` and center-relative
cut coordinate `t`, with `-r < t < r`:

```text
A(t) = r² (asin(t/r) + pi/2) + t sqrt(r²-t²)
first moment along cut coordinate = -2/3 (r²-t²)^(3/2)
```

Subtract each cylinder's clipped volume and first moments from the clipped
blank. A uniform local body-force density `b` on that retained volume gives
force `V*b` and moment `cross(first_moment - cut_datum*V, b)`. Full volume,
centroid and source density are checked before any result is written.

Allocated hardware remains the original 12 receiver point wrenches per bottom
cleat, including their recorded free couples exactly once. This is the saved
hardware-transfer approximation, not a newly qualified distribution on bolt
or washer surfaces. It is distinct from the mechanical washer/bore reactions
already in the source cuts. Their source load ownership remains unchanged.

For each saved cut, let `Gmapped` and `Gphysical` be the negative-half external
gravity wrenches at the same cut datum. The internal force convention gives:

```text
new_internal = old_internal + Gmapped - Gphysical
```

All six components are retained. Whole physical and mapped gravity forces and
moments must agree in all twelve bottom block/case states. There is no second
weight addition. The original nodal cut convention and 1e-6 mm event tolerance
are preserved when classifying hardware and mapped point loads.

Four analytical geometry checks cover full volume/first moments, shortened
cylinders, a half-circle segment and an empty half. No software tests, CAD
generation, frame solve or native mechanics run is introduced.

## Coverage and claim limits

Save updated full six-component wrenches for every original bottom grain,
`u`-normal and `v`-normal cut. Reevaluate the normal tensile lower bound and
finite compression construction only for the transverse cuts. Store named
updates to both original positive peak witnesses. The old grain-normal
resistance comparisons are not transferred silently to changed local cuts.

This phase compares the original finite stations. It does not create missing
hardware-point events, prove continuous maxima, solve a compatible stress
field, qualify crack shear/torque transfer or assign a splitting capacity.
Current loads, geometry and full gravity wrench remain fixed. Complete-joint,
formal, fabrication and physical-release flags remain false.

## Preserved attempt01 execution

Executed producer snapshot SHA-256:
`de799b64718365f496295d4e836cc4342ba290b8fb81c3d438bd223ae456b7fc`.
Formatting and lint passed. Parent executes from the repository root:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/corner-physical-gravity.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/corner-physical-gravity/attempt01
```

API: `build(output)`. Fresh output is required. The producer saves its executed
snapshot, ignored cut export, checks and source/output receipt.

## Completed physical-gravity comparison

Parent executed `attempt01` successfully with the producer digest above. The
four volume/first-moment analytical checks passed. Independent authentication
confirmed all 62 source entries and four outputs recorded in its receipt.

| Result | Recorded value |
|---|---:|
| Updated bottom cut limits, retaining all six components | 50,604 |
| Transverse cut limits assessed | 25,792 |
| Finite compression witnesses | 25,692 |
| Positive necessary normal-tension cut limits | 100 |
| Maximum necessary normal tensile lower bound | 0.054537792 N |
| Maximum constructed finite compression pressure | 0.103937193 MPa |
| Maximum whole-gravity force difference | 1.735e-17 N |
| Maximum whole-gravity moment difference | 7.487e-8 N·mm |

All 100 positive limits belong to bottom right / A12-rear / `u`-normal cuts.
The former bottom-left peak now has a compression-only finite witness;
its necessary tensile lower bound is zero. At the former bottom-right
1 mm peak, the revised lower bound is 0.053568161 N. The new maximum occurs
at `u=1.252397256527047 mm`, before the event, with signed internal wrench:

```text
[N, Vp, Vq, T, Mp, Mq] =
[-2.639141681, -2.290576589, 0.794998442,
 89.176155067, -112.776975093, 122.158257464]  (N, N·mm)
```

This 0.054537792 N is the minimum normal tensile resultant for the
unbounded-pressure support-hull idealization. It is neither an actual bolt
force nor a quantified reserve in the existing bolts. Fixed real tie locations,
finite bearing areas and simultaneous shear/torque can require a different
transfer. Splitting capacity remains null and complete-joint acceptance false.

The largest finite pressure witness occurs at bottom left / A1-rear /
`u=-43.197602743473 mm`, before. It retains the simultaneous shears and
torque and is below the existing 4.309223308 MPa perpendicular-compression
reference. This is a finite normal equilibrium construction; its compatibility
and local crack transfer are not established by that comparison.

Both bottom retained volumes are approximately 930,304.310269 mm³. Their
inferred densities match the recorded 600 kg/m³, and retained centroids match
the original physical selfweight source within the required tolerance. No
whole-body gravity force or moment was intentionally changed.

For each top block, the audit includes the current corrected-frame delta:
0.558182586 kg original timber plus 0.266317415 kg added timber, totaling
0.824500001 kg. Spreading that same mass uniformly over corrected geometry
would change the recorded global x moment by approximately 14.89497243 N·mm.
Consequently, no top uniform-gravity replacement is adopted. The current
delta is accounted for; the older adapter is not treated as the full current
top mass source.

Frozen output authentication:

| `rawlocal/corner-physical-gravity/attempt01/` output | SHA-256 |
|---|---|
| `checks.json` | `190bd9d5485cd3e1643e1302904a70d340fdef7c3d6dc66740c0ccae9704994b` |
| `cuts.jsonl.gz` | `be324b7659a6b51e5f27ed8842685808e8f300c0f2ab4b6199427ff2aa35cec2` |
| `producer.py.snapshot` | `de799b64718365f496295d4e836cc4342ba290b8fb81c3d438bd223ae456b7fc` |
| `receipt.json` | `914c7532818ad4d8c33c1b968f3797692c8d12911be4409303d70843eda9c122` |

The original 0.165250430 N finding remains preserved for its frozen mapped-node
inputs. The physical-gravity comparison narrows the remaining normal tensile
diagnostic; it does not close splitting or qualify all 24 cleats.

## Final bottom longitudinal comparison follow-up

The current producer additionally recomputes the existing nominal grain-normal
comparisons on every changed full grain cut. It uses authenticated
`corner-timber-sections.section`, `corner-net-section.nominal_section` and
each bottom body's original member-screen `CF_only_reference_mpa` values.
The original affine longitudinal strain, area-based shear sharing and common
regional twist hypotheses remain explicit. It records tension, compression,
bending, the existing axial-plus-bending reference sum, and simultaneous
regional shear/torsion. No new interaction law or transverse capacity is added.

Prepared follow-up producer SHA-256:
`7666448f5f841d9a6d8a5cccededbb8047ec75df7463a4dd7c4a27a47693cf94`.
Formatting and lint passed. Parent executes the same API to a fresh child:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/corner-physical-gravity.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/corner-physical-gravity/grain-attempt02
```

Parent executed `grain-attempt02` successfully with that frozen source.
Independent authentication confirmed 62 source entries and four outputs.
The 24,812 changed grain-normal cut limits cover both bottom bodies and all
six cases, giving 12 body/case states. Results use the original conditional
references and the same declared nominal sharing hypotheses:

| Recomputed nominal comparison | Maximum ratio |
|---|---:|
| Longitudinal tension / Ft | 0.023747361 |
| Longitudinal compression / Fc | 0.009636046 |
| Bending / Fb | 0.013126440 |
| Existing axial-plus-bending reference sum | 0.016330288 |
| Simultaneous regional shear/torsion / Fv | 0.088243297 |

All five maxima occur on bottom left / A1-rear. Shear/torsion governs at
grain station 43.350000014358734 mm, before; the other maxima occur at
59.84999998591819 mm, compression before and the others after. The complete
signed witness wrenches and regional fields are preserved in the output.
All computed nominal comparisons remain below their existing references.
The reference sum is a recorded diagnostic, not a newly adopted interaction
law or buckling qualification.

Both bodies retain `Ft=5.946728165`, `Fc=10.704110698`, `Fb=9.307922346` and
`Fv=1.241056313 MPa`. These are the source's conditional CF-only references,
not newly established capacities. The 0.054537792 N necessary transverse
tensile lower bound remains unchanged. No splitting capacity or complete-joint
acceptance is assigned.

| `rawlocal/corner-physical-gravity/grain-attempt02/` output | SHA-256 |
|---|---|
| `checks.json` | `e11c2c469c6ef8a8582f5117231d72cfa148c0780de2e5e0ef9fb8365c2492db` |
| `cuts.jsonl.gz` | `2dd0b988977d1ac726af41b26e8ac5793347b528125931da8838469233319f25` |
| `producer.py.snapshot` | `7666448f5f841d9a6d8a5cccededbb8047ec75df7463a4dd7c4a27a47693cf94` |
| `receipt.json` | `9f89a14231101cf4c09dd7ae6adc431b43b6f8f39fd90ad049e1ad3aaeba3b68` |

This completes the bounded bottom physical-gravity and longitudinal comparison
follow-up. The original attempt01 and prior mapped-gravity packets remain
unchanged. Transverse local cracking and the recorded spatial-transfer
limitations remain unresolved.

## Remaining 20 cleats: source applicability census

After the completed replay, the source census identifies all 20 remaining
registered connector bodies. Together with the four outer corners, their IDs
match the 24-body joint register exactly; the two knee spines are registered
connector bodies. The three existing packets and their combined 31 source
entries, including those packets themselves, were authenticated. No new
mechanics, CAD, load reconstruction or resistance calculation was run.

| Existing saved packet | Bodies | Completed grain-normal traces | Checks SHA-256 |
|---|---:|---:|---|
| `rawlocal/header-cleat-net-sections/attempt01` | 6 | 1,968 | `b70fd818654a4d6509186a2718a81fa0b564cfc7ad808be52946f0eddfead1a2` |
| `rawlocal/knee-spine-net-sections/attempt02` | 2 | 600 | `6b6c8df94f1ccab859ee980dd1835ba19286718f44e8a36ce6b9d0014064fc85` |
| `rawlocal/remaining-net-sections/attempt01` | 12 | 2,304 | `80600628f956f5a957efca382d2c4e2ca9110cefbff8c7aee21a1995a430892f` |

Those saved nominal results remain within their original working hypotheses.
None supplies full transverse `u`- or `v`-normal cut coverage or an accepted
splitting capacity. The corner hull and pressure results do not transfer to
these bodies.

| Registered body or mirrored pair | Grain length (mm) | Width × depth (mm) | Bore topology |
|---|---:|---|---|
| `center_post_cleat_left`, `center_post_cleat_right` | 128.9 | 88.9 × 88.9 | Two transverse, two longitudinal |
| `center_principal_cleat_left`, `center_principal_cleat_right` | 134.7 | 83.9 × 139.7 | Two transverse, two longitudinal |
| `knee_outer_left_inner_frame_block`, `knee_outer_right_inner_frame_block` | 139.0 | 88.9 × 133.35 | Two transverse, two longitudinal |
| `knee_outer_left_spine`, `knee_outer_right_spine` | 276.3 | 38.1 × 139.7 | Four transverse |
| `bottom_center_left_cleat`, `bottom_center_right_cleat` | 119.7 | 88.9 × 88.9 | Four transverse |
| `top_center_left_cleat`, `top_center_right_cleat` | 119.7 | 88.9 × 88.9 | Four transverse |
| `left_service_inner_lower_cleat`, `left_service_inner_upper_cleat` | 119.7 | 88.9 × 88.9 | Four transverse |
| `left_service_outer_lower_cleat`, `left_service_outer_upper_cleat` | 119.7 | 88.9 × 88.9 | Four transverse |
| `wj04_lower_full_stock_cleat` | 119.7 | 88.9 × 88.9 | Four transverse |
| `wj04_upper_g7_crosscut_full_stock_cleat` | 86.9 | 88.9 × 88.9 | Four transverse |
| `wj06_outer_lower_right_cleat`, `wj06_outer_upper_right_cleat` | 119.7 | 88.9 × 88.9 | Four transverse |

The six header/inner-knee bodies and two spines have global +Z grain axes.
The twelve remaining bodies have their individual rotated grain frames in
the saved member geometry; assuming +Z for them would be incorrect. The six
header bodies' longitudinal holes also require geometry handling beyond the
current four-transverse-cylinder corner helper. Their existing grain-plane
subset method does not establish transverse cut geometry or an end-bridge
pressure witness.

For every one of the 20 bodies:

- All six current cases have saved point-force/free-couple arrays with six
  signed components, source row IDs and application coordinates. The case IDs
  are A12-rear, A12-forward, A12-left, K12-right, K12-rear and A1-rear.
- The original unexpanded selfweight row, physical source centroid, mass and
  600 kg/m³ density exist. Every body has twelve allocated hardware receiver
  point wrenches, with their original free couples.
- No body appears in the current corrected model's `wood_mass_changes`.
  This distinguishes them from the corrected top outer corners; it does not
  itself validate a uniform-gravity sub-cut replacement.
- The action roles include lateral bolt transfer, outer-seat bolt tension,
  timber/panel contact and discrete body loads. Equivalent gravity must be
  replaced, not added a second time, in any physical sub-cut comparison.
- Contact geometry exists with vertices and boundaries: two contact patches
  and eight operator contact rows per body, except each spine has four patches
  and sixteen rows. Those are source coverage counts, not a recovered physical
  pressure distribution.

The reusable source inventory is:

| Source | Path from repository root | SHA-256 |
|---|---|---|
| Six-component action archive | `docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/member-screen-attempt02/four-screw-layout01/action-section-arrays.npz` | `ddfa310266661ea5ba6e188d2bf473121d99158d50921c84760744519e2a7caf` |
| Body frames and descriptors | `docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/member-screen-attempt02/four-screw-layout01/geometry.json` | `c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af` |
| Case metadata and original references | `docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/member-screen-attempt02/four-screw-layout01/member-results.json` | `54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5` |
| Physical selfweight and allocated hardware wrenches | `docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-frame-input-adapter-attempt01/a12-rear/model.json` | `61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8` |
| Source mass, density and centroid | `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-mass-centroids-attempt01/mass-centroids.json` | `4c107b76d42d2a6f49b81c4857ba20bb236920932a7c34392c63e70d0882099a` |
| Current corrected mass changes | `docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/operators-attempt02/model.json` | `b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626` |
| Contact patch boundaries | `docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01/contact-geometry.json` | `034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151` |
| Current row ownership | `docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/operators-attempt02/row-identities.json` | `cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27` |
| Exact 24-body registration | `docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-register/attempt01/register.json` | `79db8c6830dee42e47dcdcd75c331ce22a67cd3d27e38f9a8b616e820c37d3ca` |
| Finished hole/surface geometry | `docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/surfaces.json` | `33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb` |

For an extension, grain-only archived contact footprints cannot be treated as
transverse footprints. Source rows must be joined to their actual contact
patch geometry, and body-specific bolt/washer/bore transfers must remain
distinct from those gravity wrenches. Uniform retained-volume first moments,
complete gravity-wrench agreement and new transverse section geometry have
not been evaluated for these 20 bodies in this census.

The source inventory and prior grain checks are therefore available without
another global frame solve. The source applicability census is complete;
transverse splitting assessment and complete-cleat acceptance are not.
