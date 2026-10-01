# Retained 3/4-in tool geometry search — attempt03

**Outcome:** this expanded, source-only review found no newly accessible
Wera-issued exact-part CAD file or complete dimensioned profile for Wera 6000
Joker Imperial 3/4-in wrench, part `05073287001`. The checked Wera public page
and family datasheet identify the exact part and provide discrete dimensions;
the official AR material describes generic 3D product viewing but does not
bind a geometry asset to this part number. Four retained `#407` wrench axes
remain `NOT_RUN_SOURCE_GAP`.

This is a bounded source-route result, not a claim that no model exists. Exact
part-number datasheet routes could not be retrieved; Wera's data/media portals
were inaccessible or login-gated; the current compact catalogue and Joker
sales folder exceeded the browser reader's size limit. Search queries, URLs,
identifiers, outcomes and profile coverage are recorded in
[`source-audit.json`](source-audit.json). The companion
[`source-observations.md`](source-observations.md) preserves the reviewed
content summaries. The browser tool supplied rendered page/PDF text, not raw
HTTP/PDF bytes, so no source-file hash is claimed; packet files are locally
hashed in [`terminal-hashes.json`](terminal-hashes.json).

## Existing result and fixed scope

Attempt02 remains unchanged and its verifier passed during this attempt. Its
independent review remains `SUPPORTED_WITH_QUALIFICATION`; that review already
recognized that the page-linked datasheet variant table includes the exact
part's dimensions while the PDF cover identifies a different family variant.
Attempt03 narrows no earlier source claim and does not supersede that review.

The comparison scope remains the four existing lumber-leg axes tied to the
preserved Bolt Depot `#407` 3/4-in-head catalog reference. The other eight
retained axes have distinct `#367`/`#368` references and are not targets here.
No axis, bolt arrangement, product choice, geometry, fit result, operation
status, or candidate criterion changed. No CAD/tool-motion, physical fit,
access, service, assembly, transport, native solver, or Docker operation was
performed.

## Next evidence needed

The four target axes can leave `NOT_RUN_SOURCE_GAP` only after an exact-part,
traceable Wera geometry source becomes accessible: a Wera-issued `STEP`/other
usable exterior model, a complete dimensioned drawing, or a Wera-authorized
portal record that explicitly binds its model bytes/revision to
`05073287001`. The source must define units and datum and the entire wrench
exterior, including the open jaw/holding plate, head transitions, handle, ring
end and their relative positions. If Wera's login-gated channels are used,
obtain the files through normal authorized access; this attempt made no vendor
contact. Once received, retain the original file and hash it before any
bounded comparison against the unchanged four axes. A visual AR object alone
is not accepted unless it has a traceable exact-part binding and usable,
measurable geometry.

Run the read-only local packet check from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/retained-3-4-tool-geometry-source-gap-attempt03/verify_source_search.py
```
