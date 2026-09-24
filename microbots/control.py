"""Closed-loop control for magnetic microbot path tracking: PID heading control
and a linear-quadratic model-predictive controller, with tracking-error stats."""
from __future__ import annotations
import math
import numpy as np

from microbots.langevin import simulate_swimmer


def pid_steer(waypoint: np.ndarray, k_p: float = 2.0):
    """Pure-pursuit PID-style steering toward a waypoint: returns steer_fn."""
    def steer(state, t):
        pos, heading = state
        delta = waypoint - pos
        if np.linalg.norm(delta) < 1e-12:
            return heading
        return math.atan2(delta[1], delta[0])
    return steer


def track_waypoints(speed: float, waypoints, dt: float, max_time: float,
                    d_t: float, d_r: float, reach_radius: float, seed: int = 0):
    """Sequentially steer through waypoints under Brownian noise.
    Returns dict with per-waypoint arrival times, positions, and miss flags."""
    rng = np.random.default_rng(seed)
    pos = np.zeros(2); heading = 0.0
    t = 0.0
    arrivals = []
    traj = [pos.copy()]
    wi = 0
    steps = int(max_time / dt)
    sdt = math.sqrt(dt)
    for k in range(steps):
        if wi >= len(waypoints):
            break
        target = np.asarray(waypoints[wi], dtype=float)
        delta = target - pos
        dist = np.linalg.norm(delta)
        if dist < reach_radius:
            arrivals.append({"waypoint": wi, "time": t, "error": dist})
            wi += 1
            continue
        desired = math.atan2(delta[1], delta[0])
        err = math.atan2(math.sin(desired - heading), math.cos(desired - heading))
        heading += np.clip(3.0 * err, -2.5, 2.5) * dt
        heading += math.sqrt(2 * d_r) * sdt * rng.standard_normal()
        pos += speed * dt * np.array([math.cos(heading), math.sin(heading)])
        pos += math.sqrt(2 * d_t) * sdt * rng.standard_normal(2)
        traj.append(pos.copy())
        t += dt
    return {"arrivals": arrivals, "trajectory": np.array(traj),
            "reached": len(arrivals), "total": len(waypoints), "elapsed": t}


def mpc_linear_tracking(A, B, Q, R, x0, x_ref, horizon: int):
    """Finite-horizon LQR/MPC for a linear system x' = A x + B u with quadratic
    cost sum x'Qx + u'Ru. Returns optimal control sequence via Riccati recursion."""
    n = A.shape[0]
    P = Q.copy()
    gains = []
    for _ in range(horizon):
        K = np.linalg.solve(R + B.T @ P @ B, B.T @ P @ A)
        P = Q + A.T @ P @ (A - B @ K)
        gains.append(K)
    us, x = [], np.asarray(x0, dtype=float)
    for K in reversed(gains):
        u = -K @ (x - np.asarray(x_ref, dtype=float))
        us.append(u)
        x = A @ x + B @ u
    return np.array(us)
