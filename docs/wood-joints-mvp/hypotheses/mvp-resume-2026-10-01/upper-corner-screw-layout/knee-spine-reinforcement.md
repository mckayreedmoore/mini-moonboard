# Knee-spine direct bridge: bounded proposal

**Parent calculation complete: all 984 listed cuts / 12 body-case states have finite normal-transfer witnesses below the declared references. Proposal remains unadopted.**
Add two hypothetical 1/4-in through-bolts along local `v` in each spine, at
`(grain,u)=(100,0)` and `(250,0)` mm, through the 139.7-mm depth. Proposed bore
envelope is 7.5 mm, matching current quarter-inch envelopes; it is not a drill
instruction. Current model and 104 axes remain authority. Four added stacks
would give **108 bolts, 108 metal nuts, 216 washers and unchanged 66 Hillman
screws**, only after owner review and later adoption.

Use the conditional partial-thread Grade 5 policy: the initial force packet retains an 8-in Lawson lead; the [corrected stock profile](knee-bridge-hardware.md) proposes 6.5 in to place threads at the nut seat.
Use matched quarter-inch Grade 5 metal nuts, and **25.4/8.3058/2.5 mm
OD/ID/thickness washer hypotheses at both ends**. [Existing product basis](washer-product-basis.md),
[washer hypothesis](retail-washer.md) and [axial-profile convention](../assembly-package/hardware-engagement.md)
are source-pinned. Nominal length does not establish thread at the nut seat.
Delivered body/thread length, thread engagement, head/nut bearing profile,
washer metal resistance, neighboring scene, bolt-tip clearance and tool access
remain unproved. The producer records the necessary conditional thread window.

## Frozen load and geometry basis

| Input under `rawlocal/` | SHA-256 |
| --- | --- |
| `remaining-block-transverse/attempt01/checks.json` | `f3118804d3a03df66d274d783ca93248757ac3d629de4a874d23e85da9a61f19` |
| Same receipt | `dce3437a105cdd269aec9ff98ac831c00d6e64e34a807c42254030ca4fffb519` |
| Same receipt-bound `cuts.jsonl.gz` | `86757d2db86751aa5cba5343df0065ac3d38cc7d69eeab71f02c55eedc72d4cc` |
| `knee-spine-net-sections/attempt02/checks.json` | `6b6c8df94f1ccab859ee980dd1835ba19286718f44e8a36ce6b9d0014064fc85` |

Keep all six original 250 lb × 2 + signed 300 N / 100 mm cases, original
forces/free couples, physical-gravity correction and source scope. The producer
authenticates inherited sources and binds every spine/case `v`-normal cut.
It analytically checks stock, full perpendicular-cylinder separation, new-bore
separation, radial boundaries and both washer lands, using frozen geometry.
Support is only on the source spine; no scene or actual-part fit follows.

## One allocation across every cut

For each spine/case minimize `T1+T2`, with nonnegative **constant** bolt tensions
across all its `v` planes. Enumerate two-variable LP vertices with the standard
library. For plane coordinates `p=grain`, `q=u`, set `P=−Mq`, `Q=Mp`:

```text
sum Ti >= N
sum gi Ti >= P
sum (L−gi) Ti >= L N−P
sum (ui+w/2) Ti >= Q+(w/2)N
sum (w/2−ui) Ti >= −Q+(w/2)N
wood: Nw=N−sum Ti, Pw=P−sum gi Ti, Qw=Q−sum ui Ti
```

Aggregate the maximum right-hand side across the case; keep each controlling
full-wrench witness. This hull optimum is a necessary lower bound with unbounded
point pressure. It is hypothetical **passive, load-induced tension demand**,
not credited installation preload or a solved elastic bolt reaction.

Evaluate the optimum and one declared **1.25 uniform force-margin candidate**.
Scale both case tensions together; change no load or stiffness, and do not tune
the margin. Reuse frozen normal/end-band and cylinder-exclusion helpers. Finite
positive-area compression rectangles use grain-end bands clear of all four
existing and two proposed cylinders, with every cut-specific rectangle checked.
Recover all normal resultants; retain both shears and torque unchanged. Added
steel transfers only axial normal force and its position moments.

Compare constructed wood pressures and each end's supported-annulus **mean**
with existing `Fc_perp=4.309223308230226 MPa`. Record separate conditional axial
bolt-yield/nut-proof references; no washer metal capacity is supplied. Failed or
absent finite constructions retain exact witnesses. An excessive sufficient
pressure construction is not proof that every possible pressure field fails.
Parent executes unloaded-zero-tension, combined-cut LP, cylinder-exclusion and
frozen geometric/normal known answers; these are arithmetic coupons, not tests.

## Required limits and parent command

**[Modified grain nominal checks complete](knee-bridge-grain.md): 1,560 signed limits, maximum shear/torsion index 0.416137.** Each new bore center removes
about 20% of its grain-plane area and changes regional torque sharing. Producer
exports actual modified center/tangency section geometry using the existing
section helper; the linked parent calculation compares full frozen grain W /
source CF references on modified sections. No old grain pass transfers. Equal concentric end-pressure/
axial-tie pairs give zero whole-body and grain-cut wrench under declared symmetry;
that identity supplies no regional sharing or compatibility solution.

Removed-wood volume/mass is recorded geometrically; added hardware mass and the
combined gravity delta remain pending global adoption. Current loads are kept
fixed for this proposal. Static witnesses, reference comparisons, delivered fit,
compatibility and qualification are distinct. Existing tangential/torque duties
remain; no Ft-perpendicular, complete-joint or physical acceptance is claimed.

API: `build(output)`; use a fresh child of `rawlocal/knee-spine-reinforcement/`.
Producer SHA-256: `2ecd3e799dc9929b2524b3fd17efd853ea2a0c0e57dcd3da5d7506267d7c0741`.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-spine-reinforcement.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-spine-reinforcement/attempt01
```

Saved `rawlocal/knee-spine-reinforcement/attempt01/checks.json` SHA **c9360e7ca4ab167a5cbc505373b2bd1342aa6a830f72a26113da9f7c4a8ad778**; receipt SHA **991f6742f6aae386552338b1fea79f02766bd0def09bfa8fabea27560ba13819**. All 47 source pins and four receipt artifacts match.
At the declared 1.25 force margin, peak bolt tension is **1060.657 N**; wood compression/washer-mean/bolt-yield/nut-proof indices are **0.616 / 0.544 / 0.082 / 0.063**. Full-wrench recovery error is below 0.000000001 N/N·mm.
Bare hull optima do not supply finite pressure. The linked margin construction retains both shears and torque; it establishes a prescribed static route without an elastic allocation or global feedback.
No software tests, review loop, CAD/frame/native solve, geometry adoption or physical release occurred. Old applicability note and frozen evidence remain active.
Parent owns the separate grain result; Tesla owns the saved-scene fit task.
