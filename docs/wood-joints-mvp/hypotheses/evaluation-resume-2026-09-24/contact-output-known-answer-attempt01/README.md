# CalculiX 2.23 contact-iteration output check

## Decision and known answer

Check that the pinned 2.23 solver accepts `LAST ITERATIONS,CONTACT ELEMENTS`
on `*CONTACT FILE`, writes the documented iteration output, and preserves the
small coupon's baseline solution. The coupon uses two C3D10 blocks with a
frictionless surface-to-surface interface and prescribed top motion. Its
boundary values are frozen in `model-context.json`.

The baseline and instrumented decks are byte-identical except for adding those
output parameters. This checks output instrumentation only; it does not
qualify the full joint's contact response or capacity.

## Source

Inputs and hashes are in `input-freeze.json`. The pinned primary source is the
[CalculiX 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf), pp. 435–436.
It describes `CONTACT ELEMENTS` as per-iteration contact-element output and
`LAST ITERATIONS` as nonconverged displacement output.

## Execution and limits

Run baseline, then instrumented, serially with the image and executable in
`input-freeze.json`. Compare accepted displacement and contact outputs. Check
that CEL iteration sets align with `.cvg` counts. The generated sets identify
contact-element topology; they do not report per-pair force or establish a
joint response.

## Result

Both 2.23 jobs completed normally in under one second. The accepted `.sta`,
`.cvg` and `.dat` files match byte-for-byte; the `.frd` files match after
normalizing the generated `UTIME` header. The instrumented job produced 16
CEL iteration groups, and every group's element count matches its `.cvg`
record. It also wrote `ResultsForLastIterations.frd`. See `result.json` and
`execution.json` for exact counts and hashes.

This verifies the output writer and output-only equivalence for this small
coupon. It does not qualify the full joint, identify forces for individual
contact pairs, or establish capacity.
