# Current source wording reconciliation

October 1, 2026. This additive primary record corrects source attribution
and interpretation in the older notes identified by the
[secondary handoff](../bottom-quarter-inch-resistance-basis-2026-10-01/source-corrections-for-primary.md).
Those notes and review receipts remain byte-preserved inputs to existing
packets. For the identified wording, read this record together with the
[current source note](../bottom-quarter-inch-resistance-basis-2026-10-01/source-note.md).
No equation, material scenario, source response, geometry or criterion
disposition changes.

The approximate bolt relation `Fyb ≈ (Fy + Fu)/2` appears in nonmandatory
NDS Appendix I.4, printed page 185; attribution to a separately published
Commentary is inaccurate. I.4 discusses many commonly available bolts
without an explicit diameter qualifier, then separately discusses lag-screw
samples at diameter at least 3/8 inch. Table I1's parenthetical is ambiguous
for bolts. These pages do not establish an unambiguous blanket exclusion
of quarter-inch bolts, or a guaranteed bending-yield minimum for the exact
quarter-inch Grade 5 product. The inspected Chapter 12 Table 12A starts
its bolt-diameter rows at 1/2 inch. An unavailable TR-12 PDF and its search
excerpt cannot settle a different source requirement.

The primary checked the pinned Appendix PDF pages 20–21 and Chapter 12
pages 17–18 and 23; Table I1 and Table 12A were also visually inspected.
The PDF hashes match the current source note. A fresh read of the
[Lawson FA21103 product page](https://www.lawsonproducts.com/products/hex-cap-screw-grade-5-1-4-20-x-8-fa21103)
confirmed the catalog's 1/4-20 × 8 inch Grade 5 partial-thread description,
J429 statement, 120 ksi tensile minimum and B18.2.1 dimensional statement.
This is a catalog lead, with no adoption or delivered-part observation.

The primary independently replayed the complete bottom packet byte for
byte, checked its stable receipt hashes, and ran its seven focused tests
and Ruff. Its three independent Luna/max reviews are recorded in
[validation.md](../bottom-quarter-inch-resistance-basis-2026-10-01/validation.md).
The report SHA-256 is
`d9740027cc0d72295e21986ba0711be767ccab043822e0a28f91fd89aa9ef962`.

Both 45 and 106 ksi remain unadopted scenarios. For A1 full-load `side_1`,
the unadjusted lateral ratios are 1.094508867 and 0.713136407 respectively;
the latter is a required combined-factor budget, not an established group
or geometry factor. The unity-factor Mode IV equality threshold is
53,907.734650 psi. The two rail bolts change governing mode at 106 ksi,
so a universal square-root rescaling would be incorrect. All signed axial
ties, interface and complete-body wrenches remain present. Adjusted joint
resistance, product-specific bending yield and acceptance remain unresolved.

The current [kicker edge-obligation note](../../current-kicker-edge-obligation.md)
contains a count attribution error in its mechanics paragraph: “18 Hillman
axes per kicker.” The authenticated final panel register instead has 18 kicker
axes total, nine per kicker: five header, two outer-post and two center-post
axes on each side. The primary independently counted the exact axis IDs in
`receiver-transfer.json` at SHA-256
`0ac0e30d582322f8919277aabec3af134c7bf5ecb2b0523d649622bcd4a47534`.
The full panel/kicker inventory remains 66 Hillman axes. The count correction
changes no station, receiver, purchase policy or adopted criterion. Preserve
the pinned original note and read its edge/load-path requirements with this
additive correction; continuous direct backing remains unprescribed.
