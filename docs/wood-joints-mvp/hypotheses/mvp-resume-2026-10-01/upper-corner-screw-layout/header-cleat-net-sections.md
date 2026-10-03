# Six header cleats: nominal retained-wood section comparison

## Scope and status

The parent executed the frozen [producer](header-cleat-net-sections.py) once,
returning `COMPLETE_HEADER_CLEAT_NOMINAL_SUBSET_COMPARISONS`. All 36 body/case
comparisons and 1,968 signed traces completed; all reported nominal subset
indices are below 1.0 under the stated hypotheses. This completes the assigned
nominal arithmetic, without establishing joint acceptance. It covers the two
center-post cleats, two center-principal cleats and two inner knee blocks
excluded from [the twelve-block comparison](remaining-net-sections.md).
The [header comparison](header-net-section.md) covered `base_header`, not these
six bodies. The worker inspected sources, linted the producer and authenticated
the returned parent result; it did not execute the calculator or run tests.

The original 100 mm force lever, 250 lb × 2 downward load, signed 300 N load,
gravity and separate 25 kg accessory assumption remain the frozen basis.
Use all six saved cases, each body's full 40 point actions and free couples,
and both saved one-sided traces at every recorded station. This is 36 body/case
comparisons and 1,968 signed section traces. Nothing is replaced with an
isolated header-interface force or a peak from another case.

## Completed comparison

All five peaks below occur on `knee_outer_left_inner_frame_block` in A12-rear.
Each row retains its own station and one-sided trace; the peaks are not combined
into a synthetic load state.

| Nominal comparison | Peak index | Grain station (mm) | Trace |
| --- | ---: | ---: | --- |
| Total tension / Ft | 0.030579739 | 88.787553 | before |
| Total compression / Fc | 0.009685956 | 88.787553 | before |
| Absolute bending / Fb | 0.017266023 | 88.787553 | before |
| Axial-plus-bending reference sum | 0.020922650 | 54.315553 | before |
| Same-state transverse-plus-torsional shear bound / Fv | 0.138130010 | 54.315553 | after |

The simplification deliberately omits up to 16.93% of actual net sound wood for
the posts, 10.35% for the principals and 11.22% for the knees. All original six
wrench components still pass through the retained rectangles. No nominal
section deficit is identified in this finite scenario under the declared
sharing assumptions. These results support retaining the reviewed cleat
sections for the working MVP; they supply no local stress or complete-joint
qualification.

All nine available exact right-knee section areas match the analytic physical
circle/slot areas within 3.64e−12 mm². Independent restoration of saved cuts
differs by at most 8.53e−14 N and 1.73e−11 N·mm; regional reconstruction differs
by at most 5.69e−14 N and 3.64e−12 N·mm. The parent also completed the existing
translated-rectangle known-answer arithmetic. These small accounting errors
establish arithmetic closure, not precision of the physical assumptions.

## Finished geometry and practical simplification

All six finished bodies have six rectangular outer planes, two full transverse
X bores and two full longitudinal Z bores. Grain is +Z; section coordinates are
u=+X and v=+Y. No slope, housing or blind passage is introduced.

| Bodies, left and right | Finished u × v × grain length (mm) | Bore diameter (mm) | Saved stations per body |
| --- | ---: | ---: | ---: |
| Center-post cleats | 88.9 × 88.9 × 128.9 | 7.3 | 26 |
| Center-principal cleats | 83.9 × 139.7 × 134.7 | 7.3 | 28 |
| Inner knee blocks | 88.9 × 133.35 × 139.0 | 7.5 | 28 |

The longitudinal holes leave circular voids at every grain-normal section.
The existing nominal calculator accepts rectangles. The parent approved
omitting full strips enclosing these circles, spanning the finished X width:

| Family | Longitudinal-hole Y centers (mm, global) | Omitted Y strips (mm, global) |
| --- | --- | --- |
| Post | −148.75, −113.75 | [−152.4, −145.1], [−117.4, −110.1] |
| Principal | −140, −75 | [−143.65, −136.35], [−78.65, −71.35] |
| Knee | −155.7, −62.35 | [−159.45, −151.95], [−66.1, −58.6] |

At each saved station, remove the actual transverse cylindrical chord as well.
The remaining rectangles are wholly inside the physical wood. Their topology
is artificial: a connected physical ligament may be represented by several
rectangles. The result records the actual disks and transverse slots, actual
opening area, retained subset area, and deliberately omitted sound-wood area
and fraction. No hole or stock dimension is changed.

Authentication checks all six outer planes, complete cylinder trims and radii,
nonintersecting holes, six STEP bindings and analytic finished-solid volumes.
The actual circle/slot areas also must match the nine existing exact saved
sections for the right inner knee block. No new CAD section is generated.

## Load transfer and existing references

