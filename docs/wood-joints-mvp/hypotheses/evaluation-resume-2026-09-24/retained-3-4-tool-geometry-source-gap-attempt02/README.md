# Retained 3/4-in tool geometry source gap — attempt02

**Decision:** the bounded search found Wera-published size and envelope
dimensions for Joker part `05073287001`, but no accessible manufacturer-primary
source file or dimensioned drawing that defines its complete external profile.
The dimensions are useful for identifying the size mismatch in the earlier
7/16-in proxy; they do not bind the full wrench shape. The four retained `#407`
axes therefore remain `NOT_RUN_SOURCE_GAP`.

This is a source review only. It does not change the reviewed geometry, select
the Wera wrench, or screen fit, access, turning motion, counterhold, service,
installation/removal, or transport. It does not clear any operation or
candidate criterion.

## Manufacturer routes checked

Routes were checked on 2026-09-28. The source roles and retrieval outcomes are
recorded in [`source-pins.json`](source-pins.json); the local inputs and their
hashes are frozen there as well.

- Wera's [6000 Joker Imperial product page](https://www.wera.de/en/tools/6000-joker-ratcheting-combination-wrenches-imperial)
  identifies `05073287001` as 3/4 in and publishes 246 mm overall length,
  42 mm open-end external width, 9.5 mm open-end head thickness, 34.8 mm
  ratchet-end external width, and 11 mm maximum ratchet-head height. It also
  publishes the 30-degree open-end return angle and 80-tooth ratchet. Those are
  discrete dimensions and feature data, not a complete dimensioned outline.
- The official [user manual PDF](https://www.wera.de/fileadmin/pdf/manuals/11670984-00000177-09_screen.pdf)
  was opened from the product page. It describes intended use and features;
  it is not a dimensioned drawing.
- The product page's visible datasheet download resolved to a Wera-hosted PDF
  for part `05073280001` (5/16 in), not the target `05073287001`. The target
  part-number PDF short-link and the corresponding Wera media-PDF URL were also
  attempted directly; the browser retrieval tool could not access either
  route. This records an access limitation, not proof that Wera has no such
  file.
- Wera's [catalog download index](https://www.wera.de/en/downloads/catalogs)
  lists the manufacturer's compact catalogues and Joker sales folder. Wera's
  indexed catalogue/sales-folder tables repeat the nominal size and profile
  dimensions above, but no complete, dimensioned outline was exposed in the
  reviewed material. The Joker PDF was too large for the available reader to
  fetch. The official [Data Cockpit page](https://www.wera.de/en/data-cockpit)
  and [Digital Support PDF](https://www.wera.de/sh/Wera-Digital-World.pdf)
  describe product-data/media access; the public description names product
  data, Excel/XML exports, and product/application images. It does not provide
  this exact wrench geometry or establish that a CAD file is unavailable
  behind Wera's internal-sales access route.
- Manufacturer-domain searches for `05073287001` with CAD, STEP, 3D, and drawing
  terms were discovery checks. They did not locate a Wera-hosted full-profile
  geometry artifact. Search-result absence is not treated as evidence that no
  such artifact exists.

The distributor [Olander listing](https://www.olander.com/items/05073287001)
continues to be only a discovery lead because its “View 3D CAD Model” label
does not bind the model bytes to Wera authorship/authorization, the exact
part/revision, datum, units, or a file hash. It is not used as geometry
evidence.

## Exact missing source

The remaining source gap is a Wera-issued, exact-part `05073287001` 3D exterior
model (for example, STEP) or a complete manufacturer-dimensioned drawing that
binds the nominal external shape. The record must identify the exact product
and model/drawing revision, units, and datum/orientation. It must define the
full open-jaw outline and engagement surfaces, holding plate/limit-stop
features that affect the shape, head thickness and transitions, the handle,
and the ratcheting ring end and its position relative to the jaw. No contour,
tolerance, or motion envelope is reconstructed from the published dimensions,
photographs, or bounding boxes.

If such a source is later obtained, it can support only a bounded, conditional
CAD envelope comparison against the unchanged four `#407` arrangements. A CAD
comparison would still not establish physical jaw fit, real access, hand
workspace, turning/counterhold pairing, torque method, cable service, or
reversible installation/removal.

## Frozen scope and gates

The geometry revision remains `led-clearance-2x6-runner-seated-blocks-v1`.
All 12 retained bolt-arrangement identities are listed in `source-gap.json`.
Only the four lumber-leg axes mapped in T08 to the preserved selected-baseline
Bolt Depot `#407` catalog reference are matching-size targets; the other eight
axes retain their distinct `#367`/`#368` reference boundary and are not
screened here. All four target axes remain `NOT_RUN_SOURCE_GAP`; the other
eight are inventory-only and `NOT_TARGETED_DIFFERENT_SIZE_REFERENCE`.

No geometry or bolt arrangement changed. No product was selected. No motion,
fit, access, transport, or physical-operation screen was run. All physical
operation statuses remain open and all candidate criteria remain pending. No
native, Docker, or solver execution occurred.

Run the read-only packet and source-pin check from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/retained-3-4-tool-geometry-source-gap-attempt02/verify_source_gap.py
```

The verifier checks packet hashes, all pinned repository inputs, the upstream
T07/T08 parent-review states, and the frozen 12-axis target set. It performs
no geometry or operation screen. This attempt is awaiting parent review.
