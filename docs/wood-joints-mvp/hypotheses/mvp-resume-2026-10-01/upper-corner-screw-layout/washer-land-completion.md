# Complete the 20 missing nominal washer-land bindings

Status: **parent attempt01 completed all 120 generic-annulus probes; this
owner authenticated and annotated the result without another geometry run**.
The [runner](washer-land-completion.py) consumes the completed
[washer-end source continuation](washer-end-source-completion.md), imports
four effective STEP solids once, and runs only its 120 requested inward and
outward annular probes. It rebuilds no scene or frame and changes no mechanics,
hardware, source loads, authority or release flags.

## Completed parent attempt01

The result is `COMPLETE_120_PROBES_WITH_OPEN_NOMINAL_LANDS`: all **120 reports
are finite**, **12 of 20 seats** have full support under their preserved
source tolerances, and eight do not. The child elapsed time was **3.623 s**
within its 120-second allowance. Independent read-only authentication checked
all **234 source pins and eight output artifacts**, with identical before/after
source hashes. The producer remains frozen at
`e6e42f901d08042c1c3ef1045af9b3f3cf0aea65bb1bcf8b051978bdc18ba0aa`.

| Attempt01 artifact | SHA-256 |
| --- | --- |
| `receipt.json` | `7d541cef4b05b03a6d501243759dd1ea435eeb42be4ce2d71eda27cd9ea78679` |
| `washer-land-completion.json` | `a7c2b3349d81f0b064aa29a2c772bbbf04602ec722b9a7c713c2dc30bdfb7e7e` |
| `probe-progress.jsonl` | `902f269ba7094fbdc311d3010d441b7dc2bc3340219de4307f8e70ede96bc737` |
| `worker-result.json` | `533bf5f2902339e4ca1493fe98b481d1252a1819bc0b87631371b8aa7631bbad` |

The 12 full generic lands are the four bottom-side heads, four left service
upper/lower side heads and four right wj06 upper/lower side heads. Each has
minimum inward fraction 1.0 and maximum outward overlap 0.0. The known central
partial land and four corrected retail lands were reused rather than queried.

### Eight non-full generic rings

Each of the following has all six numeric probes, a matching planar datum,
unit normal alignment, and **zero outward overlap at every depth**. The only
screen reason is inward clipping of the generic minimum-area ring. The
preserved upper-source fraction tolerance is 1e-8. Plane offsets are at most
4.55e-13 mm, so the approximately 4.42% area difference is not a tiny surface
kernel error.

| Exact axis | End and receiver | Minimum inward fraction | Maximum outward overlap |
| --- | --- | ---: | ---: |
| `top_outer/clip_single_top_left_1/side_1` | head, `base_side_left` | 0.955831947100743 | 0.0 |
| `top_outer/clip_single_top_left_1/side_1` | nut, `top_outer_left_cleat` | 0.9558319471061337 | 0.0 |
| `top_outer/clip_single_top_left_1/side_2` | head, `base_side_left` | 0.9558319471007433 | 0.0 |
| `top_outer/clip_single_top_left_1/side_2` | nut, `top_outer_left_cleat` | 0.9558319471061338 | 0.0 |
| `top_outer/clip_single_top_right_2/side_1` | head, `base_side_right` | 0.9558319471061608 | 0.0 |
| `top_outer/clip_single_top_right_2/side_1` | nut, `top_outer_right_cleat` | 0.9558319470962028 | 0.0 |
| `top_outer/clip_single_top_right_2/side_2` | head, `base_side_right` | 0.9558319471061605 | 0.0 |
| `top_outer/clip_single_top_right_2/side_2` | nut, `top_outer_right_cleat` | 0.9558319470962028 | 0.0 |

