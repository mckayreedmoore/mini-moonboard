# All-joint splitting assessment

## Scope and decision boundary

The owner clarified that the remaining splitting assessment must cover **all
joints**. This packet covers all **24 block duties and six retained two-bolt
arrangements**, including both sides of their connections: **24 cleats and 20
frame timbers, six simultaneous cases and both transverse directions**. Panel
screw actions on those timber receivers are included. Plywood screw-head
pull-through is a separate failure mode.

The reviewed **104-axis** layout remains authority. The completed **108-axis
knee proposal** remains a separate, unadopted source. Here, an outer knee spine
means the vertical cleat at the kicker/main-panel transition joining the outer
post to the sloping side member. Rear `lumber_leg_*` to floor-runner joints are
different duties and are included separately.

**A complete splitting-resistance pass is not established.** A positive normal
tensile lower bound identifies an opening requirement in the stated action
placement. A zero bound does not establish a local stress or fracture pass.
Existing axial bolt actions are already included and cannot be credited again
as spare reinforcement. Bolt alignment alone does not establish a supported
bolt/washer/host-contact load path.

## Existing evidence reused

| Timber scope | Exact source and remaining interpretation |
| --- | --- |
| Twenty cleats other than the four outer corners | [Completed transverse assessment](../remaining-block-transverse.md): 11,064 transverse cuts, physical timber gravity, original mechanical points/free couples. All recorded compression constructions remain below their reference. Positive opening remains on 14 bodies. |
| Two top outer cleats | [Normal census](../corner-split-closure.md) and finite-pressure constructions: both groups have finite compression-only normal witnesses. Mapped top gravity, simultaneous tangential actions and fracture limits remain. |
| Two bottom outer cleats | [Physical gravity update](../corner-physical-gravity.md): left has no positive normal bound; right retains 0.054537792 N in local `u`. Existing side-bolt/host redistribution is not established. |
| Two modified spines in the unadopted proposal | [Fresh direct-bridge replay](../knee-bridge-joint-replay.md): 2,352 normal and 5,124 grain cuts. New normal-transfer and declared component comparisons are complete; anchorage, elastic compatibility and full fracture resistance remain unqualified. |
| Twenty frame receivers | Complete original-point action archives exist. The parent-run producer below supplies their missing transverse signed-demand census without replacing gravity or transferring a cleat result to a host. |

The reviewed source retains **250 lb × 2 downward, signed 300 N horizontal,
the original 100 mm hold lever and the existing gravity/accessory allowance**.
No load variant, new frame solve or material allowance is selected here.

## A concrete remaining geometry distinction

The saved opening paths are not confined to the two outer knee spines:

| Body / local direction | Saved maximum necessary tensile resultant (N) | Reviewed bolt direction |
| --- | ---: | --- |
| Left / right outer knee spine, `v` | 430.147568 / 424.262642 | All four existing shafts run along `u`; none directly crosses this opening direction. |
| Left / right inner knee frame block, `v` | 55.453 / 49.263 | Side shafts run along `u`; header shafts along grain. No existing `v` tie. |
| Left / right center-post cleat, `v` | 1.364486 / 1.468498 | Post shafts run along `u`; header shafts along grain. No existing `v` tie. |
| Left / right center-principal cleat, `v` | 4.933802 / 5.172594 | Principal shafts run along `u`; header shafts along grain. No existing `v` tie. |

These are source-placement demand lower bounds, **not physical failure loads,
new bolt requirements or capacity ratios**. The four proposed spine bolts do
not bridge the other six bodies. Their recorded forces/free couples must be
mapped to supported physical boundary tractions before an apparent point-load
opening is treated as a required physical reinforcement change.

Other positive paths have parallel existing bolts. Those bolts normally have
one outer washer on the cleat and the other on a host. Their route depends on
the host/contact reaction; they are not independent two-washer ties inside the
cleat. Any revised allocation must balance every affected host and cleat,
including both shears, torque and both bending moments.

## Applicable resistance and load-path basis

[NDS 2024 §3.8.2](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf)
directs avoidance of perpendicular tension and sufficient mechanical
reinforcement where unavoidable. It supplies no generic sawn-lumber
perpendicular tensile design value. §§3.10.2 and 3.10.4 supply bearing
comparisons; their bearing-length adjustment is conditional and is not
automatically applicable to these short cleats.

