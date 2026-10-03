# Two knee spines: EC5 splitting applicability disposition

**Finite applicability task complete; the proposed 24 group/case EC5
beam-splitting comparisons lack a justified loaded-edge/group mapping.** All
four shafts have the same axis, so the crossed-corner exclusion does not apply.
The side pair transfers opposite transverse forces, including near-zero-
resultant couple states, and shares the timber path with the post pair. The
available primary sources do not establish independent Figure 8.1 checks for
that arrangement. This is a source-bound applicability inference, not physical
failure or a normative prohibition of every moment-transferring connection.

## Frozen source and actual topology

Only `knee_outer_left_spine` and `knee_outer_right_spine` are considered. Their
original six simultaneous cases remain `a12-rear`, `a12-forward`, `a12-left`,
`k12-right`, `k12-rear`, and `a1-rear`: 250 lb × 2, signed 300 N horizontal
action and the original 100 mm lever. The source point forces and free couples
remain authoritative. The completed transverse packet supplies the corrected
physical timber gravity and original allocated hardware wrenches, with the
unchanged **1.1111358300342407** gravity multiplier.

| Authenticated artifact under `rawlocal/` | SHA-256 |
| --- | --- |
| [Remaining twenty checks](rawlocal/remaining-block-transverse/attempt01/checks.json) | `f3118804d3a03df66d274d783ca93248757ac3d629de4a874d23e85da9a61f19` |
| [Remaining twenty receipt](rawlocal/remaining-block-transverse/attempt01/receipt.json) | `dce3437a105cdd269aec9ff98ac831c00d6e64e34a807c42254030ca4fffb519` |
| [Receipt-bound signed cuts](rawlocal/remaining-block-transverse/attempt01/cuts.jsonl.gz) | `86757d2db86751aa5cba5343df0065ac3d38cc7d69eeab71f02c55eedc72d4cc` |
| [Spine geometry and original source pins](rawlocal/knee-spine-net-sections/attempt02/checks.json) | `6b6c8df94f1ccab859ee980dd1835ba19286718f44e8a36ce6b9d0014064fc85` |

The original `member-screen-attempt02/four-screw-layout01` geometry, action
archive and member results matched their existing pins `c6113908…f453af`,
`ddfa3102…a7caf`, and `54f38885…965c5`, respectively. No force redistribution
or compatible-shaft replacement was made. The completed twenty-body packet
contains 19,536 finite cuts and no affected-body scope stops.

Local grain is global Z, `u` is X, and `v` is Y. Stock is 276.3 mm along grain,
38.1 mm along `u`, and 139.7 mm along `v`; all four 7.5 mm bores run through
`u`. The two actual connection groups are:

| Group | Receivers | Bore centers `(grain, v)`, mm | Entire bore extent along grain, mm |
| --- | --- | --- | --- |
| Post pair | Spine / outer post | `(31.75, −25.4)`, `(73.8, −25.4)` | 28…77.55 |
| Continuous side pair | Spine / side member / inner frame block | `(191.615553, 5.971913)`, `(226.087553, 34.897356)` | 187.865553…229.837553 |

**70.05 mm is the second post bore's lower tangency, not its center.** The
frozen geometry gives 73.8 mm; this note changes no geometry.

Original contact patches span grain stations 0…99.2 mm against the post,
99.2…137.3 mm against the header, and 137.3…276.3 mm against the side member;
the floor contact is at grain station 0. Post/header/side face normals are
along `u`; floor reaction and physical gravity are along grain. These actions
therefore supply no direct `v` force under the recorded frictionless source,
but their eccentric forces and couples remain part of the full section wrench.
The physical connection zones extend beyond the bore envelopes. Bore-envelope
cuts can diagnose `Vv`; they cannot establish independent complete-joint zones.

## What the primary EC5/JRC evidence supports

