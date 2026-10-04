# Finished opening sections: source-bound numerical comparisons

This assessment preserves the reviewed 104 structural axes,
44 timber blanks and 66 Hillman axes. The six-bore knee-spine proposal remains
a separate, unadopted 108-axis geometry. Numerical reference exceedances are
assessment outcomes; none establishes inspected timber failure, complete joint
resistance, candidate selection or a physical release.

The completed original/proposal point-action assessment covers 22,288 finite
longitudinal and elastic transverse comparisons: the frozen 20,624 opening
comparisons and 1,664 bore-free rear-recess comparisons. It records 272 additive
longitudinal reference exceedances and 474 sampled Fv reference exceedances.
It also resolves 320 one-sided endpoints analytically. A separate exact
disk-integral calculation completes the 656 actual curved cleat sections for
longitudinal stress. These are numerical assessments within the applicability
limits below; they do not establish complete structural acceptance.

The latest refined compatible-frame packet completes **49,344 finite
longitudinal and elastic transverse comparisons**, with 200 additive normal
and 420 sampled Fv reference exceedances. It retains 120 zero and 120
divergent analytical endpoint outcomes, the two unavailable floor cases,
and all fourteen requested dispositions. The 7,008 actual curved-section
longitudinal comparisons have no reference exceedance. Its force source is
explicitly the refined action03 packet; earlier original/proposal and frame06
results retain their original scope.

The completed longitudinal replay uses the original signed forces and free
couples, exact retained rectangular-region integrals and before/after cuts.
It restores all six cut resultants from saved point actions and explicitly
transports moments to the section datum, including four header recipes whose
datums differ from their saved cut origins. It retains product inertia and a
single longitudinal strain plane over each retained region union. Its additive
axial-plus-bending reference sum is a reported comparison, not a complete
wood-joint interaction criterion.

| Force and geometry scope | Target traces | Finite longitudinal comparisons | Additive reference exceedances | Zero / divergent one-sided limits |
| --- | ---: | ---: | ---: | ---: |
| Original reviewed104 live frame, six source cases | 5,784 | 5,664 | 96 | 60 / 60 |
| Separate proposal-gravity replay on global104, six source cases | 5,784 | 5,664 | 96 | 60 / 60 |
| Proposal permanent loads on unchanged reviewed members | 1,928 | 1,888 | 40 | 20 / 20 |
| Separate proposal permanent outer-cleat / six-bore point-model duties | 624 | 624 | 0 | 0 / 0 |
| Original reviewed104 permanent loads, both gap states, C_D=0.9 | 6,824 | 6,784 | 40 | 20 / 20 |
| Total | 20,944 | 20,624 | 272 | 160 / 160 |

The 624 special proposal comparisons comprise 336 outer-cleat traces and 288
six-bore spine traces. Their maximum additive longitudinal reference is
0.008879142. These comparisons use the authenticated saved point-action
accounting. They do not establish equivalence to actual outer-cleat pressure,
distributed gravity or internal bridge sharing. Original104 permanent results
include 656 explicitly labeled artificial retained-subset traces at the six
longitudinally bored inner/header cleats. A stress reference on such a subset
does not bound stress in the actual curved finished section.

The actual curved-section longitudinal calculation is now available as a
parallel result. It authenticates the six finished cleat geometries through
`header-cleat-net-sections.py`, retains the actual transverse shaft slots,
and subtracts the two disjoint internal longitudinal disks using exact area,
first moments and full second-moment matrices. All 656 original104 permanent
cuts complete at C_D=0.9, with no additive, total-tension, total-compression or
bending reference exceedance. The maximum additive index is 0.002248082397,
at `center_principal_cleat_left`, `dead-only_zero`, station 90.010222066 mm,
after the cut. Its preserved artificial-subset index is 0.002462975298.
The signed axial-force/bending recovery error is at most 4.55e-13 N or N·mm.
Internal disjoint holes leave the extreme outer corners intact; the common
linear strain-plane extrema are evaluated at those corners. This calculation
does not provide bore stress concentrations or an actual curved-domain shear
field. All 656 earlier subset records remain separately identified.

