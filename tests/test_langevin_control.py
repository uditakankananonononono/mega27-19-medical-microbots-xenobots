import math
import numpy as np
from microbots.langevin import (stokes_einstein_translational,
                                stokes_einstein_rotational,
                                simulate_swimmer, mean_squared_displacement)
from microbots.control import track_waypoints, mpc_linear_tracking


def test_stokes_einstein_scaling():
    d1 = stokes_einstein_translational(1e-6, 1e-3, 300.0)
    d2 = stokes_einstein_translational(2e-6, 1e-3, 300.0)
    assert abs(d1 / d2 - 2.0) < 1e-12
    assert d1 > 0


def test_free_diffusion_msd_matches_theory():
    # zero propulsion: MSD(2D) = 4 D t
    d_t = 2e-13
    dt = 0.01
    pos, _ = simulate_swimmer(0.0, dt, 4000, d_t, 0.0, seed=1)
    lag = 1000
    msd = mean_squared_displacement(pos, lag)
    theory = 4 * d_t * lag * dt
    assert 0.5 * theory < msd < 2.0 * theory


def test_waypoint_tracking_beats_noise():
    # strong propulsion, small noise: all waypoints reached
    res = track_waypoints(1e-4, [(1e-3, 0.0), (1e-3, 1e-3)], 0.01, 60.0,
                          1e-14, 1e-4, 1e-4, seed=2)
    assert res["reached"] == 2
    assert all(a["time"] < 60.0 for a in res["arrivals"])


def test_mpc_double_integrator_converges():
    # position/velocity double integrator, unit mass
    A = np.array([[1.0, 1.0], [0.0, 1.0]])
    B = np.array([[0.0], [1.0]])
    Q = np.eye(2); R = np.array([[0.1]])
    us = mpc_linear_tracking(A, B, Q, R, x0=[5.0, 0.0], x_ref=[0.0, 0.0], horizon=30)
    x = np.array([5.0, 0.0])
    for u in us:
        x = A @ x + B.ravel() * u[0] if hasattr(u, '__len__') else A @ x + B.ravel() * u
    assert abs(x[0]) < 5.0  # controller drove position toward the reference
