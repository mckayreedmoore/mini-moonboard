# Current outer base-angle resistance checkpoint

The two current ML24Z angles have a useful conditional directional reference,
but **their adequacy is not established**. Current joint force and moment demands
are unavailable. Neither the earlier gusset forces nor rigid-floor equilibrium
witnesses represent these new connections.

The installed geometry matches a bearing-installation analogy: the rim end
rests on the header, with the angle on the rim's side. Interpreting the
manufacturer's arrows in this orientation gives the following per-angle limits:

| Applied rim force direction | Letter direction | Conditional DF/SP reference |
| --- | --- | ---: |
| Either direction along world Y / bracket bend | F1 | 2,646.69 N |
| Outward across frame width, away from angle face | F3 | 2,001.70 N |
| Inward across frame width, toward angle face | F4 | 3,336.17 N |
| Vertical uplift from header | F2 | Not listed for bearing installation |
| Downward into header | Wood bearing | Separate timber/contact check |

These are a geometric interpretation and conditional reference values, not
manufacturer approval of this climbing frame. The [manufacturer's supplemental
letter](https://ssttoolbox.widen.net/content/iczmiabsx6/pdf/L-C-MLZ25.pdf), dated
December 23, 2025 and valid through December 31, 2027, was downloaded again and
its bearing-installation drawing inspected on September 11, 2026. Its byte hash
matches the existing reference record. It specifies six SDS25112 screws per
ML24Z, provides no duration increase for these single-angle values, and calls
for consideration of reinforcement when cross-grain bending or tension cannot
be avoided. The [2026 catalog, page 323](https://ssttoolbox.widen.net/content/wrzfhjzbna/pdf/C-C-2026-p323.pdf)
also requires the specified fasteners and directs lateral-load questions to
the supplemental letter.

The inspected ML letter supplies no simultaneous-direction interaction equation
or independent moment rating. The screen therefore returns **unassessed** for
mixed-axis force, applied moment, uplift or downward bearing demands. It does
not borrow uplift values from a different installation table or multiply two
angle capacities into a frame capacity. Even a single-direction comparison below
a listed value retains all design-qualification flags as false.

The numerical probes use 1,000 N separately in six world directions at each
angle. They verify direction mapping and comparison behavior; they are not
predicted frame reactions. Product, lumber, installation, timber edge/end
resistance and service conditions still require their own checks.

The next required calculation is the current rim/header interface wrench under
an independently checked frame load path, including compression-only bearing,
connector slip and plausible load sharing. If that calculation produces uplift,
a substantial connection moment or simultaneous components, an applicable
manufacturer-supported connection model or another detail is needed before a
strength verdict. Enlarging the timber alone does not fill those missing
connection directions.

The published v1 screen remains a historical record of the angle-base variant.
Its replay test authenticates every recorded source file, requires that the
current provenance contains every original path and digest, and checks that
the current tree produces identical engineering results and qualification flags.
Later variant modules expand the generator's package-wide provenance inventory;
they do not retroactively become inputs to the original record.

```sh
uv run pytest tests/test_angle_base_connection_screen.py -q
uv run python -m fea.angle_base_connection_screen --output /tmp/base-angle-screen.json
```
