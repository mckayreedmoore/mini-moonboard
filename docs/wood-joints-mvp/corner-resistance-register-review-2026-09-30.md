# Independent corner resistance-register review — September 30, 2026

This review covers the consolidated
[BG001 → BG003 → BG045 resistance register](hypotheses/mvp-acceleration-2026-09-28/current-corner-complete-resistance-register-attempt01/README.md)
for `compact-floor-flush-wood-joints-development`, reviewed revision
`led-clearance-2x6-runner-seated-blocks-v1`. The FEA coordinator owns that
register, its mechanics calculations, the support implementation and native
execution. This separate review changes none of those files or reviewed
geometry. It records source-to-register verification, not joint acceptance.

## Reviewed revision and checks

| Reviewed file | SHA-256 |
| --- | --- |
| Register README | `3becd6ab5c928e51a4ee02ef005fc3953beed21f8556781875e27fcc6e6d25d0` |
| Register producer | `756e397f7e34c05eee6dfd7b25473033c10e81d1ca3424db2ef5f9f99a1e7b10` |
| Local signed-demand output | `557b994f7600ceb7c958d50dd01350724d7ea86c671a086677b6f3044ecc2f48` |

The producer's read-only `--verify` run passes with
`PASS_BYTE_IDENTICAL_168_SIGNED_PLANE_STATES`. A separate direct-source
comparison reads the three hash-pinned corner exports rather than invoking
the register builder. A12-rear, A1-rear and K12-rear each have seven
increments; all 21 case/increment states retain passing source response gates
and all-five-body raw and interval balance flags. These are authenticated
source checks, not new solves. The comparison then checks:

- All 168 lateral-plane records match source group, physical bolt, case,
  increment, receiver ownership, application point and signed endpoint force.
- Each endpoint force has its equal-and-opposite partner. The six physical
  bolts have two BG001 planes, four BG003 planes and two BG045 planes per
  state; BG003's two planes remain part of the same physical bolt.
- Each row retains that state's axial tie and all lateral planes of its
  physical bolt. No independent peak is substituted for a simultaneous action.
- Independent `hypot` reconstruction differs from stored lateral magnitude
  by at most `1.4210854715202004e-14 N`. All eight peak records select the
  controlling source state for their own plane.
- Every local evidence link in the reviewed register README resolves. The
  resistance/transfer table contains 15 rows, including the complete corner
  boundary, neighboring timber contact and scoped retained-frame duties.

The latest linked three-case axial-seat register covers 21 states, 126 signed
tie records and 252 outer-seat records: six physical ties and twelve washer
seats per state. Each BG003 continuous bolt has one tie and two outer seats;
the middle `base_side_left` receiver has no washer seat. All 126 ties are in
tension. The 119.343 N maximum and 0.535828 MPa full-CAD-annulus value are
three-case demand and uniform-average pressure references, not resistance,
local pressure or a six-case envelope. Existing Fc⊥ comparisons apply only
to matching transverse seats; the proposed BG045 block seats load along
grain.

This checks register fidelity to existing audited exports. It does not
repeat the native force recovery, revalidate the underlying carrier laws,
or establish physical joint stiffness or strength. The source balance flags
are retained from the authenticated exports, not presented as a new solve.

## Resistance and completion boundaries

The table correctly keeps individual conditional reference calculations
separate from complete-joint acceptance. In particular:

- BG003's `4.8292 MPa` spine result is a necessary lower bound on required
  projected bearing peak. It is not a sufficient demand envelope, an
  allowable stress or a passing ratio. Compatible bearing/contact and
  continuous-bolt, shared-timber and axial transfer remain required.
- BG045's conditional `5.4 mm` loaded-edge comparison remains subject to
  applicability and direction interpretation. Its axis-2-only proposal
  reaches the stated comparator with no tolerance margin; no change to the
  reviewed coordinates or transfer of existing demands to a moved axis is
  supported by this review.
- Splitting, adjusted/group resistance, combined bolt actions, thread and
  engagement, washer support/response and local member stress transfer remain
  open. The existing signed cuts and average contact pressures are demand
  records, not resistance calculations.
- The three rear cases are not a six-case envelope. Compatible gravity and
  the forward/left/right cases remain support dependencies. Further method
  work must address a named blocker to those results.
- Unchanged LEG/FLOOR-RUNNER resistance is reused within its recorded scope.
  Only identified changed demands, receivers, geometry or hardware require
  rechecking. Panel work stays limited to named affected transfer paths for
  this corner deliverable.

The parallel hardware/material packet owns the remaining source-bound inputs
already represented in the 15-row register: receiver species/grade and
declared grain direction with the corresponding embedment basis and
adjustments; selected-fastener shank, runout and thread regions along the
continuous BG003 stack; bolt tension, thread-stripping and nut-engagement
checks with a combined bolt-action method; supported head/nut footprints,
washer material and washer bending/spreading/pull-through resistance; and a
tolerance-aware resolution of BG045's conditional 20 versus 25.4 mm
loaded-edge comparison. These inputs add no adopted capacity or acceptance
result here.

The [published hardware/material packet](hypotheses/hardware-material-specification-2026-09-30/README.md)
now supplies per-member profile requirements for all 92 candidate axes and
declared wood/grain scenarios. Those inputs allow scoped conditional
calculations to proceed. Exact product transition/engagement guarantees,
washer metal resistance, compatible bearing and combined joint resistance
remain separate closure requirements; the specification packet adopts no
joint capacity.

The sibling [review script](corner-resistance-register-review-2026-09-30.py)
exposes `--self-test`, runnable with
`.venv/bin/python docs/wood-joints-mvp/corner-resistance-register-review-2026-09-30.py --self-test`.
The updated checker pins the declared producer hash and rehashes `produce.py`
before reading the source exports. Its self-test rejected all 11 in-memory
corruptions, including an incorrect producer hash and mixed-state BG003 tie.
This validates source-to-register checking only; complete resistance and
joint acceptance remain open.

The checker requires the local pinned corner exports and signed-demand file.
Those numerical results remain local under the owner's code-and-summary
publication policy; a source-only checkout cannot replay this check without
that evidence. Missing files or changed pins fail explicitly.

## Coordination and disposition

The parallel hardware/material packet owns binding the listed inputs without
claiming physical parts have been inspected. The FEA coordinator retains
mechanics-method adoption, any model revisions, frozen native readiness and
serialized execution. This review leaves those active packets and status
ledgers with their current owners.

Disposition: **source-to-register verification passes; complete resistance
and joint acceptance remain open.** No criterion is closed, capacity invented,
native job launched, physical operation authorized, or raw result data
published by this review. The persistent goal remains the complete conditional
MVP-E package on `master`, with all 47 criteria supported and independent
final review; it is not fabrication or climbing release.
