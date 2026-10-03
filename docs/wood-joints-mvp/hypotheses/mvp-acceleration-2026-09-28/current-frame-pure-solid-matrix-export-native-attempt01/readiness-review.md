# Independent exact-freeze readiness review

Decision: ready for one scoped native MATRIXSTORAGE export attempt. The exact
reviewed `freeze.json` SHA-256 is
`614c9b466fd05c0b5ee6917aa26e108fd8151b36459b8b84999cd474f13d9ed3`. The
frozen `model.inp` and `model.json` hashes match that manifest, all 99 live
source entries match, and each of the three frozen FEA source snapshots is
byte-identical to its current source module.

The deck has 12,549 physical nodes, 1,903 C3D20 elements in 68 element sets,
and 50 disjoint physical-body node/element maps. I independently compared the
deck node IDs and `.14g` coordinate tokens and the element IDs, types, and
connectivity against `model.json`; all match. The deck has no SPC, MPC,
connector, or load keyword and ends with the single
`*FREQUENCY,SOLVER=MATRIXSTORAGE,GLOBAL=YES` step. It retains the material,
orientation, and solid-section cards identified by the pinned source audit;
the parent reports that the read-only proposal verifier confirms their exact
source-card equality.

Each of the 50 materials has a `1.0e-9 tonne/mm^3` density added only so the
frequency export can write its companion mass matrix. The pinned source audit
separates density from the unloaded linear elastic C3D20 stiffness path. The
`.mas` file must be discarded and must not be used as physical gravity input.

The pinned CalculiX 2.23 manual and source support the terminal matrix-export
method. Parent reports the bounded free and constrained known-answer coupons
pass, and the sparse assessment method's fixture replay passes. That evidence
checks export mechanics and parsing; the actual 12,549-node export remains
unobserved. The capped run is one launch, at most 120 seconds and 6 GiB, with
no automatic retry.

The scope ends at an unconstrained elastic operator export. It does not select
or impose gravity/contact states, recover MPC/SPC reductions, add connector or
floor-stick tangents, or establish frame equilibrium. The sparse assessment
may check the physical `.dof` map, separated-body matrix structure, and six
rigid kinematic fields per body; it cannot certify exact rank, exclude all
internal mechanisms, or accept the frame. I did not launch CalculiX or modify
the frozen inputs.
