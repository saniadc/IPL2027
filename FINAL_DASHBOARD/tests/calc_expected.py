"""Independent recomputation used by the filter test (reads the raw files directly, not via utils)."""
from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data"


def ipl_states():
    s = pd.read_csv(DATA / "processed/second_innings_pressure.csv.gz", usecols=["league"])
    return int((s.league == "IPL").sum())


def batters_at_least(n):
    fe = pd.read_csv(DATA / "final/FINAL_PLAYER_EVALUATION.csv")
    return int(((fe.role == "bat") & (fe.pressure_deliveries >= n)).sum())
