# Conditional stitch and gusset bolt reference values

The current two-member stacks now have reproducible single-fastener lateral
reference calculations. They are **not adjusted connection allowables** and
cannot yet be compared to a qualified individual-bolt demand.

| Family | Modeled member lengths | Conditional reference per bolt | Governing yield mode |
| --- | --- | ---: | --- |
| Six leg-ply stitches | 19.05 + 19.05 mm | 115.21 lbf / approximately 512 N | II |
| Eight base-gusset bolts | 38.1 + 19.05 mm | 138.20 lbf / approximately 615 N | II |

## Explicit assumptions

- Use 0.298 inch throughout for both bearing and bending diameter, including the
  stitch bolts. This is the typical 3/8-inch bolt root diameter in
  [2024 NDS Appendix L, Table L1, p.191](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf),
  not a measured minimum for the delivered bolts. Actual thread geometry and
  tolerances remain to be verified.
- Use conditional Fyb=45,000 psi and moment `Fyb × Dr³ / 6`. Appendix I Table I1
  gives that reference for its described bolt material basis. This calculation
  does not establish that the selected A307 product has all those properties;
  do not substitute tensile ultimate strength for a verified bending basis.
- Use plywood Fe=5,600 psi from the [TR12 basis](plywood-bolt-resistance-basis.md).
  For the timber side, retain 3,650 psi as a deliberately low directional input
  associated with nominal 3/8-inch DF-L perpendicular bearing; do not increase it
  for the smaller root diameter or more favorable grain direction in this screen.
- Use Kθ=1.25 for all rows: reduction terms 5 for Im/Is, 4.5 for II, and 4 for
  IIIm/IIIs/IV. No favorable plywood direction is presumed. These conservative
  directional choices do not cover unrelated material or connection limit states.
- Model zero gap, with individual lengths recovered from current part-local
  geometry. Include no adhesive, friction, composite-ply or axial resistance.

The Appendix PDF inspected locally has SHA256
`99b0a54e7133b3cf6dd156d8fe864c1717c951487bf5baa99c34da9a68a6bbb7`.
No PDF is redistributed.

## Reproduction and decision boundary

`fea.two_member_yield.build()` authenticates the thread-exposure source geometry
and returns all fourteen named rows, member identities, calculation inputs and
six mode values. The independently benchmarked TR12 kernel performs the arithmetic.

```sh
uv run pytest -q tests/test_two_member_yield.py tests/test_bolt_thread_bearing.py tests/test_dowel_yield.py
```

Do not multiply these values by bolt count to claim a group resistance. End-use
adjustments, group effects, spacing/edge/end geometry, member splitting and net
section, washers, preload and combined lateral/axial loading remain open. The
three-member leg/rim joint is excluded. The next demand comparison must distinguish
gusset-group force/moment distribution and differential leg-ply transfer; neither
is supplied by the existing aggregate frame reactions.

No hardware or frame geometry is changed by this calculation. Keep the present
joint selections provisional pending those checks.
