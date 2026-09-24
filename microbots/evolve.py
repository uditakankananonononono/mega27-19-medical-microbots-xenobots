"""Evolutionary search over xenobot actuation genomes: tournament selection,
Gaussian mutation, elitism. Real fitness evaluations against the soft-body sim."""
from __future__ import annotations
import numpy as np


def evolve_actuation(body, generations: int, pop_size: int, duration: float,
                     mutation_sigma: float = 0.4, elite: int = 2,
                     tournament: int = 3, seed: int = 0):
    """Returns (best_genome, best_fitness, history of per-generation stats)."""
    rng = np.random.default_rng(seed)
    pop = rng.uniform(0, 2 * np.pi, size=(pop_size, body.n_cells))
    history = []
    best_g, best_f = None, -np.inf
    for gen in range(generations):
        fitness = np.array([body.locomotion_fitness(g, duration) for g in pop])
        order = np.argsort(-fitness)
        if fitness[order[0]] > best_f:
            best_f = float(fitness[order[0]])
            best_g = pop[order[0]].copy()
        history.append({"generation": gen, "best": float(fitness[order[0]]),
                        "mean": float(fitness.mean()), "std": float(fitness.std())})
        new_pop = [pop[i].copy() for i in order[:elite]]
        while len(new_pop) < pop_size:
            cand = rng.choice(pop_size, size=tournament, replace=False)
            parent = pop[cand[np.argmax(fitness[cand])]]
            child = (parent + rng.normal(0, mutation_sigma, size=parent.shape)) % (2 * np.pi)
            new_pop.append(child)
        pop = np.array(new_pop)
    return best_g, best_f, history
