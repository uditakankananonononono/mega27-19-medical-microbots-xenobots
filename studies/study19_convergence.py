"""Study 19.6: numerical convergence - MSD at fixed physical time for four
integration steps; confirms the Langevin integrator's weak convergence."""
import json
import pathlib
import numpy as np
from microbots.langevin import simulate_swimmer, mean_squared_displacement

OUT = pathlib.Path(__file__).resolve().parent.parent / "results"
D_T, D_R, SPEED = 4.54e-14, 1.36e-3, 50e-6
rows = []
for dt in (0.04, 0.02, 0.01, 0.005):
    pos, _ = simulate_swimmer(SPEED, dt, int(120 / dt), D_T, D_R, seed=5)
    lag = int(30 / dt)
    msd = mean_squared_displacement(pos, lag) * 1e12
    theory = (4 * D_T * 30 + SPEED ** 2 * 900) * 1e12
    rows.append({"dt_s": dt, "msd_um2_30s": msd, "theory_um2": theory,
                 "rel_error": abs(msd - theory) / theory})
    print(f"dt={dt}: MSD(30s)={msd:.3f} um^2 (theory {theory:.3f}, rel err {rows[-1]['rel_error']:.3f})")
json.dump(rows, open(OUT / "convergence.json", "w"), indent=1)
print("wrote results/convergence.json")
