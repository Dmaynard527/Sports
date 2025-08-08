# pages/home.py
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import plotly.express as px
import matplotlib.pyplot as plt
from streamlit_folium import st_folium
import os
from utils import highlight_team, real_teams, target_lines

def render(data):
    df = data['df'].copy()
    upcoming_games = data['upcoming_games'].copy()
    completed_games = data['completed_games'].copy()
    color_df = data['color_df'].copy()
    location_df = data['location_df'].copy()
    teams = data['teams']
    new_year = data['current_year']
    path = data['path']
    logo_path = data['logo_path']

    # Title and layout columns like original
    title_col1, title_col2, title_col3, title_col4 = st.columns([3,1,0.9,8])
    top1, top2 = st.columns([10,0.01])
    middle1, middle2, middle3 = st.columns([0.75,5,5])

    # Create folium map and display in middle2 (so click sets map selection)
    import folium
    m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)
    for _, loc in location_df.iterrows():
        try:
            icon = folium.CustomIcon(loc["logo_path"], icon_size=(50, 50))
            folium.Marker(location=[loc["latitude"], loc["longitude"]], icon=icon, popup=loc['city_team']).add_to(m)
        except Exception:
            # fallback: plain marker
            folium.Marker(location=[loc.get("latitude", 39.0), loc.get("longitude", -98.0)], popup=loc.get('city_team','')).add_to(m)
    # Sidebar page-specific options
    with middle1:
        page1_options = ['Passing', 'Rushing', 'Receiving']
        page1_selection = st.selectbox("Options", page1_options)
        
    with middle2:
        returned_map_data = st_folium(m, width=1200, height=370)
        if returned_map_data["last_object_clicked"]:
            lat = returned_map_data["last_object_clicked"]['lat']
            map_selection = location_df.loc[location_df['latitude']==lat,'city_team'].values[0]
            map_selection_index = teams.index(map_selection)
        else:
            map_selection_index = 0

    # Sidebar filters include team selection and years (same as original)
    team_selected = st.sidebar.selectbox("Select a team", teams, index=map_selection_index)
    team_color = '#1f77b4'
    try:
        team_color = color_df[color_df['NFL Team Name'] == team_selected]['Color 1'].values[0]
    except Exception:
        pass

    
    # compute record metric like original
    winner_ct = len(completed_games[completed_games['team1'] == team_selected])
    loser_ct = len(completed_games[completed_games['team2'] == team_selected])
    record = f"{winner_ct} - {loser_ct}"

    with title_col1:
        st.title("NFL Stats Dashboard")
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

    # year multiselect
    year_list = sorted(list(df['year'].unique()))
    with st.sidebar.expander("Select year(s)", expanded=False):
        selected_options = st.multiselect('Years', year_list, default=year_list)

    # filter dataframes
    passing = df[df['Passing_Yds'] > 0].copy()
    rushing = df[df['Rushing_Yds'] > 0].copy()
    receiving = df[df['Receiving_Yds'] > 0].copy()
    passing = passing[passing['year'].isin(selected_options)]
    rushing = rushing[rushing['year'].isin(selected_options)]
    receiving = receiving[receiving['year'].isin(selected_options)]

    # Top lists & aggregates (like original)
    df_sum = df.groupby(['Player','year']).sum().reset_index()
    df_sum = df_sum.rename({'Passing_Int':'Int','Passing_TD':'Pass_TD'}, axis=1)
    df_sum = df_sum[df_sum['year'] == str(new_year)]
    df_sum['Team'] = df_sum['Team'].astype(str).str[:3]

    # avg df similar to original
    df_avg = df.groupby(['Player','Team','year']).mean(numeric_only=True).reset_index()
    df_avg = df_avg.rename({'Passing_Yds':'Avg_Pass_Yds','Passing_Rate':'Avg_Passer_Rating','Rushing_Yds':'Avg_Rush_Yds','Receiving_Yds':'Avg_Rec_Yds'}, axis=1)
    df_avg = df_avg[df_avg['year'] == str(new_year)]
    for col in ['Avg_Pass_Yds','Avg_Passer_Rating','Avg_Rush_Yds','Avg_Rec_Yds']:
        if col in df_avg.columns:
            df_avg[col] = df_avg[col].round(1)

    df_sum = pd.merge(df_sum, df_avg[['Player','Team','Avg_Pass_Yds','Avg_Passer_Rating','Avg_Rush_Yds','Avg_Rec_Yds']], how='left', on=['Player','Team'])

    # Projected stats (same approach)
    games_won = completed_games['team1'].value_counts()
    games_lost = completed_games['team2'].value_counts()
    games_played = games_won.add(games_lost, fill_value=0).astype(int).reset_index().rename({'index':'NFL_Team','count':'max_week'}, axis=1)
    # map to 3-letter team codes where possible
    from utils import reversed_real_teams
    games_played['Team'] = games_played['NFL_Team'].map(reversed_real_teams)
    df_sum = pd.merge(df_sum, games_played[['Team','max_week']], how='left', on='Team')
    for col, src in [('Projected_Pass_Yds','Passing_Yds'), ('Projected_Rush_Yds','Rushing_Yds'), ('Projected_Rec_Yds','Receiving_Yds')]:
        if src in df_sum.columns and 'max_week' in df_sum.columns:
            df_sum[col] = round((df_sum[src] / df_sum['max_week']) * 17, 0)

    # color mapping for players in active roster (keeps original palette code)
    active_roster = sorted(list(df.loc[(df['year'] == str(new_year)) & (df['Real_Team']==team_selected),'Player'].unique()))
    num_players = len(active_roster) if active_roster else 1
    colors = plt.cm.tab20(np.linspace(0, 1, num_players))
    color_mapping = {player: f'#{int(c[0]*255):02x}{int(c[1]*255):02x}{int(c[2]*255):02x}' for player, c in zip(active_roster, colors)}

    # layout: left side top lists and plots (roughly matches original)
    home_col1, home_col2, home_col3 = st.columns([1,5,5])

    with home_col1:
        # st.write("Passing")
        
        passing_top_df = df_sum.sort_values('Passing_Yds',ascending=False).reset_index()
        passing_top_df = passing_top_df.rename({"Passing_Yds":'Pass_Yds'},axis=1)

        passing_top_df['Rank'] = (passing_top_df.index + 1).astype(str) + ': ' + passing_top_df['Player']
        # st.dataframe(passing_top_df[['Rank','Team','Pass_Yds','Projected_Pass_Yds']].set_index('Rank'),
        #              use_container_width=True,
        #              height=145)
        
        #### CUMULATIVE PASSING YARDS ####
        passing_current = passing.loc[passing['year']==str(new_year)]
        passing_players = passing_current.groupby('Player').sum().sort_values('Passing_Yds', ascending=False).reset_index().reset_index(drop=True).iloc[:5]['Player']
        passing_current = passing_current.loc[(passing_current['Player'].isin(passing_players)) | (passing_current['Real_Team']==team_selected)]

        # Calculate cumulative sum of Passing_Yds by Player over weeks
        passing_current['cumulative_yards'] = passing_current.groupby('Player')['Passing_Yds'].cumsum()

        # To fix the issue, duplicate rows so that each frame includes data from all previous weeks
        passing_expanded = pd.DataFrame()

        for week in passing_current['week'].unique():
            # Add all data up to the current week for each frame
            temp_df = passing_current[passing_current['week'] <= week].copy()
            temp_df['current_week'] = week  # Store the current frame week
            passing_expanded = pd.concat([passing_expanded, temp_df])

        passing_expanded_sorted = passing_expanded.sort_values(by='cumulative_yards', ascending=False)
        sorted_players = passing_expanded_sorted['Player'].unique()

        # Create an animated line chart using Plotly Express
        fig_passing = px.line(
            passing_expanded,
            x='week',
            y='cumulative_yards',
            color='Player',
            line_group='Player',
            animation_frame='current_week',
            markers=True,
            title='Cumulative Passing Yards Over Weeks by Player',
            labels={'week': 'Week', 'cumulative_yards': 'Cumulative Passing Yards'},
            category_orders={'Player': sorted_players}
        )

        passing_current_max_week = passing_current['week'].max()+1
        passing_current_max_yards = passing_current['cumulative_yards'].max() + 500
        # Update layout to set y-axis range and other options
        fig_passing.update_layout(
            yaxis=dict(range=[0, passing_current_max_yards], title='Cumulative Passing Yards'),
            xaxis=dict(range=[0, passing_current_max_week], title='Week'),
            showlegend=True,
            width=800,
            height= 400
        )


        # st.plotly_chart(fig_passing)        

    with home_col2:
        # st.write("Rushing")
        rushing_top_df = df_sum.sort_values('Rushing_Yds',ascending=False).reset_index()
        rushing_top_df = rushing_top_df.rename({"Rushing_Yds":'Rush_Yds'},axis=1)

        rushing_top_df['Rank'] = (rushing_top_df.index + 1).astype(str) + ': ' + rushing_top_df['Player']
        # st.dataframe(rushing_top_df[['Rank','Team','Rush_Yds','Projected_Rush_Yds']].set_index('Rank'),
        #              use_container_width=True,
        #              height=145)
        
        #### CUMULATIVE RUSHING YARDS ####
        rushing_current = rushing.loc[rushing['year']==str(new_year)]
        rushing_players = rushing_current.groupby('Player').sum().sort_values('Rushing_Yds', ascending=False).reset_index().reset_index(drop=True).iloc[:5]['Player']
        rushing_current = rushing_current.loc[(rushing_current['Player'].isin(rushing_players)) | (rushing_current['Real_Team']==team_selected)]

        # Calculate cumulative sum of Passing_Yds by Player over weeks
        rushing_current['cumulative_yards'] = rushing_current.groupby('Player')['Rushing_Yds'].cumsum()

        # To fix the issue, duplicate rows so that each frame includes data from all previous weeks
        rushing_expanded = pd.DataFrame()

        for week in rushing_current['week'].unique():
            # Add all data up to the current week for each frame
            temp_df = rushing_current[rushing_current['week'] <= week].copy()
            temp_df['current_week'] = week  # Store the current frame week
            rushing_expanded = pd.concat([rushing_expanded, temp_df])
        rushing_expanded_sorted = rushing_expanded.sort_values(by='cumulative_yards', ascending=False)
        sorted_players = rushing_expanded_sorted['Player'].unique()
        # Create an animated line chart using Plotly Express
        fig_rushing = px.line(
            rushing_expanded,
            x='week',
            y='cumulative_yards',
            color='Player',
            line_group='Player',
            animation_frame='current_week',
            markers=True,
            title='Cumulative Rushing Yards Over Weeks by Player',
            labels={'week': 'Week', 'cumulative_yards': 'Cumulative Rushing Yards'},
            category_orders={'Player': sorted_players}
        )

        rushing_current_max_week = rushing_current['week'].max()+1
        rushing_current_max_yards = rushing_current['cumulative_yards'].max() + 100
        # Update layout to set y-axis range and other options
        fig_rushing.update_layout(
            yaxis=dict(range=[0, rushing_current_max_yards], title='Cumulative Rushing Yards'),
            xaxis=dict(range=[0, rushing_current_max_week], title='Week'),
            showlegend=True,
            width=800,
            height=400
        )


        # st.plotly_chart(fig_rushing)  

    with home_col3:
        # st.write("Receiving")
        receiving_top_df = df_sum.sort_values('Receiving_Yds',ascending=False).reset_index()
        receiving_top_df = receiving_top_df.rename({"Receiving_Yds":'Rec_Yds'},axis=1)

        receiving_top_df['Rank'] = (receiving_top_df.index + 1).astype(str) + ': ' + receiving_top_df['Player']
        # st.dataframe(receiving_top_df[['Rank','Team','Rec_Yds','Projected_Rec_Yds']].set_index('Rank'),
        #              use_container_width=True,
        #              height=145)
        
       #### CUMULATIVE RECEIVING YARDS ####
        rec_current = receiving.loc[receiving['year']==str(new_year)]
        rec_players = rec_current.groupby('Player').sum().sort_values('Receiving_Yds', ascending=False).reset_index().reset_index(drop=True).iloc[:5]['Player']
        rec_current = rec_current.loc[(rec_current['Player'].isin(rec_players)) | (rec_current['Real_Team']==team_selected)]

        # Calculate cumulative sum of Passing_Yds by Player over weeks
        rec_current['cumulative_yards'] = rec_current.groupby('Player')['Receiving_Yds'].cumsum()

        # To fix the issue, duplicate rows so that each frame includes data from all previous weeks
        rec_expanded = pd.DataFrame()

        for week in rec_current['week'].unique():
            # Add all data up to the current week for each frame
            temp_df = rec_current[rec_current['week'] <= week].copy()
            temp_df['current_week'] = week  # Store the current frame week
            rec_expanded = pd.concat([rec_expanded, temp_df])

        rec_expanded_sorted = rec_expanded.sort_values(by='cumulative_yards', ascending=False)
        sorted_players = rec_expanded_sorted['Player'].unique()
        # rec_expanded = rec_expanded.sort_values(by='cumulative_yards', ascending=True)

        # Create an animated line chart using Plotly Express
        fig_rec = px.line(
            rec_expanded,
            x='week',
            y='cumulative_yards',
            color='Player',
            line_group='Player',
            animation_frame='current_week',
            markers=True,
            title='Cumulative Receiving Yards Over Weeks by Player',
            labels={'week': 'Week', 'cumulative_yards': 'Cumulative Receiving Yards'},
            category_orders={'Player': sorted_players}
        )

        rec_current_max_week = rec_current['week'].max()+1
        rec_current_max_yards = rec_current['cumulative_yards'].max() + 100
        # Update layout to set y-axis range and other options
        fig_rec.update_layout(
            yaxis=dict(range=[0, rec_current_max_yards], title='Cumulative Receiving Yards'),
            xaxis=dict(range=[0, rec_current_max_week], title='Week'),
            showlegend=True,
            width=800,
            height=400
        )

    # Build cumulative chart using the exact logic (passing as example)
    def cumulative_chart(df, yard_type):
        # example df: passing, rushing, receiving
        # example yard_type: 'Passing_Yds', 'Rushing_Yds', 'Receiving_Yds'
        yard_type_chart = yard_type[:-4]
        current = df[df['year'] == str(new_year)].copy()
        if not current.empty:
            players = current.groupby('Player').sum().sort_values(yard_type, ascending=False).reset_index().iloc[:5]['Player']
            current = current.loc[(current['Player'].isin(players)) | (current['Real_Team']==team_selected)]
            current['cumulative_yards'] = current.groupby('Player')[yard_type].cumsum()
            # expand frames
            expanded = []
            for week in sorted(current['week'].unique()):
                temp = current[current['week'] <= week].copy()
                temp['current_week'] = week
                expanded.append(temp)
            if expanded:
                expanded = pd.concat(expanded, ignore_index=True)
                sorted_players = expanded.sort_values('cumulative_yards', ascending=False)['Player'].unique()
                fig = px.line(
                    expanded,
                    x='week',
                    y='cumulative_yards',
                    color='Player',
                    line_group='Player',
                    animation_frame='current_week',
                    markers=True,
                    title=f'Cumulative {yard_type_chart} Yards Over Weeks by Player',
                    labels={'week': 'Week', 'cumulative_yards': f'Cumulative {yard_type_chart} Yards'},
                    category_orders={'Player': sorted_players}
                )
                # set y/x ranges similarly
                current_max_week = current['week'].max() + 1 if not current['week'].empty else 1
                current_max_yards = current['cumulative_yards'].max() + 500 if 'cumulative_yards' in current else None
                fig.update_layout(yaxis=dict(range=[0, current_max_yards], title=f'Cumulative {yard_type_chart} Yards'),
                                          xaxis=dict(range=[0, current_max_week], title='Week'),
                                          showlegend=True, width=800, height=400)
                return fig
 
    with middle2:
        if page1_selection == 'Passing':
            fig_passing = cumulative_chart(passing, 'Passing_Yds')
            st.plotly_chart(fig_passing, use_container_width=True)
        elif page1_selection == 'Rushing':
            fig_rushing = cumulative_chart(rushing, 'Rushing_Yds')
            st.plotly_chart(fig_rushing, use_container_width=True)
        else:
            fig_receiving = cumulative_chart(receiving, 'Receiving_Yds')
            st.plotly_chart(fig_receiving, use_container_width=True)

    # create a combined Altair bar chart for the chosen stat (mirrors original bar + projected)
    with middle3:
        if page1_selection == 'Passing':
            passing_top_df = df_sum.sort_values('Passing_Yds',ascending=False).reset_index()
            passing_top_df = passing_top_df.rename({"Passing_Yds":'Pass_Yds'},axis=1)
            passing_top_df['Rank'] = (passing_top_df.index + 1).astype(str) + ': ' + passing_top_df['Player']
            passing_top_df['NFL_Team'] = passing_top_df['Team'].map(real_teams)
            top_for_chart = pd.concat([passing_top_df.iloc[:5], passing_top_df.loc[passing_top_df['NFL_Team'] == team_selected]], axis=0).drop_duplicates()
            top_for_chart = top_for_chart[top_for_chart['Pass_Yds'] > 0]
            if not top_for_chart.empty:
                color_condition = alt.condition(alt.datum.NFL_Team == team_selected, alt.value(team_color), alt.value('darkgrey'))
                proj = alt.Chart(top_for_chart).mark_bar().encode(x=alt.X('sum(Projected_Pass_Yds):Q', axis=alt.Axis(title=None)),
                                                                 y=alt.Y('Player:N', sort=alt.EncodingSortField(field='Pass_Yds', op='sum', order='descending')),
                                                                 color=alt.value('lightgrey'))
                actual = alt.Chart(top_for_chart).mark_bar().encode(x=alt.X('sum(Pass_Yds):Q', axis=alt.Axis(title=None)),
                                                                     y=alt.Y('Player:N', sort=alt.EncodingSortField(field='Pass_Yds', op='sum', order='descending')),
                                                                     color=color_condition,
                                                                     tooltip=['Player:N','Pass_Yds:Q','NFL_Team:N'])
                st.altair_chart(proj + actual, use_container_width=True)

                # styled dataframe: show columns similar to original and allow toggle to show only team players
                passing_top_df_short = passing_top_df[passing_top_df['Pass_Yds'] > 0][['Rank','NFL_Team','Pass_Yds','Projected_Pass_Yds','Pass_TD','Int','Avg_Pass_Yds','Avg_Passer_Rating']].set_index('Rank')
                only_team = st.toggle("Show only selected team players")
                if only_team:
                    passing_top_df_short = passing_top_df_short[passing_top_df_short['NFL_Team'] == team_selected]
                # apply styling using dataframe .style and our highlight_team helper
                styled = passing_top_df_short.style.apply(lambda r: highlight_team(r, team_selected), axis=1)
                st.dataframe(styled, width=900, height=400)
        elif page1_selection == 'Rushing':
            rushing_top_df = df_sum.sort_values('Rushing_Yds', ascending=False).reset_index(drop=True)
            rushing_top_df = rushing_top_df.rename({"Rushing_Yds": 'Rush_Yds'}, axis=1)
            rushing_top_df['Rank'] = (rushing_top_df.index + 1).astype(str) + ': ' + rushing_top_df['Player']
            rushing_top_df['NFL_Team'] = rushing_top_df['Team'].map(real_teams)
            top_for_chart = pd.concat([rushing_top_df.iloc[:5], rushing_top_df.loc[rushing_top_df['NFL_Team'] == team_selected]], axis=0).drop_duplicates()
            top_for_chart = top_for_chart[top_for_chart['Rush_Yds'] > 0]
            if not top_for_chart.empty:
                color_condition = alt.condition(alt.datum.NFL_Team == team_selected, alt.value(team_color), alt.value('darkgrey'))
                proj = alt.Chart(top_for_chart).mark_bar().encode(x=alt.X('sum(Projected_Rush_Yds):Q', axis=alt.Axis(title=None)),
                                                                 y=alt.Y('Player:N', sort=alt.EncodingSortField(field='Rush_Yds', op='sum', order='descending')),
                                                                 color=alt.value('lightgrey'))
                actual = alt.Chart(top_for_chart).mark_bar().encode(x=alt.X('sum(Rush_Yds):Q', axis=alt.Axis(title=None)),
                                                                     y=alt.Y('Player:N', sort=alt.EncodingSortField(field='Rush_Yds', op='sum', order='descending')),
                                                                     color=color_condition,
                                                                     tooltip=['Player:N','Rush_Yds:Q','NFL_Team:N'])
                st.altair_chart(proj + actual, use_container_width=True)

                rushing_top_short = rushing_top_df[rushing_top_df['Rush_Yds']>0][['Rank','NFL_Team','Rush_Yds','Projected_Rush_Yds','Rushing_Receiving_TD','Avg_Rush_Yds','Avg_Rec_Yds']].set_index('Rank')
                only_team = st.toggle("Show only selected team players")
                if only_team:
                    rushing_top_short = rushing_top_short[rushing_top_short['NFL_Team'] == team_selected]
                st.dataframe(rushing_top_short.style.apply(lambda r: highlight_team(r, team_selected), axis=1), width=900, height=400)
        else:
            receiving_top_df = df_sum.sort_values('Receiving_Yds', ascending=False).reset_index(drop=True)
            receiving_top_df = receiving_top_df.rename({"Receiving_Yds":"Rec_Yds"}, axis=1)
            receiving_top_df['Rank'] = (receiving_top_df.index + 1).astype(str) + ': ' + receiving_top_df['Player']
            receiving_top_df['NFL_Team'] = receiving_top_df['Team'].map(real_teams)
            top_for_chart = pd.concat([receiving_top_df.iloc[:5], receiving_top_df.loc[receiving_top_df['NFL_Team'] == team_selected]], axis=0).drop_duplicates()
            top_for_chart = top_for_chart[top_for_chart['Rec_Yds'] > 0]
            if not top_for_chart.empty:
                color_condition = alt.condition(alt.datum.NFL_Team == team_selected, alt.value(team_color), alt.value('darkgrey'))
                proj = alt.Chart(top_for_chart).mark_bar().encode(x=alt.X('sum(Projected_Rec_Yds):Q', axis=alt.Axis(title=None)),
                                                                 y=alt.Y('Player:N', sort=alt.EncodingSortField(field='Rec_Yds', op='sum', order='descending')),
                                                                 color=alt.value('lightgrey'))
                actual = alt.Chart(top_for_chart).mark_bar().encode(x=alt.X('sum(Rec_Yds):Q', axis=alt.Axis(title=None)),
                                                                     y=alt.Y('Player:N', sort=alt.EncodingSortField(field='Rec_Yds', op='sum', order='descending')),
                                                                     color=color_condition,
                                                                     tooltip=['Player:N','Rec_Yds:Q','NFL_Team:N'])
                st.altair_chart(proj + actual, use_container_width=True)

                receiving_top_short = receiving_top_df[receiving_top_df['Rec_Yds']>0][['Rank','NFL_Team','Rec_Yds','Projected_Rec_Yds','Rushing_Receiving_TD','Avg_Rec_Yds','Avg_Rush_Yds']].set_index('Rank')
                only_team = st.toggle("Show only selected team players")
                if only_team:
                    receiving_top_short = receiving_top_short[receiving_top_short['NFL_Team'] == team_selected]
                st.dataframe(receiving_top_short.style.apply(lambda r: highlight_team(r, team_selected), axis=1), width=900, height=400)

    # done
    st.success("Home page loaded.")