"""Study 19.9: domain-randomized evolution pilot - roadmap priority 1.
Evolve actuation gaits under per-generation randomized physics (stiffness,
friction) and test whether the robust champion beats the original champion
on the off-design sensitivity grid."""
import json, pathlib
import numpy as np
from microbots.softbody import SoftBody

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "results"

def fitness_on(body_params, genome, duration=4.0):
    b = SoftBody(6, 4, stiffness=body_params[0], friction_mu=body_params[1])
    return b.locomotion_fitness(genome, duration)

def evolve_randomized(generations=14, pop_size=16, duration=4.0, seed=11,
                      k_range=(30.0, 120.0), mu_range=(0.4, 1.6)):
    """Fitness each generation = MEAN over two random physics draws (robust objective)."""
    rng = np.random.default_rng(seed)
    n_cells = SoftBody(6, 4).n_cells
    pop = rng.uniform(0, 2 * np.pi, size=(pop_size, n_cells))
    best_g, best_f = None, -np.inf
    history = []
    for gen in range(generations):
        draws = [(rng.uniform(*k_range), rng.uniform(*mu_range)) for _ in range(2)]
        fit = np.array([np.mean([fitness_on(d, g, duration) for d in draws]) for g in pop])
        order = np.argsort(-fit)
        if fit[order[0]] > best_f:
            best_f = float(fit[order[0]]); best_g = pop[order[0]].copy()
        history.append({"generation": gen, "best": float(fit[order[0]]),
                        "mean": float(fit.mean())})
        elite = [pop[i].copy() for i in order[:2]]
        new = elite
        while len(new) < pop_size:
            cand = rng.choice(pop_size, size=3, replace=False)
            parent = pop[cand[np.argmax(fit[cand])]]
            new.append((parent + rng.normal(0, 0.4, size=parent.shape)) % (2 * np.pi))
        pop = np.array(new)
    return best_g, best_f, history

GRID = [(k, m) for k in (30.0, 60.0, 120.0) for m in (0.4, 0.8, 1.6)]

print("evolving robust gait (domain-randomized objective)...")
rob_g, rob_f, hist = evolve_randomized()
orig = json.load(open(OUT / "xenobot_evolution.json"))
orig_g = np.array(orig["best_genome_phases"])

rob_grid = [fitness_on(p, rob_g) for p in GRID]
orig_grid = [fitness_on(p, orig_g) for p in GRID]
rec = {"robust_genome_fitness_train": rob_f,
       "grid": [{"stiffness": p[0], "friction_mu": p[1],
                 "original_champion": round(o, 3), "robust_champion": round(r, 3)}
                for p, o, r in zip(GRID, orig_grid, rob_grid)],
       "original_mean_grid": float(np.mean(orig_grid)),
       "robust_mean_grid": float(np.mean(rob_grid)),
       "original_min_grid": float(np.min(orig_grid)),
       "robust_min_grid": float(np.min(rob_grid)),
       "history": hist}
json.dump(rec, open(OUT / "domain_rand.json", "w"), indent=1)
print(f"original champion: mean grid {rec['original_mean_grid']:.2f}, min {rec['original_min_grid']:.2f}")
print(f"robust champion:   mean grid {rec['robust_mean_grid']:.2f}, min {rec['robust_min_grid']:.2f}")
print("wrote results/domain_rand.json")
