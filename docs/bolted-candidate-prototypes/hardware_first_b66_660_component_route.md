# UB66/B66 660-mm component-route probe

Checked 2026-09-20. **This nominal pose is rejected.** It is one bottom-right
rail trial in the kerf-right B 660-mm spaced-rib parent, not a connected
architecture, accepted connector, purchase instruction, or drilling release.
The script and JSON are reproducible diagnostic geometry, not hole locations
for fabrication.

The exact retail item is [Home Depot UB66](https://www.homedepot.com/p/313507617),
mapped by [MiTek's retail conversion chart](https://images.thdstatic.com/catalog/pdfImages/2f/2f1009db-047c-4da8-a283-bcda2c494ebe.pdf)
to B66. Nominal leg and hole positions come from the
[manufacturer B66 DXF](https://www.mitek-us.com/wp-content/uploads/files/Drawing%20Library/B66_3view.dxf):
6-in. reach, 1½-in. width, four approximate Ø10.3-mm holes, two per leg,
at about 25.4 and 126.744 mm from each free end. The model uses an
illustrative 2.66-mm plate envelope; coating, bend radius, tolerances and
delivered dimensions remain unverified. Availability of the exact item at a
particular store was not checked.

[MiTek ESR-3455](https://www.mitek-us.com/wp-content/uploads/files/pdf/Code%20Evaluation%20Reports/esrESR-3455.pdf)
Table 3 specifies ⅜-in. ASTM A307 Grade A or better bolts with minimum
45,000-psi bending yield strength, at least 3-in. actual wood thickness,
and qualifying wood specific gravity of at least 0.50 unless excepted.
The ESR also assumes wood at or below 19% moisture for its dry-condition
values. Its F1 bidirectional provision calls for braces on both sides;
a lone rail brace cannot inherit bidirectional F1 capacity.
Its B66 material is 12-gauge ASTM A653 Structural Steel Grade 40 G90 with
at least 0.099-in. base steel. These inputs identify the product; they do
not establish this joint's resistance. The ESR's 710/335-lbf B66 F1/F2
values are at `C_D=1.6` and expressly may not be adjusted to other load
durations. No normal-duration or combined-force/moment rating is adopted.

The representative B66 spans the right rib and a one-piece zero-gap rail
pad extended to cover the full 152.4-mm seat. All 66 protected screw axes
retain their receiving wood in this local reconstruction. Against the
parent's modeled wood, eight header brackets and nominal bolt/washer/tool
envelopes, no other clash was found for this station. Those envelopes are
only straight 25.4-mm washers and 38.1-mm-by-30-mm tool cylinders; actual
heads, nuts, washer stack, wrench sweep, disassembly and purchased lengths
were not established.

**Decisive geometry result:** the first upright bolt's *centerline* crosses
88.9 mm of rib, but its complete 9.525-mm-diameter wood bore does not.
Approximately 1,869.507 mm³ of that ideal bore exits the modeled rib.
The other three nominal wood bores remain inside their respective receivers.
This pose is therefore not a viable four-bolt installation. Merely reporting
centerline thickness would conceal the failure. The exact local edge/end
distances, tolerances, and machining feasibility are not yet established.

Five other rail ends, changed frame-bolt axes, wood bearing/yield and
edge/end checks, steel/formed-angle resistance under applicable load cases,
action coverage, and the normal-duration rating route remain open. Nothing
in this probe approves cutting or drilling.
