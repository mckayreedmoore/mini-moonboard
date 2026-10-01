# Parent validation: group-action method attempt10

**Disposition:** parent validation passes for the bounded NDS-2024 group-action
factor method only. This does not establish bolt-group resistance, per-fastener
load distribution, a candidate capacity, a criterion disposition, or a joint
result.

## Reproduction

On 2026-09-28, the parent independently checked the attempt10 package and its
maintained source:

- All five files in the attempt10 terminal manifest matched their SHA-256
  entries.
- The attempt07 base module and test hashes matched the frozen base pins.
- The maintained module and test hashes matched the attempt10 terminal hashes.
- The source-pins file matched the hash recorded by the independent reviews;
  the current `criteria-method-map.md` matched the method-map hash in the pins.
- `git apply --check` accepted `attempt10.patch` against a separate temporary
  copy of the pinned base, and replayed bytes matched both maintained hashes.
- The isolated focused suite passed: **51 tests**.

The independent correctness, architecture, and test reviews reported no
actionable findings for their pinned attempt10 snapshots. Their reports are
linked below with their report hashes. Review probes remain method-only and
do not make candidate inputs or capacities known.

## Scope boundary

The validated helper calculates the NDS-2024 `Cg` factor for a bound straight,
uniform-pitch, same-diameter dowel row with one to three total members. The
sensitivity helper reconciles exact declared input paths, including escaped
object keys and list changes. Four-or-more-member applicability remains
unsupported. Neither helper calculates resistance, distributes group force to
bolts, applies loads, or compares a demand with capacity. Candidate capacity
remains unset and all 47 criteria remain pending.

The current hash-bound aggregate remains `criteria_pending`: 47 pending, zero
conditional passes, zero failures, and all engineering, drilling, fabrication,
structural, and climbing release flags false. The group-action validation does
not alter that aggregate.

No geometry, candidate material or hardware assignment, solver input, Docker
build, or native run changed. No current-joint result is implied.

## Bound evidence

- [Attempt10 package](../current-group-action-method-attempt10/README.md),
  source pins SHA-256 `d66ae5481bdcdd2accd54d72f0ffdb7b80c66ef6d21223d573fc235f95e52a8c`.
- Maintained module SHA-256
  `121ec9d5399aa3e856b4038232e6d61c628aac42ce2addf8d1ff7e3a0e4c3df9`;
  focused test SHA-256
  `741ef514d6a7ea6a88c24f95a53241d126b61e4cd8af6c13d7288268b18adef9`.
- Current method-map SHA-256
  `2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7`.
- [Current 47-criterion aggregate](../current-criteria-overlay-attempt02/current-inventory-reviewed-attempt02/current-aggregate.json),
  SHA-256 `6eaaa9ab534428dfecbbf4b8a6f9940090da0df7c6451a8b67a5ecb18635ab36`.
- Correctness review:
  [README.md](../current-group-action-method-attempt10-correctness-review/README.md),
  SHA-256 `a4df3f829d87967b19576e4b69af1d7ff03c5e46907526da708fc4027262be86`.
- Architecture review:
  [report.md](../current-group-action-method-attempt10-architecture-review/report.md),
  SHA-256 `4573f4c2cfc7a9a31dfe67385f42167f274cd8421543742d32031b000066a685`.
- Test review:
  [README.md](../current-group-action-method-attempt10-test-review/README.md),
  SHA-256 `66ac949552fd502f330e8d1974c309b1aa7a4e91b13aa7d9fa8ec4de6a92c15b`.
