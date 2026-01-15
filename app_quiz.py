import streamlit as st
import random
import time
import pandas as pd
from datetime import datetime
import finance_formulas as fin
from supabase import create_client, Client

# --- 1. CONFIGURATION PAGE ---
st.set_page_config(page_title="Quiz IAE Nantes - Finance", layout="centered", initial_sidebar_state="collapsed")

# --- 2. CONNEXION SUPABASE ---
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = get_supabase()

# --- 3. INITIALISATION ---
# On s'assure que TOUTES les variables existent dès le début
if 'game_started' not in st.session_state: st.session_state['game_started'] = False
if 'game_over' not in st.session_state: st.session_state['game_over'] = False
if 'score_saved' not in st.session_state: st.session_state['score_saved'] = False
if 'user_pseudo' not in st.session_state: st.session_state['user_pseudo'] = "Invité"
if 'score' not in st.session_state: st.session_state['score'] = 0
if 'current_q_index' not in st.session_state: st.session_state['current_q_index'] = 0

# --- CSS ---
st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 5rem; }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 1px solid #444; padding-bottom: 0px; }
        .stTabs [data-baseweb="tab"] {
            height: auto; background-color: var(--secondary-background-color) !important;
            color: var(--text-color) !important; border: 1px solid transparent;
            border-radius: 6px 6px 0px 0px; padding: 12px 25px; font-size: 18px; font-weight: 600; opacity: 0.7;
        }
        .stTabs [aria-selected="true"] {
            background-color: var(--background-color) !important; color: var(--text-color) !important;
            border-top: 3px solid #ff4b4b !important; border-bottom: 1px solid var(--background-color) !important; opacity: 1;
        }
        div.stButton > button {
            background-color: #262730 !important; color: white !important; border: 1px solid #444;
            border-radius: 6px; font-size: 16px; padding: 10px 24px;
        }
        div.stButton > button:hover { border-color: #ff4b4b; color: #ff4b4b !important; }
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;} 
        .custom-footer {
            position: fixed; left: 0; bottom: 0; width: 100%;
            background-color: var(--secondary-background-color); color: var(--text-color); 
            text-align: center; padding: 10px 0px; font-size: 13px; border-top: 1px solid #444; z-index: 999;
        }
    </style>
    <div class="custom-footer">
        Conçu par <b>Julien Duc</b> - 2026 | 
        <a href="https://julienduc-econ.github.io/L2_MF/" target="_blank" style="text-decoration: none; color: #ff4b4b;">📖 Accéder au cours</a>
    </div>
