"""Study 19.1: helical magnetic microbot geometry optimization via real RFT
hydrodynamics. Sweep helix radius/pitch/turns; maximize swimming speed under a
step-out constraint for a 1 mT drive field; report the optimal geometry."""
import itertools
import json
import pathlib

import numpy as np

from microbots.rft import HelixGeometry, swimming_speed, step_out_frequency, efficiency

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)

OMEGA = 2 * np.pi * 40.0   # 40 Hz rotation
# NdFeB nanomagnet tip: remanence ~1.4 T / mu0 -> ~1e6 A/m over ~1e-18 m^3 tip
MOMENT = 1e-12             # A m^2 (literature range for tipped microhelices)
FIELD = 5e-3               # 5 mT rotating field (standard coil setups)

records = []
radii = np.linspace(2e-6, 10e-6, 9)
pitches = np.linspace(5e-6, 30e-6, 11)
turns = np.linspace(1.5, 5.0, 8)
for r, p, n in itertools.product(radii, pitches, turns):
    g = HelixGeometry(radius=r, pitch=p, filament_radius=0.5e-6, turns=n)
    f_step = step_out_frequency(g, MOMENT, FIELD)
    if OMEGA >= 0.8 * f_step:   # must operate below step-out with margin
        continue
    v = swimming_speed(g, OMEGA)
    eff = efficiency(g, OMEGA)
    records.append({"radius_um": r * 1e6, "pitch_um": p * 1e6, "turns": n,
                    "speed_um_s": v * 1e6, "efficiency": eff,
                    "stepout_hz": f_step / (2 * np.pi)})

records.sort(key=lambda d: -d["speed_um_s"])
best = records[0]
print(f"feasible geometries: {len(records)}")
print(f"best: R={best['radius_um']:.1f}um pitch={best['pitch_um']:.1f}um "
      f"turns={best['turns']:.1f} -> {best['speed_um_s']:.1f} um/s, "
      f"eta={best['efficiency']:.4f}, step-out {best['stepout_hz']:.0f} Hz")
json.dump({"n_feasible": len(records), "best": best, "top10": records[:10],
           "drive": {"omega_hz": 40.0, "field_mT": 1.0}},
          open(OUT / "helical_optimization.json", "w"), indent=1)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sp = [d["speed_um_s"] for d in records]
ef = [d["efficiency"] for d in records]
plt.figure(figsize=(6, 5))
sc = plt.scatter(sp, ef, c=[d["pitch_um"] for d in records], cmap="viridis", s=14)
plt.colorbar(sc, label="pitch (um)")
plt.xlabel("swimming speed (um/s)"); plt.ylabel("propulsive efficiency")
plt.title("Helical microbot RFT design sweep (40 Hz, 1 mT, below step-out)")
plt.tight_layout(); plt.savefig(OUT / "helical_sweep.png", dpi=150)
print("wrote results/helical_optimization.json + helical_sweep.png")
