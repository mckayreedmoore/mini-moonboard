# Current full-frame conditional material crosswalk — attempt01

## Result

This append-only source crosswalk joins attempt04's exact 50-body finished-STEP
inventory to the existing body-level conditional orientation maps. It covers
20 frame timbers and 24 connector blocks. Each of those 44 wood bodies has two
right-handed transverse ring-orientation scenarios, for 88 conditional cases
in total. The six plywood panel rows retain their exact STEP identities and
leave product, layup, axes, elastic properties, density, and solver material
IDs unresolved.

The wood rows reference the existing Douglas-fir orthotropic diagnostic
elastic scenario. Its values are conditional inputs combining the DF-L No. 2
longitudinal modulus with Douglas-fir clear-wood elastic ratios; they are not
measurements or delivered-stock properties. Growth-ring orientation remains
unknown per board. Density is null for every body. The separate dead-load
contract carries mass accounting and accessory scenarios; it does not supply
a per-body density-to-mesh assignment.

The map binds each row to `member_id`, finished STEP path and SHA-256, shape
summary hash, and source-shape fingerprint. The producer checks the 20 timber
orientation records against their separate 20-row transverse-case map; the
24 block rows retain the block map's two cases. Every row also reconciles with
attempt03 coverage on exact body ID and STEP path/hash.

## Remaining limits

This is a partial pre-mesh source/model-input improvement. The six panel
layups, density values, steel body or role assignments, physical fastener
products, solver material/body/element/node/DOF IDs, mass/load mapping,
connection laws, and complete mechanics model remain unresolved. Attempt04's
`inputs_ready`, `per_member_material_mapping_ready`,
`six_plywood_panel_layups_assigned`, `solver_body_element_dof_material_mapping_complete`,
and `native_solve_executed` flags remain false. No readiness or release flag is
advanced here.

The producer does not rebuild geometry, make a mesh, write solver input, or
invoke a solver. The crosswalk does not identify delivered timber species,
grade, moisture, treatment, receiving condition, measured elastic properties,
density, or actual ring orientation. It establishes no material acceptance,
connection behavior, demands, capacity, candidate acceptance, fabrication
release, or climbing release. Independent review is pending.

## Verification

From the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-conditional-material-crosswalk-attempt01/produce.py --verify
```

Verification is read-only. It checks source pins, attempt04-pinned map hashes,
all 50 exact STEP files, exact body joins, 88 two-case wood orientations,
right-handed frames, unresolved fields, and the crosswalk record digest.
