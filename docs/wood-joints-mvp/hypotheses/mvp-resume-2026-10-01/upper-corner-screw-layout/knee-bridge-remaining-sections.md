# Fresh knee-bridge finite opening-section comparisons

## Implementation status and parent API

[The producer](knee-bridge-remaining-sections.py) exposes `build(output)`.
The parent completed all three finite families in one serialized saved-action
calculation. No original producer pipeline, coupon, software test, native
mechanics, CAD rebuild, frame run or review loop ran. Completion establishes
the named nominal comparisons, with the limits below.

`output` must be a new immediate child of
`upper-corner-screw-layout/rawlocal/knee-bridge-remaining-sections/`.
For example, from the repository root, the parent can load the file by path:

```python
import importlib.util
from pathlib import Path

u = Path("docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout")
spec = importlib.util.spec_from_file_location("fresh_remaining_sections", u / "knee-bridge-remaining-sections.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
receipt = module.build(u / "rawlocal/knee-bridge-remaining-sections/attempt01")
```

Existing output children are preserved. The return value reports overall
status, family status and gaps, completed finite limit counts, same-state peaks,
and hashes of `checks.json` and `receipt.json`. A missing geometry API or a
failed family accounting assertion leaves an explicit family gap and preserves
its partial worksheets. The other families continue independently. Partial
worksheets never count as completed family results. Source authentication
failures stop the build and cannot produce a complete receipt.

## Original finite families

| Family | Geometry recipe | Expected fresh limits |
| --- | --- | ---: |
| Six header cleats | `header-cleat-net-sections.py`: `opening_geometry`, `subset_section`; all original recorded stations | 1,968 |
| Remaining twelve blocks | `remaining-net-sections.py`: `geometry`; `corner-timber-sections.py`: `section`; original bore/tangency stations | 2,304 |
| Header paired bores | `header-net-section.py`: `section_geometry`; six original disconnected section identities | 72 |

The shared `corner-net-section.py` calculator supplies `nominal_section` and
its unchanged rectangle torsion method. The original
`remaining-net-sections.py:cut_summary` retains finite same-state normal and
shear indices. No original `build`, `run`, `main`, coupon or test API is called.
No new stations, continuous-section search, pressure method, geometry, strength,
hardware scenario, material law or load variant is introduced.

The cleat family preserves the deliberately retained rectangle subsets around
longitudinal circular holes. The remaining blocks preserve their full rectangle
minus transverse bore-chord sections. The header preserves its three actual
rectangular ligaments at each paired bore, actual section centroid and unchanged
X-grain/Y/Z section frame; the recorded rotated radial/tangential assignment
does not become a new shear-modulus model.

## Fresh source authority and accounting

The fixed loads remain 250 lb multiplied by two, signed 300 N horizontal load
and the original 100 mm hold lever. The fresh dead-load factor is
`1.1110134616260479`. All six nominal-gap cases remain simultaneous signed
states. Geometry recipes and historical section outputs supply no accepted
load results.

| Fresh source relative to the resume folder | SHA-256 |
| --- | --- |
| `member-screen-attempt02/knee-bridge-gravity01/member-results.json` | `5178d1a246aa04044429c1c2bc81709214ae9abd713313d07a949a2848de3dd0` |
| Same folder: `action-section-arrays.npz` | `3be032470253e872690637b09566076256374071adfe7d057ed4d329debef596` |
| Same folder: `geometry.json` | `c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af` |
| Same folder: `inputs.json` | `34219c91e8b23588f76f4e2e2b6c564b25e1b979ccd4106dd0002c9f03cc0457` |
| `upper-corner-screw-layout/rawlocal/knee-bridge-frame/attempt02/response/comparison.json` | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| Same response folder: `response.npz` | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |
| `upper-corner-screw-layout/rawlocal/knee-bridge-gravity/attempt01/operator-assessment.json` | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |

The producer authenticates the fresh extraction's source manifest, its output
bindings, gravity operator outputs, comparison/response binding, unchanged
helper bytes, historical geometry/material contract and finished STEP bytes.
It reauthenticates sources before and after output publication. The fresh
extraction's recorded missing historical artifact stays visible; this producer
does not reconstruct it or invoke its original producer.

Every consumed mechanical action is independently checked against its current
signed response row and the complete `-D` body projection. Moments about the
physical node mean are converted from N·m to N·mm; the point lever arm is
subtracted to recover the saved free couple. Ownership, source ID, receiver,
role, point and row sign must agree, with every incident mechanical row present
once. Discrete body loads retain their saved physical node points and zero free
couples. Their complete wrench must match the fresh gravity/live `W` load
operator with the new dead factor, and the fresh member receipt.

