# Independent review: four outer-post hardware axes

**Reviewed:** 2026-09-25. **Scope:** current four `knee_outer_*_post_*`
axes, stack fit and source-backed hardware listing. This note reviews the
conditional option only; it selects no hardware or capacity.

## Pinned basis

The reviewed [option](../current-outer-post-hardware-option.md) is SHA-256
`40dbdc2eded704a61f689e3caaceb5461f3fb69398d60b0374f41151a4aecf01`.
Its [geometry source](evaluation-resume-2026-09-24/grip-screen-attempt02.json)
is pinned as `9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a`;
the [hardware schedule](../current-hardware-schedule.md) is
`47a1de21705570cfd23fb493c640d8983945ee410623e15484cf53ed7596bffa`.
The frozen rows confirm four axes, 76.200 mm wood grip and a 101.600 mm
unthreaded shaft occupancy envelope. The latter is model geometry, not a
delivered-length condition.

Using the pinned 76.200 mm grip, two Type A Wide washer limits of
1.2954–2.032 mm, and finished-nut limits of 5.3848–5.7404 mm, the stack
recalculates to:

| Quantity | Recalculated range / limit |
| --- | ---: |
| Nut bearing face | 78.7908–80.2640 mm |
| Far nut face | 84.1756–86.0044 mm |
| Far wood face | 77.4954–78.2320 mm |
| `LG,max` | 82.5500 mm |
| Far nut face + 3.175 mm physical-tip projection | 89.1794 mm |

The reported bearing-face distances to `LG,max` (3.7592 mm at the earliest
seat and 2.2860 mm at the latest) are correct. `LG,max` lies inside the
physical nut interval for all screened stack limits. That is a conservative
gage-coordinate warning, not an actual full-form-thread location: full
functional engagement of the matched nut can only be established from an
applicable part drawing or matched-pair fit evidence. The option correctly
does not require the full-form thread to cover the nut's physical chamfered
faces or the added tip tail.

## Corrections verified in the reviewed option

The current version converts the stated 3.94 in minimum overall length to
100.076 mm. This yields 14.0716 mm beyond the 86.0044 mm maximum nut face
and 10.8966 mm beyond the 89.1794 mm tip target. It also describes the
3.0480 mm and 3.7592 mm nut shifts as reaching `LG,max` with zero clearance,
and says additional movement is needed for positive clearance.

The close-out sentence asks for a physical bolt-tip projection of at least
3.175 mm past the far nut face and explicitly says this tail need not have
full-form thread. That resolves the earlier conflicting phrase “adequate
thread beyond the nut.”

## Primary listing check and status

K.L. Jack's [25C400HCS5Z listing](https://www.kljack.com/products/25c400hcs5z/)
and current category entry identify a 1/4-20 × 4 in zinc Grade 5 cap-screw
SKU and a 100-piece package. The exact item page did not return full thread
specifications in the source lookup; the option appropriately labels the
4.5 in same-family 2A/partial-thread data as supporting evidence only and
leaves exact-item class and functional thread location open. Its
[25CNFH5Z nut listing](https://www.kljack.com/products/25cnfh5z/) supports
the listed 1/4-20, Grade 5, ASME B18.2.2 / SAE J995, Class 2B, 7/32 in
nominal nut. It does not prove a matched pair.

The [25NWUS washer listing](https://www.kljack.com/products/25nwus/)
confirms a 1/4 in plain USS washer to ASME B18.21.1 Type A Wide, 0.312 in
listed ID, 47/64 in OD, 0.051–0.080 in thickness, low-carbon steel, plain
finish with light protective oil, and a 100-piece package. The option
identifies its material and finish accurately and does not assign washer
capacity. The cited [Type A Wide dimension sheet](https://www.fastenal.com/content/product_specifications/FW.LC.USS.A.P.00.pdf)
supports the ID tolerance used for the washer-to-shaft comparison.

The catalog facts support a conditional sourcing scenario only. No washer
grade/capacity, delivered stock, matched-nut fit, or current authority
changes follow from them. The reviewed option's geometry, arithmetic and fit
interpretation are publishable within its stated conditional scope.
