# Upper-left compatible block component replay

The completed [common-cleat calculation](upper-left-block.md) supplies
all four actual left bolt responses in the six current nominal-gap cases.
This replay applies the existing finished wood-path, single-shear, supported
annulus and conditional smooth-bolt references to those new individual
responses. No right-corner force or acceptance is transferred.

| Component screen | Maximum index | Governing state / bolt |
| --- | ---: | --- |
| Single-shear lateral / adjusted reference | 0.722296 | A12-left, side 2 |
| Parallel component / declared finished tangent path | 0.142295 | A12-left, side 2 |
| Full-annulus mean washer pressure / `Fc_perp` | 0.667024 | A12-left, rail 1 |
| Smooth-shank beam VM / conditional 92 ksi | 0.275588 | A12-left, side 2 |

The 24 bolt states retain actual left grain axes, rail bearing lengths
38.1/139.7 mm, side lengths 88.9/88.9 mm, the original rail `Cg*Cdelta`
multiplier and both possible signed finished paths. Mean washer pressure
uses the unchanged supported minimum annulus. The original mean index
0.717681 decreases to 0.667024 under the compatible local allocation.
The steel proxy includes the pair's beam bending and remains conditional
on the recorded smooth-shank and 92 ksi assumptions.

These component indices do not constitute combined oblique-group or
splitting acceptance. The original complete-host cut records are included
for geometry/scope only: preserving each group wrench does not prove that
all cuts inside the redistributed group retain their old demands. The
characteristic splitting equation is not silently converted to a design
resistance. Spring pressure peaks are diagnostic contact-law outputs, not
adopted local bearing utilizations. Actual washer/head/nut resistance and
elastic cleat interaction remain open.

Joint qualification and physical release remain HOLD. No geometry, purchased
hardware, current full-frame load, formal criterion or authority flag changes.

## Reproduction

Use a new output path:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
uv run --no-sync python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/upper-left-block-components.py \
  --source docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/upper-left-block/attempt01/checks.json \
  --source-sha256 5e8c52e529f58f9276c4c67f554fa0b74a990dd501e347e59434aa244e628ed0 \
  --output /tmp/upper-left-block-components-fresh
```

The producer authenticates the left result and its complete source closure,
the component geometry and the unchanged single-shear implementation. It
performs arithmetic only: no native/frame/CAD operation, software test or
review loop. Ignored `rawlocal/upper-left-block-components/attempt01/`
contains the producer snapshot, result and exact source/output receipt.

- Left mechanics: `5e8c52e529f58f9276c4c67f554fa0b74a990dd501e347e59434aa244e628ed0`.
- Component result: `25f0bb27a752f68d28ededb97017b1675d47751f44922d95d021d1b91e096420`.
- Original component geometry: `401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6`.
