# Hybrid HL35 upper toe versus header-seat band

This is a bounded nominal search within the [rejected hybrid
pose](hardware_first_center_hybrid.md), not a different installed joint,
load rating, or drilling plan. Reproduce the JSON with
`uv run python -m scripts.hardware_first_center_hybrid_toe`.

Sliding both upper HL35 brackets forward along their unchanged X faces
could move the first upper bolt rows away from the sloped principal toes.
The rear of each 127-mm-long seat starts at Y = −175.7 mm in the hybrid
pose. Its front must remain at or behind the header front, Y = −36 mm,
to keep the full nominal seat under wood. The largest such shift is
**12.7 mm**. At that shift, each first principal's illustrative 14.2875-mm
bore still lacks **800.964 mm³** of receiving wood. A sampled 15-mm shift
contains those ideal bore cylinders, but puts at least **2.3 mm** of the
nominal seat beyond the header front.

This bounds only full-cylinder containment, not the NDS end-distance,
loaded-edge, splitting, washer, steel, or installed bolt-stack requirements.
The factory horizontal hole offset and bend variation remain unverified.
No catalog load is assigned to a partly unsupported seat. Extending the
header forward, altering principal toes, or changing bracket orientation
would require a distinct installed geometry and contact/load-path check;
the current pose already collides with neighboring rails. The protected
panel/kicker axes and selected frame are unchanged here. No cutting or
drilling follows.
