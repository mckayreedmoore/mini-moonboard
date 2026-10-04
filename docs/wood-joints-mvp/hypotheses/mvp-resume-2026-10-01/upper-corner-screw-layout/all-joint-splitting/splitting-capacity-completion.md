# Conditional transverse tension and finite splitting comparisons

The active normal-traction component is numerically complete under the stated
conditional material scenario. It covers all 44 current timber bodies in all
12 accepted coupled frame states, with both limiting sides of the local u = 0
and v = 0 transverse cuts. There are **2,112 actual comparisons**, no geometry
limits and no reference exceedances. The maximum conditional Ft90 index is
**0.9457669511**, at `base_post_outer_left`, `a12-left_gap`, local axis 2,
immediately after the load station. This is a nominal normal-traction component;
it does not establish bore stress concentration, crack resistance or complete
splitting acceptance.

The active force authority is the accepted `frame-attempt08` response and
`joint-frame-action-reconciliation/attempt03` exports, whose receipt SHA256 is
`370dafc75a90967cc45e9888bdbd5610fa2df6930a5821d4cd52d01bae70904e`.
The two requested zero-gap states `a12-left_zero` and `k12-right_zero` have no
audited positive-bearing floor branch and supply no accepted forces. Their
88 timber-state slots are explicitly unavailable; they are not zero demands,
strength passes or proofs of physical infeasibility.

The first active finite body, `center_post_cleat_left`, now has **384 actual
comparisons** covering all eight declared paths, twelve accepted states, both
R/T bindings and 20/15 mm grids. Its conditional initiation index reaches
**12.45866758**; 136 path rows exceed that reference. The separate free-face and
contact-upper indices reach 0.02127655 and 0.04453979. Ninety-four stress mesh
comparisons exceed the original 20% guard; neither energy measure does. These
are retained conditional comparisons and mesh limits, not complete splitting
qualification. A second cleat has 96 fine-grid and 72 coarse-grid comparisons,
bringing the actual total to **552 of 37,056**; **36,504 remain pending**.

The preserved direct-method plan has thirty body domains within its 180,000 DOF
gate, twelve dimension limits and two profile limits. Those dispositions are
not inherited by the localized method. Exact condensation and its first current
body fields are supported. Chunked stiffness allocation and exact cross-plane
reuse now pass a bounded current right-cleat project and its saved-field audit.
The actual 1:12 profile adapter passes its known-answer and geometry checks;
current leg fields remain pending. Earlier solid comparisons retain their original force
authority and cannot qualify the changed coupled actions.

## Active saved-action and exact-section evidence

The pure adapter [coupled-prepared01](rawlocal/splitting-capacity-completion/coupled-prepared01/plan.json)
contains 528 accepted timber-state records and the complete fourteen-state
source disposition inventory. It copies every original point, signed force,
free couple, body gravity term and source availability flag exactly. It preserves
replaced canonical rows as flagged unavailable placeholders while retaining their
physical replacement actions; it never treats the placeholders as measured zero
forces. The saved body loads already contain gravity, so the adapter adds none.
All 528 full body wrenches satisfy 1e-7 N / 1e-5 Nmm gates without balancing
corrections. All four source branches match the same current STEP hashes,
origins, material frames and dimensions for all 44 timbers.

The [active nominal result](rawlocal/splitting-capacity-completion/coupled-nominal02/nominal.json)
and [receipt](rawlocal/splitting-capacity-completion/coupled-nominal02/receipt.json)
record the actual component comparisons. Result SHA256:
`4863425df8dbddadad7984a4ee230fb125484531136e700ef9a4ed3f0fbcf662`.
Receipt SHA256:
`b4d05b34403cabae0e02ae62d5a47a6961fa5897fb24eaca35ea8fd323ac2674`.
The [source-bound component aggregate](rawlocal/splitting-capacity-completion/active-component-coverage01/summary.json)
records normal-component completion separately from the pending fracture work;
its summary SHA256 is `74a7aa321978a3088107143073e3de21d4f67790573dbba284aa49ed397817db`.
There are 1,056 supported state/orientation pairs and 2,112 before/after cuts.
The signed normal force and both normal-force moments define one affine normal
traction on the exact retained section. Source actions in the 1e-7 mm plane
band are included immediately before and excluded immediately after the
station. Both sides are calculated. Signed shear and torsion remain separate
component obligations.

