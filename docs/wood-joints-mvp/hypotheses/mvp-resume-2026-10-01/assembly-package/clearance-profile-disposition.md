# Thirteen nominal clearance profile dispositions

This bounded N18 supplement dispositions the thirteen non-host service/profile
pairs named by the frozen [clearance exception packet](clearance-tolerance-completion.md).
All **thirteen nominal pairs have finite separation certificates**: eleven
LED7/upper-panel pairs and two T-nut/cleat pairs. These certificates use
authenticated primary enclosures and current saved STEP/source signatures;
they do not supply purchased-profile, machining or loaded-motion bounds.
They close this specific nominal applicability gap, not all N18.

The [producer](clearance-profile-disposition.py) is inert on import. Every
operation uses the Python standard library. Recipe files are parsed as
source, never imported or executed. No shape is rebuilt, imported, converted
or intersected. The actual comparison is a finite interval projection, with
zero CAD imports and zero exact-geometry queries.

## Actual finite results

| Current effective timber | Nominal service | Count | Separation lower bound, mm |
| --- | --- | ---: | ---: |
| `main_upper_left` | `light_A7` through `light_F7` | 6 | 13.650000000000 each |
| `main_upper_right` | `light_G7` through `light_K7` | 5 | 13.650000000000 each |
| `wj04_lower_full_stock_cleat` | `hold_tnut_main_G6` | 1 | 18.139999951634 |
| `top_center_right_cleat` | `hold_tnut_main_G12` | 1 | 18.139999810819 |

The result has eleven `NOMINAL_FINITE_FOOTPRINT_CYLINDER_SEPARATION` and two
`NOMINAL_FINITE_TNUT_ENCLOSURE_SEPARATION` records, with no pending profile
pair in this thirteen-pair inventory. Every record preserves its original
exception-stream line number, exact effective STEP pin, saved nominal mesh
pin, source shape fingerprint and source-summary signature.

The parent's fresh standard-library preparation and finite run completed at
`parent-prepare-attempt01/` and `parent-attempt01/`, both with exit 0. Their
receipts retain **650 source pins**, unchanged before and after publication,
and record **0.785787557 s** for preparation and **0.460650527 s** for the
finite run, with zero CAD imports and zero exact-geometry queries. All
**thirteen pair records are identical** to the original worker result; the
eleven preserved wire-intersection records are also identical. Only the
producer binding and resulting setup/report receipts changed.

The original worker runs used **Python 3.12.3** and remain preserved as
historical exact artifacts: preparation **0.794089843 s**, finite build
**0.468803012 s**, both exit 0. These runtimes include source authentication
and publication work; they are not parent slot limits or solver runtimes.
Worker AST parsing passed. No software test or review loop was run.

## LED7 finite footprint and cylinder certificate

The authenticated `panel_grid_v2.py` recipe places LED7 at **1199.2 mm** along
the main face, twenty millimetres below the **1219.2-mm** upper-panel start.
The primary electrical recipe models these lights as **12.7-mm-diameter
cylinders** along the board normal. Their board-S interval therefore ends at
**1205.55 mm**. The finite upper-panel footprint starts at 1219.2 mm, giving
**13.65 mm** separation along the unit board tangent. Cylinder axial length
and rear projection lie along the orthogonal normal and do not consume this
tangential separation.

Both finite panel footprints retain their kerf-right X extents, full
1219.2-mm height and recorded 18.25625-mm category thickness. The saved
stock-profile outer corners check the panel-S interval. The current saved
panel/source signatures bind those footprints to the effective panel STEPs.
The pinned right-panel remachining recipe clips restored plugs to the
inherited outline; its holes and plug restoration cannot add material below
that footprint. No G2 move or old coordinate is applied to these eleven
unchanged row-7 lights.

The saved rear lower corner is used for the world transform, including the
floor-flush translation. A generic historical model-origin default is not
substituted. The inherited **1e-7-mm** datum/query resolution is an identity
gate, not a cutting tolerance. Recorded JSON corner rounding is not used as
a shop interval or loaded displacement allowance. The 13.65-mm values are
nominal primary-geometry separation certificates, not a delivered electrical
body envelope or an observed installation margin.

