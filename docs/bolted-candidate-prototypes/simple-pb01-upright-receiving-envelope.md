# PB-01 upright: separate provisional 8-in bolt receiving envelope

Status: **conditional axial arithmetic only; no selected upright bolt, washer,
joint rating, or drilling release.** Run `python -m
scripts.simple_pb01_upright_receiving_envelope` at the repository root. This
reuses the [rail receiving calculator](simple-pb01-rail-receiving-envelope.md)
but does **not** require the rail and upright bolts to share a thread pattern
or manufacturer.

The [Home Depot Prime-Line 9058821 1/4-20 × 8-in bolt][bolt] is an online
A307 Grade A length lead. The earlier [source screen]
(quarter-inch-bolt-source-screen.md) infers a 1-in nominal threaded portion
from a common ASME B18.2.1 pattern, starting at 7.00 in under the head.
That is **not a product drawing or a measured first complete thread**. The
upright trial geometry has a 7.00-in wood-only grip. It keeps the rail's
separate fully threaded concept and its root-based calculation distinct.

| Independent development input | Assumed range (in) |
| --- | ---: |
| Bolt under-head length | 7.95–8.05 |
| Upright wood-only grip | 6.95–7.05 |
| Head washer and nut washer, each | 0.055–0.075 |
| Nut axial height | 0.20–0.25 |
| First complete thread from head | 6.95–7.05 |
| Unusable thread at tip | 0–0.125 |
| Required complete-thread projection beyond nut | 0.05 minimum |

Every spread in this table is an **invented sensitivity interval**, not a
catalog tolerance or an observed piece. The washer spread is around the
0.065-in Everbilt wide-flat trial pattern, whose NDS classification remains
open; the nut and 0.05-in projection criterion are likewise unqualified
development assumptions. For independent adverse extremes, the nut bearing
plane is **7.06–7.20 in**, its outer face is **7.26–7.45 in**, and the last
usable thread is **7.825–8.05 in**. The assumed latest first thread at 7.05
is only **0.01 in** before the earliest nut bearing plane. The minimum
complete-thread projection is 0.375 in. A mere 0.02-in later first thread
would erase that seating margin; neither sensitivity establishes actual
Prime-Line threading. Complete thread in modeled wood ranges **0–0.175 in**
under the assumed intervals, so full-body versus root bearing must be
resolved from the received shank/thread placement and applicable NDS rule.

For each actual piece, measure under-head length `L`, first complete thread
`F`, unusable tip `U`, wood grip `G`, both washer thicknesses `W_h`/`W_n`,
and nut bearing height `N`. Let `B = W_h + G + W_n`, `O = B + N`. Require
`F ≤ B`, `L − U ≥ O`, and `L − U − O` at least the **adopted** complete-thread
projection, then physically verify seating, engagement, washer bearing,
tip projection and accessible tightening. The chosen installation method
may require more than this provisional 0.05 in. A measured fit does not
resolve bolt root/bending input, washer classification, member/bolt strength,
group action, or all-six-case demand. **Do not drill from this screen.**

[bolt]: https://www.homedepot.com/p/310465152
