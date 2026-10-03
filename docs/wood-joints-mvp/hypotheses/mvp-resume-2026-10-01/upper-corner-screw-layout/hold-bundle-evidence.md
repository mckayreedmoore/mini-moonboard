# Mini MoonBoard 2025 hold bundle and force-offset evidence

**2026-10-02 — primary-source fact packet complete.** No load, frame,
geometry, hardware policy or joint acceptance is changed. The current
100 mm source and completed 50 mm sensitivity remain separate.

## Decision supported by the evidence

The owner's Mini 2025 bundle contains Originals, School Set F, Wood B and
Wood C. The wood sets have published nominal thicknesses up to 50 mm.
That does **not** establish a 50 mm bound for the complete bundle: the
official setup picture places blue Set F holds at both A12 and K12, the
upper locations used by the current six cases. No normal-to-mounting-base
depth for those resin holds was found in the reviewed official material.

The owner subsequently directed retaining the existing loading and avoiding
further lever studies. Keep 100 mm as the working analytical assumption and
50 mm as completed sensitivity evidence.
Neither number is a manufacturer-qualified bundle-wide force-offset bound.
The useful remaining fact is the Set F profile dimension, rather than
another frame calculation or a bolt-length inference.

## Exact catalog contents

The [USA bundle page](https://us.moonclimbing.com/products/mini-moonboard-2025-hold-set)
and [EU bundle page](https://eu.moonclimbing.com/mini-moonboard-2025-setup-hold-bundle.html)
identify SKU **60-105-2025** and the same four component sets. The USA page
states 138 holds; the individual product counts reconcile exactly:

| Component | Product SKU | Catalog quantity | Published hold thickness/profile |
| --- | --- | ---: | --- |
| [Original School Holds](https://moonclimbing.com/moonboard/holds-and-bolts/original-school-holds.html) | 60-116-020 | 40 PU hand holds + 10 PU footholds | No hold-depth dimension in the reviewed product page; its box dimensions describe packaging |
| [School Holds Set F](https://moonclimbing.com/moonboard/holds-and-bolts/new-school-holds-set-f.html) | 60-121-06-277 | 40 PE hand holds | Pockets, pinches and edges described; no hold-depth dimension in the reviewed UK or [USA page](https://us.moonclimbing.com/products/moonboard-school-holds-set-f) |
| [Wood Holds Set B](https://eu.moonclimbing.com/wood-holds-set-b.html) | 60-154-02-060 | 24 wood hand holds | Eight each at 23, 35 and 50 mm |
| [Wood Holds Set C](https://moonclimbing.com/moonboard/holds-and-bolts/wood-holds-set-c.html) | 60-154-03-060 | 24 wood hand holds | Eight each at 23, 35 and 50 mm |
| **Total** | | **128 hand holds + 10 footholds = 138** | Wood dimensions cover 48 hand holds; resin depths remain unspecified here |

The hold-only bundle excludes mounting bolts, T-nuts and the LED system.
This is catalog inventory, not an observation of the delivered owner's set
or a count of populated grid stations. The DIY kit is a different product.

## Which holds matter to the current cases

The [official Mini 2025 setup image](https://us.moonclimbing.com/cdn/shop/files/2025-mini-setup.png?v=1770821238&width=1440)
is linked from the USA bundle product page. Visual reading shows:

| Current load location | Visible family | Consequence for the offset question |
| --- | --- | --- |
| A12 | Blue resin; inferred Set F from the bundle's sole blue set | The wood sets' 50 mm thickness does not establish this hold's depth |
| K12 | Blue resin; inferred Set F on the same basis | The same missing Set F profile fact applies |
| A1 | Wood | The wood catalog gives a nominal 50 mm maximum across B/C; this image does not establish its individual hold number or thickness |

These are family identifications from the manufacturer's front-view layout,
not depth measurements. The picture lacks a calibrated side profile.
Individual hold numbers and measured contact locations are not inferred
from small labels, apparent image size or perspective. Searches of the
official product and installation material did not locate a dimensioned
Set F/Original profile or a calibrated video measurement; that is a bounded
search result, not a claim that no unpublished drawing exists.

## What the dimension would establish

The existing [load-origin worksheet](../panel-attachment/load-realism.md)
defines the current 100 mm as a guessed outward **hold-contact offset from
the panel front face**. It is not a climber center-of-gravity offset. The
[50 mm comparison](load-lever.md) changes that normal offset while keeping
the full applied force and the original patch center. It retains the
9.128125 mm front-face-to-midplane offset, giving reference-plane offsets
of 109.128125 and 59.128125 mm respectively.

For a hold mounted directly on its flat base, a documented maximum profile
depth can bound the normal coordinate of a single physical surface contact.
Thus the wood catalog supports a **nominal 50 mm maximum normal extent**
for the published B/C profiles, conditional on that direct mounting and
the catalog thickness representing their full projection. It does not
measure the force's effective application point, delivered tolerances,
spacers or an individual grip.

The distinction is visible in `r = s*n + t` and `M = r cross F`: `s` is
the outward coordinate being varied, while `t` is any offset along the
panel face. Hold depth alone does not identify `t`, the pressure distribution,
or a couple produced by several hand/foot contacts. This packet leaves the
current single-force, fixed-patch idealization intact; it does not introduce
a new contact model or qualification prerequisite.

The Originals page lists M10 × 60 mm mounting bolts. The wood pages list
M10 countersunk bolts of 50 and 70 mm. Those are fastener specifications,
not grip depths: panel thickness, thread engagement and recessed bearing
locations consume different portions of their lengths. They supply no
valid shortcut to a 50 or 100 mm force offset for Set F or Originals.

## MVP disposition

The owner directed making reasonable assumptions and simplifying the MVP,
then explicitly declined further modeling of the lever difference. Retain
the existing 100 mm force source and the completed 50 mm sensitivity. No
additional hold profile, owner measurement or frame variant is required
for the current working model. The unspecified resin dimensions remain an
explicit assumption; this fact packet establishes no physical load rating.

## Evidence capture

The ignored capture is
`rawlocal/hold-bundle-evidence/attempt01/`. It contains original HTML,
readable text extractions, the setup image and `sources.json`, which records
URLs, HTTP status, capture time and content hashes. Capture time was
2026-10-03 UTC, still October 2 in America/Denver. All eight captures
returned HTTP 200. The HTML/media hashes below pin the reviewed bytes;
the manifest also records text-extraction hashes.

| Capture | SHA-256 |
| --- | --- |
| `mini-2025-bundle-us.html` | `89e87bb47d7e90d44feb0c5ea6db8ac18f49af34ab9a98a2d6aeae3392b51dc5` |
| `mini-2025-bundle-eu.html` | `440337e4ea8982e9c6245059fb0b7e2eddc8d01bb282c7f0b6592d5c2968eb91` |
| `wood-b-eu.html` | `036942f80396aa815d43bb165a573c1b785c3795a8b1263aa455fc0535b63bd2` |
| `wood-c-uk.html` | `c3da71ad27d91964d6ed50bb848663c10a3c1e4f5624ba4a267f325136547ef2` |
| `original-uk.html` | `34146b1617bd464d14a4339fa7ba5d4e0454334abda72e5fbd5b4fbf09cb70cd` |
| `set-f-us.html` | `0ffae0a20758fdb85e7cee0def05827fa33e54f1c48971f088ea0041ecf6b09f` |
| `set-f-uk.html` | `b6af2bc69e99e91f53e75a2f49b608a90e3bd1ae4f60838781a13a124e0428a6` |
| `mini-2025-setup-image.png` | `a05b4a57ea03776b228e2e7b85c6199cef501a286189f55a3de010b6c45beebe` |
| `sources.json` | `05bd0f07cae13e4eed05adcaf5b99ad13b96e04815d0c473ac70afce8eef020a` |

Local interpretation inputs, read without editing:
`load-lever.md` SHA-256
`fd6c9d7d1f5f97b83da5d8074d2f8ea7bc79033b2b1748d911003eeec336f422`;
`../panel-attachment/load-realism.md` SHA-256
`afb3ee10c7746293b14da0fd8b404635066b7fd588517fab33e24040559cf59d`.
