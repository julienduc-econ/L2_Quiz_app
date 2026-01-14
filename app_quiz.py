import streamlit as st
import random
import time
import pandas as pd
from datetime import datetime
import finance_formulas as fin
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION PAGE & CSS ---
st.set_page_config(page_title="Quiz IAE Nantes - Finance", layout="centered", initial_sidebar_state="collapsed")

# --- NOUVEAU CSS CORRIGÉ POUR LES ONGLETS ---
st.markdown("""
    <style>
        /* Conteneur de la liste des onglets */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px; /* Espace entre les onglets */
            border-bottom: 1px solid #e0e0e0; /* Ligne de démarcation en bas */
            padding-bottom: 0px;
        }

        /* Style par défaut des onglets (inactifs) */
        .stTabs [data-baseweb="tab"] {
            height: auto; /* Laisse la hauteur s'adapter au texte */
            white-space: nowrap; /* Empêche le texte de passer à la ligne */
            background-color: #f8f9fa; /* Gris très clair pour se distinguer du fond */
            border-radius: 8px 8px 0px 0px; /* Arrondi en haut */
            padding: 12px 20px; /* Espace intérieur confortable */
            color: #666; /* Texte un peu moins noir */
            border: 1px solid transparent; /* Bordure invisible pour l'alignement */
            font-weight: 500;
        }

        /* Style de l'onglet SÉLECTIONNÉ (Actif) */
        .stTabs [aria-selected="true"] {
            background-color: #ffffff !important; /* Fond blanc pur pour ressortir */
            color: #000 !important; /* Texte noir foncé */
            /* Bordure rouge en haut, grise sur les côtés, et on masque le bas pour lier au contenu */
            border-top: 3px solid #ff4b4b;
            border-left: 1px solid #e0e0e0;
            border-right: 1px solid #e0e0e0;
            border-bottom: 1px solid white; /* Masque la ligne du conteneur */
        }

        /* Autres styles */
        footer {visibility: hidden;}
        .block-container {padding-top: 2rem;}
    </style>
""", unsafe_allow_html=True)


# --- FONCTION DE SAUVEGARDE ---
def enregistrer_score():
    try:
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        conn = st.connection("gsheets", type=GSheetsConnection)
        
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

        try:
            existing_data = conn.read(spreadsheet=url, ttl=0)
        except:
            existing_data = pd.DataFrame()

        if existing_data is None or existing_data.empty:
            updated_df = new_row
        else:
            existing_data = existing_data.dropna(how='all')
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
        
        conn.update(spreadsheet=url, data=updated_df)
        st.cache_data.clear()
        st.success(f"🏆 Bravo {st.session_state.get('user_pseudo')}, ton score est enregistré !")
        return updated_df

    except Exception as e:
        st.error(f"Erreur de sauvegarde : {e}")
        return pd.DataFrame()

# --- CONSTANTES & LOGIQUE JEU ---
NB_QUESTIONS = 2

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
        return {"cat": "Général", "txt": "Question de test (Logique à compléter)", "sol": 0, "unit": "€"}

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

# ==============================================================================
# STRUCTURE PRINCIPALE AVEC ONGLETS
# ==============================================================================

# CHANGEMENT ICÔNE ICI : 📖 au lieu de 🎮
tab_jeu, tab_leaderboard = st.tabs(["📖 S'exercer", "🏆 Classement Général"])

