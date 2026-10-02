# Conditional grain-aware panel sheet placements

Completed rectangular arithmetic, 2026-10-02. These are cutting **options** for
the unchanged six source panel envelopes, not a purchased-sheet assignment,
selected cut plan or fabrication release. Four main blanks remain
1217.6125 X × 1219.2 T × 18.25625 N mm; two kicker blanks remain
1217.6125 X × 277 T × 18.25625 N mm. No panel, member or fastener count changes.

Sheet coordinates are **L along declared factory face grain** and W across
grain. Nominal 4×8 sheets have L = 2438.4, W = 1219.2 mm. Nominal 4×4 sheets
have L = W = 1219.2 mm, but their grain direction still needs identification:
the square outline supplies no material axis. The Roseburg AC fir purchase
identity in [purchased materials](../../../../purchased-materials.md) remains
known; actual usable sheet dimensions, grade/group and grain placement remain
unobserved. These nominal rectangles do not establish compatibility with the
retailer-listed usable width.

The frozen elastic model assumes strong T for all six panels. For main panels
that is the board-slope direction, perpendicular to X. For kickers it is the
vertical direction. Every option here retains kicker strong T. Main strong X
is a different response orientation; rotating an already cut rectangular main
blank does not preserve the exact X/T envelope.

## Sheet counts and matched axes

| Nominal sheets | Kerf, mm | Main strong axis | Sheets | Match frozen main axes? | Placement |
| --- | ---: | --- | ---: | --- | --- |
| 4×8 | 3.175 | X | 3 | No | Two paired-main sheets; one kicker sheet |
| 4×8 | 3.2 | X | 4 | No | One main per sheet; both kickers in first remainder |
| 4×8 | 3.175 | T | 4 | Yes | One main per sheet; both kickers in first remainder |
| 4×8 | 3.2 | T | 4 | Yes | One main per sheet; both kickers in first remainder |
| 4×4 | 3.175 | X | 5 | No | Four main sheets; one kicker sheet |
| 4×4 | 3.2 | X | 5 | No | Four main sheets; one kicker sheet |
| 4×4 | 3.175 | T | 5 | Yes | Four main sheets; one kicker sheet |
| 4×4 | 3.2 | T | 5 | Yes | Four main sheets; one kicker sheet |

These counts are minimums for the axis-aligned rectangular envelopes and
specified grain assignments, not a general nesting optimization for profiled
parts. Two mains cannot fit across W in either orientation. Along L, two
strong-X mains need 2 × 1217.6125 + kerf: exactly 2438.4 mm at 3.175 mm kerf,
but 2438.425 mm at 3.2 mm kerf. Two strong-T mains need
2 × 1219.2 + kerf and cannot fit either 4×8 option. The paired-main sheets
leave no kicker-sized region. On 4×4 sheets, a main leaves no kicker-sized
region, so a fifth sheet is necessary.

## Explicit rectangular placements

M1 = `main_lower_left`, M2 = `main_lower_right`, M3 = `main_upper_left`,
M4 = `main_upper_right`; K1 = `kicker_left`, K2 = `kicker_right`.
All W starts are zero; all coordinates are after any retained-edge trimming.
Kerf k separates successive retained blanks along L.

| Body orientation | Size along L × W, mm |
| --- | --- |
| Main strong X | 1217.6125 × 1219.2 |
| Main strong T | 1219.2 × 1217.6125 |
| Kicker strong T | 277 × 1217.6125 |

- **4×8, strong X, k = 3.175:** sheet 1 has M1 at L = 0 and M2 at
  L = 1220.7875; sheet 2 has M3 at L = 0 and M4 at L = 1220.7875.
  Sheet 3 has K1 at L = 0 and K2 at L = 280.175.
- **4×8, strong X, k = 3.2:** sheet 1 has M1 at L = 0, K1 at
  L = 1220.8125 and K2 at L = 1501.0125. Sheets 2–4 respectively have
  M2, M3 and M4 at L = 0.
