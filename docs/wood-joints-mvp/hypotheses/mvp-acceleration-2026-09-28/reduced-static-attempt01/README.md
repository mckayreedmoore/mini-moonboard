# Current reduced static model: assembly preparation

The owner directed beginning the accelerated six-case model with Luna/max
agents after reviewing the [route assessment](../README.md). This packet
starts that implementation for `compact-floor-flush-wood-joints-development`,
revision `led-clearance-2x6-runner-seated-blocks-v1`. It changes no geometry,
candidate selection, physical-work permission or criterion disposition.

## Implemented

`prepare.py` binds the frozen attempt04 manifest, current contact graph,
mass-centroid/topology records and applied-load contract. It produces
`model-inputs.json` and `body-external-wrenches.csv`:

- 50 distinct current timber, block and panel bodies.
- 92 candidate bolts, 12 retained bolts and 66 Hillman screw axes. Four
  three-receiver bolts remain four physical bolts; pair associations are not
  expanded into separate independent connectors.
- 96 adjacent raw-wood interface stations along the 92 candidate bolts,
  derived from their ordered receiver intervals. All are contiguous within
  0.00001 mm in this model. All 96 points match a finished contact plane of
  the same member pair within 0.00001 mm (maximum discrepancy approximately
  0.000000116 mm). Plane coincidence does not establish inclusion within the
  trimmed patch, shear-plane capacity, bolt continuity or a spring law.
- Six load cases and 300 body external-wrench records, with global XYZ forces
  in N and moments in N mm about each body's modeled center of mass.
- All 778 modeled mass rows retained exactly once. Timber/panel/block own
  weight and same-panel T-nut weight bind directly to their current bodies.
  The other 586 hardware rows, totaling 7.728314 kg, retain their exact global
  gravity and centroids with their possible receiver members. Their mechanical
  mass carriers are not guessed from nearest geometry or equal sharing.
- The separate 25 kg accessory placement scenarios are preserved, without
  silently attaching them to the model or including them in the base table.

The loaded panels are `main_upper_left` for the three A12 cases,
`main_upper_right` for the two K12 cases, and `main_lower_left` for A1-rear.
Each mapping follows the existing same-hold T-nut/panel source association.
The source patch and 100 mm hold standoff remain in each load record.
Climber dynamic amplification is already included in the specified applied
force; gravity is added once without that amplification.

**The CSV contains external loads, not calculated interface or joint demands.**
All six assembled force/moment totals, including the still-unassigned hardware
gravity, match the source resultants. This establishes input accounting and
reference-point consistency; it does not establish load sharing or a response.

An independent Luna/max reviewer recomputed the six global resultants from
the 300 CSV rows and checked the load directions, reference shifts, hold
carriers and mass inventory against the frozen source records. No force,
moment-sign or mass-conservation defect was found.

`contact_geometry.py` imports the 50 frozen STEP solids and extracts 117
opposed planar patches across 115 touching member pairs, retaining their
areas, centroids, outward normals, vertices and line/circle boundary data.
It checks all 147 broadphase pairs against the prior graph; the maximum area
difference is 0.000000829 square millimeters. The eight existing timber floor
faces match the preceding equilibrium screen. No floor support or active
contact is added by this export.

Six graph pairs still have zero-area or unresolved touch. These include the
left and right center-principal-cleat/kicker pairs; they receive no fictitious
bearing patch. Their alternate supporting and fastener paths remain explicit
work for the response model. A touching edge alone is not a supported seat.

`member_geometry.py` exports 44 grain-aligned member envelopes and six panel
geometry descriptors from the pinned STEP bodies and current material-frame
maps. It reports actual-to-envelope volume ratios and omitted geometric
features. These are preparation records, not an accepted gross-section
stiffness approximation. Their geometric section axes are not automatically
the material radial/tangential axes.

