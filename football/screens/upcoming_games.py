# pages/upcoming_games.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import altair as alt
import os

def render(data):
    df = data['df'].copy()
    upcoming_games = data['upcoming_games'].copy()
    completed_games = data['completed_games'].copy()
    color_df = data['color_df'].copy()
    logo_path = data['logo_path']

    st.title("Upcoming Games")
    # distinct teams
    teams = sorted(list(df['Real_Team'].unique()))
    team_selected = st.sidebar.selectbox("Select a team", teams)
    upcoming_games = upcoming_games[upcoming_games['Home_Team'].str.contains(team_selected) | upcoming_games['Away_Team'].str.contains(team_selected)].reset_index()


    if upcoming_games.empty:
        st.info("No upcoming_games file found for current season.")
        return

    game = st.sidebar.selectbox('Game:', upcoming_games['Game'].unique())
    away_team = game.split('@')[0].strip()
    home_team = game.split('@')[1].strip()

    # Build completed_games_sub (same logic as original)
    completed_games['opponent_team'] = np.nan
    completed_games['searched_team'] = np.nan
    completed_games['opponent_score'] = np.nan
    completed_games['team_score'] = np.nan

    # populate for both away & home
    for team in [away_team, home_team]:
        # Mask for when this team is team1 or team2
        mask_team1 = completed_games['team1'] == team
        mask_team2 = completed_games['team2'] == team
        
        # Opponent team
        completed_games.loc[mask_team1, 'opponent_team'] = completed_games.loc[mask_team1, 'team2']
        completed_games.loc[mask_team2, 'opponent_team'] = completed_games.loc[mask_team2, 'team1']
        
        # Searched team
        completed_games.loc[mask_team1, 'searched_team'] = completed_games.loc[mask_team1, 'team1']
        completed_games.loc[mask_team2, 'searched_team'] = completed_games.loc[mask_team2, 'team2']
        
        # Scores
        completed_games.loc[mask_team1, 'opponent_score'] = completed_games.loc[mask_team1, 'opp_score']
        completed_games.loc[mask_team2, 'opponent_score'] = completed_games.loc[mask_team2, 'tm_score']
        completed_games.loc[mask_team1, 'team_score'] = completed_games.loc[mask_team1, 'tm_score']
        completed_games.loc[mask_team2, 'team_score'] = completed_games.loc[mask_team2, 'opp_score']

    completed_games_sub = completed_games[['year_week','opponent_team','searched_team','opponent_score','team_score']].copy()
    completed_scores = completed_games_sub[completed_games_sub['opponent_team'].notnull()].copy()
    completed_scores['WinLoss'] = 'Loss'
    completed_scores.loc[(completed_scores['opponent_score'] - completed_scores['team_score']) < 0, 'WinLoss'] = 'Win'
    avg_scores = completed_scores.groupby(['searched_team']).agg({'team_score':'mean','opponent_score':'mean'}).reset_index()

    # Defense/offense past merging (like original)
    passing = df[df['Passing_Yds'] > 0].copy()
    rushing = df[df['Rushing_Yds'] > 0].copy()
    receiving = df[df['Receiving_Yds'] > 0].copy()

    passing_def = pd.merge(passing, completed_games_sub, how='inner', left_on=['year_week','Real_Team'], right_on=['year_week','opponent_team'])
    passing_def['team_category'] = 'Defense ' + passing_def['searched_team']
    passing_off = pd.merge(passing, completed_games_sub, how='inner', left_on=['year_week','Real_Team'], right_on=['year_week','searched_team'])
    passing_off['team_category'] = 'Offense ' + passing_off['searched_team']
    passing_past = pd.concat([passing_off, passing_def], axis=0)

    passing_awayteam = passing_past[passing_past['team_category'].isin(['Offense ' + away_team, 'Defense ' + home_team])]
    passing_hometeam = passing_past[passing_past['team_category'].isin(['Offense ' + home_team, 'Defense ' + away_team])]

    total_passing_away = passing_awayteam.groupby(['year_week','Player','team_category']).agg({'Passing_Yds':'sum'}).reset_index().sort_values(['year_week','Passing_Yds'], ascending=[True, False])
    total_passing_home = passing_hometeam.groupby(['year_week','Player','team_category']).agg({'Passing_Yds':'sum'}).reset_index().sort_values(['year_week','Passing_Yds'], ascending=[True, False])

    # same for rushing & receiving
    rushing_def = pd.merge(rushing, completed_games_sub, how='inner', left_on=['year_week','Real_Team'], right_on=['year_week','opponent_team'])
    rushing_def['team_category'] = 'Defense ' + rushing_def['searched_team']
    rushing_off = pd.merge(rushing, completed_games_sub, how='inner', left_on=['year_week','Real_Team'], right_on=['year_week','searched_team'])
    rushing_off['team_category'] = 'Offense ' + rushing_off['searched_team']
    rushing_past = pd.concat([rushing_off, rushing_def], axis=0)
    rushing_awayteam = rushing_past[rushing_past['team_category'].isin(['Offense ' + away_team, 'Defense ' + home_team])]
    rushing_hometeam = rushing_past[rushing_past['team_category'].isin(['Offense ' + home_team, 'Defense ' + away_team])]
    total_rushing_away = rushing_awayteam.groupby(['year_week','Player','team_category']).agg({'Rushing_Yds':'sum'}).reset_index().sort_values(['year_week','Rushing_Yds'], ascending=[True, False])
    total_rushing_home = rushing_hometeam.groupby(['year_week','Player','team_category']).agg({'Rushing_Yds':'sum'}).reset_index().sort_values(['year_week','Rushing_Yds'], ascending=[True, False])

    receiving_def = pd.merge(receiving, completed_games_sub, how='inner', left_on=['year_week','Real_Team'], right_on=['year_week','opponent_team'])
    receiving_def['team_category'] = 'Defense ' + receiving_def['searched_team']
    receiving_off = pd.merge(receiving, completed_games_sub, how='inner', left_on=['year_week','Real_Team'], right_on=['year_week','searched_team'])
    receiving_off['team_category'] = 'Offense ' + receiving_off['searched_team']
    receiving_past = pd.concat([receiving_off, receiving_def], axis=0)
    receiving_awayteam = receiving_past[receiving_past['team_category'].isin(['Offense ' + away_team, 'Defense ' + home_team])]
    receiving_hometeam = receiving_past[receiving_past['team_category'].isin(['Offense ' + home_team, 'Defense ' + away_team])]
    total_rec_away = receiving_awayteam.groupby(['year_week','Player','team_category']).agg({'Receiving_Yds':'sum'}).reset_index().sort_values(['year_week','Receiving_Yds'], ascending=[True, False])
    total_rec_home = receiving_hometeam.groupby(['year_week','Player','team_category']).agg({'Receiving_Yds':'sum'}).reset_index().sort_values(['year_week','Receiving_Yds'], ascending=[True, False])

    # basic header metrics and logos
    othercols = st.columns([3.5,1.6,1.5,1.2,1,1.5,3])
    event_date = upcoming_games.loc[upcoming_games['Game'] == game, 'event_date']
    formatted_event = 'TBD'
    if not event_date.empty:
        try:
            formatted_event = datetime.strptime(event_date.values[0], '%Y-%m-%d').strftime('%B %d, %Y')
        except Exception:
            formatted_event = str(event_date.values[0])
    with othercols[0]:
        st.metric('', formatted_event)

    # avg scores metrics
    away_score = round(avg_scores.loc[avg_scores['searched_team'] == away_team, 'team_score'].values[0], 1) if not avg_scores[avg_scores['searched_team'] == away_team].empty else np.nan
    home_score = round(avg_scores.loc[avg_scores['searched_team'] == home_team, 'team_score'].values[0], 1) if not avg_scores[avg_scores['searched_team'] == home_team].empty else np.nan
    with othercols[1]:
        away_score_against = round(avg_scores.loc[avg_scores['searched_team'] == away_team, 'opponent_score'].values[0], 1) if not avg_scores[avg_scores['searched_team'] == away_team].empty else np.nan
        away_vs = away_score - away_score_against if (not np.isnan(away_score) and not np.isnan(away_score_against)) else np.nan
        away_vs = round(away_vs, 1)
        st.metric("Average Score (Away)", away_score, f"{away_vs}, Avg Differential")
    with othercols[2]:
        # show away logo & record
        away_svg = away_team.lower().replace(' ', '-') + '-logo.svg'
        away_svg_path = os.path.join(logo_path, away_svg)
        svg_content = ''
        try:
            with open(away_svg_path, 'r') as f:
                svg_content = f.read().replace('width="700"', 'width="100"').replace('height="400"', 'height="100"')
        except Exception:
            svg_content = ''
        if svg_content:
            st.markdown(f'''<div style="width: 75px; height: 75px; display:flex; align-items:center; justify-content:center;">{svg_content}</div>''', unsafe_allow_html=True)
        away_wins = completed_scores[(completed_scores['WinLoss']=='Win') & (completed_scores['searched_team']==away_team)]['year_week'].count()
        away_losses = completed_scores[(completed_scores['WinLoss']=='Loss') & (completed_scores['searched_team']==away_team)]['year_week'].count()
        away_record = str(away_wins) + "-" + str(away_losses)
        st.markdown(f'''<div style="width: 75px; height: 10px;  justify-content: center;text-align: center;">{away_record}</div>''', unsafe_allow_html=True)

    with othercols[3]:
        st.metric('', "@")
    with othercols[4]:
        home_svg = home_team.lower().replace(' ', '-') + '-logo.svg'
        home_svg_path = os.path.join(logo_path, home_svg)
        svg_content = ''
        try:
            with open(home_svg_path, 'r') as f:
                svg_content = f.read().replace('width="700"', 'width="100"').replace('height="400"', 'height="100"')
        except Exception:
            svg_content = ''
        if svg_content:
            st.markdown(f'''<div style="width: 75px; height: 75px; display:flex; align-items:center; justify-content:center;">{svg_content}</div>''', unsafe_allow_html=True)
        home_wins = completed_scores[(completed_scores['WinLoss']=='Win') & (completed_scores['searched_team']==home_team)]['year_week'].count()
        home_losses = completed_scores[(completed_scores['WinLoss']=='Loss') & (completed_scores['searched_team']==home_team)]['year_week'].count()
        home_record = str(home_wins) + "-" + str(home_losses)
        st.markdown(f'''<div style="width: 75px; height: 10px;  justify-content: center;text-align: center;">{home_record}</div>''', unsafe_allow_html=True)

    with othercols[5]:
        home_vs = (home_score - (round(avg_scores.loc[avg_scores['searched_team'] == home_team, 'opponent_score'].values[0],1) if not avg_scores[avg_scores['searched_team'] == home_team].empty else 0))
        st.metric("Average Score (Home)", home_score, f"{home_vs}, Avg Differential")

    st.markdown("---")
    # st.subheader("Player breakdown charts (Passing, Rushing, Receiving) per week")

    # use colors extracted from color_df if present
    def team_color(team_name, fallback):
        try:
            return color_df[color_df['NFL Team Name'] == team_name]['Color 1'].values[0]
        except Exception:
            return fallback

    top_team_color_left = team_color(away_team, '#1f77b4')
    bottom_team_color_left = team_color(home_team, '#d62728')
    top_team_color_right = team_color(home_team, '#1f77b4')
    bottom_team_color_right = team_color(away_team, '#d62728')

