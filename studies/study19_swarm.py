"""Study 19.2: controlled vs uncontrolled microbot navigation under Brownian
noise. Monte Carlo waypoint-tracking success for a 10 um robot in water at
body-relevant conditions, with real Stokes-Einstein noise."""
import json
import pathlib

import numpy as np

from microbots.langevin import (stokes_einstein_translational,
                                stokes_einstein_rotational, simulate_swimmer)
from microbots.control import track_waypoints

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "results"; OUT.mkdir(exist_ok=True)

RADIUS = 5e-6
ETA, TEMP = 1e-3, 310.0          # water, body temperature
D_T = stokes_einstein_translational(RADIUS, ETA, TEMP)
D_R = stokes_einstein_rotational(RADIUS, ETA, TEMP)
SPEED = 50e-6                    # 50 um/s from the optimized helix
WAYPOINTS = [(1e-3, 0.0), (1e-3, 1e-3), (0.0, 1e-3)]
DT, MAX_T, REACH = 0.02, 120.0, 50e-6

N = 200
controlled = [track_waypoints(SPEED, WAYPOINTS, DT, MAX_T, D_T, D_R, REACH, seed=s)
              for s in range(N)]
success = [r["reached"] == r["total"] for r in controlled]
times = [[a["time"] for a in r["arrivals"]] for r in controlled if r["reached"] == r["total"]]
flat_times = [t for ts in times for t in ts]

# uncontrolled baseline: straight-line propulsion + diffusion, distance from target
uncontrolled_reach = 0
for s in range(N):
    pos, _ = simulate_swimmer(SPEED, DT, int(MAX_T / DT), D_T, D_R, seed=1000 + s)
    d = np.linalg.norm(pos - np.array(WAYPOINTS[-1]), axis=1)
    if (d < REACH).any():
        uncontrolled_reach += 1

summary = {
    "robot_radius_um": RADIUS * 1e6, "speed_um_s": SPEED * 1e6,
    "D_t_m2_s": D_T, "D_r_rad2_s": D_R, "temperature_K": TEMP,
    "controlled_success_rate": float(np.mean(success)),
    "controlled_success_ci95": float(1.96 * np.std(success) / np.sqrt(N)),
    "mean_leg_time_s": float(np.mean(flat_times)),
    "uncontrolled_reach_rate": uncontrolled_reach / N,
    "n_runs": N,
}
print(json.dumps(summary, indent=1))
json.dump(summary, open(OUT / "swarm_control.json", "w"), indent=1)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.figure(figsize=(6, 6))
for r in controlled[:40]:
    tr = r["trajectory"] * 1e3
    plt.plot(tr[:, 0], tr[:, 1], lw=0.4, alpha=0.5)
wps = np.array(WAYPOINTS) * 1e3
plt.scatter(wps[:, 0], wps[:, 1], c="red", marker="*", s=120, label="waypoints", zorder=5)
plt.xlabel("x (mm)"); plt.ylabel("y (mm)")
plt.title(f"Microbot waypoint tracking under Brownian noise "
          f"(success {np.mean(success):.0%}, n={N})")
plt.legend(); plt.tight_layout(); plt.savefig(OUT / "swarm_trajectories.png", dpi=150)
print("wrote results/swarm_control.json + swarm_trajectories.png")
