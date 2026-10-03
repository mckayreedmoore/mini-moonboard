# Actual corner cleat timber-section worksheet

The completed first-order result supplies independently balanced applied
actions for **both actual cleats, both hosts and six cases**. This worksheet
calculates 25,224 finite grain-plane cut limits from those actions and original
mapped W included once. The largest conditional intact-section normal,
translational-shear and individual finished-path parallel references are
**0.046877**, **0.153673** and **0.169280**, respectively. They do not resolve
the local transfer through the bored sections.

The deciding unresolved right witness is **K12-rear**, at grain station
**62.973880 mm, after**: its shaft-axis action account carries
**48,521.003487 N·mm** resultant bending and **−20,225.821586 N·mm** torque
through a section containing three separate material regions. Those regions
have no assigned loads or compatible timber stress field. The corresponding
actual-left witness is A12-left, with **43,176.665320 N·mm** bending and
**20,846.726547 N·mm** torque. The two sides use their own states and geometry.

## Inputs and finite action account

[The producer](corner-timber-sections.py) consumes the parent's completed
`rawlocal/corner-first-order/attempt01/checks.json`, SHA256
`b15b57d3879fdca2dac607d11a2ad127acd1008f6c2a6f546333a1b26c754cfe`.
Its 12 block states contain `physical_cleat_actions`, four actual bolts,
32 face cells per block, and the original `current_weight_once_n_nmm`.
Geometric shortening and preload stiffness are absent together; the parent's
frame response, contact laws and recorded first-order assumptions are retained.
This producer imports only the frozen traction arithmetic and existing DOF
label parser. It runs no contact solution, mechanics, CAD or frame solve.

For each block, the producer uses the returned `physical_cleat_actions` once
and independently reconstructs all 20 original nodal W actions from the
frozen F operator and node coordinates:

```text
F_case = 1.1111358300342407 * F[:,2i] + F[:,2i+1]
Q_external(c) = sum [F_j, (r_j-c)×F_j]
```

That nodal sum must equal both the original W block and the parent's saved
weight wrench, including its moments. No gravity point, uniform weight,
balancing couple or second copy of W is substituted. Whole-cleat residuals
reproduce the parent result; maximum global components are
0.000099119 N and 0.004499565 N·mm.

The actual left/right grain directions are opposite. Each block retains its
own right-handed frame `[g,u,v]`, with `u=global X` and `v=g×u`. Its grain
station starts at `c−L g/2`, where `c` is that block's actual common datum.
Wrenches on the negative half's outward +grain cut are ordered
`[N,Vu,Vv,T,Mu,Mv]`; positive N is tension.

For each station, the arithmetic retains both limits:

```text
Q_internal,before = −sum(actions strictly before the plane)
Q_internal,after  = −sum(actions before or on the plane)
Q_same_internal   = +sum(actions on the opposite half)
```

All moments are independently transported to the cut datum. Plane events
include every retained action's grain coordinate, bore centers and shoulders,
the two grain ends, and midpoints between bore shoulders. Events within
1e-6 mm are grouped for coordinate rounding; on-plane jumps are retained.
The largest disagreement between opposite-half accounts is
0.000132634 N or 0.004730912 N·mm in the grain frame, consistent with the
recorded whole-body residual transported to the cut. No averaging hides it.
These are finite sampled-action results; a continuous envelope inside a bore
interval is not established.

## Exact current finished geometry

