"""Convertit le classeur Excel brut en CSV compressé (chargement bien plus rapide).

Usage : python scripts/prepare_data.py [chemin_du_fichier.xlsx]
"""
import sys
from pathlib import Path

import pandas as pd

src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw/data_nettoye.xlsx")
out = Path("data/data_nettoye.csv.gz")
df = pd.read_excel(src).dropna(axis=1, how="all").round(4)
df.to_csv(out, index=False, compression="gzip")
print(f"{len(df):,} lignes -> {out}")
