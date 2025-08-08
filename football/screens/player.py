# pages/player.py
import streamlit as st
import pandas as pd
import plotly.express as px
from utils import real_teams

def render(data):
    """
    Player page: show per-player time series and season summary.
    """
    df = data['df'].copy()
    new_year = data['current_year']
    teams = data['teams']

    st.title("Player Page")

    # Player selection: get all players available in df
    all_players = sorted(df['Player'].dropna().unique())
    player = st.sidebar.selectbox("Select player", all_players, index=0)

    # Team selection (optional)
    team_selected = st.sidebar.selectbox("Team (optional)", ["All"] + teams, index=0)

    # Filter
    player_df = df[df['Player'] == player].copy()
    if team_selected != "All":
        player_df = player_df[player_df['Real_Team'] == team_selected]

    if player_df.empty:
        st.info("No data for selected player / team.")
        return

    # quick player header
    player_team = player_df['Real_Team'].dropna().unique()
    team_label = player_team[0] if len(player_team) > 0 else "Unknown"
    st.header(f"{player} — {team_label}")

    # aggregate season totals
    season_totals = player_df.groupby('year').sum(numeric_only=True).reset_index()
    st.subheader("Season totals")
    if not season_totals.empty:
        st.dataframe(season_totals.set_index('year'))
    else:
        st.write("No season totals available")

    # Time series charts for Passing, Rushing, Receiving (if present)
    # Ensure week exists and is numeric-like for x-axis
    if 'week' in player_df.columns:
        try:
            player_df['week_num'] = player_df['week'].astype(int)
        except Exception:
            player_df['week_num'] = player_df['week']

    # Passing
    if player_df.get('Passing_Yds', 0).sum() > 0:
        st.subheader("Passing Yards by Week")
        pass_df = player_df[['year', 'week_num', 'Passing_Yds']].copy()
        fig_pass = px.line(pass_df, x='week_num', y='Passing_Yds', color='year', markers=True,
                           labels={'week_num': 'Week', 'Passing_Yds': 'Passing Yards'}, title='Passing Yards')
        st.plotly_chart(fig_pass, use_container_width=True)
    else:
        st.write("No passing yards for this player.")

    # Rushing
    if player_df.get('Rushing_Yds', 0).sum() > 0:
        st.subheader("Rushing Yards by Week")
        rush_df = player_df[['year', 'week_num', 'Rushing_Yds']].copy()
        fig_rush = px.line(rush_df, x='week_num', y='Rushing_Yds', color='year', markers=True,
                           labels={'week_num': 'Week', 'Rushing_Yds': 'Rushing Yards'}, title='Rushing Yards')
        st.plotly_chart(fig_rush, use_container_width=True)
    else:
        st.write("No rushing yards for this player.")

    # Receiving
    if player_df.get('Receiving_Yds', 0).sum() > 0:
        st.subheader("Receiving Yards by Week")
        rec_df = player_df[['year', 'week_num', 'Receiving_Yds']].copy()
        fig_rec = px.line(rec_df, x='week_num', y='Receiving_Yds', color='year', markers=True,
                          labels={'week_num': 'Week', 'Receiving_Yds': 'Receiving Yards'}, title='Receiving Yards')
        st.plotly_chart(fig_rec, use_container_width=True)
    else:
        st.write("No receiving yards for this player.")

    # quick metrics for the player's most recent season
    st.markdown("---")
    st.subheader("Latest season snapshot")
    latest_year = player_df['year'].max()
    latest_df = player_df[player_df['year'] == latest_year]
    if not latest_df.empty:
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
        with metrics_col1:
            st.metric("Passing Yds (season)", int(latest_df['Passing_Yds'].sum()))
            st.metric("Passing TDs", int(latest_df.get('Passing_TD', 0).sum()))
            st.metric("INTs", int(latest_df.get('Passing_Int', 0).sum()))
        with metrics_col2:
            st.metric("Rushing Yds (season)", int(latest_df.get('Rushing_Yds', 0).sum()))
            st.metric("Rushing TDs", int(latest_df.get('Rushing_TD', 0).sum()))
        with metrics_col3:
            st.metric("Receiving Yds (season)", int(latest_df.get('Receiving_Yds', 0).sum()))
            st.metric("Receiving TDs", int(latest_df.get('Receiving_TD', 0).sum()))
    else:
        st.write("No snapshot for latest season available.")

    st.success("Player page loaded.")
