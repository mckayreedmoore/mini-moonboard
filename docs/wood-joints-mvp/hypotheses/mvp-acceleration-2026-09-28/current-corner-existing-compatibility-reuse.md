# Existing conditional compatibility inputs for the current left corner

**Status:** source-bound reuse map for the six new left-corner bolt axes only.
This supplies conditional stiffness ingredients, not signed demand, resistance,
joint acceptance, or a full-frame result.

The maintained reduced-property and assembly code already implements one
conditional axial outer-seat tie for each physical through-bolt. Thus an
unqualified blanket statement that the current model has no bolt axial law is
stale. The older preparation note is still correct when scoped to the cited
Swedish Wood service-slip table: that table does not supply the axial washer
law. The implementation below is a model scenario, not a tested product law.
The Hillman screws still have no supported physical axial law; their cycle-11
ratio-one spring remains a non-qualifying diagnostic.

## Reusable six-axis coefficients

The frozen cycle-11 trial stores one lateral spring group per wood/wood shear
plane and one axial tie per physical bolt. Values below are read from its
saved spring rows; stiffnesses are N/mm. `Kser` is per bolt per shear plane.
The C11 freeze declares a zero-clearance diagnostic, so its lateral rows use
`bolt_gap_factor = 0`.

| Group / axis IDs | Modeled receivers and lateral planes | Lateral `Kser` | One outer-seat axial tie per bolt |
| --- | --- | ---: | ---: |
| BG001 `knee_outer_left_post_1/2` | `knee_outer_left_spine` ↔ `base_post_outer_left`; 1 plane each | 3,086.746 each | 4,670.054 each |
| BG003 `knee_outer_left_side_1/2` | `knee_outer_left_spine` ↔ `base_side_left` ↔ `knee_outer_left_inner_frame_block`; 2 planes per bolt | 3,086.746 per plane | 4,234.008 each |
| BG045 `knee_outer_left_inner_header_1/2` | `base_header` ↔ `knee_outer_left_inner_frame_block`; 1 plane each | 3,086.746 each | 3,207.383 each |

The source axis diameter is 6.35 mm throughout. Modeled wood grip is 76.2 mm
(BG001), 215.9 mm (BG003), and 177.1 mm (BG045). The lateral coefficient is
the implemented EC5 service-slip comparison
`Kser = ρmean^1.5 D / 23`, with `ρmean = 500 kg/m³`; its declared density
sensitivity is 400/500/600 kg/m³. These are elastic comparison coefficients,
not bearing strengths. For these six axes, the 22 saved spring records
comprise 8 lateral planes × 2 DOFs plus 6 axial ties; BG003's two planes remain
associated with one physical bolt axis.

The axial property producer uses the series-compliance scenario

```text
k_axial = 1 / (Lsteel/(Esteel Asteel) + h/(Eseat1 Awasher) + h/(Eseat2 Awasher))
```

where `Asteel = πD²/4` is smooth gross-shaft area, `Lsteel` is wood grip plus
two modeled washer thicknesses, and each outer washer-seat wood column uses
its orthotropic effective modulus along the bolt axis. Baseline steel
`E = 200,000 MPa` (declared perturbations 190,000/210,000 MPa); baseline
column depth `h` is the equivalent washer diameter derived from modeled
washer annular area, with depth factors 0.5/1/2 in sensitivity. No sensitivity
range is inferred here from the baseline rows.

For cycle-11's ring-case-A material assignment, the pinned conditional tensor
is `EL/ER/ET = 11,032/750.176/551.6 MPa`,
`GLR/GLT/GRT = 706.048/860.496/77.224 MPa`, and
`νLR/νLT/νRT = 0.292/0.449/0.390`. It is the documented Douglas-fir elastic
diagnostic, not measured stock. The axis-specific baseline seat moduli used by
the axial law are:

| Axes | First / second modeled outer-seat receivers | Ring-A `Eaxis` at the seats |
| --- | --- | ---: |
| BG001 `post_1/2` | spine / outer post | 750.176 / 750.149593 MPa |
| BG003 `side_1/2` | spine / inner-frame block | 750.176 / 750.176 MPa |
| BG045 `inner_header_1/2` | header / inner-frame block | 273.512 / 11,032 MPa |

