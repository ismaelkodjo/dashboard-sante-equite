"""Tableau de bord dynamique – maladies chroniques et équité en santé (format OMS HEAT)."""
import io
import re
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

DEFAULT_FILE = Path(__file__).parent / "data" / "data_nettoye.csv.gz"
REQUIRED = {"setting", "date", "indicator_abbr", "indicator_name", "dimension", "subgroup",
            "estimate", "ci_lb", "ci_ub", "setting_average", "iso3",
            "favourable_indicator", "subgroup_order"}

# Sous-thèmes des maladies chroniques : le premier qui correspond l'emporte.
# Un indicateur qui ne correspond à aucun sous-thème est hors périmètre et n'est pas chargé.
THEMES = [
    ("Mortalité par maladies chroniques", r"NCD\) mortality|premature deaths|probability of dying between age 30|cancer mortality"),
    ("Hypertension", r"hypertension|blood pressure"),
    ("Diabète", r"diabetes"),
    ("Cholestérol", r"cholesterol"),
    ("Activité physique", r"physical activity"),
]
DISPLAY = ["Hypertension", "Diabète", "Cholestérol", "Mortalité par maladies chroniques", "Activité physique"]
PREFERRED = "NCD_HYP_PREVALENCE_A"  # indicateur affiché par défaut


def theme_of(text: str):
    return next((label for label, pattern in THEMES if re.search(pattern, text, re.I)), None)


@st.cache_data(show_spinner="Chargement des données…")
def load(content: bytes, name: str) -> pd.DataFrame:
    buf = io.BytesIO(content)
    if name.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(buf)
    else:
        df = pd.read_csv(buf, compression="gzip" if name.lower().endswith(".gz") else None)
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError("colonnes manquantes : " + ", ".join(sorted(missing)))
    df["date"] = df["date"].astype(int)
    ind = df[["indicator_abbr", "indicator_name"]].drop_duplicates("indicator_abbr")
    ind["theme"] = (ind.indicator_abbr + " " + ind.indicator_name).map(theme_of)
    df = df.merge(ind[["indicator_abbr", "theme"]], on="indicator_abbr").dropna(subset=["theme"])
    if df.empty:
        raise ValueError("aucun indicateur de maladie chronique dans ce fichier")
    return df


st.set_page_config(page_title="Tableau de bord – Maladies chroniques", page_icon="📊", layout="wide")
sb = st.sidebar
sb.header("Filtres")
up = sb.file_uploader("Charger un autre fichier (xlsx / csv, format OMS HEAT)", type=["xlsx", "csv", "gz"])
try:
    df = load(up.getvalue(), up.name) if up else load(DEFAULT_FILE.read_bytes(), DEFAULT_FILE.name)
except Exception as exc:  # fichier illisible ou au mauvais format
    st.error(f"Impossible de lire le fichier : {exc}")
    st.stop()

themes = sorted(df.theme.unique(), key=DISPLAY.index)
theme = sb.selectbox("Sous-thème", themes)
inds = df.loc[df.theme == theme, ["indicator_abbr", "indicator_name"]].drop_duplicates().sort_values("indicator_name")
names = inds.indicator_name.tolist()
pref = inds.loc[inds.indicator_abbr == PREFERRED, "indicator_name"].tolist()
ind = sb.selectbox("Indicateur", names, index=names.index(pref[0]) if pref else 0)
sub = df[df.indicator_name == ind]
all_countries = sorted(sub.setting.unique())
countries = sb.multiselect("Pays", all_countries, default=all_countries)
ymin, ymax = int(sub.date.min()), int(sub.date.max())
y0, y1 = sb.slider("Période", ymin, ymax, (ymin, ymax)) if ymin < ymax else (ymin, ymax)

st.title("Tableau de bord – maladies chroniques")
st.caption(f"{theme} · Indicateur : **{ind}** · {len(countries)} pays · {y0}–{y1}")

d = sub[sub.setting.isin(countries) & sub.date.between(y0, y1)]
if d.empty:
    st.warning("Aucune donnée pour cette sélection.")
    st.stop()
fav = bool(d.favourable_indicator.iloc[0])  # True : une valeur élevée est favorable
scale = "RdYlGn" if fav else "RdYlGn_r"

# Moyenne nationale par pays et par année (setting_average est répétée sur chaque sous-groupe)
nat = (d.dropna(subset=["setting_average"]).groupby(["setting", "iso3", "date"], as_index=False)
       .setting_average.mean().sort_values("date"))

if not nat.empty:
    cols = st.columns(min(4, nat.setting.nunique()))
    for i, (country, g) in enumerate(nat.groupby("setting")):
        last, delta = g.iloc[-1], None
        if len(g) > 1:
            delta = f"{last.setting_average - g.iloc[-2].setting_average:+.1f} vs {int(g.iloc[-2].date)}"
        cols[i % len(cols)].metric(f"{country} ({int(last.date)})", f"{last.setting_average:,.1f}", delta,
                                   delta_color="normal" if fav else "inverse")

