# Right-corner finished-section validation

This packet records geometry and saved point-action accounting for
`compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`. It establishes no joint capacity,
regional force sharing, section traction field, candidate acceptance or
physical release. The selected baseline and historical evidence remain
unchanged.

## Frozen inputs and coverage

The source plan preserves five finished members, six current right-knee
axes and 14 matched bore memberships. It retains all 338 physical interfaces
(42 internal and 296 boundary), their 392 scalar source rows, 380 in-scope
endpoint actions and 508 physical body-load nodes per state. Opposite-side
and center header ports remain in the complete boundary.

The 888 action points and 14 geometry-only bore centers produce 902 station
identities and 271 grain planes: header 105, right post 21, right side 117,
inner block nine and spine 19. Every source identity survives coincident
plane grouping. Three cases with seven saved increments each produce
18,648 point records and 5,691 state-plane cuts. Floor support remains an
unverified no-slip assumption; selected and released floor channels retain
their provenance, including released zero actions.

The plan closure contains 180 byte-size-hash pins; the full output adds the
action method and its tests for 182 pins. Each pin was independently checked
against the live file. The source boundary replay uses `PYTHONHASHSEED=0` in
its subprocess because the unchanged upstream helper's set iteration can
alter floating-point summation order. Two separate metadata processes
reproduced the exact plan bytes. This changes neither the upstream helper
nor its physical gates.

| Artifact | SHA-256 |
| --- | --- |
| `produce.py` | `1163a16281e4e705217987eacf65b4fa3b09adea9094e01347286d021cc873d0` |
| `plan.py` | `4b3639e132f6038515762ae2edacaacdd0e9efd93385998226efa3eb2e4c87ec` |
| `actions.py` | `951779cd0970b8f15cda6a20ac69d9bca8f299acfaaefc009f6c19c5a3118a40` |
| `test_produce.py` | `66473677f2556ce92e8fe18daadcb3746035b52cf9a74f294112d6ab2c2c6255` |
| `test_plan.py` | `f0079cb2b27090e9dbbb9abd0928f651f7e1e932176cebcdbb50b93bfa2ea64d` |
| `test_actions.py` | `13ff20baffb8cd5416f9f0e66ca7fb59b114b7aa19b6e3496db25934bf88a32a` |
| `source-plan.json` | `6131d10c612aabb34bfcfb1872ccce73a57541dda4ffaa5c0bb9e4efb6e4a0b8` |
| `plan-source-pins.json` | `65d8ae24299f2fd98f4c1c22f8cf4b0449bc7c95e29678a4b39ccb0f983de20d` |
| `sections.json` | `fa7139eaed6aeeedea036717edf5a44ab0a60791eb7d40a342ecb847853b06a0` |
| `source-pins.json` | `ec4938d1055ab9571c00a7ed42d433c922d31f61817bf0de44ba01714d24b901` |

## Bounded geometry extraction

The primary's [reservation](../mvp-integration-2026-10-01/right-corner-cad-reservation.json)
bound the six Python files, exact plan and all 180 input pins. The single
authorized CAD process started at 2026-10-01 19:00:55 UTC and exited zero
after 71.20 seconds. Its wall limit was 300 seconds, address-space limit
4 GiB and peak resident memory 862,356 KiB. BLAS/OpenMP thread counts were
one. No native solver ran and no second CAD launch or retry occurred.

The unchanged frozen kernel returned positive-area properties for 270
planes, including 312 components and 36 planes with disconnected regions.
At `base_side_right:section:7afd1519d76a9d90`, the saved grain station is
approximately zero. The completed bounded BRep common has no faces, edges
or vertices. The output records `EXACT_EMPTY_FINISHED_SECTION`, null
properties, the kernel reason and all eight source body-load identities.
The 21 cuts at this terminal plane remain in the action output. No positive
area, relocated plane, resistance or terminal qualification is inferred.
The report status is `PARTIAL_FINISHED_GEOMETRY_WITH_SOURCE_ACTIONS`.

Before the candidate queries, a 10 by 20 by 30 mm box established four small
known answers: interior and terminal-face sections both have 600 mm² area;
an outside plane and a vertex-tangent plane return empty geometry with null
properties. A read-only Python profile callback observed the frozen
kernel's actual section faces. It integrated their oriented analytic BRep
edges using projected Green integrals and 32-point Gauss quadrature,
independently of the kernel's mass-property method. All 586 calls, including
the known answers, matched area, centroid and central area covariance.
Maximum differences were 3.96e-8 mm², 1.73e-9 mm and 5.76e-5 mm⁴.
These numerical comparisons validate this frozen extraction; their
comparison bounds introduce no physical criterion or accepted capacity.

