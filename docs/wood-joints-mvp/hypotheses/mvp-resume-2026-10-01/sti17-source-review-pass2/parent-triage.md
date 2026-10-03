# Parent disposition of resumed STI17 review pass 2

All three roles authenticated target
`c20fba495d8d025933aa6e2551367df9e570943d1cdc96a98b51bfb6674c3570`
and its 15 inputs. Architecture reported no substantial finding. Correctness
and testing independently identified the same review-file race. Their
original reports, target and input archive are preserved.

The parent confirmed and fixed the race: the launcher now parses one review
byte snapshot, retains its digest, requires those same bytes under the ledger
lock before reservation, and records the retained digest. A test replaces the
review during Docker preflight and verifies refusal without a ledger row.

Correctness's memory-plus-swap finding is also confirmed. The coupon command
now sets `--memory-swap=2g` alongside `--memory=2g`; the binary/utility probe
sets both to 256 MiB. The result checker and command tests require the exact
coupon swap ceiling.

The three role keys alone did not prevent repeated reports. The source-review
binding now requires distinct report paths, hashes and parent-recorded actual
reviewer identities. The synthetic test explicitly rejects reusing one role's
report for another role. These identities are metadata, not an independent
authorship attestation; parent still verifies tool assignments and reads all
three results before readiness.

Focused source checks pass 27 tests, 48 subtests and Ruff. A fresh final
three-role source review follows. No build, new image, coupon freeze or native
execution occurred during these fixes. All 47 criteria remain pending, the
original A12 STOP is preserved and physical release flags remain false.