The [CEN AC:2006 corrigendum, PDF p.4](https://cms.sia.ch/en/api/getMedia/559)
corrects §8.1.4 Eq. (8.4), identifies the two demands as design section shears
on opposite sides of the connection, and directs design resistance conversion
to §2.4.3. [JRC Dietsch slides 29–30](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1995_3_Dietsch.pdf)
reproduce the softwood Figure 8.1 arrangement and its geometric definitions;
[JRC Leijten slides 63–64](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1995_5_Leijten.pdf)
explain the maximum-side-shear convention. The cache contains this primary
corrigendum and official explanatory slides, **not the full normative §8.1.4**.

For a justified single loaded-edge arrangement the candidate plane would be
grain–`v`, normal to shaft axis `u`: `b=38.1 mm`, `h=139.7 mm`, and `w=1`
for bolts. With dimensions in mm, the raw characteristic reference in N is

```text
F90,Rk = 14 b w sqrt(he / (1 − he/h))
Fv,Ed = max(|Vv,left|, |Vv,right|)
```

Both section traces must lie immediately outside the entire identified group,
include all simultaneous actions, and retain signed
`[N, Vu, Vv, Tgrain, Mu, Mv]`. `he` measures from the actual loaded `v` edge
to the most distant fastener center. For the post pair, the geometric choices
are 95.25 mm from the `+v` edge or 44.45 mm from the `−v` edge. For the side
pair they are approximately 63.878087 mm or 104.747356 mm, respectively.
These are geometric alternatives, not selected resistance inputs.

The current working-load section values are not independently established EC5
design actions. No raw characteristic reference is a design resistance or an
NDS allowable value. No `gamma_M`, duration/service factor, species factor,
or characteristic-to-design conversion is adopted; the gravity multiplier is
not such a factor.

## Exact finite obstruction

The original `left / a12-left` transverse bolt forces are post
**+15.002372457 / +136.494539337 N** and side
**−512.957417120 / +361.460505326 N**. Right / `k12-right` likewise has side
**−499.533948672 / +353.465996934 N**. In every one of the twelve spine/case
states, the two side bolts have opposing `v` signs. Their differing grain and
`v` coordinates transmit a force couple; one net sign does not establish
which loaded-edge path represents the complete pair.

Cancellation is explicit in the source: left / `a1-rear` side forces are
**−37.46676035333633 / +37.466760353336966 N**, while its post transverse
forces are numerical zero. Thus a nearly zero exterior `Vv` can coexist with
a loaded side connection. It cannot qualify that couple's internal timber path.

The following are **existing saved cuts**, not new arithmetic. For left /
`a12-left`, the side-pair lower exterior trace at
`s=187.86555301851 mm`, before, is

```text
[103.577457527, 416.931787219, −151.496911794,
 −14674.607202523, −20376.245269832, 10626.272954310]  (N, N·mm)
```

The upper exterior trace at `s=229.83755295886 mm`, after, has
`Vv=−1.7053025658242404e−13 N`. Between the two side shafts, immediately after
`s=191.61555301851 mm`, the saved `Vv` is **+361.4605053261092 N**.
The hypothetical exterior maximum would therefore be about 151.497 N in this
state; it supplies no check of the intervening reversal or its full wrench.
Existing torque and both moments remain material demands. Original free
couples are already included in these cuts, including numerical residuals;
later compatible-shaft end couples must not be silently dropped or substituted.

Checking each of the two host groups separately would also require a supported
assignment of their shared grain-parallel splitting paths. The
[author's WCTE 2014 multiple-connection paper, PDF pp.2–3](https://pure.tue.nl/ws/portalfiles/portal/3910148/580752898430977.pdf)
describes the single-connection model's exterior crack scope and documents
that independent capacity addition for multiple connections is not generally
supported. It supplies no interaction rule for these two groups, their opposing
bolt actions or their contact zones. Combining all four bolts into one group,
splitting the side pair into independent one-bolt checks, or choosing the
smaller of two edge references would each need a justified applicability
argument; none is supplied by the cached evidence.

The active post pairs provide a candidate `+v` loaded-edge arrangement with
`he=95.25 mm`; same-axis geometry alone is not the obstruction. The side pair's
opposing actions leave its loaded-edge reduction unestablished, and the sources
provide no independent shared-path treatment for the two groups. These are the
finite missing applicability arguments for the proposed 24 comparisons.
An exterior-crack scalar, if justified, would still not qualify the internal
couple path.

## Disposition and retained limits

The saved `v`-normal tensile lower bounds **430.147568 N** on the left and
**424.262642 N** on the right remain opening/load-path evidence. They are
not EC5 `Fv,Ed`, bolt allocations, or splitting resistances. The `u`-axis
shafts provide no axial tie across a `v`-normal split. Existing axial tie
forces are already counted and cannot be credited again as reinforcement.

[NDS 2024 §§11.1.2–11.1.3, p.70](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf)
retain the local multiple-fastener/eccentric-load requirement; they supply no
numerical resistance for this transverse path. Existing grain, steel,
washer/contact and torque checks, including [the bounded K contact result](knee-contact-entry.md),
retain their own limits. Saved simultaneous-force scope, representative seating,
false source stability gates and unverified floor support remain unchanged.
Splitting capacity is unassigned; complete-joint acceptance remains false.

No producer or numerical resistance output is prepared because that
loaded-edge/group mapping is unestablished. This completes the bounded
source/applicability question without adding load variants, a new model, or a
routine qualification prerequisite. Only frozen documents, source arrays,
saved cuts and hashes were read. No engineering run, test, review, native/CAD/
frame evaluation, hardware change, staging or commit was performed.

The primary PDFs matched [the existing source pins](../../upper-outer-load-path-2026-10-01/splitting-source-cache/source-pins.json);
the read AWC Chapter 11 matched `45a3d78d…92d33`. This note and the existing
frozen packets stay active. Ignored `rawlocal/knee-spine-splitting/preparation/`
contains only rendered source pages for reading; no source evidence is replaced
or proposed for pruning. Parent owns integration into the shared summary.