The three inward depths differ only in small numerical tails. The corrected
side bores have radius 4.5 mm, while this deliberately generic probe has inner
radius 4.1529 mm and outer radius 9.2329 mm. Removing that inner strip predicts
`(9.2329^2 - 4.5^2)/(9.2329^2 - 4.1529^2)`, matching the measured fraction.
This establishes an applicability problem for that generic ring; it is not a
washer operation, load-transfer or physical strength failure.

**The current top-side hardware is a different family.** The pinned fresh
corner replay's `hosts.base_side_left/right.geometry` declares a 7.9375 mm
(5/16-inch) bolt, 9.0 mm bore, washer ID 9.906 mm, OD 22.0472 mm and
hypothetical flat radius 6 mm. Thus its washer inner radius is **4.953 mm**,
already outside the 4.5 mm bore. The generic 4.42% loss must not be reported
as a loss of actual top-side washer support. Its larger actual outer radius,
11.0236 mm, still requires a matching current support proof; the generic
probe's 9.2329 mm outer radius does not certify the extra outer band. The
quarter-inch retail plate comparisons are another distinct route.

### Source overlay and current face bounds

The eight queried points lie on the current outer X planes below. The side
head faces are face 0 on the left and face 18 on the right; the cleat nut
faces are face 7 on the left and face 0 on the right. Recorded planar face
areas are 348758.912665 mm² for either side and 16594.855498 mm² for either
cleat. The following are **whole-body STEP readback bounds**, not a polygon
or a contact mask for the whole planar face.

| Member | Queried outer X plane, mm | Body X bounds, mm | Body Y bounds, mm | Body Z bounds, mm |
| --- | ---: | --- | --- | --- |
| `base_side_left` | -1219.2 | -1219.2 to -1130.3 | -175.7 to 1535.584507 | 277.0 to 2246.290376 |
| `base_side_right` | 1216.025 | 1127.125 to 1216.025 | -175.7 to 1535.584507 | 277.0 to 2246.290376 |
| `top_outer_left_cleat` | -1041.4 | -1130.3 to -1041.4 | 1314.280462 to 1495.773411 | 2033.145997 to 2217.104083 |
| `top_outer_right_cleat` | 1038.225 | 1038.225 to 1127.125 | 1314.280462 to 1495.773411 | 2033.145997 to 2217.104083 |

The corrected cleat section source
`rawlocal/corner-timber-sections/attempt02/checks.json`, SHA
`8b954edf5743999f427d2b99fcaaf9288578f02dc59a5cf1e632da634aa2e813`,
records the two 4.5 mm side-bore radii in each `/geometry/{left,right}/bores`
array and binds the same corrected cleat STEP hashes. The current force/seat
overlay is `rawlocal/knee-bridge-corner-replay/attempt01/checks.json`, SHA
`e699b5c662992abab1f646236cdd4037feb425c5476458d8629899bcb9948976`:
left `/states/0/hosts/base_side_left/wood_seat_recovery`, right
`/states/1/hosts/base_side_right/wood_seat_recovery`. All frozen inputs and
all generic probe results remain unchanged. A separate matched-family leaf
will use those 48 own-end states and eight actual-profile support contracts.

## Completed source input

The parent completed `rawlocal/washer-end-source-completion/attempt02/` with
status `FINITE_PARTIAL_END_SOURCE_COMPLETION`. It contains 48 recovered common
knee ends replacing the isolated demands, and 1,008 ordinary moment gaps
explicitly pending the full N10 source. That continuation did not run a plate
or shaft solver. The first attempt's `host_nut` mapping stop is preserved;
the successful source accepts all four physical host/cleat head/nut labels.

| Input | SHA-256 |
| --- | --- |
| Source `receipt.json` | `d974544f39a670bde1d9a493754224b199fe10f5126fc266f9914101d5fcbe00` |
| `land-query-plan.json` | `a5bf7a49515766ed02b46af817e1795ef18e8ab259acdde83dee5185d5cd9c92` |
| Consumed source producer | `dbf242d54ae501c0bf8d4241447837dcf08e7e4d2d108703f43a2fc0e1c078c9` |

