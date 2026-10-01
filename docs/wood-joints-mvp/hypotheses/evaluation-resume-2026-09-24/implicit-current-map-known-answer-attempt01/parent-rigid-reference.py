#!/usr/bin/env python3
"""High-precision constrained-rigid Newmark reference, not an elastic FE solve."""
from decimal import Decimal as D, localcontext
from pathlib import Path
import argparse
import hashlib
import json

HERE = Path(__file__).resolve().parent
ZERO = [[D(0) for j in range(3)] for i in range(3)]
IDENTITY = [[D(i == j) for j in range(3)] for i in range(3)]
W = [[D(0),D(0),D(1)], [D(0),D(0),D(0)], [D(-1),D(0),D(0)]]


def add(a, b):
    return [[a[i][j]+b[i][j] for j in range(3)] for i in range(3)]


def scale(a, factor):
    return [[factor*v for v in row] for row in a]


def transpose(a):
    return [list(row) for row in zip(*a)]


def multiply(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def determinant(a):
    return (a[0][0]*(a[1][1]*a[2][2]-a[1][2]*a[2][1])
            - a[0][1]*(a[1][0]*a[2][2]-a[1][2]*a[2][0])
            + a[0][2]*(a[1][0]*a[2][1]-a[1][1]*a[2][0]))


def inverse(a):
    det = determinant(a)
    assert det != 0
    cofactor = []
    for i in range(3):
        row = []
        for j in range(3):
            x = [[a[r][c] for c in range(3) if c != j] for r in range(3) if r != i]
            row.append(D((-1)**(i+j))*(x[0][0]*x[1][1]-x[0][1]*x[1][0])/det)
        cofactor.append(row)
    return transpose(cofactor)


def maximum(a):
    return max(abs(v) for row in a for v in row)


def polar(a):
    assert determinant(a) > 0
    x = scale(a, 1/maximum(a))
    for count in range(100):
        following = scale(add(x, transpose(inverse(x))), D('.5'))
        difference = maximum(add(following, scale(x, -1)))
        x = following
        if difference < D('1e-65'):
            break
    else:
        raise RuntimeError("Polar iteration did not converge")
    assert maximum(add(multiply(transpose(x), x), scale(IDENTITY, -1))) < D('1e-60')
    assert abs(determinant(x)-1) < D('1e-60')
    return x


def floats(a):
    return [[float(v) for v in row] for row in a]


def calculate():
    known_rotation = [[D('.6'),D(0),D('.8')], [D(0),D(1),D(0)], [D('-.8'),D(0),D('.6')]]
    known_spd = [[D(2),D('.1'),D(0)], [D('.1'),D(3),D('.2')], [D(0),D('.2'),D(5)]]
    assert maximum(add(polar(multiply(known_rotation, known_spd)), scale(known_rotation, -1))) < D('1e-60')
    assert maximum(add(multiply(known_spd, inverse(known_spd)), scale(IDENTITY, -1))) < D('1e-60')
    p = HERE / "parent-mass-reference.json"
    mass_data = json.loads(p.read_text(), parse_float=D)
    mass = mass_data["mass_tonne"]
    r = [c-p for c,p in zip(mass_data["centroid_mm"], mass_data["pivot_from_native_control_coordinate_mm"])]
    rr = sum(v*v for v in r)
    ip = mass_data["inertia_about_pivot_tonne_mm2"]
    ic = [[ip[i][j]-mass*(D(i == j)*rr-r[i]*r[j]) for j in range(3)] for i in range(3)]
    tr = sum(ic[i][i] for i in range(3))
    covariance = [[D(i == j)*tr/2-ic[i][j] for j in range(3)] for i in range(3)]
    asym = maximum(add(covariance, scale(transpose(covariance), -1)))
    assert asym < D('1e-17')
    covariance = scale(add(covariance, transpose(covariance)), D('.5'))
    assert covariance[0][0] > 0
    assert covariance[0][0]*covariance[1][1]-covariance[0][1]*covariance[1][0] > 0
    assert determinant(covariance) > 0
    rotation, velocity, acceleration = IDENTITY, ZERO, ZERO
    dt, c = D('.001'), D('1.2')
    states = []
    for inc in range(1, 11):
        t = inc*dt
        predictor = add(add(rotation, scale(velocity, dt)), scale(acceleration, dt*dt/4))
        target = add(predictor, scale(W, dt*dt*c*t/4))
        new_rotation = polar(multiply(target, covariance))
        new_acceleration = scale(add(new_rotation, scale(predictor, -1)), 4/(dt*dt))
        new_velocity = add(velocity, scale(add(acceleration, new_acceleration), dt/2))
        stationarity = multiply(transpose(new_rotation), multiply(target, covariance))
        assert maximum(add(stationarity, scale(transpose(stationarity), -1))) < D('1e-60')
        theta, omega = c*(t**3/6+t*dt*dt/12), c*t*t/2
        center_direction = [r[2], D(0), -r[0]]
        center_u, center_v = [[s*v for v in center_direction] for s in (theta, omega)]
        kinetic_tensor = multiply(multiply(new_velocity, covariance), transpose(new_velocity))
        kinetic = mass*sum(v*v for v in center_v)/2+sum(kinetic_tensor[i][i] for i in range(3))/2
        states.append({"increment": inc, "time_s": float(t),
            "rotation_matrix": floats(new_rotation),
            "rotation_matrix_minus_identity": floats(add(new_rotation, scale(IDENTITY, -1))),
            "velocity_coefficient_matrix_per_s": floats(new_velocity),
            "acceleration_coefficient_matrix_per_s2": floats(new_acceleration),
            "centroid_displacement_mm": [float(v) for v in center_u],
            "centroid_velocity_mm_s": [float(v) for v in center_v],
            "rigid_discrete_kinetic_energy_Nmm": float(kinetic),
            "linearized_theta_rad": float(theta), "linearized_omega_rad_s": float(omega),
            "maximum_rotation_coefficient_difference_from_linear": float(maximum(add(add(new_rotation, scale(IDENTITY, -1)), scale(W, -theta)))),
            "maximum_velocity_coefficient_difference_from_linear_per_s": float(maximum(add(new_velocity, scale(W, -omega))))})
        rotation, velocity, acceleration = new_rotation, new_velocity, new_acceleration
    return {"schema": "parent_constrained_rigid_newmark_reference/v1",
        "status": "OFFLINE_RIGID_LIMIT_REFERENCE_PENDING_INDEPENDENT_REVIEW",
        "mass_reference_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        "decimal_digits": 80, "mass_covariance_about_centroid": floats(covariance),
        "covariance_symmetry_correction_max": float(asym/2), "states": states,
        "method": "For fixed consistent M and f=M*c*t*W*r0, proper polar of Y*S minimizes the Newmark inertial/external potential over rigid positions. Update affine velocity/acceleration by Newmark, not continuous angular-velocity formulas.",
        "limits": "Constrained rigid-body discrete reference only. Actual native body is elastic. Covariance inputs were integrated in binary64; 80-digit polar arithmetic does not increase their accuracy. Elastic discrepancy, native damping/initialization applicability and acceptance limits need independent review.",
        "native_execution": False, "joint_acceptance": False, "release": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    with localcontext() as context:
        context.prec = 80
        data = calculate()
    rendered = json.dumps(data, indent=2, sort_keys=True) + "\n"
    path = HERE / "parent-rigid-reference.json"
    if args.write:
        with path.open("x") as stream:
            stream.write(rendered)
    else:
        assert path.read_text() == rendered
    print(json.dumps({"status": data["status"], "terminal": data["states"][-1]}))
