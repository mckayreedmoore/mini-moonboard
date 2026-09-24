# WJ-04 upper-pair probe

Status: historical, unaccepted paired-geometry hypothesis. It does not change
the active candidate, canonical WJ-04 configuration, or manifest. The report
records zero accepted replacement duties and grants no purchase, drilling,
fabrication, or structural release.

## Reproduction and source pins

Run from the repository root:

```sh
uv run python -m scripts.wood_joint_wj04_upper_pair_probe > /tmp/wj04-upper-pair-probe.json
```

The archived JSON is the byte-for-byte copy of the preserved report
(`/tmp/wj04-upper-pair-probe.json`), SHA-256
`2df952ff8b01a9b56b1c445d54d5aea8ea7b94b75b818bcc002a1719168b9d9f`.
Its recorded producer hash is `7e042ed35b6670191e2549f4f4922af4643db8d6552fef09b6998546ae123860`,
matching both the unchanged repository script and the frozen script copy. The
unchanged test hash is
`e31e407c0711cb24211529499a402ec49441e362b8a92dfabfb1cf36249ff341`, matching
the frozen test copy.

This local materialization was bound to candidate `compact-floor-flush-development`,
variant `kerf-right`, canonical WJ-04 config SHA-256
`d1c63e1fa5617999e8af68d683cc0f3074fb84f518b048a087ec5ed276206c0e`, and source
inventory SHA-256
`07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78`. The
recorded fixed screw-axis SHA-256 is
`22224a0afc78500cb0f832f3b6c6ea4e0d1dd934813c8570d637c16cb052a4f1`; starting
frame bolt axes: `524792bb6fe1f966a7725aad7a7ed4290c355bebafcc27d84f9a5e2690ad3e27`;
uncut part shapes: `627cead591c1f0f4e63ede07a871659fba7c1b56a8e468791e5dd8f6d9845f2c`.
The JSON records hashes for the five uncut host shapes, three runtime modules,
and all 18 declared source inputs. The producer snapshots those input hashes
before and after report generation and stops if they differ. The local
materialization preserved all 66 panel/kicker screw axes and all 12 starting
frame bolts. These are provenance and preservation checks, not acceptance.

## Findings and limits

- The two cleats have a nominal 55.15 mm gap and no reported pairwise
  intersection. The upper cleat nevertheless intersects the protected
  `hold_tnut_main_G7` envelope by 562.789149 mm³.
- All eight modeled bores pass through their two intended timber layers, with
  1.0 material fraction in each layer and no reported unintended wood, panel,
  or protected-geometry bore hits. This does not clear the assembled stacks:
  corresponding lower/upper rail shafts overlap by 264.437966 mm³, with
  131.116894 mm³ head-to-opposing-shaft clashes. The assembly-order screen
  found no clear order.
- The modeled bolt SKU `25C600HCS5Z` and 127.0 mm grip are provisional.
  Catalog gaging bounds do not establish full thread at the nut; delivered
  thread transition and functional nut engagement remain unresolved.
- The envelope checks do not establish physical tool access or prove actual
  tool impossibility. The report is not a complete layout or load path and
  leaves signed member loads, member-specific checks, material condition, and
  delivered hardware unresolved.

The report's claim boundary remains zero accepted replacements, with capacity,
structural acceptance, purchase approval, drilling release, and fabrication
release all false. Treat it only as a preserved diagnostic hypothesis.
