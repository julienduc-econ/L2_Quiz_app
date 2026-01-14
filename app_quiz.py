import streamlit as st
import random
import time
import pandas as pd
from datetime import datetime
import finance_formulas as fin
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION PAGE & CSS ---
st.set_page_config(page_title="Quiz IAE Nantes - Finance", layout="centered", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        header {background-color: rgba(0,0,0,0);}
        footer {visibility: hidden;}
        .block-container {padding-top: 2rem; padding-bottom: 5rem;}
        .custom-footer {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: white; color: #555; text-align: center;
            padding: 10px 0px; font-size: 13px; border-top: 1px solid #eaeaea; z-index: 999;
        }
    </style>
    <div class="custom-footer">
        Conçu par <b>Julien Duc</b> - 2026 | 
        <a href="https://julienduc-econ.github.io/L2_MF/" target="_blank">📖 Accéder au cours</a>
    </div>
""", unsafe_allow_html=True)

def enregistrer_et_afficher_leaderboard():
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 1. Préparation de la nouvelle ligne
    duree_min = (time.time() - st.session_state['start_time']) / 60
    
    new_row = pd.DataFrame([{
        "Date": datetime.now().strftime("%d/%m/%Y"),
        "Nom": st.session_state['user_nom'],
        "Prénom": st.session_state['user_prenom'],
        "Pseudo": st.session_state['user_pseudo'],
        "Score": st.session_state['score'],
        "Thème": st.session_state['quiz_category'],
        "Temps": round(duree_min, 1)
    }])

    # 2. Lecture et mise à jour
    try:
        existing_data = conn.read()
        updated_df = pd.concat([existing_data, new_row], ignore_index=True)
        conn.update(data=updated_df)
        st.success("✅ Score enregistré dans la base de données !")
    except Exception as e:
        st.error("Erreur lors de l'enregistrement. Vérifiez les accès du GSheet.")

    # 3. Affichage du Leaderboard Public (Top 10)
    st.markdown("### 🏆 Leaderboard (Top 10)")
    if not updated_df.empty:
        # On ne montre que Pseudo, Score et Temps pour le public
        leaderboard = updated_df[["Pseudo", "Score", "Temps", "Thème"]]
        leaderboard = (leaderboard
            .sort_values(by=["Score", "Temps"], ascending=[False, True])
            .drop_duplicates(subset=["Pseudo"])
            .head(10))
        
        st.table(leaderboard)



NB_QUESTIONS = 5

# --- LOGIQUE DE GÉNÉRATION ---
def generer_question(categorie_choisie):
    types_possibles = []
    cat_map = {
        "Capitalisation": ["capitalisation"],
        "Actualisation": ["actu_simple", "actu_compose"],
        "VAN": ["van_calc"],
        "TAEG": ["taux_equiv", "taux_prop"],
        "Tout": ["capitalisation", "actu_simple", "actu_compose", "van_calc", "taux_equiv", "taux_prop"]
    }
    choix = random.choice(cat_map.get(categorie_choisie, cat_map["Tout"]))
    
    K = random.choice([1000, 5000, 10000, 20000])
    r = round(random.randint(10, 60) * 0.12, 2)
    q = {}

    if choix == "capitalisation":
        type_unite = random.choice(["jours", "mois", "annees"])
        valeur_temps = random.randint(30, 700) if type_unite=="jours" else random.randint(2, 24) if type_unite=="mois" else random.randint(1, 10)
        txt_duree = f"{valeur_temps} {type_unite}"
        sol, mode = fin.capitalisation_auto(K, r, valeur_temps, type_unite)
        
        # Variantes
        v = random.randint(1, 4)
        if v == 1: enonce = f"Valeur acquise de **{fin.fmt(K)}** à **{r}%** pendant **{txt_duree}** ?"
        elif v == 2: enonce = f"Combien recevrez-vous pour un prêt de **{fin.fmt(K)}** à **{r}%** sur **{txt_duree}** ?"
        else: enonce = f"Calculer le capital final : **{fin.fmt(K)}**, taux **{r}%**, durée **{txt_duree}**."
        
        q = {"cat": f"Capitalisation ({mode})", "txt": enonce, "sol": sol, "unit": "€"}
    
    # ... (Ajouter ici les autres catégories : actu_simple, van_calc, etc.) ...
    # Par défaut si non implémenté :
    else:
        q = {"cat": "Général", "txt": "Question de test", "sol": 0, "unit": "€"}
        
    return q

# --- INITIALISATION ---
def init_new_game(categorie, challenge_mode):
    st.session_state['quiz_data'] = [generer_question(categorie) for _ in range(NB_QUESTIONS)]
    st.session_state['current_q_index'] = 0
    st.session_state['score'] = 0
    st.session_state['game_over'] = False
    st.session_state['reponse_validee'] = False
    st.session_state['game_started'] = True
    st.session_state['is_challenge'] = challenge_mode
    st.session_state['start_time'] = time.time()

if 'game_started' not in st.session_state:
    st.session_state['game_started'] = False

# --- UI ---
if not st.session_state['game_started']:
    st.markdown("## 🎓 Quiz de Mathématiques Financières")
    st.info("Ce quiz génère des questions aléatoires. Le mode Challenge masque les réponses et permet d'intégrer le classement.")
    
    col1, col2, col3 = st.columns(3)
    nom = col1.text_input("Nom")
    prenom = col2.text_input("Prénom")
    pseudo = col3.text_input("Pseudo (Leaderboard)")

    choix_cat = st.selectbox("Thème", ["Tout", "Capitalisation", "Actualisation", "VAN", "TAEG"])
    mode_ch = st.checkbox("🏆 Activer le Mode Challenge (Masquer les corrections)")

    if st.button("🚀 Commencer le Quiz", type="primary"):
        if nom and prenom and pseudo:
            st.session_state['user_real_name'] = f"{prenom} {nom}"
            st.session_state['user_pseudo'] = pseudo
            init_new_game(choix_cat, mode_ch)
            st.rerun()
        else:
            st.warning("Veuillez remplir Nom, Prénom et Pseudo.")

else:
    # Écran de jeu
    if not st.session_state['game_over']:
        idx = st.session_state['current_q_index']
        q_data = st.session_state['quiz_data'][idx]
        
        st.markdown(f"### {q_data['cat']} - Question {idx + 1}")
        st.progress(idx / NB_QUESTIONS)
        st.write(q_data['txt'])

        if not st.session_state['reponse_validee']:
            with st.form(key=f"q_{idx}"):
                rep = st.number_input(f"Réponse en {q_data['unit']}", format="%.2f", step=0.01)
                if st.form_submit_button("Valider"):
                    st.session_state['reponse_validee'] = True
                    tol = 0.015 if q_data['unit'] == "%" else 1.0
                    if abs(rep - q_data['sol']) < tol:
                        st.session_state['score'] += 1
                        st.session_state['last_result'] = "correct"
                    else:
                        st.session_state['last_result'] = "wrong"
                    st.session_state['user_reponse'] = rep
                    st.rerun()
        else:
            # Affichage résultat selon mode
            if st.session_state['is_challenge']:
                st.info("🎯 Réponse enregistrée. (Mode Challenge : correction masquée)")
            else:
                sol_f = fin.fmt(q_data['sol'], q_data['unit'])
                if st.session_state['last_result'] == "correct":
                    st.success(f"✅ Bravo ! ({sol_f})")
                else:
                    st.error(f"❌ Faux. La réponse était {sol_f}")

            if st.button("Question suivante ➡️"):
                if idx < NB_QUESTIONS - 1:
                    st.session_state['current_q_index'] += 1
                    st.session_state['reponse_validee'] = False
                    st.rerun()
                else:
                    st.session_state['game_over'] = True
                    st.rerun()
    else:
        # ÉCRAN DE FIN
        st.balloons()
        duree = (time.time() - st.session_state['start_time']) / 60
        st.markdown(f"## Terminé, {st.session_state['user_pseudo']} !")
        st.markdown(f"### Votre score : {st.session_state['score']} / {NB_QUESTIONS}")
        
        # Conditions d'enregistrement
        if st.session_state['is_challenge']:
            if duree >= 1:
                # On enregistre et on montre le classement
                enregistrer_et_afficher_leaderboard()
            else:
                st.warning(f"⚠️ Temps : {int(duree)} min. Minimum 10 min requis pour le Leaderboard.")
        else:
            st.info("💡 Mode Entraînement : le score n'est pas enregistré.")

        if st.button("🔄 Recommencer"):
            st.session_state['game_started'] = False
            st.rerun()



