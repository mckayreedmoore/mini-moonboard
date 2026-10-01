# Parent-owned native run ledger

The coordinator uses [`luna-max-native-run-ledger.json`](luna-max-native-run-ledger.json)
to serialize native work and preserve one-run limits outside deletable attempt
packets. This ledger supplements each attempt's own runner guard; it does not
create readiness or authorize a solver launch.

The ledger now records the historical T02 r5 exact-touch coupon attempt01 as one consumed failed launch (Docker exit 139), imported from its immutable execution record. That old freeze used an obsolete patch and binary and cannot be reused. The T03 `shared_slave_penalty` coupon attempt07 remains bound to its exact input-freeze digest, unreserved, and at zero consumed launches, with false parent-readiness and native-authorization gates. On 2026-09-29 UTC, Docker access and the exact upstream CalculiX base image were revalidated.

Before a future launch, the coordinator must revalidate the freeze and reviews,
confirm the pinned runtime, establish fresh parent readiness and the exact
run-specific authorization receipt, and persist a consumed ledger entry with
the authorization digest before invoking Docker. A failed or interrupted
launch remains consumed. The coordinator must never decrement the run count or
reuse the run ID; later coupons and cases require distinct frozen inputs and
distinct ledger entries. Only the coordinator may reserve the single native
slot and launch a run.

This is an operational execution control only. A passing method coupon does
not establish joint response, a capacity, a criterion disposition, or release.
