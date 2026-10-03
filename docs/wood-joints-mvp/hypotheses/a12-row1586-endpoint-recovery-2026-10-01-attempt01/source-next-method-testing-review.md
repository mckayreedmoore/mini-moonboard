# Independent testing review: A12 source-only next method

**Disposition: PASS for the bounded saved-arithmetic replay and host/source
formatting preflight.** The checks reproduce the packet's arithmetic claim and
show that the proposed precision-only patch applies to its pinned upstream
source. They do not test a CalculiX build or prove that serialization caused
the A12 force discrepancy; no case, interval, or acceptance result changes.

## Frozen evidence and reproduction

The current A12 packet README and `output-pin.json` match the stable hashes
`028f9fbd6f8c5c514f3ab08e5113b445681c5cd2445f9ae00e20977b7a92553f` and
`d70466693a8bad39c2acffa42fb465d733a8060c5faffb50f8da781bb65b9de8`. The
precision preflight README and `source-pins.json` match
`711f1d71a3ad992d92df81f2e0be8a2db45bd9d32d04c5e0253ea4fcd3d02989` and
`1cc174760cb658614431a75532fcd0603342b6e1559ebc0df935be6310e65981`. All 19
distinct path/SHA records in the precision pin file matched; I separately
rechecked its five local preflight pins. The three A12 output-pin files also
matched their recorded hashes.

I reran the saved-data audit with its report directed to `/tmp` and ran Ruff
on the checker. Both passed. After removing the intentionally variable
`elapsed_seconds`, the replay report matched the retained
`arithmetic-result.json` exactly. Its terminal status is
`PASS_ARITHMETIC_ONLY_RF_MISS_RETAINED`; counts remain zero for native runs,
source-K factorizations, source states and `.sti` triplets, with
`sti_bytes_read: false`.

The synthetic 100 mm / 0.00001 mm transverse-offset known answer passes its
rationalized-length identity with `1.61e-98 mm` reported identity error. For
saved row 1586, the binary64 source-order mirror reproduces
`0.0036339103697834957 N`; high-precision arithmetic on those same rounded
endpoints gives `0.0036339103661339461 N`, only `-3.65e-12 N` different. The
recorded half-ULP scale is `5.65e-11 N`, about 1,576 times smaller than the
unchanged `8.90e-8 N` gap above the native RF interval. That comparison is
limited to endpoint norm/subtraction arithmetic and is not a total force-error
bound. The RF interval still fails, and the pinned raw-H comparison retains
all 27 source-force interval failures as STOP.

## Formatting check and patch applicability

Using the documented GCC flags, I compiled and ran `roundtrip.c` in a unique
`/tmp` directory. It passed all 16 exact 17-significant-digit round trips;
eight values changed at 14 significant digits. For adjacent binary64 values
around 100, the old-format subtraction collapsed to zero, while the 17-digit
round trip preserved the original `1.4210854715202004e-14` delta.

The pinned CalculiX source archive and `matrixstorage.c` member hashes matched
the preflight pins. A dry run of `precision-only.patch` succeeded against that
member in `/tmp`. Applying and reversing it there changed only the `.sti`
`f2` writer token from `%20.13e` to `%20.16e` and restored the original source
bytes; the `.mas` `f3` writer remained `%20.13e`. No repository source was
patched.

These checks establish host `snprintf`/`strtod` behavior and patch applicability
only. They do not execute the actual CalculiX writer or its linked C library,
build a solver, export or parse a matrix, or verify a candidate response. The
preflight's separate free-solid coupon and oracle remain the necessary gate
before anyone considers a separately identified patched build or candidate
export. The precision proposal therefore supplies no evidence that explains
the RF miss and does not change the 27 STOPs or any interval.
