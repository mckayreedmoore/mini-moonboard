# Parent disposition of the washer-facing source inputs

Checked October 1, 2026. Parent took over the full-clause inspection after
the worker's source trace produced no saved draft within its initial time
box. The worker subsequently saved [source-review.md](source-review.md),
SHA-256 `1a7a236ddf92f5fb1487619ebe8493de5f6ddfa97e924bc48cf5ebb5fe83f975`.
This disposition supplies inputs for an explicitly conditional contact
model, not a contact-pressure field or hardware qualification.

## What was inspected

Parent directly read §4.3 and Table 6 in the hash-pinned local B18.2.1-2012 PDF mirror
already identified by the worker (`4c7bcb75223b7e89fc27f132bc44e8b422ba672c97f7803259a24fab6bd99ba0`).
The head's 10.0127–11.1252 mm gauge-circle diameter is measured 0.1016 mm
toward the head from the bearing plane. That offset prevents treating it as
an actual contact-plane diameter without a stated transition profile. The
standard also permits bearing-face runout; across-flats and across-corners
are not circular contact boundaries. No head footprint is adopted here.

The worker had only indexed B18.2.2 text. Parent recovered the readable
[full-text transcription of the original B18.2.2-2022 standard](https://studylib.net/doc/27188368/asme-b18.2.2-2022),
hosted by a third party, and inspected §§3.3–3.4, 3.8–3.9 and Table 1.1.1-5.
Its numeric text agrees with the worker's nut-circle and countersink inputs.
This is a transcription check, **not an authenticated PDF or figure review**.
The [ASME publisher record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-2-nuts-general-applications-machine-screw-nuts-hex-square-hex-flange-coupling-nuts)
confirms the edition. No raw standard is published in this packet.

## Added alignment bounds and modeling consequence

The nut's true-position zone is diametrical, not radial: for this size its
4%-of-maximum-across-flats value is 0.445008 mm diameter, hence 0.222504 mm
maximum axis offset under the stated circular-zone interpretation. The
quarter-inch regular-hex row permits FIM 0.015 in (0.381 mm) below 150 ksi
specified nut proof stress; the conditional J995 Grade 5 case in the hardware
packet is in that band. FIM is an indicator reading, not an extra washer
thickness or an automatically prescribed assembled tilt.

Therefore the worker's 24.56–49.45 mm² nut/washer annulus can be used only as
a declared concentric, flat-face scenario. It cannot be used as a guaranteed
contact area or as a uniform-pressure boundary. A contact model must also
state the nut/body-to-thread eccentricity, washer play, face profile/runout,
coating and seating assumptions, and retain eccentric/partial overlap where
those assumptions allow it. The source does not prescribe which permitted
orientation or contact distribution actually occurs.

For the head, supply a declared bearing-plane/transition-profile scenario
consistent with the inspected gauge plane, or bind an exact product drawing.
A source drawing or receiving observation is not a blanket prerequisite to
calculating an explicit hypothetical profile. Its applicability and any
claim that it bounds catalog hardware remain separate questions.

## Next usable calculation

The contact-method implementation can now distinguish three input surfaces:
the head's declared bearing face, the nut's declared chamfered face, and the
washer's catalog/CAD annulus intersected with its finished timber receiver.
They are not interchangeable pressure areas. Bind signed axial/lateral/moment
actions and any prying to that model; validate the solid/contact method and
physical stress-recovery detail before reporting a required washer yield.
The current clamped-annulus deflection helper remains outside this boundary.

This resolves the available dimensional source trace. It leaves the actual
head contact-plane profile, bounded assembled contact, washer metal property,
complete action envelope and complete-joint resistance open. No model axis,
panel/screw policy, source response or selected candidate was changed.
