# Uncut front-joint preflight

Date: September 14, 2026. Candidate: `compact-floor-uncut-development`.
This review is limited to the existing ⅜-inch, 8½-inch bolt and Carr Lane
CL-8-FW washer option. It does not select hardware, release drilling, change the
modeled geometry, or qualify the connection.

## Decision

The arrangement is suitable as an explicit assumption for obtaining the first
uncut-frame diagnostic demands. It is **not presently qualifiable as a delivered
connection**. The placement and washer-perimeter arithmetic passes, but the
fabrication error envelope does not guarantee registration of two separately
drilled nominal bores. The bolt body and usable-thread limits require inspection
of the delivered part. Most importantly, Carr Lane publishes no minimum
through-thickness material strength for calculating CL-8-FW washer bending.

This is a supported stop, not a search for more hardware. The exact material
blocker is a manufacturer-supported minimum core/through-thickness yield basis,
an applicable published washer resistance, or representative test evidence for
CL-8-FW. Surface case-hardening alone is not a plate-bending resistance value.
Actual front-joint forces are intentionally obtained in the next diagnostic task;
they are not a prerequisite to running that solve.

## One arrangement

Use the order **bolt head → CL-8-FW → 6×6 post → 2×6 runner → CL-8-FW →
⅜-16 Grade 5 nut**, with the nut and tip facing outward. The wood grip is
177.8 mm: 139.7 mm of post and 38.1 mm of runner.

