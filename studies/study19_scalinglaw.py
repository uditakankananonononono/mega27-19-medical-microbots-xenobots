"""Study 19.4 (discovery): extend the helix sweep past the original grid boundary,
find the true constrained optimum, and fit a verified scaling law for swimming
speed. Honest report either way: a validated law or a documented failure."""
import itertools
import json
import pathlib

import numpy as np

from microbots.rft import HelixGeometry, swimming_speed, step_out_frequency, efficiency

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "results"

OMEGA = 2 * np.pi * 40.0
MOMENT, FIELD = 1e-12, 5e-3

radii = np.linspace(5e-6, 25e-6, 9)
pitches = np.linspace(20e-6, 80e-6, 13)
turns = np.linspace(1.0, 4.0, 7)
records = []
for r, p, n in itertools.product(radii, pitches, turns):
    g = HelixGeometry(radius=r, pitch=p, filament_radius=0.5e-6, turns=n)
    f_step = step_out_frequency(g, MOMENT, FIELD)
    if OMEGA >= 0.8 * f_step:
        continue
    records.append({"R": r, "pitch": p, "turns": n,
                    "v": swimming_speed(g, OMEGA),
                    "eff": efficiency(g, OMEGA),
                    "stepout": f_step})
print(f"extended feasible island: {len(records)} geometries")
records.sort(key=lambda d: -d["v"])
best = records[0]
print(f"true constrained optimum: R={best['R']*1e6:.1f}um pitch={best['pitch']*1e6:.1f}um "
      f"turns={best['turns']:.1f} v={best['v']*1e6:.0f}um/s eff={best['eff']*100:.1f}%")

# ---- scaling-law fit on log space with held-out validation
rng = np.random.default_rng(0)
idx = rng.permutation(len(records))
train, test = idx[: int(0.8 * len(idx))], idx[int(0.8 * len(idx)):]
X = np.array([[np.log(records[i]["R"]), np.log(records[i]["pitch"]),
               np.log(records[i]["turns"]), 1.0] for i in range(len(records))])
y = np.log([records[i]["v"] for i in range(len(records))])
coef, *_ = np.linalg.lstsq(X[train], y[train], rcond=None)
pred_test = X[test] @ coef
ss_res = float(((y[test] - pred_test) ** 2).sum())
ss_tot = float(((y[test] - y[test].mean()) ** 2).sum())
r2 = 1 - ss_res / ss_tot
print(f"scaling law: ln v = {coef[0]:.3f} ln R + {coef[1]:.3f} ln pitch "
      f"+ {coef[2]:.3f} ln turns + {coef[3]:.3f}")
print(f"held-out R^2 = {r2:.4f} (n_test={len(test)})")
verdict = "SCALING LAW HOLDS" if r2 > 0.95 else "SCALING LAW INADEQUATE - honest negative"
print(verdict)
json.dump({"records": [{k: float(v) for k, v in r.items()} for r in records],
           "n_feasible": len(records),
           "optimum": {k: (v if not isinstance(v, np.floating) else float(v))
                       for k, v in best.items()},
           "law_coefficients": {"ln_R": float(coef[0]), "ln_pitch": float(coef[1]),
                                "ln_turns": float(coef[2]), "intercept": float(coef[3])},
           "heldout_r2": r2, "verdict": verdict,
           "drive": {"omega_hz": 40.0, "field_mT": 5.0}},
          open(OUT / "scaling_law.json", "w"), indent=1)
print("wrote results/scaling_law.json")