""", unsafe_allow_html=True)

# --- 4. FONCTIONS ---

def enregistrer_score():
    try:
        duree_min = (time.time() - st.session_state.get('start_time', time.time())) / 60
        data = {
            "pseudo": st.session_state['user_pseudo'],
            "score": st.session_state['score'],
            "theme": st.session_state['quiz_category'],
            "temps": round(duree_min, 1)
        }
        supabase.table("scores").insert(data).execute()
        st.session_state['score_saved'] = True
    except Exception as e:
        st.error(f"Erreur de sauvegarde : {e}")

NB_QUESTIONS = 2

def generer_question(categorie_choisie):
    if categorie_choisie == "Tout le Programme":
        cat_active = random.choice(["Capitalisation et Actualisation", "Emprunts"])
    else:
        cat_active = categorie_choisie

    K = random.choice([500, 1000, 5000, 10000, 20000, 50000])
    r = round(random.randint(10, 60) * 0.12, 2)
    type_unite = random.choice(["jours", "mois", "annees"])
    valeur_temps = random.randint(30, 700) if type_unite=="jours" else random.randint(2, 24) if type_unite=="mois" else random.randint(1, 10)
    txt_duree = f"{valeur_temps} {type_unite}"

    if cat_active == "Capitalisation et Actualisation":
        variante_txt = random.randint(1, 7)
        if variante_txt in [1, 2, 3]:
            enonce = f"Valeur acquise de **{fin.fmt(K)}** à **{r}%** pendant **{txt_duree}** ?"
            sol = round(fin.capitalisation_auto(K, r, valeur_temps, type_unite), 2)
            unite_rep = "€"
        elif variante_txt == 5:
            prix = random.randint(2,30)*10
            rendements = [random.randint(-5, 10) for _ in range(3)]
            enonce = f"Action à **{fin.fmt(prix)}**. Rendements : {rendements}. Valeur finale ?"
            sol = round(fin.action(prix, rendements), 2)
            unite_rep = "€"
        else:
            VF = K * 1.5
            enonce = f"Taux d'intérêt annuel pour passer de **{fin.fmt(K)}** à **{fin.fmt(VF)}** en **{txt_duree}** ?"
            sol = round(fin.find_r(K, VF, valeur_temps, type_unite), 2)
            unite_rep = "%"
        return {"cat": cat_active, "txt": enonce, "sol": sol, "unit": unite_rep}
    
    elif cat_active == "Emprunts":
        variante_txt = random.randint(1, 7)
        if variante_txt in [1, 2, 3]:
            enonce = f"Le **{fin.fmt(prix)}**. Rendements : {rendements}. Valeur finale ?"


        return {"cat": "Emprunts", "txt": "Question Emprunts à définir", "sol": 0, "unit": "€"}

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
    st.session_state['score_saved'] = False

# ==============================================================================
# STRUCTURE
# ==============================================================================

tab_jeu, tab_leaderboard = st.tabs(["📖 S'exercer", "🏆 Classement Général"])

with tab_jeu:
    st.markdown("<br>", unsafe_allow_html=True) 
    
    # --- ETAPE 1 : ACCUEIL ---
    if not st.session_state['game_started']:
        st.markdown("## 🎓 Quiz de Mathématiques Financières")
        st.markdown(
    """
    <p style="font-size:20px;">
        Ce site est dédié au cours de <a href="https://julienduc-econ.github.io/L2_MF/" target="_blank">Mathématiques Financières</a> dispensé en L2 à l'IAE de Nantes. 
        Les questions et les valeurs numériques sont générés aléatoirement. 
        Chaque thème dispose d'environ 20 types de questions. 
        Vous pouvez effectuer autant de quizs que vous souhaitez.
    </p>
    """, 
    unsafe_allow_html=True
)


        choix_cat = st.selectbox("Thème", ["Tout le Programme", "Capitalisation et Actualisation", "Emprunts"])
        mode_ch = st.checkbox("🏆 Activer le Mode Challenge (Enregistre votre score)", value=False)
        st.info("Le mode **Challenge** enregistre votre score pour le classement général.")
        pseudo, code_prive = None, None
        if mode_ch:
            #st.info("⚠️ Identifiants requis pour le classement.")
            col1, col2 = st.columns(2)
            pseudo = col1.text_input("Pseudo (public)")
            code_prive = col2.text_input("PIN (secret)", type="password")

            user_exists = False
            nom, prenom = "", ""
            if pseudo:
                res = supabase.table("profiles").select("*").eq("pseudo", pseudo).execute()
                user_exists = len(res.data) > 0
                if not user_exists:
                    st.warning("✨ Nouveau profil ! ⚠️ Conservez votre **Pseudo** et **PIN** afin de garder votre progression.")
                    c1, c2 = st.columns(2)
                    nom = c1.text_input("Nom de famille")
                    prenom = c2.text_input("Prénom")


        if st.button("🚀 Commencer"):
            if mode_ch:
                if not pseudo or not code_prive:
                    st.error("Pseudo et Code requis.")
                else:
                    if user_exists:
                        res = supabase.table("profiles").select("*").eq("pseudo", pseudo).execute()
                        if res.data[0]['code'] == code_prive:
                            st.session_state['user_pseudo'] = pseudo
                            init_new_game(choix_cat, mode_ch)
                            st.rerun()
                        else: st.error("Code incorrect.")
                    elif nom and prenom:
                        supabase.table("profiles").insert({"pseudo": pseudo, "code": code_prive, "nom": nom, "prenom": prenom}).execute()
                        st.session_state['user_pseudo'] = pseudo
                        init_new_game(choix_cat, mode_ch)
                        st.rerun()
            else:
                st.session_state['user_pseudo'] = "Invité"
                init_new_game(choix_cat, mode_ch)
                st.rerun()

    # --- ETAPE 2 : LE QUIZ ---
    elif not st.session_state['game_over']:
        idx = st.session_state['current_q_index']
        q = st.session_state['quiz_data'][idx]
        
        st.markdown(f"### Question {idx + 1} / {NB_QUESTIONS}")
        st.progress(idx / NB_QUESTIONS)
        st.write(q['txt'])

        if not st.session_state['reponse_validee']:
            with st.form(key=f"q_{idx}"):
                rep = st.number_input(f"Réponse en {q['unit']}", format="%.2f")
                if st.form_submit_button("Valider"):
                    st.session_state['reponse_validee'] = True
                    if abs(rep - q['sol']) < 0.01:
                        st.session_state['score'] += 1
                        st.session_state['last_res'] = "✅ Correct !"
                    else:
                        st.session_state['last_res'] = f"❌ Faux (La réponse était {q['sol']:.2f} {q['unit']})"
                    st.rerun()
        else:
            st.info(st.session_state['last_res'])
            if st.button("Question suivante ➡️"):
                if idx < NB_QUESTIONS - 1:
                    st.session_state['current_q_index'] += 1
                    st.session_state['reponse_validee'] = False
                else:
                    st.session_state['game_over'] = True
                st.rerun()

    # --- ETAPE 3 : RESULTATS ---
    else:
        st.balloons()
        st.markdown(f"## Terminé, {st.session_state.get('user_pseudo', 'Invité')} !")
        st.markdown(f"### Votre score : {st.session_state['score']} / {NB_QUESTIONS}")
        
        if st.session_state['is_challenge'] and not st.session_state.get('score_saved', False):
            with st.spinner("Enregistrement..."):
                enregistrer_score()
            st.success("✅ Score enregistré !")
        
        if st.button("🔄 Recommencer"):
            st.session_state['game_started'] = False
            st.rerun()

with tab_leaderboard:
    st.markdown("## 🏆 Classement par thème")
    cat_filter = st.selectbox("Thème :", ["Tout le Programme", "Capitalisation et Actualisation", "Emprunts"], key="lb")
    
    try:
        res = supabase.table("scores").select("pseudo, score, theme, temps").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            df_f = df[df["theme"] == cat_filter] if cat_filter != "Tout le Programme" else df
            if not df_f.empty:
                stats = df_f.groupby("pseudo").agg({'score': 'mean', 'pseudo': 'count', 'temps': 'min'}).rename(columns={'score': 'Moyenne', 'pseudo': 'Parties', 'temps': 'Record'}).reset_index()
                st.dataframe(stats.sort_values("Moyenne", ascending=False), width='stretch')
    except Exception as e:
        st.error(f"Erreur classement : {e}")