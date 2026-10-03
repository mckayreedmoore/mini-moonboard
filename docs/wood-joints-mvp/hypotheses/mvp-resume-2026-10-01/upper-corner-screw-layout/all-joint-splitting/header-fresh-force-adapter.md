# Fresh header cleat force adapter

`header-fresh-force-adapter.py` creates a new six-case source package for the
six header-related cleats. It restores point actions from the fresh member
arrays, maps the header washer, contact and lateral bore actions with the
finished geometry and existing field methods, then integrates the mapped
fields at new v stations derived from the fresh actions and field geometry.
Fresh gravity and live-load point actions remain at their saved application
points. The producer does not call either frozen 104-axis header `build()` or
`source_context()` API.

## Authority and load basis

The reviewed 104-axis geometry remains the current reviewed development
authority. The new source is the fresh global connector response with 104 axes
and the updated planning
gravity operators whose modeled mass reflects the unadopted 108-inventory
proposal. That is not a fully coupled 108-axis response. Four proposed internal
V ties have no global connector rows; their force, couple and tie duties remain
unrecovered and unqualified. The adapter assigns no forces to those ties and
does not transfer any prior 104-axis action, mass, wrench, cut or demand result.

The old header transfer `model.json` is read for static interface and finished
surface geometry only. Each of the six cleat STEP hashes and the header-host
STEP hash must agree with the fresh member geometry. The old transfer
`inputs.json`, old force archives, old gravity, and old cut files are not read.
The README pin is authority context only.

## Producer API and output

The parent's first actual run, `attempt01`, stopped before engineering
arithmetic. Producer `f4974cf08ba82ca5296726208bdc1945ccf2f0cd9a92c2a0b62ffc0371d2d6f0`
passed the orientation-helper module where `floor_direction_metadata` expects
a source-reader API, causing an `AttributeError` at its `api.read` call. That
attempt and producer snapshot remain preserved. The revised caller supplies
only the required standard-library reader and authenticated gravity directory
through `SimpleNamespace(read=read, GRAVITY=GRAVITY)`. No original helper,
orientation contract, row sign, source force, geometry or accounting guard
changes. The parent then completed the new `attempt02` run described below.

`build(output)` accepts a new immediate child of
`all-joint-splitting/rawlocal/header-fresh-force-adapter/`. The command-line
entry point is:

```sh
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/header-fresh-force-adapter.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/all-joint-splitting/rawlocal/header-fresh-force-adapter/attempt02
```

The run writes `checks.json`, `sources.json`, compressed source/action and v-cut
worksheets, a producer snapshot, and a receipt binding every output and input.
It covers six cleats × six cases. Each worksheet retains source forces and free
couples, reports the full signed six-component source and mapped cut wrench,
and includes a material normal-hull diagnostic only. Pressure/tie capacity,
complete-body boundary recovery, splitting qualification, proposal adoption,
and physical release remain false.

Unsupported washer, contact or bore fields stay explicit in
`unsupported_physical_rows`; `action_recovery` retains their source force and
free couple at their original points. It also retains roundoff residuals for
mapped rows at those original points. `action_recovery` checks each complete
source six-wrench against its mapped field plus point residual; aggregate
header-interface and whole-body six-wrenches retain their accounting checks.
At each partial v cut, output keeps both signed source and mapped six-wrenches
plus mapped-minus-source delta. That delta is a load-distribution diagnostic,
not a per-cut equality requirement. The field can redistribute load across a
section while preserving complete action/interface/body wrench. No continuous
station maximum is claimed, and no separate coupon was run for this adapter.

## Row-orientation scope

The producer pins `member-opening-remainder.py` (`5db858b3…`), its original
projection contract (`4ceca771…`) and the compliance inputs binding that
contract (`3d17f953…`). The resolver records `owner_point_rigid_row_sign=-1`
for all 200 conditional floor-tangent rows. A saved-row census shows zero of
those rows incident on any of the six header cleats; each target has 20
incident mechanical rows from the two other row families. The producer also
checks each returned action row against this family before field mapping.
Therefore it passes saved row identities unchanged into the existing
`actions_for` sign and full-wrench guards; it does not adapt or guess signs.
`checks.json` records source hashes, exact row IDs and family counts. This is
schema evidence, not a force or qualification result.

