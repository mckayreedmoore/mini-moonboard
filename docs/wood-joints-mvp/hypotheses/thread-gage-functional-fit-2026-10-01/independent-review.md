# Independent review: B18.2.1 thread/gage coordinate note

Reviewed the frozen [`source-note.md`](source-note.md), SHA-256
`69f589836df358c14dde95ae3593aa8cfb5498a1b91dfe521d7d0939ffb50a5b`, against
the local ASME B18.2.1-2012 PDF, SHA-256
`4c7bcb75223b7e89fc27f132bc44e8b422ba672c97f7803259a24fab6bd99ba0`, and the
existing project hardware envelopes. The note's conditional endpoint-coordinate
interpretation is supported. No material calculation or source-boundary issue
remains in the reviewed version.

## Dimensional rows

I independently checked the four rows using the 1/4-in entries in B18.2.1
Table 12, Table 13 length tolerances, and 25.4 mm/in. The nut-stack coordinate
envelopes are the previously published project values; the table comparisons
below do not treat those envelopes as measured parts or gage travel.

| Conditional case | Table 12 `LG,max / LB,min` | Table 13 minimum length | `a − LG,max` | `L_min − b` |
| --- | ---: | ---: | ---: | ---: |
| BG001, 4 in: envelope 78.7908–86.0044 mm | 3.25 / 3.00 in | 3.94 in | −3.7592 mm; lower enclosure condition fails | +14.0716 mm |
| BG001, 3.75 in: same envelope | 3.00 / 2.75 in | 3.69 in | +2.5908 mm | +7.7216 mm |
| BG045, 8 in: envelope 179.6908–186.9044 mm | 7.00 / 6.75 in | 7.82 in | +1.8908 mm | +11.7236 mm |
| BG003, 9.5 in: envelope 218.4908–225.7044 mm | 8.50 / 8.25 in | 9.32 in | +2.5908 mm | +11.0236 mm |

The row values and conversions are correct. Table 13 gives −0.06 in for the
1/4-in 4-in and 3.75-in screw classes, and −0.18 in for the two lengths over
6 in. The 3.75-in BG001 row is correctly labeled a conditional dimensional
alternative, not a selected product or approved model change. Its additional
`LB,min` and tip-target comparisons also reproduce the published packet
comparators: +1.143 mm and +3.9116 mm. The BG001 4-in row correctly says the
endpoint condition fails and that this alone does not establish the actual
item is unfit. The reviewed version now makes the general endpoint statement
conditional (“when satisfied”), so it does not imply all four rows pass.

## Interpretation and limits

The standard definitions support the note's distinctions: `LG` is measured to
the face of a hand-assembled special GO thread ring gage; `LB` terminates at
the last thread scratch or rolled-thread extrusion angle; `LT` is a reference
dimension. The cited Table 12 values therefore do not bound the gage's working
thread profile, nut travel, first full-form thread, or effective engagement.
The note also correctly keeps Table 13 overall length (measured to the extreme
end including the point) separate from usable thread length. Section 2.5.2's
pre-coating Class 2A default, coating-allowance limit, and post-coating GO/NOT
GO gauges are described without converting them into a matched-part fit.

The product evidence is represented conditionally: BG045's Lawson lead cites
B18.2.1 dimensions, BG001's source callout is conditional on conformance, and
BG003's HC5127 listing does not claim B18.2.1 conformity. The note does not
turn the 3.75-in standard row into a procurement claim. It also correctly
states that the B18.2.1 §4.3 washer-face measurement 0.004 in below the bearing
plane is not itself a flat contact-footprint bound. B18.2.2 chamfer/contact
dimensions remain unasserted because no local source copy or hash is available;
the existing finished-hex nut envelope is clearly carried forward as a project
input rather than revalidated contact geometry.

This review establishes no delivered-part conformity, actual threaded travel,
matched 2A/2B engagement, contact footprint, fit acceptance, capacity, or joint
acceptance. The B18.2.1 copy inspected here is the identified third-party
mirror, not an ASME-hosted download; its bytes match the hash recorded in the
project source correction.
