# CalculiX 2.23 matrix output precision preflight

This is a source-only proposal plus a standalone host-C formatting check. No
CalculiX source was patched, no solver was built or run, and no `.sti` or
candidate matrix was read/exported.

## Exact proposed edit

The only source change proposed against the pinned upstream
`CalculiX/ccx_2.23/src/matrixstorage.c` is the line-304 stiffness (`.sti`)
edit in `precision-only.patch`:

```diff
-    fprintf(f2,"%" ITGFORMAT " %" ITGFORMAT " %20.13e\n",ai[i],aj[i],aa[i]);
+    fprintf(f2,"%" ITGFORMAT " %" ITGFORMAT " %20.16e\n",ai[i],aj[i],aa[i]);
```

`%.13e` writes 14 significant decimal digits; `%.16e` writes 17, enough for
binary64 round-trip. The minimum field width remains 20. The second writer at
line 543 writes mass (`.mas`) with `%20.13e`; that 14-significant-digit format
is deliberately unchanged. The source archive is
SHA-256 `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`;
the untouched writer member is SHA-256
`2b2a502637761a7663e50e43a7f5afe9322c6c775aa6c44fd7b433976bbe59c4`.
Its writer emits upper-triangle indices and `aa[i]`; this proposal does not
change assembly, storage, indexing, solver tolerances, material data, or
element calculations.

The current recipe is `fea/calculix_223/Makefile.upstream` (SHA-256
`57a25e08a51bba3897cecb3c03e45f7cf602d9c28a15c12e45d9b1ddebcad0bf`):
`gcc -Wall -O2 -I/usr/include/spooles -DARCH="Linux" -DSPOOLES -DARPACK
-DMATRIXSTORAGE -DNETWORKOUT` for C, and the recorded GCC is
`13.3.0-6ubuntu2~24.04.1`. The Makefile spells `-DARCH="Linux"`; the
recipe shell passes the effective argument `-DARCH=Linux`. The compiler and
flags here test only
`roundtrip.c`; they do not build CalculiX. The existing source archive, image,
binary, profile, and build history remain untouched. The current pinned image
is `sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38`,
and current 2.23 binary SHA-256 is
`c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863`.

## Host arithmetic check

`roundtrip.c` checks 16 exact binary64 values, including positive and negative
zero, positive and negative inputs, adjacent doubles around 100 whose
subtraction is cancellation-sensitive, and stiffness-scale values from
`1e-300` through about `1e12`. It formats/parses each using `%20.13e` and
`%20.16e`, compares raw double bits, and requires the adjacent-value delta to
collapse at 14 digits but survive at 17 digits.

Reproduce without reading solver source matrices:

```sh
gcc --version | head -1
gcc -Wall -O2 -I/usr/include/spooles -DARCH=Linux -DSPOOLES -DARPACK -DMATRIXSTORAGE -DNETWORKOUT \
  docs/wood-joints-mvp/hypotheses/ccx223-matrix-output-precision-preflight-2026-10-01/roundtrip.c \
  -lm -o /tmp/ccx223-matrix-output-precision-roundtrip
/tmp/ccx223-matrix-output-precision-roundtrip
```

Expected result: `PASS values=16 exact_17_digit_roundtrips=16`, with a zero
14-digit adjacent-value delta and a nonzero 17-digit delta equal to the
original binary64 subtraction. This tests host `printf`/`strtod`, not the
CalculiX process or its linked C library.

## Smallest retained free-solid coupon with an independent oracle

Before any candidate matrix export, use the already-retained single free
C3D20 unit-cube coupon
`mvp-acceleration-2026-09-28/current-native-elastic-operator-export-preflight-attempt01/coupon-free-c3d20-matrixstorage.inp`
(SHA-256 `e128a62f899c90965fd68be09a7362ed836a30ff6b1c3f1c6dc0581e118b79fe`)
with its existing independent checker
`matrix_export_oracle.py` (SHA-256
`17a908d1283f676df7af97511ef2ecd3c794b98c6b81dc50e2a6f14cec57b79a`). Its
analytical answers are `U = 1/2·G·gamma²·V = 2.0e-5 N·mm` for
`E=1 N/mm²`, `nu=0.25`, `gamma=0.01`, `V=1 mm³`, and `m_x = rho·V = 1` for
`rho=1`. The checker also requires the complete 60-DOF map, unique triplet
pairs, six rigid modes, and no negative modes. Preserve that deck and checker
byte-for-byte.

Any later serialized discriminator needs a newly named image/build identity;
the current `build.py` deliberately refuses to overwrite its existing 2.23
tag. Require the exact pinned archive/member, a patch dry-run plus byte-level
diff proving that only the one format token changed, unchanged numerical
source/build flags, and preservation/hash checks for the old profile and
binary. Record the new image, binary, compiler, source, deck, checker and raw
output hashes in a separate profile/receipt. Run only the existing coupon,
serially, at one CPU, at most 2 GiB and at most 60 seconds; stop on any identity,
format, map, analytical-oracle, or completion failure. Require `.sti` value
tokens to have 16 digits after the decimal and parse finite. Confirm `.mas`
retains its baseline 13 digits after the decimal; it is not the target of this
patch. Then run the pinned coupon oracle. Only after that passes may a parent
separately review whether a candidate export is warranted. This document does
not authorize that run.

The precision change may fail to explain the A12 RF discrepancy. The retained
row-1586 result is method pass / RF miss: the unchanged interval miss is
`8.903346377e-8 N`, while recovered table force differs from raw-H force by
`6.173096500e-10 N`. No unformatted global operator or rowwise export-error
bound is retained, and native and recovered states use distinct operators.
This proposal changes no source load, model, interval, solver tolerance,
result classification, or acceptance claim.
