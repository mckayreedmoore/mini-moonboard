# PB03 retail bolt-length geometry lead

Status: **geometry lead only; no structural selection.** This note converts the
current PB03 wood-grip envelopes into nominal retail bolt lengths. It does not
qualify a bolt, nut, washer, timber connection, or completed joint.

## Length arithmetic

The conservative hardware allowance used for both grip lengths is:

- two 3/8-inch galvanized flat washers: `2 × 0.083 = 0.166 in`;
- maximum finished 3/8-inch hex-nut thickness: `0.337 in`; and
- two exposed threads at 16 threads per inch: `2 / 16 = 0.125 in`.

The total allowance is therefore `0.166 + 0.337 + 0.125 = 0.628 in`.

For the 3.75-inch rail wood grip:

`3.750 + 0.628 = 4.378 in`.

A 4-1/2-inch bolt is the calculated minimum nominal length. A 5-inch galvanized
hex bolt is the preferred geometry lead because it adds allowance for lumber,
washer, nut, and bolt-length variation. Protrusion and nearby geometry still
require verification.

For the 9-inch outer-upright wood grip:

`9.000 + 0.628 = 9.628 in`.

A 10-inch bolt is therefore required by this nominal stack calculation.

## Ordinary retail leads

The following Lowe's and Home Depot listings were current during the retail
research. Store and ZIP-code availability can change and must be checked before
any later purchase decision.

Rail-stack leads:

- Home Depot Everbilt 3/8-16 × 4-1/2-inch galvanized hex bolt,
  [model 805596](https://www.homedepot.com/p/204645572), is the calculated
  minimum-length lead.
- Home Depot Everbilt 3/8-16 × 5-inch galvanized hex bolt,
  [model 805606](https://www.homedepot.com/p/204645574), is the preferred
  geometry lead.
- Lowe's Hillman 3/8-16 × 4-1/2-inch zinc-plated hex bolt,
  [model 190205](https://www.lowes.com/pd/1000897804),
  is listed as Grade 1 and partially threaded.

Outer-upright leads:

- Lowe's Hillman 3/8-16 × 10-inch zinc-plated hex bolt,
  [model 190231](https://www.lowes.com/pd/3036218),
  is listed as Grade 1 and partially threaded.
- Lowe's Hillman 3/8-16 × 10-inch galvanized carriage bolt,
  [model 812600](https://www.lowes.com/pd/3824783),
  is an ordinary individual-product lead.
- Home Depot Everbilt 3/8-16 × 10-inch galvanized carriage bolt,
  [model 805086](https://www.homedepot.com/p/204633646), is an ordinary
  individual-product lead.
- Home Depot Prime-Line 3/8-16 × 10-inch hot-dip galvanized carriage bolts,
  [model 9064160](https://www.homedepot.com/p/310499925), are sold as a pack and
  carry the clearest listing-level material claim: ASTM A307 Grade A and
  ASME B18.5.

Matching ordinary retail hardware includes the Home Depot Everbilt
[3/8-16 galvanized hex nut](https://www.homedepot.com/p/204274098) and
[3/8-inch galvanized washer](https://www.homedepot.com/p/204284545), plus the
Lowe's Hillman
[3/8-16 galvanized hex nut](https://www.lowes.com/pd/3037535)
and [3/8-inch hot-dip galvanized washer](https://www.lowes.com/pd/3037541).

## Head, washer, grade, and thread distinctions

A hex-head through-bolt can use one ordinary flat washer under the head and one
under the nut, matching the two-washer allowance above. A conventional flat
washer generally cannot sit flat beneath a carriage-bolt head because of the
square neck. A carriage-bolt option therefore needs a separately modeled
head-and-square-neck wood interface and would normally use the flat washer only
under the nut. The two-washer arithmetic must not be treated as a carriage-head
detail.

The Lowe's hex-bolt listings identify Grade 1 retail products. The Prime-Line
carriage-bolt listing identifies ASTM A307 Grade A and ASME B18.5. Those claims
are not interchangeable, and an ordinary retail nut listing does not by itself
establish a matched ASTM nut grade or proof load.

For an ASME B18.5 carriage bolt longer than 6 inches, the standard thread-length
formula is `2D + 1/2 in`. At `D = 3/8 in`, that is `1.25 in`, placing the nominal
thread start about 8.75 inches from the head on a 10-inch bolt. This supports
the length-screen inference for a 9-inch grip, but the exact stocked product's
threaded and unthreaded lengths still require confirmation.

Grade or thread documentation establishes only limited fastener properties and
dimensional clues. It does not establish wood bearing, splitting, row or group
action, washer bearing, carriage-neck crushing, threaded-section shear, cyclic
performance, or complete PB03 joint capacity.

## Release boundary

The geometry leads are a 5-inch galvanized hex bolt for each 3.75-inch rail
stack and a 10-inch bolt for each 9-inch outer-upright stack. They are not a
structural selection or purchasing recommendation. No purchase, drilling,
fabrication, construction, or structural release follows from this note.
