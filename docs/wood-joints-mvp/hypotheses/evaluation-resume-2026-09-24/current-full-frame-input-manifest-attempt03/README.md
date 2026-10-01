# Current full-frame input manifest — attempt03

## Decision and result

This source-only refresh preserves attempt02 and binds the later exact 50-member
STEP bundle, current conditional wood-orientation screens, body-gravity and
accessory scenarios, six applied load cases, and the explicit CalculiX 2.23
development profile. It supersedes attempt02's geometry-availability status
only. Candidate identity remains `compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`, reviewed checkpoint
`b1e8707d`; selected authority remains
`compact-floor-flush-development`.

Attempt03 verifies 50 individual one-solid STEP files: 20
timbers, 6 panels, and 24 candidate
blocks. Each file's hash and byte size match the source bundle; the source
export records a valid round-trip for every member. The bundle SHA-256 is
`d9d8feefea4df6ad2895a25292e164851c4d776ae6606c12956b639fb161e3fc` and its STEP-set
SHA-256 is `590e3d8ffc6a013ad10436def028b54b3c855688398c4bf9b30c460800fc987c`.

The frame map covers 20 timber orientation proposals, the block map covers 24
conditional transverse cases, the gravity contract covers 778 modeled mass
rows plus a separate 25 kg accessory allowance, and the current load contract
contains six applied wrench cases. These are geometry, orientation, mass/load
inputs only. `inputs_ready=false`; no current-frame finite-element model,
mechanical transfer model, reactions, demands, or criteria results are supplied.
All acceptance and release flags remain false.

## Bound input records

The JSON carries relative paths and file hashes for all source records and 50
individual STEP files. Core artifact content digests are:

- attempt02 snapshot
  Digest: `1ad6b404c8658147e9d10f54daf4ebd393116c1934654f5521421dc96667e0a0`
- 50-member STEP bundle
  Digest: `d9d8feefea4df6ad2895a25292e164851c4d776ae6606c12956b639fb161e3fc`
- frame timber orientation map
  Digest: `69a99e91583a4a2e9064edf24335a921cc48395ba3699fd96bec1a2272a30bb5`
- candidate block orientation map
  Digest: `4d62c18e9717dfb21b2ff00e36668db7393c3bc83016053903bb962a24c18b70`
- dead-load scenario contract
  Digest: `6161d0ed6c71013840856411ce7c5a890962410f9b7a6e1aaf536e2dfd43ba10`
- six-case current load contract
  Digest: `19fe8aa9b370f2f82758610b8e0231bf0d3972036cf849ef2ffea16e5bf05776`
- CalculiX development profile
  Digest: `f233cb12fe58983e968600befe78cc5ee0785903d60541a6269fe45e8489689c`
- source mass-centroid table
  Digest: `4c107b76d42d2a6f49b81c4857ba20bb236920932a7c34392c63e70d0882099a`
- source-to-mass topology
  Digest: `308a329a0b40db454d5b0e27c9ec2eca92d66eec96bfb222df5f7b7185bef4d4`

The inherited `source_artifacts` list preserves attempt02's source snapshot.
Its execution-plan row is historical and does not pin the current plan; the
current Step 4 input records are the `evidence_bindings` listed above.

## Remaining solver inputs

- The 50 finished STEP solids are source-replayed and round-trip checked, but no solver mesh,
  element/node map, or current-frame finite-element model is supplied.
- The 20 timber and 24 connector-block maps supply conditional orientation scenarios only;
  delivered species group, grade, moisture, treatment, connection-zone condition, and design
  properties are unobserved. Six plywood panels lack a complete layup, axis, and property map.
- No physical bolt, nut, washer, or T-nut product is selected and fit-qualified for the 92
  candidate or 12 retained stacks. The catalog screen fit-qualifies 0 of 92 candidate axes; thread
  start/runout, matched engagement, delivery tolerances, and receiving are unresolved.
- The 66 Hillman screw axes remain geometric/mass proxies; actual product conformance, embedment,
  panel/frame transfer, and resistance are not established.
- The 50-member contact graph and operation registers are geometry-only. Bolt/bore transfer, wood
  bearing/slip/opening, axial engagement, screw attachment, panel transfer, and all 24 replacement
  duties lack a demonstrated mechanical model.
- The 778-row body-gravity inventory and separate 25 kg accessory allowance are source-bound
  scenarios; no mass-to-mesh/carrier DOF map or solver load mapping exists.
- No full-frame boundary-condition/contact model is defined. The no-slip floor support remains an
  unverified analytical assumption with no qualified floor or anchorage.
- The six current cases are applied force/wrench inputs only. They provide no frame reactions,
  connection demands, load sharing, or stability results.
- Source-bound simultaneous six-component local rail/principal-port histories and a time basis for
  a physical ordinary-joint transient remain absent. The analyst-selected 1 N pulse cannot be
  transferred to a physical history.

## Reproduction

Run from this attempt directory:

```sh
python3 produce.py --verify
```

The producer checks attempt02's frozen content digest, current candidate and
revision identity, all 50 STEP hashes/sizes and member IDs, the two orientation
map coverages, 778 mass rows, six current cases, and the pinned 2.23 profile.
It does not rebuild CAD or run a solver.

Manifest SHA-256: `b0c52399de301632b587bbf336e844789e4864dd57ad7f08ea299164a0fa392c`.
