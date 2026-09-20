# Center-tongue shared post bolt: retail length screen

**Status: stack screen only; no selection or fabrication approval.** This sidecar uses
the current [center-tongue nominal pose](hardware_first_center_tongue.json): one
190.5 mm post between two 4.55 mm HL33 vertical legs. The opposed plates share
one 1/2-in post bore axis. The model is ideal CAD geometry, not delivered stock.

Retail examples are [8 in Everbilt zinc plated A307 hex bolt](https://www.homedepot.com/p/204273630),
[10 in Everbilt galvanized A307 hex bolt](https://www.homedepot.com/p/204281591),
and [12 in Everbilt zinc plated A307 hex bolt](https://www.homedepot.com/p/204633168).
All are listed as 1/2-13. The 8 and 12 in pages list 6 in of thread; the 10 in
page does not establish its thread length. The Everbilt pages identify
`A307`, but not the **Grade A** subtype that the
Simpson HL catalog explicitly requires; they are dimensional leads only,
not a selected compliant bolt schedule. Home Depot separately lists an
[exact Grade A Prime-Line 12-in bolt](https://www.homedepot.com/p/310465147),
but this Everbilt thread-length evidence cannot be transferred to it.
The illustrative matching-thread
[Hillman 1/2-13 galvanized hex nut](https://www.lowes.com/pd/1-2-in-x-13-Galvanized-Steel-Hex-Nut/3037536)
does not have a reliable SKU-specific published thickness. The
[Lindstrom ASME B18.2.2 full-hex-nut table](https://cdn.mscdirect.com/global/images/ProductDataSheet/pds_sku_254996_productbrochure_manual%20data%20sheet.pdf#page=85)
provides 0.427–0.448 in for the 1/2-in nominal size. This is a standard-pattern
proxy, not proof the Hillman nut meets that size. The example
[Everbilt 1/2-in galvanized flat washer](https://www.homedepot.com/p/204276406)
lists 0.109 in nominal thickness and 1-3/8 in OD; use one under each bearing
face for the arithmetic. Finish pairing and delivered dimensions remain open.

`190.5 + 2(4.55) = 199.6 mm` wood plus plates. Adding two listed washers gives
`205.1372 mm` from bolt-head bearing face to nut bearing face. Bolt length is
measured below the head; the head height is therefore excluded. Subtract the
nut thickness range from each nominal bolt length:

| Hex bolt | End beyond full nut, nominal mm | Length / thread finding |
| --- | ---: | --- |
| 8 in | −13.3164 to −12.783 | Too short for the two-washer stack and full nut. |
| 10 in | +37.4836 to +38.017 | Length available; thread start/runout unpublished. |
| 12 in | +88.2836 to +88.817 | Length available; 6 in listed thread begins nominally 52.7372 mm before nut face, runout unverified. |

For the 10 in SKU, usable thread must extend at least `254 − 205.1372 =
48.8628 mm` back from the tip merely to reach the nut face. Full engagement
also depends on nut height and thread runout. The 12 in listed 6 in thread
places its nominal smooth-to-thread transition at 152.4 mm below the head;
the nut face is at 205.1372 mm. Neither statement bounds delivered transition
location or proves full effective threads throughout the nut. The 8 in bolt is
short even before a thread-engagement judgment.

No head/nut CAD collision or tool-access pass is claimed. The current pose
supplies the bore and ideal plate/wood solids, but no qualified delivered head
height, nut SKU dimensions, washer tolerance, installed protrusion allowance,
or wrench/socket swept envelope. These are necessary to evaluate nearby wood,
plates, and access. This screen does not approve drilling, steel fabrication,
lap joints, connector action, or any structural capacity.