Every full signed `[N, Vu, Vv, T, Mu, Mv]` is passed to the unchanged
[rectangle calculator](corner-net-section.py). Positive N denotes tension in
the saved negative-grain-half internal convention. The opposed half checks
closure; it is not reversed into a second tension/compression load case.
Independent restoration from all source point actions checks every saved cut.
Regional forces, centroid-offset moments and free moments must recover all
six original components without an added balancing couple.

Retain the existing common longitudinal strain plane, transverse force sharing
by retained area, equal longitudinal shear moduli and common rectangular twist
with torque shared by rectangular Saint-Venant J. These are explicit working
hypotheses. Full signed demands receive no credit for the omitted sound wood.
The nominal same-state shear comparison remains
`1.5*hypot(Vu, Vv)/A + tau_torsion`, divided by existing longitudinal Fv.
Tension/Ft, compression/Fc, bending/Fb and the axial-plus-bending reference sum
are reported separately with their own case, station and trace witnesses.

| Existing reference scenario | Fb (MPa) | Ft parallel (MPa) | Fc parallel (MPa) | Fv (MPa) |
| --- | ---: | ---: | ---: | ---: |
| Post, original 4×4 CF factors | 9.307922 | 5.946728 | 10.704111 | 1.241056 |
| Principal and knee, explicit CF=1 study | 6.205282 | 3.964485 | 9.307922 | 1.241056 |

These frozen per-member values are checked against the existing
[material inputs](../../hardware-material-specification-2026-09-30/material-inputs.json).
They retain dry DF-L No. 2, normal duration, unincised wood, normal temperature
and the recorded factor assumptions. The final-section grade/size status for
ripped principal/knee blocks is not qualified by the CF=1 study. The parent's
separate duration and permanent-load work remains separate.

Omitting sound wood is a supported material-subset simplification. It does not
prove a bound on actual local stress or give exact torsion of the perforated
section. These finite nominal comparisons assign no splitting, notch,
end-bridge, perpendicular-tension or complete-group capacity. No continuous
station maximum, compatibility solution, hardware rating or joint acceptance
is established. All existing 47-criterion authority and joint/release HOLD
boundaries remain unchanged; all qualification and physical-release flags
remain false.

## Frozen sources and parent execution

| Source | SHA-256 |
| --- | --- |
| `../member-screen-attempt02/four-screw-layout01/member-results.json` | `54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5` |
| Same packet, `geometry.json` | `c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af` |
| Same packet, `action-section-arrays.npz` | `ddfa310266661ea5ba6e188d2bf473121d99158d50921c84760744519e2a7caf` |
| `../../current-finished-feature-register-2026-10-01/surfaces.json` | `33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb` |
| `rawlocal/header-local-transfer/attempt01/model.json` | `eae4fc005cdd079f90f527be611e45a137aa275b129e16eebf964c422d69ae52` |
| Same packet, `inputs.json` | `cccd8969132c30e996fe5d3509069dbe851720786cec92a46a064cc0f7c0758b` |
| `corner-net-section.py` | `8a60447291161300ec4ee4f4f89c783cdcb565ee771e972c524ffd10f006d0e5` |
| `corner-timber-sections.py` | `d0e2c5cb94b056cab71072fcab52cc7be8760fb7d32368c097a45050b3493633` |
| `remaining-net-sections.py` | `acd60cee627331fdfeb06eb02321221f09a666bcea7e3997a9e51e616c98c129` |
| `../member_stability.py` | `eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72` |

The producer additionally authenticates the contract receipt, material record,
current frame comparison/response and each STEP, and records their full hashes
in its result and receipt. It reuses the opening/interval functions and summary
function from the pinned producers without calling their run functions. The
existing translated-rectangle known-answer arithmetic is included once in
the parent's finite calculation. No software test or mechanics solve runs.

API: `build(output: str | pathlib.Path) -> dict`. The parent used the following
command once from the repository root. Preserve `attempt01`; any separately
authorized rerun requires a fresh owned child:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/header-cleat-net-sections.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/header-cleat-net-sections/attempt01
```

Outputs are `checks.json`, `receipt.json`, `producer.py.snapshot` and a local
`.gitignore`. The returned summary reports status, 36 body/case comparisons,
1,968 traces, global signed witnesses, accounting differences and output hashes.
The result retains per-body and per-case peaks, all section geometry and all
nominal regional comparisons. The worker authenticated all 21 source pins and
the two receipt-bound outputs, without rerunning arithmetic.

| Completed artifact | SHA-256 |
| --- | --- |
| Frozen `header-cleat-net-sections.py` | `3e680b2ac439c9c0be1c958dfff730725f3b8da07c1c7c38ab1b8a30d7178d6d` |
| [Parent result](rawlocal/header-cleat-net-sections/attempt01/checks.json) | `b70fd818654a4d6509186a2718a81fa0b564cfc7ad808be52946f0eddfead1a2` |
| [Parent receipt](rawlocal/header-cleat-net-sections/attempt01/receipt.json) | `89b35eaecd8b234f2b7e34eeb1df567e93278e7f01a96bd5b7b5b4d36734c316` |
