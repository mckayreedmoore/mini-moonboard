# Single-2×6 development baseline

The [revised all-2×6 layout](square-2x6-revised.md) now has an interactive viewer
and new render. This first failed baseline is also selectable in the viewer.

This is the current MVP development direction: start with single 2×6 members,
retain the candidate even when checks fail, and then enlarge individual members
or change their connections in response to specific findings. This is an
inspectable **failed development baseline**, not construction plans or a load
rating. The previous wide-support viewer and its evidence remain separate.

## Review package

- [Assembly STEP](../exports/square-2x6-development/square-2x6.step)
- [Wood blanks](../exports/square-2x6-development/wood-parts.csv) and
  [connection schedule](../exports/square-2x6-development/connections.csv)
- [Geometry results, including failures](../exports/square-2x6-development/geometry-audit.json)
- [Future insert-space schedule](../exports/square-2x6-development/future-insert-reserves.csv)

![Open-frame inspection view, face panels omitted](../exports/square-2x6-development/open-frame.png)

The inspection image omits the face and kicker panels to expose framing; the
STEP retains them. Hardware that misses its receiver remains visible because
this is the retained starting design. The existing website default is unchanged; this baseline is available through
the Design selector as “Single 2×6 · retained failed baseline”.

## Changes made

All 20 lumber members use single nominal 2×6 stock, actual 38.1 × 139.7 mm:
side rims, two principals, top and midpoint rails, two new lower rails, legs,
header and short posts. Face/kicker sheets and two plywood gussets remain.
No doubled or laminated substitute is introduced. Adjacent midpoint rails remain
separate receivers for the two panel edges; no composite action is credited.

Both principals have their former lower housing removed. The continuous flat
`timber_bottom_backing` and its two central retention bolts are removed. Two
square-cut lower rails fit between the rims and principals, with four nominal
ML24Z angles and their specified SDS screws. This also removes the specific
narrow-principal backing-bolt edge-distance problem rather than forcing the
old bolt into a 2×6 receiver. The new rail connections still need resistance
and installation checks.

The new lower rails occupy board stations 40–78.1 mm. Lowest LED centers are
at 19.2 mm and first hold centers at 99.2 mm. Their existing 40 mm service
reservations leave a 39.2–79.2 mm band; the rails fit with nominal 0.8 mm and
1.1 mm margins. They have **no hold/LED relief cuts**. Main-panel LED bores
remain required, and inherited service reliefs elsewhere in the frame remain.
This approach leaves a 40 mm lower panel-edge overhang, whose support and
fastener loads are unresolved. Manufacturing tolerances and actual cable
routing must not be inferred from these small nominal margins.

## Screws now, possible inserts later

The new candidate has 56 ordinary panel/kicker wood screws, 16 through-bolts,
22 purchased angle representations and 132 matching bracket screws. It has
zero installed threaded inserts. The panel screws reuse the previous nominal
#8 × 2-inch wood-screw family; effective engagement, head bearing and resistance
remain to be checked for this arrangement. The displayed major-diameter cuts
are occupied geometry, **not receiver pilot-drilling instructions**.

At all 56 panel/kicker receiver entries, the layout preserves a full solid
Ø12.1412 × 17 mm reservation for a possible later insert. All reservations
fit the nominal service-pocketed wood and clear other modeled fasteners.
Do not drill these reserves during initial assembly. The dimensional hypothesis
uses the existing [E-Z LOK 801420-13 reference](https://www.ezlok.com/ezhex-insert-801420-13),
which is a flush 1/4-20 × 13 mm wood insert, not an approved repair for this wall.
A later conversion requires inspection of damage and remaining wood, an
appropriate pilot/recess, matching machine screw and face countersink, usable
thread engagement, access and connection resistance. Space alone does not
establish that a stripped hole is repairable.

## Actual check results and next changes

| Check | Result | Next targeted response |
| --- | --- | --- |
| Square lower rails clear existing hold/LED reservations | Pass | Retain layout; check panel-edge support and installation tolerances |
| Principal lower housing removed; nominal wood-body collisions | Pass; no positive-volume wood overlap | Retain square-cut layout |
| All 56 future insert-space reservations | Pass | Preserve these spaces when changing joints |
| Existing rim bolt edges | Fail at six bolts; upper leg bolts have only 6.63 mm depth-edge clearance | Reposition/rework the bolt group within 2×6 first, or selectively deepen rims |
| Existing header/post and gusset fastener receivers | Fail at 16 member/fastener checks | Move hardware with the reduced base geometry; remove or reposition unsupported posts |
| Sloped-member bearing on shallow header | Only about 73.6% of nominal bearing area overlaps header | Change header placement/depth or the base support arrangement |
| Two rear central post/header contacts | No contact | Revise the base arrangement; retained posts are not supports for this header |
| Structural response, strength, buckling and unanchored stability | Not run for this redesigned frame | Run after defining a coherent load path; prior gravity/FE results do not transfer |

The bolt-edge screen preserves the project's reversible cross-grain assumption.
[AWC NDS Chapter 12, Table 12.5.1C](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210928_AWCWebsite_Chapter12.pdf)
provides the 4D loaded-edge basis; this is not a pure axial-withdrawal rule or
a complete connection design. The earlier
[direct-substitution screen](../fea/results/single-2x6-screw-screen.json) is
retained to distinguish stock swaps from the changed lower-rail layout.

No new global solve was spent on a frame whose base fasteners miss receivers.
The next useful step is one base/leg connection revision, followed by another
fit audit and the relevant structural checks—not reverting automatically to
4×6 principals or doubling 2×6s.

## Reproduce

```sh
uv run python -m fea.square_2x6_audit --output /tmp/square-2x6-audit.json
uv run python -m mini_moonboard.square_2x6_exports --output /tmp/square-2x6-package
uv run pytest -q tests/test_square_2x6.py tests/test_single_2x6_screen.py tests/test_screw_insert_repair_reserve.py
```

Verification: nine regression tests passed, including replay of the deliberately
failed geometry checks, full insert-space reservations and export hashes. Ruff
and diff checks passed. These are software/evidence checks, not structural passes.

Exports require a current checked-in geometry-audit source identity. New output
paths are exclusive; source and artifact hashes accompany the review package.
