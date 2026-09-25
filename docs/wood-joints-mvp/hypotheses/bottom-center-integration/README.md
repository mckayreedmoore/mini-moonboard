# Bottom-center pair against WJ18

Status: local diagnostic with contact and access findings, 2026-09-24.
The parent completed the [report](geometry.json) on retained WJ18 in 25.86
seconds. It covers the two remaining inner bottom-rail duties, two full-stock
88.9 × 88.9 × 119.7 mm cleats, eight 127 mm grip bolt positions, forty
installed CAD roles, and twelve proposed SDS replacements. All 66 panel axes
and twelve existing frame-bolt arrangements remain bound. The full integrated
layout still covers eighteen duties; this pair is not merged or accepted.

Nominal wood and installed-hardware collision checks, receiver layers,
washer seats, and native source reconstruction pass. Three contact slab
checks contain all expected net material. The left bottom-rail check contains
519.256883 of 527.648635 mm³ after discounting its two proposed bores:
98.4095945%, so that implemented full-material gate remains false. Determine
which source cuts explain the deficit and calculate the actual finite paired
face. Do not rename the gross rectangle a bearing area or infer capacity from
the remaining fraction.

The right cleat overlaps the retained G1 hold-projection access envelope by
745.512902 mm³. Both rail-nut approaches intersect the existing center
principal cleat: 9,716.015633 mm³ at row 1 and 4,188.225330 mm³ at row 2 on
each side. Several approach envelopes intersect wires, and the opposite
principal nut tools overlap at matching rows, as in the top-center study.
The report preserves every named hit. Tool-versus-tool overlaps on different
bolts may admit sequential use; hits against timber, wire, and hold-projection
envelopes need their own supported operation or geometry disposition. Clear
installed hardware alone does not close these findings.

Ten focused tests pass. The [execution](execution.json) and
[manifest](sha256.json) bind the producer, tests and retained WJ18 composition.
The report SHA-256 is
`b6bf3caf070a126919b426088bc523dfdf2322a16c1986b769f1e417bc55506e`.
The producer is frozen at
`2fd69088b0e1fffc3fa2e5390ded6bfbe2072686f30823fe0331e0ac5973c425`.

Two earlier adapter failures are preserved: the
[old-cut replay attempt](../bottom-center-pre-wj18-replay-fix/) reapplied
already removed WJ18 SDS holes to a principal; the
[wood-ID attempt](../bottom-center-before-wood-source-id-fix/) treated the
source's uncut wood list as timber-only despite its six plywood panels.
Neither completed a local report or ran a native solve. No tolerance was
relaxed to repair these input/scene errors. Mechanics, actual tool operation,
transport, cutting, drilling and release remain open.