t1, t2, t3, t4 = st.tabs(["Vue d'ensemble", "Tendances", "Inégalités", "Données"])

with t1:
    if nat.empty:
        st.warning("Aucune moyenne nationale disponible pour cette sélection.")
    else:
        latest = nat.groupby("setting", as_index=False).tail(1)
        a, b = st.columns(2)
        m = px.choropleth(latest, locations="iso3", color="setting_average", hover_name="setting",
                          hover_data={"date": True, "iso3": False}, color_continuous_scale=scale, scope="africa",
                          labels={"setting_average": "Valeur", "date": "Année"},
                          title="Dernière valeur disponible par pays")
        m.update_geos(fitbounds="locations", showcountries=True)
        m.update_layout(margin=dict(l=0, r=0, t=40, b=0))
        a.plotly_chart(m)
        bar = px.bar(latest.sort_values("setting_average"), x="setting_average", y="setting", orientation="h",
                     text="setting_average", color="setting_average", color_continuous_scale=scale, title="Classement")
        bar.update_traces(texttemplate="%{text:.1f}")
        bar.update_layout(coloraxis_showscale=False, xaxis_title=None, yaxis_title=None)
        b.plotly_chart(bar)

with t2:
    if nat.empty:
        st.warning("Aucune moyenne nationale disponible pour cette sélection.")
    else:
        st.plotly_chart(px.line(nat, x="date", y="setting_average", color="setting", markers=True,
                                labels={"date": "Année", "setting_average": "Valeur", "setting": "Pays"}))
        chg = nat.groupby("setting").agg(début=("date", "first"), valeur_début=("setting_average", "first"),
                                         fin=("date", "last"), valeur_fin=("setting_average", "last"))
        chg["variation"] = chg.valeur_fin - chg.valeur_début
        chg["variation_%"] = (chg.variation / chg.valeur_début * 100).replace([np.inf, -np.inf], np.nan)
        st.subheader("Évolution sur la période")
        st.dataframe(chg.round(2))

with t3:
    dims = sorted(d.dropna(subset=["estimate"]).dimension.unique())
    if not dims:
        st.info("Aucune donnée désagrégée pour cet indicateur.")
    else:
        dim = st.selectbox("Dimension d'inégalité", dims)
        e = d[d.dimension == dim].dropna(subset=["estimate"])
        e = e.assign(err_up=(e.ci_ub - e.estimate).clip(lower=0), err_dn=(e.estimate - e.ci_lb).clip(lower=0))
        e_last = e[e.date == e.groupby("setting").date.transform("max")].copy()
        e_last["pays"] = e_last.setting + " (" + e_last.date.astype(str) + ")"
        order_sg = e.sort_values("subgroup_order").subgroup.unique().tolist()
        st.plotly_chart(px.bar(e_last, x="pays", y="estimate", color="subgroup", barmode="group",
                               error_y="err_up", error_y_minus="err_dn", category_orders={"subgroup": order_sg},
                               labels={"estimate": "Estimation (IC 95 %)", "pays": "", "subgroup": "Sous-groupe"},
                               title="Dernière année disponible par pays"))
        gap = e.groupby(["setting", "date"]).estimate.agg(["max", "min", "count"]).reset_index()
        gap = gap[gap["count"] >= 2]
        gap["Écart absolu"] = gap["max"] - gap["min"]
        gap["Rapport"] = gap["max"] / gap["min"].replace(0, np.nan)
        measure = st.radio("Mesure d'inégalité", ["Écart absolu", "Rapport"], horizontal=True)
        st.caption("Écart absolu = valeur max − valeur min parmi les sous-groupes ; rapport = max / min. "
                   "Plus la mesure est élevée (rapport > 1), plus l'inégalité est marquée.")
        st.plotly_chart(px.line(gap, x="date", y=measure, color="setting", markers=True,
                                labels={"date": "Année", "setting": "Pays"}))
        st.dataframe(gap.sort_values("date").groupby("setting").tail(1)
                     .rename(columns={"setting": "Pays", "date": "Année", "max": "Max", "min": "Min"})
                     .drop(columns="count").round(2), hide_index=True)

with t4:
    cols_show = ["setting", "date", "dimension", "subgroup", "estimate", "ci_lb", "ci_ub", "setting_average"]
    st.dataframe(d[cols_show], hide_index=True)
    st.download_button("Télécharger la sélection (CSV)", d[cols_show].to_csv(index=False).encode("utf-8-sig"),
                       file_name="selection.csv", mime="text/csv")

st.caption("Source : fichier chargé (format OMS HEAT – Health Equity Assessment Toolkit). "
           "Les noms d'indicateurs sont ceux du fichier source.")