The profile observer did not replace numerical functions or alter results.
It logged every plane, including empty geometry. The receipt and progress
are local evidence at `/tmp/mini-right-cad-receipt-2026-10-01.json` and
`/tmp/mini-right-cad-progress-2026-10-01.jsonl`, with SHA-256
`603478d126654eea96667fad01ede8b46a6b9277ad27aaafdcb425e73a66872a`
and `ae96faed8e7265c8705c567fd282f264c401ccfc5f68c60fee070c6939f8be51`.
The observer script hash is
`ad71b1fd0ff6ba22660f37cf4ba835de3ed5ebadb64b314e3beab86c3b241d3f`.

## Independent saved-action comparisons

Standalone standard-library oracles imported no packet numerical helpers
and ran no CAD or native solve. They reconstructed physical forces and
radii from the frozen native response components, carrier-law inventory
and physical model loads. This is not an independent reparse of DAT tokens.

The point oracle compared every one of the 18,648 point records, preserving
both endpoints at their own application coordinates and every floor channel.
The maximum force discrepancy was 7.89e-31 N; the maximum radius discrepancy
was 3.77e-37 N. An independent native-node and finished-feature census
matched all 902 point identities, coordinates and grain stations and all
271 coincidence groups.

The full-output oracle recomputed every before-plane, on-plane and
after-plane partition from the raw points and saved frames. It matched all
5,691 cuts' signed global/local forces, moments and propagated absolute
rounding bounds; the reported numerical differences were zero. Separate
parallel-axis aggregation matched the 270 section areas, centroids and
covariances, with maximum covariance discrepancy 7.46e-9 mm⁴.

The contact oracle independently classified native physical-owner endpoint
segments against every plane and checked source row IDs, normals and areas.
All 260 recorded events have both endpoints on their plane; the geometric
event inventory and on-plane source identities matched. None assigns force
or traction to a finished region. The synthetic action tests additionally
exercise crossing and touching endpoint geometry.

Local oracle receipts are `/tmp/mini-right-raw-point-oracle.json`,
`/tmp/mini-right-station-oracle.json`,
`/tmp/mini-right-full-output-oracle.json` and
`/tmp/mini-right-contact-oracle.json`. Their SHA-256 values are respectively
`0ae42f2733d9d4c82a6ccfb5e76f4a204bbd384c1dea6749c6f0ff8aaccac1ab`,
`d0c225166eeb4bdc1cf27d1404cfc6de0dfab2655a7ebcbb1a2153ce4e3dcdbe`,
`3374564a6a0027e2d15858ab64fefdb605a0846cd042095441591a986ecd43b2` and
`830e2fe6d981b5c9bfe69a5da391b54562af048c9dca2e13003be85d5eddb32b`.
Their corresponding `.py` files are available beside those receipts.

## Tests and review

All 13 packet tests passed locally and in a clean temporary checkout
containing only the six Python files, without generated JSON, STEP,
CadQuery imports or repository `conftest.py`. Ruff checking and formatting
passed. The primary independently reproduced the metadata plan, verified
all 180 plan pins and ran the source-only plan/producer subset of ten tests.
The independent testing reviewer reran all 13 packet tests and Ruff.

One disjoint independent Luna/max review pass completed. Correctness and
testing reviewers report no substantial findings. Architecture identified
the absence of a separate dependency-lock/Python environment pin. Reviewers
received the raw task, final code, validation scope and claim boundary
without peer findings or this review record.

The frozen section kernel already records CadQuery `2.8.0` and OCP
`7.9.3.1.1` in every positive-area property record; all 270 current records
agree. Full `--verify` compares those fields with all other canonical output
bytes, so changed reported CAD versions cannot silently verify this packet.
The post-run interpreter observation was CPython `3.12.3` with NumPy
`2.5.2`; NumPy was used by the independent Green-integral observer. The
observed `uv.lock` SHA-256 is
`5ea7a77ddb3072bfe1c2ba131e34b293a0103f931eb9b911e9eb248ccb6d84d3`.
The lock and interpreter observation are recorded here, not retroactively
presented as pre-run source pins.

A separate pre-CAD lock/Python environment guard is explicitly deferred.
The current run has recorded CAD versions, direct known answers and
independent comparisons against its actual section faces; no current
numeric discrepancy was found. Adding that guard would change the frozen
producer and its source/output hashes, outside the primary's single-run
reservation. A future replay under a different environment must preserve
the exact-output verification contract and obtain its own primary-owned
reservation. No issue or Git operation was created by this secondary.

A second full CAD `--verify` replay was not run: the primary authorized one
bounded extraction and prohibited another CAD launch. Exact metadata replay,
live pin verification, small geometry known answers and the independent
edge/point/cut/contact comparisons are the completed verification scope.
The primary retains final integration and Git ownership. This record does
not close the terminal section's missing positive-area qualification.
