# Tableau de bord – maladies chroniques (Afrique de l'Ouest)

Tableau de bord interactif (Streamlit + Plotly) consacré aux **maladies chroniques** et à leurs **inégalités**
(sexe, milieu de résidence, niveau économique, âge…).

## Périmètre

Source : `data/raw/data_nettoye.xlsx` (format OMS HEAT), 8 pays : Bénin, Burkina Faso, Côte d'Ivoire, Ghana, Mali,
Niger, Sénégal, Togo. Seuls **29 indicateurs** de maladies chroniques sont chargés (les autres indicateurs du
fichier sont ignorés), répartis en cinq sous-thèmes :

| Sous-thème | Contenu |
|---|---|
| Hypertension | prévalence, diagnostic, traitement, contrôle |
| Diabète | prévalence (18+ / 30+ ans), couverture du traitement |
| Cholestérol | cholestérol total, HDL, non-HDL |
| Mortalité par maladies chroniques | mortalité MNT, décès prématurés, probabilité de décès 30–70 ans, mortalité par cancer |
| Activité physique | activité insuffisante (adultes, adolescents) |

Le périmètre et les libellés français sont définis dans `traductions.py` (dictionnaire `INDICATEURS`) : ajoutez-y une
ligne pour étendre le périmètre.

## Fonctionnalités

- Filtres : sous-thème, indicateur, pays, période
- Indicateurs clés par pays (dernière valeur et évolution, couleur selon le caractère favorable de l'indicateur)
- Carte, classement, courbes de tendance et variation sur la période
- Inégalités par dimension : intervalles de confiance, écart absolu et rapport max/min dans le temps
- Export CSV de la sélection (format français : séparateur « ; », virgule décimale)
- Interface, indicateurs, pays, dimensions et sous-groupes entièrement en français

## Lancer en local

```bash
python -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Utiliser vos propres données

Après conversion, ajoutez la traduction des nouveaux indicateurs dans `traductions.py`.

Colonnes obligatoires (format OMS HEAT) : `setting, date, indicator_abbr, indicator_name, dimension, subgroup,
estimate, ci_lb, ci_ub, setting_average, iso3, favourable_indicator, subgroup_order`.

```bash
python scripts/prepare_data.py chemin/vers/votre_fichier.xlsx   # génère data/data_nettoye.csv.gz
```

## Déploiement

[Streamlit Community Cloud](https://share.streamlit.io) : connectez ce dépôt GitHub, fichier principal `app.py`.

## Structure

```
app.py                  application
traductions.py          périmètre et libellés français
data/                   données (CSV compressé) + data/raw (Excel d'origine)
scripts/prepare_data.py conversion Excel -> CSV.gz
tests/                  tests de fumée (pytest)
.github/workflows/      intégration continue
```

## Licence

Code : MIT. Les données restent soumises aux conditions d'utilisation de leur source (OMS).
