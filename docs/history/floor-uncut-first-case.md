# First uncut-frame response investigation

Candidate: `compact-floor-uncut-development`. This investigation does not change
the selected flush candidate or qualify a construction package.

## Question to resolve

Recover the A12-left response with the actual full-stock leg/rim profiles,
6×6 post material and mixed-material front bolt seat springs. Use the resulting
rim-face stress and complete connection demands to decide whether the full bevel
can use an applicable compression-side method, or whether the separate square
seat/restraint route merits further development. A numerical pass alone cannot
answer the material/method or catalog-resistance questions.

## Preparation failure found before any native solve

The first full assembly preparation rejected the panel screw midsurface point
`[-1200.15, 13.16035781, 327.93765569]` on `base_side_left` as outside the exact
timber profile. The existing response model intentionally locates these panel
screw connections at the panel midsurface. The new exact-profile adapter must
preserve their explicit offset force/moment transfer; a strict inside-timber
locator cannot represent that interface unchanged.

The initial process and a diagnostic repeat both exited during preparation,
before creating a native case directory or invoking CalculiX. No converged
response, new resistance result or contact acceptance was produced. The second
attempt added the member and point to the error message, identifying the fault.

Correction must distinguish named panel screw offsets from actual timber
contacts. It must not clamp arbitrary outside points or relax floor/header
contact geometry. Verification requires rigid-body displacement reproduction
and force/moment consistency at the intended offset, followed by complete
assembly preparation and the native case.

## Named offset verification

Focused checks now show that the existing offset matrix reproduces arbitrary
rigid translation plus infinitesimal rigid rotation at the panel midsurface.
Its transpose preserves both the applied resultant force and its moment about
the global origin at that same point. An outside point is accepted only when it
exactly matches an explicitly named panel-screw registration; removing that
registration makes the unchanged point fail the actual-timber locator.

The verification found one bounded defect: malformed registry rows could raise
`KeyError` or silently fall through to the ordinary locator. The adapter now
requires every row to have a nonempty string name and three finite 3-vectors
before matching it. Duplicate registered points remain explicitly rejected.

`uv run pytest -q tests/test_floor_uncut_mesh.py` passed 13 tests, and
`uv run ruff check fea/floor_uncut_mesh.py tests/test_floor_uncut_mesh.py`
passed. These are interpolation and registration checks only. The subsequent
coordinator-run preparation result is recorded below; no native response or
resistance result follows from these focused checks.

Run complete A12-left preparation, without creating a case directory or
starting CalculiX, from the repository root with:

```bash
uv run python - <<'PY'
from fea.current_coulomb_run import distribute_floor_tangents
from fea.current_response_materials import connection_stiffnesses, materials
from fea.floor_flush_run import face_contacts
from fea import floor_uncut_run as uncut

before = uncut.sources()
if before != uncut.LOADED_SOURCES:
    raise RuntimeError('Restart preparation after source changes')
candidate = uncut.candidate
bolts = {connection.name: uncut.bolt_properties(connection)
         for connection in candidate.connections() if connection.kind == 'bolt'}
stiffnesses = {**connection_stiffnesses(), 'floor': 1.e5, 'bearing': 1.e6,
               'seating_per_area': 100.,
               'bolt': {**next(iter(bolts.values())), 'by_name': bolts}}
structure, metadata = uncut.prepare(
    candidate, expected_candidate=candidate.KEY, materials=materials(),
    stiffnesses=stiffnesses,
    member_contacts=face_contacts(candidate, stiffness_per_area=100.),
    clearance_monitors=(), hold='A12', pounds=250.,
    horizontal_force=(-300., 0.), frame_size=150., leg_floor_grid=3,
    patch_size=20.)
distribute_floor_tangents(structure, metadata)
if uncut.sources() != before:
    raise RuntimeError('Source changed during preparation')
print({'nodes': len(structure.nodes), 'elements': len(structure.elements),
       'members': len(structure.members), 'springs': len(structure.springs)})
PY
```

This command needs one serialized heavy-check slot and one Python process. It
builds actual CAD and the in-memory full-frame mesh but neither invokes the
native solver nor writes an output directory. Allow minute-scale CPU time;
the coordinator's measured peak resident memory was 587,876 KiB.

### Complete preparation result

The coordinator's fresh, source-guarded preparation passed in 42.87 seconds:
25,388 nodes, 5,062 elements, 20 timber members, and 1,344 springs. All 217
recorded source hashes agreed before and after preparation. This closes the
reported assembly-preparation failure and task 1 of the
[execution plan](engineering-execution-plan.md).