## Pinned inputs and methods

The producer pins the fresh member extraction (`5178d1a2…` results,
`3be03247…` action arrays, `c6113908…` geometry and `34219c91…` inputs), the
fresh gravity assessment (`ce69ba58…`), the fresh frame comparison
(`c3a8ff02…`) and response (`62bd4116…`), plus their receipts. It also binds
the static header geometry contract and the precise helper implementations
used for fresh action restoration, washer/contact/bore mapping, v-cut
integration, and the normal-hull diagnostic. `checks.json` records the complete
SHA-256 map.

The reused functions are `knee-bridge-remaining-sections.actions_for`,
`header-boundary.map_axial_seat`, `map_contact_cell` and `map_lateral_bore`,
and the finite field and action recovery methods in `header-v-cuts.py`. The
normal-hull helper reports a normal-resultant diagnostic; both shear
components and torque remain in the signed wrench and receive no capacity check.

## Completed fresh run

The parent executed `rawlocal/header-fresh-force-adapter/attempt02/` with
producer SHA-256
`0853f56924d8229272efd679eaadad8de5cffbad28791a93a9a60f6e601a2f47`.
The run completed 36 cleat/case states, 360 header boundary-action records
and 1,368 finite `v` cut limits, with zero unsupported physical rows. Of the
360 records, 359 have mapped fields with explicit source residuals and one
has zero source force and needs no pressure field. All 36 states passed the
retained source-action, integrated header-interface and whole-body accounting
checks. Other interfaces remain source point actions; this accounting pass
does not establish a complete physical body boundary.

Read-only authentication found all 35 source hashes and all six output hashes
consistent with the receipt. This document is not a consumed source in that
receipt; the numerical producer and saved output bytes remain unchanged.

The saved mapped normal-hull diagnostics have 1,360 positive normal bounds
and eight compression-only feasible results. Aggregating those saved records
gives the following per-body maxima. These are finite-catalog minimum tensile
resultant diagnostics, not screw loads, timber failure loads, reinforcement
capacities or complete-joint utilization ratios.

| Cleat | Case | Local `v`, mm | Limit | Normal-resultant diagnostic, N |
| --- | --- | ---: | --- | ---: |
| Center-post left | `a12-forward` | 0 | before | 1.36638 |
| Center-post right | `a12-forward` | approximately 0 | after | 1.46961 |
| Center-principal left | `a12-left` | 30.85 | before | 25.13843 |
| Center-principal right | `k12-right` | 30.85 | before | 28.47368 |
| Inner knee left | `a12-forward` | 2.796913 | after | 55.60809 |
| Inner knee right | `a12-forward` | 2.796913 | after | 48.98174 |

Positive bounds do not establish hardware failure or prescribe a geometry
change. All resistance, splitting qualification, complete-joint acceptance,
proposal-adoption and release flags remain false. No new coupon, native solve
or engineering producer was executed during this read-only results summary.

| Saved artifact | SHA-256 |
| --- | --- |
| `checks.json` | `94e8f4c698772530ac25df0bc5f91715db64078bba1c27fc26b42545d86680b6` |
| `receipt.json` | `5294be28ae9854dc5b90641c8223a64d7fca817d1494d90965f2c6d3173be738` |
| `fresh-header-actions.jsonl.gz` | `09293d656b0a3b49c2fe770a1b5962371c01f5ca793552edda4beed7d4d1c59b` |
| `fresh-v-cuts.jsonl.gz` | `73622836ad2e114ca579bc8df1cf131f5b31502d787d4cadc04ea60301ff8d19` |

## Limits

- Uniform annular washer pressure, clipped-cell frictionless pressure and
  half-cosine radial bore pressure remain placement assumptions. The run does
  not solve contact compatibility or peak pressure.
- Other cleat interfaces and discrete fresh body-load actions remain at their
  exact source points, so these records do not recover a complete physical
  body boundary.
- New v stations are finite event stations from fresh source action positions,
  field-domain transitions and current finished geometry. They are not a
  continuous-station envelope.
- The four internal V ties remain outside the 104-row global connector model.
  Their separate planning mass affects the fresh gravity basis; no tie force or
  resistance is inferred.
- No strength value, splitting capacity, new resistance, qualification,
  acceptance, fabrication release or physical release is established.
