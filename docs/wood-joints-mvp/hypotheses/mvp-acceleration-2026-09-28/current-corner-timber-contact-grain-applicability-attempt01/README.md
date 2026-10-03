# Current corner timber contact grain-applicability screen

This packet classifies the receiving-member grain direction for the seven
existing timber interfaces in the left outer corner. It reuses the authenticated
three-case contact screen for `a12-rear`, `a1-rear`, and `k12-rear`; it adds no
contact solve, quadrature, or cells. The saved screen contributes **588 cell
states and 147 signed pair wrenches** across 21 case increments. Each of the 14
pair/receiver combinations has the same 84 saved cell states; the packet
records 1,176 receiver/cell applicability rows because every cell acts on two
receiving members.

The producer verifies the original contact-screen replay and the hardware/
material packet replay, then checks every direct SHA in [source-pins.json](source-pins.json).
That binds the original contact model/export source, its conditional case
register, the declared material/grain inputs and their eight cited sources.
The source force, cell area, average pressure and rounding interval, contact
state, pair force and global-datum moment remain copied from the authenticated
screen. The only new calculation is the angle between its recorded contact
force normal and each receiver's proposed longitudinal grain direction.
Classification uses `abs(dot(n,g))`: parallel for at least `1−10⁻⁶`,
perpendicular for at most `10⁻⁶`, and oblique otherwise.

| Existing interface | Receiver grain applicability | Peak existing cell-average pressure | Conditional `Fc⊥` reference ratio |
| --- | --- | ---: | --- |
| `post-spine` | post perpendicular; spine perpendicular | 0.037369 MPa | 0.008672 on each receiver |
| `spine-side` | spine perpendicular; side perpendicular | 0.028236 MPa | 0.006552 on each receiver |
| `side-innerblock` | side perpendicular; inner-frame block perpendicular | 0.050947 MPa | 0.011823 on each receiver |
| `block-header` | inner-frame block parallel; header perpendicular | 0.026155 MPa | 0.006070 on header only |
| `header-post` | header perpendicular; post parallel | **0.513416 MPa** | **0.119143 on header only** |
| `header-side` | header perpendicular; side oblique (40°) | 0.169532 MPa | 0.039342 on header only |
| `header-spine` | header parallel; spine perpendicular | 0.037606 MPa | 0.008727 on spine only |

The conditional transverse comparator is DF-L No. 2 `Fc⊥ = 625 psi`, converted
with `1 psi = 0.006894757293168361 MPa` to 4.309223308230226 MPa. Its named
arithmetic scenario assumes dry service (`CM=1.0`), normal temperature
(`Ct=1.0`) and unincised wood (`Ci=1.0`); no `Cb` credit is used. NDS
§§2.3.2 and 4.3.2 exclude deformation-limit `Fc⊥` from the load-duration
factor, so `CD` is not applied. `CF` also does not apply to `Fc⊥`. The
inner-frame block's `CFstudy=1.0` remains a
hypothetical final-section arithmetic input only; it neither assigns a grade
nor changes the perpendicular property. The ratios compare a *modeled cell
average* with that conditional reference. They are not code passes, bearing
allowables, or checks of actual wood stress.

Three receiver/interface combinations are parallel and one is oblique. They
are retained as **reference-only** because this packet establishes no
applicable local member-contact resistance method for those orientations. It
does not transfer dowel-fastener embedment-angle or Hankinson equations to
timber-member contact. The largest transverse comparison is for `header-post`
on `base_header` at `a1-rear`, final increment, `SPR41` (`contact_10_0`):
0.513415586831 MPa divided by 4.309223308230226 MPa gives 0.119143416367.
Its pressure rounding interval is `[0.513415549255,
0.513415624407] MPa`; the ratio interval is `[0.119143407647,
0.119143425087]`.

The material/grain map is conditional, not stock inspection. Delivered species,
grade, grain orientation, moisture, treatment and final cut conformance remain
unknown. The inner-frame block is ripped from 4×6 stock and does not inherit its
original grade; its No. 2 final-section scenario is only arithmetic. Actual
contact support area, fit, gaps, continuous support and pressure distribution
are also unknown. Cell averages do not bound actual local peak pressure. No
parallel/oblique local bearing method, complete bearing resistance, full joint
interaction or candidate acceptance is established here.

Replay from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-timber-contact-grain-applicability-attempt01/produce.py --verify
```

`--write` rebuilds `grain-applicability.json` from the frozen sources. The
one-time `--freeze-sources` mode is included for provenance; it refuses to
replace an existing manifest. This packet launches no native solver and edits
no source model or geometry.
