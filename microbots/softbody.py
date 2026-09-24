"""2D spring-mass soft body with actuated springs: the physics core for the
xenobot morphology/actuation search. Semi-implicit Euler integration, gravity,
ground contact with Coulomb friction, per-voxel sinusoidal actuation."""
from __future__ import annotations
import numpy as np


class SoftBody:
    def __init__(self, width: int, height: int, spacing: float = 1.0,
                 stiffness: float = 60.0, damping: float = 2.0,
                 gravity: float = -9.8, friction_mu: float = 0.8):
        self.w, self.h = width, height
        self.spacing = spacing
        self.k = stiffness
        self.c = damping
        self.g = gravity
        self.mu = friction_mu
        xs, ys = np.meshgrid(np.arange(width) * spacing, np.arange(height) * spacing)
        self.pos = np.stack([xs.ravel(), ys.ravel() + spacing], axis=1).astype(float)
        self.vel = np.zeros_like(self.pos)
        self.mass = np.ones(width * height)
        self.springs = self._build_springs()
        self.n_cells = (width - 1) * (height - 1)

    def _build_springs(self):
        idx = lambda x, y: y * self.w + x
        springs = []
        for y in range(self.h):
            for x in range(self.w):
                for dx, dy in ((1, 0), (0, 1), (1, 1), (1, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.w and 0 <= ny < self.h:
                        i, j = idx(x, y), idx(nx, ny)
                        rest = np.linalg.norm(self.pos[i] - self.pos[j])
                        # cell ownership for actuation: lower-left cell index
                        cell = min(y, ny) * (self.w - 1) + min(x, nx) if y < self.h - 1 and x < self.w - 1 else -1
                        springs.append((i, j, rest, cell))
        return springs

    def actuation_phases(self, genome: np.ndarray) -> np.ndarray:
        """genome: (n_cells,) phases in [0, 2*pi); maps to per-spring phase."""
        return np.array([genome[s[3]] if s[3] >= 0 else 0.0 for s in self.springs])

    def simulate(self, genome: np.ndarray, duration: float, dt: float = 2e-3,
                 act_amp: float = 0.25, act_freq: float = 2.0, record: bool = False):
        """Run the soft body with actuation genome. Returns final positions and
        (if record) the trajectory."""
        phases = self.actuation_phases(genome)
        pos, vel = self.pos.copy(), self.vel.copy()
        steps = int(duration / dt)
        traj = []
        spring_arr = np.array([(i, j) for i, j, _, _ in self.springs])
        rest0 = np.array([r for _, _, r, _ in self.springs])
        for s in range(steps):
            t = s * dt
            rest = rest0 * (1.0 + act_amp * np.sin(2 * np.pi * act_freq * t + phases))
            pa, pb = pos[spring_arr[:, 0]], pos[spring_arr[:, 1]]
            d = pb - pa
            length = np.linalg.norm(d, axis=1) + 1e-12
            direction = d / length[:, None]
            f_spring = self.k * (length - rest)
            va, vb = vel[spring_arr[:, 0]], vel[spring_arr[:, 1]]
            rel_v = ((vb - va) * direction).sum(axis=1)
            f = (f_spring + self.c * rel_v)[:, None] * direction
            force = np.zeros_like(pos)
            np.add.at(force, spring_arr[:, 0], f)
            np.add.at(force, spring_arr[:, 1], -f)
            force[:, 1] += self.g * self.mass
            # ground contact: y >= 0 with normal reaction + friction
            below = pos[:, 1] < 0.0
            if below.any():
                force[below, 1] += -self.g * self.mass[below] - 50.0 * pos[below, 1]
                fx = force[below, 0]
                fn = force[below, 1]
                max_f = self.mu * np.abs(fn)
                force[below, 0] = np.clip(fx, -max_f, max_f)
            vel += (force / self.mass[:, None]) * dt
            pos += vel * dt
            vel *= 0.999  # global numerical damping
            if below.any():
                vel[below, 1] = np.maximum(vel[below, 1], 0.0)
            if record and s % 50 == 0:
                traj.append(pos.copy())
        return pos, traj

    def locomotion_fitness(self, genome: np.ndarray, duration: float = 6.0) -> float:
        """Net x-displacement of the center of mass (crawling task)."""
        x0 = self.pos[:, 0].mean()
        pos, _ = self.simulate(genome, duration)
        return float(pos[:, 0].mean() - x0)