## T-nut finite profile enclosure screen

The current nominal T-nut recipe has a **25.4-mm flange diameter**, **1.86-mm
flange thickness**, **11.0-mm provisional barrel diameter**, and **12.7-mm
modeled barrel projection** into the panel. The screen uses the union of two
filled outer cylinders at the authenticated G6/G12 rear seating datums. It
projects each cylinder into the respective current finished cleat's recorded
stock frame, against an enclosure containing both the source blank and the
recorded finished-face extents.

The cleat's front setback separates both cylinders. The flange controls:
its rear projection is nominally 1.86 mm while the cleat's nearest face is
nominally 20 mm behind the panel. The actual recorded frame projections give
the two **18.1399998–18.13999995-mm** lower bounds above. The barrel's
individual bounds are **20.000000058922 mm** at G6 and
**19.999999918107 mm** at G12. The union takes the minimum component bound;
it does not combine maxima or treat an overlapping world AABB as a collision.

Filling the flange retention holes and the smooth thread opening enlarges
the nominal service shape. Positive separation of that larger enclosure is
sufficient for separation of the recorded pierced profile. No flange clocking
or unmeasured barrel diameter is promoted to a purchased dimensional bound.

If a source-bound enclosure fails to separate, the executable API returns
`PRIMARY_ENCLOSURES_OVERLAP_PROFILE_METHOD_REQUIRED`, with
`nominal_separation_certified: false` and `physical_collision_claim: false`.
It retains the exact method limit: resolve the **pinned nominal mesh or the
authenticated pierced-flange/smooth-bore recipe against the effective finished
STEP**. No exact T-nut STEP is supplied by the current pair plan. A filled-disk
overlap cannot establish a collision of the pierced profile. This branch was
not needed for the current two pairs; the method limit remains in both
records.

## Saved identities and source closure

The producer authenticates **650 consumed pins**, including all **628 original
N18 pins**, before and after publication. The original maintained N18 leaves
remain frozen at Python `9c73c99103ad95ecaf71a0deaa68bc8aa769ce18c36dc6f39a7e021bfa680505`
and Markdown `fd0276ef89bf51ada429a5bd09b77322ea38ddea8a652e7e276f022aac65a742`.
The original result, receipt, exception interpretation and query plan remain
unchanged. This new receipt does not relabel their preserved verdicts.

| Effective STEP | SHA-256 |
| --- | --- |
| `main_upper_left.step` | `4be26c61e59ca3c74f370989097f4bff9edf337fa4de1a30d7e5de9eb7ef52f7` |
| `main_upper_right.step` | `2791dca8f42b86a49b9e685f0f85d896642cbe9975a89bf1524bed89eddfea8f` |
| `wj04_lower_full_stock_cleat.step` | `231262125246a456aab725c97175e6035e3112bd7a06e0753f232ca1a80b29b3` |
| `top_center_right_cleat.step` | `95408c99e9fda6a274f71f764b95c3298c7077f1d0cf6e91fd45a7efcbb2493d` |

The corresponding source fingerprints and shape-summary signatures join
`operators-attempt02/model-inputs.json`, the current saved-solid bundle,
the effective pair plan and, for both cleats, `surfaces.json`. The saved-solid
bundle pin is `8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420`.
Its recorded source hashes match all ten recipe hashes declared in the
maintained producer. Relevant shop-manifest hashes match as well; no source
producer is replayed. `primary_recipe_sha256` in the setup preserves every
exact recipe pin.

