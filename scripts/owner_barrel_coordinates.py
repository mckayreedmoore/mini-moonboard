"""Inclined-member coordinates for the detached barrel-nut layouts."""

import math

ANGLE = math.radians(50)
T = (math.cos(ANGLE), math.sin(ANGLE))
N = (-math.sin(ANGLE), math.cos(ANGLE))


def xyz(x, t, n):
    return (x, t * T[0] + n * N[0], t * T[1] + n * N[1])


def local_bounds(shape):
    vertices = shape.Vertices()
    return {
        "x": (min(v.X for v in vertices), max(v.X for v in vertices)),
        "t": (
            min(v.Y * T[0] + v.Z * T[1] for v in vertices),
            max(v.Y * T[0] + v.Z * T[1] for v in vertices),
        ),
        "n": (
            min(v.Y * N[0] + v.Z * N[1] for v in vertices),
            max(v.Y * N[0] + v.Z * N[1] for v in vertices),
        ),
    }
