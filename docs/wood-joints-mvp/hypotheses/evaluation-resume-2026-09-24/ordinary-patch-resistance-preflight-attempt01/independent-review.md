# Independent review: ordinary-patch resistance preflight, attempt 01

**Review result:** no material correction is required. The artifact is suitable
as a conditional, pre-demand component-reference screen. It does not establish
member or joint resistance, demand, load sharing, or acceptance.

## Pins reviewed

| Artifact | SHA-256 |
| --- | --- |
| [README](README.md) | `3ea2cc8ca8c03fda4db5ffd6516665270c9f9f0bcce394e24a06cec038fa8740` |
| [Machine report](resistance-preflight.json) | `57e3fe87c5aea3f8f6f02def83f4ceeb2da8a4b517c4fd761724e96f2d9aafdf` |
| Producer | `e9e53c6e66d977fc69f153dc72f2b0edc9e5e8529d56006da8151b6bcdcd4043` |
| Focused tests | `e0215957a4abc1e6bb74e7259068b6cf4938efbe2219219978a366952611ac4d` |
| `mini_moonboard/wood_joint_bolt_resistance.py` | `302f6f298d40b1ef33be8ed82639cddcfbeebce6512dfaf6067d29bba7392226` |
| `mini_moonboard/bolted_timber_checks.py` | `a1414547d9eaa3d60e81482b4a2cac2d49e88f31aafa341dca5be9ec8ef4aa13` |
| Frozen patch inventory | `70b396e636175abcad7467dc145029d7126c1ea7dff1d053a61f8c5321e1c1d3` |
| Frozen seat classification | `18bdf1b9736ce6ca2cf2b3dd0488a7651da05f35e531605fd465e7b502363f13` |
| Proposal-only material map | `9e1cbc8945d33683de3cb71ba716581919f508466d8a27b181865da4cc675fd4` |

## Findings

The eight reported wood seats are the head-side and nut-side washer seats for
the four current bolts, each mapped to the correct first or last wood receiver.
The source classifier marks finite opposed planar mesh overlays and explicitly
leaves pressure, preload, and a load-transfer law unestablished. The
`mesh_overlay_area_mm2` field remains geometry evidence; it is not treated as
pressure or resistance and is not used to claim that every washer tolerance
extreme has full support on delivered wood.

The washer envelope is traceable to the 1/4-in Type A Wide series: the cited
[ASME B18.21.1-2009 (R2016)](https://www.asme.org/codes-standards/find-codes-standards/b18-21-1-washers-helical-spring-lock-tooth-lock-plain-washers)
covers plain-washer dimensions and states that dimensional inclusion does not
mean every size is a stock item. The corresponding limits, ID 0.307–0.327 in
and OD 0.727–0.749 in, convert to the report's 7.7978–8.3058 mm and
18.4658–19.0246 mm. K.L. Jack 25NWUS is only a candidate dimensional example;
no washer is selected or delivered. Since the 7.5 mm value is a CAD bore
envelope and is smaller than even the minimum washer ID, `max(wood bore,
washer ID)` correctly makes washer ID the inner diameter of the conditional
annulus at both extrema.

I independently checked the annulus endpoints: minimum OD with maximum ID
gives 213.6279 mm² and 920.5702 N; maximum OD with minimum ID gives
236.5067 mm² and 1,019.1603 N, using 625 psi and the exact pound-force
conversion in the producer. These are raw `Fc⊥ × area` references under
uniform compression, full annular support on sound wood, and no preload or
bearing-area increase. The source is the [AWC 2024 NDS Supplement, Table
4A](https://awc.org/resources/2024-nds-supplement/) and the linked
[NDS-2024 resistance-basis note](../../../bolt-resistance-basis.md). The
625 psi value is conditional on dry DF-L No. 2 lumber in the table's
normal-duration basis; delivered stock is unverified and no adjustment factor
is applied. It is not an allowable joint load or a washer/bolt capacity.

The group calculation binds the two current pairs correctly. Both have
33.0 mm center pitch and parallel axes with negligible axial datum offset;
33/6.35 = 5.19685 is explicitly a ratio to the 6.35 mm CAD shaft envelope,
not to delivered bolt diameter. For each receiver the recorded bolt-axis
angle is 90 degrees to the inventory's declared longitudinal grain vector;
the pitch line is 0 or 90 degrees to that vector as reported. These are
orientation facts from proposal/source grain vectors, not loaded-angle,
spacing, end/edge, splitting, tear-out, or group checks. Fresh signed force
directions and finished-edge projections remain absent.

The NDS screens are also properly bounded. The 22.225 mm cleat and 9.525 mm
host thread-bearing limits are one quarter of their respective 88.9 mm and
38.1 mm projected receiver lengths, not assertions about actual thread
occupancy. This matches the full-body-`D` exception in NDS-2024
§12.3.7.2; the report leaves actual `D`/`Dr`, member-specific thread lengths,
and tested/evaluated `Fyb` unresolved. Its cited
[ASTM F1575/F1575M-24](https://store.astm.org/f1575_f1575m-24.html) and
[ASTM F606/F606M-26a](https://store.astm.org/f0606_f0606m-26a.html) routes do
not permit a generic Grade 5 value to be substituted for applicable bolt
evidence. Fresh per-bolt actions and a supported current-joint response are
left for later; no per-seat values are summed and no utilization or criterion
pass is produced.

## Verification and small clarity note

The focused pure test file passes: `6 passed`. Re-reading the frozen manifests
and rebuilding the report through the pure API uses the exact recorded input
hashes; the producer itself writes only when run as a command and was not run
for this review.

No correction blocks use of this preflight. For added precision in any later
reuse, the wood-property label can say explicitly that 625 psi is the
unadjusted normal-duration/dry Table 4A base value. The README already says
that it is conditional and applies no bearing-area increase, and the report
does not present it as adjusted design resistance.
