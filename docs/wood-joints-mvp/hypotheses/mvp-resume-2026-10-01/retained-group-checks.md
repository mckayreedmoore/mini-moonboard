# Retained bolt-pair group scenarios

## Result and working decision

The twelve retained frame bolts were the closest eligible individual lateral
reference in the current remaining-joint worksheet. This calculation retains
all six nominal-gap force states, six two-bolt duties, and signed unequal
bolt forces. It adds 36 pair records and 72 individual records, without
rerunning the frame or changing hardware, geometry, floor laws or panel laws.

The largest ratio after division by the smallest of four declared row-factor
scenarios is **0.961261**, at `rail_front_bolt_left_2`, A12-forward. The
unadjusted individual ratio was **0.952117**. This comparison does not indicate
a larger retained bolt from the declared scenarios. It does not establish the
actual factor or full resistance of an oblique group carrying a couple.

| Retained pair | Pair pitch, mm | Minimum of four declared factors | Peak individual ratio divided by that factor |
| --- | ---: | ---: | ---: |
| Front left | 39.500 | 0.990488 | 0.961261 |
| Front right | 39.500 | 0.990488 | 0.938497 |
| Rear left | 44.365 | 0.990157 | 0.556205 |
| Rear right | 44.365 | 0.990157 | 0.535678 |
| Upper leg left | 56.000 | 0.995593 | 0.607047 |
| Upper leg right | 56.000 | 0.995593 | 0.597314 |

Each peak is its own simultaneous state. Forces and tensions from different
cases are not combined. The governing bolt retains V=1041.963 N, simultaneous
outer tie T=190.904 N, and its original 92 ksi lateral reference 1094.364 N.
That particular lateral reference is mode II and also governs the existing
45/106 ksi scenarios. The tie is recorded separately, not converted into an
additional lateral force or an adopted steel-interaction result.

## Primary method and applicability

The pinned [NDS 2024 Chapter 11](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf),
printed p.74, supplies Eq.11.3-1 and §§11.3.6.1–.3. The local source is
`../upper-block-strength-2026-10-01/source-cache/chapter11-2024-awc-20260911.pdf`,
SHA-256 `45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33`.
The [AWC errata](https://web-media.awc.org/wp-content/uploads/2025/03/31134949/2024-NDS-Errata-and-Addenda-03.28.25.pdf)
also confirms that the diameter exponent in the wood-to-wood row modulus is
1.5. The calculation uses `gamma=180000 D^1.5`, with D in inches: 3/8 in at
the front/rear pairs and 1/2 in at the upper legs. It does not reuse the
quarter-inch value from the earlier top-corner helper.

NDS defines a row by load alignment and includes a proximity rule for
staggered adjacent rows. Each saved record therefore includes the actual
force-to-pair-line angle and projected parallel/transverse spacing. At the
governing front-left bolt, the angle is 69.516 degrees; projected spacing is
13.823 mm along its force and 37.002 mm across it. This is not an aligned
two-fastener load row. The pair's net lateral resultant is also oblique,
47.645 degrees from the pair line in that case. The two bolt directions and
their moment are preserved; no equal sharing is inferred from the resultant.

The proximity flags in the machine output are geometric diagnostics for
each bolt-force direction. They are not a classification of the complete
joint under one uniform load. **Actual oblique-group Cg remains null.**
Neither a singleton row assertion nor a favorable two-bolt factor closes
the complete group or its couple transfer.

For a finite sensitivity, each receiver has two explicit area choices:

1. Recorded gross stock cross-section, with no subtraction for bolt holes.
2. Declared perpendicular-load equivalent area: minimum saved bearing
   length on the bolt times the pair's projection on that receiver's grain.

All four combinations use the existing dry DF-L No.2 modulus hypothesis,
E=1,600,000 psi, and the actual pair pitch. The front-pair gross areas are
8.25 in² on both sides; its declared equivalent areas are 1.649452 in².
The two mixed combinations give 0.990488; the two equal-area combinations
give 1.0. These four values do not bound every oblique loaded-area choice,
and the equivalent-width construction is not an adopted interpretation
for this joint. No edge, end or minimum spacing passes follow from it.
The NDS row modulus is used only in this equation, not as a replacement
frame spring stiffness.

## Force and evidence scope

[retained_group_checks.py](retained_group_checks.py) consumes the unchanged
`remaining-joint-screen-attempt04/all-two-receiver-92ksi` report and CSV.
The report SHA-256 is
`5b85139b2acaefd8ff74df916229766438c0caf3bc9c3a1a7b5080f8f393033a`.
Its current force source is `two-receiver-frame-attempt03/`. The six nominal
states have bounded, nonunique seating, not a unique pose or strict tangent
stability; this calculation uses saved forces only.

The original `/tmp/mini-moonboard-retained-frame-bolt-current-resistance-basis-2026-10-01.json`
supplies receiver stock frames, diameters, grain and finished bearing lengths.
Its SHA-256 remains
`c3250f067c4590ee43f7ec7a5765d056d87e6ff5adb42837ed27710d9b4d4eb1`.
All thirteen input bindings, including the eight unique receiver STEPs,
matched before and after execution. No historical three-rear-case force
records were used as current forces.

Each pair output retains its bolt-only six-component wrench about the mean
shear-plane datum. Contact forces, free couples and other joint actions are
outside that wrench; it is not a replacement whole-joint balance. Actual
washer/wood transfer, steel interaction, local splitting and the full group
remain the previously recorded conditions. The panel attachment deficit
and top-rail proxy exception are unchanged.

Result: `retained-group-attempt01/checks.json`, SHA-256
`601ec4adb6528ad8b2b51289c2d0dd5b851988b7087408e18b1990701b082f0f`.
The result, source pins and exact producer snapshot are local and ignored.

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/retained_group_checks.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/retained-group-attempt02
```

Use a fresh output directory. Ruff passes; no software tests, CAD rebuild,
frame solve, native execution or review loop were run. Hardware selection,
reviewed geometry change, complete-joint acceptance and physical release
remain false; all 47 criteria remain pending.