An earlier successful preparation overlapped a final registration-validation
edit and was repeated; only the fresh guarded run is the accepted checkpoint.
Neither run invoked CalculiX or created a native case directory. The first
native response and its interpretation remain task 4, with provisional modeled
hardware distinguished from any proposed catalog replacement.

## Remaining interpretation limits

The [front bolt envelope](floor-uncut-front-bolt-envelope.md),
[alternative hardware investigation](floor-uncut-front-hardware-options.md),
[bevel-method audit](floor-runner-bevel-method-audit.md), and
[commercial angle review](floor-flush-angle-review.md) remain separate open
questions. The first case will not establish the other five cases, contact
sampling adequacy, machining release, or a complete build decision.

## First native attempt

The source-guarded A12-left run completed its declared 100-cycle budget at
`fea/generated/floor-uncut-first/a12-left/block-01`. It used the current
provisional hardware representation described in
[floor-uncut-front-preflight.md](floor-uncut-front-preflight.md), not a modeled
8½-inch/CL-8-FW physical stack.

The run is **numerically rejected**. It terminated with
`Coulomb/contact iteration budget exhausted` after 698.88 seconds. The final
normal-contact active set passed, as did global equilibrium, member equilibrium
and MPC checks, but the explicit floor-friction law did not. Final and best
peak friction residual was 23.2533 N against the unchanged 0.01 N tolerance,
at `floor_base_post_center_left_2_friction`. The residual fell from a 728.528 N
peak during the search and was still decreasing over the final iterations;
this trend does not convert the rejected state into a converged solution.

The final rejected iterate has maximum timber/panel displacements of
5.6380/14.6053 mm and 91 active bearings. These are troubleshooting values,
not accepted structural demands or resistance inputs. No rim-face, bolt,
angle or member pass/fail conclusion is drawn from them.

The archive is about 1.7 GiB and records 217 source hashes and 1,249 artifact
hashes. Preserve it as the failed numerical witness. Do not seed a design
assessment from it merely because the final normal-contact set passed.

The next finite step is a numerical convergence diagnosis using the preserved
cycle history. It should identify whether slow secant convergence, a switching
floor point or another deterministic issue explains the residual, then justify
one bounded retry configuration. Do not increase the cycle limit or change
damping without that comparison, and do not start the remaining five cases.

## Scope correction and accepted no-slip response

The owner identified that floor attributes are outside the current assessment.
The Coulomb controller above conflicted with the controlling instruction to use
an explicit no-slip support assumption. Its failed archive remains a historical
numerical witness; no convergence diagnosis or retry is required for current
acceptance work.

The uncut runner now uses the existing no-slip response controller. Compression-
only normal floor cells may open, while conditional tangential supports prevent
sliding on a contacting floor body. No friction coefficient, measured floor
property or installed anchor is inferred.

The fresh no-slip A12-left response converged in 11 contact cycles at
`fea/generated/floor-uncut-first/a12-left/no-slip-01`. Global equilibrium,
member equilibrium, MPC and normal-contact checks all passed. Maximum timber
and panel translations were 5.6657 and 14.5667 mm. The CLI exposed a missing
success `termination` label only after the complete report and artifact hashes
had been written; the shared runner now supplies that label. The archived report
remains authenticated to the exact pre-label-fix source snapshot and has SHA-256
`d1d8b6e4747a6f2875b1811fcf0fc7001c55dba82677b33305b08b81bcafcc81`.

Portable evidence is under `fea/results/floor-uncut-first/a12-left`. Its full
assessment meets all 25 listed conditional criteria. Governing listed ratios
are 0.592846 for the adopted bolt/group comparison, 0.417165 for sampled net
members, and 0.468799 for rated commercial-angle force components. These checks
do not assign capacity to unlisted angle separation or flange moments. The
largest recorded unlisted angle separation is 260.618 N at
`clip_timber_header_outer_left`.

The first recovered full rim section has compression on both left-rim q+ corners
in both station-load conventions. The right rim has small q+ tension, reaching
0.017573 MPa. These adjacent full-section values do not recover local bevel-edge
or transition stresses, but they reject a blanket compression-only classification
of both bevels. The existing bevel-method gate therefore remains open.

The response uses the current provisional modeled bolt/washer representation.
The proposed 8½-inch/CL-8-FW stack remains unmodeled and unqualified for the
registration, delivered-body and washer-material reasons in the preflight. The
uncut candidate remains unselected and `qualified_for_design` remains false.
