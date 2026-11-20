"""Indicateur retenu et traductions françaises des libellés du fichier source OMS HEAT."""
import re

CODE = "NCD_HYP_PREVALENCE_A"  # code de l'indicateur dans le fichier source (version standardisée selon l'âge)
LIBELLE = "Prévalence de l'hypertension, adultes de 30 à 79 ans (%)"

PAYS = {"Benin": "Bénin", "Senegal": "Sénégal"}  # les autres noms sont identiques en français
DIMENSIONS = {"Sex": "Sexe", "Place of residence": "Milieu de résidence",
              "Economic status": "Statut économique", "Household composition": "Composition du ménage"}
SOUS_GROUPES = {"Female": "Femmes", "Male": "Hommes", "Urban": "Urbain",
                "Quintile 1 (poorest)": "Quintile 1 (le plus pauvre)", "Quintile 5 (richest)": "Quintile 5 (le plus riche)"}


def dimension_fr(x: str) -> str:
    m = re.fullmatch(r"Age \((\d+) groups\) \((.+)\)", x)
    return f"Âge ({m[1]} groupes) ({m[2]} ans)" if m else DIMENSIONS.get(x, x)


def sous_groupe_fr(x: str) -> str:
    x = SOUS_GROUPES.get(x, x)
    x = re.sub(r"(\d+)\+ years", r"\1 ans et plus", x)
    return re.sub(r"(\d+)-(\d+) years", r"\1-\2 ans", x)


# Locutions pour les phrases de synthèse (« au Niger », « en Côte d'Ivoire »)
LOCUTIONS = {"Bénin": "au Bénin", "Burkina Faso": "au Burkina Faso", "Côte d'Ivoire": "en Côte d'Ivoire",
             "Ghana": "au Ghana", "Mali": "au Mali", "Niger": "au Niger", "Sénégal": "au Sénégal", "Togo": "au Togo"}