Thirty-six bodies use the existing rectangle/full-circle/strip integrals. The
remaining six clipped hosts and two legs use the source-bound
[exact transverse geometry helper](rawlocal/splitting-capacity-completion/project-draft09/transverse-section-geometry.py),
SHA256 `42f6c10f88681747c60779761355b782b3298e0a24be4622497ef205504e9a6b`.
It clips saved outward half-planes and uses the actual three-zone 1:12 taper
recipe. It supplies polygon moments, disjoint full-circle deductions and clipped
rectangular bore strips, plus retained vertices for the affine maximum.
Unsupported partial circles, oblique ellipses or overlapping voids are refused.
Its independent [polygon/cylinder/taper oracle](rawlocal/splitting-capacity-completion/project-draft09/transverse-section-geometry-oracle02.json), SHA256
`65626c8f309e2bee1bbf7a8215dfea3494c10316b28d942b337d3f5e6922d2f1`,
and [original-domain oracle](rawlocal/splitting-capacity-completion/project-draft09/transverse-section-geometry-original-domain-oracle03.json), SHA256
`f2c6215788118452312294e4e748f48cfd4b2d50f1badda12af0edfd558ad6d0`,
are in the same frozen packet. The independent integrated audit verifies all
295 transitive bindings and all 2,112 current component rows; audit SHA256 is
`d1b7c6357ac472386defa1ea46c31954d16be96dd56f183cd9310397060a73d8`.
No horizontal shoulder or changed physical recess is introduced.

The source's `non_qualifying_parametric_screw_withdrawal` spring forces retain
that scalar-law hypothesis. These component calculations do not qualify the
screw stiffness or resistance, the assumed no-slip floor, actual timber or
hardware. All complete-joint and physical-release flags remain false.

## Conditional resistance scenario and finite solid law

The independently declared scenario is **Ft90 = 0.500 MPa** and
**Gc >= 0.100 N/mm in every assessed mode, mixture and R/T orientation**.
These are explicit hypotheses, not measured timber properties, NDS DF-L No. 2
design values or characteristic-to-design conversions. The existing unmeasured
orthotropic elastic scenario is retained in both `R=u,T=v` and `R=v,T=-u`
bindings when those bindings are actually sampled. No duration factor is applied
to these hypotheses. Live and permanent actions remain separate same-state
records, even when solved as multiple right-hand sides of one geometry system.

The saved finite crack family consists of full-front straight flaws extending
from 5 to 10 mm from each grain end on the selected u/v plane, and the existing
axis-aligned transverse-bore family. A bore flaw initially spans its grain center
plus/minus the actual bore radius and 5 mm; each tip separately extends to 10 mm.
Actual bore void cells contribute no fictitious sound crack area. This is a named
finite family, not an exhaustive crack-front or washer-plug search.

For fixed physical nodal forces, strain energy is U = 0.5 f.T u. The traction-free
increment is `G_free = (U_final_free - U_initial_free) / added_sound_area`.
The separate conservative contact reference is
`G_upper = (U_final_free - U_intact) / added_sound_area`. Intact displacements are
admissible in the initial unilateral crack, and final contact constraints restrict
the final free displacement space. The upper reference includes release of the
initial flaw; it is not the traction-free increment or an observed fracture
failure. Its exact contact-energy oracle is preserved with the DCB coupon.

Every intact/initial/final configuration uses the same physical force cloud,
including source free couples and body loads. Existing minimum-norm wrench
mapping uses nearby nodes on the original side, excludes seam nodes and has a
fixed 15 mm footprint rule. Rounded physical node-position/force hashes must
match across crack configurations. This is an explicit local boundary hypothesis,
not recovered washer/contact pressure.

