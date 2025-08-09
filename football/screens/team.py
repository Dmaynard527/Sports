# pages/team.py
import streamlit as st
import altair as alt
import pandas as pd
import numpy as np
import os
from utils import real_teams
import matplotlib.pyplot as plt

def render(data):
    """
    Team page: shows team-level charts and per-player breakdowns.
    Expects data dict from data_loader.load_data()
    """
    df = data['df'].copy()
    color_df = data['color_df']
    teams = data['teams']
    logo_path = data['logo_path']
    new_year = data['current_year']

    st.title("Team Page")

    # Sidebar: player selection for the selected team
    team_selected = st.sidebar.selectbox("Select a team", teams, index=0)

    # Build roster lists and active roster for the team
    team_roster = sorted(list(df.loc[df['Real_Team'] == team_selected, 'Player'].unique()))
    active_roster = sorted(list(df.loc[(df['year'] == str(new_year)) & (df['Real_Team'] == team_selected), 'Player'].unique()))

    # Generate colors using a colormap
    num_players = len(active_roster)
    colors = plt.cm.tab20(np.linspace(0, 1, num_players))
    
    # Create a color mapping
    color_mapping = {player: f'#{int(color[0]*255):02x}{int(color[1]*255):02x}{int(color[2]*255):02x}' for player, color in zip(active_roster, colors)}

    ### PLAYER SELECTION ###
    with st.sidebar.expander("Select player(s)", expanded=False):
        player_selection = st.multiselect('Players',
                                        team_roster, 
                                        default=active_roster)
    # Filter stat DataFrames
    passing = df[df.get('Passing_Yds', 0) > 0].copy()
    rushing = df[df.get('Rushing_Yds', 0) > 0].copy()
    receiving = df[df.get('Receiving_Yds', 0) > 0].copy()

    if player_selection:
        passing = passing[passing['Player'].isin(player_selection)]
        rushing = rushing[rushing['Player'].isin(player_selection)]
        receiving = receiving[receiving['Player'].isin(player_selection)]

    # # Create color mapping for players using a simple palette if available
    # players_all = sorted(list(set(list(passing['Player'].unique()) + list(rushing['Player'].unique()) + list(receiving['Player'].unique()))))
    # # fallback color palette
    # palette = alt.Scale(range=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b',
    #                            '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'])

        ### ADDED INFO TO SIDEBAR ###
    qb_list = sorted(list(passing[passing['Player_Category']=='Quarterback']['Player'].unique()))
    rb_list = sorted(list(rushing[rushing['Player_Category']=='Running Back']['Player'].unique()))
    rec_list = sorted(list(receiving[receiving['Player_Category']=='Receiver']['Player'].unique()))

    qb_sidebar = st.sidebar.write('QBs:',', '.join(qb_list))
    rb_sidebar = st.sidebar.write('RBs:',', '.join(rb_list))
    rec_sidebar = st.sidebar.write('Receivers:',', '.join(rec_list))

    passing_players = list(passing['Player'].unique())
    passing_mapping = {key: value for key, value in color_mapping.items() if key in passing_players}
    rushing_players = list(rushing['Player'].unique())
    rushing_mapping = {key: value for key, value in color_mapping.items() if key in rushing_players}
    receiving_players = list(receiving['Player'].unique())
    receiving_mapping = {key: value for key, value in color_mapping.items() if key in receiving_players}                       
    
    # Create four columns for legend + three charts as in original
    col1, col2, col3, col4= st.columns([0.5,2,2,2])

    team_pg_height = 250

    # PASSING - legend (in original, empty bars used for legend)
    with col1:
        if not passing.empty:
            passing_legend = alt.Chart(passing).mark_bar(opacity=0).encode(
                x=alt.X('year_week:O',axis=alt.Axis(title=None)),
                y='Passing_Yds:Q',
                color=alt.Color('Player:N', 
                                scale=alt.Scale(domain=list(passing_mapping.keys()), 
                                                range=list(passing_mapping.values())),
                                legend=alt.Legend(
                                    title="Passing",  # Custom legend title
                                    orient='left',  # Position the legend on the left
                                    direction='vertical'  # Make the legend vertical
                                )),
                order=alt.Order('Season_Passing_Yds', sort='descending'),
                tooltip=['Player', 'Season_Passing_Yds', 'week'],
        
            ).properties(
                width=600,
                height=team_pg_height
            ).configure_legend(
                orient='left' # Position the legend on the left
            )
            st.altair_chart(passing_legend, use_container_width=True)
        else:
            st.write("No passing data for selection")

        # RUSHING - legend
        if not rushing.empty:
            rushing_legend = alt.Chart(rushing).mark_bar(opacity=0).encode(
                x=alt.X('year_week:O', axis=alt.Axis(title=None)),
                y='Rushing_Yds:Q',
                color=alt.Color('Player:N',
                                scale=alt.Scale(domain=list(rushing_mapping.keys()), 
                                                range=list(rushing_mapping.values())),
                                legend=alt.Legend(title="Rushing", orient='left', direction='vertical')
                                ),
                order=alt.Order('Season_Rushing_Yds', sort='descending'),
                tooltip=['Player', 'Season_Rushing_Yds', 'week']
            ).properties(width=600, height=team_pg_height).configure_legend(orient='left')
            st.altair_chart(rushing_legend, use_container_width=True)
        else:
            st.write("No rushing data for selection")

        # RECEIVING - legend
        if not receiving.empty:
            receiving_legend = alt.Chart(receiving).mark_bar(opacity=0).encode(
                x=alt.X('year_week:O', axis=alt.Axis(title=None)),
                y='Receiving_Yds:Q',
                color=alt.Color('Player:N',
                                scale=alt.Scale(domain=list(receiving_mapping.keys()), 
                                                range=list(receiving_mapping.values())),
                                legend=alt.Legend(title="Receiving", orient='left', direction='vertical')
                                ),
                order=alt.Order('Season_Receiving_Yds', sort='descending'),
                tooltip=['Player', 'Season_Receiving_Yds', 'week']
            ).properties(width=600, height=team_pg_height + 150
                        ).configure_legend(orient='left')
            st.altair_chart(receiving_legend, use_container_width=True)
        else:
            st.write("No receiving data for selection")


    # Main charts: Passing, Rushing, Receiving breakdowns

    # Passing yards chart
    with col2:
        if not passing.empty:
            passing_yds_chart = alt.Chart(passing).mark_bar().encode(
                x=alt.X('year_week:O', axis=alt.Axis(title=None)),
                y=alt.Y('Passing_Yds:Q', axis=alt.Axis(title=None)),
                color=alt.Color('Player:N', scale=alt.Scale(domain=list(passing_mapping.keys()), range=list(passing_mapping.values())), legend=None),
                order=alt.Order('Season_Passing_Yds', sort='descending'),
                tooltip=['Player', 'Passing_Yds', 'year_week']
            ).properties(title='Passing Yards', width=600, height=team_pg_height)
            st.altair_chart(passing_yds_chart, use_container_width=True)
        else:
            st.write("No passing yards to show.")

    # Rushing yards chart
        if not rushing.empty:
            rushing_yds_chart = alt.Chart(rushing).mark_bar().encode(
                x=alt.X('year_week:O', axis=alt.Axis(title=None)),
                y=alt.Y('Rushing_Yds:Q', axis=alt.Axis(title=None)),
                color=alt.Color('Player:N', scale=alt.Scale(domain=list(rushing_mapping.keys()), range=list(rushing_mapping.values())), legend=None),
                order=alt.Order('Season_Rushing_Yds', sort='descending'),
                tooltip=['Player', 'Rushing_Yds', 'year_week']
            ).properties(title='Rushing Yards', width=600, height=team_pg_height)
            st.altair_chart(rushing_yds_chart, use_container_width=True)
        else:
            st.write("No rushing yards to show.")

    # Receiving yards chart
        if not receiving.empty:
            receiving_yds_chart = alt.Chart(receiving).mark_bar().encode(
                x=alt.X('year_week:O', axis=alt.Axis(title=None)),
                y=alt.Y('Receiving_Yds:Q', axis=alt.Axis(title=None)),
                color=alt.Color('Player:N', scale=alt.Scale(domain=list(receiving_mapping.keys()), range=list(receiving_mapping.values())), legend=None),
                order=alt.Order('Season_Receiving_Yds', sort='descending'),
                tooltip=['Player', 'Receiving_Yds', 'year_week']
            ).properties(title='Receiving Yards', width=600, height=team_pg_height)
            st.altair_chart(receiving_yds_chart, use_container_width=True)
        else:
            st.write("No receiving yards to show.")

    with col3:
    ### PASSING
        passing_td_chart = alt.Chart(passing).mark_bar().encode(
            x=alt.X('year_week:O',axis=alt.Axis(title=None)),
            y=alt.Y('Passing_TD:Q',axis=alt.Axis(title=None)),
            color=alt.Color('Player:N',scale=alt.Scale(domain=list(passing_mapping.keys()), range=list(passing_mapping.values())),legend=None),
            order=alt.Order('Season_Passing_Yds', sort='descending'),
            tooltip=['Player', 'Passing_TD', 'year_week']
        ).properties(
            title='Passing Touchdowns',
            width=600,
            height=team_pg_height
        )

        # Display the chart in Streamlit
        st.altair_chart(passing_td_chart, use_container_width=True) 

    ### RUSHING
        rushing_td_chart = alt.Chart(rushing).mark_bar().encode(
            x=alt.X('year_week:O',axis=alt.Axis(title=None)),
            y=alt.Y('Rushing_TD:Q',axis=alt.Axis(title=None)),
            color=alt.Color('Player:N', scale=alt.Scale(domain=list(rushing_mapping.keys()), range=list(rushing_mapping.values())),legend=None),
            order=alt.Order('Season_Rushing_Yds', sort='descending'),
            tooltip=['Player', 'Rushing_TD', 'year_week']
        ).properties(
            title='Rushing Touchdowns',
            width=600,
            height=team_pg_height
        )

        # Display the chart in Streamlit
        st.altair_chart(rushing_td_chart, use_container_width=True)

    ### RECEIVING
        receiving_td_chart = alt.Chart(receiving).mark_bar().encode(
            x=alt.X('year_week:O',axis=alt.Axis(title=None)),
            y=alt.Y('Receiving_TD:Q',axis=alt.Axis(title=None)),
            color=alt.Color('Player:N', scale=alt.Scale(domain=list(receiving_mapping.keys()), range=list(receiving_mapping.values())),legend=None),
            order=alt.Order('Season_Receiving_Yds', sort='descending'),
            tooltip=['Player', 'Receiving_TD', 'year_week']
        ).properties(
            title='Receiving Touchdowns',
            width=600,
            height=team_pg_height
        )

        # Display the chart in Streamlit
        st.altair_chart(receiving_td_chart, use_container_width=True) 

  

    with col4:
    ### PASSING
        passing_rushing_yds_chart = alt.Chart(passing).mark_bar().encode(
            x=alt.X('year_week:O',axis=alt.Axis(title=None)),
            y=alt.Y('Passing_Rushing_Yds:Q',axis=alt.Axis(title=None)),
            color=alt.Color('Player:N', scale=alt.Scale(domain=list(passing_mapping.keys()), range=list(passing_mapping.values())),legend=None),
            order=alt.Order('Season_Passing_Yds', sort='descending'),
            tooltip=['Player', 'Passing_Rushing_Yds', 'year_week']
        ).properties(
            title='Passing + Rushing Yards',
            width=600,
            height=team_pg_height
        )

        # Display the chart in Streamlit
        st.altair_chart(passing_rushing_yds_chart, use_container_width=True) 

    ### RUSHING
        rushing_receiving_yds_chart = alt.Chart(rushing).mark_bar().encode(
            x=alt.X('year_week:O',axis=alt.Axis(title=None)),
            y=alt.Y('Rushing_Receiving_Yds:Q',axis=alt.Axis(title=None)),
            color=alt.Color('Player:N', scale=alt.Scale(domain=list(rushing_mapping.keys()), range=list(rushing_mapping.values())),legend=None),
            order=alt.Order('Season_Rushing_Yds', sort='descending'),
            tooltip=['Player', 'Rushing_Receiving_Yds', 'year_week']
        ).properties(
            title='Rushing + Receiving Yards',
            width=600,
            height=team_pg_height
        )

        # Display the chart in Streamlit
        st.altair_chart(rushing_receiving_yds_chart, use_container_width=True) 

    ### RECEIVING
        receiving_target_chart = alt.Chart(receiving).mark_bar().encode(
            x=alt.X('year_week:O',axis=alt.Axis(title=None)),
            y=alt.Y('Receiving_Rec:Q',axis=alt.Axis(title=None)),
            color=alt.Color('Player:N', scale=alt.Scale(domain=list(receiving_mapping.keys()), range=list(receiving_mapping.values())),legend=None),
            order=alt.Order('Season_Receiving_Yds', sort='descending'),
            tooltip=['Player', 'Receiving_Rec', 'year_week']
        ).properties(
            title='Receiving Receptions',
            width=600,
            height=team_pg_height
        )

        # Display the chart in Streamlit
        st.altair_chart(receiving_target_chart, use_container_width=True)

    st.success("Team page loaded.")
