import math

# --- FORMATAGE ---
def fmt(montant, symbol="€"):
    if symbol == "%":
        # Affiche 2.630 au lieu de 2.6300 si nécessaire, ou reste à 2 décimales
        return f"{montant:.2f} %" 
    return f"{montant:,.2f}".replace(",", " ").replace(".", ",") + " " + symbol

# ==========================================
# 1. CAPITALISATION
# ==========================================
def capitalisation_auto(capital, taux_annuel_pct, duree, type_unite):

    # 1. Conversion de la durée en années
    duree_annees = 0.0
    if type_unite == "jours":
        duree_annees = duree / 360
    elif type_unite == "mois":
        duree_annees = duree / 12
    elif type_unite == "annees":
        duree_annees = float(duree)
        
    # 2. Application de la règle
    if duree_annees > 1.0:
        # Composés
        montant = capital * ((1 + taux_annuel_pct/100) ** duree_annees)
    else:
        # Simples
        montant = capital * (1 + (taux_annuel_pct/100) * duree_annees)
        
    return montant

def action(capital, taux_annuel_pct):
    for i in range(len(taux_annuel_pct)):
        capital=capital*(1+taux_annuel_pct[i]/100)
    return capital

def rdt_moyen_annuel(rdts):
    rdt_cum=1
    for i in range(len(rdts)):
        rdt_cum=rdt_cum*(1+rdts[i]/100)
    return (rdt_cum**(1/len(rdts))-1)*100

def find_r(K,VF,duree,type_unite):
    # 1. Conversion de la durée en années
    duree_annees = 0.0
    if type_unite == "jours":
        duree_annees = duree / 360
    elif type_unite == "mois":
        duree_annees = duree / 12
    elif type_unite == "annees":
        duree_annees = float(duree)

    if duree_annees > 1.0:
        # Composés
        r = (VF/K)**(1/duree_annees) - 1
        mode = "Composés (> 1 an)"
    else:
        # Simples
        r = (VF/K-1)*(1/duree_annees)
        mode = "Simples (≤ 1 an)"
    return r*100

# ==========================================
# 2. EMPRUNTS
# ==========================================

def ann_csts(K, r, duree, differe, unite):
    tx=r
    if unite == "mois":
        tx=r/12
    m = K*((1+tx)**differe)*tx/(1-(1+tx)**(-duree))
    c= duree*m-K
    return m, c



# ==========================================
#               EXERCICES GENERAUX 
# ==========================================

# HERITAGE
def heritage(capital, r, inf, ages, age_maj):
    nb_enf=len(ages)
    denom=0
    heritage=[]
    tx=(1+r)/(1+inf)
    for j in range(nb_enf):
        denom=denom+tx**(-max(age_maj-ages[j],0))
    for j in range(nb_enf):
        part=capital*tx**(-max(age_maj-ages[j],0))/denom
        heritage.append(part)
    return heritage