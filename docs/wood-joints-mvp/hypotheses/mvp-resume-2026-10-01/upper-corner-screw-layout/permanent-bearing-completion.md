# Permanent bearing completion: frozen parent-run adapter

## Execution state and API

The parent executed `rawlocal/permanent-bearing-completion/attempt01` with terminal exit 0 and status **COMPLETED_PERMANENT_BEARING_COMPARISON_WITH_EXPLICIT_GAPS**. The saved nominal permanent comparison has zero supported reference exceedances. The worker authenticated the saved evidence and annotated this document; it ran no tests, numerical producer, solver, frame, geometry generator or CAD process. Import is inert and loads only the Python standard library.

The API is `build(output: Path)`. The output must be a fresh immediate child of `rawlocal/permanent-bearing-completion/`; existing attempts and symlink output paths are refused. `prepare()` authenticates the inputs and returns header/census metadata without creating output or importing numerical packages.

Parent command, from the repository root, using the frozen Python environment:

```sh
python -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/permanent-bearing-completion.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/permanent-bearing-completion/attempt01
```

Required runtime is Python **3.12.3** and NumPy **2.5.2**, enforced by the reused contact method. SciPy, OSQP and Clarabel are not imported or required. Execution is bounded to one saved state, one D-array read, 1,170 cell-row geometry checks, 956 represented cell means, 108 face means, eight floor means and 190 receiver-side scalar records. There are no nonlinear iterations, seed runs, retries or alternate load cases. The parent owns the serialized execution slot and any external process time cap.

## Frozen inputs

All hashes are SHA-256. The producer contains the complete 21-pin map, including its own snapshot pin. Paths below are relative to this directory unless stated otherwise.

| Input | Exact hash |
| --- | --- |
| Executed producer `permanent-bearing-completion.py` and attempt01 snapshot | `17b5f63502d9ceaa66bd91fefee3eb6ec11bd68285d4616e27322ea2d8133c22` |
| Historical preparation producer, preserved in `rawlocal/permanent-bearing-completion/source-snapshots/producer-557fcb61.py.snapshot` | `557fcb612073dfe786a8b0eff35e011cec1520d181009e077d544643573570a9` |
| `rawlocal/knee-bridge-permanent-resolve/attempt02/response.npz` | `605ef2df67345633860a7d7d77da89e9ec85e94be62ad3c5cd4737c5a0084033` |
| Same attempt `comparison.json`, including stored CD0.9 member references | `3179d7d40d60a3e21f101610c83acfb588f7e9612941cd253123c9881bbd708a` |
| `contact-bearing-completion.py` | `4c1240a296f764d2565edf219e2a5aa1b0fae25958840f7cc64a610662bee1ee` |
| `receiver-bearing-completion.py` | `767da34553071c946b9f0ea88047bb1dedf83b7034cdb47e4945382cb50de8b4` |
| `rawlocal/contact-bearing-completion/attempt02/geometry-inventory.json` | `68b421d5d8b16579fbbd5214167830cc0376163e629fcec7a2f407efcf0d1db3` |
| Same attempt `receipt.json` | `7e7fdf6195f1611dcf4b020e75cd6ec9c99b04a09e58bdb7631e9e7d51aae326` |
| `rawlocal/knee-bridge-gravity/attempt01/operator-assessment.json` | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| Same attempt `operators.npz` | `7877699053a8285b77621ca0cfcb7b09d22b19e5c20729c193e1e5c3f4840e4f` |
| Same attempt `row-identities.json` | `cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27` |
| `rawlocal/kicker-path-completion/parent-attempt01/contact-bearing.json`, direction/identity fields only | `e6d71fdd4355c001a6dcf8ce6a5288e4b68c6bdfe4975cae46be13c37b322dea` |
| `../../hardware-material-specification-2026-09-30/material-inputs.json` | `0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a` |

The historical preparation's canonical source map hash is `fb73e1269965920b06cd44a9011947156371a0c29736a187df2fb089d4143a5f`. The actual attempt01 `sources.json` hash is `d176d86e74382b1df83d165e9e4ee7117310ce6d2838ae8307c37e2708d7c83e`. Before execution, the parent changed only dict-literal style and removed an unused assignment while retaining its pure-function extraction call; the historical 557 source remains preserved byte-exact. No engineering result existed before that style correction. The remaining pins bind the unchanged model, model inputs, N15 receipt, receiver addendum, original/corrected contact geometry and pure wrench/reference helpers. The contact receipt and permanent comparison agree byte-for-byte on shared operator, model, model-input and row pins.

## Same-state scope and method

The only force/motion arrays consumed are `permanent-only_gap_raw_force_n` (1,888), `permanent-only_gap_lumped_q_mm` (1,612) and the corresponding nominal response headers. The saved zero-gap state remains preserved and is not evaluated here. The load basis is the saved ce69 gravity model plus 25 kg equipment once: gravity column zero, multiplier `1.1110134616260479`, and zero live gravity, horizontal and hold-moment scales. No force envelope, live maximum, climber load, geometry or stiffness is substituted.

