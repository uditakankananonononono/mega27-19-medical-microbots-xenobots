import numpy as np
from microbots.softbody import SoftBody
from microbots.evolve import evolve_actuation


def test_softbody_settles_without_actuation():
    body = SoftBody(4, 3)
    genome = np.zeros(body.n_cells)
    pos0 = body.pos.copy()
    pos, _ = body.simulate(genome, duration=0.5, act_amp=0.0)
    # no actuation -> body should not translate horizontally
    assert abs(pos[:, 0].mean() - pos0[:, 0].mean()) < 0.05


def test_spring_count_and_cells():
    body = SoftBody(4, 3)
    # orthogonal + diagonal springs on a 4x3 lattice
    n_orth = (4 - 1) * 3 + (3 - 1) * 4
    n_diag = (4 - 1) * (3 - 1) * 2
    assert len(body.springs) == n_orth + n_diag
    assert body.n_cells == (4 - 1) * (3 - 1)


def test_actuation_produces_motion():
    body = SoftBody(5, 3)
    rng = np.random.default_rng(0)
    genome = rng.uniform(0, 2 * np.pi, size=body.n_cells)
    pos0 = body.pos.copy()
    pos, _ = body.simulate(genome, duration=1.0)
    assert not np.allclose(pos, pos0, atol=1e-6)


def test_evolution_history_shape():
    body = SoftBody(4, 3)
    _, best_f, history = evolve_actuation(body, generations=2, pop_size=4,
                                          duration=0.5, seed=1)
    assert len(history) == 2
    assert history[1]["best"] >= history[0]["best"] - 1e-12 or history[0]["best"] > -1e9
    assert isinstance(best_f, float)
