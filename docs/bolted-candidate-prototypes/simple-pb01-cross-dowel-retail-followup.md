# PB01 cross-dowel retail follow-up

21 September 2026. Scope: factory 1/4-20 cross dowels ordinarily listed by Lowe's or
Home Depot. Public sources only; no supplier contact or physical sample. This is a supplementary public-source screen to the retained\n[cross-dowel trial](simple-pb01-cross-dowel-trial.md); no previously measured SKU\nproperties are inferred.

## Evidence and disposition

| Product | Drawing | Resistance | Disposition |
| --- | --- | --- | --- |
| [Hillman 880543/44/45][h] | None | None | Fit screen only |
| [Everbilt Type F 817818/28][f] | None | None | Thread fit for 817828 only |
| [Everbilt 801914/24][e] | None | None | Availability only |
| [Stafast JCD14201606][s] | Catalog geometry | None | Separate reference |

The [Hillman 880543 listing][h] gives 1/4-20 zinc-plated steel; the 880544 and
880545 variants have nominal 3/4 and 1/2 in lengths. A Hillman answer on the
880543 page gives OD 0.394 in and overall length 0.630 in. Its “All-Purpose”
grade field is a retail category, not a mechanical grade. No axis, engaged length
or proof load is supplied.

[Everbilt Type F 817818][f13] and [817828][f] list 13 and 16 mm lengths.
The 817828 page calls out 1/4-20 × 16 mm, with supplier confirmation of the
thread. Zinc plating is specified; base metal, axis, engagement and rating are
not. “Type F” alone establishes no strength class. The 817818 thread needs
independent confirmation for design use.

[Everbilt 801914][e14] and [801924][e] are distinct 1/4-20 zinc-plated
four-pack listings. The 801914 listing says steel, but neither has a part
drawing, grade or proof load. Distinct SKUs are not presumed interchangeable.

[Stafast's own table][st] gives JCD14201606 as 1/4-20, OD 0.394 in,
length 0.630 in and dimension `L1` 0.236 in; its [family page][sf] says steel.
No grade or proof/ultimate load is given. The two matching dimensions do not
identify the Hillman item as Stafast-made or prove equal axis, thread form,
material or process.

Search paths tested: Lowe's/Home Depot model numbers and cross-dowel category listings;
SKU/model plus UPC, alternate “dowel nut,” “joint connector” and “Type F” names;
Hillman/Everbilt drawing and PDF searches; Stafast's own catalog; barrel-nut test
standards and published pull-out work. The numeric model searches did not yield a
defensible retail-to-Stafast identity. The relevant published
[NASM1312-32 Method 32][nas]
defines a tensile test of the barrel nut itself; its public description supplies
neither a test result for these products nor strength of the installed joint.
Published furniture/wood dowel pull-out studies concern different fasteners and
substrates, so their loads cannot be assigned to PB01's cross dowel.

**Assessment:** No exact store part has enough public axis, thread-engagement and
strength information for a bounded same-geometry resistance calculation. The
closest grounded path is a part-number-specific manufacturer drawing plus a
part-number-specific material/proof requirement or Method 32 result, followed by
PB01 joint checks for bolt, bearing, tear-out and substrate. Stafast establishes a
geometry path, not a graded-strength route. Do not apply generic nut-grade charts
to any of the retail parts. No candidate is approved on this evidence; no
calculation script is warranted without a published resistance input.

[h]: https://www.lowes.com/pd/Hillman-20-x-5-8-in-Slotted-Drive-Zinc-plated-Barrel-Nut/3012559
[f13]: https://www.homedepot.com/p/204281672
[f]: https://www.homedepot.com/p/204281673
[e14]: https://www.homedepot.com/p/204276112
[e]: https://www.homedepot.com/p/204276113
[s]: https://shop.stafast.com/cross-dowels/cross-dowels-with-1-hole/jcd14201606
[st]: https://shop.stafast.com/cross-dowels/cross-dowels-with-1-hole
[sf]: https://shop.stafast.com/cross-dowels
[nas]: https://store.accuristech.com/standards/aia-nasm1312-32?product_id=2905400