- **4×8, strong T, either kerf:** sheet 1 has M1 at L = 0, K1 at
  L = 1219.2 + k and K2 at L = 1496.2 + 2k. Sheets 2–4 respectively have
  M2, M3 and M4 at L = 0.
- **4×4, either main orientation/kerf:** sheets 1–4 respectively have
  M1–M4 at L = 0. Sheet 5 has K1 at L = 0 and K2 at L = 277 + k.

The first four-sheet remainder uses different body-to-sheet orientations when
mains are strong X: the mains' X runs along L, while kickers' X runs across W.
Both kicker T axes still run along factory grain. This arrangement is possible
without changing the panel envelopes or joining pieces.

## Conditional trim limits

Budgets below are **combined losses at both ends or both edges**, not
allowances at each edge. Each sheet must retain at least its occupied L/W
dimensions, including internal separation kerfs. Zero budget means factory
size and retained edges must supply the exact envelope without cleanup loss.

| Option / sheet role | Combined L trim budget, mm | Combined W trim budget, mm |
| --- | ---: | ---: |
| 4×8 strong X, 3.175; each paired-main sheet | 0 | 0 |
| 4×8 strong X, 3.175; kicker-only sheet | 1881.225 | 1.5875 |
| 4×8 strong X, 3.2; main + both kickers | 660.3875 | 0 |
| 4×8 strong X, 3.2; each main-only sheet | 1220.7875 | 0 |
| 4×8 strong T, 3.175; main + both kickers | 658.85 | 1.5875 |
| 4×8 strong T, 3.2; main + both kickers | 658.8 | 1.5875 |
| 4×8 strong T, either; each main-only sheet | 1219.2 | 1.5875 |
| 4×4 strong X, either; each main sheet | 1.5875 | 0 |
| 4×4 strong T, either; each main sheet | 0 | 1.5875 |
| 4×4 either, 3.175; kicker-only sheet | 662.025 | 1.5875 |
| 4×4 either, 3.2; kicker-only sheet | 662 | 1.5875 |

For a different usable sheet, subtract occupied L/W from its usable dimensions;
a negative result invalidates that placement. An edge trim narrower than the
kerf assumes part of the blade can overhang the discarded outer edge; this
arithmetic does not establish tool support, clamping, straightness or an actual
cutting procedure. Internal kerfs consume their full specified width. Holes,
profiling, defects, machining and any additional cleanup allowance are outside
this rectangular comparison.

## Engineering appendix

The three-sheet option is the earlier grain-blind assembly quantity scenario
made explicit: it implies strong X if grain follows factory L. It cannot be
combined with the existing strong-T response as though the axes matched.
The four-sheet strong-T options preserve modeled orientation, conditionally;
no actual sheet assignment or structural acceptance follows from that match.
The selected baseline's separate kerf-right packet is not imported here.

Producer: [panel_placement.py](panel_placement.py), SHA-256
`9e9e5566ba0342083895c4c66b971fbbc8976d013e57ff5ce21e68ec93a371f4`.
Arithmetic output: `rawlocal/panel-placement/attempt01/result.json`, SHA-256
`0fd347745b493accdfcc67a8d087dd2382ae1a962874a827d3eb0e5fd754fc02`.
Its producer snapshot and all eight explicit placement records are saved in
that ignored child. Decimal quantities are serialized as exact decimal strings.

| Frozen input | SHA-256 |
| --- | --- |
| `rawlocal/catalog-labels-attempt01/reconciled-assembly.json` | `d79bedb1edbc0d4cbde095e77fdebc99bbcb3348ee5cca1866eb80737a732590` |
| `docs/purchased-materials.md` | `3a1e09c02e223cdec91ad96e258046e73322a23c6417252453f818624c3b8bad` |
| `upper-corner-screw-layout/operators-attempt02/model.json` | `b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626` |

From the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/panel_placement.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/panel-placement/attempt02
```

Use a fresh child to preserve the completed calculation. This producer reads
saved records only; it does not run CAD, frame mechanics, native solves or
software tests. No receiving observation or physical release is claimed.
