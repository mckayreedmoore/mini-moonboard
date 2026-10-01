# Current full-frame input manifest — attempt04

## Result and lineage

Attempt04 preserves the complete attempt03 geometry, source-member identity,
STEP, 778-row mass, six-case load, and solver-profile records. It adds a
source-reviewed transverse-scenario map for the 20 frame timbers and a
conditional elastic role map for the 92 candidate bolt axes. The existing
24-block orientation map remains bound. Attempt03 is pinned as the immutable
baseline; its files are not regenerated or edited here.

The geometry inventory remains 50
one-solid STEP files: 20 timbers, 6
panels, and 24 candidate blocks. Its STEP bundle
digest remains
`d9d8feefea4df6ad2895a25292e164851c4d776ae6606c12956b639fb161e3fc`.
The current mass-source map still contains
778
mass rows, with the separate 25 kg accessory allowance. Six applied force/wrench
case inputs remain `a12-rear, a12-forward, a12-left, k12-right, k12-rear, a1-rear`; they provide
no reactions or joint demands.

## Added and reaffirmed conditional evidence

| Inventory | Bound evidence | Still unresolved |
| --- | --- | --- |
| 20 frame timbers | 40 transverse alternatives, two per member | No received ring orientation, wood property assignment, solver orientation card, or element assignment |
| 24 connector blocks | Existing 48 conditional transverse cases | No received ring orientation or wood property assignment |
| 92 candidate bolt axes | 460 component roles and nine generic elastic scenarios | No delivered product, grade, solver body/element/DOF mapping, or material cards |
| 6 plywood panels | Source geometry is preserved | Layups, material axes, and properties remain unassigned |
| 12 retained frame-bolt axes | 60 role rows separately inventoried | Remain unassigned by default; current-candidate recheck remains required |

The steel reference scenario is `steel_elastic_diagnostic_baseline_2026-09-24`.
Its E/nu family is a conditional model input; the head and shaft roles share
candidate bolt identity while remaining separate mass/component rows. It does
not identify delivered alloy, grade, yield, plasticity, preload, or resistance.
No material card or solver-body assignment is emitted by any new map.

Attempt04 changes only the current conditional-material evidence/status fields.
It does not claim full-frame material readiness: `inputs_ready=false`,
`per_member_material_mapping_ready=false`, all acceptance/release flags remain
false, and no full-frame finite-element model, connection transfer law,
reaction, demand, or criteria result is supplied.

## Pinned evidence

The attempt03 baseline manifest SHA-256 is
`b0c52399de301632b587bbf336e844789e4864dd57ad7f08ea299164a0fa392c`. Added and reaffirmed map content digests are:

- Frame-timber transverse cases: `fc1d5611d99cc7a5b8f7226e112af29a96ed83cd45d759e997bdb351261a2d7a`
- Candidate steel role map: `978a1c638321f65c6ffb6b7eb7ec93fbabd383cbb1035d730733d53fe8138e14`
- Existing block map: `4d62c18e9717dfb21b2ff00e36668db7393c3bc83016053903bb962a24c18b70`

Attempt03's inherited `source_artifacts` remain the historical attempt02
snapshot. The exact attempt03 file, producer, and README pins are separately
listed as the preserved baseline. New reviewed map and review-file hashes are
recorded under `evidence_bindings.attempt04_conditional_material_map_bundle`.

## Remaining inputs

- The 50 finished STEP solids are source-replayed and round-trip checked, but no solver mesh,
  element/node map, or current-frame finite-element model is supplied.
- Each of the 20 frame timbers now has two source-bound conditional transverse frames, and the 24
  candidate blocks retain their existing 48 conditional cases. These are orientation alternatives,
  not observed board rings or delivered properties. Six plywood panels still have no assigned
  layup, axes, or properties.
- A conditional generic steel elastic scenario family is now bound to 460 candidate component
  roles on 92 axes, but no solver body/element/DOF material mapping or material card exists. No
  physical bolt, nut, washer, or T-nut product is selected and fit-qualified for the 92 candidate
  or 12 retained stacks; thread start/runout, matched engagement, delivery tolerances, and
  receiving remain unresolved. The 60 retained component roles remain unassigned by default.
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

From this attempt directory:

```sh
python3 produce.py --verify
```

Verification checks fixed input SHA-256 pins, reruns only the four pinned
source producers in read-only `--verify` mode, rechecks all 50 STEP files,
778 mass rows, and six exact load-case IDs, then reconstructs this manifest
and README. It does not rebuild CAD, create a solver deck, or launch CalculiX.
Use `--write` once in a fresh attempt directory; both outputs use exclusive
creation and existing files are never replaced.

Manifest SHA-256: `8db026d0764ee3f4f9f83656133e18ea11ebe250acd0c431567e85fa4d4d23bc`.
