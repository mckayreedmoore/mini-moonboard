"""TR12 Table 1-1 single-shear equations; supplied inputs are not qualified here."""
import math


def single_shear(*, main_length_in, side_length_in, main_bearing_lb_in,
                 side_bearing_lb_in, main_yield_moment_lb_in,
                 side_yield_moment_lb_in, gap_in, reduction_terms):
    """Return six P/Rd reference values in lbf, before end-use adjustments.

    Bearing intensities q and dowel yield moments M are explicit inputs so the
    caller must resolve diameter/thread exposure rather than silently receiving
    a smooth-shank assumption. Only two solid-cross-section members, one shear
    plane; no group, splitting, axial, friction or connection approval.
    """
    lm, ls = main_length_in, side_length_in
    qm, qs = main_bearing_lb_in, side_bearing_lb_in
    mm, ms = main_yield_moment_lb_in, side_yield_moment_lb_in
    modes = ("Im", "Is", "II", "IIIm", "IIIs", "IV")
    if (not all(math.isfinite(v) and v > 0 for v in (lm, ls, qm, qs, mm, ms))
            or not math.isfinite(gap_in) or gap_in < 0
            or set(reduction_terms) != set(modes)
            or not all(math.isfinite(v) and v > 0 for v in reduction_terms.values())):
        raise ValueError("Require positive finite lengths, q, M and six reduction terms; gap >=0")
    coefficients = {
        "II": (1/(4*qs)+1/(4*qm), ls/2+gap_in+lm/2, -qs*ls**2/4-qm*lm**2/4),
        "IIIm": (1/(2*qs)+1/(4*qm), gap_in+lm/2, -ms-qm*lm**2/4),
        "IIIs": (1/(4*qs)+1/(2*qm), ls/2+gap_in, -qs*ls**2/4-mm),
        "IV": (1/(2*qs)+1/(2*qm), gap_in, -ms-mm),
    }
    yields = {"Im": qm*lm, "Is": qs*ls}
    for mode, (a, b, c) in coefficients.items():
        # Equivalent positive quadratic root avoids cancellation for large gaps.
        yields[mode] = -2*c/(b+math.sqrt(b*b-4*a*c))
    reference = {mode: yields[mode]/reduction_terms[mode] for mode in modes}
    if not all(math.isfinite(v) and v > 0 for v in reference.values()):
        raise ValueError("Nonfinite or nonpositive calculated reference value")
    governing = min(reference, key=reference.get)
    return {"yield_values_lbf": yields, "reference_values_lbf": reference,
            "governing_mode": governing, "reference_lateral_lbf": reference[governing],
            "limits": "Supplied-input single-fastener lateral yield only; not adjusted "
            "joint resistance, multi-member/group analysis or approval"}
