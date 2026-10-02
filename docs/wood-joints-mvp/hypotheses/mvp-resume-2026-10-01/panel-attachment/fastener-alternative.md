# One stock fastener alternative: GRK RSS 5/16 × 2½ inch

**Decision: this option does not close the panel joint at the saved forces.**
The carbon-steel GRK RSS, part **12217** (100-pack), is a concrete same-length
option if the owner permits replacing the purchased Hillman screws. A proposed
66-screw substitution would preserve the stations and count. It is not selected.
The [manufacturer listing](https://www.grkfasteners.com/grk-products/structural-framing-screws/rss-rugged-structural-screw)
identifies that size and part. No resistance or installation rule is transferred
to Hillman, SPAX, or SDS hardware.

## Basis and applicability

[ICC-ES ESR-2442](https://icc-es.org/wp-content/uploads/report-directory/ESR-2442.pdf),
revised March 2026, Table 1, supplies these carbon-steel RSS inputs:

| Quantity | Value |
| --- | ---: |
| Underhead length / rated thread length, including tip | 63.5 / 38.1 mm |
| Shank / outside thread / root diameter | 4.953 / 7.010 / 4.242 mm |
| Circular washer-head diameter | 15.748 mm |
| Minimum bending yield strength | 171,800 psi |
| Steel ASD tension / shear strengths | 5667 / 3932 N |

The [manufacturer drawing](https://www.grkfasteners.com/getmedia/f67510e0-6c64-4904-8bf0-a2387c5e9502/GRK-RSS-Customer-Drawing_1.pdf?ext=.pdf)
gives nominal head height 3.988 mm, shoulder diameter 7.645 mm and T30 drive.
Its thread length is 1.57 inches; this screen uses the report's smaller
1.50-inch thread length, rather than combining the two sources favorably.

**An applicable complete plywood connection rating is absent.** ESR-2442
§3.5 covers sawn lumber, glulam and CLT, excluding other engineered products;
§4.2.3 requires at least 19.05 mm side thickness. The modeled plywood is
18.25625 mm. Its penetration rule also fails here: with permitted tip
`E=2Dr=8.484 mm`, penetration excluding tip is 36.760 mm, below
`6D=42.062 mm`. Consequently the following plywood lateral and head numbers
are **generic diagnostic extensions, not available rated connection capacities**.

## Resistance screen using unchanged attempt08 forces

The input is the existing 792 simultaneous screw records: six cases × two
gap states × 66 axes. Receiver identities and forces are reused unchanged.
DF-L remains `G=.50`; modeled tip penetration is 45.24375 mm. No new sharing,
stiffness, frame solution or seating-motion envelope is inferred.

[NDS Chapter 12](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf)
provides the generic head, lateral and combined equations. The head calculation
uses the entire 18.25625 mm net thickness, with no countersink deduction.
The contacting-member lateral calculation uses `Dr=.167 in`, `Fyb=171800 psi`,
timber `Fe=4650 psi`, plywood `Fe=3350/4650 psi`, and main bearing length
`p-E/2=41.002 mm`. ESR-2442 uses `Ds=.195 in` for the reduction-table footnote,
so all six yield modes use `Rd=2.2`, without `Kθ`.

| Diagnostic reference | Other/unknown plywood | Structural I/Marine hypothesis |
| --- | ---: | ---: |
| Circular head pull-through, NDS §12.2.5 | 758 N | 1074 N |
| Lateral, minimum of six yield modes | 606 N, IIIs | 687 N, IIIs |

Table 2's withdrawal values are 165 and 227 lbf/in at timber SG .42 and .55.
With the report's 1.50-inch thread these give **1101 and 1515 N**. Neither
endpoint is the recorded DF-L SG .50; no interpolation is adopted. The larger
endpoint is used below solely as an explicitly favorable diagnostic reference.
Even that endpoint cannot carry the governing saved timber-withdrawal demand.

For each simultaneous tuple, use `R=hypot(V,T)` and
`I=V²/(R Z)+T²/(R A)`, with `A=W×thread length`. Head transfer is checked
separately. All adjustment multipliers are set to one for this comparison;
[NDS Chapter 11](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf)
governs end-use adjustments. No favorable duration factor is selected.

| Same-state result, using favorable 1515 N withdrawal and 687 N lateral diagnostics | Zero gaps | Modeled gaps |
| --- | ---: | ---: |
| A12-rear, upper-left `edge_2`: T / simultaneous V | 1911.837 / 730.822 N | 1836.884 / 807.662 N |
| That screw: T / favorable withdrawal reference | 1.262 | 1.213 |
| That screw: T / favorable head diagnostic | 1.780 | 1.710 |
| That screw: combined withdrawal term alone | 1.179 | 1.110 |
| Maximum combined index across all 396 screws | 1.647 | 1.847 |
| Records with combined index above one | 10 | 10 |

The zero-gap combined maximum is A12-rear upper-left `rim_4`, with
`V=1130.854 N, T=770.431 N`. The modeled-gap maximum is K12-rear upper-right
`rim_4`, with `V=1274.054 N, T=625.635 N`. These are different tuples from the
withdrawal maximum. Two tuples in each gap set have withdrawal term at least
one even under the favorable diagnostic; no finite lateral reference can
make those fixed tuples meet the combined equation. Four reference scenarios
on all 792 records give 3168 comparisons; no independent peaks are paired.

The **lower-left main panel is also an affected duty**: A1-rear, modeled
gaps, `round_panel_lower_left_edge_2` into `base_rail_bottom_left` carries
`T=993.956 N` and simultaneous
`V=396.596 N`. It exceeds the largest existing Hillman head diagnostic,
628.941 N, by a factor of 1.580. For this RSS sizing screen its head ratios
are 1.311 / 0.925 at the two plywood hypotheses, and its favorable combined
index is 0.823. These favorable individual numbers do not cure RSS's missing
plywood applicability or accept that lower joint. All four main panels and
both kickers were included in the 792-record census. The parent now treats
all four main panels in its separate edge-restraint statics; kicker duties
remain separate, and no compatible frame with a correction exists yet.

## Required changes and next decision

This substitution would require a wider screw bore envelope, a 15.748 mm
supported head seat, and T30 access at all retained stations. The existing
3/8-inch face-countersink tool does not establish that seat or permit embedding
the new head. Increasing countersink depth would reduce the head diagnostic.
The report's DF-L lead-hole range is 2.972–3.715 mm: the existing 1/8-inch
pilot lies inside that range, but existing holes, backing, edge/end distances
and head clearance have not been inspected or qualified for RSS. Report
Table 5 detailing and group/member limits would still apply.

Do not select part 12217 as a standalone correction. Its head and withdrawal
diagnostics already miss the demands by substantial amounts, and its complete
plywood/lateral applicability is absent. This one-option result does not rule
out all stock fasteners. The parent owns the alternative edge-restraint load
path; that proposal must address lateral sharing as well as normal restraint.
Any changed fastener would require its own compatible force allocation.
Reviewed geometry, 66 purchased-Hillman policy, source evidence, all 47 formal
criteria and all joint/release HOLD boundaries remain unchanged.

## Reproduction and pins

Run from the repository root. This is component arithmetic only, with the
existing generic six-mode helper; it runs no frame, CAD, native solve or tests.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import csv, hashlib, math
from pathlib import Path
from fea.dowel_yield import single_shear
p = Path('docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/panel-attachment/results/attempt08-all-two-receiver/screw-states.csv')
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'a074b374f487ed05865a20c62f5395898338ceb9bce6f2e204406e84316d2e51'
rows = list(csv.DictReader(p.open()))
assert len(rows) == 792 and len({r['axis_id'] for r in rows}) == 66
n, dr, fyb = 4.4482216152605, .167, 171800
t, penetration, tip = 18.25625/25.4, 45.24375/25.4, 2*dr
for fe, g in ((3350, .42), (4650, .50)):
    result = single_shear(
        main_length_in=penetration-tip/2, side_length_in=t,
        main_bearing_lb_in=4650*dr, side_bearing_lb_in=fe*dr,
        main_yield_moment_lb_in=fyb*dr**3/6,
        side_yield_moment_lb_in=fyb*dr**3/6, gap_in=0,
        reduction_terms=dict.fromkeys(('Im','Is','II','IIIm','IIIs','IV'), 2.2))
    z = result['reference_lateral_lbf']*n
    head = 690*math.pi*.620*g*g*t*n
    print('diagnostic Z/head/mode', z, head, result['governing_mode'])
    for w in (165, 227):
        a = w*1.5*n
        for gap in (0, 1):
            states = []
            for r in rows:
                if float(r['gap_scale']) != gap:
                    continue
                v, tension = float(r['lateral_resultant_n']), float(r['withdrawal_n'])
                resultant = math.hypot(v, tension)
                b = tension*tension/(resultant*a) if resultant else 0
                i = v*v/(resultant*z)+b if resultant else 0
                states.append((i, b, r))
            peak = max(states, key=lambda x: x[0])
            print(fe, w, gap, 'I', peak[0], peak[2]['case_id'], peak[2]['axis_id'],
                  'above1', sum(s[0] > 1 for s in states),
                  'no_finite_Z', sum(s[1] >= 1 for s in states))
PY
```

The five external primary sources used above were read on October 2, 2026.
Retained downloaded PDFs and exact source/output pins:

| Artifact | SHA-256 |
| --- | --- |
| `/tmp/panel-alternative-ESR-2442-2026-10-02.pdf` | `f3e988d93912e7866c173276463b50c4642542cd82c24fd539c7d1e9ae474229` |
| `/tmp/panel-alternative-GRK-RSS-drawing-2026-10-02.pdf` | `100f4c3109095808f20227dfcd7556fd69e65c8ba1242bbc7ad5e0d21df50de4` |
| Pinned `source-cache/chapter12-2024-awc-20260911.pdf` | `53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f` |
| Pinned `source-cache/chapter11-2024-awc-20260911.pdf` | `45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33` |
| Existing `fea/dowel_yield.py` | `d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45` |
| Attempt08 `comparison.json` | `7146069ad3ecf913cbb354f3a37d1e6af6768fc3b577f574feb5a10bd483eb2f` |
| Attempt08 `screw-states.csv` | `a074b374f487ed05865a20c62f5395898338ceb9bce6f2e204406e84316d2e51` |
| Attempt08 `receipt.json` | `fd0ea72c61bd3ff8bc7295b68a639d5f9ef9174e119bb8f4cd03d2bf8ff34217` |

The caches are in `../../upper-block-strength-2026-10-01/source-cache/`.
Earlier lookup downloads, all frozen leaves and referenced `/tmp` evidence
are preserved. No helper, review loop, staging or commit was used.
