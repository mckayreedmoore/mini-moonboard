# Upper-left service joint: reuse and panel-sharing check

**Existing Hillman action results were found and reused. The conditional
working scenario remains useful, but its panel restraint is essential.
The complete joint and release remain HOLD; the 47-criterion authority and
eight release flags are unchanged.**

The reviewed cleat, four bolt axes, 33 mm pitches and both host members are
unchanged. This is the finite next check recommended by the
[completed frame worksheet](../upper-left-service-frame-clearance-2026-10-01/README.md).

## What already existed

The [current panel receiver packet](../current-panel-receiver-transfer-2026-10-01/README.md)
already joins **66 Hillman 42605 panel/kicker screws × 21 saved states**:
1,386 same-state screw records, 4,158 scalar actions and receiver wrenches.
Its physical-body endpoint projection reproduces all 5,544 endpoint records.
The distinct recursive reduced mapping remains refused for its recorded
42 force and 77 point-moment discrepancies. These results are force/action
accounting under source laws, not screw resistance or measured stiffness.

The existing packet's peak withdrawal forces at the original recorded loads
are approximately **1,157 N (A1-rear), 1,921 N (A12-rear), and 1,624 N
(K12-rear)**. Its [Hillman applicability note](../current-panel-receiver-transfer-2026-10-01/hillman-applicability.md)
does not establish product-specific withdrawal, lateral, head pull-through,
bending or load-slip values. The [purchase policy](../../../current-panel-screw-purchase.md)
also retains that distinction. Historical
[SPAX results](../../../../fea/results/horizontal-panel-fastener-screen-v1.json)
and [stiffness hypotheses](../../../history/provisional-connection-assumptions.md)
were located, but are not Hillman qualifications and are not substituted here.
This is a repository lookup, not a new exhaustive manufacturer search.

## Small additional comparison

The producer imports the authenticated, unchanged `Frame` helper and reuses
all **21 baseline states** from the completed frame comparison. Only
**42 additional trials** are run: half and quarter stiffness for the same
66 screws, at the same 1.15 mm outer-bolt clearance. Both lateral and withdrawal
stiffness change together; their source ratio of 1 is retained. This is a
clearly hypothetical range, not a product-supported bound or a measured law.

| Screw law multiplier | Lateral and withdrawal stiffness | Floor-consistent states | Local host motion / rotation | Single-screw withdrawal peak |
| --- | ---: | ---: | ---: | ---: |
| 1, saved baseline | 2,690 N/mm | 21 of 21 | 0.558 mm / 0.105° | 3,845 N |
| 0.5, hypothetical | 1,345 N/mm | 0 of 21 | Not accepted | Not accepted |
| 0.25, hypothetical | 672 N/mm | 0 of 21 | Not accepted | Not accepted |
| Zero withdrawal credit | Lateral stiffness immaterial to the outward mode | No equilibrium in declared model | No solution | Necessary group restraint below |

All rows refer to **2× the recorded proportional gravity-plus-climber loads**.
This scales gravity as well as climber load; it is not an adopted load
combination. Missing A12-forward, A12-left and K12-right responses remain missing.

The softer trials violate the recorded floor bearing/open signs. The helper's
existing normal-law gates refuse each trial; they are preserved, not relaxed.
No motion or force result from those stopped branches is presented as an
accepted response. This does **not** establish physical frame failure or
insufficient screw strength. It establishes that the old floor contact pattern
cannot be reused to claim a stiffness bound for these hypotheses. No new
floor selection or native analysis is attempted.

The saved baseline's **3,845 N withdrawal peak** is at
`round_panel_upper_left_edge_2`, into `base_rail_top`, at full A12-rear.
Its upper-left panel group withdrawal total there is **5,939 N**. The source
springs are elastic without resistance caps, so these values are conditional
model demands, not proof that Hillman screws can carry them. The largest
modeled screw lateral resultant over the 21 baseline states is **2,255 N**;
it need not occur at the withdrawal peak. The outer cleat bolts' low
9 N shear / 13 N tension peaks cannot qualify the other load paths.

## Why zero withdrawal credit does not work

For each upper panel, construct a rigid translation along its source outward
normal, approximately `[0, 0.766044, -0.642788]`. Project the body-equilibrium
equation `D.T * f = W` onto that mode. The bilateral lateral rows and floor
rows have zero projection, within the declared `1e-12` geometry roundoff
tolerance. All remaining unilateral projections are nonpositive. Since their
forces must be nonnegative, they cannot oppose a positive outward load without
the withdrawn screw restraint. This necessary condition does not depend on
screw lateral stiffness, a selected contact branch or a trial matrix inverse.

At full 2× A12-rear, the upper-left panel requires at least **3,528 N total
withdrawal restraint across its 12 screws**. At full 2× K12-rear, the
upper-right panel requires at least **3,527 N**. This is a group equilibrium
lower bound: the approximately 294 N average is not an individual screw
capacity requirement or an assumed equal allocation. Self-weight gives a
positive outward requirement even when the applied climber load is on another
panel. The certificate covers both upper panels at all 21 saved states.

## Decision and next check

**Robust within the declared source geometry:** upper panels require an
outward restraint path; lateral screw stiffness alone cannot replace it.
Existing screw action results already represent that load path and need not
be regenerated. The completed clearance worksheet remains a conditional
reason to retain the reviewed cleat geometry.

**Assumption dependent:** the small host motion and low outer-bolt demand
rely on unqualified screw restraint, other bolts with zero clearance and
the recorded no-slip floor pattern. This new comparison does not establish
robust motion over the hypothetical softer screw range.

**Recommended next design check:** compare the existing upper-panel normal
demands with a defensible Hillman screw withdrawal/head pull-through resistance
basis, including the actual receiver and panel assumptions. This is more
likely to change the working design decision than strengthening the lightly
loaded outer cleat bolts. The main agent can then decide whether its integrated
frame calculation needs a newly selected floor branch; no source mask pass
transfers automatically. No socket, new fastener or geometry change is proposed.

Bolt bending, washer/contact transfer, timber bearing, finished sections,
splitting, group applicability and turning/counterhold remain open. The
source checker's completed status and all prior evidence are preserved.

## Evidence and reproduction

- [Comparison](comparison.json): existing results, 21 reused baseline states,
  42 explicit stop diagnostics, and both zero-credit certificates.
- [Response vectors](response-vectors.npz): only the 21 accepted, reused
  baseline vectors; stopped trials have no accepted vector or motion.
- [Producer](study.py): exact source/authority authentication and the small
  comparison, using the original helper without editing it.
- [Receipt and main-agent handoff](receipt.json): final artifact hashes,
  focused arithmetic/reuse checks and reproduction record.

Ruff passes. Replay preserves the 21 reused response vectors byte-for-byte,
both outward certificates, all comparison values and all 42 stop dispositions.
The only report differences are 15 last-bit reciprocal-condition estimates,
at most `1e-23` absolute. The report itself is not byte-identical. The replay
is preserved at `/tmp/upper-left-service-panel-sharing-replay-3tcwpdmo`.

Reproduce into fresh paths; existing output files are refused:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/upper-left-service-panel-sharing-2026-10-01/study.py \
  --output /tmp/service-panel-sharing-replay.json \
  --vectors /tmp/service-panel-sharing-replay.npz
```

No source packet, authority file, reviewed geometry, native readiness flag,
commit or push was changed. Dirty, untracked, ignored and referenced `/tmp`
evidence remains preserved.
