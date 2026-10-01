# Independent calculation review

**Disposition:** the frozen output matches the separate NDS closed-form
single-shear equations under the packet's conditional end-grain main-member
interpretation. All source rows and axis geometry records remain unchanged.
This validates the arithmetic and source copying; it does not establish an
adopted resistance or joint acceptance.

## Independent replay

I checked the parent's 210-row result against the pinned 52-axis source and
ten-axis role-census records. All 210 state keys match exactly, and every
inherited source state field—including both signed receiver-force vectors,
their resultant and angles, the source exclusion/null-reference fields, and
the separately reported outer tie—is unchanged. The new axis geometry and
grain records equal the pinned role-census records. All reported source path
and SHA-256 pins authenticate.

For the equation check, this verifier imports only `nds_modes` and the acute
angle helper from the earlier independent closed-form verifier. It does not
import the production quadratic single-shear or wood-bearing helpers. For
each state it re-derives the main and side roles from the axis and source
grain vectors, recomputes the side member's actual load-to-grain angle and
Hankinson bearing value, converts each modeled interval from millimetres to
inches, and independently recalculates all six yield modes using
`Fe,main = 4,450 psi`, the angle-dependent side `Fe`, `D = 0.25 in`,
`Fyb = 45,000 psi`, zero gap, and `theta = 90 degrees` (`Ktheta = 1.25`).
The end-grain main role appears on five modeled head-seat sides and five
modeled nut-seat sides; role assignment follows the grain relationship, not
the endpoint label.

The replay checked **1,260 raw mode values** and **1,260 values after one
`Ceg = 0.67` multiplier**, then checked each governing value and lateral-only
demand/reference ratio. Maximum relative differences were:

| Check | Maximum relative difference |
| --- | ---: |
| Raw modes, lbf | `7.910789410126054e-16` |
| Raw modes, N | `8.793598505998266e-16` |
| `Ceg`-only modes | `8.047765704334135e-16` |
| Ratios | `4.335372706600755e-16` |

The largest conditional comparison in these three saved response cases is
`center_principal_header_left_2`, K12 rear, full load: **120.091599 N /
396.632330 N = 0.302778140**, Mode IV. No state ratio exceeds one. These are
not fully adjusted design ratios and do not constitute pass/fail criteria.
The outer tie remains outside the lateral demand numerator.

## Applicability limits

The role extension is explicitly an engineering interpretation: AWC's
explanatory main-member guidance is extended to the main-member-specific
end-grain provisions; the pinned NDS text does not state that interpretation
verbatim. The computed comparison is conditional on that interpretation and
on a smooth full-body quarter-inch scenario. The model records a nominal
6.35 mm shaft, but that does not establish a delivered bolt's NDS diameter,
thread/root bearing diameter, or bending-yield value. In particular,
the `45,000 psi` scenario is **not qualified** for a quarter-inch bolt by the
tabulated full-body value or the cited larger-diameter example.

The source supplies proposed grain maps and modeled CAD bearing intervals,
not inspected wood or measured bearing length. The method does not complete
the contact, spacing, edge/end-distance, material, adjustment-factor,
splitting, tear-out, axial/lateral/bending interaction, washer/contact, or
complete-joint checks. It covers three saved response cases, not a six-case
envelope. No native solve, physical work, or acceptance change was made.

## Pinned bytes and replay

| Record | SHA-256 |
| --- | --- |
| End-grain producer | `8e10846bf008430b7e5e30c484c20624bbaa71a6addc74a63bd17b1445c229b8` |
| Role-census producer | `a8bd7797b1f46c11f0a9603c5a2fa87742bf9d39e99e0db33942546216ec664c` |
| Parent end-grain result JSON | `29854f8b333fd952fab92788517fad1af64a9a807be5b0c134fc1bc47756779f` |
| Role-census result JSON | `5ec2ef3f76dbc7eab0a7a83ae7a5007ff7caec77da56418641208e29846bb16c` |
| Upstream 52-axis result JSON | `6551861db1112c91b87c5705bbceb3bb26f55f0d7e70029a74d828519425145e` |
| Independent closed-form oracle | `848e65019ad87dfb7ad07916f845511e1fe78931df070b5242161a79af133e54` |
| NDS-2024 Chapter 12 PDF | `5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a` |
| Parent README reviewed | `d06973946933326d9f0a4b02c090007f54d22d67dc2cb279cacedaee7879fe17` |
| This verifier | `71ecdc282c4c4ed552ef53c3b95271dcb6dfa191733acbe7566e0eb233a2392c` |

Recreate the role-census input from the frozen upstream 52-axis result, then
replay the independent calculation verifier from the repository root:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/end-grain-single-shear-method-2026-10-01/role_census.py \
  --source-report /tmp/remaining-single-shear-reference-2026-10-01.json \
  > /tmp/end-grain-role-census-2026-10-01.json
.venv/bin/python docs/wood-joints-mvp/hypotheses/end-grain-single-shear-method-2026-10-01/parent_verify.py \
  --report /tmp/mini-moonboard-end-grain-reference-2026-10-01.json \
  --source-report /tmp/remaining-single-shear-reference-2026-10-01.json \
  --census-report /tmp/end-grain-role-census-2026-10-01.json
```

The result is `PASS_INDEPENDENT_END_GRAIN_CLOSED_FORM_CEG_ARITHMETIC_ONLY`.

## Final full-producer replay and README review

I also ran the producer separately against the README's exact upstream input
path, directing output to a distinct temporary file. The replay output was
byte-identical to the parent's pinned result; both hash to
`29854f8b333fd952fab92788517fad1af64a9a807be5b0c134fc1bc47756779f`.
This re-exercises the role-census API and producer together, beyond comparing
the saved arithmetic output.

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/end-grain-single-shear-method-2026-10-01/produce.py \
  --source-report /tmp/mini-moonboard-remaining-single-shear-reference-2026-10-01.json \
  > /tmp/mini-moonboard-end-grain-reference-independent-replay-2026-10-01.json
sha256sum /tmp/mini-moonboard-end-grain-reference-independent-replay-2026-10-01.json
cmp -s /tmp/mini-moonboard-end-grain-reference-2026-10-01.json \
  /tmp/mini-moonboard-end-grain-reference-independent-replay-2026-10-01.json
```

The final parent README reviewed is pinned to SHA-256
`d06973946933326d9f0a4b02c090007f54d22d67dc2cb279cacedaee7879fe17`.
Its 210-row count, highest comparison (`0.302778140`, Mode IV), next-largest
ratio (`0.290076202`), five/five modeled seat-side split, source-row
preservation, 1,260 raw and once-adjusted mode counts, and maximum relative
mode differences agree with the authenticated records and replay above. The
document keeps the main-role extension identified as an engineering
interpretation, the quarter-inch `Fyb` scenario explicitly unqualified, and
the result outside joint/pass/failure claims. The 10-test and full-folder Ruff
pass statement is the parent's recorded verification; I did not rerun those
already-passed checks. No native solve was run.
