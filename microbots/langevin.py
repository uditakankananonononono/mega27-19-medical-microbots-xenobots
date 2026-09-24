"""Langevin dynamics for a microswimmer with Brownian noise (2D).
Euler-Maruyama integration with Stokes-Einstein translational and rotational
diffusion - the real noise model for micron-scale robots in fluid."""
from __future__ import annotations
import math
import numpy as np

KB = 1.380649e-23  # Boltzmann constant J/K


def stokes_einstein_translational(radius: float, eta: float, temperature: float) -> float:
    """Translational diffusion coefficient D_t = k_B T / (6 pi eta r)."""
    return KB * temperature / (6 * math.pi * eta * radius)


def stokes_einstein_rotational(radius: float, eta: float, temperature: float) -> float:
    """Rotational diffusion coefficient D_r = k_B T / (8 pi eta r^3)."""
    return KB * temperature / (8 * math.pi * eta * radius ** 3)


def simulate_swimmer(speed: float, dt: float, steps: int, d_t: float, d_r: float,
                     steer_fn=None, seed: int = 0, start=(0.0, 0.0, 0.0)):
    """Propelled Brownian particle at constant `speed`; heading diffuses with
    D_r, position with D_t. steer_fn(state, t) -> target heading (rad) or None.
    Returns (positions (steps+1,2), headings (steps+1,))."""
    rng = np.random.default_rng(seed)
    pos = np.array([start[0], start[1]], dtype=float)
    heading = float(start[2])
    positions = np.zeros((steps + 1, 2)); positions[0] = pos
    headings = np.zeros(steps + 1); headings[0] = heading
    sdt = math.sqrt(dt)
    for k in range(steps):
        if steer_fn is not None:
            target = steer_fn((pos.copy(), heading), k * dt)
            err = math.atan2(math.sin(target - heading), math.cos(target - heading))
            heading += 2.0 * err * dt  # bounded turning rate
        heading += math.sqrt(2 * d_r) * sdt * rng.standard_normal()
        pos += speed * dt * np.array([math.cos(heading), math.sin(heading)])
        pos += math.sqrt(2 * d_t) * sdt * rng.standard_normal(2)
        positions[k + 1] = pos
        headings[k + 1] = heading
    return positions, headings


def mean_squared_displacement(positions: np.ndarray, lag: int) -> float:
    """MSD at a given frame lag."""
    d = positions[lag:] - positions[:-lag]
    return float((d ** 2).sum(axis=1).mean())