The geometry is the frozen correction's **119.7 mm grain length** and
**88.9 × 139.7 mm** section. The proposal's construction is a rectangular
blank with exactly four disjoint transverse through cylinders;
[the original construction, lines 130–177](../top_corner_correction.py#L130)
and the two corrected STEP hashes are pinned. No STEP is reopened in CAD.
The analytic removed volumes reproduce each recorded finished volume to
less than 0.001 mm³. Older 88.9 mm depth descriptors supply grain axes only.

At station s, each bore removes a full-width stripe in its own transverse
direction with half-width `sqrt(radius²−(s−s_bore)²)` when the expression is
positive. Rectangle-minus-stripe areas are evaluated directly. Tangencies
and a 1e-6 mm neighborhood also withhold elementary intact-section screens.

| Current plane | Actual geometric net area, mm² | Material regions |
| --- | ---: | ---: |
| Bore-free rectangle | 12,419.330 | 1 |
| Either rail-bore center, s=43.35 or 76.35 mm | 11,371.580 | 2 |
| Paired side-bore centers, s=59.85 mm | 10,819.130 | 3 |

The rail-bore center regions are 5,546.090 and 5,825.490 mm², with their
order reversed between the two actual sides. The paired side-bore regions
are 2,793.6825, 5,231.7650 and 2,793.6825 mm². These are actual geometric
areas; no common strain or distribution of N, V, T or M among them is assigned.

At a bore-intersecting plane, the force account follows the source's requested
shaft-axis station resultants. The model does not recover a radial bore-wall
traction field or its allocation across this grain plane. Thus neither the
cut wrench nor summed region area establishes actual regional timber actions
there. Bore-free cuts outside the whole bore footprint retain the complete
station resultants in one half. The paired side-bore and disconnected-ligament
limitations remain explicit.

## Conditional NDS normal and shear comparisons

The existing material record supplies DF-L No. 2, normal duration, dry,
unincised and normal-temperature references. The current nominal 4×6 size
factors are **1.3 for Fb/Ft** and **1.1 for Fc**; the old smaller-cleat factors
are excluded. Fv remains 180 psi. Cfu and Cr remain 1; this worksheet adds
no duration increase, CL/CP credit or characteristic-to-design conversion.

| Reference | CF-only value, MPa |
| --- | ---: |
| Ft parallel | 5.153831077 |
| Fc parallel | 10.238714580 |
| Fb | 8.066866033 |
| Fv parallel | 1.241056313 |

These reproduce the existing
[member reference arithmetic](../member_screen.py#L147). They remain a
conditional material scenario, not inspected stock or newly adopted resistance.

The cached primary Chapter 3 was read directly. Applicable elementary
equations are net section/eccentricity in §3.1.2 (p.16), bending in
§3.3.2 (p.17), rectangular translational shear in §3.4.2.1 (p.19), and
parallel tension in §3.8.1 (p.24). Combined tension and bending in §3.9.1
(p.25) motivates the retained conditional normal comparison. Compression
and biaxial stability requirements in §3.9.2 remain separate.
[NDS 2024 Chapter 3](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf)

For an **intact bore-free rectangle** only:

```text
A = b d;  fn = N/A
fb_u = 6|Mu|/(b d²);  fb_v = 6|Mv|/(d b²)
normal_tension_reference = max(fn,0)/Ft + (fb_u+fb_v)/Fb
shear_u_reference = 1.5|Vu|/(A Fv)
shear_v_reference = 1.5|Vv|/(A Fv)
shear_sum_screen = 1.5(|Vu|+|Vv|)/(A Fv)
```

The bending sum bounds the elementary biaxial corner field. The shear sum
is a triangle-inequality screen of the two translational components, not an
NDS-listed combined shear/torque interaction. Torque is retained without a
resistance. The compression sum `max(−fn,0)/Fc+(fb_u+fb_v)/Fb` is recorded
as a diagnostic, **not** substituted for NDS Eq.3.9-3. Short-block contact
concentrations, timber compatibility, R/T shear applicability and stability
are not supplied by these elementary comparisons.

For every geometric net section, the producer also records positive and
negative `N/A` against Ft/Fc. This is scalar mean-force arithmetic for the
computed cut account. It establishes no bending distribution or regional
sharing. At bore sections, bending and shear comparisons remain null.
The maximum mean tension reference is 0.009505496 on actual right, and
0.008446435 on actual left, at the paired side-bore plane. These small numbers
do not remove the retained moments or qualify a code critical net section.
The §3.1.2.2 staggered-array interpretation for the orthogonal bore families
and 16.5 mm adjacent grain spacing remains unestablished.

### Individual finished-path parallel channels

The completed component geometry supplies both signed finished tangent paths
for every bolt. The producer uses those areas directly without redoing CAD,
bolt yield, washers, hardware or the assembly peer's component replay.
From each bolt's 24 actual cleat bore actions, it separately sums positive
and negative grain components within the same case. Each channel uses its
own matching path sign; opposed pressures are not cancelled into one demand.

The existing single-fastener reference is `Fv * minimum_one_plane_area`.
It retains Appendix E.3's two shear lines and triangular stress convention;
no extra factor of two, row count or group resistance is added.
[NDS Appendix E.1/E.3, pp.174–175](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Appendix.pdf)
Each result covers its parallel bore channel only. Other forces, seat moments,
opposed-channel interactions and the complete oblique group remain outside
that reference's scope.

## Finite results and deciding local witnesses

The sweep contains **14,316 intact** and **10,908 bore/tangency** cut limits.
Each table entry is a maximum selected from simultaneous records of that
one case. Columns are not combined into a new load state or utilization.

| Case | Left intact normal reference | Right intact normal reference | Left shear sum | Right shear sum | Left finished-path channel | Right finished-path channel |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| a12-rear | 0.041351 | 0.003403 | 0.133139 | 0.016964 | 0.148081 | 0.013418 |
| a12-forward | 0.034584 | 0.001667 | 0.110720 | 0.007913 | 0.122687 | 0.006540 |
| a12-left | 0.041712 | 0.002047 | 0.135726 | 0.009786 | 0.149320 | 0.007522 |
| k12-right | 0.002885 | 0.046370 | 0.014205 | 0.153673 | 0.010479 | 0.167346 |
| k12-rear | 0.004395 | 0.046877 | 0.021216 | 0.152979 | 0.016736 | 0.169280 |
| a1-rear | 0.000284 | 0.000294 | 0.001245 | 0.001319 | 0.001034 | 0.001034 |

The left intact normal witness is A12-left, s=55.336052 mm before; the right
is K12-rear, s=64.355131 mm after. Largest compression-plus-bending diagnostics
are 0.009189448 left and 0.010394468 right. None is complete joint acceptance.

The maximum finished-path channels are actual left A12-left side_2 positive,
**977.810849 N / 6,548.416698 N**, and actual right K12-rear side_2 negative,
**1108.518398 N / 6,548.416698 N**. Each uses its own 5,276.486353 mm²
finished path. These are recomputed cleat bore channels from the corrected
physical result, rather than acceptance transferred from an old host force.

The largest finite unallocated bending witnesses are:

| Side / case | Grain station / limit | N, N | Vu, N | Vv, N | T, N·mm | Mu, N·mm | Mv, N·mm |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Left / a12-left | 56.399753 / before | 470.972928 | −445.073947 | −612.129293 | 20,846.726547 | 25,340.560060 | 34,958.267176 |
| Right / k12-rear | 62.973880 / after | 530.026160 | −499.294359 | −693.126904 | −20,225.821586 | −28,316.751163 | −39,401.134285 |

The left witness's three material areas are approximately
2,936.908517 / 5,518.217035 / 2,936.908518 mm²; the right witness's are
2,905.781966 / 5,455.963932 / 2,905.781965 mm². No moment is dropped merely
because the whole cleat closes. At the right minimum-area paired-bore center,
s=59.85 mm after, the same K12-rear state carries
`[530.026160,−371.115063,−693.126904,−19591.281924,−26151.505612,−40737.649233]`
in N/N·mm. These exact inventory witnesses identify the next local transfer
question; their regional stresses are not established.

**The missing method is local timber transfer through the actual paired-bore
and between-bore ligaments**, including bore-wall placement, regional normal
and shear sharing, sectional bending, torque/warping and the simultaneous
face/washer actions. The rigid cleat supplies independent boundary equilibrium
but no such timber compatibility or stress field. A usable method must also
resolve the applicable staggered critical net section and interacting parallel
paths; Appendix E.4 cannot be filled by summing these individual references.
Any actual induced perpendicular-tension mechanism must be identified from
that transfer, with an applicable existing mechanical route. No Ft-perpendicular,
F90 conversion, fraction of Fv or invented interaction/capacity supplies it.

The **48 completed exterior host cuts** are reused from the frozen group
receipt. Current physical host interface differences are at most
0.000001419 N and 0.000067516 N·mm, within the recorded reuse scope. Their
complete-host equilibrium totals are preserved; no host mechanics or
intersecting host-section replay is performed. Component assembly remains
with the peer; knee work remains with the parent.

## Producer and receipt

From the repository root, a fresh arithmetic replay uses:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/corner-timber-sections.py \
  --nds-chapter3 /tmp/nds2024-ch3.pdf \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/corner-timber-sections/attempt03
```

The producer authenticates the cached primary PDF without a runtime PDF
parser. Runtime was Python 3.12.3 and NumPy 2.5.2. Targeted Ruff passed;
only finite arithmetic and source authentication ran. No tests, mechanics,
native/CAD/frame solve, shared-source edit, staging or commit occurred.

| Current delivered artifact | SHA256 |
| --- | --- |
| Producer | `d0e2c5cb94b056cab71072fcab52cc7be8760fb7d32368c097a45050b3493633` |
| [Attempt02 checks.json](rawlocal/corner-timber-sections/attempt02/checks.json) | `8b954edf5743999f427d2b99fcaaf9288578f02dc59a5cf1e632da634aa2e813` |
| [Compressed cut inventory](rawlocal/corner-timber-sections/attempt02/cut-records.jsonl.gz) | `0294778e879733fd28c72fe4c2a9e246569d02ce0176ca58b6a0fbd11f650372` |
| [Receipt](rawlocal/corner-timber-sections/attempt02/receipt.json) | `6aa0c694b8dca8998c7f3208d010b4088b2eea2df669ca36cbb6d1537f70726d` |

The ignored 3.41 MB compressed inventory retains all cut limits, geometry,
signed wrenches, opposite-half disagreements and null comparisons. The
786.8 kB checks file contains deciding witnesses, bolt-center sections,
finished-path channels and exterior-cut pointers. Attempt01 is retained;
attempt02 adds the explicit grain metadata/source-construction pins and
compresses the same cut inventory. All current **34 source pins** are checked
before calculation and after it; key bindings include:

| Input | SHA256 |
| --- | --- |
| Existing exterior-cut/group receipt | `0a69cd84902c9105f5e6b8f3c70e59efaae9ac56bc4c3238935d97a4185d210b` |
| Finished component paths | `401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6` |
| Actual corrected geometry proposal | `5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2` |
| Left corrected STEP | `7955c0ff9f0b23483b0607f6357c7825904bf2a9d949b7aba8876b3a96516d1d` |
| Right corrected STEP | `fe199dcce78d43140ef5299d82d0b888631905bd8686537d98a0997163e45b79` |
| Conditional material record | `0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a` |
| Grain/case metadata | `e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc` |
| Cached NDS Chapter 3 | `205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644` |
| Cached NDS Appendix | `1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31` |

The frozen traction and group leaves remain unchanged. This task owns only
the new timber-section producer/worksheet and ignored raw folder. It adds
no whole-group resistance, complete-joint acceptance or physical release.
