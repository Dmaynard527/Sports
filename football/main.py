# main.py
import streamlit as st
from data_loader import load_data
from screens import home, upcoming_games, team, player, bets
# , fantasy_football

st.set_page_config(layout="wide", page_title="NFL Stats Dashboard")

# Load data once
data = load_data()

# Sidebar page selection (keeps original order)
page = st.sidebar.selectbox(
    "Choose a page",
    ["Home", "Upcoming Games", "Team", "Player", "Bets", "Fantasy Football"]
)

# Route to pages
if page == "Home":
    home.render(data)
elif page == "Upcoming Games":
    upcoming_games.render(data)
elif page == "Team":
    team.render(data)
elif page == "Player":
    player.render(data)
elif page == "Bets":
    bets.render(data)
# elif page == "Fantasy Football":
#     fantasy_football.render(data)
