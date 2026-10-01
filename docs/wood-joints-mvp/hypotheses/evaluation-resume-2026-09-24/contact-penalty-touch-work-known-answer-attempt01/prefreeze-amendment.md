# Prefreeze contract amendment

This note records a bounded correction to the initial preparation before any
freeze or native run. The output deck and prescribed five-state schedule are
unchanged.

The original prepared hashes were:

- `prepare.py`: `4fac64dd4225c1a6f55696ae1996f0ead18a173eb0356352073410a27a551cc6`
- `README.md`: `01d8745da590e2fd974d2502b16a96a0657f36767ca86ba685df31183f89238d`
- `expected.json`: `4f4d73fd829fcb6d3bf0801dc5b2d1c0d3607c3a361630654cdc5df32df2ab7a`
- `preparation.json`: `35c689dfc748fd5b02e474179b8ef627507915cf17254f94e91196823016f939`
- `input/penalty_touch_work.inp`: `fffe98b9992ce22a7f9447d423be2fe9f7cf183066ef3f1d9c50b5a295888a0c`

The contract now predeclares the compression origin-moment oracle for `CF`,
`CFN`, and `CFS`, with a stated tolerance, and binds the inherited mechanical
profile, force, compliance, direct-step, full-mesh trace, and section-output
gates to the passing penalty record in
`contact-section-force-known-answer-attempt02`. Its exact frozen history and
predeclared tolerances are pinned in `expected.json`. This closes two review
gaps: the first contract did not give an explicit moment target, and it did not
bind the inherited mechanical gates to their source contract. No physical
model, displacement schedule, base output request, or input deck changed.

The revised `expected.json` and `preparation.json` hashes are recorded in the
current preparation files and parent review; the unchanged deck retains the
hash above. This remains preparation only, with execution and acceptance flags
false.