The frozen contact method's pure definitions are compiled into a private namespace. Declared overrides are the saved permanent response/comparison, one `permanent-only` case, and the terminal census changed from six-case 648/48 to one-case 108/8. The census expression must match exactly once. Original method files and globals remain untouched; every contact-law, signed-D, area, wrench and floor-projection audit remains active at its original tolerance.

Positive areas are recovered from the **nominal permanent forces**, using the existing exact `force > 0` mask and inventory cell areas. Live active masks, live resultants, utilization values and pass flags are not consumed. Floor areas follow the frozen uniform-footprint projection law, including its exact full-positive-mask and area-closure checks.

| Output scope | Count |
| --- | ---: |
| Wood-involving contact faces / cells | 108 / 856 |
| Wood receiver sides | 190 |
| Floor footprints / projected cells | 8 / 100 |
| Base/header faces, included within the 108 | 16 |
| Represented emitted cell records | 956 |
| Excluded panel/panel faces / cells | 9 / 214 |
| Receiver classes: perpendicular / conditional parallel / conditional oblique / ripped parallel study | 156 / 26 / 4 / 4 |

Receiver-side records join exact raw-row sets and owners to frozen N15 direction metadata. Only receiver, other body, face identity, raw rows and grain-direction dot product are copied. The four standard parallel interfaces that had no active compression in the earlier live packet remain included; new permanent masks determine their numerical applicability.

Stored `references_cd0_9` supply `Fc_star_mpa` directly to the unchanged receiver scalar kernel. CD0.9 is applied **once in the stored references**, with no second multiplier and no column-stability factor CP. Conditional perpendicular bearing remains the existing 625 psi / `4.309223308230226` MPa reference, unchanged by CD. Oblique means use the frozen Hankinson formula. Parallel means retain the separate `mean_stress / (0.75 Fc_star)` plate trigger; an exceeded trigger requires a plate that this packet does not establish.

The inherited contact/floor kernel also emits its 625 psi face/cell diagnostics, base average, quarter-area corner sensitivity and total-resultant quarter-area bound. Grain-matched receiver means are reported separately. A perpendicular diagnostic on a parallel or oblique interface does not replace the applicable receiver law or establish complete connection capacity.

Zero positive area requires zero compression. Such receivers retain explicit `NO_ACTIVE_COMPRESSION`; parallel/oblique resistance ratios and plate evaluations stay null when there is no active demand. Four ripped parallel receivers always retain **null supported resistance**, with finite hypothetical ratios only when active: `center_principal_cleat_left/right` and `knee_outer_left/right_inner_frame_block`. Their CF1 study references do not establish grade inheritance from ripped 4×6 stock.

## Evidence, outputs and remaining limits

Actual attempt01 receipt SHA-256 is `2ee4b21edb30da8efcfedfa07bc9f004f388568ed70e1afb9110df9708ebfec5`; report SHA-256 is `570451dffb2a480f3aa514ab10695eabd0f615318aba50d404cb4b51618c139e`. All **21 current source pins and eight recorded outputs** authenticated, before/after source maps agree, and both the executed and historical producer snapshots authenticated. Runtime was Python 3.12.3 / NumPy 2.5.2. Actual output census is exactly 108 wood faces / 856 wood cells, 190 receiver sides, eight floor footprints / 100 cells, 16 included base/header faces and 956 emitted cells; nine panel/panel faces / 214 cells remain excluded. No solve or test was performed by this producer.

### Actual receiver means and null distinctions

The values below are saved maxima by applicable resistance ratio, with the stress and reference from that same permanent-only nominal witness. References already include CD0.9 where applicable; perpendicular resistance is unchanged.

| Receiver class | Sides | Finite supported ratios | Inactive sides | Supported nulls | Peak ratio | Witness mean / reference (MPa) |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Perpendicular | 156 | 156 | 12 | 0 | 0.024626620520530416 | 0.10612160715001041 / 4.309223308230226 |
| Conditional parallel | 26 | 18 | 8 | 8 | 0.00870318708409561 | 0.08019850364413848 / 9.214843122319516 |
| Conditional oblique | 4 | 4 | 0 | 0 | 0.011469811388487084 | 0.07188209117115052 / 6.267068283555451 |
| Ripped parallel study | 4 | 0 | 0 | 4 | 0.0003525693653215813, hypothetical only | 0.0029535194465219365 / 8.377130111199559, hypothetical only |

All supported and hypothetical finite ratios have zero exceedances. There are **20 inactive receiver sides**, covering 12 inactive wood faces; all eight floor footprints are active. The 12 inactive perpendicular ratios are explicit zero-demand zeros under the inherited mean method. Eight inactive conditional parallel ratios remain null because there is no positive area. The other four supported nulls are active ripped-stock interfaces lacking a supported material basis; all four have separately labeled finite hypothetical ratios. Inactive demand and missing supported capacity therefore remain distinct.

