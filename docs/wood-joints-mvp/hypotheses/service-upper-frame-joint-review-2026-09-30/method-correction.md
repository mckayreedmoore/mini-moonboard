# Upper-joint end-method correction, September 30, 2026

The earlier [uppermost-block README](../upper-frame-joint-review-2026-09-30/README.md)
correctly recorded signed actions and its pure parallel end-distance
sensitivities. Its generic statement that oblique grain loading requires the
NDS shear-area interpretation is misleading for the current bolt-normal
lateral actions. This note supersedes that interpretation and the wording of
the same generic oblique-loading sentence in the
[representative directional audit](../../representative-directional-end-edge-audit.md).
It preserves their numerical and geometric records and adopts no capacity.

## The two angles are different

NDS-2024 §12.5.1.2(b) addresses loading at an angle to the **fastener axis**
through an equivalent shear-area comparison. The current upper lateral
vectors lie normal to their bolt axes, despite being oblique to grain.
The separate axial outer-seat ties represent a different transfer path;
they do not turn a bolt-normal lateral vector into that angled-loading case.
The method source is the pinned [official AWC Chapter 12 PDF](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf),
SHA-256 `5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`.
The edition is identified on [AWC's 2024 NDS page](https://awc.org/resources/2024-nds/).
The inspected normative rule is on printed page 98. Despite its filename,
this Chapter 12 PDF contains no Commentary.

The official **2018** Commentary C12.5.1.2, printed page 263, supports linear
interpolation of tension-end requirements for an angle **to grain**. That
historical guidance is used here as a declared sensitivity. With conditional
softwood and nominal D = 6.35 mm, the full end-distance comparison is
`e_full(alpha) = D * (7 - 3 * alpha / 90)`, with alpha in degrees from grain.
The corresponding half-distance floor is `e_full/2`. Within that branch,
`min(1, e_actual/e_full)` is the eligible square-end factor when the half
floor is met. The source is AWC's [official historical Commentary](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf),
SHA-256 `3402c7703cddef3e6693741ebaef9bfd0c1b0ddf075762c6f411fe1916751f7d`.

The corresponding **2024 Commentary has not been directly verified**.
The pinned normative 2024 end table provides the pure-direction values;
it does not supply this interpolation. Earlier repository assertions do not
substitute for that missing primary source. AWC lists the Commentary in its
[2024 package](https://awc.org/resources/2024-nds/). This packet does not adopt
the historical interpolation as a current design rule.

The smallest applicable factor for a defined group and multiple-shear
connection is specified by normative 2024 §12.5.1.2; spacing remains a
separate branch. Historical Commentary C12.5.1.3, printed page 264, discusses
the absence of intermediate-angle edge guidance. Normative 2024 Table
12.5.1C also lists pure-direction rows, but its current Commentary treatment
has not been directly checked. End interpolation therefore supplies no
oblique-edge rule or factor here. The verified primary sources are the
[2024 specification](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
and the separately identified [historical Commentary](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf).

## Current square-end branch

[end_branch.py](end_branch.py) independently recomputes grain and cross-grain
components from each member's signed physical vector, then alpha using
`atan2(abs(Fcross), abs(Fgrain))`. It checks both grain and lateral action
against the recorded bolt axis. The maximum lateral axial projection is
8.46e-16 N. The signs select the loaded boundary separately for each member;
the equal-and-opposite action is retained.

Scope is the two uppermost center-principal bolt pairs and both shortened G7
interfaces: eight bolts, both members, three cases and seven increments.
The outer-square-end tension branch is explicitly assumed. The base-center
principal's grain-negative terminal is an angled foot profile, so those
records are excluded. Finished STEP hashes are checked; the preserved
[finite-face query and review](../evaluation-resume-2026-09-24/ordinary-finished-end-edge-query-attempt01/independent-review.md)
explain why the foot profile must not be counted as a square-cut end.
That query's sampled stations do not establish continuous thickness extrema.
No actual timber, hole or cut has been inspected.

The table gives full-load minima across each provisional pair's eligible
square-end records, including both cleat and host. It defines an extraction
scope, not an independently resisting bolt group.

| Pair scope | A1-rear | A12-rear | K12-rear |
| --- | ---: | ---: | ---: |
| Top center left principal pair | 1.000* | 0.659 | 0.753 |
| Top center right principal pair | 1.000 | 0.835 | 0.630 |
| G7 rail pair | 0.846 | 1.000 | 0.882 |
| G7 principal pair | 1.000* | 1.000* | 1.000* |

`*` Host directions toward the angled foot are excluded. The number applies
only to eligible square-end records; it does not close that pair's end check.
Across all seven increments, the displayed minima are unchanged at this
precision. There are 280 eligible square-end records and 56 excluded angled
foot records. None of the eligible distances is below the interpolated half
floor. This is a bounded geometry comparison, not a complete-joint pass.

For top-center `principal_2`, the short +grain terminal is 27.9 mm away.
Left A12 has alpha = 10.056° and e_full = 42.3215 mm, giving 0.659;
right K12 has alpha = 0.720° and e_full = 44.2976 mm, giving 0.630.
Right A1 is much closer to perpendicular, alpha = 86.611°, and its full
reference is 26.1173 mm, giving 1.000. Left A1 loads the opposite foot
profile instead. The earlier 27.9/44.45 = 0.628 remains a pure-parallel
tension sensitivity and should not replace these signed angle-specific
comparisons.

For G7 `upper_rail_1` on the cleat, the signed force points toward the
26.95 mm square end in all three full-load samples. Alpha is 59.429° for
A1, 84.713° for A12 and 65.608° for K12. The angle-specific minima above
replace the earlier pure-parallel 26.95/44.45 = 0.606 sensitivity for those
rows. Neither result changes the separate 26.95 mm host-edge comparison.

## Applicability limits and replay

[end-branch-freeze.json](end-branch-freeze.json) pins the action reports and
supporting geometry/method records. [conditional-end-branches.json](conditional-end-branches.json)
retains 336 member-direction records and 84 pair-history summaries;
[CSV](conditional-end-branches.csv) makes the branch inputs inspectable.
Known-answer checks cover the parallel, 45° and perpendicular endpoints.

The interpolation remains a declared historical-method sensitivity. Current
edition verification, relevant member loading and square-end applicability
are unresolved. Complete group identity, spacing, shared-cleat
behavior, oblique edges, local bores, member shear/splitting and combined
axial transfer still require their own evidence. The script applies no
factor to resistance and claims no accepted end/group/joint criterion.
This correction removes a method conflation; it does not remove those
distinct engineering checks or add a new blanket approval prerequisite.
