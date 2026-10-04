# Ordinary washer fine reference

## Finite question and status

The completed own-end worksheet contains 1,006 finite ordinary end demands.
Of these, **994 have supported full annuli and declared profiles accepted by
the existing general annular plate method**: 850 quarter-inch washer ends,
48 retained Bolt Depot 15025 ends and 96 retained Bolt Depot 15023 ends.
Their fresh plate/contact and sampled steel comparisons are applicable work.

The parent completed `rawlocal/washer-ordinary-fine-reference/attempt01` with
three fine models and **958 finite loaded state calls**, plus **36 analytical
zero-demand references**. There were **zero numerical stops and zero
head-pressure load-path exclusions**. The worker authenticated all 356 source
pins and five artifacts, then checked the saved worksheet arithmetic without
importing or running the numerical producer. The parent owns the numerical
run and publication. All joint, formal-criterion, fabrication and
physical-release boundaries remain **HOLD**.

The twelve remaining finite ordinary rows use restricted central contact and
remain separate. Two additional G7 rows have unknown own moments and remain
null. The 48 common-knee rows are outside this ordinary run. Nothing here
changes the fresh top-side result: ten of its 48 sampled stress proxies exceed
the hypothetical 250 MPa comparator, as recorded in
[washer-top-side-fine-reference.md](washer-top-side-fine-reference.md).

## Returned parent comparisons

Status is
`FINITE_ORDINARY_WASHER_REFERENCES_WITH_HYPOTHETICAL_YIELD_EXCEEDANCES`.
All 994 references were returned, with 994 unique physical/case keys. The
quarter geometry stayed below both unchanged component comparators. The two
retained washer profiles produced **ten sampled Fy250 exceedances**. No
ordinary sampled wood peak exceeded its end's recorded conditional base
reference. These are declared-scenario component results, not physical test
failures, verified product ratings or complete adjusted joint resistance.

| Profile | Finite numerical / analytical zero | Steel >250 MPa | Wood/base >1 | Peak sampled steel | Steel/Fy250 | Peak wood/base |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Quarter | 814 / 36 | 0 | 0 | 158.9918437 MPa | 0.6359673749 | 0.3753652615 |
| Retained Bolt Depot 15025 | 48 / 0 | 6 | 0 | 407.3624226 MPa | 1.629449691 | 0.7622651713 |
| Retained Bolt Depot 15023 | 96 / 0 | 4 | 0 | 352.4042404 MPa | 1.409616962 | 0.6371229663 |
| Total | 958 / 36 | 10 | 0 | — | — | — |

| Same-state witness | Prescribed T / own M | Returned comparison |
| --- | --- | --- |
| Quarter steel: `a12-left`, `knee_outer_left_post_2`, head on `knee_outer_left_spine` | 98.20993502 N / 468.4590043 Nmm | 158.9918437 MPa |
| Quarter wood: `k12-rear`, `knee_outer_right_post_1`, head on `knee_outer_right_spine` | 142.5638868 N / 568.2026224 Nmm | 1.617532734 MPa / 4.309223308 MPa base = 0.3753652615 |
| Retained 15025 steel and wood: `k12-right`, `lumber_leg_bolt_right_2`, nut on `lumber_leg_right` | 887.6340026 N / 7770.079567 Nmm | 407.3624226 MPa steel; 3.284770843 MPa wood / 4.309223308 MPa base = 0.7622651713 |
| Retained 15023 steel and wood: `k12-right`, `rail_front_bolt_right_2`, nut on `base_floor_right` | 354.6639860 N / 2387.519136 Nmm | 352.4042404 MPa steel; 2.745505137 MPa wood / 4.309223308 MPa base = 0.6371229663 |

The six 15025 exceedances are both head and nut of `lumber_leg_bolt_left_2`
in `a12-forward` and `a12-left`, and both ends of `lumber_leg_bolt_right_2`
in `k12-right`. The forward pair is only about 1.01045 times the assumed yield;
the other four reach 392.123–407.362 MPa. The four 15023 exceedances are both
ends of `rail_front_bolt_left_2` in `a12-left` and `rail_front_bolt_right_2`
in `k12-right`, at 348.666–352.404 MPa. Rounding does not remove the reported
exceedances. These ten ordinary references remain distinct from the ten fresh
top-side exceedances in the separate matched side packet.

