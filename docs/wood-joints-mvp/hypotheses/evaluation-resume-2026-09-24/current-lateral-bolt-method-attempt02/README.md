# Lateral-bolt input-validation follow-up — attempt02

**Status:** parent-reviewed bounded fail-closed input-validation repair only.
This is a supplement to [attempt01](../current-lateral-bolt-method-attempt01/README.md),
which remains the source and mechanics record for the NDS-2024 method.

An independent audit of the attempt01 API found that an unhashable value
(such as a list or object) supplied as `main_member_id` or `side_member_id`
inside an adjacent-pair role could raise Python `TypeError` during set
comparison. The API contract says malformed inputs raise `ValueError`. The
maintained evaluator now checks that both IDs are strings before comparing
them with the adjacent member IDs. Two regression cases exercise list and
object values and require `ValueError`.

The existing NDS equations, supported member counts, applicability boundary,
input requirements, and current-axis outputs are unchanged. Attempt01's pinned
NDS-2024 Chapter 12, January 2025 Table 12.3.1B erratum, current 2026 errata,
and TR12 example remain the method authority and cross-check basis. The API
still validates the shape of source references rather than authenticating
their underlying physical or external evidence; consuming reviews must resolve
sources and the applicable current errata independently.

Validation on 2026-09-27 (America/Denver):

- Focused method suite: **28 passed**.
- Related lateral-yield and exact47 suite: **76 passed**.
- `py_compile` for the maintained evaluator: passed.
- Exact source and code hashes are recorded in [`terminal-hashes.json`](terminal-hashes.json).

This follow-up establishes no capacity result. All 92 current bolt axes remain
pending and all 47 criteria remain pending. No candidate acceptance, native
solve, physical inspection, fabrication, drilling, or release status changed.
