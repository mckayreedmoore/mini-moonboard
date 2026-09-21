# PB-01 rail: provisional 800676 receiving envelope (RV-1)

Status: **conditional axial geometry only. No receiving pass, selected stack,
connection rating, or drilling release.** Run
`python -m scripts.simple_pb01_rail_receiving_envelope` at the repository root.
This screen concerns only the two rail-side bolts of the four-bolt PB-01 trial
pose. It does not change the upright bolts or any panel/kicker screws.

The [previous two-sided stack screen](simple-pb01-thread-stack-screen.md)
puts the partially threaded Prime-Line 5-in rail bolt's inferred first thread
0.37 in beyond the nut bearing plane. The [Home Depot 800676 listing][bolt]
identifies a 1/4-20 × 5-in Everbilt hex bolt; the earlier
[quarter-inch source screen](quarter-inch-bolt-source-screen.md) records the
retail lead as fully threaded. This is a *candidate lead*, not a controlled
thread drawing or evidence of a delivered lot's dimensions. The [PB-01 trial
geometry](simple_rail_joint_comparison.json) has a 2.25-in cleat plus 1.5-in
rail, hence a nominal 3.75-in wood-only grip. The 7.5-mm diagnostic bore and
CAD washer envelopes are not drilling or purchased-hardware instructions.

All distances below run from the underside of the bolt head toward its tip.
The head washer precedes the wood; the nut washer follows it. The nut must
seat against that washer, with its **entire axial height on complete usable
threads**. “First complete thread” excludes the under-head incomplete lead;
“unusable tip” excludes incomplete or chamfered threads at the far end.
Counting the nominal bolt tip alone would overstate usable projection.

| Independent RV-1 trial input | Assumed interval, in | Status |
| --- | ---: | --- |
| Underside-head to tip length | 4.95–5.05 | Invented ±0.05 sensitivity, not a catalog tolerance |
| Wood-only rail grip | 3.70–3.80 | Invented ±0.05 around the 3.75-in geometry |
| Washer thickness, each side | 0.055–0.075 | Invented spread around the 0.065-in [807210 sheet][washer-sheet] value |
| Nut axial height | 0.20–0.25 | Invented sensitivity; [801730 retail nut][nut] has no verified height here |
| First complete thread from head | 0–0.25 | Invented under-head allowance; must be measured |
| Unusable threaded tip length | 0–0.125 | Invented allowance; must be measured |
| Minimum complete thread beyond nut | 0.05 | Invented one-pitch criterion for 20 TPI; confirm fastening method |

These are simultaneous independent bounds, deliberately combined at adverse
extremes. They are **not** asserted manufacturing limits, wood tolerances, or
an acceptance result for a purchased fastener. The washer source gives an
approximately 0.312-in ID, 0.734-in OD, and 0.065-in thickness pattern;
physical bearing suitability still needs review. One washer is required at
each end of the trial stack. No lock washer or second nut is included.
The [source screen](quarter-inch-bolt-source-screen.md) records a 2024 NDS
Chapter 12 / Appendix L6-versus-L8 cross-reference discrepancy and a
separate 1/4-in retail cut-washer lead. Neither proves that this 807210
wide-flat-washer stack meets the cut-washer-or-equivalent requirement.

| Derived interval | RV-1 result, in |
| --- | ---: |
| Nut washer bearing plane = head washer + wood + nut washer | 3.810–3.950 |
| Nut outer face = bearing plane + nut height | 4.010–4.200 |
| Last usable thread = bolt length − unusable tip | 4.825–5.050 |
| Metal tip beyond nut | 0.750–1.040 |
| Complete-thread projection beyond nut | **0.625–1.040** |
| Complete thread axially within wood | 3.505–3.800 |

Thus the *assumed interval* puts the first complete thread before the
earliest nut bearing plane (0.25 < 3.81), and the last usable thread after
the latest nut outer face (4.825 > 4.20). Its worst complete-thread
projection exceeds the provisional 0.05-in minimum. This is an **arithmetic
feasibility result only**. Up to 0.195 in of the wood grip may precede the
first complete thread at the adverse head-washer/first-thread limits; the
rest is threaded. Do not transfer a full-shank bearing assumption to this
rail bolt. The separate [quarter-inch yield screen](simple-pb01-quarter-yield-screen.md)
uses a conditional thread-root model, not SKU qualification.

## Receiving acceptance before any further decision

For each actual rail stack, record the bolt package/model and measure
underside-head length `L`, first complete thread `F`, and distance `U` from
tip back to the last complete thread. Measure the actual dry-fit wood grip
`G`, **both** washers `W_h`, `W_n`, and nut height `N` at the bearing faces.
Use the actual values, not nominal labels. Recalculate if any value falls
outside the trial ranges; that voids this numerical envelope rather than
automatically accepting or rejecting the delivered part.

1. Confirm the correct 1/4-20 bolt and compatible nut, one correctly sized
   bearing washer under head and nut, flat seating, and no bottoming or
   damaged/incomplete threads at the nut. Confirm washer bearing category
   and wood bearing/crushing separately; the retail “flat washer” name is
   insufficient for the NDS cut-washer-or-equivalent requirement.
2. Compute nut bearing plane `B = W_h + G + W_n` and nut outer face
   `O = B + N`. Require `F ≤ B` and `L − U ≥ O` so the whole nut occupies
   complete threads. Physically demonstrate full nut engagement; axial
   inequalities alone do not prove thread fit or clamp seating.
3. Require `L − U − O ≥ 0.05 in` of **complete** thread beyond the nut,
   plus visible positive metal-tip projection. The 0.05-in minimum is an
   RV-1 assumption, not a manufacturer installation instruction; revise it
   if the chosen nut/fastening method specifies more. Record the observed
   projection after seating rather than inferring it from package length.
4. Record first-thread placement across the wood, actual thread minor/root
   diameter range and bolt material basis. Revisit rail bearing and lateral
   yield with the actual root; the published typical 0.189-in NDS root is
   **not** a certified minimum for SKU 800676. Check washer bearing, clamp,
   splitting, row/group effects and combined six-case joint actions before
   selecting a stack. An arithmetic fit alone cannot close those gates.

**Unresolved:** controlled SKU-specific root/minor-diameter limits and
bending-yield basis; actual delivered bolt, nut and washer dimensions;
verified washer suitability and wood bearing; complete joint resistance and
demand. No parts were inspected or bought. **Do not drill from this screen.**
The owner excludes half-laps and custom metal; this screen adds neither and
does not alter the panel screw layout.

[bolt]: https://www.homedepot.com/p/204633308
[nut]: https://www.homedepot.com/p/204274089
[washer-sheet]: https://images.thdstatic.com/catalog/pdfImages/13/1353fc43-4c14-45d4-ba92-5745b045eae3.pdf
