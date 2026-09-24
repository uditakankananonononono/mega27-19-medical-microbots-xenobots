"""Resistive force theory (RFT) for a helical magnetic microswimmer in
Stokes flow (low Reynolds number): real hydrodynamics per Purcell/Lauga.

Model: rigid helix of radius R, pitch lambda, filament radius a, N turns,
rotating about its axis at angular velocity omega in fluid of viscosity eta.
Local drag anisotropy on each filament element gives net thrust and torque.
"""
from __future__ import annotations
import math
from dataclasses import dataclass

WATER_VISCOSITY = 1e-3  # Pa.s at 20 C


@dataclass
class HelixGeometry:
    radius: float           # helix radius R (m)
    pitch: float            # helix pitch lambda (m)
    filament_radius: float  # filament radius a (m)
    turns: float            # number of turns N

    @property
    def contour_length(self) -> float:
        return self.turns * math.sqrt((2 * math.pi * self.radius) ** 2 + self.pitch ** 2)

    @property
    def pitch_angle(self) -> float:
        return math.atan2(2 * math.pi * self.radius, self.pitch)

    @property
    def axial_length(self) -> float:
        return self.turns * self.pitch


def drag_coefficients(eta: float, filament_radius: float, segment_length: float):
    """RFT drag coefficients per unit length for a slender filament
    (Lauga & Powers 2009 slender-body forms)."""
    if segment_length <= 2 * filament_radius:
        raise ValueError("segment too short for slender-body approximation")
    log_term = math.log(2 * segment_length / filament_radius)
    xi_perp = 4 * math.pi * eta / (log_term - 0.5)
    xi_par = 2 * math.pi * eta / (log_term - 1.0)
    return xi_perp, xi_par


def thrust_torque(geom: HelixGeometry, omega: float, eta: float = WATER_VISCOSITY):
    """Net axial thrust (N) and resistive torque (N.m) at rotation rate omega."""
    L = geom.contour_length
    xi_perp, xi_par = drag_coefficients(eta, geom.filament_radius, L)
    psi = geom.pitch_angle
    delta = xi_perp - xi_par
    thrust = delta * omega * geom.radius * math.sin(psi) * math.cos(psi) * L
    torque = (xi_perp * math.cos(psi) ** 2 + xi_par * math.sin(psi) ** 2) \
        * omega * geom.radius ** 2 * L
    return thrust, torque


def swimming_speed(geom: HelixGeometry, omega: float, eta: float = WATER_VISCOSITY,
                   body_drag: float = 0.0) -> float:
    """Steady swimming speed (m/s): thrust balances axial drag of helix+body."""
    L = geom.contour_length
    xi_perp, xi_par = drag_coefficients(eta, geom.filament_radius, L)
    psi = geom.pitch_angle
    axial_drag = (xi_perp * math.sin(psi) ** 2 + xi_par * math.cos(psi) ** 2) * L + body_drag
    thrust, _ = thrust_torque(geom, omega, eta)
    return thrust / axial_drag


def _torque_per_omega(geom: HelixGeometry, eta: float) -> float:
    L = geom.contour_length
    xi_perp, xi_par = drag_coefficients(eta, geom.filament_radius, L)
    psi = geom.pitch_angle
    return (xi_perp * math.cos(psi) ** 2 + xi_par * math.sin(psi) ** 2) \
        * geom.radius ** 2 * L


def step_out_frequency(geom: HelixGeometry, magnetic_moment: float,
                       field_strength: float, eta: float = WATER_VISCOSITY) -> float:
    """Step-out rotation rate (rad/s): magnetic torque m*B balances viscous
    resistive torque; beyond it the swimmer slips."""
    if magnetic_moment <= 0 or field_strength <= 0:
        return 0.0
    return magnetic_moment * field_strength / _torque_per_omega(geom, eta)


def efficiency(geom: HelixGeometry, omega: float, eta: float = WATER_VISCOSITY) -> float:
    """Propulsive efficiency: useful axial power / rotational input power."""
    v = swimming_speed(geom, omega, eta)
    _, torque = thrust_torque(geom, omega, eta)
    input_power = abs(torque * omega)
    if input_power == 0:
        return 0.0
    L = geom.contour_length
    xi_perp, xi_par = drag_coefficients(eta, geom.filament_radius, L)
    psi = geom.pitch_angle
    axial_drag = (xi_perp * math.sin(psi) ** 2 + xi_par * math.cos(psi) ** 2) * L
    return abs(axial_drag * v ** 2) / input_power
