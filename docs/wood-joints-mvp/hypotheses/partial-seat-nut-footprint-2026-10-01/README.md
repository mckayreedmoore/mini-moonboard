# Partial-seat nut projection check

**Checked:** 2026-10-01. **Disposition:** one conditional projection is
contained; one enclosing projection reaches the service passage. This is a
finished-solid geometry calculation, not an accepted contact footprint,
washer capacity, or joint.

## Question and frozen inputs

The affected outer nut seat is `center_principal_right_2` on
`base_principal_center_right`, in candidate
`compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`. The
[complete outer-seat screen](../remaining-candidate-washer-seats-2026-10-01/README.md)
found that its washer annulus intersects the retained F1/G1 service passage.
This calculation asks whether two explicitly different nut projections also
reach that passage. It preserves all 92 candidate axes and makes no model or
hardware change.

[The checker](check_footprint.py) authenticates the shared seat method,
candidate, revision, axis partition, hardware inputs and finished STEP. It
parses the hash-pinned kerf-right passage record
`bore_base_principal_center_right_072`, then binds its member, datums, axis,
radius and axial extent to the actual cylindrical STEP face. The face spans
X = 50.95 to 89.05 mm. The passage radius is 19.05 mm; its center is
25.6098763474 mm from the bolt axis in the seat plane. The nearest passage
edge is therefore **6.5598763474 mm** from that axis.

The conditional dimension inputs come from the
[reviewed bearing-face source trace](../washer-bearing-footprint-inputs-2026-10-01/parent-review.md):
1/4-in regular hex nut maximum across flats 0.438 in, maximum across corners
0.505 in, and a body-to-thread true-position diametral zone equal to 4% of
maximum across flats. These are traced standard dimensions, not an observed
delivered nut. The B18.2.2 source is a full-text transcription rather than an
authenticated publisher PDF; the source note records that limit.

## Calculation and result

The declared bolt body is 6.35 mm in a 7.30-mm modeled bore. Conditional
radial body play is 0.475 mm. Half the nut true-position zone adds
0.222504 mm. Both scenarios assume the nut thread axis coincides with the
bolt axis. A centered enclosing disk adds those two offsets to the scenario
radius. The test removes the bolt's own timber bore from the disk, then
checks the remaining material against the finished solid at inward depths
0.01, 0.05 and 0.10 mm. The same depths check outward solid occupancy.

| Explicit scenario | Shape radius (mm) | Enclosing radius (mm) | Passage clearance budget (mm) | Minimum inward support fraction | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| Declared flat circular end face, diameter equal to maximum across flats | 5.562600 | 6.260104 | +0.299772 | 0.999999999999936 | Enclosure contained outside the own bore |
| Disk enclosing the complete hex silhouette in every orientation | 6.413500 | 7.111004 | −0.551128 | 0.985094249081212 | Enclosure reaches the service passage |

Outward overlap is zero for both scenarios at all three probe depths.
The returned status is `PROJECTION_ENCLOSURE_EXCEPTIONS`, with one of two
projection enclosures contained. Exit status **1 is expected** for this
result; it reports the geometric enclosure exception rather than a failed
strength criterion.

The circular scenario is an explicit idealization. A standard's chamfer-circle
dimension does not establish a centered flat pressure patch or its complete
transition geometry. The across-corners disk is a conservative enclosure,
not occupied hex material or loaded bearing material. Failure of that disk
to fit does not prove that the actual nut face lacks support. Conversely,
the smaller circular scenario's success cannot be transferred to the whole
hex body or to an unestablished bearing patch.

## Reproduction and record

From the repository root, with the existing CadQuery environment:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/partial-seat-nut-footprint-2026-10-01/check_footprint.py --check > /tmp/partial-seat-nut-footprint.json
```

The parent run used that command and returned the expected exit status 1.
Ruff passed. Raw output remains local; this packet publishes code and the
summary above.

| Record | SHA-256 |
| --- | --- |
| Checker | `6c67a2fddc01c9fc65d27a55b0f242c96015408509b842f52c6a595bef8ee3b1` |
| Parent raw JSON | `16c5c06a1be0e5cd00df960d903bf2fbe02d99b8630f1958d69e11c41637ce4b` |
| Finished member STEP | `9053a7210a781e919038a4a823f867325dd5c78907bd028d8b9e76dc0b46df58` |
| Kerf-right passage source | `5c86941458a6a92432941fdf7e13b2b21ef2f933332e0e1ec602d4d57796f15f` |
| Shared seat checker | `a3cedb8e6fddf9d4080afd82cf12cf3e5a39658868baa478ad1f14eee7d07967` |
| Bearing-face parent source trace | `952b5753823048135822985659e8c0150602dd534f005564233fe957e2b291be` |

The raw output additionally records all authenticated upstream input hashes
and the measured passage face bounds. See the
[independent review](independent-review.md) for the separate check.

## Remaining resistance work

The washer's outer annulus remains partially supported. This result supplies
two geometric scenarios for later contact and plate analysis; it supplies no
metal bending, pull-through, wood bearing, pressure distribution or complete
joint resistance. Thread-fit translation, minimum delivered shank, tilt,
seat tolerances and a face-profile bound remain outside this calculation.
The nominal CAD bore is not a drilling instruction, and no physical part or
wood cut was inspected. No native solve, fabrication, drilling, candidate
selection or climbing release is authorized by this packet.
