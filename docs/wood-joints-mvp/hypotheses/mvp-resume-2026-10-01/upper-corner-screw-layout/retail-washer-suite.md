# Retail washer: finite suite of 48 current rail ends

**Parent completed the serialized finite suite: 48 of 48 ends and one coupon,
with no numerical stops. Formal acceptance, complete joint acceptance and
physical release remain false.**

The [268-line wrapper](retail-washer-suite.py) extends the existing
[retail washer comparison](retail-washer.md) to all four current top-rail bolts,
their two distinct exterior ends and six nominal cases. Each physical bolt has
one shared axial tie and two separately retained end moments. The suite uses
the compatible records in `rawlocal/corner-first-order/attempt01/checks.json`.
Every tension is positive; an unexpected zero-tension state stops preflight
without assigning a successful unloaded solution.

The largest tension and largest moment remain the `k12-right`, right,
`rail_1` host witness: **707.8836379321689 N / 2432.0683873549224 Nmm**, with
M/T **3.4356895074723695 mm**. The largest eccentricity is the
`a12-forward`, left, `rail_2` host: **292.95726204203874 N /
1298.6281869903887 Nmm**, with M/T **4.432824699201477 mm**. These are separate
same-state sources. Largest T/M alone does not bound washer stress. The
completed finite suite identifies the maximum sampled stress proxy among
exactly these 48 frozen ends, under the fixed assumptions below.

## Frozen model and method

| Input | Fixed value |
| --- | --- |
| Analytical washer ID / OD / thickness | 8.3058 / 25.4 / 2.5 mm |
| E / nu / assumed Fy | 200000 MPa / 0.3 / 250 MPa |
| Kwood / Khead | 20 / 10000 MPa/mm |
| Concentric pressing footprint radius | 5 mm at every end |
| Timber bore radius under these lands | 3.75 mm |
| Saved fine resolution | 4 inner + 12 outer radial elements; Fourier order 8; 128 angles; 1142 unknowns |

The unchanged retail producer and its frozen edge/flexure/helper chain supply
the model, rigid-mode diagnostics, coupon, equilibrium solver, field recovery
and CSV writer. The wrapper adds records, support inventory and reporting. It
does not introduce another mechanical model. One assembled fine model and one
full-face 100 N / zero-moment coupon serve the entire suite. Each end starts
from its own saved rigid contact, with no warm start from another end.

The signed moment and slope vectors, global beam-end moment, physical pressure
frame, exterior seat and common axial-tie identity remain in each source
record. The inherited circular plate uses that end's moment-aligned magnitude
drive. Each actual eccentricity is retained. Both radial edges remain free;
wood and head contact remain compression only. Existing gradient, force and
moment tolerances remain 1e-4 N, 0.001 N and 0.02 Nmm. The fields and free-edge
residual traces remain those of the unchanged helper.

## Eight nominal exterior seat lands

The four `base_rail_top` host lands reuse the retail producer's finished-face
support extraction with the corresponding axis identity. Each check retains
the saved STEP binding, rectangular outer trim and all eight circular holes.
The four cleat lands use the already frozen corrected geometry in
`rawlocal/corner-timber-sections/attempt02/checks.json`: its grain frame,
rectangular bounds and four through-bore records. The own rail bore is inside
the declared washer opening, the other rail bore clears the outer disk, and
the two orthogonal side bores do not intersect the exterior seat plane.

| Side / rail bolt | Host disk edge margin | Cleat disk edge margin |
| --- | --- | --- |
| Right / rail_1 | 32.75 mm | 30.65 mm |
| Right / rail_2 | 30.65 mm | 30.65 mm |
| Left / rail_1 | 32.75 mm | 30.65 mm |
| Left / rail_2 | 30.65 mm | 30.65 mm |

The minimum other-bore clearance is approximately **16.55 mm**. Each declared
concentric supported annulus is **452.525755 mm²**. These are saved nominal
geometry results, not inspected seats or loaded shift/tilt guarantees. No CAD
extraction or geometry reconstruction is required. Unsupported trim or a bore
reaching an unexpected exterior stops preparation.

## Source pins and API