The maximum returned scaled gradient was 9.623181e-5 N, below 1e-4 N.
Maximum absolute contact-force residual was 9.623181e-5 N, below 0.001 N;
maximum absolute contact first-moment residual was 0.0004702531 Nmm, below
0.02 Nmm. The largest Newton count was 24, below the unchanged 100-step limit.
The largest absolute energy-identity residual was 5.877610e-11 Nmm. Thus the
reported exceedances are finite completed comparisons, not solver stops.
The 36 exact-zero rows retain null head pose and no uniqueness claim. All six
small positive-force states below 0.1 N received numerical calls.

| Profile | Recorded setup seconds | Recorded profile seconds |
| --- | ---: | ---: |
| Quarter | 0.03618 | 557.7102 |
| Retained 15025 | 0.03376 | 91.5192 |
| Retained 15023 | 0.03712 | 171.2990 |

The producer recorded **822.4870 seconds**, about 13 minutes 42 seconds,
including source handling and profile work, before final summary/receipt
serialization. Parent reported terminal exit 0. There was no retry, coupon,
law sweep, new coupling, CAD, shaft, frame or native run. Runtime used Python
3.12.3, NumPy 2.5.2 and SciPy 1.18.1.

| Completed artifact | SHA256 |
| --- | --- |
| `attempt01/receipt.json` | `a0afe7975411a2413d858ec816e315db768ddca7a7e88561a24fb133a347e386` |
| `attempt01/washer-ordinary-fine-reference.json` | `41762102f0193857cd1344d0efec321dd40f457d3430e2248c07b7ada453496b` |
| `attempt01/end-states.jsonl` | `5276fb712e8676759fb2217aa9f69a275fc60c644b77b5e79000f77e1a8d4944` |
| Consumed producer snapshot | `5501c39ca510f576a77f4ccb3256848f88aff2854263e06cba4fcfd44e469fcf` |

The original static preparation is preserved at
`rawlocal/washer-ordinary-fine-reference/preparation-5501c39c/receipt.json`,
SHA256 `3da2ca5fdb34b8812ce5f6be012b4d32ff0b5d2d4e5e677e9852e16d296c2baa`.
Its worksheet snapshot preserves the pre-run note; that receipt has not been
repinned to this returned-result annotation.

## Frozen input and necessary head-pressure certificate

Only the completed `rawlocal/washer-end-reference-join/attempt01` packet supplies
demands and support bindings. It preserves the same six simultaneous states,
fresh frame comparison `c3a8ff…`, response `62bd411…`, and signed own-seat
receiver moments. The source receipt authenticates its historical producer
snapshots without replacing those receipts.

| Frozen artifact | SHA256 |
| --- | --- |
| Source join receipt | `8f8b06d4a90b6c9462fb5f21fa398e42582a7d9be337c1fb327324b42d035783` |
| Source `washer-end-states.jsonl` | `b5e3160ec167ee9ef00cd7542a7701912ce43ab4db4673abbaa6291e8d0c717e` |
| Retained nominal support | `72ecad11051f7a72695f83561bb12503bfd79a44d3c3f6eeac2de476e3bc3448` |
| Reused fine48 consumer | `3905be16b88c55feadfad9145f7aaf896cf1dd16691bf982f467d7922919cb53` |
| Existing fine edge method | `ffe3db3e8c707851d44f0c60c43e6e6ef4aa4845f753dc6880c64186e3c75e61` |
| Existing flexure/material helper | `782ded96afd5e02e27873bd72b77073a643ed7c2a7946703a3240b1f51b21eac` |

For nonnegative head pressure on a circular annulus of outer radius `R`, the
pressure centroid lies within that circle. Therefore `T > 0` requires the
necessary condition `e = |M|/T <= R`. If `T = 0`, a compression-only pressure
field can transmit no moment. An `e > R` or zero-force/nonzero-moment source
would be recorded as a **head-pressure load-path limit**, with no arbitrary
solve or claim of physical hardware failure. Passing this necessary condition
does not establish compatible pressure, finite strength or adequacy at the
boundary `e = R`.

