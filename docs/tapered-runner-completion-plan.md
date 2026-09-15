# Tapered-runner DIY completion plan

Requested September 14, 2026. This is the finite work plan for
`compact-floor-flush-development`, following the owner's preference for tapered
outboard floor beams, whole kicker panels and flush adjoining timber faces.
The preceding `compact-floor-taper-development` remains the comparison baseline;
older candidates and their evidence remain preserved.

The owner subsequently requested a fresh flush-end revision: trim the front and
rear `base_floor` ends to the outer post and rear-leg faces, and trim the lower
`base_side` ends flush to those posts. Relocate the angle brackets if necessary.
Use a separate `compact-floor-flush-development` model while investigating this
revision; the six passing taper cases do not automatically qualify its changed
ends, support footprint, bearing or bracket positions. The owner also requested
rear-leg tops flush with the side rims, removing the prior 18 mm projection;
upper bolt end distance must be reassessed. The owner authorized moving bolts
to make the flush detail work; retain complete stack and fresh-drilling checks
and evaluate the relocated joint with valid forces.

## Completion claim

Complete means a consistent, reproducible, engineer-unreviewed **conditional DIY
design and build package** for this exact assembly. It does not mean a built
structure has been inspected, a universal climber rating has been established,
or every conceivable failure mode has been qualified. Physical receiving and
installation inspections are specified in the plans, not falsely marked done.

The accepted panel/T-nut construction remains the design basis. No new general
panel campaign, floor-friction test, external engineering sign-off, destructive
test, or search for a failure weight is added. The current native floor scenario
uses assumed per-cell Coulomb friction at mu = 0.4; it must not be described as
measured friction or as the older no-slip model. Publishing remains outside the
authorized local-only scope.

## Current execution checkpoint

The flush geometry, relocated bolts, viewer, draft assembly guide and current
construction drawings are implemented. All 24 receivers fit. One fresh A12-left
case is numerically accepted and archived with verified source/native hashes.
Its current assessment meets 37 of 38 implemented criteria; the rim end-cut
screen remains negative. The subsequent source review has not established an
applicable passing alternative for the tensile cut-face state. The leg taper
also retains an unresolved local stress/resistance method. These findings keep
the design-release gates open; they are not a reason to label the six old cases
as current or to claim the package is complete.

See [current checkpoint](current-completion-status.md),
[cut-method review](flush-cut-method-review.md),
[taper-method review](taper-method-applicability-review.md),
[draft assembly guide](floor-flush-assembly-guide.md), and
[current drawings](floor-flush-construction/).

## Required gates

### 1. Establish one exact design authority

- [x] Record the tapered-runner selection consistently in the README, current
  design basis, completion record, relevant working agreements and viewer.
- [x] Identify solid 4x6 legs/rims, two full 2x6 outboard runners, whole kickers,
  the 277 mm main-face datum, 56 mm upper bolt pitch, twelve complete bolt stacks,
  66 panel/kicker screws, retained commercial connections and two loose pads.
- [ ] Link the exact model, matching drawings, hardware and evidence. Preserve
  older designs with historical labels; remove conflicting current directions.
- [ ] Implement the requested flush cuts and bracket relocation, preserving bolt
  end/edge distances, full washer seats and required bearing. Record any conflict
  between the desired finish and supported connection geometry instead of
  silently discarding either requirement. Include front and rear runner bolts
  as well as upper leg bolts; retain the fresh-stock drilling basis.

### 2. Audit the analytical basis and actual load path

- [ ] Establish a traceable ledger from the six load cases and actual geometry
  through numerical acceptance, member actions and all 35 listed criteria.
- [ ] Review material values, adjustments, connection stiffness, contact,
  eccentricity, prying and section sampling for this exact candidate. Identify
  assumptions explicitly rather than inferring capacity from a green status.
- [ ] Verify the cited taper/notch method's applicability to the side recess,
  loading direction and solid timber; justify the mixed EC5/ASD comparison and
  the shear/torsion bounds. Confirm that bore-region checks and sampled sections
  cover the actual critical locations without claiming local stresses are
  resolved by a gross-section calculation.
- [ ] Resolve the omitted runner/leg contact: recover relative interface motion
  from saved native data for the 2 mm gap and nominally touching side faces, then
  establish that omitted contact is inactive or account for its effect. Empty
  contact-monitor lists are not evidence that those gaps remain open.
- [ ] Explicitly justify the current notch factor of 1.0 and the rectangular
  torsion coefficient for orthotropic timber, or replace them with supported
  comparisons. The word "conservative" is not itself a demonstrated bound.
- [ ] Resolve concrete in-scope defects found by that audit. Reuse authenticated
  existing results where valid; rerun only analyses affected by confirmed gaps
  or changes. Do not require another whole-frame comparison by default.

### 3. Disposition every known limitation

- [ ] Provide a ledger separating passed criteria, non-adopted sensitivities,
  installation-dependent assumptions and unqualified actions.
- [ ] Explain both failing full-root bolt sensitivities and why the adopted
  nominal-diameter route requires specific full-body/thread coverage.
