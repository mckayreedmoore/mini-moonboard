# Upper-G7 shaft completion

This narrowly scoped producer addresses the sole applicable numerical null in
the frozen [bolt reference completion](bolt-reference-completion.md): case
`a12-left`, axis
`wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/upper_rail_1`,
T=0 N and V=1.9755775926692833 N. Original receipt
`353f5890dd8cccc8db5cbf29bd7f2daa1de8877e3031825343a807a47421aa22`
retains 503 completed shafts, 1,006 completed own ends, and one shaft/two end
nulls. Those original outputs, receipts and producer remain unchanged.
The force basis is the saved **108-axis knee-bridge proposal frame with its
fresh gravity allowance**, authenticated through `knee-bridge-other-bolts`.
Its 84 existing physical axes are a subset of that proposal calculation.
This completion does not supply forces or results for a later original
104-axis compatible-frame calculation.

## Actual result and disposition

The parent executed `rawlocal/g7-shaft-completion/attempt01`. Receipt
`79aac71598f9e63f787620b14f2344c42f21417f2d87972b09991f85ee92032f`, summary
`dd442a24c08bfe724248b20224d7d28a2867de8900e71ee78317f09af9bca9a6`.
All **172 source bindings and nine output bindings** authenticate. One new
shaft-helper call completed the missing state and both own-end sources.

| Same-state isolated comparison | Completed | Numerical nulls | Maximum index | Reference exceedances |
| --- | ---: | ---: | ---: | ---: |
| Continuous shaft axial/bending/shear steel | 504/504 | 0 | 0.11193008492743632 | 0 |
| Simultaneous average T/V | 504/504 | 0 | 0.04052274152621833 | 0 |
| Nominal thread tension | 504/504 | 0 | 0.018390332348961952 | 0 |
| Independent signed own-end T/M and pressure-wrench sources | 1,008/1,008 | 0 | Separate sources, not washer capacity | Not applicable |

The initializer took **two nullspace descent steps and one range Newton
step**. Contacts changed from `[23,24]` to `[0,23,24]`, then `[0,23,24,47]`.
The tangent nullity changed from two to one to zero. The unchanged original
helper accepted the resulting seed at iteration zero with scaled gradient
**2.1060997390520697e-10 N**, far below its unchanged 1e-6 N gate. Host force
and moment residuals are **6.836975430246639e-12 N** and
**-2.5935698033663357e-11 Nmm**. Both end-contact moments are exactly zero
under the supplied T=0 law. The target shaft stress reference index is
**0.00015327895594591207**; its same-state combined steel index is
**0.00017033762076957602**. No demand or reference was reduced.

Independent saved-data validation reconstructed the 36-coordinate pose and
all 48 bore reactions with the pinned helper's beam rows, then recomputed
the original gradient and all 80 beam fields. Its maximum gradient is
**1.9130320851740157e-10 N**; recovered moment/shear/stress errors are below
**4.66e-10 Nmm / 1.17e-10 N / 9.03e-12 MPa**. The cleat's independently
summed interface moment is **-1.3398554044030675e-8 Nmm**. All force/moment
gates close. Validation is saved at
`rawlocal/g7-shaft-completion/validation01/checks.json`, SHA-256
`0c03bf2f0e37b98a6ef03a93430498f9106719f32edeb336751102effac49ca7`.

Byte comparison independently confirms the original **503 accepted steel
rows, 1,006 accepted end rows, 40,240 shaft field samples and 72 end-grain
rows remain exact**. The new 80 fields bring the total to 40,320. Thus the
previous numerical null is actually completed, with its original failed
result preserved as history. Convex stationarity completes this isolated
model comparison; it does not establish complete joint resistance.

## Exact question and method

The saved branch activates only host sample 23 and cleat sample 24. Host
sample 23 is 1.2523972581577472 mm from the interface. At T=0 the annular end
contacts transmit no moment; this single off-interface host force cannot
balance both the imposed shear and zero interface moment. The previously
recorded 0.0194798531 N scaled rotation residual therefore needs an additional
bore reaction. The prior regularized tangent-null step barely advances toward
another contact. Repeating that branch or increasing the iteration cap would
not answer a new method question.

At T=0 the unchanged first-order finite shaft model has convex energy

`E(z)=0.5 z'Kz+l'z+0.5 sum(w_i [abs(C_i z)-g_i]_+²)`.

