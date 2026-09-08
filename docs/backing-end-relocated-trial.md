# End-retention trial with relocated gusset bolts

**Unselected fit trial, not a new build or drilling schedule.** This retains the
current timber sections, central backing bolts and base gussets. It combines
the two nominal ML23Z end angles with a 45 mm rear-normal relocation of
`timber_base_left_1` and `timber_base_right_1`. All other existing connections
remain at their current positions; eight specified SDS screws are added for
the two trial angles. The advertised wider-principal model is unchanged.

## Geometry result

The earlier [fixed-bolt end-angle placement](backing-end-retention-trial.md)
collided with both base-gusset bolts. The revised positions clear those collisions
in the nominal solids. The two relocated bolts retain their 76.2 mm length,
57.15 mm grip and existing hardware envelopes.

| Datum, both sides unless noted | Trial value |
| --- | ---: |
| Rear-normal shift | 45 mm / 1.772 in |
| Bolt world Y | −114.472 mm |
| Bolt world Z | 328.925 mm |
| Bolt board S | 17.6005 mm, unchanged |
| Bolt board N | 122.7038 mm |
| Distance to the other rim/gusset bolt | 61.619 mm |
| Nominal rim rear-edge distance along N | 61.446 mm |

The distance to the other bolt is not a passed spacing requirement: the offset
has components along and across grain, and applicable loaded-edge/group rules
must be checked. Likewise, nominal material engagement does not qualify dowel
bearing, splitting or gusset resistance. The move changes the base connection's
force distribution; old joint actions cannot be assigned unchanged.

Two tests verify that only the designated existing axes move; lengths, grip and
members are unchanged; complete proposed 11.1125 mm bores fit inside both raw
receivers; and the added/relocated hardware clears current wood, inserts, angles
and all other connection bodies. Only intended shaft/bore engagement is exempted
from collision checking—not screw heads, washers or nuts. The original rejected
trial's tests remain intact.

## Not yet established

The subsequent [installation-source check and prepared inquiry](end-angle-installation-gate.md)
identifies a concrete limit: the trial does not meet the generic SDS axial
edge/end-distance provisions. Connector-specific applicability remains unresolved;
nominal fit must not be promoted to a capacity claim.

- Manufacturer installation and edge/end/spacing requirements for the ML23Z
  connections and revised gusset bolt group.
- Actual load sharing, local resistance and unanchored behavior.
- Socket/driver approach and complete removal/transport sequence. Adding the
  angles must not turn repeatedly removed SDS screws into assumed demountable
  structural fasteners.
- Fresh manufacture-ready solids and schedules. A selected redesign must rebuild
  the affected wood from raw stock with only the new bores; the old holes must
  not remain in its CAD. This is **not permission to redrill an existing gusset
  or rim** without assessing the abandoned holes.

The trial code is `mini_moonboard/backing_end_relocated_trial.py`; run
`uv run pytest -q tests/test_backing_end_relocated_trial.py`. It defines proposed
connection locations for investigation, not a viewer variant or purchasing
approval. The result supports continuing this compact arrangement's evaluation,
not declaring the backing connection structurally adequate.
