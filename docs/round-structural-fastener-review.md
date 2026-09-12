# Current structural panel screw review

The 56 SPAX XFT08P-2000 attachments have a usable published resistance basis,
but **panel attachment qualification remains open**. The current geometry audit
establishes fit and minimum geometric distances; it does not establish connection
demand. Earlier round-service and insert force results do not qualify this layout.

## Verified product basis

[SPAX TER 2010-02](https://www.drjcertification.org/report/download/1936),
revised November 4, 2025, renewal January 1, 2027:

- Table 2: T20; 2-inch length; 1.24-inch thread including tip; steel tension
  460 lbf and shear 345 lbf.
- Table 10: DF-L face-grain withdrawal 133 lbf/in; minimum embedded thread
  1 inch including tip. Apply applicable NDS adjustments.
- Table 6: 23/32-inch plywood, assigned specific gravity at least 0.50:
  head pull-through 212 lbf, before adjustments.
- Table 13: #8 x 2-inch, 23/32-inch plywood: 51 lbf lateral at 1-9/32-inch
  penetration, **SPF receiver**. This is not an assigned DF-L capacity.
- Table 19: edge 9.525 mm; reversible loaded end 44.45 mm; same-row spacing
  parallel/perpendicular to grain 44.45/31.75 mm; inline rows 15.875 mm.
  Preventing splitting may require larger distances.
- Sections 9.5–9.7: no lead hole required; install flush without overdriving;
  default penetration 1.5 inches unless a specific report provision differs.

## Current geometry calculation

The nominal 18.25625 mm plywood leaves 32.54375 mm penetration. The entire
31.496 mm threaded interval lies inside the receiver, starting 1.04775 mm behind
the plywood. Under Table 10's evaluated convention, no arbitrary tapered-tip
subtraction is necessary. This corrects older wording that automatically treated
1.24 inches as only an optimistic upper bound. Actual product and uninterrupted
wood engagement still must match.

The resulting unadjusted withdrawal reference is **733.601 N per attachment**.
The conditional head reference is **943.023 N**. Those are individual references,
not capacities that may be multiplied by twelve to qualify a face panel.
The report's plywood specific-gravity condition is not established merely by
calling the face veneer fir or the grade AC; confirm the panel's applicable
assigned value, or adopt a justified lower reference.

The saved [current audit](../fea/results/round-structural-audit-v1.json) checks
all 56 screw axes and contains uninterrupted receiver intervals and tip margins.
Its source hashes must match before relying on it. A CAD subtraction representing
occupied screw volume is **not** an instruction to drill a full-diameter receiver
hole; doing that would invalidate normal wood-thread engagement.

## Installation detail for this candidate

Use the selected screw and T20 bit, clamp the panel seated against its receiver,
and control the final drive to seat the head flush. The
[manufacturer head drawing](round-panel-countersink-reference.json) supplies the
90-degree nominal profile. Establish the seat on an offcut with the actual screw;
do not prescribe a fixed countersink depth from ideal CAD cones or invent torque.
No insert pilots, machine-screw clearances or insert recesses are part of this
assembly. Reserve space only. Inspect seats, splitting and stripped holes during
assembly; a damaged attachment needs a supported repair detail.

## Smallest remaining closure

Obtain current signed axial and lateral demands with panel/receiver contact and
a justified force-distribution model. Establish DF-L lateral resistance and
applicable adjustment/combined-action checks; do not reuse an SPF table without
a supported applicability basis. Include the kicker and every face attachment.
Equal sharing is not established by symmetric screw placement. Nor is assigning
an entire external force to one screw automatically a conservative bound:
eccentricity, contact and prying can create larger internal reactions.

Historical peak withdrawal around 1.55 kN exceeds the present unadjusted reference,
so the earlier diagnostic result is a reason to resolve demand, not a current
failure verdict or permission to release construction. No larger screw is
selected by this review. Any upsize requires renewed head-seat, end-distance,
passage-clearance and tip checks; adding length alone is not a capacity solution.
