# Splitting resistance: primary reference scope

## Disposition

**The first-generation EC5 expression is a supported softwood beam-connection
reference, but it is not an established allowable resistance for the complete
current cleats, end-grain connections or crossed/opposing connection actions.**
DF-L is not excluded merely because it is Douglas fir, and short grain length
is not itself an explicit §8.1.4 prohibition. Those observations do not establish
the actual load/support mapping, material equivalence or design format.

This note completes the bounded source investigation. It assigns no new
capacity, utilization, physical failure or hardware requirement. The parent's
[all-joint assessment](all-joint-splitting/README.md) retains its 30 duties and
44 timber bodies. Reviewed 104-axis global authority and the unadopted 108-axis
proposal remain distinct. N05/N06 bearing arithmetic does not supply splitting
resistance.

## Sources and edition boundaries

The equation was checked visually in the **primary CEN AC:2006 corrigendum,
PDF p.4**, and in the primary standard scan, **printed p.57 / PDF p.59**.
Figure 8.1 was inspected in the official **JRC Dietsch slide 30**; slides
29–30 reproduce the scope and geometry. The **JRC Leijten slides 63–64**
explain the section-shear criterion. These workshop documents are official
explanations, not replacement normative standards.
[CEN corrigendum](https://cms.sia.ch/en/api/getMedia/559),
[JRC Dietsch](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1995_3_Dietsch.pdf),
[JRC Leijten](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1995_5_Leijten.pdf).

The full scan identifies **BS EN 1995-1-1:2004+A1:2008**, incorporating the
June 2006 corrigendum. Its host is an unofficial mirror; its publisher text is
primary, but it has no authenticated publisher download binding here. It
corroborates the official equation/figure and supplies the observed surrounding
§§2.4.3 and 3.2 text. It is not proof of an adopted A2:2014 or 2025 edition.
[Primary standard scan, printed pp.25–26 and 56–58](https://www.phd.eng.br/wp-content/uploads/2015/12/en.1995.1.1.2004.pdf).

**EN 1995-1-1:2025 exists.** BSI records publication on November 30, 2025
and UK coexistence with first-generation standards until March 30, 2028;
applicability depends on the relevant authority/project. The detailed final
2025 splitting provisions were not inspected. Neither the old equation nor an
unverified committee draft is attributed to that edition.
[BSI edition and transition record](https://knowledge.bsigroup.com/products/eurocode-5-design-of-timber-structures-general-rules-and-rules-for-buildings).

## EC5 equation, dimensions and load definition

The corrected first-generation equation is:

```text
F90,Rk = 14 b w sqrt(he / (1 - he/h))                       (8.4)
Fv,Ed <= F90,Rd                                            (8.2)
Fv,Ed = max(Fv,Ed,1, Fv,Ed,2)                              (8.3)
```

`F90,Rk` is characteristic resistance in **N**. The 14 coefficient has the
implied units **N/mm^(3/2)**; it is not dimensionless. The radical's denominator
is `1 - he/h`, not `(1 - he)/h`. The positive geometric domain is
`0 < he < h`; the singular limit at `he=h` is not infinite physical capacity.
These dimensional/domain statements follow directly from the verified
equation. No `Fv`, `Ft`, density or fracture energy is an input to (8.4).
[Corrected equation and demand legend, CEN PDF p.4](https://cms.sia.ch/en/api/getMedia/559).

| Quantity | Required Figure 8.1 interpretation |
| --- | --- |
| `h`, mm | Checked timber depth perpendicular to its grain in the inclined-force plane. It is not grain length. |
| `b`, mm | Checked timber thickness normal to that plane. Figure 8.1 shows a central thickness `b`, or two timber sides of `b/2` each. Thickness cannot be pooled across unlike receivers without the corresponding force/support allocation. |
| `he`, mm | Distance from the actual loaded edge to the center of the farthest fastener; for punched plates, to the plate edge. It is not the nearest-fastener distance or grain-end distance. |
| `w` | Dimensionless; **1 for the current bolts**. The punched-plate branch does not apply to washers or a steel side plate. |
| `alpha` (`theta` in the task), radians or degrees consistently | Inclined connection-force angle to this timber's grain; not the bolt-axis angle or a global frame angle. |

These geometry definitions and the explicit **softwood / Figure 8.1** scope
are reproduced in [JRC Dietsch slides 29–30](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1995_3_Dietsch.pdf).

### Actual transverse action and section shears

The splitting cause identified in §8.1.4 is the connection's tension component
perpendicular to grain, `FEd sin(alpha)`. Equations (8.2)–(8.3) check the
larger **section shear beside the connection**, not an optimized tensile
resultant on a transverse cut. Interpret the two Figure shear values as
positive magnitudes; maintain consistent signs when recovering them from the
saved wrenches.
[JRC Leijten slides 63–64](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1995_5_Leijten.pdf).

For a candidate group, the parent needs its actual signed timber forces,
physical application points and free couples in each of the six simultaneous
cases. With unit grain `g` and an established in-plane transverse direction
`t`, recover the connection component as `P_t = sum(f_i dot t)`. Only for a
single coplanar force resultant with the appropriate opening direction does
`abs(P_t)` represent `F sin(theta)`. Report the individual signed forces and
couple as well: a small resultant can conceal opposing forces. This is a
mechanics interpretation, not a new code interpolation.

Recover both adjacent grain-normal section shears from **all** actions on
their respective sides, including contacts, gravity and other connections.
For the simple single-load arrangement with two same-direction balancing
reactions and no other transverse action, equilibrium partitions `P_t` between
the two sides; `abs(P_t)` then bounds the larger shear. Equality needs the
particular support allocation. Without those conditions, neither equality nor
that bound follows. A free couple can also leave an internal opening path
outside the exterior-shear scalar's qualification.

The existing cut-hull scalar solves a different problem: minimum tensile
normal traction compatible with a particular cut wrench and an enlarged
pressure hull. It has different cut orientation, traction component and
optimization constraints. No equivalence to `F sin(theta)` or `Fv,Ed` is
proved. **Do not compare an EC5 resistance to that scalar**, including the
historical 0.054537792 N corner result or the spine opening bounds.

### Supports, ends and groups

Figure 8.1 depicts a grain-parallel receiving member, an inclined connected
member, one identified loaded edge and balancing shears on both sides. A
physical support need not be exactly at each section trace. It must provide
the stated equilibrium and crack/load path. End distance, fastener layout,
recesses and other duties still require their applicable checks. The equation
contains no explicit end-distance, group-moment or three-dimensional
interaction term; this omission is not permission to ignore those effects.

Short blocks are therefore not automatically outside the printed clause.
Their actual boundary conditions must establish a matching receiving-member
component. The primary multiple-connection experiments found interaction and
conservative EC5 predictions for their **simply supported beam** configurations;
they do not validate independent resistance addition for the current cleats.
[Leijten, WCTE 2014, PDF pp.2–6](https://pure.tue.nl/ws/portalfiles/portal/3910148/580752898430977.pdf).

## Material and design-format boundaries

Section 8.1.4(3) names softwoods, without a spruce-only or C24-only restriction.
For a Eurocode solid-timber design, the observed §3.2(1)P also requires
EN 14081-1 timber; EN 338 supplies strength classes. §3.1.1 allows supported
property determination through tests, comparisons or established relations.
A US DF-L No.2 label alone establishes neither that product/grading basis nor
a particular Eurocode strength class.
[Primary standard scan, printed pp.26 and 57](https://www.phd.eng.br/wp-content/uploads/2015/12/en.1995.1.1.2004.pdf).

The pinned [material inputs](../../hardware-material-specification-2026-09-30/material-inputs.json)
are a conditional dry DF-L No.2 **NDS** scenario, not delivered-stock
observations. Their base parallel shear is 180 psi; there is no sawn-lumber
perpendicular tensile value, splitting characteristic or fracture energy.
Four section-ripped blocks already have an unresolved final-size grade basis.
Analytical density and NDS specific gravity do not fill a missing characteristic
fracture property. Under a separately declared matching softwood geometry
hypothesis, (8.4) can be recorded as a raw reference without inventing those
properties; calling it the actual DF-L cleat characteristic resistance requires
an applicability basis.

There is also substantive primary research caution. Jensen et al.'s **2012
WCTE paper**, printed pp.392–394, tested Douglas-fir **glulam** and Radiata-pine
products and challenged using 14 universally. The tested products and statistical
results are not DF-L No.2 sawn-cleat properties. The paper also questions the
maximum-side-shear rule on its tested beams; that research criticism does not
silently amend the normative rule. No test coefficient, glulam value or new
fracture parameter is transferred here.
[Authors' paper, institutional repository](https://ltu.diva-portal.org/smash/get/diva2%3A1013109/FULLTEXT01.pdf).

The observed §2.4.3 conversion is `F90,Rd = kmod F90,Rk / gammaM`.
`kmod` accounts for moisture/service and action duration; `gammaM` belongs to
the adopted partial-factor basis. Associated **ULS design actions**, material
classification and a coherent applicable National Annex must be stated.
[Primary standard scan, printed p.25](https://www.phd.eng.br/wp-content/uploads/2015/12/en.1995.1.1.2004.pdf),
[JRC National Annex guidance](https://eurocodes.jrc.ec.europa.eu/en-eurocodes-implementation/nationally-determined-parameters).

The current six nominal states are not authenticated EC5 ULS combinations.
Their gravity correction is a modeled-load correction, not `kmod`, `gammaM`
or NDS `CD`. Neither the steel 1.25 convention nor an NDS duration multiplier
converts (8.4) into ASD. A raw-characteristic comparison would remain explicitly
non-adopted. An alternative ASD method needs a supported allowance/reliability
derivation for the same material, topology and demand; no conversion is supplied
by combining unrelated factors.

## Current geometry and load fit

These are component applicability decisions, not another numerical census.
Existing [corner](corner-splitting-disposition.md),
[spine](knee-spine-splitting.md), [detailing](bolt-group-applicability.md) and
[proposal geometry](knee-bridge-geometry.md) supply the topology.

| Actual connection class | Possible matching component / exact limitation |
| --- | --- |
| Ordinary side-grain bolt into a frame receiver | An identified planar receiving-member component may match Figure 8.1. It needs actual `F sin(theta)`, both section shears, loaded edge, farthest fastener, supports and material/design basis. Another timber's grain or group cannot be inherited. No blanket failure is established. |
| Four outer corner cleats with orthogonal side/rail axes | For rail-induced local `u` action, candidate Figure plane is grain–`u`, with `h` along `u` and `b` along `v`. The complete block also has the orthogonal pair, washer actions, contacts and couples. One planar scalar does not cover that combined duty. |
| Existing knee spine `u` shafts | Grain–`v` is the candidate lateral-force plane: `b=38.1 mm`, `h=139.7 mm`. Same-axis geometry is potentially suitable. Opposing side-pair actions and its shared post/contact path prevent assuming one resultant/loaded edge or independent capacities. Historical isolated-shaft forces cannot replace current common forces. |
| Proposed internal spine `v` ties | The four additional ties belong to the 108 proposal, not the 104 global lateral register. Their axial washer/anchorage action is not a Figure 8.1 lateral splitting capacity. Their allocated force is already counted. The modified six-bore stock and any other split path need their own mapping. |
| Fastener axis parallel to a cleat's grain / end-grain connection | Load angle to grain and fastener-axis orientation are different quantities. A side-grain beam figure cannot be imposed by rotating labels onto this end face. Side-grain scope on the other receiver does not qualify this cleat. The NDS end-grain adjustment to lateral fastener resistance is not a splitting allowance. |
| Short, housed or obliquely cut cleat; multiple shared groups | Identify retained depth/thickness, actual end faces, loaded edge and support/crack path. Stock-envelope dimensions alone do not establish a net path, compatible support or independence. Opposing forces, torque and free moments must remain assigned to supported simultaneous mechanisms. |

The latest detailing note records nonordinary/end-face classification limits,
not a pure table shortfall that this note turns into physical failure. A bolt
steel pass, a washer compression construction, a contact mean or a zero normal
opening lower bound does not provide the missing complete timber resistance.

## NDS and Commentary: a matching ASD component route

The pinned **NDS 2024 §3.4.4.1**, printed p.21 / PDF p.7, provides shear
equations for **rectangular bending members** connected by bolts, lag screws,
split rings or shear plates. For bolts, `de` is depth `d` minus distance from
the unloaded edge to the nearest bolt center. With inches, psi and pounds:

```text
connection less than 5d from member end:
Vr' = [(2/3) Fv' b de] (de/d)^2                            (3.4-6)

connection at least 5d from member end:
Vr' = (2/3) Fv' b de                                      (3.4-7)
```

`V` comes from engineering mechanics; `Fv'` is the applicable adjusted shear
value. Consistent conversion of the entire equation is possible. Neither
the 5d branch nor `de` can be selected from nominal member names. A notch on
a concealed bearing plate follows the separate §3.4.3.1 route.
[NDS 2024 Chapter 3, Figure 3E and §3.4.4.1](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf).

This can provide a **matching NDS ASD beam-connection shear check using the
existing conditional material basis**, after its geometry, member behavior,
actual induced shear and applicable adjustments are established. It does not
assign a universal resistance to a short crossed cleat or axial washer plug.
The missing evidence is the component map and applicable adjusted `Fv'`, not
an invented `Ft_perp` or new load/stiffness choice. A pass of this component
would still leave any separate eccentric opening, torsion or anchorage path.

The official **March 2026 errata** corrects old references from §3.4.3.3 to
§3.4.4.1. Its current **C12.5.1** edge-distance excerpt expressly calls for
the reduced-depth shear check for perpendicular connections. This is directly
verified 2024 Commentary evidence.
[AWC errata, PDF pp.1–2](https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf).

NDS §§11.1.2–11.1.3 require local mechanics and appropriate procedures or
tests for eccentric connections inducing perpendicular tension; §11.1.1.3
permits supported alternative procedures. They do not prescribe a new full
three-dimensional solve or physical test in every case. NDS §3.8.2 retains
the perpendicular-tension concern. A matching simpler proof remains possible.
[NDS 2024 Chapter 11, printed p.70](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf).

For ordinary perpendicular bolt loading, Table 12.5.1C supplies loaded and
unloaded edge requirements; its footnote separately restricts medium/heavy
loads suspended below a beam's neutral axis without suitable reinforcement.
Section 12.5.2.2 applies `Ceg=0.67` to **lateral** resistance for dowels
inserted along the main member's fibers. Neither provision supplies the
current end-grain cleat's complete splitting capacity. Exact applicability
remains in the detailing/group packet.
[NDS 2024 Chapter 12, printed pp.99–100](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-12-Dowel-Type-Fasteners.pdf).

### Commentary provenance correction for parent integration

The authenticated Chapter 3 PDF at
`rawlocal/profile-method-completion/sources/nds2024-chapter3.pdf` contains
**12 specification pages**. It contains §3.8.2 at printed p.24; it does **not**
contain C3.8.2 or printed p.222. The root resistance-routes attribution of
C3.8.2 to that file is unsupported and needs parent correction. No root path
is edited by this task.

The directly inspected **2018 Commentary**, C3.8.2 at printed p.208 and
C11.1.3 at p.249, explains the absence of commercial sawn-lumber perpendicular
tensile design values and discusses mechanical reinforcement and drying.
Its small-clear-wood discussion is not a sawn-lumber `Ft_perp = Fv/3` rule.
Glulam radial tension is a different product/action. These historical passages
are context; current C3.8.2 wording remains unverified. Current C12.5.1 is
supported by the 2026 errata excerpt above.
[Official 2018 Commentary, PDF pp.16 and 57](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf).

## Parent integration and remaining limits

1. Correct the Chapter 3 Commentary attribution and carry the current
   §3.4.4.1/C12.5.1 shear route as a bounded alternative for matching receivers.
2. Retain first-generation (8.4) only as a scoped characteristic reference.
   Species wording and short length alone are not blanket exclusions; the
   actual group, support and coherent design basis remain necessary.
3. If pursuing either route, join each actual timber/group to its same-state
   signed lateral forces, contacts and couples. Establish `F sin(theta)` and
   the required section shears; do not substitute cut-hull minima, old isolated
   fits, independent peaks or already allocated tie force as reserve.
4. A supported existing load path or applicable simpler local mechanics proof
   may resolve a component before hardware changes. Current evidence does not
   establish every opening/anchorage path or a complete splitting pass.

This note changes no geometry, material, force, floor law, authority or adopted
capacity. No engineering arithmetic, numerical/CAD/frame/native execution,
software test, review loop, staging or commit was performed. Source PDFs were
read or rendered in memory using existing cached dependencies; no downloads,
PDF copies or render files were written into the checkout. Existing evidence
stays active; there are no new raw artifacts to archive.

## Read-only source fingerprints

The first six source files already exist. The remaining PDF digests identify
bytes fetched into memory only; URLs are given above, with no repinning of
existing evidence.

| Source | SHA-256 |
| --- | --- |
| NDS 2024 Chapter 3 | `205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644` |
| NDS 2024 Chapter 11 | `45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33` |
| NDS 2024 Chapter 12 | `53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f` |
| CEN AC:2006 corrigendum | `ff5bd62c586cc714eed9b8b7e557bbe030f36fe7e3ccd29dd10a24db755b03a5` |
| JRC Dietsch | `20b6cfc83a1b3a1afb124f9c7cc337ab3b23c141ebe3da8c74906a8eece8017d` |
| JRC Leijten | `b3d6a181479e7b07ae1a7a86e85ffe99d848f85af708225428b8d24d4194689d` |
| Mirrored CEN/BSI 2004+A1:2008 scan | `05042b33af906ef5b9c3eaace5c14258f11fa2bc69ee9cb2479d611634444c8c` |
| Jensen et al., WCTE 2012 | `6309ccc1836046675b0914f0b04a44ee54d2b208f40f4b458c9e270e3cd6e15a` |
| Official NDS 2018 Commentary | `3402c7703cddef3e6693741ebaef9bfd0c1b0ddf075762c6f411fe1916751f7d` |
| Existing conditional material-inputs.json | `0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a` |
| Existing 108 proposal geometry manifest | `254dd58d2f311553b32637b01b85b8bacbc0b474acfee667597333c501afe147` |

The current gravity input read was `b260af3d53a199e66962caf6c7074086e1d433526e43d263a3f1247ba4c61b99`
(`rawlocal/knee-bridge-gravity/attempt01/model-inputs.json`), with saved factor
1.1110134616260479. The old spine note's different gravity factor and forces
are historical applicability examples, not current resistance demands. No new
load conversion or source authority is inferred from either.
