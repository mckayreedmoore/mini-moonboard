# WJ-04 full-stock threaded-bearing screen

Status: bounded geometry screen only, 2026-09-24. The [report](thread-screen.json)
consumes the archived, source-bound [eight-bolt WJ04 mechanics input](../wj16-full-stock-mechanics-inputs/mechanics-inputs.json).
It evaluates the two ordered wood receivers for each of eight G7 bolts at all
16 combinations of independent ±0.5 mm wood-layer corners and the catalog
minimum/maximum thickness of both washers. This produces 128 bolt-and-corner
combinations covering 256 member-specific corner fractions.

Using the recorded 127 mm minimum smooth-body length as a screen boundary, all
256 member-specific corner fractions are at or below the recorded NDS
one-quarter condition. The largest is 7.8549% in a 38.1 mm nominal receiver
layer at its 38.6 mm corner thickness; the maximum geometric overlap after the
boundary is 3.032 mm. The upper-rail cleat receiver peaks at 3.3915%.

This is not a delivered-bolt thread-location measurement. `Lb` identifies the
minimum body dimension, not the first full-form thread; the actual thread
transition and nut engagement remain open. `Lg` is preserved as a grip-gaging
bound and is not used as a thread boundary. The result does not establish the
NDS full-body-diameter option, a capacity, full smooth-shank coverage, fit, or
installation. The NDS condition concerns lateral-yield diameter use; it is not
a resistance calculation.

The six-inch cap-screw dimensions use the primary ASME table derivation in the
[source-correction note](../../bolt-dimension-source-correction.md). The
misordered Nickel Systems row is not used as the dimension source. See the
[ordinary-bolt method note](../wj04-ordinary-bolt-options.md) for the broader
NDS and hardware context.

Reproduce the JSON with `uv run python
scripts/wood_joint_wj04_full_stock_thread_screen.py`. Focused verification is
`uv run pytest -q tests/test_wood_joint_wj04_full_stock_thread_screen.py`.
