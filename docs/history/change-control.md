# Change control and review record

This repository is the controlled record for the Mini MoonBoard project.
Nothing in a working tree, chat, photograph, or uncommitted export is an
approved construction input.

## Controlled baseline

The release candidate consists of one tagged Git commit containing:

- CadQuery source, generated STEP files, drawings, CSV cut lists, and BOM;
- source records and the resolved site-survey inputs;
- the reviewer-approved design basis, calculations, and connection details;
- the construction, commissioning, inspection, and maintenance documents; and
- this review record with all comments resolved or explicitly deferred.

The current `master` branch is a development baseline. It is not a build-ready
release until Gate 3 in [`design-basis.md`](design-basis.md) is satisfied and a
qualified reviewer accepts a tagged commit.

## Changes that require review

Record and obtain review before fabricating when a change affects any of the
following:

- room dimensions, floor interface, anchors, crash-pad arrangement, or kicker
  height;
- plywood species, grade, thickness, laminate count, adhesive, or sheet size;
- frame member geometry, connection hardware, fasteners, feet, bracing, or
  portability;
- panel template system, panel size, hole diameter, T-nut system, LED system,
  mounting pattern, hold set, or finish;
- design loads, applicable standards, reviewer identity, or local requirements;
- a CAD source file or generated artifact included in the proposed release; or
- any observed defect, field deviation, relocation, water exposure, collision,
  or structural event.

Cosmetic documentation changes that do not alter a controlled fact may be
reviewed as editorial changes, but must still identify the source commit.

## Change procedure

1. Create an issue or change record describing the reason, affected files,
   installation impact, and whether already-built parts are affected.
2. Update the source fact, measured input, or explicit design assumption; never
   overwrite a source fact with an inference.
3. Regenerate all affected CAD artifacts and run the repository checks.
4. Update BOM, cut list, drawings, construction record, and inspection record
   together when a physical part or process changes.
5. Ask the qualified reviewer to evaluate changes affecting the load path,
   stability, impact area, electrical system, or fabrication.
6. Record acceptance, required revisions, or rejection in the review table.
7. Commit the coherent change. Only tag a commit after the reviewer accepts the
   complete release package.

## Review record

| Field | Record |
| --- | --- |
| Change or review ID | **unresolved** |
| Date | **unresolved** |
| Base commit | **unresolved** |
| Candidate commit | **unresolved** |
| Reason and affected parts | **unresolved** |
| Source facts changed | **unresolved** |
| Assumptions changed | **unresolved** |
| Calculations/drawings reviewed | **unresolved** |
| Reviewer name, qualification, and jurisdiction | **unresolved** |
| Decision and conditions | **unresolved** |
| Release tag, if accepted | **unresolved** |

## Field deviations

If fabricated parts differ from the released drawing, stop that affected work.
Measure and photograph the deviation, open a change record, and determine
whether rework, a revised design, or reviewer approval is required. Do not use
"as-built" measurements to silently redefine the design.