# ------------------------------------------------------------------------------
# ONGLET 1 : LE JEU
# ------------------------------------------------------------------------------
with tab_jeu:
    if not st.session_state['game_started']:
        st.markdown("## 🎓 Quiz de Mathématiques Financières")
        st.info("Le mode Challenge enregistre votre score pour le classement général.")
        
        col1, col2, col3 = st.columns(3)
        nom = col1.text_input("Nom")
        prenom = col2.text_input("Prénom")
        pseudo = col3.text_input("Pseudo (sera visible)")

        choix_cat = st.selectbox("Thème", ["Tout", "Capitalisation", "Actualisation", "VAN", "TAEG"])
        mode_ch = st.checkbox("🏆 Activer le Mode Challenge", value=True)

        if st.button("🚀 Commencer", type="primary"):
            if nom and prenom and pseudo:
                st.session_state['user_nom'] = nom
                st.session_state['user_prenom'] = prenom
                st.session_state['user_pseudo'] = pseudo
                init_new_game(choix_cat, mode_ch)
                st.rerun()
            else:
                st.warning("Veuillez remplir Nom, Prénom et Pseudo.")
    else:
        # PENDANT LE JEU
        if not st.session_state['game_over']:
            idx = st.session_state['current_q_index']
            q_data = st.session_state['quiz_data'][idx]
            
            st.markdown(f"### Question {idx + 1} / {NB_QUESTIONS}")
            st.progress((idx) / NB_QUESTIONS)
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
                    st.info("🔒 Réponse enregistrée (Mode Challenge)")
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
            # FIN DU JEU
            st.balloons()
            duree = (time.time() - st.session_state['start_time']) / 60
            st.markdown(f"## Terminé, {st.session_state['user_pseudo']} !")
            st.markdown(f"### Votre score : {st.session_state['score']} / {NB_QUESTIONS}")
            
            if st.session_state['is_challenge']:
                if duree >= 0: # REMETTRE A 0.5 ou 1 en production
                    enregistrer_score()
                    st.info("👉 Allez voir l'onglet 'Classement Général' pour voir votre moyenne !")
                else:
                    st.warning("Temps trop court pour être validé.")
            
            if st.button("🔄 Recommencer"):
                st.session_state['game_started'] = False
                st.rerun()

# ------------------------------------------------------------------------------
# ONGLET 2 : LE CLASSEMENT GÉNÉRAL (AVG)
# ------------------------------------------------------------------------------
with tab_leaderboard:
    st.markdown("## 🏆 Classement par Moyenne")
    st.write("Ce classement calcule la moyenne de vos scores pour la catégorie sélectionnée.")
    
    # 1. Filtre Catégorie
    cat_filter = st.selectbox("Filtrer par catégorie :", ["Tout", "Capitalisation", "Actualisation", "VAN", "TAEG"])
    
    if st.button("🔄 Actualiser le classement"):
        st.cache_data.clear()
        st.rerun()

    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        df = conn.read(spreadsheet=url, ttl=0)
        
        if not df.empty:
            if cat_filter != "Tout":
                df_filtered = df[df["Thème"] == cat_filter]
            else:
                df_filtered = df

            if not df_filtered.empty:
                # Calcul moyenne
                stats = df_filtered.groupby("Pseudo").agg(
                    Moyenne_Score=('Score', 'mean'),
                    Nb_Quiz=('Score', 'count'),
                    Meilleur_Temps=('Temps', 'min')
                ).reset_index()

                stats = stats.sort_values(by=["Moyenne_Score", "Nb_Quiz"], ascending=[False, False])
                stats["Moyenne_Score"] = stats["Moyenne_Score"].round(2)
                stats.index = range(1, len(stats) + 1)
                
                st.dataframe(
                    stats, 
                    column_config={
                        "Moyenne_Score": st.column_config.ProgressColumn(
                            "Note Moyenne", 
                            help="Moyenne des scores obtenus",
                            format="%.2f",
                            min_value=0,
                            max_value=NB_QUESTIONS
                        ),
                        "Nb_Quiz": st.column_config.NumberColumn("Parties Jouées"),
                        "Meilleur_Temps": st.column_config.NumberColumn("Record (min)", format="%.1f")
                    },
                    use_container_width=True
                )
            else:
                st.info(f"Aucune donnée trouvée pour la catégorie '{cat_filter}'.")
        else:
            st.warning("Le tableau des scores est vide pour l'instant.")

    except Exception as e:
        st.error("Impossible de charger le classement pour le moment.")
