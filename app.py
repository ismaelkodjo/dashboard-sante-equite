"""Tableau de bord – prévalence de l'hypertension en Afrique de l'Ouest (données OMS HEAT)."""
import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from traductions import CODE, LIBELLE, PAYS, dimension_fr, sous_groupe_fr  # noqa: E402

DEFAULT_FILE = Path(__file__).parent / "data" / "data_nettoye.csv.gz"
F, H = "Femmes", "Hommes"
C_F, C_H, ENCRE = "#C2185B", "#0E7C86", "#0B2545"  # femmes, hommes, bleu nuit
PALETTE = ["#0B2545", "#C2185B", "#0E7C86", "#E8A33D", "#5B8E3E", "#7D4E9E", "#D1603D", "#4F6D8F"]
FONT = "DM Sans, Segoe UI, sans-serif"

CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;800&family=DM+Sans:wght@400;500;700&display=swap');
.stApp {background:#EEF3F6; font-family:'DM Sans','Segoe UI',sans-serif; color:#0B2545;}
#MainMenu, footer {visibility:hidden;}
.modebar-container {display:none;}
.block-container {max-width:1240px; padding-top:1.4rem;}
section[data-testid='stSidebar'] {background:#FFFFFF;}
.hero {background:#0B2545; color:#fff; border-radius:18px; padding:34px 40px 30px; margin-bottom:22px;}
.hero p {margin:0; color:#fff;}
.hero .sur {font-size:.95rem; opacity:.72; margin-bottom:12px;}
.hero h1 {font-family:'Bricolage Grotesque',sans-serif; font-weight:800; font-size:2.3rem; line-height:1.18; color:#fff; margin:0; padding:0; max-width:920px;}
.hero .sexe {margin-top:18px; font-size:1.1rem; opacity:.92; max-width:840px; border-top:1px solid rgba(255,255,255,.25); padding-top:14px;}
.cartes {display:grid; grid-template-columns:repeat(auto-fill,minmax(215px,1fr)); gap:14px; margin-bottom:14px;}
.carte {background:#fff; border-radius:8px; padding:14px 16px 12px; border-left:6px solid var(--c);}
.carte .n {font-weight:700; font-size:1.02rem;}
.carte .v {font-family:'Bricolage Grotesque',sans-serif; font-size:2.1rem; font-weight:800; line-height:1.15;}
.carte .a {font-size:.84rem; color:#586A82;}
.carte .b {height:6px; background:#E3EAF0; border-radius:3px; margin:9px 0;}
.carte .b i {display:block; height:6px; border-radius:3px; background:var(--c);}
.carte .sx {font-size:.85rem; display:flex; justify-content:space-between;}
.pt {display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:5px;}
.bon {color:#1E8E5A; font-weight:700;} .mauvais {color:#C0392B; font-weight:700;}
.duo {display:flex; flex-wrap:wrap; gap:14px 44px; margin:4px 0 16px;}
.duo div {font-family:'Bricolage Grotesque',sans-serif; font-size:2.7rem; font-weight:800; line-height:1.1;}
.duo small {display:block; font-family:'DM Sans',sans-serif; font-size:.95rem; font-weight:500; color:#586A82;}
.stTabs [data-baseweb='tab-list'] {gap:8px;}
.stTabs [data-baseweb='tab'] {background:#fff; border-radius:999px; padding:8px 22px;}
.stTabs [aria-selected='true'] {background:#0B2545;}
.stTabs [aria-selected='true'] p {color:#fff;}
.stTabs [data-baseweb='tab-highlight'], .stTabs [data-baseweb='tab-border'] {display:none;}
[data-testid='stPlotlyChart'] {background:#fff; border-radius:12px; padding:8px 10px;}
</style>"""


def fr(x: float, signe: bool = False) -> str:
    """Nombre au format français (1 234,5)."""
    return format(x, "+,.1f" if signe else ",.1f").replace(",", "\u202f").replace(".", ",")


def show(fig, hauteur=430):
    fig.update_layout(separators=", ", template="plotly_white", height=hauteur, font=dict(family=FONT, color=ENCRE),
                      legend=dict(orientation="h", y=1.12, x=0, title_text=""), hoverlabel=dict(font_family=FONT))
    st.plotly_chart(fig, theme=None)


@st.cache_data(show_spinner="Chargement des données…")
def load() -> pd.DataFrame:
    df = pd.read_csv(DEFAULT_FILE)
    df = df[df.indicator_abbr == CODE].copy()
    df["setting"] = df.setting.replace(PAYS)
    df["dimension"] = df.dimension.map(dimension_fr)
    df["subgroup"] = df.subgroup.map(sous_groupe_fr)
    return df


st.set_page_config(page_title="Hypertension en Afrique de l'Ouest", page_icon="🫀", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
df = load()

sb = st.sidebar
sb.header("Filtres")
all_countries = sorted(df.setting.unique())
countries = sb.multiselect("Pays", all_countries, default=all_countries, placeholder="Choisir des pays")
ymin, ymax = int(df.date.min()), int(df.date.max())
y0, y1 = sb.slider("Période", ymin, ymax, (ymin, ymax)) if ymin < ymax else (ymin, ymax)

d = df[df.setting.isin(countries) & df.date.between(y0, y1)]
if d.empty:
    st.warning("Choisissez au moins un pays.")
    st.stop()
fav = bool(d.favourable_indicator.iloc[0])  # True : une valeur élevée est favorable
echelle = ["#FFF1D6", "#F6B26B", "#D9534F", "#7A1E0E"]
echelle = echelle[::-1] if fav else echelle
couleur = {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(all_countries)}


def tendance(diff):
    """(classe CSS, texte) d'une variation ; vert si elle va dans le bon sens."""
    if abs(diff) < 0.05:
        return "", "► stable"
    return ("bon" if (diff > 0) == fav else "mauvais"), f"{'▲' if diff > 0 else '▼'} {fr(diff, True)} pt"


# Moyenne nationale par pays et par année (setting_average est répétée sur chaque sous-groupe)
nat = (d.dropna(subset=["setting_average"]).groupby(["setting", "iso3", "date"], as_index=False)
       .setting_average.mean().sort_values("date"))
first, last = nat.groupby("setting").first(), nat.groupby("setting").last()
y_first, y_last = int(nat.date.min()), int(nat.date.max())
val = last.setting_average
moy = val.mean()

# Répartition selon le sexe (dernière année disponible de chaque pays)
e = d[d.dimension == "Sexe"].dropna(subset=["estimate"])
p = pd.DataFrame()
if not e.empty:
    p = e[e.date == e.groupby("setting").date.transform("max")].pivot_table(index="setting", columns="subgroup", values="estimate")
sexes = {F, H} <= set(p.columns)
if sexes:
    p["ecart"] = p[F] - p[H]

# --- En-tête : le constat en une phrase
if len(val) > 1:
    phrase = (f"En {y_last}, {fr(moy)} % des adultes de 30 à 79 ans sont hypertendus en moyenne, "
              f"de {fr(val.min())} % ({val.idxmin()}) à {fr(val.max())} % ({val.idxmax()}).")
else:
    phrase = f"En {y_last}, {fr(moy)} % des adultes de 30 à 79 ans sont hypertendus ({val.index[0]})."
sexe_txt = ""
if sexes:
    n = int((p.ecart > 0).sum())
    sexe_txt = (f"<p class='sexe'>La prévalence est plus élevée chez les femmes que chez les hommes dans {n} pays sur "
                f"{len(p)}. Écart moyen femmes − hommes : {fr(p.ecart.mean(), True)} points.</p>")
st.markdown(f"<div class='hero'><p class='sur'>{LIBELLE} – valeurs standardisées selon l'âge, moyenne simple "
            f"des pays sélectionnés, source OMS</p><h1>{phrase}</h1>{sexe_txt}</div>", unsafe_allow_html=True)

# --- Une carte par pays
cartes = []
for c in last.index:
    cls, txt = tendance(val[c] - first.setting_average[c])
    sx = ""
    if sexes and c in p.index:
        sx = (f"<div class='sx'><span><span class='pt' style='background:{C_F}'></span>{F} {fr(p.loc[c, F])} %</span>"
              f"<span><span class='pt' style='background:{C_H}'></span>{H} {fr(p.loc[c, H])} %</span></div>")
    cartes.append(f"<div class='carte' style='--c:{couleur[c]}'><div class='n'>{c}</div>"
                  f"<div class='v'>{fr(val[c])} %</div><div class='a'><span class='{cls}'>{txt}</span> depuis {y_first}</div>"
                  f"<div class='b'><i style='width:{min(100, val[c] / df.setting_average.max() * 100):.0f}%'></i></div>{sx}</div>")
st.markdown(f"<div class='cartes'>{''.join(cartes)}</div>", unsafe_allow_html=True)

t1, t2, t3, t4 = st.tabs(["Vue d'ensemble", "Tendances", "Femmes et hommes", "Données"])

with t1:
    a, b = st.columns(2)
    m = px.choropleth(last.reset_index(), locations="iso3", color="setting_average", hover_name="setting",
                      hover_data={"date": True, "iso3": False}, color_continuous_scale=echelle, scope="africa",
                      labels={"setting_average": "Prévalence (%)", "date": "Année"},
                      title=f"Prévalence en {y_last} (%)")
    m.update_geos(fitbounds="locations", visible=False, showcountries=True, countrycolor="#FFFFFF",
                  showland=True, landcolor="#E8EDF2", bgcolor="rgba(0,0,0,0)")
    m.update_layout(margin=dict(l=0, r=0, t=50, b=0), coloraxis_colorbar=dict(title="%", thickness=14))
    with a:
        show(m)
    r = last.reset_index().sort_values("setting_average")
    bar = px.bar(r, x="setting_average", y="setting", orientation="h", text="setting_average", color="setting_average",
                 color_continuous_scale=echelle, title="Classement des pays (%)",
                 labels={"setting_average": "Prévalence (%)", "setting": "Pays", "date": "Année"}, hover_data={"date": True})
    bar.update_traces(texttemplate="%{text:.1f}")
    bar.update_layout(coloraxis_showscale=False, xaxis_title=None, yaxis_title=None)
    with b:
        show(bar)

with t2:
    ln = px.line(nat, x="date", y="setting_average", color="setting", markers=True, color_discrete_map=couleur,
                 title="Évolution de la prévalence (%)", labels={"date": "Année", "setting_average": "Prévalence (%)", "setting": "Pays"})
    ln.update_traces(line_width=3, marker_size=6)
    ln.update_layout(hovermode="x unified", xaxis_title=None)
    show(ln, 460)
    var = (val - first.setting_average).sort_values()
    vb = go.Figure(go.Bar(x=var.values, y=var.index, orientation="h", text=[fr(v, True) for v in var],
                          textposition="outside", cliponaxis=False, hovertemplate="%{y} : %{x:+.1f} points<extra></extra>",
                          marker_color=["#1E8E5A" if (v > 0) == fav else "#C0392B" for v in var]))
    vb.update_layout(title=f"Variation entre {y_first} et {y_last} (points de pourcentage)", xaxis_title=None, yaxis_title=None)
    show(vb, 400)

with t3:
    if not sexes:
        st.info("Aucune donnée par sexe pour cette sélection.")
    else:
        y_sx = int(e.date.max())
        st.markdown(f"<div class='duo'><div style='color:{C_F}'>{fr(p[F].mean())} %<small>{F}, moyenne des pays</small></div>"
                    f"<div style='color:{C_H}'>{fr(p[H].mean())} %<small>{H}, moyenne des pays</small></div>"
                    f"<div style='color:{ENCRE}'>{fr(p.ecart.mean(), True)} pt<small>Écart femmes − hommes</small></div></div>",
                    unsafe_allow_html=True)
        q = p.sort_values(F)
        db = go.Figure()
        for c, row in q.iterrows():
            db.add_trace(go.Scatter(x=[row[H], row[F]], y=[c, c], mode="lines", line=dict(color="#C9D3DD", width=6),
                                    hoverinfo="skip", showlegend=False))
        for nom, col, pos in ((H, C_H, "middle left"), (F, C_F, "middle right")):
            db.add_trace(go.Scatter(x=q[nom], y=q.index, mode="markers+text", name=nom, text=[fr(v) for v in q[nom]],
                                    textposition=pos, marker=dict(color=col, size=17, line=dict(color="#fff", width=2)),
                                    hovertemplate="%{y} – " + nom + " : %{x:.1f} %<extra></extra>"))
        db.update_layout(title="Prévalence selon le sexe, dernière année disponible (%)", xaxis_title=None, yaxis_title=None)
        show(db, 470)
        ev = e.groupby(["date", "subgroup"]).estimate.mean().unstack()
        sx = go.Figure()
        sx.add_trace(go.Scatter(x=ev.index, y=ev[H], name=H, line=dict(color=C_H, width=3)))
        sx.add_trace(go.Scatter(x=ev.index, y=ev[F], name=F, line=dict(color=C_F, width=3), fill="tonexty",
                                fillcolor="rgba(194,24,91,.10)"))
        sx.update_layout(title="Évolution selon le sexe, moyenne des pays sélectionnés (%)", hovermode="x unified",
                         xaxis_title=None, yaxis_title=None)
        show(sx, 400)
        with st.expander("Voir le détail par pays"):
            st.dataframe(p[[F, H, "ecart"]].rename(columns={"ecart": "Écart femmes − hommes"}).rename_axis("Pays").round(1))
        st.caption(f"Valeurs de {y_sx}, dernière année disponible. Les écarts sont des différences brutes, sans test statistique.")

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