A 20×12 mm rectangle with two unequal off-center disks validates the disk
integrals with independent rectangle Gauss and polar quadrature: integral
error 9.10e-13 in the corresponding units and signed wrench error 1.14e-13.
The independent audit also checks all 656 actual geometries, with maximum
integral error 1.53e-15 relative to the absolute quadrature summands and signed
wrench error 9.10e-13. It verifies all 240 source pins and seven outputs.
`circular-normal-attempt01` has producer SHA
`768e18891308d1358eaddd27763b1b9158745dca2f178f753b4c8302d904f0e4`,
summary `113cd717b7d29262eec6449f58d0a5541956090015b197a768e62244d111b096`
and receipt `23deca11e028aa1d0ec772e523b2b64d74dc48a90d97b7bf6c590c04a95244fe`.
Its command, which performs pure arithmetic without a CAD, FE or frame solve,
is:

```sh
.venv/bin/python -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/member-opening-general-completion/ownership-draft01/circular-normal-replay.py docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/member-opening-general-completion/circular-normal-attempt01
```

The finite exceedances occur in near-terminal retained sections. The largest
original104 permanent additive index is 129135.138231. A nonzero saved point
wrench on a section whose area vanishes gives a divergent one-sided beam
model limit; this is retained as a numerical outcome. A source wrench within
the recorded equilibrium tolerance gives the finite zero limit. Neither
outcome substitutes for a three-dimensional load introduction model at the
actual end or notch. No epsilon witness is promoted to a physical capacity.

The longitudinal result is frozen in
`rawlocal/member-opening-general-completion/draft-arithmetic-attempt03/`:
producer SHA-256 `5a49c7597c53dd1033ea4f0e4acfc9a20ebba0b3375c558879b4390de4734f07`,
summary `f0a949fd84ea900f6e852e2fb02c2233b9cf470f1e0df889092f796784061ea5`,
receipt `7038ba34731d6fa2a65235e8955b67dd8822fda82866f655ad98199b8005fc50`.
Its 232 pinned inputs include the original104 permanent source
`rawlocal/dead-load-check/parent-attempt06/`: comparison
`20802196776a89ea8b041832b413ef8d8613493b1bf36f89a3810807c5166e75`,
response `9ff6f4ca177029b2c03acfb5425be9f943ad34679c8ab59013eb36764dd92f14`,
member actions `cfe750ab9082ed854a5d641b781cd420fa79bbdaba3fa5978570ae7f20f6fa09`.
The source closure and receipts bind the exact producer snapshots, helpers,
geometry and action arrays; no global frame or CAD replay was required.