For BG045, the header-axis modulus is the orthotropic response for its modeled
`+Z` bolt axis, with ring-A components approximately `R = 0.766`, `T = 0.643`;
the inner block axis is its proposed `+Z` grain. The reversed second axis
changes vector sign, not that modulus. Grain, R/T assignment, species, grade,
moisture, and the elastic constants remain unobserved scenarios.

## What this connection model does and does not connect

For each BG003 bolt, the saved model has two independent lateral plane
connectors, one from spine to `base_side_left` and one from `base_side_left`
to the inner block. It has exactly one axial tie between the two outer washer
seats on spine and inner block; it does not add an axial tie to the middle
member. This is the correct count for the current physical-axis abstraction,
and avoids treating the two shear planes as two bolts. It does **not** make a
continuous deformable bolt element across the stack: there is no bolt bending
or flexure law, nor a coupled three-body lateral action law. The plane springs
remain independent and cannot by themselves produce the actual signed split
between the outer members and middle member.

The tie is flagged tension-only and initially inactive in the source property
record. The active/inactive trial uses linear spring branches; metadata alone
does not make a spring constitutively one-sided. The prescribed sign and
contact checks must close before its action can be interpreted. The frozen
cycle-11 input therefore provides stiffness properties only; its force results
are excluded here because that sign branch did not close.

The coefficient set can be reused as an explicitly conditional input when
assembling the BG001 → BG003 → BG045 corner compatibility record. It cannot
select tie force, axial/contact sharing, active seats, or interface demands.
Still missing for that record are the same-case signed actions and compatibility
through all three groups, including BG003's per-bolt two-plane action vectors
and middle-member reaction; verified member order and installed contact;
delivered bolt/thread/root/grade and washer dimensions; and a supported or
calibrated washer-seat compliance/contact law. The CAD hardware roles, smooth
shaft area, zero preload, no-spread wood columns, and modeled washer geometry
remain assumptions. Do not reuse cycle-11 connection forces or infer an
acceptance result from these coefficients.

## Source pins

- [Cycle-11 saved model](reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/model.json), SHA-256 `d3417111926c982a07ced393aa1c12f815aa87b5b8eb851b45bc63a1ea10fac0`; [freeze manifest](reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/freeze.json), SHA-256 `1633e79900afd194ece79c7463a7b383a11bb96920e7449e6a25c528e933b8e2`. Its scope says zero-clearance active-set cycle 11, no joint acceptance.
- [Property producer](../../../../fea/wood_joint_reduced_properties.py), SHA-256 `26b6e8bf8800208bfb867439694afa705558ac63ca338778e9210e940a55d9a1`; [reduced assembly](../../../../fea/wood_joint_reduced_model.py), SHA-256 `f94b1161b984b7599f6c8d4a131ad49a3f12a0033ec6a0b6b5892a5b9d45e2f7`; [connector kinematics](../../../../fea/wood_joint_reduced_connections.py), SHA-256 `76c4043f78dd22ff22c57606a1ef275e1fa851dc259bcd3a33b4c1c3557a7196`.
- [Frozen reduced model inputs](reduced-static-attempt01/model-inputs.json), SHA-256 `178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9`; [member geometry](reduced-static-attempt01/member-geometry.json), SHA-256 `121f1940d0180367f953a1f92443964ded901ca775536750a9b028e37d6c8187`.
- [Frame material map](../evaluation-resume-2026-09-24/current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json), SHA-256 `f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409`; [block material map](../evaluation-resume-2026-09-24/current-block-material-frame-map-attempt02/material-frame-map.json), SHA-256 `8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480`; [material scenario](../../current-material-scenarios.md) and [orthotropic tensor basis](../../orthotropic-material-scenario.md).
- [Current fastener-axis register](../evaluation-resume-2026-09-24/current-hardware-material-cost-closeout-attempt01/fastener-axis-register.json), SHA-256 `c1e53e9a08599d13a992fc11a493853c1695f697f3fe99b45af20795c430240a`.
- The earlier wording is in [reduced-static preparation attempt01](reduced-static-attempt01/README.md), under “Reuse decisions.” It distinguishes the cited service-slip table from the rest of the implemented law and should not be read as saying that no conditional bolt axial tie exists.
