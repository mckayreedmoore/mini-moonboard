# PB-01 two-sided bolt thread and stack interval screen

Status: **conditional geometry only; no selected stack or drilling release.** Run
`uv run python -m scripts.simple_pb01_thread_stack_screen` from the repository
root to reproduce the numbers. Lengths are measured from the underside of the
bolt head. This is one axial dimension screen for each of the two serial PB-01
interfaces, not a bolt capacity or a connection verdict.

The modeled wood grips are 3.75 in at the rail and 7.00 in at the upright.
The trial has one 0.065-in [Everbilt 807210 wide washer][washers] under the
head and one under the nut, so the wood spans are 0.065–3.815 and
0.065–7.065 in. The nut-side washer bearing planes are therefore **3.88**
and **7.13 in**. The [Prime-Line 9058745 5-in bolt][prime5] and
[9058821 8-in bolt][prime8] are ordinary Home Depot retail leads. Their
0.75- and 1.00-in nominal threaded portions are the **assumed ASME B18.2.1
pattern** recorded in the [source screen](quarter-inch-bolt-source-screen.md),
not verified product dimensions. The corresponding inferred starts are 4.25
and 7.00 in. A 0.25-in earlier start is a hypothetical transition
sensitivity, not evidence that usable complete threads begin there.

The nut-height interval **0.20–0.25 in is assumed solely for sensitivity**;
neither bound is a measured or published height for the proposed retail nut.
"Engagement" below means axial overlap of the modeled thread interval and
the nut-height interval. It does not count complete engaged turns, prove a
nut can be seated on runout, or establish thread strength. Projection is the
nominal tip beyond the outer nut face, `bolt length − bearing plane − nut
height`; it excludes length tolerances, tip chamfer and locking hardware.

| Case | Start | Seat gap | Wood thread | Nut overlap | Tip past nut |
| --- | ---: | ---: | ---: | ---: | ---: |
| 5-in rail, nominal | 4.25 | **0.37 short** | 0 | **0–0** | 0.87–0.92 |
| 5-in rail, −0.25 | 4.00 | **0.12 short** | 0 | **0.08–0.13** | 0.87–0.92 |
| 8-in upright, nominal | 7.00 | 0.13 before | 0.065 | 0.20–0.25 | 0.62–0.67 |
| 8-in upright, −0.25 | 6.75 | 0.38 before | 0.315 | 0.20–0.25 | 0.62–0.67 |

All table dimensions are inches. The −0.25 cases move the assumed thread
start earlier by 0.25 in. Nut overlap is across the assumed 0.20–0.25-in
nut-height interval; the rail −0.25 case covers only part of either nut.

For the 5-in rail bolt, positive tip projection does **not** repair the
missing threads at the nut seat. Even the hypothetical earlier start places
part of the nut on unthreaded shank, so this Prime-Line rail stack fails the
modeled seating screen. The upright case has a nominally threaded nut interval,
but its first complete thread, delivered length, actual nut, washers and
projection remain unverified. Its wood contains some modeled thread; no
full-body bearing credit follows from this calculation.

One ordinary rail alternative is the [Home Depot Everbilt 800676 1/4-20 ×
5-in hex bolt][everbilt5], whose listing calls it **fully threaded**. That
listing is a lead for moving the rail nut onto threads while retaining the
nominal 5-in length. It does **not** establish the first complete thread,
delivered root range, shank diameter, bending-yield input, nut compatibility
or a verified thread length for this exact product. A fully threaded rail
bolt would also put threads through the wood, so the earlier conditional
full-body assumptions cannot be transferred to it. It is not a selected
replacement or a released stack.

Before any stack or hole is released, measure the delivered bolt's first
complete thread, usable threaded length and overall length; identify and
measure the actual nut and both washers; confirm complete nut engagement and
required projection under the chosen fastening method; then revisit root,
bearing and complete joint checks. The [quarter-inch yield
screen](simple-pb01-quarter-yield-screen.md) and [member
screen](simple-pb01-quarter-member-screen.md) remain conditional components,
not a joint rating. **No drilling release.**

[washers]: https://www.homedepot.com/p/204284538
[prime5]: https://www.homedepot.com/p/310326760
[prime8]: https://www.homedepot.com/p/310465152
[everbilt5]: https://www.homedepot.com/p/204633308