[NDS §§11.1.2–11.1.3](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf)
permit local engineering mechanics and appropriate procedures for eccentric
connections. They do not provide a scalar capacity for this complete crossed
group. The [USFS timber bridge manual, §5.8, p.5-88](https://www.dot.state.mn.us/bridge/pdf/insp/USFS-TimberBridgeManual/em7700_8_chapter05.pdf)
supports bolt tension and net-annulus washer bearing checks, but does not
provide a short-block washer plug-shear or anti-split anchorage capacity.

[Appendix E](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Appendix.pdf)
supports matching parallel-grain net-section and row/group tear-out paths.
Those results cannot become a transverse splitting capacity. The existing
[corner](../corner-splitting-disposition.md) and
[spine](../knee-spine-splitting.md) decisions explain why the EC5 loaded-edge
beam scalar does not qualify these complete opposing/crossed connection
actions. No characteristic-to-design conversion is invented.

The bounded closure route is therefore one of:

1. Supported physical boundary placement and timber transfer that needs no
   perpendicular opening resistance, with the simultaneous shear/torque path
   retained under the stated nominal sharing assumptions.
2. A supported, simultaneous existing bolt/washer/host reaction allocation
   that carries the opening, with its combined steel, bearing and anchorage
   resistance established.
3. An applicable resistance procedure for the actual timber opening path.

The source data do not establish routes 2 or 3 merely because a bolt's steel
index is low. This identifies an exact missing basis; it adds no blanket
physical-test, new-FEM or external-sign-off requirement.

## Finite parent-run producer

[closure.py](closure.py) authenticates the completed receipts, source closures,
44 timber geometries and the reviewed force register. It reuses all saved
cleat normal/pressure states. It then evaluates original archived receiver
point forces and free couples on both sides of every selected transverse
station, carrying the complete signed
`[N, Vp, Vq, T, Mp, Mq]` wrench.

Receiver stations are their source action positions, near faces and interval
midpoints. No continuous maximum is claimed. A gross stock rectangle encloses
the removed-hole/recess geometry, so its hull gives a **necessary lower bound
under that point-action placement**. A zero value on this larger hull supplies
no retained-material pressure witness. Receiver gravity stays mapped; it is
not silently converted to a physical uniform field.

The output links every one of the 30 duties to all its timber sides, both
transverse orientations, six-case witnesses and existing aligned bolt
candidates. Existing local corner allocations and the original global frame
actions retain their own force authority. Existing tie values are recorded
with full-state source pointers; they are not subtracted from opening demand.

API: `build(output)`. Output must be a fresh child of this folder's ignored
`rawlocal/`. Parent owns execution, integration and publication. No source
packet, hole, geometry, frame, native solve or software test is changed.

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/closure.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/rawlocal/attempt01
```

## Completed parent calculation and final disposition

Parent executed the frozen producer once, exit 0. Independent authentication
confirmed **all 498 source pins and four output artifacts**, with no changed
inputs. Targeted Ruff passed. No software tests, review loop, new frame/CAD/
native solve or geometry change occurred.

| Saved artifact in `rawlocal/attempt01/` | SHA-256 |
| --- | --- |
| `producer.py.snapshot` / current `closure.py` | `095cc122b4f0292fecd108446c24744a2671a703d156527afcd243eb8de9035d` |
| `checks.json` | `91124cdd68bd440d5221047f77d81b47f13cbcf06e68093f3ebc6c5091a74fb9` |
| `receipt.json` | `1c037ed5f138cf738f4f4ca8628e377ef2ffbcf332419f496a5b03aab7d759b9` |

Coverage is **30 joint duties, all 44 timber sides and 528 body/case/transverse
orientation states**. The calculation reuses **62,376 cleat cut limits** and
adds **25,212 original-point receiver cut limits**. These are overlapping
method records, not additional hardware or independent joint capacities.

### Complete duty coverage

Left/right means two independently sourced duties, not a mirrored acceptance.

| Joint family / duties | Connected timber sides |
| --- | --- |
| Bottom center, left/right | Center principal, bottom rail, cleat |
| Bottom outer, left/right | Side member, bottom rail, cleat |
| Center post/header, left/right | Center post, header, cleat |
| Center principal/header, left/right | Center principal, header, cleat |
| Outer knee inner-frame block, left/right | Header, side member, inner block; the side shafts also end on the spine |
| Outer knee spine, left/right | Outer post, side member, spine; the side shafts also end on the inner block |
| Left service inner, lower/upper | Left center principal, matching service rail, cleat |
| Left service outer, lower/upper | Left side, matching service rail, cleat |
| Top center, left/right | Center principal, top rail, cleat |
| Top outer, left/right | Side member, top rail, cleat |
| WJ04 right service inner, lower/upper | Right center principal, matching service rail, cleat |
| WJ06 right service outer, lower/upper | Right side, matching service rail, cleat |
| Retained upper rear-leg pair, left/right | Side member and rear `lumber_leg` |
| Retained front-runner pair, left/right | Floor runner and outer post |
| Retained rear-runner pair, left/right | Floor runner and rear `lumber_leg` |

The four continuous knee-side axes remain one bolt each with two lateral
interfaces. Their middle side-member receiver is included even though its
washer is not on that middle member. The machine result preserves every
exact axis ID and receiver link, and checks that all 44 timber bodies appear
in the duty map.

### Supported normal transfer versus unresolved resistance

| Final finite disposition | Coverage | What is established / exact remaining basis |
| --- | ---: | --- |
| Reused finite compression-only normal constructions | 27 cleat body/direction envelopes | Supported normal force/moment transfer at the listed cuts, below the recorded compression reference. Simultaneous tangential transfer, local concentrations and full fracture resistance are not established by this normal subcheck. |
| Positive cleat opening with aligned existing bolts | 13 cleat body/direction envelopes | A bolt/host geometry candidate exists. Its present force is already counted. A changed allocation still needs actual supported washer/contact pressure, full cleat/host wrench recovery, combined bolt loading and local anchorage resistance. |
| Positive cleat opening without parallel existing bolt | Eight cleat body/direction envelopes | The six header/inner-frame paths and two spine paths listed above. No existing axial stitch route is established. Supported physical boundary placement or an applicable opening-resistance/host-bypass procedure is needed. A nonparallel bolt group may provide a host bypass, but alignment data alone neither establishes nor excludes it. |
| Receiver original-point gross-hull opening diagnostic | All 40 receiver body/direction envelopes | Full signed demands are recorded. The boundary placement and exact local group/crack path must be established before assigning a splitting demand or comparing resistance. These are not 40 new physical failures or automatic hardware changes. |

Nine cleats have no positive normal bound in either listed transverse
direction: both bottom-center cleats, bottom-outer left, both left-service
inner cleats, both top-outer cleats and both WJ04 cleats. The other fifteen
have at least one positive bound. This is a statement about the frozen finite
normal paths, not a complete resistance classification.

### Receiver diagnostics and their practical limit

The largest receiver original-point lower bounds are:

| Receiver / local direction | Necessary tensile resultant lower bound (N) |
| --- | ---: |
| Top rail, `v` | 1,941.122340 |
| Left / right side member, `v` | 1,558.412524 / 1,475.294296 |
| Left / right rear leg, `v` | 1,079.217999 / 1,059.906811 |
| Left / right outer post, `v` | 751.064446 / 745.299180 |
| Left / right floor runner, `v` | 496.501591 / 489.115848 |
| Header, `u` | 333.497446 |

The recorded receiver peaks aggregate each whole body's actions. They are
**not loads allocated to individual joints or additional bolts**. Receivers
retain lumped mechanical moments and mapped gravity; spreading those actions
onto actual bore walls, washer lands and contact cells preserves the whole
wrench but can change an internal transverse cut. A single moment at a point
does not define how boundary traction is divided by that cut. Accordingly,
these larger numbers cannot prescribe reinforcement or establish physical
splitting without that placement basis. Some receiver actions also belong to
the existing panel screw head/withdrawal path, whose exception is already
recorded separately.

### Exact bounded closure basis

The next finite question is **boundary placement and anchorage at the affected
path**, not another global frame or load study:

- For the six small header/inner-frame `v` paths, recover the existing tie,
  contact and bore actions on their actual supported cleat surfaces while
  preserving each saved simultaneous interface wrench. The completed
  [header traction map](../header-traction-map.md) supplies the header side
  only; it is not a cleat-side pressure field. The completed continuous-shaft
  fields likewise do not supply all inner-frame timber tractions.
- For positive paths with aligned existing bolts, an admissible host bypass
  must balance both timber bodies at the actual supported pressure locations.
  An extra axial reaction is a new passive allocation, not existing tension
  available for reuse. Present source data supply neither that allocation nor
  a generic short-block washer anchorage resistance.
- For the 20 frame receivers, isolate the physical group/cut of interest and
  use an already-supported boundary recovery where available. Current
  physical top-rail recovery is grain-section evidence; it does not supply
  all transverse traction cuts. Whole-body point envelopes cannot fill that
  gap or serve as a universal EC5 loaded-edge demand.

No supported complete existing-host redistribution or universally applicable
splitting resistance was found in the frozen inputs. The two-spine proposal
supplies its particular **conditional normal-transfer route**, with its
unchanged anchorage and compatibility limits. It does not close the six other
unbridged cleats or the receivers. The data do not establish that additional
holes are required, and this packet proposes none.

**Final result: all-joint demand/path evaluation complete; all-joint splitting
resistance remains unresolved.** This is a finite conclusion about the
available evidence, not an instruction for an open-ended modeling program.
Reviewed 104-axis geometry, the separate 108-axis proposal, the 47 formal
criteria and all complete-joint/fabrication/physical-release flags remain
unchanged. Parent owns shared integration and publication.