The separate [conditional load-cloud proof](rawlocal/splitting-capacity-completion/localized-large-domain-preflight01/load-cloud-project-proof01/result.json)
retains every applicable original mapping byte-for-byte. Only the original
four-node or wrench-rank geometry guard retries the same original-side,
nonseam weighted distributor with a 30 mm increment above the nearest-node
distance. Unsupported targets and other errors retain their STOP. The actual
load-only proof covers eleven knee, rail and tapered-leg configurations across
twelve states: 132 saved nodal-force fields, 34,318 unchanged calls and 2,628
fallback calls. Independent saved-array/source audit passes, with aggregate
force and couple residuals at most 2.44e-11 N and 1.61e-8 Nmm. The
[frozen installer](rawlocal/splitting-capacity-completion/localized-large-domain-preflight01/load-cloud-install.py)
and separate field wrapper preserve the original field gates. The 30 mm cloud
remains a conditional boundary hypothesis; these load-only checks supply no
response, energy, pressure, resistance or resource qualification. Earlier
pre-stiffness load-cloud STOPs remain preserved, with their fields pending.

The C3D20 solid law, translated-element stiffness reuse and six-scalar rigid gauge
remain unchanged. QR selects six independent scalar DOFs; rank, conditioning,
vanishing reaction, rigid-load projection, equilibrium and energy gates apply.
The current field grid has grain pitch at most four times the transverse pitch,
with all bore and crack breakpoints frozen. Each actual cylinder is sampled by
at least four radial partitions per diameter. Every bore requires positive void
cells, resolved independent clipped-cylinder volume and local volume error below
20%; retained whole-body voxel volume must differ from STEP by less than 5%.
The radial staircase is fixed separately from the 20/15 mm field-grid comparison;
there is no exact curved-face stress claim. Sampled stress is an integration-point
value, not a continuous maximum. Original 20% response-change guards remain.

## Supported method checks and preserved historical comparisons

The original DCB [coupon03](rawlocal/splitting-capacity-completion/coupon03/validation.json)
passed the source-supported energy method: fine G = 0.373188402465 N/mm against
analytic 0.377862622984 N/mm, a -1.237% error and 2.361% mesh change. The exact
contact bound passed three opening/closing states. This supports the recorded
method domain and does not transfer a pine material property to current timber.

The corrected [bore-coupon01](rawlocal/splitting-capacity-completion/bore-coupon01/bore-validation.json)
passed four records across both R/T bindings and two grids. It sampled the actual
finite bore with -4.507% void-volume error, recovered the exact affine axial field
to 7.27e-13 mm and the retained-mesh energy to 1.44e-14 relative error. Exact
curved-cylinder versus staircase energy differed by +0.338%. The independent
30-case clipped-cylinder volume oracle and the fresh
[gauge02](rawlocal/splitting-capacity-completion/gauge02/gauge-validation.json)
are preserved. Gauge energy error was at most 2.06e-14 relative, reaction
3.60e-12 N and transverse-field difference 1.42e-13 MPa.

The corrected historical
[center-post-cleat-v01](rawlocal/splitting-capacity-completion/center-post-cleat-v01/result.json)
completed **32 actual comparisons** at 20/15 mm, covering eight original reviewed104
live/permanent states, **one** `R=u,T=v` binding and **two** paths: the low grain-end
flaw and `center_post_cleat_left/facet006/low`. Its frozen aggregate prose says
both R/T; the explicit `sampled_RT_bindings`, `assessed_paths` and records govern
this narrower actual scope. All four physical bores passed the corrected local
geometry gates. Runtime was 1,484.425 s. All 38 source pins and six outputs
were independently authenticated.

| Finest historical comparison | Maximum index | Governing scope |
| --- | ---: | --- |
| Traction-free G / conditional Gc | 0.000021570696 | Original `dead-only_zero`, bore-low path |
| Separate contact upper / conditional Gc | 0.000054534314 | Same state/path |
| Intact sampled tension / conditional Ft90 | **1.361949104** | Original `dead-only_zero`, shared intact field |

The initiation exceedance is retained. Three unique intact states exceed the
original 20% stress-change guard: `a12-forward` (21.75%), `k12-right` (24.92%) and
`dead-only_zero` (32.31%). They appear as six path-row mesh flags. Energy and
upper-reference changes were at most 6.47% and 7.67%, respectively, with no
energy flags. This is `COMPARED_WITH_MESH_LIMITS`, not converged complete
splitting qualification or a physical failure claim. Result SHA256:
`4a1cd8c2a651a1dc0ae7db5bc6cc5e97ba13e26280b630b8911726e50602e5f5`;
receipt SHA256:
`6d22f2842274d60cd1ccd6ab92b65af19bb74c3a352126060e134dd38306d4ad`.

