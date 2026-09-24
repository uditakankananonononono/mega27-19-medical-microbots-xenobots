"""Study 19.8: gait robustness - champion genome fitness across stiffness and
friction. Is the evolved gait tuned to its physics, or robust to parameter drift?"""
import json
import pathlib
import numpy as np
from microbots.softbody import SoftBody

OUT = pathlib.Path(__file__).resolve().parent.parent / "results"
genome = np.array(json.loads((OUT / "xenobot_evolution.json").read_text())["best_genome_phases"])
rows = []
for k in (30.0, 60.0, 120.0):
    for mu in (0.4, 0.8, 1.6):
        body = SoftBody(6, 4, stiffness=k, friction_mu=mu)
        f = body.locomotion_fitness(genome, 4.0)
        rows.append({"stiffness": k, "friction_mu": mu, "fitness": f})
        print(f"k={k} mu={mu}: fitness {f:.3f}", flush=True)
json.dump(rows, open(OUT / "gait_sensitivity.json", "w"), indent=1)
print("wrote results/gait_sensitivity.json")
