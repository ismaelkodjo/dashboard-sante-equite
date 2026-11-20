import re
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from traductions import CODE, LIBELLE, PAYS, dimension_fr, sous_groupe_fr  # noqa: E402

APP = str(ROOT / "app.py")
# Mots anglais du fichier source et noms de colonnes bruts qui ne doivent apparaître nulle part.
ANGLAIS = re.compile(r"\b(years|Female|Male|Urban|poorest|richest|mortality|prevalence|treatment|coverage|diabetes"
                     r"|cholesterol|standardized|Sex|residence|Economic|status|groups)\b"
                     r"|setting|estimate|subgroup|iso3|err_up|err_dn", re.I)


def test_app_loads():
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception
    assert len(at.tabs) == 4


def test_traductions_completes():
    df = pd.read_csv(ROOT / "data" / "data_nettoye.csv.gz")
    df = df[df.indicator_abbr == CODE]
    textes = (set(df.setting.replace(PAYS)) | set(df.dimension.map(dimension_fr))
              | set(df.subgroup.map(sous_groupe_fr)) | {LIBELLE})
    assert not [t for t in textes if ANGLAIS.search(t)]


def test_un_seul_indicateur_8_pays():
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception
    assert len(at.sidebar.selectbox) == 0 and len(at.main.selectbox) == 0
    assert sum(m.value.count("class='carte'") for m in at.markdown) == 8


def test_interface_et_graphiques_en_francais(monkeypatch):
    figs = []
    monkeypatch.setattr(st, "plotly_chart", lambda fig, *a, **k: figs.append(fig.to_json()))
    at = AppTest.from_file(APP, default_timeout=120).run()
    assert not at.exception
    textes = [e.value for e in at.markdown] + [e.value for e in at.caption]
    textes += [m.label for m in at.metric]
    for box in at.main.selectbox:
        textes += [box.label, *box.options]
    assert not [t for t in textes if ANGLAIS.search(t)]
    assert figs and not [f for f in figs if ANGLAIS.search(f)]


def test_donnees_un_seul_indicateur():
    df = pd.read_csv(ROOT / "data" / "data_nettoye.csv.gz")
    assert df.indicator_abbr.unique().tolist() == [CODE] and len(df) == 480