Earlier left-spine coarse results retain their initiation exceedances, original
force basis and explicit omitted-bore approximation. The global 5% volume guard
alone missed some physical bores. The 514-configuration historical census found
342 configurations with an omitted bore. Those results cannot inherit corrected
four-bore qualification. The original 5 mm augmented and sparse-gauge LU memory
stops remain preserved. The 7.5 mm LU completed but an avoidable `factor.L/U`
metadata materialization exceeded its cap; the corrected diagnostic uses documented
`stored_factor_nonzeros = factor.nnz`, whose semantics differ from materialized
structural L+U counts. No 5 mm project rerun was performed.

The [exact interface-condensation prototype](rawlocal/splitting-capacity-completion/interface-condensation-prototype01/known-answer01/result.json)
passed sixteen tiny unbored fixture/configuration records in 3.267 s. It reproduces
the original nodes/elements, full fields, interior-load energy correction and
equilibrium while reusing two side factors. Maximum relative K reassembly error
was 1.73e-16, energy error 6.54e-13 and displacement error 3.07e-12; Gauss stress
tensor difference was at most 3.34e-11 MPa and equilibrium residual 1.46e-10 N.
All twenty bound sources and output hashes were authenticated. Result SHA256:
`2ed829bb4b53363a894a78f323a27cb9504e87d17d61f89ca450aab9e5f6cd2d`;
receipt SHA256:
`7b73e8f8e10aa470488c1e0cb4b4eb9e498c0d6d9c52a2c4fc98d0ec17af9dd4`.
The largest tiny system had 984 split DOFs / 438 retained port DOFs. This proves
only the recorded exact condensation construction on those fixtures. Project
side connectivity, interior invertibility, dense interface size, conditioning,
full source force maps and runtime still require a bounded parent comparison.
No project speedup or completed fracture queue is inferred from the prototype.

The [localized-union oracle](rawlocal/splitting-capacity-completion/interface-condensation-localized-oracle01/known-answer01/result.json)
passed **38 tiny configurations** in 5.605 s, including the same sixteen source
fixtures, both R/T bindings on a shifted `u = 5 mm` plane, and crossing u/v
release planes sharing an exact element-coordinate grid. It retains actual
coordinates and every original scalar gauge, recovers the full internal fields,
and includes the interior-load energy constant. Exact incidence intersections
create the maximal release union; only coordinate copies released by a source
configuration and the original gauge-node union are retained. The original
sixteen node/element/load exports remain byte-identical. The deterministic
force lift places each original DOF force on one actual latent representative;
`P.T F_union = F_original` is checked exactly, including a three-copy toy.

All 29 sources and twenty outputs were authenticated. Maximum relative K
reassembly, energy and displacement errors were 1.44e-16, 2.12e-13 and
2.63e-12; every sampled Gauss tensor differed by at most 2.95e-11 MPa.
Equilibrium residual was at most 1.95e-10 N. The largest tiny union had 870
DOFs and the largest retained set had 237 DOFs. Result SHA256:
`266addd60483eb475c82e268739793534c22e3f8836fef219ccf057320f3b9d7`;
receipt SHA256:
`7c4800763eb4cf4c19540f3f1fdb3998cd820ee3249a54d9d151bd2b620af729`.
This supports the exact tested reduction. The subsequent
[historical cleat equivalence pilot](rawlocal/splitting-capacity-completion/interface-condensation-localized-project01/historical-cleat20-attempt01/result.json)
completed its three original configurations and eight historical force columns
in 158.7 seconds. Its 60,843 union DOFs / 414 ports required one 60,429-DOF
interior factor with 307,165,632 stored factor entries. Full recovered fields,
physical force clouds, original gauges, equilibrium and sampled stress witnesses
match the saved monolithic outputs; relative energy differences are below
8e-14. The [independent saved-field audit](rawlocal/splitting-capacity-completion/interface-condensation-localized-project01/independent-audit01/audit.json)
authenticates 273 bindings. This historical force basis supplies a method check;
it does not replace the current twelve force states. A complete null spectrum
was not assessed. The historical metadata aliases saying no native execution
and unbored fixtures are clarified in that audit: numerical solid solves did
run on the actual bored geometry; no external native solver or CAD executable
ran. The unexecuted whole-plane project readiness is preserved.