Same-state ratio witnesses are:

- Perpendicular: `lumber_leg_right` against `main_upper_right`, `legacy/contact-patch-112`, raw rows 1230–1233; compression `167.62058452092487` N over positive area `1579.5141915254005` mm².
- Parallel: `base_post_center_left` against `base_header`, `legacy/contact-patch-8`, raw rows 364–367; compression `213.43107477059104` N over `2661.2849999999994` mm².
- Oblique: `base_principal_center_left` against `base_header`, `legacy/contact-patch-12`, raw rows 380–383; compression `91.8854697102747` N over `1278.2804202439847` mm².
- Ripped study: `center_principal_cleat_right` against `base_header`, `legacy/contact-patch-19`, raw rows 408–411; compression `17.061617240335696` N over `5776.7072637451065` mm².

The largest conditional parallel plate-trigger ratio is **0.011604249445460813**, at the parallel witness above; none of the 18 active conditional parallel comparisons exceeds `0.75 Fc_star`. Eight inactive parallel sides retain no plate evaluation. The largest hypothetical ripped trigger is `0.00047009248709544175`, at the ripped witness above; none of the four hypothetical triggers exceeds its study threshold. These results do not establish a plate or qualify ripped resistance.

### Actual contact/floor diagnostics and audits

All four inherited conditional contact checks are true: base average, quarter-area corner sensitivity, flush-face wood bearing and floor-rail wood bearing. These use the existing perpendicular reference and retain the grain-law distinction above.

| Saved diagnostic | Maximum ratio | Same-state witness |
| --- | ---: | --- |
| Base active-area average | 0.018610895260630058 | `legacy/contact-patch-8`, base_header / base_post_center_left |
| Base quarter-active-area corner sensitivity | 0.06672394167539404 | `legacy/contact-patch-12`, base_header / base_principal_center_left |
| Represented wood cell mean | 0.02600296358155129 | `legacy/contact-patch-82`, base_rail_top / main_upper_left |
| Floor uniform-footprint mean | 0.017695570941559772 | `floor/lumber_leg_left`, 557.3300205468242 N over 7308.846772218796 mm² |
| Floor-rail uniform-footprint mean | 0.00021616512156965385 | `floor/base_floor_left`, 64.43782753627164 N over 69176.13100390004 mm² |

Saved audit maxima are contact-law error `2.2147779077386076e-7` N, floor-projection error `2.842170943040401e-14` N, signed wrench force error `5.009326287108706e-12` N and moment error `1.9172148313373327e-9` Nmm. There are zero force/closure branch disagreements. These passed the unchanged method tolerances; no audit was relaxed.

Existing saved contact attempt02 records `PASS_CONDITIONAL_BEARING_ARITHMETIC` for its six live states; the receiver attempt01 records `COMPLETE_SCALAR_BEARING_ADDENDUM_WITH_EXPLICIT_LIMITS`. These authenticate prior execution of the reused kernels. Their forces, masks, maxima and acceptance do not transfer to this permanent comparison. This implementation does not repeat their software tests or require a new method coupon.

The parent run wrote `inputs.json`, `bearing-results.json`, `cell-actions.jsonl`, `receiver-bearing.json`, `report.json`, `sources.json`, `producer.py.snapshot`, `.gitignore` and `receipt.json`. It authenticated sources before and after arithmetic, verified the snapshot, recorded actual after hashes and all preceding artifact hashes, and checked actual output census. Exceptions preserve a STOP receipt and are re-raised without retry. Completion does not require all comparisons to pass. Terminal output is a compact result with status, counts and producer/report/receipt hashes.

The finite saved-state comparison has supplied permanent mean bearing reference ratios and exceedance/plate-trigger counts. It does not resolve physical pressure peaks, contact refinement, local crushing/plasticity/splitting, the actual floor substrate or pressure patch, friction/no-slip verification, plywood-side bearing or excluded panel/panel capacities. Ripped parallel supported capacities remain missing as specified above; actual stock/grade remains unobserved.

The source nominal solution retains rank **296**, nullity **4**, bounded seating, no strict active-tangent stability acceptance and no uniqueness of seating/force envelope. The 104 global bolt axes and 66 screw axes remain the modeled system; four additional proposal-internal static ties are absent from global connector rows. This scalar comparison supplies no new tie compatibility, changed-hole stiffness, joint/frame acceptance or physical/fabrication release.

Historical source-only preparation completed under producer 557 and document hash `64bc4d046ca595c334cfb5cea051c217566d025b601e3375b0f866fbafaaf544`, with 21 authenticated pins, the exact census and receiver classes above, and no NumPy/SciPy/OSQP/Clarabel import. Actual execution under producer 17b5 completed the same-state finite permanent bearing comparison. The producer, attempts and source snapshots remain unchanged; this document alone was annotated and frozen for publication.