The [Carr Lane product page](https://www.carrlane.com/product/clamping-hardware/washers/flat-washers)
was retrieved on September 14, 2026. Its current tables identify CL-8-FW for a
⅜-inch or M10 bolt with 1-inch OD, 13/32-inch ID and 3/16-inch thickness, and
describe the steel version as 1010 steel, case hardened, black oxide. Those
tables do not state minimum yield, hardness, case depth or core properties.

The bolt and nut identities remain those recorded in
[the catalog option](floor-uncut-front-hardware-options.md): Grainger 29DK47,
⅜-16 × 8½ inches, SAE J429 Grade 5, with the retained ⅜-16 Grade 5 nut. Direct
retrieval of the linked Grainger product and drawing routes returned error-page
content during this preflight, so this review makes no new assertion of current
availability or guaranteed body/thread geometry. The recorded catalog evidence
is adequate to define the investigation, but not to waive delivered-part checks.

## Reproducible combined envelope

Run:

```sh
uv run python scripts/floor_uncut_front_preflight.py
```

The script uses the existing nominal geometry and the proposed project receiving
bounds from the catalog option. It performs no CAD build or structural solve.

| Check | Conservative result | Required result | Status |
| --- | ---: | ---: | --- |
| Bolt pitch after two independent 1 mm position errors | 38.500 mm | 38.100 mm | Pass by 0.400 mm |
| Tight 4D or 7D timber boundary after 1 mm drill and 2 mm cut errors | — | — | Pass by 0.143588 mm |
| Maximum-OD washer to raw boundary, including drill/cut error and maximum washer float | 24.171988 mm clear | Nonnegative | Pass |
| Adjacent maximum-OD washers, including drill errors and maximum washer float toward each other | 10.356800 mm clear | Nonnegative | Pass |
| Relative axes of two ideal parallel 11.1125 mm bores for a nominal 9.525 mm bolt | 1.587500 mm maximum | 2.000 mm independent-error envelope | **Not guaranteed; short by 0.412500 mm** |

The 0.143588 mm timber margin is almost entirely consumed by the stated errors.
Stock undersize, datum error and another drilling allowance cannot be added to
it. The 4D/7D placement use also remains conditional on the actual solved force
directions and applicable NDS geometry provisions.

The registration comparison is separate from bolt spacing. For measured bolt
diameter `D`, measured bore diameters and actual centerlines through the complete
grip, a straight bolt must fit inside every bore at every depth. For ideal equal,
parallel bores this reduces to relative axis offset no greater than `H − D`.
With the modeled 11.1125 mm bore and nominal bolt, that is 1.5875 mm. A common
assembled drilling method or a functional full-grip gauge may establish fit;
two independent ±1 mm locations do not establish it by arithmetic alone. This
is a later fabrication/receiving criterion, not a request for measurements before
the diagnostic solve.

The washer can float by 0.9906 mm about a nominal bolt at the proposed maximum
11.5062 mm washer bore. Combining that with the nominal wood-bore radial
clearance gives a 1.78435 mm worst washer-to-wood-bore eccentricity. A concentric
circle enclosing that eccentric wood opening is 14.6812 mm diameter. Against
the proposed 25.2222 mm minimum washer OD, 5.2705 mm of radial seat remains.
That proves only that a nonzero seat can exist. Any washer calculation must use
the actual union of the timber opening, washer opening and eccentricity; it may
not credit a small washer ID as wood support over the larger timber bore.

## Bolt body and thread envelope

For actual grip `G`, head washer `Wh`, nut washer `Wn` and runner bearing length
`T`, measured from under the head:

- first reduced body or any transition must be at least `G + Wh − T/4`;
- first complete usable thread must be no farther than `G + Wh + Wn`;
- complete usable thread must continue through the seated nut and beyond its
  chamfer.

Using the proposed receiving extremes gives these limits:

| Item | Limit |
| --- | ---: |
| Underhead bolt length | 211.328–215.900 mm |
| First reduced section, including runout | At least **173.275 mm** |
| First complete usable thread | No farther than **186.800 mm** |
| Tip beyond two 5.0 mm washers and 8.5598 mm nut at shortest accepted bolt | **14.9682 mm** |

At nominal 3/16-inch washers, a nominal 1¼-inch thread start is 3.175 mm before
the nut-side washer face. This is not a guaranteed supplied body length. Applying
the previously recorded −0.18-inch bolt-length and 0.312-inch transition
sensitivities to a minimum 1¼-inch thread gives only 171.6532 mm of body, 1.6218
mm short of the receiving limit. Longer-than-minimum threading can reduce the
body further. Therefore the catalog description cannot produce a blanket pass;
the stated body and usable-thread locations are delivered-part rejection limits.

## Material and resistance route

The Grade 5 bolt route retains the repository's established SAE J429 basis:
92 ksi minimum tensile yield for the applicable diameter and the conditional
90 ksi NDS bending-yield route described in
[the higher-leg study](compact-higher-leg-study.md). This supports a specified
bolt-material input; it does not prove nominal-diameter bearing where thread or
runout occupies too much of either wood member. Nut identity and full usable
thread engagement remain separate direct and thread-stripping checks.

After a numerically accepted case supplies individual bolt force vectors, the
front connection still needs all of the following using the current 6×6 timber
and runner properties:

- bolt direct axial/shear and combined action;
- dowel-yield resistance using actual bearing lengths, grain directions and the
  accepted full-body or detailed threaded-bearing route;
- spacing, force-directed edge/end factors, group/action applicability,
  splitting and net-section checks;
- post and runner bearing under each washer using supported adjusted wood
  properties and actual effective seat area;
- head/nut contact, washer bending with a supported CL-8-FW material basis, and
  any prying or local seat deformation demanded by the assembled load path.

No current load demand is available for those comparisons. The missing demand
is expected output from the first case, not evidence that the case must wait for
final resistance qualification. The unsupported washer material floor remains
an independent qualification blocker even after demands are recovered. The
historical assumed 33 ksi washer yield is not transferred to CL-8-FW.

## First diagnostic solve versus qualification

Current CAD still shows an 8-inch bolt and the preceding thinner washer. That
hardware must not be described as the 8½-inch/CL-8-FW arrangement. Nevertheless,
the existing response spring has the same nominal mechanical inputs used by the
new option: 9.525 mm bolt diameter, 177.8 mm grip, 25.4 mm washer OD, 11.1125 mm
effective timber opening, and the current mixed 6×6-post/runner seat paths. Bolt
overall length and washer thickness do not enter that spring analogy. Its nominal
effective seat area is 409.7205 mm² and its assumed axial stiffness is 1061.712
N/mm, so the unmodified first run remains useful as a **member/contact/bevel
diagnostic under an explicitly provisional hardware representation**.

It is not an authenticated solve of the proposed physical stack and must not be
used to claim its fit or resistance. If the hardware is explicitly adapted later,
the record must show the 215.9 mm nominal bolt and 4.7625 mm washers. The response
must retain the wood opening as the effective centered seat opening, because it
is larger than the nominal CL-8-FW ID. Across the proposed project OD acceptance
range, the same spring analogy spans 1043.632–1140.538 N/mm; use a sensitivity if
front-joint demands are materially stiffness-sensitive.

## Later fabrication and receiving gates

These checks belong after a stable arrangement and demands exist; they are not
inputs demanded from the owner now:

1. Verify actual axes against the direct 38.1 mm spacing and applicable edge/end
   limits; do not add unbudgeted error to the nominal 0.143588 mm margin.
2. Bound bore diameter, straightness and assembled registration with the actual
   bolt diameter. Require free full-grip passage without forcing or enlarging a
   rejected bore.
3. Accept each washer only within the proposed 4.50–5.00 mm thickness,
   25.2222–26.1620 mm OD and 10.00–11.5062 mm bore envelope, with a flat,
   undamaged seat and free passage over the actual underhead fillet. These are
   project bounds, not Carr Lane manufacturing tolerances.
4. Measure actual grip and runner bearing length, then recompute the body/thread
   inequalities. Reject any bolt outside the underhead length, first-reduced-body,
   usable-thread or nut-seat limits above.
5. Establish the missing CL-8-FW material/resistance basis before treating a
   washer-bending comparison as qualified.

Stop condition: proceed to one diagnostic uncut case with the current hardware
representation clearly labeled provisional. Do not select or release this joint
until the explicit stack is modeled, actual demands are checked, registration
and seat bounds are incorporated into fabrication controls, and the washer
material/resistance blocker is resolved.
