"""microbot-design: usable CLI built on the item-19 master-curve discovery.

Commands:
  evaluate  --radius-um R --pitch-um P --turns N --freq-hz F
      -> reduced speed, speed, efficiency, step-out check, delivery feasibility
  design    --target-speed-um-s V --radius-um R [--freq-hz F]
      -> geometry (pitch, turns) meeting the target speed via the master curve
  threshold -> print the delivery-feasibility threshold record
All physics from microbots.rft; thresholds from the measured noise study.
"""
from __future__ import annotations
import argparse, json, sys
import numpy as np
from scipy.optimize import brentq
from .rft import HelixGeometry, swimming_speed, efficiency, step_out_frequency

# measured delivery threshold (results/noise_sensitivity.json):
DELIVERY_MIN_UM_S = 25.0   # 100% delivery at/above this speed
DELIVERY_MAX_FAIL_UM_S = 10.0  # 0% delivery at/below this speed


def _feasibility(speed):
    if speed >= DELIVERY_MIN_UM_S:
        return "FEASIBLE (>=25 um/s: 100% delivery in 120 s window, measured)"
    if speed <= DELIVERY_MAX_FAIL_UM_S:
        return "INFEASIBLE (<=10 um/s: 0% delivery, measured)"
    return "MARGINAL (10-25 um/s: inside the measured feasibility cliff)"


def cmd_evaluate(a):
    g = HelixGeometry(radius=a.radius_um * 1e-6, pitch=a.pitch_um * 1e-6,
                      filament_radius=a.filament_um * 1e-6, turns=a.turns)
    om = 2 * np.pi * a.freq_hz
    v = swimming_speed(g, om) * 1e6
    eff = efficiency(g, om)
    so = step_out_frequency(g, magnetic_moment=1e-16, field_strength=1e-3)
    out = {"radius_um": a.radius_um, "pitch_um": a.pitch_um, "turns": a.turns,
           "freq_hz": a.freq_hz, "pitch_angle_rad": round(g.pitch_angle, 4),
           "speed_um_s": round(v, 2), "efficiency": round(eff, 4),
           "reduced_speed_v_over_omegaR": round(v * 1e-6 / (om * a.radius_um * 1e-6), 5),
           "step_out_hz_at_reference_drive": round(so, 1),
           "drive_margin_vs_stepout": "OK" if a.freq_hz < 0.5 * so else "TOO CLOSE TO STEP-OUT",
           "delivery_feasibility": _feasibility(v)}
    print(json.dumps(out, indent=1))


def cmd_design(a):
    om = 2 * np.pi * a.freq_hz
    R = a.radius_um * 1e-6
    def speed_at_pitch(p_um):
        g = HelixGeometry(radius=R, pitch=p_um * 1e-6,
                          filament_radius=a.filament_um * 1e-6, turns=a.turns)
        return swimming_speed(g, om) * 1e6 - a.target_speed_um_s
    # master curve: speed rises then falls with pitch angle; find the low-branch root
    try:
        p_star = brentq(speed_at_pitch, 1.0, 300.0, xtol=1e-3)
    except ValueError:
        print(json.dumps({"error": "target speed unreachable at this radius/frequency "
                                   "on the low branch; raise frequency or radius"}))
        sys.exit(1)
    g = HelixGeometry(radius=R, pitch=p_star * 1e-6,
                      filament_radius=a.filament_um * 1e-6, turns=a.turns)
    v = swimming_speed(g, om) * 1e6
    out = {"target_speed_um_s": a.target_speed_um_s, "achieved_speed_um_s": round(v, 2),
           "solution": {"radius_um": a.radius_um, "pitch_um": round(p_star, 2),
                        "turns": a.turns, "pitch_angle_rad": round(g.pitch_angle, 4)},
           "note": "turn count is hydrodynamically free (master-curve cancellation) - "
                   "choose it for payload/fabrication, not speed",
           "delivery_feasibility": _feasibility(v)}
    print(json.dumps(out, indent=1))


def cmd_threshold(a):
    print(json.dumps({
        "source": "results/noise_sensitivity.json (measured, n=40 per level)",
        "0%_delivery_at_or_below_um_s": DELIVERY_MAX_FAIL_UM_S,
        "100%_delivery_at_or_above_um_s": DELIVERY_MIN_UM_S,
        "explanation": "cliff set by rotational diffusion (Appendix W of the paper)"}, indent=1))


def main():
    ap = argparse.ArgumentParser(prog="microbot-design",
        description="Design/evaluate helical medical microbots via the master-curve discovery")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("evaluate"); d = sub.add_parser("design"); t = sub.add_parser("threshold")
    for p in (e, d):
        p.add_argument("--radius-um", type=float, required=True)
        p.add_argument("--filament-um", type=float, default=0.5)
        p.add_argument("--turns", type=float, default=5.0)
        p.add_argument("--freq-hz", type=float, default=40.0)
    e.add_argument("--pitch-um", type=float, required=True)
    d.add_argument("--target-speed-um-s", type=float, required=True)
    args = ap.parse_args()
    {"evaluate": cmd_evaluate, "design": cmd_design, "threshold": cmd_threshold}[args.cmd](args)

if __name__ == "__main__":
    main()