The four analytical elastic null modes are shaft rigid translation, shaft
rigid rotation, host translation and host rotation. Restricting those modes
by the currently active bore rows gives the exact tangent nullspace. A
nonzero projected gradient supplies a descent direction that preserves
bending and existing active penetrations until another contact engages.
Otherwise the positive tangent eigenmodes supply a Newton direction. Each
direction uses the exact convex line minimum: all positive bore breakpoints
are enumerated, and the zero of the affine derivative is found within its
piecewise quadratic interval. Roundoff of a nominally zero bending curvature
is bounded and clipped at zero only in this initializer's line calculation.

The [NumPy 2.5 SVD](https://numpy.org/doc/stable/reference/generated/numpy.linalg.svd.html)
and [symmetric eigensystem](https://numpy.org/doc/stable/reference/generated/numpy.linalg.eigh.html)
documentation specifies the decomposition and ordering used here. No new
dependency or physical regularization is introduced. The initializer has a
32-step bound and supplies only a pose; it cannot accept a shaft result.

The pinned `upper-right-combined-transfer.py` helper then evaluates that pose
with its original signed clearance springs, Kwood=20 MPa/mm, 48 bore samples,
1e-6 N scaled gradient gate, independent host force/moment gates and all 80
shaft field samples. The existing `seeded_shaft_solver` changes only its
initial pose and logging. The first-order bending convention remains the
consumed producer's convention. Geometry, loads, material assumptions,
stiffness, gaps, quadrature and reference capacities remain unchanged.

## Preparation and execution boundary

The three-coordinate analytic oracle has two independent gap/nullspace modes
and one 10,000 N/mm elastic mode. Its exact answer is
`[1.155, -0.95, 0.0004] mm` for signed drives `[5, -4, 4] N`. It must exercise
null descent and recover the answer within 1e-10 mm before any target call.
It passed with pose error **2.220446049250313e-16 mm**. Frozen preparation
receipt `9356e1af866867550e31a50c7793202fd8501a2138727f798bf19e8175676183`
is at `rawlocal/g7-shaft-completion/preparation-rank-aware01/receipt.json`.
Run this light prerequisite with:

```sh
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/g7-shaft-completion.py --oracle
```

Parent execution owns the sole real target call, using a fresh immediate child
of ignored `rawlocal/g7-shaft-completion`. The producer authenticates all 159
original source bindings and ten outputs, the original receipt and producer,
and its own source/document bytes before and after computation. It reuses
the exact saved terminal pose and source actions; it does not invoke the
previous two-target `recover()` API. The new outputs preserve the original
503 accepted steel rows, 1,006 accepted end rows, 40,240 field samples and
72 end-grain rows byte-exact. Only the missing shaft and its two own-end
source rows may change; 80 fields may be appended.

The executed producer snapshot SHA-256 is
`7db839064cb4aa3327cc65f436d96d54a25d22805a6e39a8f2ea125c2a1d0f7b`;
its bytes remain unchanged in `attempt01/producer.py.snapshot`.
The maintained source now explicitly captures each loop iteration's line
derivative arguments and renames one unused unpacked variable. These are
lint-only changes. After normalizing those two edits, its full module AST
equals the executed snapshot; the complete three-coordinate oracle report
is identical, including the 2.220446049250313e-16 mm pose error. Scoped Ruff
passes. No actual shaft solve was repeated. Historical source-path bindings
must resolve to the executed snapshot, whose receipt and nine output hashes
remain unchanged; no receipt is repinned.

The consumed preparation documentation SHA-256
`81eae438832cf59719d7e630df0e1067e59dd9a3d7af7d499aa1d1c8493bca8b`
remains exact in both `preparation-rank-aware01/documentation.md.snapshot`
and `attempt01/documentation.md.snapshot`. The receipt's original maintained
documentation-path binding must resolve to that consumed snapshot when
authenticating the later maintained result narrative; no receipt is repinned.

The conditional isolated 504-shaft/1,008-end comparison inventory is complete
on this force basis. Reference exceedances remain outcomes. Complete joint resistance, actual
hardware capacities, common-host/global compatibility, physical release and
all formal criteria remain outside this initializer and stay unaccepted.
This producer supplies own-end pressure/wrench sources; it cannot complete
N09 washer resistance by itself. No native/CAD/global frame solve, geometry
change, fabrication, formal acceptance, staging or commit occurred here.
The new raw run and validation remain active as evidence;
the preserved unsuccessful runs remain recoverable history.
