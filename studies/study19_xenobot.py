"""Study 19.3: xenobot actuation evolution. Evolve per-voxel actuation phases
for the soft-body crawler; report the fitness curve and best-genome behavior."""
import json
import pathlib

import numpy as np

from microbots.softbody import SoftBody
from microbots.evolve import evolve_actuation

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "results"; OUT.mkdir(exist_ok=True)

body = SoftBody(6, 4)
best_g, best_f, history = evolve_actuation(body, generations=14, pop_size=16,
                                           duration=4.0, seed=7)
base_f = body.locomotion_fitness(np.zeros(body.n_cells), 4.0)
print(f"evolved fitness (COM x-displacement): {best_f:.3f} body-lengths-ish units")
print(f"unactuated baseline: {base_f:.3f}")
print(f"improvement: {best_f - base_f:.3f}")
json.dump({"best_fitness": best_f, "baseline_fitness": base_f,
           "best_genome_phases": best_g.tolist(), "history": history},
          open(OUT / "xenobot_evolution.json", "w"), indent=1)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
gens = [h["generation"] for h in history]
plt.figure(figsize=(6, 4))
plt.plot(gens, [h["best"] for h in history], label="best")
plt.plot(gens, [h["mean"] for h in history], label="population mean")
plt.axhline(base_f, ls="--", c="gray", label="unactuated baseline")
plt.xlabel("generation"); plt.ylabel("locomotion fitness (x displacement)")
plt.title("Xenobot actuation evolution (spring-mass soft body)")
plt.legend(); plt.tight_layout(); plt.savefig(OUT / "xenobot_fitness.png", dpi=150)

# visualize best-genome crawl
pos, traj = body.simulate(best_g, duration=4.0, record=True)
plt.figure(figsize=(7, 3))
for i, frame in enumerate(traj[::4]):
    plt.scatter(frame[:, 0], frame[:, 1], s=8, alpha=0.3 + 0.7 * i / max(len(traj[::4]) - 1, 1),
                c=range(len(frame)), cmap="viridis")
plt.title("Evolved xenobot gait (light -> dark in time)")
plt.xlabel("x"); plt.ylabel("y"); plt.tight_layout()
plt.savefig(OUT / "xenobot_gait.png", dpi=150)
print("wrote results/xenobot_evolution.json + figures")
