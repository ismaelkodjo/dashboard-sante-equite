"""Tableau de bord dynamique – maladies chroniques et équité en santé (données OMS HEAT)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from traductions import CODE, LIBELLE, PAYS, dimension_fr, sous_groupe_fr  # noqa: E402

DEFAULT_FILE = Path(__file__).parent / "data" / "data_nettoye.csv.gz"


def fr(x: float, signe: bool = False) -> str:
    """Nombre au format français (1 234,5)."""
    return format(x, "+,.1f" if signe else ",.1f").replace(",", "\u202f").replace(".", ",")


def show(fig):
    fig.update_layout(separators=", ")  # virgule décimale, espace pour les milliers
    st.plotly_chart(fig)


@st.cache_data(show_spinner="Chargement des données…")
def load() -> pd.DataFrame:
    df = pd.read_csv(DEFAULT_FILE)
    df = df[df.indicator_abbr == CODE].copy()
    df["setting"] = df.setting.replace(PAYS)
    df["dimension"] = df.dimension.map(dimension_fr)
    df["subgroup"] = df.subgroup.map(sous_groupe_fr)
    return df


st.set_page_config(page_title="Tableau de bord – Hypertension", page_icon="📊", layout="wide")
st.markdown("<style>.modebar-container{display:none}</style>", unsafe_allow_html=True)  # barre d'outils Plotly (anglais)
df = load()

sb = st.sidebar
sb.header("Filtres")
all_countries = sorted(df.setting.unique())
countries = sb.multiselect("Pays", all_countries, default=all_countries, placeholder="Choisir des pays")
ymin, ymax = int(df.date.min()), int(df.date.max())
y0, y1 = sb.slider("Période", ymin, ymax, (ymin, ymax)) if ymin < ymax else (ymin, ymax)

st.title("Prévalence de l'hypertension en Afrique de l'Ouest")
st.caption(f"{LIBELLE} · valeurs standardisées selon l'âge · {len(countries)} pays · {y0}–{y1}")

d = df[df.setting.isin(countries) & df.date.between(y0, y1)]
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
            delta = f"{fr(last.setting_average - g.iloc[-2].setting_average, True)} vs {int(g.iloc[-2].date)}"
        cols[i % len(cols)].metric(f"{country} ({int(last.date)})", fr(last.setting_average), delta,
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
        with a:
            show(m)
        bar = px.bar(latest.sort_values("setting_average"), x="setting_average", y="setting", orientation="h",
                     text="setting_average", color="setting_average", color_continuous_scale=scale, title="Classement",
                     labels={"setting_average": "Valeur", "setting": "Pays", "date": "Année"},
                     hover_data={"date": True})
        bar.update_traces(texttemplate="%{text:.1f}")
        bar.update_layout(coloraxis_showscale=False, xaxis_title=None, yaxis_title=None)
        with b:
            show(bar)

with t2:
    if nat.empty:
        st.warning("Aucune moyenne nationale disponible pour cette sélection.")
    else:
        show(px.line(nat, x="date", y="setting_average", color="setting", markers=True,
                     labels={"date": "Année", "setting_average": "Valeur", "setting": "Pays"}))
        chg = nat.groupby("setting").agg(debut=("date", "first"), v0=("setting_average", "first"),
                                         fin=("date", "last"), v1=("setting_average", "last"))
        chg["var"] = chg.v1 - chg.v0
        chg["pct"] = (chg["var"] / chg.v0 * 100).replace([np.inf, -np.inf], np.nan)
        chg.columns = ["Année de début", "Valeur de début", "Année de fin", "Valeur de fin", "Variation", "Variation (%)"]
        st.subheader("Évolution sur la période")
        st.dataframe(chg.rename_axis("Pays").round(2))

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
        fig = px.bar(e_last, x="pays", y="estimate", color="subgroup", barmode="group",
                     error_y="err_up", error_y_minus="err_dn", category_orders={"subgroup": order_sg},
                     hover_data={"err_up": False, "err_dn": False},
                     labels={"estimate": "Estimation (IC 95 %)", "pays": "Pays", "subgroup": "Sous-groupe"},
                     title="Dernière année disponible par pays")
        fig.update_layout(xaxis_title=None)
        show(fig)
        gap = e.groupby(["setting", "date"]).estimate.agg(["max", "min", "count"]).reset_index()
        gap = gap[gap["count"] >= 2]
        gap["Écart absolu"] = gap["max"] - gap["min"]
        gap["Rapport"] = gap["max"] / gap["min"].replace(0, np.nan)
        measure = st.radio("Mesure d'inégalité", ["Écart absolu", "Rapport"], horizontal=True)
        st.caption("Écart absolu = valeur max − valeur min parmi les sous-groupes ; rapport = max / min. "
                   "Plus la mesure est élevée (rapport > 1), plus l'inégalité est marquée.")
        show(px.line(gap, x="date", y=measure, color="setting", markers=True,
                     labels={"date": "Année", "setting": "Pays"}))
        st.dataframe(gap.sort_values("date").groupby("setting").tail(1)
                     .rename(columns={"setting": "Pays", "date": "Année", "max": "Maximum", "min": "Minimum"})
                     .drop(columns="count").round(2), hide_index=True)

with t4:
    labels = {"setting": "Pays", "date": "Année", "dimension": "Dimension", "subgroup": "Sous-groupe",
              "estimate": "Estimation", "ci_lb": "IC 95 % – borne inférieure", "ci_ub": "IC 95 % – borne supérieure",
              "setting_average": "Moyenne nationale"}
    out = d[list(labels)].rename(columns=labels)
    st.dataframe(out, hide_index=True)
    st.download_button("Télécharger la sélection (CSV)", out.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       file_name="selection.csv", mime="text/csv")
    st.caption("Le fichier CSV utilise le format français : séparateur « ; » et virgule décimale (ouverture directe dans Excel).")

st.caption("Source : Organisation mondiale de la santé (OMS), Boîte à outils d'évaluation de l'équité en santé (HEAT). "
           "Libellés traduits en français à partir du fichier source.")
