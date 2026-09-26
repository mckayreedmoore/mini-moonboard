# Independent review: contact-storage upper bound

The frozen endpoint audit’s pairwise storage upper bound is numerically
consistent with the source-selected face-to-face contact integration scope.
It shows that the represented LINEAR contact springs cannot supply all of the
work-required contact term at `.020 s`; it does not identify the remaining
energy difference’s cause or establish acceptance.

The reviewed producer, result, and parent reproduction pins are:

- `analyze_contact_storage_bound.py`: `426fc93b40f501515b2f74635a4cc87d97344767104975219051ed55465e6e3d`
- `contact-storage-bound.json`: `909deb3929b6c97d0889363eae1fb8726a22c7e35ca975f4295ab91e79f38f16`
- `parent-validation.json`: `0515b6e8ff2add30cc982cf489073130e20ecd59812fe5ccb7ba76f644e0b483`

The result binds the immutable non-atomic snapshot (`18fac09d22a3b2caab941ad0aa81ff5533d1c60f193a96ae13b39b908407d46e`), DAT (`0adf58de363e4b08483134802ebd61a493b5373d14bdfe48333ba1c58d4c04f4`), LOG (`bcde2b262d1ade3d2ad25f4df9409128d5de93cbb3cec299112db4c9fd9aabc4`), STA (`343cc6f488f9d9f5fb0950d74d317a50313bf34495ac4d3232e0a94894d3285c`), and current `pilot.inp` (`a9f891c92fed7eaa7e3b78f0656c5829d330a28a3df450ea7128b9ea52eb49c4`). Its first 20 DAT/LOG/STA states are byte-identical to the prefix used by the independent work audit. That audit’s `.020 s` discrete work is `5.891621650386964 N·mm` versus native LOG external work `5.891622 N·mm`; the difference is within the native half-print quantum `5e-7 N·mm`.

The frozen contact fragment contains 35 `SURFACE TO SURFACE` pairs. I checked each pair against the ordered manifest and the DAT headers at both endpoints: `WJCP_001_S/WJCP_001_M` through `WJCP_035_S/WJCP_035_M` match by index, and each endpoint has three area-bearing reports for every pair. All `.019 s` rows (`108,297`) and `.020 s` rows (`72,155`) match `CNUM` for both `CDIS` and `CSTR`; every element/face row maps once to a frozen slave surface and then to a manifest pair. The `.020 s` result includes 72,046 compression/overlap rows and all 109 small opening/tensile-residual rows in its absolute-product bound.

The positive-area selector argument checks out for the pinned upstream CalculiX 2.21 source archive (`52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad`). The verified path is `precontact.c` → `slavintpoints.f`/`faceinfo.f` for the C3D10 six-node face → `shape6tri` → `treatmasterface`. The clipped triangle area uses an absolute determinant; all seven `weight2d6` quadrature weights are positive; `gencontelem_f2f` multiplies by a Jacobian norm and stores the nonnegative result in `springarea`; and `printoutcontact` sums those same areas. The direct `faceinfo.f` hash is `3c4c454c4be4286fa90a8acd93cbf8070177f5776bc226edb75f1658cdbf4041`. I verified the current file matches this hash. The executable result’s source-file list omits `faceinfo.f`, so this direct hash is documented in the README and here rather than enforced by the producer itself.

At `.020 s`, the pairwise upper bound is `0.287187281868343124666393125 N·mm`. The LOG values give
`E_required = external_work − internal_energy − kinetic_energy = 0.4664306 N·mm`, with a printed interval of `[0.46642955, 0.46643165] N·mm`. Subtracting the upper contact bound from the lower required value leaves at least `0.179242268131656875333606875 N·mm` outside this contact-storage envelope. The native elastic contact energy (`0.001345491 N·mm`) is not subtracted again when forming `E_required`; doing so would count it twice. Half-last-digit uncertainty is propagated for pressure, clearance, positive pair area, and the LOG energy fields. Pair maxima times summed area are conservative even though the individual spring area is not printed beside every contact row; no exact integration is claimed.

The source archive does not establish bitwise identity with the packaged solver binary (`6adaabf5bf0382fc2bfd692b984320ed375dba777f7dc8297562f818043faa1b`). The source-based energy interpretation is therefore conditional on upstream 2.21. The actual printed fields separately satisfy `pressure = -10000 × clearance` within their print quanta. The audit covers only these two endpoint states and the modeled LINEAR contact storage. It does not establish numerical dissipation, explain the balance residual, bound between-step evolution, or accept a joint.
