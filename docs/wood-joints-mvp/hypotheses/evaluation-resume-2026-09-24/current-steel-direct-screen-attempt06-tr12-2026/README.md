# T06 AWC TR-12 2026 source-observation screen — attempt06

**Disposition:** official AWC search-index excerpts clarify TR-12's visible
lateral-yield scope and identify fastener-bending inputs in that route. The
complete 2026 PDF was not accessible, so the report's treatment of axial bolt
tension or a combined through-bolt N+V+M method remains **unknown**. No method
is adopted, no capacity or criterion result is produced, and no candidate,
criteria, method map, hardware, geometry, solver, or release state is changed.

## Source and access

The official AWC [Technical Reports collection](https://awc.org/collection/technical-reports/)
lists *TR 12 — General Dowel Equations for Calculating Lateral Connection
Values*. The AWC [2026 report PDF](https://awc.org/wp-content/uploads/2026/06/TR-12_2026_formatted.V3.pdf)
is titled *Technical Report 12: General Dowel Equations for Calculating
Lateral Connection Values with Appendix A*. Indexed front matter identifies
American Wood Council copyright © 2026. The file path is under `/2026/06/`.
The search index labels it “Published: 3 months ago”; that crawler metadata is
not treated as a publication date.

On 2026-09-28, direct opens of both official URLs returned HTTP 403. The
official `web-media.awc.org` alternative and AWC WordPress REST URLs were also
unavailable in this review. Search queries scoped to the exact official PDF
URL returned partial indexed text. The binary was not retrieved, so no
SHA-256 digest of the 2026 PDF is available. The query strings, observed
snippets, and access outcomes are recorded in
[`source-observations.json`](source-observations.json).

## What the indexed text supports

The indexed excerpt for §1.2 describes the equations as calculating lateral
values for single-fastener connections. It defines the equation output as a
reference 5%-offset yield value `P`; §1.3 identifies `Z` as a reference
lateral design value formed from applicable yield-mode values and an NDS
reduction term. The same §1.2 excerpt lists tension, bearing, shear, spacing,
group action, member strength, and other subjects as **NDS design criteria**.
That list does not state a combined axial-fastener-tension interaction.

The indexed Table 1-1 excerpt is specifically titled for solid cross-section
members and displays single- and double-shear yield modes. Its mode III/IV
equation terms include labels `M_s` and `M_m`. Appendix A Table A2 is titled
for dowel bending yield strength `Fyb`; its indexed entry identifies bolts and
lag screws with `D ≥ 3/8 in`, along with drift pins, and shows a 45,000 psi
reference value. These excerpts support dowel bending and `Fyb` within the
lateral-yield method. They do not establish direct steel-bolt resistance to
axial tension, or an interaction for simultaneous axial tension, lateral
shear, and bolt bending. The exposed fragments do not include all variable
definitions, assumptions, adjustment rules, or table footnotes.

The indexed Table 1-2 excerpt covers a solid main member with hollow side
member(s). That table is not the solid-timber/solid-timber target topology;
it is recorded as a boundary observation only. Table 1-1 is the visible
solid-member table relevant to that topology, subject to full source review
and the report's complete applicability conditions.

## Axial-tension search and disposition

Narrow searches scoped to the exact 2026 PDF URL for “axial tension,”
“combined tension,” “tension forces in the fastener,” and a combined
tension/shear/bending interaction did not return a 2026-report excerpt
addressing those terms. A no-hit search result is not
evidence that the complete report contains no such equation. The exposed
reference to tension among NDS design criteria is likewise not an interaction
equation. Therefore the 2026 report's direct axial bolt-tension treatment and
any N+V+M interaction remain **unknown**.

This partial source observation does not close the existing `steel_direct`
gap. The ordinary-joint basis continues to distinguish NDS lateral-yield
`Fyb` from direct bolt tension and shear references; the method map's
simultaneous direct tension/shear/bending requirement remains pending. Do not
infer absence of every possible method, transfer the 2015 TR-12 scope to the
2026 edition, or treat the search index as a complete report review.

## Exact next source route

Obtain the complete PDF through the official AWC [Technical Reports entry](https://awc.org/collection/technical-reports/)
or direct AWC [TR-12 2026 PDF](https://awc.org/wp-content/uploads/2026/06/TR-12_2026_formatted.V3.pdf)
when accessible. Hash the retrieved bytes, verify edition and page content,
then review the complete scope, solid-member equations and variable
definitions, Appendix A, examples, and references for an explicit axial bolt
tension rule or a supported combined N+V+M method. Preserve the present
unknown unless the complete primary source resolves it.

## Preservation and validation

The existing attempt03, attempt05, attempt01 lateral-method packet, ordinary
bolt-resistance basis, criteria map, and task queue were read-only context.
Their observed SHA-256 values are pinned in the JSON record. This packet is
limited to this new attempt06 directory. No native/solver run, capacity
calculation, hardware selection, criterion disposition, test run, or existing
file edit was performed. `terminal-hashes.json` binds the exact bytes of this
README and `source-observations.json` and intentionally excludes itself.
