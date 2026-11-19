"""Périmètre (maladies chroniques) et traductions françaises des libellés du fichier source OMS HEAT.

Pour ajouter un indicateur : ajouter une ligne dans INDICATEURS (code de l'indicateur -> sous-thème, libellé).
"""
import re

SOUS_THEMES = ["Hypertension", "Diabète", "Cholestérol", "Mortalité par maladies chroniques", "Activité physique"]
S, B = " – standardisation selon l'âge", " – valeurs brutes"
INDICATEURS = {}


def _add(sous_theme, base, **variantes):
    for code, suffixe in variantes.items():
        INDICATEURS[code] = (sous_theme, base + suffixe)


H, D, C, M, P = SOUS_THEMES
_add(H, "Prévalence de l'hypertension (PAS ≥ 140 ou PAD ≥ 90), adultes de 30 à 79 ans (%)", BP_03=B, BP_04=S)
_add(H, "Prévalence de l'hypertension, adultes de 30 à 79 ans (%)", NCD_HYP_PREVALENCE_A=S, NCD_HYP_PREVALENCE_C=B)
_add(H, "Couverture du diagnostic chez les adultes hypertendus de 30 à 79 ans (%)", NCD_HYP_DIAGNOSIS_A=S, NCD_HYP_DIAGNOSIS_C=B)
_add(H, "Couverture du traitement chez les adultes hypertendus de 30 à 79 ans (%)", NCD_HYP_TREATMENT_A=S, NCD_HYP_TREATMENT_C=B)
_add(H, "Couverture effective du traitement (tension contrôlée) chez les adultes hypertendus de 30 à 79 ans (%)",
     NCD_HYP_CONTROL_A=S, NCD_HYP_CONTROL_C=B)
_add(D, "Prévalence du diabète, 18 ans et plus (%)", NCD_DIABETES_PREVALENCE_AGESTD_18=S, NCD_DIABETES_PREVALENCE_CRUDE_18=B)
_add(D, "Prévalence du diabète, 30 ans et plus (%)", NCD_DIABETES_PREVALENCE_AGESTD_30=S, NCD_DIABETES_PREVALENCE_CRUDE_30=B)
_add(D, "Couverture du traitement du diabète, 30 ans et plus (%)", NCD_DIABETES_TREATMENT_AGESTD=S, NCD_DIABETES_TREATMENT_CRUDE=B)
_add(C, "Cholestérol HDL (lipoprotéines de haute densité), moyenne", NCD_CHOL_MEANHDL_A=S, NCD_CHOL_MEANHDL_C=B)
_add(C, "Cholestérol non-HDL, moyenne", NCD_CHOL_MEANNONHDL_A=S, NCD_CHOL_MEANNONHDL_C=B)
_add(C, "Cholestérol total, moyenne", NCD_CHOL_MEANTOTALCHOL_A=S, NCD_CHOL_MEANTOTALCHOL_C=B)
INDICATEURS.update({
    "NCDMORT3070": (M, "Probabilité de décès entre 30 et 70 ans par maladie cardiovasculaire, cancer, diabète "
                       "ou maladie respiratoire chronique (%)"),
    "NCD_UNDER70": (M, "Décès prématurés par maladies non transmissibles (MNT), en proportion de tous les décès par MNT (%)"),
    "WHS2_131": (M, "Taux de mortalité par maladies non transmissibles (MNT), pour 100 000 habitants" + S),
    "SA_0000001807": (M, "Taux de mortalité par cancer, 15 ans et plus, pour 100 000 habitants" + S),
})
_add(P, "Activité physique insuffisante chez les adultes de 18 ans et plus (%)", NCD_PAA=S, NCD_PAC=B)
_add(P, "Activité physique insuffisante chez les adolescents scolarisés de 11 à 17 ans (%)", NCD_PAC_ADO=B)

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
