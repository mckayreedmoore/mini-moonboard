"""Stable original-potential increments for the frozen numerical continuation.

Only Armijo/model-reduction energy arithmetic changes. Published energy,
physical gradient, tangent, contact forces and final tolerance still come from
the frozen potential. An optional saved iterate is initialization only.
"""

from __future__ import annotations

import math
from pathlib import Path
from unittest.mock import patch

import numpy as np

from scripts import thin_bolted_frame_mechanics as frame
from scripts import thin_bolted_numerical_step as previous

PREVIOUS_SHA = "82b7d5a8d9d9dc871ee6410fb4c5854093a998cfd9b331fdd986917b63ebbc28"
LOADED_PRODUCER_SHA256 = frame.sha(Path(__file__))
ORIGINAL_FIELDS = previous.physical_fields
ORIGINAL_NUMERICAL_SOLVE = previous.numerical_solve


def positive_quadratic_remainder(value, change, stiffness):
    """E(x+dx)-E(x)-E'(x)dx for .5k max(x,0)^2, without cancellation."""
    new = value + change
    if value > 0. and new > 0.:
        return .5 * stiffness * change**2
    if value <= 0.:
        return .5 * stiffness * max(new, 0.)**2
    return -.5 * stiffness * value**2 - stiffness * value * change


def radial_remainder(lateral, change, stiffness, gap):
    """Exact circular-gap Bregman remainder, stable for small directional steps."""
    radius = float(np.linalg.norm(lateral))
    new_radius = float(np.linalg.norm(lateral + change))
    old_extension, new_extension = max(radius - gap, 0.), max(new_radius - gap, 0.)
    if old_extension == 0.:
        return .5 * stiffness * new_extension**2
    projection = float(lateral @ change) / radius
    if new_extension == 0.:
        return -.5 * stiffness * old_extension**2 - stiffness * old_extension * projection
    perpendicular = change - lateral * (projection / radius)
    transverse_squared = float(perpendicular @ perpendicular)
    denominator = new_radius + radius + projection
    norm_remainder = (transverse_squared / denominator if denominator > 1e-12 * radius
                      else new_radius - radius - projection)
    return .5 * stiffness * float(change @ change) - stiffness * gap * norm_remainder


def physical_energy_increment(K, applied, groups, C, ck, state, delta, *, gradient=None):
    """Exact unchanged potential difference, assembled from stable local terms.

    This is gradient·delta plus convex Taylor remainders. It equals direct
    factorized spring/contact energy changes and delta·(Kq-F)+.5delta·Kdelta,
    but avoids cancellation of the much larger opposing first-order terms.
    """
    if gradient is None:
        gradient = ORIGINAL_FIELDS(K, applied, groups, C, ck, state)[0]
    terms = [float(gradient @ delta), .5 * float(delta @ (K @ delta))]
    for group in groups:
        value, change = np.asarray(group["B"] @ state).ravel(), np.asarray(group["B"] @ delta).ravel()
        if group["tension_only"]:
            terms.append(positive_quadratic_remainder(value[0], change[0], group["ka"]))
        else:
            terms.append(.5 * group["ka"] * change[0]**2)
        terms.append(radial_remainder(value[1:], change[1:], group["kl"], group["clearance"]))
    values, changes = np.asarray(C @ state).ravel(), np.asarray(C @ delta).ravel()
    terms.extend(positive_quadratic_remainder(value, change, stiffness)
                 for value, change, stiffness in zip(values, changes, ck, strict=True))
    return math.fsum(terms)


class EnergyThreshold:
    """A comparison datum carrying an original potential plus an offset."""

    def __init__(self, energy, offset):
        self.energy, self.offset = energy, offset

    def __add__(self, offset):
        return EnergyThreshold(self.energy, self.offset + offset)

    __radd__ = __add__


class IncrementalEnergy(float):
    """Serialize as original scalar energy; compare by its stable difference."""

    def __new__(cls, energy, K, applied, groups, C, ck, state, gradient):
        obj = super().__new__(cls, energy)
        obj.data = (K, applied, groups, C, ck, state.copy(), gradient.copy())
        return obj

    def difference_to(self, other):
        K, applied, groups, C, ck, state, gradient = self.data
        if K is not other.data[0] or applied is not other.data[1]:
            raise ValueError("potential comparison crosses a different physical floor pattern or load")
        return physical_energy_increment(K, applied, groups, C, ck, state, other.data[5] - state, gradient=gradient)

    def __sub__(self, other):
        return -self.difference_to(other) if isinstance(other, IncrementalEnergy) else float(self) - other

    def __add__(self, offset):
        return EnergyThreshold(self, offset)

    __radd__ = __add__

    def __le__(self, other):
        if isinstance(other, EnergyThreshold):
            return other.energy.difference_to(self) <= other.offset
        return float(self) <= other


def stable_fields(K, applied, groups, C, ck, state, *, tangent=False):
    fields = ORIGINAL_FIELDS(K, applied, groups, C, ck, state, tangent=tangent)
    gradient, energy, *rest = fields
    return gradient, IncrementalEnergy(energy, K, applied, groups, C, ck, state, gradient), *rest


def compatible_contact_solve(K, applied, groups, contacts, tangents, max_iterations=500, *, warm_q=None):
    """Reuse frozen continuation; optional q is a source-bound initialization only."""
    source_pins()
    if warm_q is not None:
        warm_q = np.array(warm_q, dtype=float)
        if warm_q.shape != (K.shape[0],) or not np.isfinite(warm_q).all():
            raise ValueError("finite warm iterate with unchanged degrees of freedom required")
    initialization_calls = 0

    def initial_or_step(A, b):
        nonlocal initialization_calls
        initialization_calls += 1
        if warm_q is not None and initialization_calls <= 2:
            return warm_q.copy()
        return ORIGINAL_NUMERICAL_SOLVE(A, b)

    with (patch.object(previous, "physical_fields", stable_fields),
          patch.object(previous, "numerical_solve", initial_or_step)):
        result = previous.compatible_contact_solve(K, applied, groups, contacts, tangents, max_iterations=max_iterations)

    def plain_energy(value):
        if isinstance(value, IncrementalEnergy):
            return float(value)
        if isinstance(value, dict):
            return {key: plain_energy(item) for key, item in value.items()}
        if isinstance(value, list):
            return [plain_energy(item) for item in value]
        return value

    result = plain_energy(result)
    result["numerical_step_strategy"] = "adaptive-scaled-Levenberg-stable-original-potential-increments"
    result["warm_iterate_used_only_as_initialization"] = warm_q is not None
    result["original_force_tolerance_or_physical_laws_changed"] = False
    source_pins()
    return result


def source_pins():
    pins = {"scripts/thin_bolted_incremental_step.py": LOADED_PRODUCER_SHA256,
            "scripts/thin_bolted_numerical_step.py": PREVIOUS_SHA,
            "scripts/thin_bolted_frame_mechanics.py": previous.FRAME_SHA}
    if any(frame.sha(frame.ROOT / path) != digest for path, digest in pins.items()):
        raise ValueError("incremental numerical strategy source differs")
    return pins