| Source | SHA-256 |
| --- | --- |
| Suite producer | `0775cced28cba10094e540ef74b57a5c1ac5a54646f74fa2b0983ad737f0434f` |
| Unchanged retail producer | `894608d5abc879e3d679e8149cbf181c0cda224f2fbb164a0cbdb06f882e246f` |
| Current first-order checks | `b15b57d3879fdca2dac607d11a2ad127acd1008f6c2a6f546333a1b26c754cfe` |
| Corrected timber geometry checks | `8b954edf5743999f427d2b99fcaaf9288578f02dc59a5cf1e632da634aa2e813` |
| Saved attempt02-fine checks | `c920d85bfdab7a9cbc802a0e4f79f817e2ac68fe8dfaf4ab1f50aa31d8dec5ae` |
| Saved attempt02-fine output receipt | `71e348c521af93f56a0d7941028ec0ac487a8d379692ca12e20029a7089fa355` |

Read-only preflight authenticated **46 pins**, **48 unique ends**, **24
case-specific axial ties**, **four rail bolts**, **six cases** and **eight
exterior lands**. Preparation executed source authentication and nominal
support checks only. No mechanical calculation or software tests were run.

`build()` authenticates the helper chain and returns the prepared records,
supports, pins, fixed settings and imported helpers. It does not assemble a
mechanical model. `preflight()` returns a serializable plan;
`preflight(prepared)` can reuse the dictionary returned by `build()`.
`run(output)` performs the parent-owned serialized mechanical execution.

