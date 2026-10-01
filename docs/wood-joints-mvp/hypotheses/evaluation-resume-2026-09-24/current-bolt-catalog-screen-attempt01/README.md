# Current 1/4-20 bolt catalog screen — attempt 01

Read-only catalog screen checked 2026-09-27 for the 92 candidate bolt axes in
the current wood-joints development lane. It covers every current length/grip
row, shared nut and washer leads, and the conditional ordinary-axis spacer.
The 12 retained selected-baseline frame bolts are outside this screen.

## Frozen input

- Candidate: compact-floor-flush-wood-joints-development
- Reviewed geometry revision: led-clearance-2x6-runner-seated-blocks-v1
- Axis source: grip-screen-attempt02.json, SHA-256
  9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a
- Manifest: current-full-frame-input-manifest-attempt02, embedded SHA-256
  1ad6b404c8658147e9d10f54daf4ebd393116c1934654f5521421dc96667e0a0;
  raw file SHA-256 21073d852474d4443f61f2172cd9eabc3ce49ee86414facb105773822e3c60f3.
- The selected baseline compact-floor-flush-development remains preserved.
  The manifest says selected hardware is not ready and release flags are false.

The [structured catalog screen](catalog-screen.json) pins these inputs and
12 local source documents by SHA-256. It contains the exact axis IDs for each
row, vendor URLs, copied specs, price/availability observations, and
thread-fit limits.

| Candidate axes | Count | Wood grip | Modeled length | Screened lead/class |
| --- | ---: | ---: | ---: | --- |
| Outer post | 4 | 76.2 mm | 101.6 mm | 4 in HiStrength / Tanner / K.L. Jack leads |
| Center principal | 4 | 122.0 mm | 139.2174 mm | 5-1/2 in HiStrength / Tanner leads |
| Center post | 4 | 127.0 mm | 139.2174 mm | 5-3/4 in class has no verified SKU; 6 in alternatives |
| Ordinary | 48 | 127.0 mm | 152.4 mm | 6 in K.L. Jack / HiStrength leads; Würth conflict |
| Center post header | 4 | 167.0 mm | 179.2174 mm | 7-1/2 in HiStrength / Fastener SuperStore |
| Center principal header | 4 | 172.8 mm | 190.0174 mm | 7-1/2 in HiStrength / Fastener SuperStore |
| Knee inner header | 4 | 177.1 mm | 202.5 mm | 7-3/4 in class has no verified SKU; 8 in leads |
| Side | 16 | 177.8 mm | 203.2 mm | 8 in Lawson / HiStrength leads |
| Knee outer side | 4 | 215.9 mm | 241.3 mm | 9-1/4 in class has no verified SKU; 9-1/2 in Ro-Brand lead |

## Catalog status and fit boundary

No SKU is safely selectable. Current indexed observations include displayed
HiStrength, Tanner, K.L. Jack, Würth, Lawson, Fastener SuperStore, Ro-Brand,
and McMaster-Carr data. The JSON distinguishes same-day pages from aged
captures and failed fetches. For example, Lawson and McMaster pages were
retrieved today; K.L. Jack pages timed out, Würth's capture is about six months
old and has a thread-length conflict, and the Ro-Brand page could not be
rechecked. Only publicly displayed prices and stock text are recorded; account
pricing, shipping, and tax are excluded.

Catalog Thread Length, ASME LT, LG, and LB are not delivered full-form-thread
transition coordinates. No source here bounds the actual bolt thread start,
last scratch, runout/point, or matched nut's active internal-thread interval
and chamfers. UNC Class 2A/2B compatibility alone does not prove full
functional nut engagement. The 3.175 mm physical tip projection is not a
requirement for full thread through that tail. The conditional two-spacer
layout is a geometry proposal only.

The Tanner 5-1/2 in listing was rechecked directly on 2026-09-27 and displayed
$32.05 per 50-piece box ($28.85 at 10+) and “Available to Order.” The initial
screen's $30.24/$27.22 amounts came from a roughly two-month-old page capture;
they remain in the structured record as superseded history. This price update
does not select or fit-qualify that SKU. Its product URL is recorded in
[catalog-screen.json](catalog-screen.json).

All 92 axes remain without a fit-qualified stack. This artifact selects no
product or SKU, records no purchase, accepts no hardware, and authorizes no
drilling, fabrication, structural release, or climbing release.

## Verification

Run python3 verify.py from this directory. It checks all local source hashes,
candidate/revision/manifest identity, product references, 9-row / 92-axis
coverage, and unreleased disposition; the result is recorded in
[verification.json](verification.json). This is artifact integrity verification,
not a CAD/solver run or project test.