| Raw artifact under `rawlocal/clearance-profile-disposition/` | SHA-256 |
| --- | --- |
| Current `parent-prepare-attempt01/setup.json` | `0284bb4953939acc1d24ffd3b844f2be130a4c7d24db82433cced6657b20d362` |
| Current `parent-prepare-attempt01/receipt.json` | `14ea66a611d05e77198e4e37e064f15b3e4634cf57c8f15b74d3346463c06228` |
| Current `parent-attempt01/result.json` | `537d373152c7f882227aae254c0ba689d2a9f490a8b2aec79fcf147d2bdcd1af` |
| Current `parent-attempt01/receipt.json` | `447556879b27ed65dfbce530b17a7b2bbccc3c2881650ac38658bc68e1fc4ef0` |
| Historical `prepare-attempt01/setup.json` | `1865b7d1fc9d325abb25559213d9113970ca562af809626edaacb304bc61bce9` |
| Historical `prepare-attempt01/receipt.json` | `4303169d545853542efa6d62ae7f97f52ca771b648cca79e9f8e38548a7c2d34` |
| Historical `attempt01/result.json` | `649218784eb5054aceb78400081bdcf1295ead8d1f3769b50e0be5acc9439d6f` |
| Historical `attempt01/receipt.json` | `995ddef92da3de013dabce3e8c2c06e3109ba33f68f1e204c315f93f2b6b4cbb` |

The parent corrected only import ordering for Ruff `I001` after ownership
returned. The current maintained producer and both fresh parent snapshots
have SHA-256
`d9eefbc8254aeab1e6436d437d6d4c627af9fb20395a261ea160e4259fefea14`.
The original worker snapshots remain byte-exact at
`81fab4319707668b03fc54f9a03554f81a026fbf8600a307fb5ac4e234029cfa`.
Their original setup/result/receipts are historical exact records and are
not rebound to the current producer. The import-order correction changes no
geometry or finite comparison. Existing output is never replaced.

## Executable API and parent replay

After an inert import, `prepare(output)` authenticates and joins the recorded
sources into `setup.json`. `iter_queries(setup)` exposes exactly thirteen
descriptors. `evaluate(query)` returns a finite separation certificate or the
explicit overlap/profile-method limit. `build(output, setup)` authenticates
the prepared receipt and evaluates only those thirteen standard-library
projections. `run(output, setup)` is the same cheap operation; it imports no
CAD. Every output must be a fresh immediate child of this leaf's raw folder.

Future parent replay begins with fresh preparation using the current
producer, then builds from that new setup. The original worker setup binds
the preserved `81fab431…` producer and must not be used with the maintained
`d9eefbc8…` producer. Both output children below must be fresh:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/clearance-profile-disposition.py prepare \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/clearance-profile-disposition/replay-prepare-attempt01

PYTHONDONTWRITEBYTECODE=1 python3 \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/clearance-profile-disposition.py run \
  --setup docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/clearance-profile-disposition/replay-prepare-attempt01/setup.json \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/clearance-profile-disposition/replay-attempt01
```

The completed parent run above used the separately frozen
`parent-prepare-attempt01/setup.json`; its exact source/producer binding is
recorded in the current artifact table. Output consists of setup/result,
receipt, producer snapshot and an ignore marker. A changed source, producer,
STEP/signature, prepared receipt or thirteen-pair identity stops publication.
No cached-geometry call is required for the current thirteen successful
separation certificates. A future overlap remains pending for the parent
within its exact pierced-profile/mesh method limit.

## Remaining scope

The **eleven original positive saved wire/timber intersections are preserved
verbatim as source records** in both setup and result. They are not queried,
relabelled or discharged by this supplement. Reviewed 104 geometry, the four
unadopted stacks, the 66 Hillman axes and the full 50-body authority retain
their existing scopes and source pins.

The 274 intended panel service interfaces retain their separate unsupported
profile-fit basis. Delivered electrical/T-nut profiles, barrel depth datum,
clocking and dimensional intervals remain unavailable where previously
unavailable. Machining and same-state relative loaded-motion margins remain
null; no universal tolerance, preload or 7.321-mm obstacle expansion is
introduced. No physical inspection is claimed or added as a requirement.
All criterion, complete-joint, adoption, catalog, delivered-hardware,
machining, loaded-motion, physical and fabrication qualification flags remain
false.

This leaf and its finite receipts remain active evidence for parent
integration. No prior packet, raw run, history or foreign work is pruned,
archived, altered or staged. Parent owns publication, staging and commits.
