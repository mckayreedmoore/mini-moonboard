# Working washer profiles in the revised numerical model

The owner authorized incorporating the completed wider washer evidence into
the numerical model. This contract assigns the working Hillman 885522 / Lowe's
755754 profile to the **eight top-rail ends on four axes**. Its analytical
ID/OD/thickness is **8.3058 / 25.4 / 2.5 mm**, with a hypothetical circular
pressing radius of 5 mm. It supplies a shared profile for axial stiffness,
isolated shaft contact and the plate calculation. The preserved older 48-end
suite is evidence for the method and those dimensions on its original forces;
it is not a new-frame metal result.

The [completed suite](retail-washer-suite.md) covers all 48 ends across six
nominal cases, with zero numerical failures or assumed-250-MPa yield
exceedances. Its maximum index is **0.8288213724731663**. Result SHA256 is
`3e2dee327dbd81d8584955de3c4918c9acc695b0386fa46abd568ba767c64f74`;
receipt is `8eaeee303516584b7d031365cb83446c287735e9fa801120c0ec58dca1e67f79`.
All eight saved nominal support lands and their finished STEP sources are
retained. Current physical top-rail outer-seat datums match those proofs within
the recorded 1e-5 mm precision. The old mean worksheet's cleat support datums
were 50.8 mm shorter and remain preserved as unsupported old joins; the new
profile binds the corrected cleat STEP and canonical outer-seat datum.

The other working roles remain 168 K.L. Jack 25NWUS, eight Bolt Depot 2995
top-side, sixteen 15023 retained 3/8-inch and eight 15025 retained 1/2-inch
washers. Existing side and retained fine calculations preserve their
exceedances. No completed widened or thickened replacement for those roles
was found in the maintained washer evidence. The old two-loose-washer
sensitivity remains above assumed yield, and the 1.5 mm strip-bound sensitivity
is a different force/pressure hypothesis. Neither becomes a replacement
profile or a result for the revised forces.

## The shared numerical profile and stiffness law

The inert API is
`profile_for_axis(contract, axis_id, source_diameter_mm, mode="source")`.
It returns the plate profile, shaft contact annuli, material/contact
hypotheses and an explicit source/working diameter mismatch. Source mode
preserves the quarter-inch representation of the four top-side axes;
working mode identifies the 5/16-inch branch as requiring an explicit model
binding. No larger shaft or washer pass is transferred to the quarter-inch
source. `center_principal_right_2` retains the existing 5 mm supported wood
radius at both shaft ends. Its actual plate retains the catalog outer radius
9.2329 mm and the separate actual supported-mask method.

For the frame, only original axial rows **1850, 1851, 1886 and 1887** change.
Their IDs are `top_outer/clip_single_top_left_1/rail_1`, `rail_2`, and the
corresponding `top_outer/clip_single_top_right_2` axes, each with the suffix
`/outer-seat-axial-tie`. Four ties represent eight exterior seats.
The producer reproduces the original spring before calculating its update:

| Existing axial-column input | Old numerical profile | Working wider profile |
| --- | ---: | ---: |
| Annular wood area, mm² | 222.72621215121478 | 452.52575506508134 |
| Washer thickness at each end, mm | 2.032 | 2.5 |
| Steel extension length, mm | 181.864 | 182.8 |
| Axial stiffness, N/mm | 3751.291479490876 | 5108.952204674765 |

This is the unchanged steel-stretch plus two orthotropic wood-column series
law in `fea/wood_joint_reduced_properties.py:_bolt_axial_law`, using steel
E=200,000 MPa, shaft diameter 6.35 mm, wood grip 177.8 mm and the recorded
seat moduli 750.1495934967178 / 551.6 MPa. Column depth remains
`sqrt(4*A/pi)`. The source is `top-corner-contact-geometry.json`, SHA256
`987af6908d6677165b6a712537ecca0c02827d558ca386ced96f4c1f6436008f`.
The original reduced-properties method is pinned at
`26b6e8bf8800208bfb867439694afa705558ac63ca338778e9210e940a55d9a1`.

The separate isolated contact/plate hypotheses remain Kwood=20 MPa/mm,
Khead=10,000 MPa/mm, E=200,000 MPa, nu=0.3 and assumed Fy=250 MPa, with zero
preload. The column moduli and these contact springs are separate recorded
models. Plate flexure is not silently inserted into the scalar spring law.
Timber datums, D/W mappings, lateral laws and physical counts are unchanged.

`joint_updates()` returns each original row, its exact expected old stiffness,
new stiffness and complete source-column-law pointer.
`to_frame_update(update, original_to_port_map)` emits the core's
`joint_frame_scalar_seat_update/v1` rows `(port_row, old_k, new_k)`.
The frame caller must authenticate its original-to-lumped-port identity map,
verify old stiffness and preserve row ownership/directions. The profile
contract and receipt must be bound before the revised coupled solve.

## Current-force preparation and actual comparison boundary

The initial source-only join binds action03 receipt
`370dafc75a90967cc45e9888bdbd5610fa2df6930a5821d4cd52d01bae70904e`.
It preserves all fourteen dispositions, twelve accepted states and two
unavailable floor-search states. Of 2,496 accepted ends, **2,400 scalar own-end
moments remain unknown** and 96 continuous moments are available. There are
416 unavailable required ends, giving 2,912 total identities. Every metal
stress/index remains null in this preparation. Nominal and zero-gap identities
are kept separate; no small force or moment is rounded to zero.

The dedicated current shaft worker supplies the actual source-bound ordinary
and corner recovery. A changed coupled force basis requires a new same-state
recovery or exact input-equality reuse. The earlier corner group allocation
and proposal results cannot substitute for the new per-bolt force join.
Scalar isolated recovery retains `source_force_compatibility=false`; the four
continuous shafts retain their separately audited compatible fields.

Current metal completion requires each available own-end T/M, signed physical
moment and receiver datum, the selected profile and a matching nominal support
mask. For nonnegative pressure inside pressing radius R, positive T requires
`|M|/T <= R`; T=0/nonzero M is a finite load-path limit, and only exact T=M=0
allows an analytic zero-stress reference. Eligible inputs need actual plate
fields from the existing fine helper. A preparation, unknown moment or raw
numerical STOP cannot become a completed metal comparison. Runtime must be
estimated from a parent-owned governing-family pilot before the full inventory.

Run only the source/authentication preflight with:

```sh
PYTHONDONTWRITEBYTECODE=1 uv run --no-sync python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/washer-working-profile-completion.py
```

To freeze the contract, original-row update and current-end inventory, add
`--prepare --output` with a fresh immediate child of
`rawlocal/washer-working-profile-completion`. It binds every declared source
and output of the historical wider suite and current bolt/mean packets,
including retained field files, before and after publication. Source and
documentation snapshots preserve the consumed bytes. No numerical, geometry
or CAD library is imported by this preparation. Parent owns actual shaft/plate
execution and final integration.

Working dimensions, steel yield, pressing lands and wood stiffness remain
conditional hypotheses. Loaded support shift/tilt, delivered profiles/material,
full stress convergence and complete joint resistance remain explicit limits.
All formal criteria and fabrication/climbing release flags remain unchanged.
