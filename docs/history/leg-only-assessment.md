# Single 2×6 support-leg assessment

> **Superseded by the completed assessment:** see
> [the current decision](leg-completion-decision.md). It adds explicit foot-pressure
> variation and corresponding joint moments. The member passes the selected
> full-contact cases; both the existing and investigated smooth-bolt connection
> fail their lateral criterion. This page preserves the earlier axial comparisons.

The owner narrowed the assessment on September 12, 2026 to the rear support
legs. Panel construction is accepted as the owner-specified design basis.
No comparison frame or floor-friction qualification is required. Feet are
assumed not to slide.

The single 2×6 **member passes the stated 250 lb doubled-load comparison**.
This is a conditional lumber result; the four-bolt attachment and its imposed
moments have not been established by this calculation. It is not an installed
assembly rating or a prediction of breaking weight.

## Calculation and results

The calculation uses current geometry and modeled assembly mass (181.21 kg),
scans all 142 hold positions, and balances moments about the front support.
It includes a 300 N rearward horizontal force and up to 100 mm hold projection.
The entire combined rear-support compression is assigned to one leg, without
credit for equal sharing between legs. An additional 25 kg (55.1 lb) allowance
covers holds and electrical equipment,
placed entirely at the rear-most hold projection, Y = 1,549.55 mm. This is an
explicit design allowance, not a measured kit weight. Installed equipment must
remain within that mass and rearward extent; modeled mass plus allowance is
206.21 kg.

| Climber and vertical load | Compression assigned to one leg | Member interaction, supported span | Member interaction, full stock length |
| --- | ---: | ---: | ---: |
| 250 lb, body weight | 2.820 kN | 0.431 | 0.532 |
| 250 lb, twice body weight | 4.072 kN | 0.802 | 1.079 |
| 300 lb, twice body weight | 4.572 kN | 1.002 | 1.415 |

An interaction at or below 1 meets the modeled design criterion. The actual
foot-to-bolt-group span is 1,612 mm. Using the entire 1,808 mm stock length as
the effective span is an additional conservative sensitivity, not the actual
distance between supports. With the equipment allowance, the longer-span
sensitivity exceeds its criterion
at 250 lb while the actual-span result remains below 1. At 300 lb doubled load,
the actual-span criterion is also just exceeded. These are allowable-design
comparisons under specified loads, not predictions of physical failure.

The member calculation assumes dry, unincised, grade-stamped US Douglas
Fir–Larch No. 2, actual section 38.1 × 139.7 mm, normal load duration, and
pin-ended restraint with no intermediate bracing credit. It checks compression,
buckling and biaxial bending using NDS 2024. It conservatively carries the
weakest staggered bolt-hole net section through the member, includes a
19.05 mm load eccentricity, the net-section centroid shift, and self-weight
bending. It does not assume additional frame-imposed joint couples or
transverse point loads.

Reference design values and equations come from the same edition of the
[AWC NDS and Supplement](https://awc.org/resources/2024-nds-supplement/).
The primary chapter sources are recorded in
[the timber resistance notes](reinforced-timber-resistance.md).

## Four-bolt attachment result

The existing hole pattern passes the checked end, edge and row-spacing limits.
A conventional rigid-group calculation gives the following conditional lateral
bolt results for the 4.072 kN combined rear compression:

| Share carried by one leg | Peak bolt demand/reference, zero imposed moment | Additional sagittal joint-moment interval |
| --- | ---: | ---: |
| 50% | 0.616 | −58.7 to +58.7 N·m |
| 75% | 0.924 | −15.9 to +15.9 N·m |
| 100% | 1.232 | No passing interval |

The pure-axial group reference is 3.305 kN. Under these assumptions, one joint
can carry at most 81.2% of the calculated combined rear compression before the
lateral criterion is reached, with no additional sagittal joint moment.
These shares are sensitivity cases, not a finding that the frame shares load
50/50 or stays within the displayed moment interval. The intervals check bolt
lateral yield and parallel-grain local stresses only, not the combined member
response to additional joint moments.

The calculation uses a conservative 0.298-inch bolt root diameter throughout,
a 45 ksi bending-yield requirement, dry-service factors and normal load
duration. The current A307 bolt identification does not establish that bending
property. The requirement is **documented bending yield of at least 45 ksi**;
a supported SAE J429 Grade 1 specification is one route identified in the
[existing primary-source notes](reinforced-timber-resistance.md). No hardware
substitution has been made or represented as already installed.

**Conclusion:** the 2×6 member passes the specified actual-span case, but the
existing leg attachment has not demonstrated adequacy. It does not pass the
all-rear-load-on-one-leg comparison even before extra joint bending. That
comparison does not establish actual failure or prove larger lumber necessary.

Closing the attachment result requires establishing its actual load share and
joint moments, including single-lap prying/washer action and perpendicular-grain
splitting in the receiving rim, or providing a connection detail whose stated
resistance covers those actions. The calculation cannot certify these effects
from bolt count or passing edge distances alone. These are aspects of the same
leg connection, not additional panel or floor-friction work.

The equipment-weight omission is resolved by the explicit allowance. Lumber
remains a receiving specification: dry, unincised US Douglas Fir–Larch No. 2
or better for both legs and the assumed receiving wood. No photograph or
receiving record confirms the actual stock grade here; different species or
unspecified lumber do not inherit the result.

## Reproduction

The [load calculation](../fea/leg_only_load_check.py) uses geometry from the
archived model, not its spring-model forces. It calls the
[member calculation](../fea/leg_member_capacity.py); the
[result file](../fea/results/leg-only-load-check-v2.json) records input hashes,
individual cases and limitations.

```sh
uv run python -m fea.leg_only_load_check --output /tmp/leg-only-check.json
uv run pytest -q tests/test_leg_member_capacity.py tests/test_leg_only_load_check.py
```

Focused tests cover the member, load balance and attachment-force recovery. The load balance and member comparison also received
an independent calculation review. These checks verify the implementation;
they do not independently establish installed joint behavior.

The [attachment calculation](../fea/leg_attachment_check.py) and
[attachment results](../fea/results/leg-attachment-check-v1.json) preserve
individual bolt forces, geometry checks and the conditional moment intervals.
The v1 load result is historical evidence without the equipment allowance;
v2 is the current comparison.
