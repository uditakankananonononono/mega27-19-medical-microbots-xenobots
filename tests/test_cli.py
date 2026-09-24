"""CLI smoke tests (hermetic): evaluate/design/threshold consistency with the solver."""
import json, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

def run(*args):
    return subprocess.run([sys.executable, "-m", "microbots.cli", *args],
                          capture_output=True, text=True, cwd=ROOT)

def test_evaluate_runs_and_reports_speed():
    out = run("evaluate", "--radius-um", "10", "--pitch-um", "40", "--turns", "5")
    assert out.returncode == 0, out.stderr
    d = json.loads(out.stdout)
    assert d["speed_um_s"] > 0 and 0 < d["efficiency"] < 1

def test_design_hits_target_speed():
    out = run("design", "--target-speed-um-s", "30", "--radius-um", "10")
    assert out.returncode == 0, out.stderr
    d = json.loads(out.stdout)
    assert abs(d["achieved_speed_um_s"] - 30.0) < 0.5

def test_threshold_record():
    out = run("threshold")
    assert out.returncode == 0
    d = json.loads(out.stdout)
    assert d["100%_delivery_at_or_above_um_s"] == 25.0