Only **exactly zero T and exactly zero M**, with exactly zero signed physical
force/moment vectors, receive an analytical zero-pressure/zero-stress reference.
No small positive force or small nonzero moment is rounded to zero. No unique
unloaded head translation or tilt is inferred. Existing source-vector checks
retain their tolerances; the head-radius comparison adds no tolerance or dial.

| Profile | Source states | Loaded calls | Exact-zero references | Head-pressure limits | Maximum e/R |
| --- | ---: | ---: | ---: | ---: | ---: |
| Quarter, K.L. Jack 25NWUS | 850 | 814 | 36 | 0 | 0.9918370783 |
| Retained Bolt Depot 15025 | 48 | 48 | 0 | 0 | 0.9783324426 |
| Retained Bolt Depot 15023 | 96 | 96 | 0 | 0 | 0.9916703392 |
| Total | 994 | 958 | 36 | 0 | — |

The quarter maximum is `k12-rear`, bottom-right `rail_2`, nut on
`base_rail_bottom_right`: T = 0.5822243251 N, M = 2.887358367 Nmm and
e = 4.959185391 mm against the declared 5 mm pressing radius. The minimum
positive quarter T is 0.06009257613 N; it remains a loaded calculation.

The retained 15025 maximum is `a1-rear`, `lumber_leg_bolt_left_2`, nut on
`lumber_leg_left`: T = 83.93393230 N, M = 767.5480294 Nmm and
e = 9.144669007 mm against 9.3472 mm. The retained 15023 maximum is
`a12-rear`, `rail_rear_bolt_right_2`, head on `base_floor_right`:
T = 1.589831799 N, M = 11.03249712 Nmm and e = 6.939411533 mm against
6.9977 mm. These are same-state witnesses, not independently combined peaks.

| Quarter case | Loaded calls | Exact-zero references |
| --- | ---: | ---: |
| `a1-rear` | 136 | 6 |
| `a12-forward` | 138 | 4 |
| `a12-left` | 134 | 6 |
| `a12-rear` | 136 | 6 |
| `k12-rear` | 134 | 8 |
| `k12-right` | 136 | 6 |

Each case adds eight 15025 and sixteen 15023 loaded end calls.

## Explicit profile bindings and unchanged physics

The general helper `make_model(module, 'fine')` reads numerical radii and
thickness from `module.FAMILIES['rail']`. Its annular assembly is parameterized;
the older fixed `load_source()` is a source wrapper for one historical state,
not a restriction on these new parameter instances. The producer bypasses
that loader and supplies each source and profile explicitly. It reuses the
frozen fine48 source-loading functions and the unchanged edge solver.

| Binding | Inner radius | Outer radius | Head/nut radius | Thickness | Nominal lands |
| --- | ---: | ---: | ---: | ---: | ---: |
| Existing quarter geometry | 4.1529 mm | 9.2329 mm | 5.0 mm | 1.2954 mm | 142 |
| New declared 15025 parameter instance | 7.3279 mm | 17.3736 mm | 9.3472 mm | 2.1844 mm | 8 |
| New declared 15023 parameter instance | 5.7531 mm | 12.6111 mm | 6.9977 mm | 1.6256 mm | 16 |

Every instance satisfies `0 < inner_radius < head_radius < outer_radius` and
positive thickness. The washer dimensions use catalog maximum ID, minimum OD
and minimum thickness. The wood annuli and head pressing annuli match the
recorded source contact domains exactly. Circular pressing radii remain
hypotheses; catalog hex widths do not qualify delivered bearing footprints.

The 850 quarter states have full nominal support: 802 saved matched states
and 48 newly matched states. Their K.L. Jack dimensional envelope matches the
older Bolt Depot 2994 helper envelope. This supports geometry/method reuse and
does not transfer steel grade, yield or rated capacity. The 144 retained
states bind the existing 24 supported nominal lands in the pinned retained
support packet. Lack of an earlier saved plate family was a configuration gap,
not an annular-method domain exclusion. The parent has now completed their
144 fresh calculations using those explicit parameter bindings.

