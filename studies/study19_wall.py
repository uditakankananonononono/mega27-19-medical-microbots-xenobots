"""Study 19 wall correction: Faxen hydrodynamic wall effects on microbot speed.

Bulk-fluid RFT (master curve, study19_mastercurve.py) assumes an unbounded
fluid. A microbot in a microvessel can swim within a body radius of the
endothelium, where wall hydrodynamics are first-order. This study applies
the exact Faxen series for a sphere moving near a plane wall:

  lambda_parallel(x) = 1 - (9/16)x + (1/8)x^3 - (45/256)x^4 - (1/16)x^5
  lambda_perp(x)     = 1 - (9/8)x + (1/2)x^3

with x = a/h (sphere radius a, center-to-wall distance h). At fixed thrust
the speed scales by lambda. Rows are parametrized by clearance c = h - a,
which is the physically controlled quantity (a robot cannot sit closer than
c=0). Validity limits, stated honestly: the series is single-wall and loses
accuracy in the lubrication regime (x > 0.8); in a capillary whose radius is
comparable to the robot (a/R > 0.3), two-wall confinement dominates and
these numbers are a lower-fidelity estimate, flagged in the JSON.

Outputs: results/wall_correction.json + wall_correction.png.
"""
import json
import pathlib

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
RES = ROOT / "results"

def faxen_parallel(x):
    x = np.asarray(x, float)
    return 1 - 9/16*x + 1/8*x**3 - 45/256*x**4 - 1/16*x**5

def faxen_perp(x):
    x = np.asarray(x, float)
    return 1 - 9/8*x + 1/2*x**3

a = 2.0  # um, robot body radius (within the paper's 1-10 um design band)
vessels = [("capillary", 5.0), ("postcapillary venule", 10.0),
           ("arteriole", 25.0), ("small artery", 50.0)]
clearances = [("wide (c=5a)", 5.0), ("close (c=a)", 1.0),
              ("grazing (c=0.1a)", 0.1)]
rows = []
for vname, R in vessels:
    confined = a / R > 0.3
    for cname, cfrac in clearances:
        c = cfrac * a
        h = a + c
        x = a / h
        rows.append({"vessel": vname, "vessel_radius_um": R,
                     "clearance": cname, "clearance_um": c,
                     "a_over_h": float(x),
                     "lambda_parallel": float(faxen_parallel(x)),
                     "lambda_perp": float(faxen_perp(x)),
                     "two_wall_confinement_regime": bool(confined)})

for r in rows:
    print(f"{r['vessel']:22s} {r['clearance']:18s} a/h={r['a_over_h']:.3f} "
          f"lambda_par={r['lambda_parallel']:.3f} lambda_perp={r['lambda_perp']:.3f}"
          f"{'  [confined: low fidelity]' if r['two_wall_confinement_regime'] else ''}")

# wall-corrected delivery threshold: bulk threshold 25 um/s (delivery
# feasibility study). Near-wall 'close' swimming (c=a, the realistic
# margination case) in unconfined vessels:
lam_close = float(faxen_parallel(0.5))
bulk_threshold = 25.0  # um/s
corrected = bulk_threshold / lam_close
print(f"close-swimming lambda_parallel (c=a, x=0.5) = {lam_close:.3f}")
print(f"bulk threshold {bulk_threshold} um/s -> {corrected:.1f} um/s "
      f"bulk-equivalent for close-to-wall operation")

out = {"model": "Faxen exact series, sphere near a single plane wall",
       "formulas": {"parallel": "1 - 9x/16 + x^3/8 - 45x^4/256 - x^5/16",
                    "perpendicular": "1 - 9x/8 + x^3/2"},
       "robot_radius_um": a,
       "validity": ["single-wall approximation; two-wall confinement "
                    "(a/R>0.3, capillary rows) is lower fidelity",
                    "series truncated at x^5; lubrication regime (x>0.8, "
                    "grazing rows) underestimates drag"],
       "table": rows,
       "close_swimming_lambda_parallel": lam_close,
       "bulk_delivery_threshold_um_s": bulk_threshold,
       "wall_corrected_bulk_equivalent_um_s": float(corrected),
       "verdict": (f"at a realistic close-to-wall clearance (c=a), wall drag "
                   f"cuts speed to {lam_close:.1%} of bulk; the bulk 25 um/s "
                   f"delivery threshold becomes a {corrected:.1f} um/s "
                   f"bulk-equivalent requirement. Grazing contact "
                   f"(c=0.1a) cuts speed to ~{float(faxen_parallel(1/1.1)):.1%} "
                   f"- near-wall crawling is strongly penalized.")}
(RES / "wall_correction.json").write_text(json.dumps(out, indent=1))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
xs = np.linspace(0.05, 0.95, 200)
ax1.plot(xs, faxen_parallel(xs), label="parallel")
ax1.plot(xs, faxen_perp(xs), label="perpendicular")
ax1.axvspan(0.8, 0.95, color="gray", alpha=0.15, label="lubrication: low fidelity")
ax1.set_xlabel("a/h (radius / center-wall distance)")
ax1.set_ylabel("Faxen lambda")
ax1.set_title("Faxen wall correction factors")
ax1.legend(fontsize=8); ax1.grid(alpha=0.3)
for r in rows:
    if r["clearance"].startswith("grazing") and not r["two_wall_confinement_regime"]:
        pass
vnames = [v[0] for v in vessels]
lam_close_rows = [r["lambda_parallel"] for r in rows if r["clearance"].startswith("close")]
colors = ["#e67e22" if r else "#2980b9" for r in [row["two_wall_confinement_regime"] for row in rows if row["clearance"].startswith("close")]]
ax2.bar(vnames, lam_close_rows, color=colors)
ax2.set_ylabel("lambda_parallel at c=a")
ax2.set_title("speed retention, close-to-wall (orange = confined, low fidelity)")
ax2.tick_params(axis="x", rotation=20); ax2.grid(alpha=0.3)
plt.tight_layout(); plt.savefig(RES / "wall_correction.png", dpi=150)
print("wrote results/wall_correction.json + wall_correction.png")
