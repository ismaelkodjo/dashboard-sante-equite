"""Extrait l'indicateur retenu du fichier OMS HEAT (xlsx ou csv) vers data/data_nettoye.csv.gz.

Usage : python scripts/prepare_data.py chemin/vers/fichier_oms.xlsx
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from traductions import CODE  # noqa: E402

if len(sys.argv) < 2:
    sys.exit(__doc__)
src = Path(sys.argv[1])
df = pd.read_excel(src) if src.suffix.lower() in (".xlsx", ".xls") else pd.read_csv(src)
df = df[df.indicator_abbr == CODE].dropna(axis=1, how="all").round(4)
out = ROOT / "data" / "data_nettoye.csv.gz"
df.to_csv(out, index=False, compression="gzip")
print(f"{len(df):,} lignes -> {out}")
