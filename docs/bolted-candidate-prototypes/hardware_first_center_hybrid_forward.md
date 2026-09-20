# Hybrid HL35 center: 15 mm forward nominal trial — rejected

This is one bounded CAD trial of the existing kerf-right hybrid center, not a
selected design or shop instruction. The upper HL35 rectangles move 15 mm
forward in Y; the two widened principal solids and the lower HL35 stay at the
parent pose. The central raised region of the one-piece header extends 2.3 mm
forward, from Y = −36 to −33.7 mm, just enough to support the two full 127 mm
upper seat rectangles. The same six rails receive one planar inner-end cut at
X = ±120 mm. The original selected candidate, panel outlines, and all 66
panel/kicker screw axes are fixed.

**Result: reject.** The necessary header extension intersects the unchanged
left kicker by 20,015.787 mm³ and the right kicker by 20,294.013 mm³. It
cannot be used with the fixed panel geometry. No capacity, cutting, drilling,
or procurement approval follows. Do not advance this pose by relying on the
otherwise clear nominal checks.

All ten changed timber solids (header, post, two principals, six rails) were
screened against the fixed main/kicker panels and remaining adjacent wood.
All six ideal plate rectangles were screened against those panels, adjacent
wood, and changed timber. Among those checked pairs, the only positive
collision was the header with the two kickers. Pairwise overlaps among the
changed timbers, apart from their intended butt contacts, were not separately
screened in this stopped trial. The changed solids each remain one connected
CAD solid. The 12
nominal bore cylinders, including both first principal bores, are wholly in
their assigned receiving wood. No protected screw cylinder intersects an
ideal plate or bore; none of the 66 fixed axes loses modeled receiving wood.
The 12 existing frame-bolt occupied cylinders intersect neither the new
hardware nor changed timber in this screen. These are ideal occupancy checks,
not installed bolt-stack or screw-embedment checks.

Unresolved even apart from the panel collision: a prefabricated rail-to-center
connection and load path across the nominal 5.55 mm gap; other frame-bolt
connections and complete head/washer/nut stacks; full tool and withdrawal
clearance; delivered HL35 hole and bend positions; wood edge/end distances;
connector and bolt resistance; and procurement of suitable one-piece blanks.
The modeled 4.55 mm plates and 14.2875 mm bores are diagnostic envelopes,
never drilling coordinates.

Regenerate the paired JSON with:

```sh
uv run python -m scripts.hardware_first_center_hybrid_forward \
  --output docs/bolted-candidate-prototypes/hardware_first_center_hybrid_forward.json
```
