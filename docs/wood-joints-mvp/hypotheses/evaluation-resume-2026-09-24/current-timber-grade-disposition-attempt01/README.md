# Current timber grade disposition — attempt 01

**Date:** 2026-09-27. **Status:** source-bound preliminary disposition. No
grade, design value, acceptance, or release is assigned.

This note is for `compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`, reviewed at `b1e8707d`. It preserves
selected authority `compact-floor-flush-development` and pins the current
source-yield attempt, attempt02 manifest, source inventory, and 20-member and
24-block material-frame maps. See
[`grade-disposition.json`](grade-disposition.json) and its read-only
[`verify.py`](verify.py).

## Four proposed 4×6 section rips

The pinned source-yield schedule records these proposed dimensions:

- `center_principal_cleat_left/right` (2): from 88.9 × 139.7 mm; 5 mm rip to
  proposed section 83.9 × 139.7 mm; proposed blank length 134.7 mm. Recorded
  bounds are 83.9 × 139.7 × 134.7 mm.
- `knee_outer_left/right_inner_frame_block` (2): from 88.9 × 139.7 mm; 6.35 mm
  rip to proposed section 88.9 × 133.35 mm; proposed blank length 139.0 mm.
  Recorded bounds are 88.9 × 133.35 × 139.0 mm.

These are source-proposed blanks and recorded geometry bounds, not physical
measurements or fabrication tolerances. The center pair has no per-body BRep or
STEP fingerprint in the pinned sources. The inner pair has reported shape
fingerprints. None of the four has a delivered species group, grade, or
post-rip inspection basis.

NIST PS 20-25 Table 3 gives the minimum dressed dry dimensions for nominal 4×6
as 3.5 × 5.5 in (88.9 × 139.7 mm). Both proposed sections are nonstandard
sections. PS 20-25 §6.1.6 and §8.1.4 allow inspection of specified nonstandard
sizes under the applicable certified grading rules. That possibility assigns
no grade to these parts by itself.

PS 20-25 §7.3.7 states that ripping/remanufacturing negates the original
product's grade, mark, and design values, and requires the original mark's
removal. Current ALSC Lumber Enforcement Regulations, dated November 7, 2025,
§5.10.1 require removing or obliterating a grade mark when remanufacture may
alter grade. The listed exceptions do not cover these section rips. No original
4×6 grade or design values transfer to the four proposed blocks.

## Evidence needed for any later grade-specific values

Before assigning values to a ripped block, retain a traceable post-rip
grade/inspection record or mark for each piece under applicable certified
rules. It must identify the final nonstandard section and seasoning condition,
species or species group, grade or explicit no-grade disposition, grading
agency/rule basis, and piece identity linking it to its source board. Record the
source mark and stock identity before ripping. The source/model basis
`DF-L No. 2` is not a delivered grade. No agency or supplier was contacted.

The public [ALSC agency list](https://alsc.org/lumber-accredited-agency-list/)
lists current accredited agencies. WWPA describes contracted onsite grading
and inspection; applicability and availability for these pieces are unconfirmed
([WWPA contracted services][wwpa-services]).

## Primary standards

- [NIST, Voluntary Product Standard PS 20-25][nist-ps20]: Table 3 and §§6.1.6,
  7.3.7, 8.1.4.
- [ALSC, Lumber Enforcement Regulations][alsc-regs], November 7, 2025:
  §§5.9, 5.10, 5.10.1.

[nist-ps20]: https://www.nist.gov/document/ps-20-25-final
[alsc-regs]: https://alsc.org/uploaded/20251107%20Lumber%20Program_Enforcement%20Regs.pdf
[wwpa-services]: https://www.wwpa.org/about-wwpa/services/contracted-services/

## Scope limits

This is a grading-evidence disposition only. It does not change the reviewed
candidate, selected baseline, geometry, material assumptions, or release state.
It does not establish supplier stock, grade, species, treatment, moisture,
cut yield, capacity, design values, or acceptance. No plan/ledger, CAD, solver,
test, or external contact was used.

## Reproduction

From the repository root, run:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/\
current-timber-grade-disposition-attempt01/verify.py
```

The verifier checks pinned file hashes, geometry/revision identity, the 20- and
24-member map counts, the four part IDs and their source-proposed dimensions,
and that no grade or design value is assigned. It reads files only.
