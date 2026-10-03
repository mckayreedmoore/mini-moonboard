# Finite member opening refresh

## Status and parent API

**Finite comparisons complete in parent-run attempt02.** All 1,320 unique
signed cut limits and 1,632 duration comparison records are finite, with no
reference exceedance in the retained nominal methods. This does not establish
transverse splitting resistance or complete joint acceptance. The
[producer](member-opening-refresh.py) exposes `build(output)`. Import is inert.
`--prepare` authenticates saved sources and joins station identities using only
the standard library. No numerical helper is imported by preparation.

Preparation and arithmetic used Python **3.12.3** and NumPy **2.5.2**.
The workload is 1,320 signed cut limits and 1,632 duration comparison records;
each of the 24 physical cleat states supplies 96 exact bore-pressure profiles.

The successful run used parent serialization, from the repository root:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/member-opening-refresh.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/member-opening-refresh/attempt02
```

The API accepts only a new immediate child of
`rawlocal/member-opening-refresh/`. Existing output directories are refused.
It returns the `checks.json` dictionary. Only pure helpers from the existing
producers are called; their build, solve, coupon and test entry points are not.

## Authenticated inputs

[Preparation 02](rawlocal/member-opening-refresh/preparation02/preparation.json)
and its [receipt](rawlocal/member-opening-refresh/preparation02/receipt.json)
record **174 source pins**, including the producer itself. All matched before
and after the saved-source join and output writes. Preparation 01 remains
preserved as the earlier implementation snapshot. Preparation 02 records the
original prepared producer; attempt02 authenticates the current producer and
the same frozen engineering inputs.

| Binding | SHA-256 |
| --- | --- |
| Current producer | `53f5a40e71f33558a4d23a36846b66b4261e4cf9600896f7629d45012b9f68c2` |
| Prepared producer snapshot | `fcd344944837e35da376b16aec664499f454bc9f260ff425aa18a83e600099a0` |
| Attempt02 checks | `40beca5a3a5863612a0fadcee4b259f1edacf55f9c58035bc058918c1d64f7e8` |
| Attempt02 receipt | `1b31e5582c67c5374bbabcfbbd179957aea976701fbb991f41a0268084d3d694` |
| Preparation 02 | `5681322791e516465510fe63ff844465acce58315b68b4d36d8b74f84c283e6b` |
| Preparation 02 receipt | `5f1e43042856aead4fa427a3726e33fdbfb286c0b95862950b497328a65ffed6` |
| Current gravity assessment | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| Current frame comparison | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| Current frame response | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |
| Current physical corner replay | `e699b5c662992abab1f646236cdd4037feb425c5476458d8629899bcb9948976` |
| Frozen coverage ledger | `a9dc39d5dbd153c7928923caf79dcf678e653c0b707a35514e1177c8bd4337b2` |

The fresh member extraction and physical corner receipt provide the saved
provenance closure. Historical group and side-host receipts bind section
recipes and unchanged finished STEP identities. Their old forces and passes
are not transferred. The exact restored washer receipt is not a directly
consumed source in this closure; this producer never writes or repins it.

`build` reauthenticates the prepared closure before arithmetic, after
arithmetic, after result writes and after receipt write. The numerical context
must consume the same prepared closure. Any missing file, conflicting hash,
changed source, unmatched station or failed wrench recovery stops execution.

## Coverage matrix

These are the finite missing families identified by the
[frozen coverage audit](member-opening-coverage.md). Counts are simultaneous
signed cuts, with all six existing cases and both before/after limits.

| Body | Recorded stations | Signed limits | Duration comparison records | Demand interpretation |
| --- | ---: | ---: | ---: | --- |
| `top_outer_left_cleat` | 26 | 312 | 312 | Fresh physical cleat actions; original C_D=1 |
| `top_outer_right_cleat` | 26 | 312 | 312 | Fresh physical cleat actions; original C_D=1 |
| `bottom_outer_left_cleat` | 16 | 192 | 192 | Fresh physical cleat actions; original C_D=1 |
| `bottom_outer_right_cleat` | 16 | 192 | 192 | Fresh physical cleat actions; original C_D=1 |
| `base_side_left` | 13 | 156 | 312 | Fresh saved point actions; original C_D=1 and existing C_D=1.25 scenario |
| `base_side_right` | 13 | 156 | 312 | Fresh saved point actions; original C_D=1 and existing C_D=1.25 scenario |
| **Total** | **110** | **1,320** | **1,632** | **All finite; no retained reference exceedance** |

### Completed numerical result

Attempt02 returned `COMPLETE_FINITE_COMPARISONS`. Its 174 source pins and six
output hashes matched independently after execution. Every retained normal,
tension, compression, shear and torsion comparison is finite and at or below
one. The governing sufficient combined shear bounds are:

| Family | Duration factor | Maximum bound / Fv |
| --- | ---: | ---: |
| Four outer cleats, governing top-right | 1.0 | 0.334554 |
| Left side host | 1.0 | 0.691133 |
| Right side host | 1.0 | 0.682198 |
| Left side host | 1.25 | 0.552906 |
| Right side host | 1.25 | 0.545758 |

The two side-host evaluated face peaks at C_D=1.25 are 0.523968 and 0.528352.
These are nominal section comparisons using the demand interpretations below,
not splitting capacities or a physical pressure solution for the side hosts.

Attempt01 completed the arithmetic but stopped while serializing NumPy integer
counters into summary JSON. Its snapshot, partial outputs and stop record are
preserved. The only producer changes convert the two Boolean counter sums to
ordinary integers; geometry, loads, methods and reference values are unchanged.
Attempt01 supplies no accepted numerical receipt.

### Four cleat grain families

The 84 stations come directly from the frozen audit's uncalculated finished
opening list. This finite packet does not claim a continuous station maximum,
refresh all 49,964 historical grain cut limits, or repeat the historical
transverse-plane fracture worksheet.

`knee-bridge-remaining-sections.py:actions_for` authenticates the source member
forces against current response rows, D and W, including free couples and
gravity/live load mapping. Each fresh corner state's 20 saved weight nodes
must match that source individually; weight is used once.

`corner-group-finish.py:pressure_profiles`, `partial_wall` and `cut_material`
supply the unchanged half-cosine radial bore-pressure method and exact cut
integrals. The 96 bore station resultants per state are replaced by those
profiles. The other physical actions retain their recorded points. Full bore
force/moment recovery, whole-cleat balance and opposed-half balance are
checked under the existing tolerances; no balancing couple is introduced.

`corner-timber-sections.py:section` supplies the retained rectangles. Its area
is cross-checked against the exact plane integral. The existing
`corner-net-section.py:nominal_section` carries the complete signed wrench
through those regions and recovers that wrench after centroid translations.
The material references retain each body's existing CF recipe, checked
against the pinned material input. Normal, transverse shear and full torque
comparisons use the existing common-strain, area-sharing and common-twist
hypotheses.

### Two side-host opening families

The historical packet supplies exactly 13 section recipes per side. Its STEP
hashes and station indices must match the current member extraction and the
frozen uncalculated set. Current response forces, all recorded moment arms,
all free couples and mapped body loads enter demands.

`top-host-net-sections.py:global_cut` reproduces every complete signed cut
against the fresh saved negative-grain array. The existing
`knee-bridge-top-rail.py:duration_results` reuses the original nominal section
and signed rectangle-face comparisons at C_D=1 and C_D=1.25. This is the
original point-placement interpretation for side hosts. A physical pressure
interpretation of those hosts would require replacing each complete corner
interface once and recovering its wrench; this packet does not claim that
interpretation.

## Explicit outcomes and outputs

All 1,320 target limits now have finite comparison records. Preparation alone
supplied source and coverage identities; the accepted attempt02 supplies the
numerical results.

Build writes:

- `checks.json`: every cut/duration summary, seven original normal/shear/torque
  metrics, three additional side-host face/bound metrics, explicit metric
  outcomes, counts and maximum witnesses. Its `coverage_matrix` separates
  each body and duration.
- `cuts.jsonl.gz`: retained section recipes, complete signed local cuts,
  regional recovery, longitudinal corner comparisons and side-host signed
  face vectors for every duration.
- `action-audits.json`: current force/load bindings and the physical cleat
  actions and bore-pressure profiles actually consumed.
- `preparation.json`, `producer.py.snapshot`, `.gitignore` and `receipt.json`:
  source closure, exact implementation, output hashes and before/after
  authentication.

Every metric has an explicit finite value and disposition, or
`UNCALCULATED`. Missing or nonfinite values never count as a pass. Above-one
sufficient shear bounds remain distinct from an evaluated face that exceeds
Fv and from nominal normal or torsional reference exceedances. Successful
arithmetic can be complete while reporting exceedances; completion does not
mean every comparison is at or below one. Nulls keep the target set open.

The complete nominal signed wrench, regional recovery and same-state
normal/shear/torque results remain available; component maxima are not
combined across different cases. The original normal reference sum remains
the existing diagnostic, without a new resistance or interaction rule.

## Genuine remaining comparison scope

The complete finite result removes 1,320 signed limits from the frozen gap.
The remaining inventory is **12,624
finished-opening traces at 1,052 stations**, plus **264 unmachined exclusion
traces at 22 stations**. All are on the 20 frame bodies. The unchanged 1,176
terminal traces at 98 stations remain inapplicable to the point-load rectangle
method, with no vanishing-area strength ratio fabricated.

| Remaining frame body family | Finished-opening signed traces | Unmachined exclusion traces |
| --- | ---: | ---: |
| Two compact floor members | 624 | 0 |
| Header beyond six refreshed paired-bore centers | 936 | 0 |
| Two center posts | 576 | 0 |
| Two outer posts | 864 | 0 |
| Two principal members | 2,448 | 0 |
| Bottom left/right rails | 1,284 | 0 |
| Four service rails | 2,568 | 0 |
| Top rail beyond its physical four-bore refresh | 372 | 144 |
| Two side hosts beyond these 26 stations | 2,304 | 120 |
| Two rear legs' retained bores | 648 | 0 |
| **Total** | **12,624** | **264** |

Preparation retains the exact remaining body/station/feature identities in
`future_if_targets_finite.remaining_station_identities`. No additional
comparison obligation is inferred from generic formal-pending labels.

After this build, the smallest next reusable arithmetic is the header's
existing paired-bore shoulder/interior stations, followed by other finished
frame bore, screw and passage sections for which an exact finite recipe can
be joined. Existing saved signed actions and section helpers remain the
starting inputs. The 1:12 rear-leg taper already has bore-free reduced-section
comparisons; its surviving 648 bore traces remain in the list above. The
historical square notch is not a second surviving recess requiring a new
nominal strength check. Splitting and tangential fracture remain the peer's
scope; global stability and permanent-load comparisons remain the parent's.

## Preparation checks and retention

Preparation used stdlib authentication/coverage joins, AST parsing and Ruff.
The parent subsequently executed the finite engineering arithmetic and checked
all source and output hashes. No CAD, native solver, new frame run, software
tests or review loop was performed. Existing coverage leaves, historical
attempts and source evidence remain unchanged.

Only the two new producer/document leaves and their ignored raw output are
owned here. Preparation snapshots remain active provenance for parent
execution. No source, temporary file or historical evidence was removed.