The optional CLI `--preflight` prints the plan without calculations or output
writes. The parent executed the command below once under the serialized slot,
from the repository root. This is the reproduction command for the completed,
immutable `attempt01-fine` output, not a rerun request. The producer requires a
fresh immediate child of `rawlocal/retail-washer-suite/` for execution.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/retail-washer-suite.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/retail-washer-suite/attempt01-fine
```

## Retained output and completed result

The ignored output retains the producer snapshot, input snapshots and manifest,
the full preflight plan in `inputs-before.json`, and actual source hashes in
`inputs-after.json`. All pins are authenticated again after execution. Each
`end-NN/` contains its source, full state or numerical-stop diagnostic in
`checks.json`, and recovered `fields.csv` when available. A failed end retains
its last accepted state and any recovered partial fields; it receives no
successful result and is not retried. A coupon/setup stop leaves all 48 source
records explicitly stopped.

The suite `checks.json` records completion counts, the one coupon, runtime
versions, eight lands, per-end paths and separate maximum envelopes for stress
proxy, assumed-Fy ratio, wood/head pressures, closure, tilt, sampled deflection,
non-affine displacement and gradient residual. Every maximum retains its own
simultaneous source. An incomplete suite labels its envelopes partial.
`source-pins.json` authenticates the output files. The complete ignored run,
including all 48 sampled field files and snapshots, occupies **767,438,748
bytes (0.767 GB)**; no bulky output belongs in staging.

The current host witness is compared against every key of the saved fine state,
the exact baseline source, the complete field CSV SHA-256 and the saved coupon.
Metric differences are also retained. Incomplete end coverage, changed source
pins or a failed exact baseline comparison make the suite status `STOP`.
Numerical completion is a finite hypothesis result, not formal acceptance.

The parent returned CLI exit **0** and status
`FINITE_RETAIL_WASHER_SUITE_HYPOTHESIS`. Saved results retain **48 completed
ends, six nominal cases, four rail bolts, eight exterior lands and one
satisfied coupon**. Setup failure and all 48 end failures are null. All 48
recorded `elastic_Fy_250MPa_hypothesis_exceeded` flags are false. The runtime was
Python 3.12.3, NumPy 2.5.2 and SciPy 1.18.1.

Read-only authentication after completion verified **46 source pins and 121
output pins**, with no missing or changed files. Recorded before/after source
hashes are unchanged. The suite checks SHA-256 matches the parent's supplied
hash; the output receipt is also identified here:

| Saved result | SHA-256 |
| --- | --- |
| `rawlocal/retail-washer-suite/attempt01-fine/checks.json` | `3e2dee327dbd81d8584955de3c4918c9acc695b0386fa46abd568ba767c64f74` |
| `rawlocal/retail-washer-suite/attempt01-fine/source-pins.json` | `8eaeee303516584b7d031365cb83446c287735e9fa801120c0ec58dca1e67f79` |

The `k12-right`, right, `rail_1` host is retained in `end-24/`. Direct read-only
comparison confirms the exact baseline source, equality on every saved fine
state key, the identical saved coupon and **byte-identical full `fields.csv`**.
The field SHA-256 is
`3f24b1d693119d34213ef395ab00c812712c61ba0ab1ebb13822f8f852bf9e30`,
matching `rawlocal/retail-washer/attempt02-fine/fields.csv`. All nine recorded
metric differences from that baseline are exactly zero.

### Separate maximum witnesses

All envelopes cover the full 48 ends. Each row below names its own simultaneous
case/side/bolt/end. Values from different rows are not combined into a load or
contact state.

| Recorded maximum | Value | Case / side / bolt / end |
| --- | --- | --- |
| Sampled through-thickness stress proxy | 207.20534311829158 MPa | k12-right / right / rail_1 / host |
| Proxy / assumed 250 MPa Fy | 0.8288213724731663 | k12-right / right / rail_1 / host |
| Wood contact pressure | 2.962580253887594 MPa | k12-right / right / rail_1 / host |
| Head contact pressure | 144.85680316292465 MPa | k12-rear / right / rail_2 / host |
| Absolute head closure | 0.08916972687818453 mm | k12-right / right / rail_1 / cleat |
| Head tilt magnitude | 0.01405595469316601 rad | k12-rear / right / rail_2 / host |
| Sampled absolute plate deflection | 0.14824184808574736 mm | k12-right / right / rail_1 / host |
| Non-affine deflection weighted RMS | 0.004160249610910746 mm | k12-right / right / rail_1 / host |
| Scaled gradient residual | 8.845339726804013e-05 N | a12-rear / left / rail_2 / host |

The stress maximum is the existing host witness, with its original
707.8836379321689 N / 2432.0683873549224 Nmm pair. Its sampled maximum is face
von Mises at the free inner radius **4.1529 mm**, theta **0**, in element 0;
it is a recovered plate proxy, not a measured contact-edge stress. The largest
head pressure and head tilt instead belong to a
**393.8622595400373 N / 1732.7136066778476 Nmm** pair at the `k12-rear`, right,
`rail_2` host, with M/T **4.399288240262868 mm**. Maximum head closure belongs
to the `k12-right`, right, `rail_1` cleat with the same shared
**707.8836379321689 N** tension and its own **470.6470684769568 Nmm** moment,
with M/T **0.6648650191319373 mm**. The largest M/T source remains the separate
`a12-forward`, left, `rail_2` host recorded above.

The largest saved contact force residual across all ends is
**8.845339658591911e-05 N**; the largest absolute contact first-moment residual
is **0.0009919880846496199 Nmm**. These and the maximum gradient remain within
the unchanged numerical tolerances. Sampled free-edge residual traces remain
in every end result. They were not zeroed; for the stress witness, the inner
edge maximum absolute Mrr / Mrt / Qr traces are approximately
**0.00902891 N / 0.01654526 N / 0.04300195 N/mm**, and outer traces are
**0.00333830 N / 0.02233839 N / 0.00832906 N/mm**. Numerical equilibrium and
the one known-answer coupon do not establish stress convergence or an actual
product capacity.

### Limits and ownership at closure

The Hillman retail choice remains the existing product hypothesis. Its
conflicting listed nominal thickness fields do not guarantee a delivered
minimum; the modeled **2.5 mm** is the lowest listed nominal. The generic
**8.3058 mm ID** is not a measured product bore or guaranteed upper bound, and
numerical steel yield is unlisted. **250 MPa Fy**, E, nu and the **20 /
10000 MPa/mm** wood/head springs remain assumed inputs, without a measured
stiffness calibration. The **5 mm** concentric pressing radius is fixed at all
ends; actual head/washer fillets, chamfers, bore fit, shifted or tilted support
and delivered seat geometry are not established by this run.

The plate approximation omits contact-edge 3D stress, sigmaZZ, plasticity,
preload, friction and membrane/geometric nonlinearity. This thicker annulus
has less separation between thickness and radial span than the earlier thin
washer; the inherited method remains a screen. Prescribed T/M pairs are the
frozen current compatible demands. Changed washer thickness and contact
compliance are not fed back into joint or frame response. Finite coverage
establishes the sampled maxima only for these 48 ends at this fixed resolution
and these assumptions. All formal acceptance, complete joint acceptance and
physical-release flags remain false; actual stress and capacity remain null.

The finite suite and this result annotation are complete. Its frozen inputs,
source snapshots, baseline and ignored `attempt01-fine` output remain retained
for reproduction; no additional cases, dimensions, sweep or refinement are
scheduled here. No archive or pruning was performed. Parent owns planning,
physics decisions, all other documentation and staging/commits. Only this
Markdown file was edited for the result annotation; ownership is returned to
the parent at closure.