Whole-body equilibrium and opposed-half source traces retain the original
0.1 N / 2 N·mm closure limits. Independent source-action cut restoration uses
1e-7 N / 1e-5 N·mm limits. Reconstructed regional wrenches use
1e-7 N / 1e-6 N·mm limits. These are accounting limits, not physical accuracy
or timber capacity. The existing material references are authenticated against
their original DF-L No. 2 base properties and recorded CF scenario. The pinned
original `four-screw-layout01/member-results.json` supplies only the original
conditional material recipes, including those of the twelve remaining blocks;
no historical cut forces or stress indices are consumed from it.

## Header point-placement assumption and full torque

Fresh direct cuts use the original nominal point-placement method. Each saved
force acts at its recorded lateral-plane origin, contact-cell point or body-load
node, with its entire saved free couple at that point. A grain station partitions
the complete action; `before` excludes coincident actions and `after` includes
them using the existing 1e-6 mm convention. No action is partially assigned to
a cut by a pressure footprint.

For the header, the full fresh array wrench at the source grain-axis datum is
translated to the actual saved net-section centroid. A separate sum of fresh
negative-half point forces, lever-arm moments and free couples at that centroid
must reproduce it. Historical header traction-map forces are never loaded or
transferred. The exact source placement is a nominal method assumption; it does
not establish physical bore-wall or washer pressure placement.

Both full A1-rear traces at the 133.35 mm left-knee paired-bore section remain
in `full_A1_rear_133_35mm_torque_witness`, including all six signed components,
actual centroid translation, regional reconstruction and separate role wrenches.
The torque is freshly computed; historical torque values are not targets.

## Machine outputs and applicability limits

`checks.json` retains family completion/gaps, original finite counts, every
same-state summary, family and body peaks, counts above one, source balances,
section recipes, saved exact-area crosschecks and the full A1-rear witness.
Each family's compressed `*-cuts.jsonl.gz` worksheet retains the full nominal
section, regional/corner indices and six-component regional wrench recovery,
source trace index, included point indices, cut datum and cut-restoration
residuals. Its `*-actions.jsonl.gz` file supplies the fresh point actions and
source audit for each body/case. `sources.json`, `receipt.json` and
`producer.py.snapshot` bind consumed sources and produced files.

These finite comparisons retain common longitudinal strain, grain-end bridges,
area-proportional transverse sharing, equal longitudinal shear moduli, common
regional twist and nominal free warping. Artificial cleat rectangles can omit
sound wood and do not bound actual local stresses. Indices below one record only
the declared nominal reference comparisons.

No redistributed top, bottom or knee joint load is inferred from these global
actions. Local pressure, notch/bore concentration, perpendicular-tension
resistance, group/splitting qualification, endbridge capacity, stability,
delivered parts, fabrication and complete-joint acceptance remain unsupported.
The global source's filled-bore stiffness idealization, conditional connector
laws, nonunique seating, accessory allowance and no-slip floor assumption remain
visible. Qualification and release flags remain false.

The code and this API description remain active for the parent's single
serialized calculation and integration. Generated worksheets remain in the
owned ignored raw folder; no existing source or historical output is archived
or pruned by this implementation.

## Completed parent result

`rawlocal/knee-bridge-remaining-sections/attempt01/` contains all **4,344
signed limits**. The parent authenticated **149 source pins and ten receipt
artifacts**. All reported reference indices are below one.

| Family | Limits | Normal diagnostic peak | Same-state shear/torsion bound |
| --- | ---: | ---: | ---: |
| Six header cleats | 1,968 | 0.020888 | 0.137945 |
| Remaining twelve blocks | 2,304 | 0.001795 | 0.032102 |
| Header paired bores | 72 | 0.163057 | 0.348582 |

The paired-header tension/compression/bending ratios are separately
**0.254047 / 0.127237 / 0.162102**. Its A1-rear after-limit torque remains
**−12.767797 N·m**, with the complete simultaneous wrench and opposite limit
retained. Family source restoration and regional recovery use the original
tolerances. No physical pressure redistribution, splitting capacity or
complete-joint acceptance follows from the nominal indices.

| Artifact under the completed child | SHA-256 |
| --- | --- |
| `checks.json` | `f519ecc04af7622ec5637162b7a86d6a88e6478e2b15332bf566e6d0e5a3d4c3` |
| `receipt.json` | `e1796242c3ede025927db911af73b69d226ddd7b7e03aa621f77a548a4f322d0` |
| Executed producer | `e2a08ca075fdb397696889d22d8cbbfb30d83a3d4bb5e3af1726574c38ca2e15` |
