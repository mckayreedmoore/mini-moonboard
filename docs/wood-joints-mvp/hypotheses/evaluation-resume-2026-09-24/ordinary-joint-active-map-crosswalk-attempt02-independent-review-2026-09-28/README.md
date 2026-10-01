# Independent review: ordinary-joint active-map crosswalk attempt02

Review date: 2026-09-28. **Bounded pass:** both attempt02 manifests verify and
the current replay matches its preserved output. The four attempt01 packet
artifacts, all 35 attempt01 source pins, the 14 base-freeze artifacts, the
four A00–A03 joins, port controls, transforms, A00 fixture scope, and A09
no-accepted-increment record agree with the pinned sources. No material
crosswalk discrepancy was found.

The three A00 fixture cases are `direct`, `mapped_no_carrier`, and
`mapped_carrier`; each records ten accepted states. Their scope remains A00
and its optional carrier under the small global-Y rotational body-force
fixture. A09 remains a timed-out static attempt with no accepted increment;
this is not evidence of physical joint failure. T02/T03 acceptance and
release remain open.

Two non-blocking replay coverage gaps remain. First, the replay requires the
crosswalk's acceptance, criteria, and release booleans to be false, but does
not compare those values semantically with the pinned task queue, run ledger,
and readiness records. Manual inspection found the current records consistent:
T02/T03 are waiting, readiness and authorization are false, the T03 launch
count is zero, and release/engineering completion remain false. Second, the
replay checks each case present in the crosswalk against the verifier but does
not require the crosswalk case-key set to equal the verifier's full
three-case order. The present crosswalk contains all three expected cases.
For stronger replay coverage, compare gate flags to their source records and
assert exact case-key equality.

## Reproduction

From the review directory, verify the report and source manifest hashes:

```sh
cd /home/mckay-linux/repos/mini-moonboard/docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-joint-active-map-crosswalk-attempt02-independent-review-2026-09-28
sha256sum -c SHA256SUMS
```

From the repository root, verify the five attempt02 files pinned by this
review's source manifest:

```sh
cd /home/mckay-linux/repos/mini-moonboard
sha256sum -c docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-joint-active-map-crosswalk-attempt02-independent-review-2026-09-28/SOURCE-SHA256SUMS
```

From the attempt02 directory, verify its four payload hashes:

```sh
cd /home/mckay-linux/repos/mini-moonboard/docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-joint-active-map-crosswalk-attempt02-2026-09-28
sha256sum -c SHA256SUMS
```

From the repository root, verify the four attempt01 packet pins:

```sh
cd /home/mckay-linux/repos/mini-moonboard
sha256sum -c docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-joint-active-map-crosswalk-attempt02-2026-09-28/SOURCE-SHA256SUMS
```

Replay to standard output and compare it with the saved output without
overwriting packet files:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-joint-active-map-crosswalk-attempt02-2026-09-28/replay.py | cmp - docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-joint-active-map-crosswalk-attempt02-2026-09-28/replay-output.txt
```

This review also verified that attempt02's replay rechecks attempt01's
`SHA256SUMS`, all 35 attempt01 source pins, the 14-artifact freeze chain, all
seven direct deck includes, map/equation/carrier joins, coordinate and port
arithmetic, the A00 verifier scope, A09 output sizes, and the recorded
unselected/unfrozen follow-on state.