#########################################
    up_col1 , up_col2 , up_col3, up_col4 = st.columns([1, 5, 5, 1])

    max_pass_value = passing_past.groupby(['year_week','team_category']).sum()['Passing_Yds'].max()
    pass_limit = round(max_pass_value / 50) * 50
    max_rush_value = rushing_past.groupby(['year_week','team_category']).sum()['Rushing_Yds'].max()
    rush_limit = round(max_rush_value / 50) * 50
    max_rec_value = receiving_past.groupby(['year_week','team_category']).sum()['Receiving_Yds'].max()
    rec_limit = round(max_rec_value / 50) * 50
    chart_ht = 200
    with up_col1:
        away_top_pass = passing_awayteam[passing_awayteam['searched_team']==away_team]
        away_top_pass_qb = away_top_pass.groupby(['Player']).agg({'Season_Passing_Yds': 'max'})
        away_top_pass_qb = away_top_pass_qb.reset_index().sort_values('Season_Passing_Yds', ascending=False)['Player'].values[0]
        away_top_pass_avg = away_top_pass[away_top_pass['Player']==away_top_pass_qb].groupby(['Player']).agg({'Passing_Yds': 'mean'}).reset_index()['Passing_Yds'].values[0]
        away_top_pass_avg = round(away_top_pass_avg,1)
        latest_away_year_week = away_top_pass.sort_values('year_week',ascending=False)['year_week'].values[0]
        away_last_week_pass_yds = away_top_pass.loc[(away_top_pass['Player']==away_top_pass_qb) & (away_top_pass['year_week']==latest_away_year_week),'Passing_Yds']
        if not away_last_week_pass_yds.empty:
            away_last_week_pass_yds = away_last_week_pass_yds.values[0]
        else:
            away_last_week_pass_yds = 0
        away_pass_yds_diff = round(away_last_week_pass_yds - away_top_pass_avg,1)
        st.write("Top Passer")
        st.metric(away_top_pass_qb,away_top_pass_avg,f"{away_pass_yds_diff} Trending")

        st.write("")
        st.write("")
        st.write("")
        st.write("")
        st.write("")
        st.write("")

        away_top_rush = rushing_awayteam[rushing_awayteam['searched_team']==away_team]
        away_top_rush_rb = away_top_rush.groupby(['Player']).agg({'Season_Rushing_Yds': 'max'})
        away_top_rush_rb = away_top_rush_rb.reset_index().sort_values('Season_Rushing_Yds', ascending=False)['Player'].values[0]
        away_top_rush_avg = away_top_rush[away_top_rush['Player']==away_top_rush_rb].groupby(['Player']).agg({'Rushing_Yds': 'mean'}).reset_index()['Rushing_Yds'].values[0]
        away_top_rush_avg = round(away_top_rush_avg,1)
        away_last_week_rush_yds = away_top_rush.loc[(away_top_rush['Player']==away_top_rush_rb) & (away_top_rush['year_week']==latest_away_year_week),'Rushing_Yds']
        if not away_last_week_rush_yds.empty:
            away_last_week_rush_yds = away_last_week_rush_yds.values[0]
        else:
            away_last_week_rush_yds = 0

        away_rush_yds_diff = round(away_last_week_rush_yds - away_top_rush_avg,1)
        st.write("Top Rusher")
        st.metric(away_top_rush_rb,away_top_rush_avg,f"{away_rush_yds_diff} Trending")

        st.write("")
        st.write("")
        st.write("")
        st.write("")
        st.write("")
        st.write("")

        away_top_rec = receiving_awayteam[receiving_awayteam['searched_team']==away_team]
        away_top_rec_wr = away_top_rec.groupby(['Player']).agg({'Season_Receiving_Yds': 'max'})
        away_top_rec_wr = away_top_rec_wr.reset_index().sort_values('Season_Receiving_Yds', ascending=False)['Player'].values[0]
        away_top_rec_avg = away_top_rec[away_top_rec['Player']==away_top_rec_wr].groupby(['Player']).agg({'Receiving_Yds': 'mean'}).reset_index()['Receiving_Yds'].values[0]
        away_top_rec_avg = round(away_top_rec_avg,1)
        away_last_week_rec_yds = away_top_rec.loc[(away_top_rec['Player']==away_top_rec_wr) & (away_top_rec['year_week']==latest_away_year_week),'Receiving_Yds']
        if not away_last_week_rec_yds.empty:
            away_last_week_rec_yds = away_last_week_rec_yds.values[0]
        else:
            away_last_week_rec_yds = 0
        away_rec_yds_diff = round(away_last_week_rec_yds - away_top_rec_avg,1)
        st.write("Top Receiver")
        st.metric(away_top_rec_wr,away_top_rec_avg,f"{away_rec_yds_diff} Trending")

