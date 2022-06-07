import streamlit as st
import os, joblib
import pandas as pd
import numpy as np
from functions import get_featuring_graph_chart
from random import seed

st.set_page_config(
     page_title = "Roland Gamos",
     page_icon = "🎾"
     )

# --- Initialising SessionState ---

if "play_button" not in st.session_state:
    st.session_state.play_button = False

if "level" not in st.session_state:
    st.session_state.level = None

if "bot_artist_id_list" not in st.session_state:
     st.session_state.bot_artist_id_list = list()

if "player_artist_id_list" not in st.session_state:
    st.session_state.player_artist_id_list = list()

if "game_status" not in st.session_state:
    st.session_state.game_status = None

if "game_message" not in st.session_state:
    st.session_state.game_message = None

if "contributor_status" not in st.session_state:
    st.session_state.contributor_status = False

# --- Variables ---

INPUT_PATH = "data"
DEFAULT_VALUE = "Entre un artiste..."
START_TIME = 1543

# --- Importing Data ---

G = joblib.load(os.path.join(INPUT_PATH, "graph.p"))
artist_dict = joblib.load(os.path.join(INPUT_PATH, "artist_names.p"))

# --- Main ---

artist_dict_r = {artist_name:artist_id for artist_id, artist_name in artist_dict.items()}
artist_list = sorted([artist_name for artist_id, artist_name in artist_dict.items()])
seed(42)

# --- Introduction ---

st.markdown("""
# Le Rolland Gamos

Bienvenue sur l'application du jeu du Roland Gamos inspiré de l'émission Rap Jeu produite par Red Bull Binks.

## 🎲 Règles du jeu

Le but étant de partir d'un.e artiste du rap game et de trouver à tout de rôle un autre artiste ayant fait un featuring avec le précédent cité. 
Mais une démonstration vaut mieux que mille explications, voici une des joutes les plus mémorables de l'émission :
""")
st.video("https://www.youtube.com/watch?v=ihGqtHBIOEQ", start_time=START_TIME)

# --- The Game ---
with st.container():

    st.markdown("""## 💊 Le jeu
***""")
    
    col1, col2 = st.columns(2)
    path = list()

    if len(st.session_state.bot_artist_id_list) > 0:
        col1.markdown("<h1 style='text-align: center;'>🤖</h1>", unsafe_allow_html=True)
        col2.markdown("<h1 style='text-align: center;'>👤</h1>", unsafe_allow_html=True)

    for i, (bot_artist_id, player_artist_id) in enumerate(zip(st.session_state.bot_artist_id_list, st.session_state.player_artist_id_list)):
        
        path.extend([bot_artist_id, player_artist_id])

        if i < len(st.session_state.player_artist_id_list) - 1 or st.session_state.game_status is None:
            col1.info(artist_dict[bot_artist_id])
            col2.success(artist_dict[player_artist_id])
        
    if not st.session_state.play_button:

        level = st.radio("Sélectionne le niveau de difficulté :", ["Rookie", "Digger", "Puriste"], horizontal=True)
        if level == "Rookie":
            level = 6
        elif level == "Digger":
            level = 4
        else:
            level = 2
        
        play = st.button("Play")

        if play:
            st.session_state.play_button = True
            st.session_state.level = level
            st.session_state.round = 0
            st.experimental_rerun()

    else:
        replay = st.button("Replay")

        if replay:
            for key in st.session_state.keys():
                del st.session_state[key]
            st.experimental_rerun()
       
        else:

            if len(st.session_state.bot_artist_id_list) == 0:
                start_artist_id_list = [node for node in G.nodes() if len(G.edges([node])) > st.session_state.level * 10]
                bot_artist_id = np.random.choice(start_artist_id_list)
                st.session_state.bot_artist_id_list.append(bot_artist_id)
            
                col1.markdown("<h1 style='text-align: center;'>🤖</h1>", unsafe_allow_html=True)
                col2.markdown("<h1 style='text-align: center;'>👤</h1>", unsafe_allow_html=True)

            else: 
                bot_artist_id = st.session_state.bot_artist_id_list[-1]
            
            if not st.session_state.game_status is None:
                
                if st.session_state.game_status == True:
                    col1.info(artist_dict[bot_artist_id])
                    col2.success(artist_dict[st.session_state.player_artist_id_list[-1]])
                    st.success(st.session_state.game_message)

                else:
                    col1.info(artist_dict[bot_artist_id])
                    col2.error(artist_dict[st.session_state.player_artist_id_list[-1]])
                    st.error(st.session_state.game_message)

                    if st.session_state.game_message == "🤖 Pas de featuring trouvé entre ces artistes !":
                        if st.session_state.contributor_status == False:
                            st.markdown("✏️ Aidez nous ! Si ce featuring existe, complète notre base de données :")
                            url = st.text_input("URL youtube.com")
                            send = st.button("Envoyer")

                            if send:
                                if url.startswith("https://www.youtube.com/watch?v="):
                                    st.session_state.contributor_status = True
                                    st.experimental_rerun()
                                else:
                                    st.error("❌ URL invalide !")
                        else:
                            st.success("✅ Merci pour votre contribution !")

                with st.spinner('Visualisation de la partie...'):
                    fig = get_featuring_graph_chart(G, path, artist_dict)
                    st.plotly_chart(fig)

                st.markdown("🔍 **[Zoom]** Zoom dans le graphe en sélectionnant une zone pour explorer les connections.")
            
            else:
                featuring_list = [n1 for n0, n1 in G.edges([bot_artist_id])]
                print([artist_dict[a] for a in featuring_list]) # for tests

                col1.info(artist_dict[bot_artist_id])
                col2.warning("?")

                artist_name = st.selectbox(label="", options=[DEFAULT_VALUE] + artist_list)
                validate = st.button("Validé")

                if validate and artist_name != DEFAULT_VALUE:
                    artist_id = int(artist_dict_r[artist_name])
                    logs = st.session_state.bot_artist_id_list + st.session_state.player_artist_id_list
                    
                    if artist_id in logs:
                        st.session_state.game_status = False
                        st.session_state.game_message = "🤖 Cet artiste a déjà été joué !"
                        
                    elif not artist_id in featuring_list:
                        st.session_state.game_status = False
                        st.session_state.game_message = "🤖 Pas de featuring trouvé entre ces artistes !"
                            
                    else:
                        featuring_list = [n1 for n0, n1 in G.edges([artist_id])]
                                
                        if len(featuring_list) < st.session_state.level:
                            st.session_state.game_status = True
                            st.session_state.game_message = "🤖 Je m'avoue vaincu ... bien joué !"
                        
                        else:
                            l = np.random.randint(1, 100)
                            if st.session_state.round >= l:
                                st.session_state.game_status = True
                                st.session_state.game_message = "🤖 Je m'avoue vaincu ... bien joué !"
                            
                            else:
                                logs.append(artist_id)
                                featuring_list = [node for node in featuring_list if len(G.edges([node])) > st.session_state.level and not node in logs]
                                
                                if len(featuring_list) == 0:
                                    st.session_state.game_status = True
                                    st.session_state.game_message = "🤖 Je m'avoue vaincu ... bien joué !"
                                
                                else:
                                    st.session_state.round += 1
                                    
                                    # new bot artist
                                    bot_artist_id =np.random.choice(featuring_list)
                                    st.session_state.bot_artist_id_list.append(bot_artist_id)

                    st.session_state.player_artist_id_list.append(artist_id)
                    st.experimental_rerun()