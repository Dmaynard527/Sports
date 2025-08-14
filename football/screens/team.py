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
    completed_games = data['completed_games']

    title_col1, title_col2, title_col3, title_col4 = st.columns([4,1,0.9,8])
    # Sidebar: player selection for the selected team
    team_selected = st.sidebar.selectbox("Select a team", teams, index=0)

    with title_col1: 
        st.title(f"{team_selected}")
        # compute record metric like original
    winner_ct = len(completed_games[completed_games['team1'] == team_selected])
    loser_ct = len(completed_games[completed_games['team2'] == team_selected])
    record = f"{winner_ct} - {loser_ct}"

    # logo rendering
    svg_selected = team_selected.lower().replace(' ', '-') + '-logo.svg'
    svg_path = os.path.join(logo_path, svg_selected)
    svg_content = ''
    try:
        with open(svg_path, 'r') as f:
            svg_content = f.read().replace('width="700"', 'width="100"').replace('height="400"', 'height="100"')
    except Exception:
        svg_content = ''

    with title_col2:
        if svg_content:
            st.markdown(f'''<div style="width: 100px; height: 100px; overflow: hidden; display:flex; align-items:center; justify-content:center;">{svg_content}</div>''', unsafe_allow_html=True)
    with title_col3:
        st.metric('', record)


    # Build roster lists and active roster for the team
    team_roster = sorted(list(df.loc[df['Real_Team'] == team_selected, 'Player'].unique()))
    active_roster = sorted(list(df.loc[(df['year'] == str(new_year)) & (df['Real_Team'] == team_selected), 'Player'].unique()))
    active_roster_value = ', '.join(active_roster)
    active_roster_header = f"Team: {team_selected} | Active Roster:{active_roster_value}"
    st.markdown(f"<h5 style='font-size: 14px;'>{active_roster_header}</h5>", unsafe_allow_html=True)
    st.markdown("---")



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
        
    # year multiselect
    year_list = sorted(list(df['year'].unique()))
    with st.sidebar.expander("Select year(s)", expanded=False):
        selected_options = st.multiselect('Years', year_list, default=year_list)

    # Filter stat DataFrames
    passing = df[df.get('Passing_Yds', 0) > 0].copy()
    rushing = df[df.get('Rushing_Yds', 0) > 0].copy()
    receiving = df[df.get('Receiving_Yds', 0) > 0].copy()
    passing = passing.loc[passing['year'].isin(selected_options)]
    rushing = rushing.loc[rushing['year'].isin(selected_options)]
    receiving = receiving.loc[receiving['year'].isin(selected_options)]

    if player_selection:
        passing = passing[passing['Player'].isin(player_selection)]
        rushing = rushing[rushing['Player'].isin(player_selection)]
        receiving = receiving[receiving['Player'].isin(player_selection)]

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
    def legend_chart(df, mapping, yard_type):
        if yard_type == 'Receiving_Yds':
            height = 250 + 150
        else:
            height = team_pg_height
        title = yard_type[:-4]
        season_label = 'Season_' + yard_type
        if not df.empty:
            legend = alt.Chart(df).mark_bar(opacity=0).encode(
                x=alt.X('year_week:O',axis=alt.Axis(title=None)),
                y=f'{yard_type}:Q',
                color=alt.Color('Player:N', 
                                scale=alt.Scale(domain=list(mapping.keys()), 
                                                range=list(mapping.values())),
                                legend=alt.Legend(
                                    title=f"{title}",  # Custom legend title
                                    orient='left',  # Position the legend on the left
                                    direction='vertical'  # Make the legend vertical
                                )),
                order=alt.Order(f'{season_label}', sort='descending'),
                tooltip=['Player', f'{season_label}', 'week'],
        
            ).properties(
                width=600,
                height=height
            ).configure_legend(
                orient='left' # Position the legend on the left
            )
            st.altair_chart(legend, use_container_width=True)
            return legend
        else:
            st.write("No passing data for selection")

    with col1:
        # PASSING - legend
        passing_legend = legend_chart(passing, passing_mapping, 'Passing_Yds')

        # RUSHING - legend
        rushing_legend = legend_chart(rushing, rushing_mapping, 'Rushing_Yds')

        # RECEIVING - legend
        receiving_legend = legend_chart(receiving, receiving_mapping, 'Receiving_Yds')


    #### Main charts: Passing, Rushing, Receiving breakdowns ###

    # Base Yards Bar Chart
    def base_yards_bar_chart(df, mapping, yard_type):
        title = yard_type[:-4] + ' Yards'
        season_label = 'Season_' + yard_type
        if not df.empty:
            yds_chart = alt.Chart(df).mark_bar().encode(
                x=alt.X('year_week:O', axis=alt.Axis(title=None)),
                y=alt.Y(f'{yard_type}:Q', axis=alt.Axis(title=None)),
                color=alt.Color('Player:N', scale=alt.Scale(domain=list(mapping.keys()), range=list(mapping.values())), legend=None),
                order=alt.Order(f'{season_label}', sort='descending'),
                tooltip=['Player', f'{yard_type}', 'year_week']
            ).properties(title=f'{title}', width=600, height=team_pg_height)
            st.altair_chart(yds_chart, use_container_width=True)
            return yds_chart
        else:
            st.write(f"No {title} to show.")


    # Yards Bar chart
    with col2:
        passing_yds_chart = base_yards_bar_chart(passing, passing_mapping, 'Passing_Yds')
        rushing_yds_chart = base_yards_bar_chart(rushing, rushing_mapping, 'Rushing_Yds')
        receiving_yds_chart = base_yards_bar_chart(receiving, receiving_mapping, 'Receiving_Yds')

    # Touchdown Bar Chart
    def td_bar_chart(df, mapping, yds_type):
        title = yds_type[:-4] + ' Touchdowns'
        td_type = yds_type[:-3] + 'TD'
        season_label = 'Season_' + yds_type
        if not df.empty:
            td_chart = alt.Chart(df).mark_bar().encode(
                x=alt.X('year_week:O', axis=alt.Axis(title=None)),
                y=alt.Y(f'{td_type}:Q', axis=alt.Axis(title=None)),
                color=alt.Color('Player:N', scale=alt.Scale(domain=list(mapping.keys()), range=list(mapping.values())), legend=None),
                order=alt.Order(f'{season_label}', sort='descending'),
                tooltip=['Player', f'{td_type}', 'year_week']
            ).properties(title=f'{title}', width=600, height=team_pg_height)
            st.altair_chart(td_chart, use_container_width=True)
            return td_chart
        else:
            st.write(f"No {title} to show.")


    with col3:
    ### Touchdown Bar Chart
        passing_td_chart = td_bar_chart(passing, passing_mapping, 'Passing_Yds')
        rushing_td_chart = td_bar_chart(rushing, rushing_mapping, 'Rushing_Yds')
        receiving_td_chart = td_bar_chart(receiving, receiving_mapping, 'Receiving_Yds')

    def other_bar_chart(df, mapping, yds_type):
        title_split = yds_type.split('_')
        title = title_split[0] + ' + ' + title_split[1] + ' Yards'
        season_label = 'Season_' + yds_type[:7] + '_Yds'
        if not df.empty:
            other_yds_chart = alt.Chart(df).mark_bar().encode(
                x=alt.X('year_week:O',axis=alt.Axis(title=None)),
                y=alt.Y(f'{yds_type}:Q',axis=alt.Axis(title=None)),
                color=alt.Color('Player:N', scale=alt.Scale(domain=list(mapping.keys()), range=list(mapping.values())),legend=None),
                order=alt.Order(f'{season_label}', sort='descending'),
                tooltip=['Player', f'{yds_type}', 'year_week']
            ).properties(
                title=f'{title}',
                width=600,
                height=team_pg_height
            )
            st.altair_chart(other_yds_chart, use_container_width=True) 
            return other_yds_chart
        
        else:
            st.write(f"No {title} to show.")
    with col4:
    ### OTHER BAR CHART
        passing_rushing_yds_chart = other_bar_chart(passing, passing_mapping, 'Passing_Rushing_Yds')
        rushing_receiving_yds_chart = other_bar_chart(rushing, rushing_mapping, 'Rushing_Receiving_Yds')

    ### OTHER BAR CHART - RECEIVING
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
