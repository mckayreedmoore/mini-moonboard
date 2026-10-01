# Retained 3/4-in tool geometry source gap — attempt01

**Decision:** no authoritative, full-profile, matching-size tool geometry
record is available in the reviewed T07/T08 source packet. The 3/4-in Wera
`05073287001` record is a manufacturer-published dimensional/profile
comparator. It is not a 3D shape that can support a reproducible tool-motion
envelope without filling in missing geometry.

The parent-reviewed [critical-envelope screen](../current-fit-transport-critical-envelopes-attempt01/README.md)
uses a synthetic 7/16-in FACOM profile on the retained 1/2-13 lumber-leg
references. Bolt Depot #407 lists a 3/4-in head across flats, so that existing
proxy is undersized. Wera's official product page identifies `05073287001` as
3/4 in and publishes an overall length of 246 mm, open-end external width of
42 mm and head thickness of 9.5 mm, ring-end external width of 34.8 mm and
maximum head height of 11 mm, plus a 30-degree return angle and 80-tooth ring
mechanism. The reviewed page exposes manual and data-sheet PDF downloads. The
reviewed Wera record does not provide a manufacturer-issued CAD/STEP model or
a dimensioned full-profile drawing in the source packet. Bolt Depot's #407
page confirms the catalog head size; it does not supply Wera tool geometry.

The exact missing source is a Wera-issued or Wera-authorized 3D model for
`05073287001` (with file identity, revision, units, datum and a hash), or a
complete dimensioned outline defining the same full tool shape and 3/4-in
open-jaw engagement profile. The record must cover the jaw opening and
engagement surfaces, head outline and thickness, transitions/offsets, handle,
and ring end. Published overall dimensions and product images are insufficient
to reconstruct those contours. A distributor page surfaced with a “View 3D
CAD Model” label, but the currently available evidence does not establish
Wera authorship or authorization, source revision, datum or exact model bytes;
that lead is therefore not accepted as authoritative geometry.

No motion or clearance calculation was run. The four size-matched target axes
are listed as `NOT_RUN_SOURCE_GAP`; the other eight retained arrangements are
inventory-only here and remain unchanged because their #367/#368 references
are not the #407 size. All 12 retained axis identities are frozen from T08.
This source-gap record changes no geometry, product/tool selection, fit/access
or service status, transport status, or candidate criterion disposition.

## Source basis

The local hashes and exact status/identity checks are recorded in
[`source-pins.json`](source-pins.json). The focused verifier is
[`verify_source_gap.py`](verify_source_gap.py); run it from the repository
root. The packet artifact hashes are recorded in
[`terminal-hashes.json`](terminal-hashes.json):

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/retained-3-4-tool-geometry-source-gap-attempt01/verify_source_gap.py
```

Public source references checked on 2026-09-28:

- [Wera 6000 Joker ratcheting combination wrenches, Imperial](https://www.wera.de/en/tools/6000-joker-ratcheting-combination-wrenches-imperial) — manufacturer identity, nominal sizes and published profile dimensions/features.
- [Bolt Depot product #407](https://boltdepot.com/Product-Details?product=407) — catalog reference states 1/2-13 × 8 in and 3/4-in width across flats.
- [Olander listing for 05073287001](https://www.olander.com/items/05073287001) — distributor CAD lead only; not evidence of manufacturer-issued geometry.

The T07 parent review still records every physical operation gate as open.
The 3/4-in comparator is not a selected tool; even a future conditional CAD
envelope comparison would not establish actual tool access, jaw fit, hand
space, turning/counterhold pairing, torque method, cable service, or reversible
installation/removal. No native, Docker or solver execution occurred.