Parent review corrected a rotated-section envelope error before this packet
was finalized. All 20 timber section dimensions now independently match the
pinned source section dimensions within 0.00001 mm. The smallest actual-to-
envelope volume ratio is 0.8797 for the inclined legs; omitted bevels, bores
and cuts still need appropriate treatment in the response and resistance
models. A Luna/max reviewer checked the corrected source replay.

`bolt_clearance.py` measures coaxial cylindrical surfaces in the current
finished receiver STEP bodies for all 92 candidate bolts and 188 receiver
incidences. It finds 156 modeled radial gaps of 0.575 mm and 32 of 0.475 mm;
the latter belong to the center-block family. These measurements are bound
per receiver in `model-inputs.json`. They are centered CAD clearances, not
as-built measurements, drill instructions, complete bearing engagement or
an adopted spring law. Retained-bolt and Hillman connection behavior remains
separate work.

## Reuse decisions

Use the existing native CalculiX `Structure`/`CurrentStructure` member,
panel and attachment building blocks where their kinematics apply. The old
`current_response_model.prepare()` assembles a different bracketed candidate
and cannot be called unchanged for this wood-joint frame. No existing
candidate passes or connector forces are transferred.

The audit found specific incompatible spring inputs in
`fea/current_response_materials.py`: the panel law reads a SPAX product,
the SDS law refers to the replaced attachments, and the bolt example is a
synthetic 3/8-inch family. None supplies the current Hillman or candidate
quarter-inch bolt law. The current DF-L/FPL material scenario and conditional
APA equivalent-panel implementation are reusable mathematical ingredients;
their per-member classification, panel applicability and orientations still
need an explicit current binding.

The published [Swedish Wood joint-slip table](https://www.swedishwood.com/siteassets/5-publikationer/pdfer/sw-design-of-timber-structures-vol2-2022.pdf)
(Volume 2, page 33) provides a possible service-slip comparison per fastener
and shear plane, with clearance deformation separate. It does not provide a
complete corner-block law, axial washer behavior, or verified Hillman product
behavior. Using an elastic comparison in a diagnostic model requires explicit
applicability and sensitivity; it is not an adopted connection capacity.

## Remaining assembly work

The [coordinator handoff](../COORDINATOR-HANDOFF.md) records the live work split
and execution gates. Two additional implementation pieces now exist:
`fea/wood_joint_reduced_contacts.py` partitions exact trimmed patches while
preserving area and first moment; `fea/wood_joint_reduced_loads.py` compiles all
778 source masses into 362 named carrier wrenches and maps the nine accessory
scenarios. Their focused checks pass. The latter resolves source/carrier
identities for the previously deferred 586 hardware rows, but carrier DOFs and
receiver force sharing still require mechanical integration. Neither module
adds a native response or changes the preparation JSON's readiness flags.

Bind the actual planar contact patches and floor-bearing geometry, current
member/panel elements and material frames, physical bolt-stack interfaces,
and connection engagement laws. Define hardware gravity carriers and map
the accessory scenarios without changing their force/moment totals. Then
check the assembled model for mechanisms and run a bounded static diagnostic
with individual-body and whole-frame equilibrium recovery. Sensitivity must
address clearance, seating and unsupported stiffness choices before its
forces can feed resistance acceptance.

Prior direct-contact method documents describe the previous implementation.
They do not make detailed native contact analysis of every bolt a blanket
prerequisite for this owner-authorized reduced route. Any revised method must
still demonstrate that its response quantities are adequate for the physical
checks they support. Native method changes retain parent readiness, frozen
inputs, small known-answer checks and serialized execution.

## Reproduce

From the repository root:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01/contact_geometry.py --verify
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01/member_geometry.py --verify
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01/bolt_clearance.py --verify
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01/prepare.py --verify
```

Use `--write` to regenerate the two preparation artifacts. Assertions check
source hashes, unique hold carriers, vector units and moment shifts, inventory
coverage, and all six force/moment totals. No native solve is launched.
