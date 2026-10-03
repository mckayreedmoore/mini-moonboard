# Fresh top-side washer fine reference

## Finite question and status

The actual top-side washer rings and their 48 own-end demands are now bound.
The existing sparse fine plate method can represent their declared circular
profile. Fresh washer flexure and steel comparisons were applicable work
requiring execution, rather than a supported domain exclusion.

The parent completed `rawlocal/washer-top-side-fine-reference/attempt01`:
one existing fine model, 48 completed same-state end calls and zero numerical
stops, with no coupon, retry, convergence sweep or new profile. The worker
authenticated 256 source pins and five output artifacts without importing a
numerical solver or executing the producer. All
joint, fabrication, physical release and formal-criterion flags stay unchanged.

## Returned parent comparisons

Status is `FINITE_SIDE_WASHER_REFERENCES_WITH_HYPOTHETICAL_YIELD_EXCEEDANCES`.
Ten of 48 sampled stress proxies exceed the unchanged hypothetical 250 MPa
yield comparator. This is a failed component comparison under the declared
scenario, not a physical test failure or a verified Hillman/bolt/washer rating.

| Returned peak | Same-state result |
| --- | --- |
| Sampled washer stress proxy | 339.3251729 MPa; ratio 1.357300692 to hypothetical 250 MPa yield |
| Sampled wood-pressure/base ratio | 0.9837306641 |
| Physical witness for both peaks | `k12-right`, right top `side_2`, nut on `top_outer_right_cleat` |
| Simultaneous prescribed demand there | T = 508.9271523 N; own M = 2539.363827 Nmm |

The ten exceedances are head and nut ends of left top `side_2` in
`a12-forward`, `a12-left` and `a12-rear`, plus right top `side_2` in
`k12-rear` and `k12-right`. The earlier 0.3876062484 mean wood-pressure ratio
remains valid as a mean reference; it did not predict the plate/contact peak or
prove washer steel adequacy. Actual steel grade, thickness, head/nut profile
and coupled feedback remain unqualified.

| Completed artifact | SHA256 |
| --- | --- |
| `attempt01/receipt.json` | `c72bd446d28bb92e540a6f74a02b4d39acba1b69d32304ba89623fdbeb093057` |
| `attempt01/washer-top-side-fine-reference.json` | `5426aef730f1ebf7a09dce013a19e6b4310703927e18fe0a7c6b673d41fc644e` |
| `attempt01/end-states.jsonl` | `7552d3e974ce3fc232c4b7ce0303ebaf61f4676f784aae77eedfae0427097982` |
| Consumed producer snapshot | `3905be16b88c55feadfad9145f7aaf896cf1dd16691bf982f467d7922919cb53` |

## Frozen source and profile

The only force/support packet is
`rawlocal/washer-land-reference-completion/attempt01`, receipt SHA256
`0218731514788a808ea8cb313945fe1000cbf63b51c181c9415b366ab374a46a`.
It has eight supported nominal rings, 48 finite geometry probes and 48 own-end
states from the fresh simultaneous corner response `e699b5…` under the same
`c3a8…` frame comparison and `62bd…` response. Every saved tension is positive.
No ordinary N10 end or quarter-inch retail end is substituted.

| Declared profile or material quantity | Fixed value |
| --- | ---: |
| Washer inner/outer radius | 4.953 / 11.0236 mm |
| Washer thickness | 1.6256 mm |
| Circular head/nut pressing radius | 6.0 mm |
| Steel modulus / Poisson ratio | 200,000 MPa / 0.3 |
| Hypothetical steel yield comparator | 250 MPa |
| Wood / head contact stiffness | 20 / 10,000 MPa/mm |
| Wood base comparison reference | Existing conditional dry DF-L No. 2 perpendicular-to-grain value, 625 psi |

These are the existing `side` family and constitutive hypotheses from
[upper-right-washer-flexure.py](upper-right-washer-flexure.py), SHA256
`782ded96afd5e02e27873bd72b77073a643ed7c2a7946703a3240b1f51b21eac`.
They are not measurements or delivered product ratings.

The solver is unchanged
[upper-right-washer-edge.py](upper-right-washer-edge.py), SHA256
`ffe3db3e8c707851d44f0c60c43e6e6ef4aa4845f753dc6880c64186e3c75e61`.
Its `make_model` selects a `rail` slot. This run supplies an in-memory copy of
the existing side profile in that slot, as the earlier retail consumer supplied
its own declared profile. No helper source, dimensions, stiffness, loading law
or free-edge boundary condition changes.

## Parent API and bounded execution

Producer: [washer-top-side-fine-reference.py](washer-top-side-fine-reference.py).
Import is inert; the API is `build(output: Path)`.

```sh
uv run --no-sync python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/washer-top-side-fine-reference.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/washer-top-side-fine-reference/attempt01
```

The output must be a fresh unaliased immediate child of the specified raw
folder. The parent owns the numerical slot. The source contract and producer
snapshot are written before setup; one JSONL record is flushed after each end.
The final summary and receipt retain numerical stops and source/artifact hashes.
No earlier producer, standalone helper launcher, engineering coupon, software
test, ordinary-state solve, frame solve, CAD query or native solver is called.

