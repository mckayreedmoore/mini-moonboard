# Upper-left panel hotspot: one complete saved load path

The frozen A12-rear nominal-clearance route loads the unchanged
`round_panel_upper_left_edge_2` screw into `base_rail_top` with
**1,871.2512062195326 N axial tension** and simultaneous
**726.6105292217607 N lateral force**. Axial tension acts through both
the head/plywood route and the thread/timber route. They need separate
resistance comparisons.

The existing route exceeds the favorable retailer-nominal head references
of 930.222–984.128 N. This is a conditional design-reference exception,
not an observed screw or panel failure. A larger head or washer alone must
not be called a complete correction: timber withdrawal and simultaneous
lateral action remain part of the same screw load path.

The parent completed the finite saved-data producer once. All twelve ties,
every incident contact and lateral action, actual modeled receiver
identities, and adjacent-tie diagnostics are retained. The complete panel
force/moment balance closes within **7.275957614183426e-12 N** and
**9.415089152753353e-9 N·mm**. Only `edge_2` exceeds the stated favorable
head reference in this exact state. This packet changes no source force,
receiver, screw axis, geometry, count, material or stiffness.

## Frozen state and physical route

The source is the six-case 250 lb × 2 envelope with signed 300 N horizontal
actions, recorded dead load and the **100 mm front-face lever**. Only
`a12-rear`, `main_upper_left`, gap scale 1 is consumed here. The later
50 mm, panel orientation/count and contact refinement comparisons are
not mixed into this state.

At the governing screw, the source point is
`[-835.075, 1523.3394035191589, 2141.899800434121]` mm. Saved modeled opening
is 0.6957154863778605 mm. The withdrawal stiffness is the unmeasured
2,689.678816784642 N/mm hypothesis. These are model quantities, not observed
installation slip or Hillman test data.

The complete route is: the force and couple at hold A12 enter the flexible
upper-left plywood; all panel contacts, seams and twelve screw ties act
together; each tie transfers axial and lateral action to its recorded timber
receiver; the receiver's frame joints carry those actions onward. Contacts
can carry compression only. A nearby bearing cell is not assigned as the
governing screw's sole opposing partner. Source local free couples and
centroid-offset moments are retained in the complete panel balance.

The producer reuses the existing `panel-contact-sharing.py` extraction API
in a private imported module for this body, case and frozen frame. It does
not rerun that producer's twelve/twenty-screw comparison. The twelve saved
head-check records independently bind each tie's axial and lateral forces.
Receiver grain/axis checks identify whether the retained side-grain
withdrawal equation applies.

## Completed panel and receiver accounting

All actions act on `main_upper_left`. Moments below use the saved panel datum
`[-675.7612351514234, 1182.3986986322998, 1721.381648966736]` mm.
Tables display forces to 0.001 N and moments to 0.001 N·m; the pinned output
retains complete signed N/N·mm values and local free couples.

| Action | Fx, N | Fy, N | Fz, N | Mx, N·m | My, N·m | Mz, N·m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| External panel wrench | 0.000 | 300.000 | -2404.873 | -891.157 | -751.732 | -103.032 |
| All screw axial reactions | 0.000 | -2809.691 | 2357.611 | 1536.086 | 266.347 | 317.420 |
| All screw lateral reactions | -535.194 | 19.839 | 23.644 | -0.282 | -5.652 | -1.634 |
| All contact reactions | 535.194 | 2489.851 | 23.618 | -644.647 | 491.037 | -212.754 |

The panel's outward-normal external action is 1,775.635668718094 N.
All screw tensions total 3,667.791012718217 N; opposing normal contacts
total 1,892.1553440001144 N. Their signed difference balances that external
normal action. Thus screw tension can exceed the net external normal force
because the source includes a compression/tension couple. This is the saved
response, not an additional applied load or equal force-per-screw split.

Every modeled receiving body is retained below. The last three bodies carry
contact-only actions in this panel state; their full signed vectors still
participate in balance even when panel-normal action is zero.

| Receiver | Contact cells / active | Screw ties | Sum of screw tension, N | Signed normal contact action, N |
| --- | ---: | ---: | ---: | ---: |
| `base_principal_center_left` | 24 / 7 | 3 | 170.278 | 204.102 |
| `base_rail_service_upper_left` | 22 / 6 | 2 | 216.513 | 244.388 |
| `base_rail_top` | 24 / 6 | 3 | 2410.903 | 1378.495 |
| `base_side_left` | 26 / 3 | 4 | 870.097 | 65.172 |
| `lumber_leg_left` | 4 / 2 | 0 | 0.000 | 0.000 |
| `main_lower_left` | 26 / 10 | 0 | 0.000 | 0.000 |
| `main_upper_right` | 26 / 0 | 0 | 0.000 | 0.000 |

The complete same-state screw inventory is:

| Upper-left screw suffix | Receiver | Axial T, N | Lateral V, N |
| --- | --- | ---: | ---: |
| `center_1` | `base_principal_center_left` | 36.154 | 79.379 |
| `center_2` | `base_principal_center_left` | 51.927 | 31.757 |
| `center_3` | `base_principal_center_left` | 82.198 | 5.524 |
| `center_4` | `base_rail_top` | 259.805 | 391.614 |
| `edge_1` | `base_rail_top` | 279.846 | 209.469 |
| **`edge_2`** | **`base_rail_top`** | **1871.251** | **726.611** |
| `rim_1` | `base_side_left` | 3.293 | 215.325 |
| `rim_2` | `base_side_left` | 0.000 | 189.812 |
| `rim_3` | `base_side_left` | 192.412 | 341.254 |
| `rim_4` | `base_side_left` | 674.393 | 1244.301 |
| `service_1` | `base_rail_service_upper_left` | 116.584 | 26.674 |
| `service_2` | `base_rail_service_upper_left` | 99.929 | 19.092 |

All twelve receiver-grain/screw-axis dot products satisfy the source's
side-grain interpretation. That verifies applicability of this geometry
branch; it does not establish the purchased screws' thread or steel properties.

### Hotspot contacts and adjacent ties

The nearest active top-rail cell is `contact_82_17`, 35.42464082293273 mm
from `edge_2` in the panel plane. It carries 853.0669574621274 N compression
at offset `[+34.11095681993595 X, -9.557604420682882 T]` mm. Its paired cell
`contact_82_16` at the opposite T offset is open. The next cells on the
other X side, `contact_82_18/19`, are also open. These contacts are included
in the complete balance, not used to invent a two-force prying ratio.

The nearest other tie is `rim_4`, **365.075 mm** away, into `base_side_left`.
Next are `edge_1` at 400 mm into `base_rail_top`, `rim_3` at
559.766499000054 mm into `base_side_left`, and moved `center_4` at
765.075 mm into `base_rail_top`. Their existing loads are shown above.
Neither a neighboring tie's spare reference nor a nearby bearing cell
establishes compatible redistribution of `edge_2`'s force.

## Reference scope and required correction

The [head worksheet](head-reference-basis.md) already supplies the current
Hillman 42605 retailer-nominal 9.017 mm head diameter, the plywood G and
net-thickness branches, and the explicit favorable connection-duration
scenario `CD=1.6`, `CM=Ct=1`. These remain hypotheses. The parent owns any
duration adoption; this packet introduces no new factor or Hillman rating.

The pinned NDS Chapter 12, printed p.90, Table 12.2F covers head diameters
**0.234–0.500 in (5.9436–12.7 mm)** and net side-member thicknesses
**5/16–1.5 in (7.9375–38.1 mm)**. Section 12.2.5.1 restricts the equation
to that range. The inverse head diameter required at unchanged panel
thickness is outside the diameter range. It is an algebraic diagnostic,
not a permissible resistance assignment to a bigger washer or head.

The second head equation also supplies a thickness-independent ceiling
for the existing 9.017 mm head. Extra plywood thickness alone cannot be
assumed to close this unchanged-head route.

| Head branch: G=.50, CD=1.6, CM=Ct=1 | Adjusted reference, N | T/reference | Inverse diameter diagnostic, mm | Reference at maximum tabulated 12.7 mm head, N |
| --- | ---: | ---: | ---: | ---: |
| Net plywood 17.25625 mm | 930.2216248187035 | 2.011618689883964 | 18.138765726683705 | 1310.1713025615545 |
| Gross plywood 18.25625 mm, no countersink reduction | 984.127984822685 | 1.901430743844445 | 17.14520101724536 | 1386.0957532713874 |

Even the maximum tabulated head diameter at unchanged panel thickness remains
below 1,871.251 N. The existing 9.017 mm head's thick-side-member ceiling is
**1,215.18412038975 N**, also below that demand. No larger washer or changed
plywood thickness is assigned an unproved capacity by this calculation.

For timber withdrawal, the saved No.10 cut/rolled side-grain equation and
G/penetration scenarios are reused. The current 63.5 mm nominal length
minus 18.25625 mm plywood leaves at most **45.24375 mm gross timber
penetration**. A tip or unthreaded segment can make the effective thread
length smaller. Nominal screw length is not delivered effective thread.

The simultaneous-action requirement is retained from NDS §12.4:

```text
R = hypot(T, V)
T²/(R W′) + V²/(R Z′) ≤ 1
```

Here W′ is the adjusted timber withdrawal reference and Z′ the adjusted
lateral reference. Head pull-through is a separate comparison. Where the
withdrawal term is already at least one, no finite lateral reference can
close this combined comparison. No Hillman lateral resistance is supplied
by the current evidence; the producer reports the required reference,
without assigning a product capacity.

The completed withdrawal/combined-action comparisons at the most favorable
retained 45.24375 mm effective-thread hypothesis are:

| Timber G; CD=1.6 | W′, N | T/W′ | T²/(R W′) | Required Z′, N |
| --- | ---: | ---: | ---: | ---: |
| .45 | 1390.1279156914577 | 1.3461000136010948 | 1.2548201213792547 | No finite value closes this branch |
| .50 | 1716.207303322787 | 1.0903410110168867 | 1.0164042983171964 | No finite value closes this branch |
| .55 | 2076.610837020573 | 0.9011082735676748 | 0.8400035523282613 | 1643.8609754022884 |

The .55 timber sensitivity is separate from plywood G=.50; it does not
establish the current timber's assigned specific gravity. All shorter
retained penetration branches remain in the output.

At timber G=.50 and CD=1.6, effective penetration must be **strictly greater
than 45.98594197198865 mm** even to admit a finite Z′ in this simultaneous
comparison. The current gross ceiling is only 45.24375 mm. The separate
axial-only comparison would require **49.33111611719527 mm** effective
thread. These facts make the thread route an additional declared exception,
even before assigning actual Hillman lateral or head resistance.

Keeping the saved forces requires a **changed fastening assembly** with
independently supported head pull-through resistance at least equal to the
axial demand, effective threaded timber embedment and lateral resistance
that satisfy the same-state interaction, and compatible head/seat geometry.
The producer includes one 76.2 mm nominal-length requirement example to
make the embedment/lateral target concrete. It neither selects a replacement
fastener nor qualifies a longer Hillman screw. A washer or larger head needs
its own supported resistance route; its outside diameter does not become
a permitted NDS head diameter automatically.

For that one requirement example, 76.2 mm nominal length minus the panel
thickness gives **57.94375 mm gross penetration**. Only if that entire
length were effective thread would the reused No.10/G=.50/CD=1.6 equation
give W′ = **2197.9497042554995 N**. It would then require Z′ at least
**1274.4724369857972 N**, plus an independently supported head pull-through
reference of at least **1871.2512062195326 N** in the actual panel/seat.
This is a concrete target for a changed fastening assembly, not evidence
that any product, longer Hillman screw or washer satisfies it. Actual
thread length, head/seat compatibility, steel and occupancy are unproved.

Such a fastening change would alter the purchased screw policy. If all
66 purchased Hillman screws must instead remain the attachment system,
the physical alternative is a changed backing/tie load path that reduces
individual demand through a new compatible response. The current saved
route supplies no corrected sharing, so this worksheet cannot prescribe
another screw position or call an uncalculated receiver change sufficient.
No geometry, procurement or installation change is made here.

## Engineering receipt

Core source identities are unchanged:

| Input | SHA-256 |
| --- | --- |
| `frame-250-attempt02/comparison.json` | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| Same response, `response.npz` | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| `operators-attempt02/model.json` | `b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626` |
| `operators-attempt02/row-identities.json` | `cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27` |
| `operators-attempt02/model-inputs.json` | `e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc` |
| `panel-contact-sharing.py` | `8fd353bb515ef4b453bb2dbf820e087c506a46f5356b5fbcf0ffb28053c3e62f` |
| `rawlocal/head-check/attempt01/screw-states.csv` | `30b34cdf7400afa909e35efc36ea308da4089987d61eb6f8e2419ab096572989` |
| `../panel-attachment/attachment_screen.py` | `c2acb48370cecb3964172e8ab82d3c8999e2836e97025e1bde778bc03cf6b9dc` |
| `../../upper-block-strength-2026-10-01/source-cache/chapter12-2024-awc-20260911.pdf` | `53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f` |
| `panel-path-reconciliation.py` | `56047e6258b6c5d45013686a8e553c07ff5b7ab23b31936bb2bb3c9da3b1af1d` |

Table 12.2F was inspected from that cached primary PDF. Its source page
image is kept only in the owned ignored rawlocal directory. Existing head
and simultaneous-action equations are reused from the authenticated
source helpers. No new supplier search was performed.

Parent executed the frozen producer once. Result path:

`docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/panel-path-reconciliation/attempt01/result.json`

Result SHA-256:
`067070ff35275cb7c994a81db48d47d343a3e6a00dc4e2410098b43dedd0dea2`.

All seventeen consumed source pins were authenticated. The saved producer
snapshot matches the unchanged `56047e62…af1d` producer byte-for-byte.
The output preserves every signed incident action, complete receiver
wrenches, all twelve tie records, the twelve retained withdrawal branches,
the exact hotspot contact/adjacent-tie diagnostics and requirement arithmetic.
Raw evidence is local-only; these numerical tables remain in the maintained
packet for fresh clones.

Completed parent execution command, recorded for provenance:

```bash
uv run --no-sync python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/panel-path-reconciliation.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/panel-path-reconciliation/attempt01
```

The ignored output contains `result.json` and the exact executed
producer snapshot. Complete-joint acceptance, hardware selection, geometry
change and physical-release flags remain false. No frame/native/CAD runs,
software tests, review loop, shared edits, staging or commits are performed
by this worker. Parent owns execution, integration and publication.
