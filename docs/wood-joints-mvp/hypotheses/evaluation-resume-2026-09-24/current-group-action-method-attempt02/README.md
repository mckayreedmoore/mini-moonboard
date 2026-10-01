# Current group-action method — attempt02 fail-closed patch

Status: **isolated candidate patch; not applied to the maintained evaluator**.
This attempt narrows the method to its tested one-to-three-total-member
scope. It does not implement a four-plus-member plane method, emit a current
group factor, compute a capacity, or change a criterion disposition.

## Change proposal

The exact patch is in [`four-plus-fail-closed.patch`](four-plus-fail-closed.patch).
It changes exactly two maintained files if later adopted:

- `mini_moonboard/nds_2024_group_action.py`: after the payload's member
  inventory and shear-plane count are validated, return `pending` with
  `four_or_more_member_plane_method_not_source_bound` whenever the payload
  has four or more total members (`1 + len(side_members) >= 4`).
- `tests/test_nds_2024_group_action.py`: add synthetic, source-bound four-
  and five-member cases and require the pending result to contain no `Cg` or
  capacity.

The existing one-side-member (two-total-member) and two-side-member
(three-total-member) behavior is unchanged. The existing two-plane synthetic
test remains a regression for that supported scope. The four-member even
case and five-member odd case both fail closed. The patch adds no stack
geometry schema, adjacent-plane interpretation, candidate payload, or
mechanics result.

## Source decision

The companion [multi-shear source audit](../current-group-action-multishear-audit-attempt01/README.md)
pins official 2024 NDS Chapter 11, Chapter 12, and current consolidated
errata. The normative §11.3.6 text defines an aggregate `A_s` and permits
single or multiple shear but does not expressly resolve a special four-plus
`Cg` procedure. Official current Commentary C11.3.6 was not obtained or
bound. The current §12.3.8 even/odd member resistance procedures are not a
substitute for that missing `Cg` interpretation. Thus the patch makes the
uncertain four-plus path pending rather than claiming either an aggregate or
plane-by-plane result is authoritative.

This is a scope guard, not a four-plus-member engineering conclusion. A
later method attempt can replace the guard only after the official current
Commentary/source is pinned, plane membership and adjacent-member sections
are independently bound, and the combination of plane-specific `Cg` with
§12.3.8 is resolved. Attempt01 and all parent acceptance files remain
untouched.

## Isolated validation

The patch was applied only to a fresh temporary copy of the pinned module
and test file, then the full focused suite was run there:

```text
patch -p1 < four-plus-fail-closed.patch
.venv/bin/pytest -q -p no:cacheprovider tests/test_nds_2024_group_action.py
29 passed
```

The temporary copy produced a clean patch application with no fuzz. The two
new parameter cases (four total members and five total members) assert:

```text
status = pending
reason_codes includes four_or_more_member_plane_method_not_source_bound
cg = null
capacity = null
criterion_disposition = pending
```

The preexisting single- and three-total-member regressions still pass in the
same 29-test run. No full repository suite, candidate evaluator, native
solver, or current joint was run for this patch. The maintained source and
attempt01 hashes were rechecked after the temporary validation and remain
unchanged.

## Limits

The patch does not settle the current 2024 Commentary interpretation, does
not calculate any plane-specific factor, and does not imply that any actual
connection passes or fails. It only prevents unsupported four-plus use from
being reported as calculated by this method until the applicability gate is
resolved from a bound current source.