Only `make_model(..., 'fine')` and `solve_state` are numerical entry points.
The fixed fine recipe has four radial elements inside the head band, twelve
outside, Fourier order eight, 128 angular stations and 1,142 unknowns. Existing
limits remain 100 Newton steps and 50 Armijo backtracks, gradient tolerance
1e-4 N, contact force tolerance 0.001 N and contact first-moment tolerance
0.02 Nmm. There is one model assembly and at most 48 state calls, with no
relaxed retry or added stiffness.

## Signed own-end load mapping and outputs

Each end retains its physical key, seat, inward normal, signed receiver force
and signed own-seat moment. The force must equal `T * inward_normal`, and the
moment must be transverse. The circular model takes the magnitude of that same
end's moment, not a global maximum or a receiver-datum lever moment.

For nonzero own moment **M** and inward normal **n**, the local pressure-offset
direction is `x = (n cross M) / |M|`. It satisfies
`|M| * (x cross n) = M`, so the scalar first-moment drive preserves the physical
moment direction. A zero-moment source uses an arbitrary recorded tangent
direction; it does not acquire an invented moment. The frozen rigid-contact
closure and tilt initialize Newton only and do not supply the returned stress.

`end-states.jsonl` retains each source, returned fine state, stress witness,
sampled wood-pressure witness, force/moment residuals, iteration diagnostics
and any numerical failure. Dense field rows are evaluated by the unchanged
helper and discarded after their witnesses are captured. This keeps the
bounded output compact without replacing the method's sampling recipe.

The result reports separate same-state peaks for sampled washer stress,
stress divided by hypothetical 250 MPa yield, and sampled wood pressure divided
by the declared base reference. Yield exceedances are explicit keys even when
all 48 numerical states finish. A numerical stop remains a method limit and
does not establish a physical test failure or joint incompatibility.

## Applicability limits retained

The existing fine approximation uses weak free radial edges and unilateral
normal contact. Its sampled face bending and midplane shear proxy does not
include contact normal stress through the thickness, three-dimensional edge
stress, plasticity, friction, preload or geometric nonlinearity. This run adds
no stress convergence sweep or actual washer capacity.

Nominal STEP support is established for the declared ring. Loaded shift/tilt
and its changed contact support remain unqualified. Thickness, steel yield,
delivered head/nut bearing geometry, timber properties and seat stiffness
remain explicit hypotheses. The washer response is not fed back into shaft,
two-group joint or frame equilibrium. The wood base reference is a component
comparison, not full adjusted timber or joint resistance.

The older degree-four side results, retail quarter-inch fine results and the
1,006 finite ordinary N10 ends remain separate evidence. They do not replace
these 48 fresh matched-family comparisons or gain an actual resistance rating
from this run.

## Read-only ordinary-end recipe inventory

The inventory uses the completed `washer-end-reference-join/attempt01` worksheet,
receipt `8f8b06d4a90b6c9462fb5f21fa398e42582a7d9be337c1fb327324b42d035783`
and result `3ab64baace0f8374071c28da13fa1cda7d8ac6d0cb347ee88078390cac02e10c`.
No ordinary end was solved during this inventory or by this producer.

| Finite ordinary rows | Declared profile and support | Existing plate recipe applicability |
| ---: | --- | --- |
| 850 | K.L. Jack 25NWUS; wood radii 4.1529–9.2329 mm, head radius 5 mm; thickness envelope 1.2954–2.032 mm; Kwood 20, Khead 10,000 | Exact dimensional match to the existing quarter-inch rail envelope at ID max, OD min and thickness min. Full nominal support is bound: 778 saved effective-STEP rows, 24 pinned outer-X proposal rows and 48 newly matched current rows. Fresh plate comparisons are unperformed, not excluded by profile/support domain. |
| 12 | Same quarter-inch catalog washer, but modeled wood and head contact radii both 4.1529–5 mm | Existing full-annulus plate contact domain does not match this restricted wood mask. Six nut rows have the central static trial; six other rows remain end-datum/full-annulus unresolved in the join. This is a specific support/contact-domain mismatch, not missing demand. |
| 48 | Bolt Depot 15025; wood radii 7.3279–17.3736 mm; head radius 9.3472 mm; thickness envelope 2.1844–3.3528 mm | Retained full nominal support exists. Dimensions do not match the existing quarter-inch, 5/16 side or retail-fender plate profiles. A new declared profile would be required and is outside this run. |
| 96 | Bolt Depot 15023; wood radii 5.7531–12.6111 mm; head radius 6.9977 mm; thickness envelope 1.6256–2.6416 mm | Same retained full-support basis and specific existing-profile mismatch. No plate result is transferred. |

All four ordinary groups retain Kwood 20 and Khead 10,000 MPa/mm. The existing
rail helper's older catalog route is Bolt Depot 2994; the 850-row K.L. Jack
25NWUS route shares its listed dimensional envelope. That is a geometry and
method match, not a transfer of steel yield, product rating or actual capacity.
The direct quarter-inch fine family uses inner/outer diameters
8.3058/18.4658 mm, thickness 1.2954 mm and pressing radius 5 mm. Its wider
25.4 mm OD, 2.5 mm thick retail variant is a separate profile.

Two additional G7 ordinary end rows remain null after the preserved
150-iteration local-equilibrium stop. Their T = 0 source tie does not turn an
unknown own moment into a usable zero-demand plate check. The 48 common-knee
rows are outside this 1,006-row finite ordinary inventory; their profile is not
inferred from missing fields in this joined worksheet. Nothing here authorizes
an ordinary-state batch or changes the current 48-side-state run.