The runner authenticates all 222 inherited source bindings, the input packet's
output artifacts, and its own method/runtime source pins. It requires the
exact query plan, physical keys, current datums, four effective member bindings,
minimum-area annulus, three depths and both directions. N10 is not required
for these geometry queries; no duplicate global or local solve follows.

The completed common source's maximum recovered own-end M is 1,179.093383
N mm at `k12-right`, `knee_outer_right_side_2`, head on the right spine, with
same-state T 316.672080 N. Its rigid-law continuous wood-pressure/reference
index is 0.818797. The maximum recovered eccentricity is a different state:
`a12-left`, right side_1 head, M 176.494236 N mm and T 36.679093 N, or
4.811848 mm. These are saved conditional source quantities, not metal
resistance or a combined peak load state.

## Parent command and API

From the repository root, the parent may run:

```sh
uv run --no-sync python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/washer-land-completion.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/washer-land-completion/attempt01
```

The inert module also exposes `build(output)`. Use a fresh immediate child of
`rawlocal/washer-land-completion/`. The parent wrapper starts one child with
the existing `.venv/bin/python`; a fixed **120-second subprocess timeout**
covers its CAD imports, four STEP readbacks and all Boolean probes. Source
authentication and receipt writing occur outside that child allowance.
The completed attempt's actual child runtime is recorded above; the same
fixed timeout applies to another explicitly authorized invocation.

On timeout, the wrapper terminates the child, preserves logs and completed
probe records, and reports `STOP_GEOMETRY_TIMEOUT`. Incomplete JSON from a
terminated write remains recoverable and cannot produce a completion claim.
Other setup/query stops retain partial output. There are no retries, alternate
depths, expanded annuli or model sweeps.

Output includes `washer-land-completion.json`, `probe-progress.jsonl`,
`worker-input.json`, optional `worker-result.json`, stdout/stderr logs,
producer snapshot and receipt. Before/after source hashes accompany complete
and stopped results. The CLI exits zero only when all 120 probes returned
numeric records under unchanged source bindings. This may still report open
nominal lands; completing a geometry query is not passing its screen.

## Existing geometry method

The method is CadQuery/OCP, not FreeCAD. Reuse the pinned
[support helper](../../corner-washer-support-2026-10-01/check_support.py)'s
`hardware_for()` and `matching_seat_planes()`, plus its imported
`WasherSeat` and `washer_support_report()` from
[wood_joint_geometry.py](../../../../../mini_moonboard/wood_joint_geometry.py).
The same callable underlies the existing upper and remaining-seat packets.

The runner requires CadQuery **2.8.0** and OCP **7.9.3.1**, as recorded by the
existing seat evidence. Each cached STEP must contain one valid solid with
positive volume. The output records its face count, volume, surface area and
bounding box. Its byte hash must match the query plan before import and after
execution; no STEP conversion, new machining or scene reconstruction occurs.

For each seat, the method makes an annular cylinder from the nominal seat
along the given inward normal for depth d, subtracts its inner cylinder and
intersects the result with the saved effective wood solid. The reverse normal
provides the outward probe. **This is an annular slab, not a zero-thickness
section at depth d.** The plan's signed offset is interpreted as the slab's
end extent, preserving the old method. It is not applied as another shift of
the seat followed by a second probe depth.

The analytic ring area is `pi * (9.2329^2 - 4.1529^2)`, or approximately
213.627873 mm². The existing helper returns the BREP volume fraction. The
runner reports mean supported area as that fraction times analytic area, and
a derived equivalent overlap volume as fraction times analytic area times
depth. The latter is not a separately returned raw Boolean volume. It does
not turn a slab mean into a local contact pressure or actual washer capacity.

### Support and outward observations stay separate

- Probe depths are 0.01, 0.05 and 0.1 mm, in both directions: 60 inward and
  60 outward reports across 20 seats.
- The planar datum helper uses 1e-5 mm plane tolerance and normal absolute
  alignment at least `1 - 1e-8`.