All three profiles retain E = 200,000 MPa, nu = 0.3, hypothetical Fy = 250 MPa,
Kwood = 20 MPa/mm and Khead = 10,000 MPa/mm. Catalog material descriptions do
not establish numeric Fy. No material rating is transferred. The wood
comparison retains **each end's recorded conditional base reference and grain
route**: perpendicular or parallel to grain as recorded, rather than replacing
every ordinary end with the 625 psi perpendicular reference.

## Parent API, scope and timing

Producer: [washer-ordinary-fine-reference.py](washer-ordinary-fine-reference.py).
Import is inert; API is `build(output: Path)`. Numerical imports, model assembly
and state calculations occur only inside the parent-owned build.

```sh
uv run --no-sync python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/washer-ordinary-fine-reference.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/washer-ordinary-fine-reference/attempt01
```

The recorded parent command used the now-completed `attempt01` child. A build
requires a fresh unaliased immediate child of that raw folder and preserves
existing packets. The completed run made three sequential model assemblies
and 958 state calls, with only one assembled profile retained at a time. There is no worker
execution, test, coupon, retry, law sweep, convergence sweep, CAD query, shaft,
frame or native solve. The twelve central contact recipes are not extended.

The fixed fine recipe has four radial elements inside the head band, twelve
outside, Fourier order eight, 128 angular stations and 1,142 unknowns. The
existing 100-step Newton and 50-backtrack Armijo limits, gradient tolerance
1e-4 N, force tolerance 0.001 N and first-moment tolerance 0.02 Nmm remain
unchanged. A numerical stop retains its last accepted diagnostics and is not
retried or treated as a physical failure.

No measured elapsed time was recorded by the earlier fine48 producer. The
pre-run work-count estimate was 958/48 = 19.96 times its loaded-call work,
plus the change from one to three model assemblies. That estimate was not a
promised wall time. This producer now records the actual per-state and
per-profile seconds summarized above. Source snapshots and the input plan
were written before setup, and every completed end was flushed to JSONL.

## Signed loads, returned comparisons and limits

Each source keeps its physical key, inward normal, own-seat datum, signed
receiver force and signed own moment. For nonzero M and normal n, the local
pressure-offset direction is `x = (n cross M)/|M|`; the recorded mapping
verifies `|M|*(x cross n) = M`. The circular scalar drive uses that same end's
moment magnitude. Saved rigid closure and tilt initialize Newton only. No
receiver-datum lever or another end's peak is substituted.

`input-plan.json` retains the 994 sources, three explicit bindings, head
certificates and the fourteen separate central/null rows.
`end-states.jsonl` retains each returned fine state, stress and wood-pressure
witness, residual/iteration diagnostics or numerical stop. Exact-zero rows
retain analytical comparison values with null pose and no numerical call.
The summary reports same-state stress/base-reference peaks and explicit
Fy250 exceedance keys; its receipt authenticates all consumed source and output
bytes before and after execution.

The approximation retains unilateral normal contact and weak free radial
edges. Its sampled face-bending/midplane-shear proxy omits contact sigmaZZ,
three-dimensional edges, plasticity, friction, preload and geometric
nonlinearity. Nominal full support does not qualify support after loaded
motion. Actual washer thickness, pressing geometry, steel yield, timber and
seat stiffness remain unverified. Washer response is not fed back into shaft,
group or frame equilibrium, and the timber reference is not complete adjusted
joint resistance.

The twelve central ordinary rows have restricted wood/head contact radii
4.1529–5 mm and do not use this full-wood-annulus recipe. Six nut rows retain
their existing compression-only static trials; six other ends remain outside
the direct recipe. The two `a12-left` G7 ends retain unknown M after the local
150-iteration stop. Their zero source tie is not an analytical zero wrench.
The 48 common-knee rows remain unchanged in their separate packet.

This finite ordinary washer question is complete: all 994 applicable
references returned with no method stop. The quarter profile satisfies these
declared component comparisons; both retained profiles contradict the
hypothetical Fy250 steel comparison in the recorded states. Actual steel
properties and delivered geometry remain unknown, and complete joint
qualification remains separate. The parent is integrating these results with
the top-side washer exceedances and its remaining permanent-bearing work.
This packet does not select new hardware, alter reviewed geometry or establish
a complete joint capacity. No optional expansion or further run is requested.
