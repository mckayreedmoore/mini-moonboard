# WJ24 baseline representative wood mesh, attempt 01

Status: the pinned-container mesh completed, and the independent deck, body
ownership, volume-record, exterior-face and source-binding audit passed. The
separate independent C3D10 Gauss5 audit also passed: all 652,806 determinants
at the 14 pinned integration points were positive, and the maximum reported
volume error was 1.1373814184922892×10⁻⁵. See the [independent Jacobian audit](../../wj24-independent-jacobian-audit/attempt-01/README.md)
for its source, execution and readback evidence. This result is mesh
preparation evidence only; it is not a contact model, native solve, strength
result, candidate acceptance or release.

The input is the separate source-bound WJ24 five-body export at
`fea/results/diagnostics/wj24-baseline-patch-geometry-v1/`. Its reconciliation
SHA-256 is
`256af45c2a6b2b48726d86f95e2f4febdd8cad726d690738e9cb1fad87a89711`.
The WJ24 source-composition report SHA-256 is
`c4cebb2870e337ece0b429eb099514c36ea5fac79bc9d321fbdcf45734310dfb`.
This worker verifies the reconciliation report, exact five STEP hashes,
source-composition pins and the durable WJ16 predecessor lineage before
meshing. It imports only the WJ24 STEP bodies. It does not consume the older
WJ16/WJ04 mesh as geometry.

Four WJ24 solids are unchanged from the representative WJ16 comparison. The
center-right principal is changed: its two-sided symmetric difference is
13,676.889461 mm³. The resulting mesh therefore covers five WJ24 baseline
solids, including that changed principal. No LED relief variant is included.

The parent launcher used Gmsh 4.12.1 in the pinned image
`sha256:083de8eefd4d9d9029d28ac1fdbb933a3b1e024225d8048165d6ef580d1b8f59`,
with Python 3.12.3 and NumPy 1.26.4. Its command was:

```text
python3 -m fea.wood_joint_wj24_patch_mesh \
  /work/fea/results/diagnostics/wj24-baseline-patch-geometry-v1 \
  /runs/attempt-01 \
  --global-max-size-mm 40 \
  --axis-local-size-mm 3 \
  --axis-refinement-band-mm 12
```

It returned exit code 0 in 13.815608 seconds. The saved CalculiX-format deck
contains only a heading, nodes and five `C3D10` element sets. No material,
contact, tie, load, restraint or solver cards were written. The independent
audit reconciled 89,743 global nodes and 46,629 elements against the deck and
the five disjoint body partitions. It found zero shared global node IDs. It
reconstructed each body's exterior quadratic faces from C3D10 connectivity
and verified exact once-only coverage by the saved CAD surface inventory.
There are 59 cross-body coincident-coordinate groups between the principal
and cleats; these are coincident coordinates with distinct node IDs, not
contact or tie assignments.

| WJ24 body | Nodes | C3D10 | Exterior TRI6 faces | Reported relative volume error |
| --- | ---: | ---: | ---: | ---: |
| Lower service rail | 23,259 | 11,662 | 7,250 | 2.0282×10⁻⁶ |
| Upper service rail | 23,220 | 11,633 | 7,242 | 2.1777×10⁻⁶ |
| Center-right principal | 24,957 | 13,346 | 6,986 | 3.0604×10⁻⁶ |
| Lower WJ04 cleat | 9,286 | 5,085 | 2,532 | 8.3097×10⁻⁶ |
| Upper WJ04 G7 cleat | 9,021 | 4,903 | 2,502 | 1.1374×10⁻⁵ |

The reported errors are below the worker's 0.001 relative volume threshold.
The independent deck audit checked those volume records against the WJ24 STEP
and imported-CAD volumes. The separate Jacobian audit independently integrated
the saved C3D10 connectivity at the 14-point Gauss5 rule and found every
determinant positive, with maximum body volume error 1.1373814184922892×10⁻⁵.
That check does not prove positivity at every point inside each quadratic
element.

The Gmsh log contains three negative-distortion warnings from initial volume
mesh generation, before high-order optimization. The final mesh report records
positive sampled and integration minima after optimization. That sequence is
preserved in `run.log`; the independent recomputation remains the check on the
saved final connectivity.

CAD surfaces remain keyed by transient Gmsh tags. Their exterior face
references and six-node TRI6 unions are reconciled, but semantic interface,
contact and bore ownership are pending a WJ24-specific classifier. The audit
does not infer interfaces from surface tag numbers or coincident coordinates.

The independent audit script and readback are `parent-audit.py` and
`parent-audit.json`. `execution.json` records the pinned invocation and source
readback. `complete-mesh-evidence.tar.gz` contains the mesh deck/report,
producer snapshots, launcher records and independent audit. The adjacent
`bundle-contents.json` and `sha256.json` bind its members and outer evidence.