- Inward support must be full and outward overlap must be clear. Outward wood
  is not credited as washer support; it can indicate an embedded or reversed
  datum.
- Upper-source seats retain fraction tolerance 1e-8; remaining-source seats
  retain 1e-7. The runner does not silently loosen either source's rule.
- A nominal full-ring result requires a matching planar datum, all six finite
  reports, minimum inward fraction at least `1 - tolerance`, and maximum
  outward fraction at most `tolerance`. Clipping, outward overlap or missing
  datum remains an explicit geometry result, not a physical failure claim.

Loaded movement, tilt, actual timber, installed holes and delivered washer
profiles remain unqualified. The eight service/wj06 heads use the current
registered head datum; the corner seats use current own-seat recovery rather
than stale upper-source coordinates.

## Frozen effective STEP solids

All paths below are relative to `mvp-resume-2026-10-01/`.

| Member | Effective STEP and SHA-256 |
| --- | --- |
| `base_side_left` | `top-corner-correction/base_side_left.step`; `bf1b7398f4c177831d9792f7efcbe07ba8145ab1045bcef1611c2e44b19b3713` |
| `base_side_right` | `top-corner-correction/base_side_right.step`; `6b79617b36f44fc6750b334556779a01191802f8b67b2a3e46c69a6c42bc9601` |
| `top_outer_left_cleat` | `top-corner-correction/top_outer_left_cleat.step`; `7955c0ff9f0b23483b0607f6357c7825904bf2a9d949b7aba8876b3a96516d1d` |
| `top_outer_right_cleat` | `top-corner-correction/top_outer_right_cleat.step`; `fe199dcce78d43140ef5299d82d0b888631905bd8686537d98a0997163e45b79` |

| Reused method/runtime source | SHA-256 |
| --- | --- |
| Corner support helper | `9b3b773c2f7f1a51d5b5f9902ff288644133f67f63575a7c3a37168028e0dc57` |
| Shared wood-joint geometry | `e437385d4894c7bcd4bbf4ee66aa9f96a53a8d3570efc6230fb225570abbb90e` |
| CAD hardware dimensions source | `77b4a8b28b02088878f1f0e0483610a7918cb85f5694f0551f50cf8888886545` |
| Connection geometry source | `f729bc64e7ea7fb9df9308411df07e02f98fc309efcf26038809a9e7bd4bc4a4` |
| `uv.lock` | `5ea7a77ddb3072bfe1c2ba131e34b293a0103f931eb9b911e9eb248ccb6d84d3` |
| `pyproject.toml` | `84e007ad5c9cfffa853f21627fecbaec0a85c602560d5d5e0b507326e9b02452` |

The source receipt retains all current point/normal source bindings and the
full common-knee/global response closure. Original support forces and old
seat coordinates are not used as new demand or geometry authority.

## Reused lands and next finite decision

The known central partial full-ring failure is carried unchanged with its
separate supported-ring contract. The four corrected retail rail-cleat lands
are carried unchanged with their existing nominal annulus evidence. Neither
route is queried again. The original N09 183/25 aggregate remains frozen.

The result decides which of the 20 remaining physical ends can use a bound
current nominal annulus in later demand comparisons. It supplies no steel or
wood resistance. Once the complete own-end T/M export arrives, the next small
steel screen should group only matching washer profiles and reuse existing
plate methods or authenticated family envelopes. Separate high-force/moment
and high-eccentricity witnesses are useful candidates; two sample results
alone do not qualify an entire nonlinear family. No wider retail washer pass
is transferred to a smaller washer, and no new 3D washer model is introduced.

This owner performed source preparation, static AST/Ruff checks and read-only
authentication/annotation of the parent's completed result.
There were no geometry queries, mechanics/native solves, software tests,
review loops, staging or commits. Source and failed raw evidence stay in
place. All 47-criterion authority and joint/release HOLD boundaries remain.
