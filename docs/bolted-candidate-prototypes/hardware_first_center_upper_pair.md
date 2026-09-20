# Center-tongue opposing upper HL33 pose

**Status: rejected installed geometry trial.** This sidecar starts from the
current `hardware_first_center_tongue` kerf-right pose. Regenerate its JSON with
`uv run python -m scripts.hardware_first_center_upper_pair --output
docs/bolted-candidate-prototypes/hardware_first_center_upper_pair.json`.
It is an occupancy screen, not a connector selection or shop layout.

The [Simpson 2026–2027 connector catalog](https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog)
(HL33 row, PDF p. 315) lists equal 82.55 mm legs, 63.5 mm bend length,
31.75 mm along-bend hole offset, 50.8 mm vertical-leg hole offset, and one
bolt hole per leg. The paired brackets use those factory dimensions. The
horizontal-leg hole inset is undimensioned in the drawing; 50.8 mm is a
screening assumption. Rectangular 4.55 mm plates and 14.2875 mm wood bores
are ideal diagnostic envelopes, not delivered dimensions or drilling data.

One inward-facing HL33 is added on each principal's inner X face at the
existing upper station, Y = -100..-36.5 mm. The original outward-facing
upper angles remain. The new vertical legs face the 51.1 mm gap between
principals. Their horizontal seats reach 82.55 mm inward from each face,
so the seats overlap each other across **51.1 mm of X** and their combined
reach exceeds the face gap by **114 mm**. The three plate-pair intersections
are 14,764.068 mm³ between seats and 1,314.609 mm³ at each opposite
vertical-leg/seat crossing. Each inner seat also intersects the *other*
principal by **9,086.691 mm³**. Its furthest X edge projects 31.45 mm past
that opposite principal's inner face. These positive-volume collisions reject
this exact same-Y pose. A 63.5 mm longitudinal separation is the minimum
to make the two ideal seat bands merely touch in Y; that arithmetic is not a
tested alternative pose or an installation recommendation.

Keeping both upper seats in the same Y band but separating them in X
would need an inner-face gap of at least 2 × 82.55 = 165.1 mm, which is
114 mm wider than the current 51.1-mm gap. Moving unchanged rectangular
principals outward symmetrically would shift each by at least 57 mm;
the left member's inner edge would then be X = -82.55 mm, beyond its
protected panel-screw centers at X = -70 mm (and symmetrically on the
right). Thus simple outward translation cannot both remove this overlap
and retain those screw receivers. A reshaped one-piece member or different
bracket orientation would be a separate, untested concept.

Each added principal bore is exactly coincident with its existing outward
HL33 principal bore, hence one shared full-width bolt axis per principal.
The four upper header axes are independent: the two new inner axes are
X = ±25.25 mm, Y = -68.25 mm, while the original outer axes are
X = ±165.25 mm, Y = -68.25 mm. The new inner header axes are independent
of the lower header axes as well. The JSON gives every new-to-existing
header-axis distance and the minimum ideal bore surface gap. No independent
bore crossing or missing receiving wood was found.

Both panel outlines and all 66 protected panel/kicker screw axes and their
receiving wood remain as in the tongue model; its six panel solids and twelve
existing frame axes are also unchanged. The new brackets and bores have no
positive-volume clash with the panel solids, protected 50.8 mm screw
envelopes, conditional 63.5 mm overall screw envelopes, existing frame-axis
envelopes, adjacent unchanged wood, or original plates. The JSON reports the
baseline tongue checks alongside all new-hardware intersections. It does not
resolve heads, washers, nuts, access, delivered geometry, fastener edge/end
distance, paired-angle action, rail attachments, capacity, or reversible F1
performance. No lap joint, custom steel, drilling, or acceptance claim follows.
