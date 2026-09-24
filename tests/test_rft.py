import math
import numpy as np
from microbots.rft import (HelixGeometry, drag_coefficients, thrust_torque,
                           swimming_speed, step_out_frequency, efficiency,
                           WATER_VISCOSITY)

GEOM = HelixGeometry(radius=5e-6, pitch=15e-6, filament_radius=0.5e-6, turns=3)


def test_drag_anisotropy_ratio():
    xi_perp, xi_par = drag_coefficients(WATER_VISCOSITY, 0.5e-6, 1e-4)
    # slender-body theory: xi_perp / xi_par approaches 2 for infinite slenderness
    assert 1.5 < xi_perp / xi_par < 2.0


def test_thrust_scales_linearly_with_omega():
    t1, _ = thrust_torque(GEOM, 100.0)
    t2, _ = thrust_torque(GEOM, 200.0)
    assert abs(t2 / t1 - 2.0) < 1e-12
    assert t1 > 0


def test_swimming_speed_physical_magnitude():
    # 5 um helix at 100 rad/s in water: expect um/s to tens of um/s
    v = swimming_speed(GEOM, 100.0)
    assert 1e-7 < v < 1e-3


def test_zero_thrust_at_zero_and_quarter_turn_pitch():
    g0 = HelixGeometry(radius=0.0, pitch=15e-6, filament_radius=0.5e-6, turns=3)
    thrust, _ = thrust_torque(g0, 100.0)
    assert abs(thrust) < 1e-20


def test_step_out_increases_with_field():
    f1 = step_out_frequency(GEOM, 1e-15, 1e-3)
    f2 = step_out_frequency(GEOM, 1e-15, 2e-3)
    assert f2 > f1 > 0


def test_efficiency_bounded():
    eff = efficiency(GEOM, 100.0)
    assert 0.0 < eff < 0.5  # bacterial/helix RFT efficiencies are a few percent