- [ ] Report this candidate's commercial-angle separation and independent
  flange-couple demands, the available capacity basis and the precise remaining
  limitation. Do not transfer another candidate's maxima or invent capacities.
- [ ] Preserve accepted scope limits without presenting them as passing checks.
  Any confirmed defect in an adopted criterion remains open until resolved;
  a caveat alone does not turn it into a pass.

### 4. Define buildable dimensions and fabrication allowances

- [ ] Provide unambiguous left/right datums, grain direction, orientation and
  dimensioned profiles for every unique cut and hole, including taper transitions,
  flush leg tops, relocated bolt axes, receiver faces and wiring passages.
- [ ] Establish supported stock, cut and drilling acceptance bounds from actual
  fit, retained section, edge/end distance and washer-seat margins. Nominal CAD
  dimensions and a 1:12 slope alone are not a fabrication-tolerance specification.
- [ ] Check the proposed allowance envelope using valid existing demands where
  possible; assess changes to stiffness/contact before reusing those forces.
- [ ] State rejection/rework rules for overcuts, misplaced holes and unsuitable
  stock. Do not authorize improvised repairs or deeper cuts without assessment.

### 5. Complete procurement and hardware acceptance

- [ ] Supply a consolidated, candidate-specific lumber and hardware list with
  quantities, grades, sizes and owned versus to-buy items; include all screws,
  bolts, nuts and washers rather than only the leg joints.
- [ ] Make the twelve bolt stacks self-contained: upper 8-inch half-inch bolts,
  front 4-inch three-eighths bolts and rear 4.5-inch three-eighths bolts, with
  matching washer/nut specifications and current dimensional requirements.
- [ ] Provide receiving checks for actual stock grip, full shank to first
  transition, usable threads, washer dimensions/material assumptions, nut seating
  and complete thread engagement. Explain permitted substitutions or require
  reassessment. Do not claim supplier stock has been measured.

### 6. Write one practical assembly guide

- [ ] Give a step-by-step sequence for stock preparation, taper layout and
  cutting, drilling, dry fit, supported assembly, commercial connectors,
  panel/kicker attachment, T-nuts, lighting and pad placement.
- [ ] Provide a workable hand-saw/plane method or supported powered method for
  the taper, with ways to inspect the finished profile. Identify temporary
  support needs and avoid unsupported handling of the heavy frame.
- [ ] Preserve whole kickers, intended direct bearing, outward bolt tips,
  independent seams and open service access. Do not borrow kicker-notch steps,
  shifted-post directions or six-inch rear bolts from the original floor design.
- [ ] Specify tightening/installation instructions from the actual hardware
  basis; do not invent torque or preload. Include final assembly and periodic
  condition checks with practical stop-use/reassessment triggers.

### 7. Deliver an accessible, matching plan package

- [ ] Create a single build-guide entry point linking stock list, dimensional
  drawings, drill sheets, wiring/panel schedules, hardware and assembly CAD.
- [ ] Check drawing legibility, units, datums and print behavior. State whether
  each sheet is dimension-only or a verified full-size template; do not imply
  that arbitrary browser printing preserves scale.
- [ ] Make local viewer default, inspection metadata, document links, crash pads
  and weight agree with the selected candidate. Public availability must not be
  claimed until a separately authorized publication occurs.

### 8. Verify final package consistency

- [ ] Rebuild/check affected CAD and fabrication artifacts, source hashes and
  weight inventory; confirm quantities and clearances against the final model.
- [ ] Run appropriate tests, lint and browser checks for changed behavior. Avoid
  repeating unaffected heavy solves simply for a metadata or guide change.
- [ ] Walk the build guide against drawings and CAD as a builder would, including
  both mirrored legs and each distinct connection. Correct missing dimensions,
  conflicting instructions and historical links.

### 9. Obtain an independent final review

- [ ] Review calculation applicability/claims, fabrication and hardware usability,
  and software/artifact consistency independently against these gates.
- [ ] Resolve substantial in-scope findings and rerun affected checks. Record
  accepted limitations separately from unresolved defects.

### 10. Record the finite completion decision

- [ ] Publish a local completion ledger with evidence for every gate, exact
  candidate/revision, test results, installation conditions and analytical limits.
- [ ] State precisely what is complete and what the builder still must inspect.
  Assert completion only when all applicable gates above are satisfied.
- [ ] Save a local commit during allowed hours with real author/committer times.
  Do not push without new authorization.

## Evidence already available

Six native cases currently pass all 35 listed conditional criteria. The prior
audit matched 1,760 native artifact hashes and all saved assessments to the
current checker. All 24 bolt receivers fit; 22 construction artifacts and matching
CAD/viewer exports exist. The recorded test run has 534 passes and 15 deselections,
with five browser variants checked. These are substantial completed evidence,
not a substitute for the applicability, tolerance and build-guide gates above.

See [taper study](floor-runner-taper-study.md),
[hardware requirements](floor-runner-taper-hardware.md), and
[previous checkpoint](current-completion-status.md).
