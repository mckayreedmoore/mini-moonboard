# Conditional floor structural-coupling fixture — attempt01

## Bounded result

The standard-library KKT verifier finds exactly one admissible contact mask
for each of the four prescribed stages: both bearing, left only, both open,
and both re-engaged. It enumerates and records all four masks at every stage;
the full set of 16 candidate branches is in [observed.json](observed.json).
The independently implemented constrained-coordinate elimination check in
[parent_check.py](parent_check.py) reproduces the same four selected states and independently compares all 16
KKT candidate vectors, admissibility decisions and episode references.

The selected contact forces are:

| Stage | Active cells | Tangent reactions (left, right), N | Normal reactions (left, right), N |
|---|---|---:|---:|
| Both bearing | left, right | (-5, -3) | (5, 15) |
| Left only | left | (-2, 0) | (5, 0) |
| Both open | none | (0, 0) | (0, 0) |
| Re-engaged | left, right | (-2, 2) | (2, 4) |

The re-engagement references are captured from the preceding recorded open
stage at `(0.10, 0.35) mm`. Maximum selected force-balance residual is
`3.553e-15 N`; maximum active-stick residual is `1.388e-17 mm`. The contact
sequence is a hand-selected method fixture. Its pass does not establish that
arbitrary loads have a unique admissible state. The parent recorded fixed-
reference one-cell cases with no admissible branch and with two admissible
branches in the [applicability counterexample](parent-reference-counterexample.md).
A positive-definite carrier therefore does not establish existence or unique
selection for arbitrary loads under this discrete reference rule. These are
method limits, not findings about a reviewed frame case or physical timber.

## Frozen fixture and method

Each cell has one tangent coordinate `x` and one signed normal gap `z`, with
`q = (x_left, z_left, x_right, z_right)`. Normal force is
`N = 100 * max(0, -z) N`. Positive normal reaction enables ideal stick at that
cell's current episode reference and returns an unrestricted signed tangent
reaction. An open cell has zero tangent reaction.

The fixture-only carrier stiffness is

```text
K = [[ 20,   5, -3,   0],
     [  5, 100,  0, -10],
     [ -3,   0, 30,  -4],
     [  0, -10, -4, 120]] N/mm
```

It is symmetric and strictly diagonally dominant with positive row margins
`(12, 85, 23, 106) N/mm`, so the stated certificate establishes positive
definiteness. The nonzero tangent/normal block is part of a numerical carrier
device. None of its values is a candidate, frame, connection, or floor
parameter.

For each of the four masks, the verifier solves the coupled equilibrium and
active stick constraints together. Trial bearing cells add the normal penalty
term to the carrier matrix; trial open cells have no contact reaction or
constraint. A branch passes only when bearing gaps and normal reactions have
the correct strict signs, open gaps are nonnegative, active tangent positions
match their episode references, and the complete four-coordinate force
balance closes. No branch is removed before its computed state and rejection
reason are saved.

Each stage's external vector is frozen in [fixture.json](fixture.json).
That input gives the scalar `Kq` and `W = Kq - contact` arithmetic explicitly.
The solver checks those handwritten load oracles, then uses the recorded
external vectors directly; it does not generate loads from the expected
states. SHA-256 pins preserve the predecessor's two-cell coupled-stick
README/input and the exact new matrix/load input.

The reset rule uses the preceding recorded open-stage tangent positions. It
does not locate first contact under continuous load evolution or establish a
full-frame loading path. The separate [parent elimination
record](parent-elimination-check.json) documents the independent 16-branch
check and a separate frozen cycle-11 input with 100 normal ownership rows
paired with 100 assumed-no-slip tangent ownership rows. A naive enumeration
of the 100 normal states alone has `2^100` masks; this small fixture does not
establish a whole-frame selector or resolve that scaling dependency.

## Limits and reproduction

This fixture verifies state selection only for its four prescribed stages.
The actual source-case corner boundary forces for `BG001`, `BG003`, and
`BG045` remain missing, so it supplies no corner demands. The fixture does not
assign floor friction, anchorage, stiffness, or resistance. It has one tangent
axis per cell and establishes no native solver API, three-dimensional body
mapping, frame stability, floor behavior, hardware behavior, design
acceptance, or climber rating. No native solve, CAD operation, or mesh run was
performed.

Reproduce the KKT solve and exact observed-record check from the repository
root with:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/conditional-floor-structural-coupling-fixture-attempt01/verify_fixture.py --verify
```

Reproduce the parent's independent elimination check from the repository root
with:

```sh
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/conditional-floor-structural-coupling-fixture-attempt01/parent_check.py
```

## Source pins

| Source | SHA-256 |
|---|---|
| [AGENTS.md](../../../../../AGENTS.md) | `672203b929d51d340d39d770e71dd43b019794ea33172bc9f4f7be469fc20536` |
| [Prior two-cell coupled-stick README](../conditional-floor-two-cell-coupled-stick-fixture-attempt01/README.md) | `2882f420b8b8bda0db5677aacfae0682407394e6aa13740af7ea6946c96c2c37` |
| [Prior two-cell coupled-stick input](../conditional-floor-two-cell-coupled-stick-fixture-attempt01/fixture.json) | `c4fbb8b9c1d87ddba3b848c113bda540945b67a3d0d9435150a5c5e1d195de31` |

The local files are integrity-pinned in [SHA256SUMS](SHA256SUMS).