The fracture method references are [Jensen et al. 2016](https://onlinelibrary.wiley.com/doi/10.1155/2016/9402650)
and the [Romanowicz and Grygorczuk 2024 DCB appendix](https://link.springer.com/article/10.1007/s10704-024-00798-z).
The recorded formulas and known-answer coupon support the method, not a material
property transfer or complete joint qualification.

## Actual current finite comparisons

The first active cleat path, `center_post_cleat_left / end/2/low`, now has
**48 actual comparisons**: twelve accepted action03 states, both R/T bindings
and 20/15 mm grids. The [paired source-only comparison](rawlocal/splitting-capacity-completion/active-path-mesh-comparison02/result.json)
binds all four terminal packets, every full-field NPZ and the unchanged
publication arithmetic. Fine-grid initiation peaks are 7.1928146685 for
`R=u,T=v` and 6.7975749182 for `R=v,T=-u`. Five zero-floor-gap states exceed
the conditional initiation reference in each binding. Thirteen stress mesh
limits exceed the original 20% response-change guard; neither free-face release
nor the separate contact-energy upper measure has a mesh-limit flag. Signed
releases are positive in every current row. The source-only result SHA256 is
`0a3b340990d8c1a04309d42a233a81efa86b6290415e59d0fd21d2f522c96334`;
receipt SHA256 is
`1efcde45774ff139f5aa02936efcbfd6979f4137e8c3cca25901d43d0a20ca59`.
These are retained numerical exceedances and mesh limits, not physical failure
claims or a converged stress qualification.

The [complete finite cleat result](rawlocal/splitting-capacity-completion/active-solid01/center_post_cleat_left/result.json)
now records **384 unique comparisons** from twelve terminal native groups. The
[frozen seven-job continuation batch](rawlocal/splitting-capacity-completion/cleat-remaining-field-batch-prepared01/batch.json)
completed the remaining 312 rows. Each group retains its own source-counted
resource allowance, full action03 dictionaries, original physical force clouds,
scalar gauges, all recovered fields and checkpoint audits. The pure publisher
closes this body's declared finite inventory only; it produces no workstream
aggregate and keeps all other canonical rows required/pending.

| Complete current cleat comparison | Maximum index | Governing scope |
| --- | ---: | --- |
| Intact sampled tension / conditional Ft90 | **12.45866758** | `a12-forward_zero`, u plane, both end tips, 15 mm, `R=v,T=-u` |
| Traction-free G / conditional Gc | 0.02127655 | Same state/grid/binding, u-plane high-end path |
| Separate contact upper / conditional Gc | 0.04453979 | Same state/grid/binding/path |

There are 136 initiation-reference exceedance rows and no free-face or
contact-upper exceedance. Shared intact fields repeat across paths; those rows
are not independent physical failures. All 192 coarse/fine pairs and 576 metric
comparisons are assessed. Ninety-four stress comparisons exceed the original
20% mesh guard, representing 21 distinct state/plane/R/T intact comparisons;
maximum stress change is 39.676%. Neither energy measure has a mesh-limit flag.
Raw signed releases are positive in every current row. The result status is
`COMPARED_WITH_MESH_LIMITS`, not converged stress qualification.

Result SHA256:
`255c6666b8b5ac17d67b15a5a261c9cdb4dcfd2467bd5ff921a750c4bc3cd72d`;
[publishing receipt](rawlocal/splitting-capacity-completion/active-solid01/center_post_cleat_left/receipt.json) SHA256:
`f58204db356692a82b64691a1dd9c2ba6708a3ea62beb48822693a9869cd5979`.
The [independent complete-body reconciliation](rawlocal/splitting-capacity-completion/interface-condensation-localized-project01/cleat-complete-independent-reconciliation01/result.json)
binds all twelve native and saved-field audit packets, 729 unique closure inputs
and 816 actual saved fields. Its result/receipt SHA256 values are
`34d3fd172e76446c0f445e5a42eee76552f931d158a76df1562cc4cb57a0fe3c` /
`3342efa5026f3a88133b1ba713afb28ed8d90bab2f3e4aaa1eae1a657ff6a0da`.
The [body-only workload](rawlocal/splitting-capacity-completion/cleat-body-publication01/workload.json)
sets `method_validation_scope = proved_kernel_and_completed_body_only`,
retains all 37,056 canonical requirements and leaves 36,672 pending. Complete
joint acceptance and full splitting qualification remain false.

The second body, `center_post_cleat_right`, first recorded **96 actual comparisons**
on all eight paths and twelve states at 15 mm in `R=u,T=v`. Its
[combined-plane packet](rawlocal/splitting-capacity-completion/multi-plane-grid-adapter02/outputs/right-cleat15-u-attempt02/result.json)
uses one exact union of sixteen original configurations. Each plane retains its
own physical load cloud, intact energy and checkpoint; all twelve nodal-load
hashes differ between planes. Exact interior-force caching stays within the
actual union block. The unchanged K/P, full-load, scalar-gauge, equilibrium,
energy and recovered-field gates pass with chunked stiffness assembly.
The run took 602.291 seconds, with 302,213,586 stored global factor entries and
about 4.80 GiB peak RSS. This is an actual domain validation, not a large-host
resource qualification. There are 32 initiation-reference exceedance rows;
maximum initiation/free-face/contact-upper indices are 7.83733839, 0.01176163
and 0.02626707. All signed releases are positive. The other R/T binding,
coarse grid and 288 right-body rows were pending at that checkpoint.

Result/receipt SHA256 values are
`435c95cae876bbdf805cc33f228456f69ec05b1ff0b0d12ce469b3891237b4e8` /
`f74eab9de4beb1782b543c7de1365746897b083365c4c615e5473c9a4d4a88d3`.

The subsequent [coarse right-cleat packet](rawlocal/splitting-capacity-completion/multi-plane-grid-adapter02/outputs/queue-d4276adff37679ba1661b276/result.json)
adds **72 actual comparisons** on six axis-2 paths at 20 mm in the same R/T
binding. Its eleven original configurations pass all published field checks;
the paired source/output/checkpoint/NPZ joins and row arithmetic authenticate.
Result/receipt SHA256 values are
`a48ee386d559d6e95bb16c1581de71fcd20e81719fe0b1abb43647775ad72a74` /
`3a4d970f545c1f9ee5a9fd8c59a754be47c05fc19e84936dd9e0e7eb45994600`.
The run took 329.702 seconds. Eighteen initiation rows exceed the reference;
maximum initiation/free-face/contact-upper indices are 4.61761943, 0.00231810
and 0.00525467. Signed releases are positive. Pure same-path coarse/fine
arithmetic retains 36 stress row changes over 20%, reaching 34.819%; free-face
and upper changes reach 12.235% and 10.937%, both within the guard. The new
packet's separate full saved-stress audit remains pending. The right body now
has **168 of 384 rows**, with **216 feasible comparisons pending**; its body
publication and remaining material/grid pairs remain open.
The [independent saved-field audit](rawlocal/splitting-capacity-completion/interface-condensation-localized-project01/right-cleat15-u-cross-plane-independent-audit01/audit.json)
authenticates 527 native sources, 45 outputs and 192 saved fields; audit/receipt
SHA256 values are
`04549fab638f7747890c4e5f42d725775878bb9a1cff4cf939be9085d3dac84e` /
`3a26151b782a8d50126f24a13e0f8e35259c2faa63a06f3e683ac1672a016675`.
The original single-plane and combined-plane outputs remain at their frozen
paths. A later common-ancestor publication must bind both without moving fields.

The earlier fine-grid attempt completed LU under its 9 GiB address-space cap
but stopped at a secondary 400-million stored-entry bound. Its frozen STOP is
preserved. A parent-owned retry measured 456,971,553 entries and completed under
10 GiB with the original field gates. The opposite R/T fine run measured
329,618,502 entries. Those attempt bounds are computational dispositions;
they supply no timber resistance or permanent method exclusion.

The [selected-plane partition coupon](rawlocal/splitting-capacity-completion/selected-plane-coupon01/known-answer01/result.json)
passes twelve known-answer fields on the exact shifted bore/plane witness.
It preserves aligned grids byte-for-byte, represents the source-selected plane
exactly, retains real seam duplicates and positive added area, and records
signed zero-release roundoff. The [corrected all-body grid audit](rawlocal/splitting-capacity-completion/corrected-all-body-grid-audit01/result.json)
then recomputes all 189 corrected grids on 42 bodies. Every actual bore's
positive void, diameter/4 radial pitch and independent local-volume guards,
and every global STEP-volume guard, passes. It records 1,484 positive-area
path/grid pairs and twelve exact zero-area pairs. This is a source geometry
and sampling result; each current solid field still needs its own audits.

The twelve aligned zero-area pairs have no source timber in either released
band, as proved by the [exact profile certificate](rawlocal/splitting-capacity-completion/localized-large-domain-preflight01/aligned-zero-profile-audit02.json).
They are path-specific applicability limits, not zero force demand or a
whole-body splitting pass. The two actual 1:12 legs remain in the full inventory.
Their source-bound three-zone profile adapter passed 48 small configuration
checks, 288 affine fields and 48 balanced-source fields. The actual 24-grid
[leg census](../rawlocal/member-opening-general-completion/ownership-draft01/taper-splitting-census-attempt01/result.json)
and independent saved-mask audit pass whole STEP volume, finite bore and radial
pitch gates. Three axis-1 end/grid pairs per leg exceed the original 20% added-area
guard: coarse low (+31.08%), coarse high (+94.49%) and fine high (+36.14%).
The separate [refined census](../rawlocal/member-opening-general-completion/ownership-draft01/taper-splitting-refined-census-attempt01/result.json)
and saved-mask audit now pass all forty positive path/grid area guards. They
preserve twenty prior grid/mask exports byte-for-byte and add transverse stations
on only four axis-1 grids, using actual cut intersections. Coarse-low and
coarse/fine-high area errors reduce to about 2e-11 and 2e-9; the unchanged
fine-low error is -8.245%. The same-fixture refined coupon also passes. Those
144 identities now await source counts and fields; the failed sampling packet
is preserved and no field pass transfers. Bore-seeded path areas agree with the exact
source bands to about 5e-12 relative error. Current leg fields remain pending. Four original
leg end fronts have no sound source timber, accounting for 192 canonical
identities; the other twenty leg paths have positive exact added area. Neither
old dimension limits nor old profile stops are inherited as permanent exclusions.

The pure [exact absent-front table](rawlocal/splitting-capacity-completion/exact-absent-front-dispositions02/dispositions.json)
expands only the six clipped-host paths and four leg paths certified to contain
no source sound area in either named crack band. It binds all **480 exact
identities** to their current geometry, profile certificate, original STEP and
accepted action03 dictionary/state. Table/receipt SHA256 values are
`83ff0637500c7ac1c8100d186ee52608f1a338b0d3108c2473878ebb3ba8adce` /
`0754705ee094699c0d123d4ddc77da35b9accd52325b242fbbab759c228e0309`.
The supplemental source closure directly binds all eight referenced STEP files,
preserving the first table and receipt unchanged; independent source and identity
audits pass. No numerical fields were run for this publication correction.
This table is **unadopted pending parent review**. It assigns no force, energy,
reference index or strength pass. All sampling, load-map, resource, timeout and
unperformed comparison obligations remain pending; no workload partition changed.

The [allocation-only known-answer packet](rawlocal/splitting-capacity-completion/localized-large-domain-preflight01/allocation-known-answer01/result.json)
passes 38 original configurations and 114 comparisons across element chunks
1, 3 and 1,024. The translated C3D20 element law, axes, connectivity, loads and
gauges are unchanged; only COO-buffer lifetime and CSR accumulation change.
Independent saved-field maximum relative displacement/energy errors are
1.119e-12/2.702e-13, and Gauss tensor differences are at most 1.521e-11 MPa.
The right-cleat run supplies the first actual chunked-assembly domain validation;
other project CSR storage, sparse fill and memory are not inferred from it. The
installer's 147,456,000-byte chunk subtotal is a configured 1,024-element buffer
envelope; the queue uses the actual `min(1,024, element_count)` buffer subtotal.
Neither is a process-memory upper bound. The [parent serial allocation queue](rawlocal/splitting-capacity-completion/serial-allocation-prepared01/queue.json)
retains all 1,068 single-plane groups / 37,056 obligations, with no inherited
whole-mesh COO prerequisite and no permanent exclusions. Source counts and
machine headroom precede each field attempt; a load-map, cap or timeout STOP
stays pending. Parent owns bounded project validation and execution.

## Exact remaining finite workload

The [retained-grid census](rawlocal/splitting-capacity-completion/coupled-resource01/resource-census.json)
uses exact corner/edge-midpoint incidences for the same center-classified retained
cell mask, without matrix assembly. Six independent node-set oracle cases and
observed 60,651/64,329 DOF cleat counts match. The
[crack-node census](rawlocal/splitting-capacity-completion/coupled-cracked-resource01/cracked-resource.json)
adds exact duplicated interface nodes. Twelve independent explicit node-set
oracles pass, and all 162 formerly ambiguous finite configurations fit their
180,000 DOF cap. The two outer posts fit at 15 mm with at most 172,101 DOFs.
The [geometry-domain census](rawlocal/splitting-capacity-completion/coupled-geometry-domain01/domain-census.json)
records local bore/profile gates independently. Four already dimension-limited
host/grid rows miss the strict radial-pitch guard by less than 1e-6 mm due to
existing grid coordinate merging; this is a numerical-coordinate issue, not
missing material or a proved physical flaw. No feasible queue body is excluded
on that basis.

The [active workload](rawlocal/splitting-capacity-completion/project-draft10/active-finite-workload.json)
records each body and exact named paths, with the preserved direct-method
resource statuses. Thirty bodies fit that direct method and their uncomputed
current comparisons remain pending. Their complete
current finite family would produce **16,512 path/state/grid/binding rows** and
require **2,856 factorizations** with the existing direct method after interval
reuse. Twelve hosts exceed the preserved direct-method fine-grid dimension gate.
Their localized reductions require actual method-specific resource checks;
that old gate is not a new exclusion. The two legs need a source-bound tapered
solid profile adapter, although their nominal transverse sections are supported. A larger cap, coarser field, local window
or new crack family cannot silently replace those domains.

The preserved workload also declares the complete inventory of **44 timbers,
772 named paths and 37,056 current state/path/grid/R/T obligations**. The
[source-only inventory audit](rawlocal/splitting-capacity-completion/active-obligation-inventory-audit01/audit.json)
confirms every canonical duty/geometry body and every literal path descriptor;
its SHA256 is `c3e9ae0b50083cb4b902f5a41d6ab52f77049639526f1caa392418c22b2f888f`.
A new method ledger must partition all these obligations into actual required
comparisons and exact source-bound method exclusions. The old direct-method
statuses are not inherited by condensation. The existing paired direct queue
accounts for 16,512 rows; its other 20,544 obligations must be reassessed.

The [deterministic queue preparation](rawlocal/splitting-capacity-completion/active-finite-queue-plan01/queue.json)
binds the existing 30-body feasible family to all twelve exact current action
records and every path interval. It has 276 plane/R/T jobs and 1,104 potential
half reductions. Equal literal float64 grid signatures identify 228 potential
localized union groups. These counts supply no operator reuse, invertibility or
runtime proof. Every changed force column requires its own current action and
physical nodal-load binding; historical stress, energy and acceptance are not
reused. The final aggregate can close only with zero pending feasible rows,
authenticated intact/initial/final field checkpoints, the complete obligation
partition and retained reference exceedances and mesh limitations.

The frozen isolated producer10, SHA256
`41b41d7475b385a15d4f4204ce230b9fbb4fecb2fa27209d8d3adea65f3862fe`,
adds exact per-configuration and per-path checkpoints, authenticated recovery
and accurate scope prose. All fourteen solid/coupon/gauge helper ASTs are exactly
the corrected frozen1682 producer; source/geometry-only changes do not reuse
energies under different forces. Inert compilation and scoped Ruff pass.
All raw inputs, commands, source snapshots, failed runs and output receipts
remain active and recoverable; nothing was pruned. Parent owns serialized solids,
readiness, final integration and validation. Existing eight NDS component
exceedances and proposal-specific history are preserved. Complete joint
acceptance and fabrication/climbing release remain false.