#######################################################3
    # show three charts in center (passing, rushing, receiving) for away team
    with up_col2:
        if not total_passing_away.empty:
            player_breakdown_passing_away = alt.Chart(total_passing_away).mark_bar().encode(
                x=alt.X('year_week:O', axis=alt.Axis(title=None)),
                y=alt.Y('Passing_Yds:Q', scale=alt.Scale(domain=[0, total_passing_away['Passing_Yds'].max()])),
                xOffset=alt.XOffset('team_category:N', sort='descending'),
                color=alt.Color('team_category:N', scale=alt.Scale(range=[top_team_color_left, bottom_team_color_left]), title=None),
                opacity=alt.Opacity('Passing_Yds:Q', scale=alt.Scale(domain=[0, total_passing_away['Passing_Yds'].max()], range=[0.3, 1]), legend=None),
                tooltip=['Player:N','Passing_Yds:Q','year_week:O']
            ).properties(title='Player Passing Yards per Week', height=chart_ht)
            st.altair_chart(player_breakdown_passing_away, use_container_width=True)

        if not total_rushing_away.empty:
            player_breakdown_rushing_away = alt.Chart(total_rushing_away).mark_bar().encode(
                x=alt.X('year_week:O', axis=alt.Axis(title=None)),
                y=alt.Y('Rushing_Yds:Q', scale=alt.Scale(domain=[0, total_rushing_away['Rushing_Yds'].max()])),
                xOffset=alt.XOffset('team_category:N', sort='descending'),
                color=alt.Color('team_category:N', scale=alt.Scale(range=[top_team_color_left, bottom_team_color_left]), title=None),
                opacity=alt.Opacity('Rushing_Yds:Q', scale=alt.Scale(domain=[0, total_rushing_away['Rushing_Yds'].max()], range=[0.3, 1]), legend=None),
                tooltip=['Player:N','Rushing_Yds:Q','year_week:O']
            ).properties(title='Player Rushing Yards per Week', height=chart_ht)
            st.altair_chart(player_breakdown_rushing_away, use_container_width=True)

        if not total_rec_away.empty:
            player_breakdown_receiving_away = alt.Chart(total_rec_away).mark_bar().encode(
                x=alt.X('year_week:O', axis=alt.Axis(title=None)),
                y=alt.Y('Receiving_Yds:Q', scale=alt.Scale(domain=[0, total_rec_away['Receiving_Yds'].max()])),
                xOffset=alt.XOffset('team_category:N', sort='descending'),
                color=alt.Color('team_category:N', scale=alt.Scale(range=[top_team_color_left, bottom_team_color_left]), title=None),
                opacity=alt.Opacity('Receiving_Yds:Q', scale=alt.Scale(domain=[0, total_rec_away['Receiving_Yds'].max()], range=[0.3, 1]), legend=None),
                tooltip=['Player:N','Receiving_Yds:Q','year_week:O']
            ).properties(title='Player Receiving Yards per Week', height=chart_ht)
            st.altair_chart(player_breakdown_receiving_away, use_container_width=True)

    with up_col3:
        if not total_passing_home.empty:
            player_breakdown_passing_home = alt.Chart(total_passing_home).mark_bar().encode(
                x=alt.X('year_week:O', axis=alt.Axis(title=None)),
                y=alt.Y('Passing_Yds:Q', scale=alt.Scale(domain=[0, total_passing_home['Passing_Yds'].max()])),
                xOffset=alt.XOffset('team_category:N', sort='descending'),
                color=alt.Color('team_category:N', scale=alt.Scale(range=[top_team_color_right, bottom_team_color_right]), title=None),
                opacity=alt.Opacity('Passing_Yds:Q', scale=alt.Scale(domain=[0, total_passing_home['Passing_Yds'].max()], range=[0.3, 1]), legend=None),
                tooltip=['Player:N','Passing_Yds:Q','year_week:O']
            ).properties(title='Player Passing Yards per Week', height=chart_ht)
            st.altair_chart(player_breakdown_passing_home, use_container_width=True)

        if not total_rushing_home.empty:
            player_breakdown_rushing_home = alt.Chart(total_rushing_home).mark_bar().encode(
                x=alt.X('year_week:O', axis=alt.Axis(title=None)),
                y=alt.Y('Rushing_Yds:Q', scale=alt.Scale(domain=[0, total_rushing_home['Rushing_Yds'].max()])),
                xOffset=alt.XOffset('team_category:N', sort='descending'),
                color=alt.Color('team_category:N', scale=alt.Scale(range=[top_team_color_right, bottom_team_color_right]), title=None),
                opacity=alt.Opacity('Rushing_Yds:Q', scale=alt.Scale(domain=[0, total_rushing_home['Rushing_Yds'].max()], range=[0.3, 1]), legend=None),
                tooltip=['Player:N','Rushing_Yds:Q','year_week:O']
            ).properties(title='Player Rushing Yards per Week', height=chart_ht)
            st.altair_chart(player_breakdown_rushing_home, use_container_width=True)

        if not total_rec_home.empty:
            player_breakdown_receiving_home = alt.Chart(total_rec_home).mark_bar().encode(
                x=alt.X('year_week:O', axis=alt.Axis(title=None)),
                y=alt.Y('Receiving_Yds:Q', scale=alt.Scale(domain=[0, total_rec_home['Receiving_Yds'].max()])),
                xOffset=alt.XOffset('team_category:N', sort='descending'),
                color=alt.Color('team_category:N', scale=alt.Scale(range=[top_team_color_right, bottom_team_color_right]), title=None),
                opacity=alt.Opacity('Receiving_Yds:Q', scale=alt.Scale(domain=[0, total_rec_home['Receiving_Yds'].max()], range=[0.3, 1]), legend=None),
                tooltip=['Player:N','Receiving_Yds:Q','year_week:O']
            ).properties(title='Player Receiving Yards per Week', height=chart_ht)
            st.altair_chart(player_breakdown_receiving_home, use_container_width=True)

    with up_col4:
        home_top_pass = passing_hometeam[passing_hometeam['searched_team']==home_team]
        home_top_pass_qb = home_top_pass.groupby(['Player']).agg({'Season_Passing_Yds': 'max'})
        home_top_pass_qb = home_top_pass.reset_index().sort_values('Season_Passing_Yds', ascending=False)['Player'].values[0]
        home_top_pass_avg = home_top_pass[home_top_pass['Player']==home_top_pass_qb].groupby(['Player']).agg({'Passing_Yds': 'mean'}).reset_index()['Passing_Yds'].values[0]
        home_top_pass_avg = round(home_top_pass_avg,1)
        latest_home_year_week = home_top_pass.sort_values('year_week',ascending=False)['year_week'].values[0]
        home_last_week_pass_yds = home_top_pass.loc[(home_top_pass['Player']==home_top_pass_qb) & (home_top_pass['year_week']==latest_home_year_week),'Passing_Yds']
        if not home_last_week_pass_yds.empty:
            home_last_week_pass_yds = home_last_week_pass_yds.values[0]
        else:
            home_last_week_pass_yds = 0
        home_pass_yds_diff = round(home_last_week_pass_yds - home_top_pass_avg,1)
        st.write("Top Passer")
        st.metric(home_top_pass_qb,home_top_pass_avg,f"{home_pass_yds_diff} Trending")

        st.write("")
        st.write("")
        st.write("")
        st.write("")
        st.write("")
        st.write("")

        home_top_rush = rushing_hometeam[rushing_hometeam['searched_team']==home_team]
        home_top_rush_rb = home_top_rush.groupby(['Player']).agg({'Season_Rushing_Yds': 'max'})
        home_top_rush_rb = home_top_rush_rb.reset_index().sort_values('Season_Rushing_Yds', ascending=False)['Player'].values[0]
        home_top_rush_avg = home_top_rush[home_top_rush['Player']==home_top_rush_rb].groupby(['Player']).agg({'Rushing_Yds': 'mean'}).reset_index()['Rushing_Yds'].values[0]
        home_top_rush_avg = round(home_top_rush_avg,1)
        home_last_week_rush_yds = home_top_rush.loc[(home_top_rush['Player']==home_top_rush_rb) & (home_top_rush['year_week']==latest_home_year_week),'Rushing_Yds']
        if not home_last_week_rush_yds.empty:
            home_last_week_rush_yds = home_last_week_rush_yds.values[0]
        else:
            home_last_week_rush_yds = 0

        home_rush_yds_diff = round(home_last_week_rush_yds - home_top_rush_avg,1)
        st.write("Top Rusher")
        st.metric(home_top_rush_rb,home_top_rush_avg,f"{home_rush_yds_diff} Trending")

        st.write("")
        st.write("")
        st.write("")
        st.write("")
        st.write("")
        st.write("")

        home_top_rec = receiving_hometeam[receiving_hometeam['searched_team']==home_team]
        home_top_rec_wr = home_top_rec.groupby(['Player']).agg({'Season_Receiving_Yds': 'max'})
        home_top_rec_wr = home_top_rec_wr.reset_index().sort_values('Season_Receiving_Yds', ascending=False)['Player'].values[0]
        home_top_rec_avg = home_top_rec[home_top_rec['Player']==home_top_rec_wr].groupby(['Player']).agg({'Receiving_Yds': 'mean'}).reset_index()['Receiving_Yds'].values[0]
        home_top_rec_avg = round(home_top_rec_avg,1)
        home_last_week_rec_yds = home_top_rec.loc[(home_top_rec['Player']==home_top_rec_wr) & (home_top_rec['year_week']==latest_home_year_week),'Receiving_Yds']
        if not home_last_week_rec_yds.empty:
            home_last_week_rec_yds = home_last_week_rec_yds.values[0]
        else:
            home_last_week_rec_yds = 0
        home_rec_yds_diff = round(home_last_week_rec_yds - home_top_rec_avg,1)
        st.write("Top Receiver")
        st.metric(home_top_rec_wr,home_top_rec_avg,f"{home_rec_yds_diff} Trending")

    # st.success("Upcoming Games loaded.")