The transverse method solves conforming Q1 whole-domain Neumann potentials
for both shears and free Saint-Venant torsion. Its conditional section model
uses equal shear moduli, zero Poisson coupling and local prismatic,
unrestrained-warping behavior. Disconnected regions use a complementary-energy
common generalized shear/twist allocation; that does not prove actual
longitudinal bypass or end compatibility. References describing these methods
are [MIT's torsion module](https://web.mit.edu/16.20/homepage/6_Torsion/Torsion_files/module_6_no_solutions.pdf),
the [sectionproperties theory](https://sectionproperties.readthedocs.io/en/stable/user_guide/theory.html)
and [SciPy sparse LU documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.splu.html).

The first full transverse attempt,
`rawlocal/member-opening-general-completion/elastic-draft-attempt01/`, stopped
at the unchanged 1e-6 weak-equilibrium residual gate. It is preserved as a
failed run. Separately, a blind-bore mouth differs from its outer boundary by
1.214886e-10 mm, leaving an unnecessary extremely thin integration row.
The corrective producer coalesces only outer-boundary coordinates within the
recorded 1e-6 mm geometry tolerance, retains every delta and leaves the exact
longitudinal arithmetic unsnapped. A census of 836 distinct positive domains
finds 55 adjusted domains, no change in exact positive-edge connectivity,
maximum coordinate change 1.833712e-9 mm and maximum area change
3.088644e-9 mm² (6.009278e-13 relative). Coalesced shear fields are conditional
section idealizations, not exact unsnapped CAD stress fields.

The separate light conditioning census shows the known rectangular sliver
mesh reducing from 902 to 861 nodes, with one constant nullspace in both
meshes. Its assembled diagonal scale ratio falls from approximately 5e9 to 4.
For the actual blind mouth it falls from 1.163e10 to 4.012; nodes change
2628 to 2598. Those ratios are indicators, not matrix condition numbers.
The accepted corrective known-answer pair has zero torsion-constant difference
from the unsplit rectangle, a 0.08333% unit-shear peak error,
9.82e-13 weak residual and 1.13e-14 unit-wrench error. The existing rectangle
torsion error is 0.0961%; its sampled torsion peak error is 2.344%.

`method-coordinate-regularization01`, `coordinate-preparation01` and
`sliver-conditioning01` retain receipts respectively
`dc4ad03bb4123ecfefd45822d5686cf56d08f973bc07180073579d8f01acdf98`,
`e629df4a2cb72b81f59f63b497fb1cbc6141ccc640e46b87275ad065fdabeb7e` and
`4cb298e1ab4d2d0d3ea49e8f8f0e8f5c0acd2a57364510beb29e926f64b31aa6`.

The corrective six-domain pilot completes 120 source-mapped traces in
8.066 seconds, with maximum integrated shear/torque error 3.64e-11,
weak residual 6.61e-10 and unit-wrench error 6.81e-14. It includes a real
blind cut, disconnected slot, near-terminal section, shifted header datum,
separate six-bore proposal and the thin blind mouth. Four of 28 blind-toprail
traces exceed the Fv reference, maximum 2.725078; all 28 near-terminal traces
exceed, maximum 8141.122499. The thin-mouth maximum is 0.183219. Several
blind/slotted sampled peaks change 18–20% between 3 and 1.5 mm meshes while
RMS changes stay below 0.32%. They are numerical samples without a rigorous
peak bound. The pilot's summary component heuristic uses a 1e-8 threshold and
mislabels the tiny original mouth connector as disconnected; its accepted
field and the exact geometry census both record one connected component.

The pilot receipt is
`5263ee0e0e229c1d6763f4c5214b2928553959b995d03fbe303d232d0fcccee5`.
It authenticates pilot SHA
`adc2cfab2166543cd6cfc77632d90e6bcf5ccac8a1573e625a8354e54c239782`
and corrective producer SHA
`fdd1ec2ee0a2d5c8eb8b74b5484c5a1d2241df2e9fbba15881b568cdad47f600`.
The corrective producer resolves `HERE` from its ignored owned draft path to
the original `upper-corner-screw-layout` directory and binds that actual
executed source path. Accepted unit fields are stored under ignored
`rawlocal/member-opening-general-completion/field-cache-v1/`, keyed by exact
original regions, mesh spacing, method bytes and pinned NumPy 2.5.2 / SciPy
1.18.1 runtime. Every reuse checks array and metadata hashes, signed unit
shear/torque recovery and the unchanged weak-residual gate. Accepted state rows
are streamed into a valid compressed checkpoint and may resume only with the
same producer, inputs, forces, references and meshes.

The outer-only corrective full run,
`elastic-checkpoint-attempt01`, also stops at its first field: header station
217.12990000000005 mm is a recorded tangent of the radius-2.0701 mm screw bore
centered at 219.20000000000005 mm. Floating arithmetic leaves a
2.457562e-7 mm chord. Its connected Q1 matrix has one constant nullspace,
rank 783 at 784 nodes, and diagonal scale ratio 1.2002e7. Five unchanged
residual corrections leave a 1.73971e-5 torsion residual, above the 1e-6 gate;
no rows or fields were accepted. The STOP hash is
`a28995ca2b96f0ba0ecbcb9db64bf321fd24ae1aaa63718c9f780de0a61b8e12`.

The subsequent certified tangent idealization applies only to shear geometry.
Every collapsed tiny internal interval is authenticated against a transverse
cylinder's source radius, center, axis and grain station. The full light census
finds 11 such domains at 51 recipe aliases. Maximum coordinate change is
4.064495e-7 mm; maximum area change is 6.194290e-5 mm² (1.163778e-8 relative).
Seven idealized domains change connectivity: 60 original104 permanent traces,
including 20 retained-subset traces. All remain explicit physical applicability
limits, with exact original longitudinal geometry preserved. The census
receipt is `937ea469f13aaf9a400bc2d21677e971c7236ab7beec9fe7181a33ec77a3db1f`.
Geometry field metadata may name a representative source alias; the census
retains the separate certificate for every member/station alias.

The bounded tangent pilot preserves the unsnapped numerical STOP and compares
the idealized stopped shape with the exact 139.7×38.1 mm rectangle. At 1.5 mm
spacing, its torsion-constant error is 0.02665%, unit-shear peak errors are
0.0042% / 0.1972%, and sampled torsion peak error is 1.6567%. Its accepted weak
residual is 6.04e-11 and unit-wrench error 3.64e-14; the recorded state Fv index
is 0.145383. Receipt
`5bd760f8b8d3b472333184c25c4cda3b0a8852298a657f69fedc5c8a4150d606`
binds executed pilot SHA
`ed9f044447030e39bd4f5a70999ba24bc65bf228eda7879ff1ab60233520311e`,
producer `bd860ad0bc6708f3f2e56c22fab17a06b6ce94c6e25f85c18909c25cbc97bd07`
and tangent helper `fc8cc691fd71136f381031c4971b136ec512ad86cfa24039b03f6fab4d12275b`.
The FE solver, original normal arithmetic, endpoint method and outer
coalescing remain unchanged from the preceding frozen corrective method;
unchanged geometry therefore reuses its accepted field keys.

The first tangent full run preserves 100 accepted state rows and ten accepted
unit fields before another unchanged-gate STOP. Its first filter tested the
full chord width against 1e-6 mm, excluding header station 1417.1299000000001 mm
whose two edge displacements are each 6.063876e-7 mm. The v2 filter checks each
individual displacement against the existing tolerance. It does not enlarge
that tolerance or relax the weak-residual gate. The stopped source hash is
`abf7194ff71b16c7b023439316fcd9dda64c12680d2a2f71ecb271a5753cc197`.

The v2 census joins every one of the 20,944 actual force-basis/state/station
traces to its source geometry. It identifies 15 tangent domains at 83 recipe
aliases, with maximum edge displacement 7.152557e-7 mm and maximum area change
0.00012717247 mm². There are 1,100 tangent-idealized state traces. Nine domains
change idealized connectivity: 68 original104 permanent traces and eight
separate proposal outer-cleat traces. Corrected outer-cleat certificates use
their independently authenticated saved geometry rather than original surface
features. Every such topology change remains a physical applicability limit.
Receipt `b1fd143216da22965081e21c01361717b8b9c3dc0aac097060602561c9ad56ec`
binds the full executable census. The bounded v2 known-answer receipt
`d03fa8b0796dfc9c3263b7c50562151d2482a975245eea270e90c4d7a50270ee`
preserves the unsnapped 1.491256e-6 torsion residual STOP and confirms the same
accepted rectangle errors as the preceding tangent pilot.

The full v2 transverse comparison completes under parent serialization in
847.425 seconds. Its independent audit verifies all 239 input pins, all
outputs and all 3,970 stored unit fields, including recursive component fields.
Every one of the 20,944 signed-wrench, datum, longitudinal and endpoint records
is bitwise identical to `draft-arithmetic-attempt03`. It resumes only the
authenticated 100 previous rows after checking their exact forces, references
and coarse/fine geometry/method field keys. Producer SHA is
`4837537ad42ae9e92abf3146cdd5b5d6be11fd0a742a300a71047c0db095921e`;
helper SHA is `beb12feab676a9c8eee601efc42597e6eed008b0e40de0482b334cb544c28b13`.
The output summary is
`2939ef70c81ebf4883cd7be60f0f1bb0aa3513bd03b7f16aae0ecbf66a16de0b`,
receipt `91c7e54a0d9a35137e87920c9e7bb191fc099d64e673022f99e95b6d9f79db3d`.
The independent `elastic-tangent-audit01` report is
`f194605f6d3f3a0af1841e7192e739c2c703dc747425112ec133daead45f330e`,
receipt `ce9c4aeaf7b0bd39eea4b35360cec2b2a7a95c4f11011c64e43733b4805f4a67`.

| Frozen force and geometry scope | Finite shear comparisons | Sampled Fv exceedances | Maximum sampled Fv index |
| --- | ---: | ---: | ---: |
| Original reviewed104 live frame | 5,664 | 197 | 29999.834957 |
| Separate proposal-gravity replay on global104 | 5,664 | 197 | 29996.531101 |
| Proposal permanent loads on unchanged reviewed members | 1,888 | 40 | 33329.479001 |
| Separate proposal permanent outer-cleat / six-bore point model | 624 | 0 | 0.02627056748 |
| Original reviewed104 permanent loads | 6,784 | 40 | 33333.149952 |
| Total | 20,624 | 474 | 33333.149952 |

Of these finite results, 15,512 use a connected whole-domain field and 5,112
use the conditional disconnected-ligament allocation. The maximum accepted
weak residual is 4.56e-8 against the unchanged 1e-6 gate; the maximum signed
unit-resultant error is 2.17e-13. All 320 endpoints retain their analytical
outcomes. No unresolved endpoint or coupled-ligament input count remains.
The actual geometry and force scopes, including the 624 separate proposal
point-model duties and 656 artificial subset shear comparisons, remain
explicit. Curved-domain shear, physical end load introduction and actual
longitudinal ligament compatibility are not qualified by this completion.

The 3 / 1.5 mm sampled peak difference exceeds 5% in 7,260 state cuts; its
maximum is 30.6990%. Maximum RMS difference is 0.871515%. These changes are
reported mesh sensitivity, without a rigorous peak bound or a convergence
pass. The large near-terminal indices retain the vanishing-section source
point-model limitation described above. The numerical gate verifies the
discrete potential equations and signed wrench recovery; it does not qualify
local stress maxima or timber resistance.
Its concrete command is:

```sh
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/member-opening-general-completion/ownership-draft01/producer-tangent-v2.py --elastic --spacing 3 --refinement 2 --resume docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/member-opening-general-completion/elastic-tangent-attempt01 --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/member-opening-general-completion/elastic-tangent-attempt02
```

The initial compatible-frame longitudinal replay uses the separately authenticated
action export `rawlocal/joint-frame-action-reconciliation/attempt02/`, receipt
`d79abda0dd3df21c84b65b83f95d1f2e0d4c00e5139fd356533b5b0ec0d60f18`.
It consumes only 12 accepted states: all six nominal live cases, four zero-gap
live cases and both permanent cases. The complete 14-key inventory retains
`a12-left_zero` and `k12-right_zero` as unavailable force fields with their
source disposition pointers; no stopped forces are synthesized. Each valid
state has 3,412 original104 opening traces, comprising 3,392 finite sections
and 20 one-sided endpoints.

This normal-only replay completes 40,704 finite longitudinal comparisons,
with 200 additive reference exceedances, plus 120 zero and 120 divergent
one-sided outcomes. It includes 3,936 explicitly labeled retained-subset
traces. Its maximum is 129135.138231 at the permanent near-terminal right
principal section. All six resultants are independently restored from the
changed point-action array at each cut, with the same explicit section-datum
transport. It validates 480 unavailable canonical action placeholders without
interpreting them as zero demand. The exporter also supplies arbitrary action
event cuts; their 3,072 supplemental station/state occurrences are inventoried
separately, without a new continuous-section strength claim.

`coupled-normal-attempt01` receipt
`51d86ec79d496513d51229d2bbe12156273dd87ce857d28f67f21cb4a3c2bffa`
and summary `113832ce34aee642f7f2ce6ce903c0cf50379732e67f6127e1bcd94c50f3d588`
bind executed consumer SHA
`60cac403967aa18ede7ab810c1ceed21e29cc1667af775f843d95938e1059cd3`
and 314 unchanged input pins. Runtime was 38.846 seconds. This historical normal-only result contains no
coupled transverse comparison. The consumer's
`--cached-fields-only` option checks every required geometry/method field
before evaluation and cannot launch a missing-field solve. Geometry-only
fields may reuse, while actual forces, durations, validity and failed-state
identities remain separately authenticated. No compatibility or strength
acceptance transfers from the preceding point-action bases. This initial
coupled result remains frozen within its frame06 scope; any later refined
frame actions require a separately authenticated replay.


The predecessor's 104 bore-free rear-recess station recipes are retained,
with their frozen `attempt07` producer/snapshot
`c4bf4023c67f861daa287503569c97a3d9c65e7c36ad5928566bfb787ddd1463` and receipt
`87257aa2f96ef97a2ae766284103ec6d5d99c0dcafa7f74190eed285ae21ff9b`.
The parent executes exactly 208 additional fields on 3 / 1.5 mm meshes in
`rear-recess-fields-attempt01`, completing 1,248 original live and 416 original
permanent comparisons. Every original normal and wrench record remains
bitwise unchanged. None exceeds the normal or sampled shear reference;
maximum sampled shear indices are 0.194444696 live and 0.009679148 permanent,
both at `lumber_leg_left`, station 98.773319216 mm, before. Maximum peak / RMS
mesh differences are 1.3090% / 0.106685%; these remain numerical differences,
not rigorous peak bounds. Weak residual is at most 1.34e-9 and independent
signed unit-wrench error at most 1.75e-13. This distinct extension takes
77.690 seconds, with receipt
`3a9ac08e49ef8d962f4c4a7f52e14266791b33a878721bc0e225deb666725382`,
summary `eb7044e935fc8272fa9c60f6011394ee549a3b18c35b0744a4b80fa171d8796e`
and audit receipt
`8b5e380103e83231cba82ff2e6889afd6a8b2b919a62dd455e1300d7b930dbd0`.
Together with the preceding frozen residual set, these provide 22,288 finite
point-action comparisons and 320 analytical endpoints, with 272 normal and
474 sampled shear exceedances. Separate proposal-gravity recess reference
results remain reused from `profile-method-completion/attempt02` within its
own source and method scope.

The existing original-live physical outer-cleat pressure result also remains
preserved: `corner-group-finish/attempt03/checks.json`, SHA
`2ae3a84f273823dc6ca751e6fdddab8e0d70425ee7b34e1e38ebc79d5b672f23`,
provides four cleats / 24 body-case states / 101,276 finite directional limits
under half-cosine bore pressure and full signed wrenches. Its regional shear
reference maximum is 0.334875020 and tension/Ft is 0.078053178. This original
live pressure result does not supply matching permanent pressure or qualify
the separately retained 624 proposal point-model duties. Both the original
full-depth 1:12 rear-recess reference results and physical live-pressure result
remain reproducible; no NDS end-notch-depth acceptance route is inferred.

The refined action03 export also contains 3,072 supplemental station/state
occurrences. Its exact finite inventory is 64 new planes on each reviewed
knee inner block and each original four-bore spine: 256 distinct planes across
12 accepted states. Before/after cuts require 6,144 comparisons. All are
positive finite sections. The 128 spine-plane aliases have exact retained
rectangular unions; the 128 inner-block aliases have actual longitudinal
slots/disks plus separately labeled artificial retained-subset shear domains.
These are source action discontinuities, without a continuous-station or
unbounded global peak search.

The parent executes `action-event-field-replay.py`, source SHA
`c5c08653bd46d45cfb01386a3593a15075f9b388f917f45262a39f4cdbbc0743`,
in 119.922 seconds. It regenerates all source geometry and authenticates the
census `351fc33cdd4d91c650ad38c5d205c5168f280a78f78d1acfd7e2ce1e29c20085`.
Of 230 distinct target field keys, six reuse accepted fields and 224 were
uncached. Its complete recursive field inventory has 686 entries. All 335
sources, seven outputs and stored field hashes pass the independent audit;
maximum weak residual / signed unit-wrench error are 6.30e-10 / 6.84e-13.
Receipt `1649a2b58eb307a0fb8f86a0d35d14145586ddd9ac9a428d0cdb32157e76ef46`,
summary `03fd958c0e6b9119869e151d44506d724ec03d0103982ba81a217479d98ab20c`
and audit receipt `bbe44856073caece33f7305ea470eb3b8ebef56e4623188b1f73fae212ff1ced`
bind this finite event-field completion. Actual curved-domain shear remains
outside the rectangular potential method.

The final pure append consumer preserves all 40,944 action03 opening rows
bitwise, then adds 2,496 compatible rear-recess cuts and 6,144 event cuts.
It reads accepted fields through a strict geometry/method/runtime/hash loader
with no solve fallback. Exactly 2,066 required unit fields are reused. Each
accepted state has 4,132 cuts: 4,112 finite comparisons and 20 analytical
endpoints. Its all-fourteen disposition inventory preserves
`a12-left_zero` and `k12-right_zero` as unavailable forces with their source
pointers. All ten unchanged source states retain exact signed-force and
normal identity to the earlier frame06 result; only `a1-rear_gap` and
`k12-rear_zero` carry the separately refined forces.

| Final action03 compatible scope | Cuts | Normal exceedances | Sampled Fv exceedances |
| --- | ---: | ---: | ---: |
| Preserved opening comparisons | 40,704 finite | 200 | 420 |
| Added bore-free rear-recess comparisons | 2,496 finite | 0 | 0 |
| Added action-event comparisons | 6,144 finite | 0 | 0 |
| Final finite total | 49,344 | 200 | 420 |
| Analytical endpoints | 120 zero / 120 divergent | Source limits | Source limits |

The 7,008 actual curved-section normal results have maximum 0.021303480368
at the left knee inner block, `a12-left_gap`, original station index 9, before.
Independent polar/rectangle quadrature on every actual curved cut recovers
its signed axial force and bending moments within 9.10e-12 N or N·mm.
All 7,008 artificial subset normal/shear records stay separately labeled;
the actual longitudinal result does not turn subset shear into an actual
curved-section field. The final packet has 1,176 tangent-idealized cuts,
including 408 explicitly topology-limited cuts. There are 5,412 sampled peak
mesh differences above 5%, with maximum 31.0011%; maximum RMS difference is
0.871515%. No added recess/event cut exceeds the references or the 5% peak
difference threshold. These are assessments and limitations, not stress peak
convergence or complete timber resistance qualification.

Final consumer `coupled-opening-complete-replay-v2.py` SHA is
`0c30dc5870037c384cb56f04625dc0fcf5dad3a8b1ce8ee1f6f7b6f05c4e7955`.
`coupled-complete-attempt02` takes 38.272 seconds, with receipt
`dc149b7b37f338fd5b23e9c5f9900a9f668d8ddf4cc92a2e51f1bb23f3248b5c`,
summary `069418d2309b17ad41ebe54f0086b8e81c9d9970f070002f6a42f83c04a6de35`
and independent audit receipt
`635bf3d675dc31ef057aecea59d8513fdfda7328f79acd8089324fd5aa464476`.
That audit checks all 364 source pins, 12 outputs, the 2,066 required unit
fields, all numerical counts, all prior-row identities, and every actual
curved-section signed wrench. The concrete command is:

```sh
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/member-opening-general-completion/ownership-draft01/coupled-opening-complete-replay-v2.py --actions docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-action-reconciliation/attempt03 --action-receipt-sha256 370dafc75a90967cc45e9888bdbd5610fa2df6930a5821d4cd52d01bae70904e --recess-fields docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/member-opening-general-completion/rear-recess-fields-attempt01 --recess-receipt-sha256 3a9ac08e49ef8d962f4c4a7f52e14266791b33a878721bc0e225deb666725382 --event-fields docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/member-opening-general-completion/action-event-fields-attempt01 --event-receipt-sha256 1649a2b58eb307a0fb8f86a0d35d14145586ddd9ac9a428d0cdb32157e76ef46 --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/member-opening-general-completion/coupled-complete-attempt02
```

Two preliminary pure consumer stops are retained as implementation findings,
not engineering limits: one joined a field-manifest wrapper incorrectly;
the other compared a run-specific reused annotation as field identity.
Their source snapshots and STOPs remain recoverable. Corrected joins require
all four immutable NPZ/metadata path/hash bindings and keep the original
unit-resultant and weak-residual gates unchanged.


The maintained producer now consolidates the source-bound rectangular,
curved longitudinal, certified tangent and strict accepted-field reader APIs.
The predecessor's bore-free recess targets, original pressure reuse and
permanent body-balance audit are retained. Physics function bytes governing
accepted fields remain identical to the executed frozen method; a narrow
module RUF007 exemption preserves its recorded cache identity. The maintained
helper's lint header changes its file hash while preserving certification
function bytes. Executed ignored producers/helpers and every receipt remain
unchanged.

Historical receipts that name an earlier mutable producer authenticate its
recorded byte-identical `producer.py.snapshot`. The shared c4 version is
preserved in `attempt07/producer.py.snapshot` and
`ownership-draft01/shared-c4bf4023.py.snapshot`; the original evidence page is
preserved in `ownership-draft01/shared-676c8e09.md.snapshot`. This redirect is
limited to that producer source path and expected hash. Geometry, action,
reference, helper and output bindings are verified at their original paths.
The source integration audit at
`rawlocal/member-opening-general-completion/promotion-audit01/audit.json`
inventories every affected receipt and its specific snapshot pointer. The
recorded source-resolution map is an audit/recovery mapping; executing a
frozen command also requires its recorded producer bytes rather than the
maintained producer. It changes no frozen receipt or result.

The field cache, completed actual-section/action packets, numerical STOPs and
original pressure/profile references stay active reproduction inputs. No raw
run is pruned. Closed attempts may be archived only through the repository's
separate verified archive workflow after consumer and running-process checks.
Complete joint resistance, actual curved shear, local hole concentrations,
physical load introduction and disconnected-ligament bypass remain outside
these section methods. No material or shop inspection, candidate adoption,
fabrication, floor verification or climbing release is asserted.
