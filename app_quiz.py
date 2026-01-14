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
    try:
        # --- 1. CONFIGURATION ROBUSTE ---
        # On laisse Streamlit gérer la connexion de base
        conn = st.connection("gsheets", type=GSheetsConnection)

        # On récupère l'URL manuellement (car le nom 'spreadsheet' pose parfois problème)
        try:
            url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        except:
            st.error("L'URL du Google Sheet est introuvable dans les secrets.")
            return

        # SÉCURITÉ : Si jamais la clé a des \n (format texte), on les convertit
        # Si la clé a déjà des vrais sauts de ligne (format triple guillemets), ceci ne change rien.
        try:
            raw_key = st.secrets["connections"]["gsheets"]["private_key"]
            if "\\n" in raw_key:
                st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")
        except:
            pass # Si ça échoue, on laisse la connexion essayer telle quelle

        # --- 2. PRÉPARATION DES DONNÉES ---
        duree_min = (time.time() - st.session_state.get('start_time', time.time())) / 60
        
        new_row = pd.DataFrame([{
            "Date": datetime.now().strftime("%d/%m/%Y"),
            "Nom": st.session_state.get('user_nom', 'Inconnu'),
            "Prénom": st.session_state.get('user_prenom', 'Inconnu'),
            "Pseudo": st.session_state.get('user_pseudo', 'Anonyme'),
            "Score": st.session_state.get('score', 0),
            "Thème": st.session_state.get('quiz_category', 'Tout'),
            "Temps": round(duree_min, 1)
        }])

        # --- 3. LECTURE & ECRITURE ---
        try:
            # On force l'usage de l'URL spécifique
            existing_data = conn.read(spreadsheet=url)
        except Exception:
            existing_data = pd.DataFrame()

        if existing_data is None or existing_data.empty:
            updated_df = new_row
        else:
            existing_data = existing_data.dropna(how='all')
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
        
        # Mise à jour dans le Cloud
        conn.update(spreadsheet=url, data=updated_df)
        st.success(f"🏆 Bravo {st.session_state.get('user_pseudo')}, score enregistré !")

        # --- 4. AFFICHAGE DU TOP 10 ---
        st.markdown("### 🥇 Classement (Top 10)")
        leaderboard = updated_df[["Pseudo", "Score", "Temps", "Thème"]].copy()
        leaderboard = (leaderboard
            .sort_values(by=["Score", "Temps"], ascending=[False, True])
            .drop_duplicates(subset=["Pseudo"])
            .head(10))
        leaderboard.index = range(1, len(leaderboard) + 1)
        st.table(leaderboard)

    except Exception as e:
        st.error(f"Erreur technique : {e}")
        
# --- CONSTANTES ---
NB_QUESTIONS = 2

# --- LOGIQUE DE GÉNÉRATION ---
def generer_question(categorie_choisie):
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
    
    if choix == "capitalisation":
        type_unite = random.choice(["jours", "mois", "annees"])
        valeur_temps = random.randint(30, 700) if type_unite=="jours" else random.randint(2, 24) if type_unite=="mois" else random.randint(1, 10)
        txt_duree = f"{valeur_temps} {type_unite}"
        sol, mode = fin.capitalisation_auto(K, r, valeur_temps, type_unite)
        enonce = f"Valeur acquise de **{fin.fmt(K)}** à **{r}%** pendant **{txt_duree}** ?"
        return {"cat": f"Capitalisation ({mode})", "txt": enonce, "sol": sol, "unit": "€"}
    else:
        return {"cat": "Général", "txt": "Question de test", "sol": 0, "unit": "€"}

def init_new_game(categorie, challenge_mode):
    st.session_state['quiz_category'] = categorie
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

# --- UI PRINCIPALE ---
if not st.session_state['game_started']:
    st.markdown("## 🎓 Quiz de Mathématiques Financières")
    st.info("Le mode Challenge masque les réponses et permet d'intégrer le classement.")
    
    col1, col2, col3 = st.columns(3)
    nom = col1.text_input("Nom")
    prenom = col2.text_input("Prénom")
    pseudo = col3.text_input("Pseudo (Leaderboard)")

    choix_cat = st.selectbox("Thème", ["Tout", "Capitalisation", "Actualisation", "VAN", "TAEG"])
    mode_ch = st.checkbox("🏆 Activer le Mode Challenge")

    if st.button("🚀 Commencer le Quiz", type="primary"):
        if nom and prenom and pseudo:
            st.session_state['user_nom'] = nom
            st.session_state['user_prenom'] = prenom
            st.session_state['user_pseudo'] = pseudo
            init_new_game(choix_cat, mode_ch)
            st.rerun()
        else:
            st.warning("Veuillez remplir Nom, Prénom et Pseudo.")
else:
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
            if st.session_state['is_challenge']:
                st.info("🎯 Réponse enregistrée.")
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
        st.balloons()
        duree = (time.time() - st.session_state['start_time']) / 60
        st.markdown(f"## Terminé, {st.session_state['user_pseudo']} !")
        st.markdown(f"### Votre score : {st.session_state['score']} / {NB_QUESTIONS}")
        
        if st.session_state['is_challenge']:
            if duree >= 0: # Seuil réglé à 1 min pour vos tests, remettez 10 après
                enregistrer_et_afficher_leaderboard()
            else:
                st.warning(f"⚠️ Temps insuffisant ({int(duree)} min) pour le classement.")
        else:
            st.info("💡 Mode Entraînement : score non enregistré.")

        if st.button("🔄 Recommencer"):
            st.session_state['game_started'] = False
            st.rerun()






