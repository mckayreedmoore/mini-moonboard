# Common-core HL33 center: bounded nominal screen

**Both tested poses are rejected for catalog inapplicability and bolt-end access.** This is one parameterized
kerf-right geometry prototype, not a structural rating, shop layout, or drilling
release. Regenerate the paired JSON with:

`uv run python -m scripts.hardware_first_hl33_common_core --output docs/bolted-candidate-prototypes/hardware_first_hl33_common_core.json`

The [Simpson 2026–2027 connector catalog](https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog)
(C-C-2026, PDF p. 315, HL33 row) supplies the nominal 82.55-mm legs, 63.5-mm
bend length, 31.75-mm along-bend hole position, 50.8-mm vertical-leg hole
position, one 1/2-in bolt per leg, and 88.9-mm minimum bolted wood thickness.
The drawing does not dimension the horizontal-leg hole inset; this model
assumes 50.8 mm. It also assumes ideal 4.55-mm rectangular plates,
14.2875-mm occupied wood bores, 25.4-mm washer discs, simplified head/nut
cylinders, and a 40-mm-diameter by 25-mm-long tool sweep. These are diagnostic
occupancy assumptions, not delivered dimensions or fastener selections.

The one-piece structural core has a 240-mm-wide rear block and a 50.8-mm-wide
integral tongue that continues to the fixed front plane. Separate one-piece
left and right backing wings receive the four center kicker screws. The tongue
backs both inner kicker edges at the −1.5875-mm seam; the raised header backs
the front above the core. The wings are joined to the core by **two modeled
factory HL33 angles**, with separate through-core bolt paths and one shared
transverse bolt through both wings and the tongue. This backing connection is
**not a catalog-applicable or rated HL33 arrangement**. These connections are
represented by ideal bodies, holes, and bolt paths; face contact is not counted
as a bracket connection. One lower rear-face HL33 links core to the changed
header. Two outward upper HL33s link the widened center principals to it.
The six affected inner rail endpoints are trimmed to |X| = 130 mm. No lap joint
or custom steel is introduced.

| Core rear extension from raw header | Rear block Y span | Tongue/backing junction Y | Core ∩ each backing | Nominal screen |
| ---: | ---: | ---: | ---: | --- |
| 45 mm | −220.70…−130.23 mm | −130.23 mm | 0 mm³ | Rejected: catalog and access |
| 65 mm | −240.70…−150.23 mm | −150.23 mm | 0 mm³ | Rejected: catalog and access |

The full core *bounding box* overlaps each wing's bounding box because it
encloses both the wide rear block and narrow forward tongue. The actual CAD
solids do not overlap: the wide block ends exactly at the junction; forward
of it, the wings occupy X = −120…−25.4 and 25.4…120 mm while the tongue
occupies X = −25.4…25.4 mm. Explicit core/wing solid intersections are zero
in both trials. The JSON records the component bounds and intersection volumes.

All six fixed panel solids and all 66 protected screw axes retain their modeled
receiving wood. The four center kicker screws each retain 438.127 mm³ of
occupied intersection with their wing. No nominal plate, bore, or bolt path
intersects a panel or protected screw, and no modeled bore exits its receiving
wood. The changed header and rail endpoints have no positive-volume timber
collision; the 12 existing frame axes do not use changed receiver members.
Raw kerf-right panel shapes are retained. Hold and LED voids are not separately
solid-modeled, so this screen only preserves their source panel geometry; it
does not prove local hole clearance or delivered panel fit.

The nominal 88.9-mm HL33 bolted-wood minimum fails at the **shared backing
bolt's integral core tongue**: it is 50.8 mm through X, short by 38.1 mm.
This is a catalog-applicability failure even though the occupied bore remains
within wood. Every other modeled receiving section reaches the nominal minimum:

| Receiving wood on a modeled bolt path | Thickness in bolt direction |
| --- | ---: |
| Lower core; each backing core-face bolt | 90.47 mm |
| Lower and both upper header holes | 88.9 mm |
| Both upper principals | 88.9 mm |
| Each backing wing on the shared transverse bolt | 94.6 mm |
| Integral tongue on the shared transverse bolt | **50.8 mm — fails** |

Independently, the transverse bolt passes through **three wood sections and
two HL33 side legs**. That paired-angle stack is not the catalog's tabulated
two-member installation. Increasing tongue thickness alone cannot make this
backing connection catalog-applicable or rated.

The smallest *thickness-only* symmetric shape bound is 88.9 mm of tongue plus
2 × 88.9 mm of wings: **266.7 mm total core width**, 26.7 mm wider than the
current 240 mm, before nut/tool gaps. Keeping the current outer width while
widening the tongue would leave each wing only 75.55 mm thick. The side plate
would move out to at least |X| = 137.9 mm, so the current 130-mm rail-end
cutoff would also need re-screening. This is arithmetic, not a tested revised
pose. The smallest connection-topology change is to replace the shared bolt
with separate, accessible two-member backing-angle attachments, one per wing;
their geometry and catalog applicability have not been demonstrated.
A direct split of the current transverse bolt was not run as a third CAD pose:
each wing's inner face directly abuts the continuous tongue, leaving **zero
millimeters** for even the assumed 3-mm washer and 12-mm nut on that side.
Widening the shape does not create that access. A distinct bracket/member pose
or qualified relief would be needed before a meaningful independent-bolt test.

A [Lowe's 4×12×12-ft #2 Better Douglas-fir green listing](https://www.lowes.com/pd/Douglas-Fir-Lumber-Common-4-in-x-12-in-x-12-ft-Actual-3-562-in-x-11-5-in-x-12-ft/1000028845)
states an actual 3.562 × 11.5 in section. **11.5 in is 292.1 mm**, not
285.75 mm; the listed width is 25.4 mm beyond the 266.7-mm arithmetic bound.
This is a width comparator only: its 90.47-mm thickness cannot contain the
modeled one-piece core's other two spans as a full blank. Delivered dimensions,
grade stamp, drying/shrinkage, local supply, machining yield, and a different
viable one-piece blank remain unverified. It is not approved stock.

The access obstruction is concrete. In both trials, the lower core bolt's
illustrative nut-side washer, nut, and tool sweep enter the integral front
tongue; the two backing-to-core bolt nut-side envelopes enter their backing
wings. At the upper joints, some tool sweeps enter bottom rails. Four pairs of
different-axis tool sweeps overlap. The JSON gives the occupied volumes and
all 54 modeled outside-face washer/head/nut/tool envelopes per trial. A
different fastener orientation, local access pocket, assembly sequence, or
rail detail would need a separate check; none is assumed to work here. These
are **potentially repairable detail/geometry failures**, but the present
poses cannot be called access-clear.

Three **fundamental integration gaps** remain independent of the access result:
the catalog-inapplicable backing connection described above, the six trimmed
rails without a modeled factory-bracket connection to the new center, and the
HL33 table's uplift/local F1 entries, which do not establish the
reversible F1, unlisted F2, or moment duties for this mixed orientation. The
backing angles' shared-bolt action is unqualified. Member edge/end
distances, actual bolt grip and length, delivered hardware tolerances, stock,
and component resistance remain open. No capacity, cutting, purchase, or
drilling claim follows.
