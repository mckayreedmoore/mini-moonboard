# Half-step contact-storage bound

This audit bounds the storage represented by the accepted native contact rows
at **0.019 s** and **0.0195 s** in the immutable prefix snapshot
[`halfdt-contact-firsttransition-prefix-attempt01`](../halfdt-contact-firsttransition-prefix-attempt01/).
The snapshot contains 34 verified input artifacts and accepted STA rows 38 and
39. It has no accepted 0.020 s state, so this audit makes no claim about that
time.

The producer maps all 35 frozen WJCP pairs and checks complete matching
CDIS/CSTR/CNUM row coverage, including zero-row pairs. It bounds each pair's
linear face-to-face spring storage with printed pressure, clearance, and
positive quadrature area, expanded by their print half-ULPs. It includes small
open/tensile-residual rows in the bound. The area positivity argument is
conditional on the pinned upstream CCX 2.21 source; the packaged solver is not
assumed to be bitwise identical.

| Accepted time | Mapped rows | Active / zero-row pairs | Contact-storage upper bound | `W - U - K` print interval | Remainder after bound |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0.019 s | 108,190 | 19 / 16 | 0.002040291 N·mm | [0.000507365, 0.000509375] N·mm | Not resolved; bound exceeds interval |
| 0.0195 s | 72,043 | 23 / 12 | 0.468718028 N·mm | [0.61099665, 0.61099875] N·mm | At least 0.142278623 N·mm outside this contact envelope |

`W - U - K` is the external-work minus internal- and kinetic-energy quantity;
native CELS is reported separately and is not subtracted again. The second
endpoint's positive remainder is arithmetic relative to the represented
contact-storage envelope only. It does not identify the energy-gap cause,
establish numerical dissipation, demonstrate timestep convergence, or imply
joint capacity or acceptance. Values at these different times are not a
timestep-convergence comparison.

Reproduce from the repository root with:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/halfdt-contact-storage-bound-attempt01/analyze_halfdt_contact_storage_bound.py \
  --snapshot-dir docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/halfdt-contact-firsttransition-prefix-attempt01 \
  --expected-snapshot-sha256 d531ba36a8a6387bc6e12f96fa5093edcf9fde6dd20a12a2bb13b6af9ee9430b \
  --expected-input-freeze-sha256 ea24423f587795743d0c1189c798f77d83159208c76d5d1d3a9fa5554eda4f56 \
  --expected-input-artifact-count 34 \
  --endpoint-time 0.019 --endpoint-time 0.0195 \
  --output /tmp/halfdt-contact-storage-bound.json
```

Frozen pins: producer SHA-256
`a9aed8b5cf381e071fc7fbb06cea7dcf28b87975b9749dea82f3e66a2579be09`,
result SHA-256
`f21d6824334562bd4096a7346a64914387134dabd01f70a857a2f896f2d5db34`,
and snapshot SHA-256
`d531ba36a8a6387bc6e12f96fa5093edcf9fde6dd20a12a2bb13b6af9ee9430b`.
[`parent-validation.json`](parent-validation.json) records an exact parent
replay of the frozen result.
