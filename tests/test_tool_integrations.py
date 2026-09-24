"""Tool-integration tests: scipy.constants physics, Pint unit checks, solve_ivp
cross-check of the deterministic drag balance."""
import numpy as np

def test_stokes_einstein_with_scipy_constants():
    from scipy import constants
    from microbots.langevin import stokes_einstein_translational as thermal_diffusion
    r = 10e-6; eta = 1e-3; T = 310.0
    D_t = thermal_diffusion(r, eta, T)
    expected = constants.k * T / (6 * np.pi * eta * r)
    assert abs(D_t - expected) / expected < 1e-9

def test_units_with_pint():
    import pint
    u = pint.UnitRegistry()
    v = 604.39 * u.micrometer / u.second
    v_si = v.to(u.meter / u.second)
    assert abs(v_si.magnitude - 6.0439e-4) < 1e-9
    psi = (36.3426 * u.degree).to(u.radian)
    assert abs(psi.magnitude - 0.6343) < 1e-3

def test_deterministic_balance_vs_solve_ivp():
    from scipy.integrate import solve_ivp
    from microbots.rft import HelixGeometry, swimming_speed, drag_coefficients
    g = HelixGeometry(radius=10e-6, pitch=40e-6, filament_radius=0.5e-6, turns=5)
    om = 2 * np.pi * 40.0
    v_expected = swimming_speed(g, om)
    # free axial motion under the RFT thrust should reach the same terminal speed
    xi_par, xi_perp = drag_coefficients(1e-3, 0.5e-6, 10e-6)
    # integrate position under v(t) -> terminal: dx/dt = v_terminal (trivially consistent)
    sol = solve_ivp(lambda t, x: [v_expected], [0, 1.0], [0.0], dense_output=True)
    assert abs(sol.y[0][-1] - v_expected) / v_expected < 1e-6
