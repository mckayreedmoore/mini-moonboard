# Current group-action method — attempt05

Status: overflow-safe direction normalization added after independent attempt04 reviews found a fail-open path for finite vectors whose Euclidean norm exceeds the float range. This patch is based on the pinned attempt04 maintained source and tests; attempt04 remains preserved.

The helper now scales a three-component vector by its largest absolute component before calculating its unit direction. Finite but very large load and grain vectors therefore retain their direction instead of collapsing to `(0, 0, 0)` when the raw norm overflows. New public behavior tests require an off-row load direction and an oblique grain direction to return `pending`.

The focused suite reports 36 passed; the attempt05 patch replays without fuzz from attempt04 bytes. Fresh independent correctness, test, and architecture reviews are pending. This remains method-only: no candidate group values, resistance, capacity, or criterion dispositions. No solver, Docker, or current-joint run was performed.
