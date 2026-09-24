"""Integration utilities: pandas manifest export + imageio gait animation.
Real uses supporting the paper's manifest and figure assets."""
import json, pathlib
import numpy as np
import pandas as pd
import imageio.v2 as imageio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from microbots.softbody import SoftBody

ROOT = pathlib.Path(__file__).resolve().parent.parent
RES = ROOT / "results"

# pandas: consolidated dataset manifest CSV from the three verification records
frames = []
for f, fam in [("external_verification.json", "round1"), ("external_verification2.json", "round2"),
               ("external_verification3.json", "round3")]:
    d = json.loads((RES / f).read_text())
    for qname, qdata in d["queries"].items():
        n = len(qdata) if isinstance(qdata, dict) else 1
        frames.append({"round": fam, "query_family": qname, "records": n})
df = pd.DataFrame(frames)
df.loc[len(df)] = {"round": "TOTAL", "query_family": "", "records": int(df["records"].sum())}
df.to_csv(RES / "dataset_manifest.csv", index=False)
print(df.to_string(index=False))

# imageio: gait animation GIF from the evolved champion
evo = json.loads((RES / "xenobot_evolution.json").read_text())
body = SoftBody(6, 4)
genome = np.array(evo["best_genome_phases"])
_, traj = body.simulate(genome, duration=4.0, record=True)
frames_png = []
for i, frame in enumerate(traj[::6]):
    fig, ax = plt.subplots(figsize=(4, 2.5), dpi=60)
    ax.scatter(frame[:, 0], frame[:, 1], s=40, c="navy")
    ax.set_xlim(-1, 12); ax.set_ylim(-1, 6); ax.set_title(f"gait frame {i}")
    fig.canvas.draw()
    frames_png.append(np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy())
    plt.close(fig)
imageio.mimsave(RES / "xenobot_gait.gif", frames_png, duration=0.25)
print("wrote results/xenobot_gait.gif + dataset_manifest.csv")
