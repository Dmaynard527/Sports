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

    def combine_info(df, yard_type):
        defense = pd.merge(df, completed_games_sub, how='inner', left_on=['year_week','Real_Team'], right_on=['year_week','opponent_team'])
        defense['team_category'] = 'Defense ' + defense['searched_team']
        offense = pd.merge(df, completed_games_sub, how='inner', left_on=['year_week','Real_Team'], right_on=['year_week','searched_team'])
        offense['team_category'] = 'Offense ' + offense['searched_team']
        past = pd.concat([offense, defense], axis=0)

        df_awayteam = past[past['team_category'].isin(['Offense ' + away_team, 'Defense ' + home_team])]
        df_hometeam = past[past['team_category'].isin(['Offense ' + home_team, 'Defense ' + away_team])]

        total_df_away = df_awayteam.groupby(['year_week','Player','team_category']).agg({f'{yard_type}':'sum'}).reset_index().sort_values(['year_week',f'{yard_type}'], ascending=[True, False])
        total_df_home = df_hometeam.groupby(['year_week','Player','team_category']).agg({f'{yard_type}':'sum'}).reset_index().sort_values(['year_week',f'{yard_type}'], ascending=[True, False])
        
        return defense, offense, past, df_awayteam, df_hometeam, total_df_away, total_df_home

    passing_def, passing_off, passing_past, passing_awayteam, passing_hometeam, total_passing_away, total_passing_home = combine_info(passing, 'Passing_Yds')
    rushing_def, rushing_off, rushing_past, rushing_awayteam, rushing_hometeam, total_rushing_away, total_rushing_home = combine_info(rushing, 'Rushing_Yds')
    receiving_def, receiving_off, receiving_past, receiving_awayteam, receiving_hometeam, total_rec_away, total_rec_home = combine_info(receiving, 'Receiving_Yds')

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
    chart_ht = 225

    def team_metrics(df_team, df_type_team, yard_type, title):
        season_yard_type = 'Season_' + yard_type
        top = df_type_team[df_type_team['searched_team']==df_team]
        top_type = top.groupby(['Player']).agg({f'{season_yard_type}': 'max'})
        top_type = top_type.reset_index().sort_values(f'{season_yard_type}', ascending=False)['Player'].values[0]
        top_type_avg = top[top['Player']==top_type].groupby(['Player']).agg({f'{yard_type}': 'mean'}).reset_index()[f'{yard_type}'].values[0]
        top_type_avg = round(top_type_avg,1)
        latest_year_week = top.sort_values('year_week',ascending=False)['year_week'].values[0]
        last_week_type_yds = top.loc[(top['Player']==top_type) & (top['year_week']==latest_year_week),f'{yard_type}']
        if not last_week_type_yds.empty:
            last_week_type_yds = last_week_type_yds.values[0]
        else:
            last_week_type_yds = 0
        type_yds_diff = round(last_week_type_yds - top_type_avg,1)
        st.write(f"Top {title}")
        st.metric(top_type,top_type_avg,f"{type_yds_diff} Trending")

        st.write("")
        st.write("")
        st.write("")
        st.write("")
        st.write("")
        st.write("")

        return top, top_type, top_type_avg, last_week_type_yds, type_yds_diff
    
    def player_breakdown(total_type, yard_type, type_limit, top_team_color, bottom_team_color, orientation):
        title = 'Player ' + yard_type[:-4] + ' Yards per Week'

        if not total_type.empty:
            player_breakdown_type = alt.Chart(total_type).mark_bar().encode(
                x=alt.X('year_week:O', axis=alt.Axis(title=None)),
                y=alt.Y(f'{yard_type}:Q', scale=alt.Scale(domain=[0, type_limit])),
                xOffset=alt.XOffset('team_category:N', sort='descending'),
                color=alt.Color('team_category:N', scale=alt.Scale(range=[top_team_color, bottom_team_color]), sort=alt.EncodingSortField(field='team_category', order='descending'),title=None),
                opacity=alt.Opacity(f'{yard_type}:Q', scale=alt.Scale(domain=[0, total_type[f'{yard_type}'].max()], range=[0.3, 1]), legend=None),
                tooltip=['Player:N',f'{yard_type}:Q','year_week:O']
            ).properties(title=f'{title}', height=chart_ht
            ).configure_legend(
                orient=orientation  # Position the legend on the left
            )
            st.altair_chart(player_breakdown_type, use_container_width=True)

            return player_breakdown_type

    # show trends for away team (passing, rushing, receiving)
    with up_col1:
        away_top_pass, away_top_pass_qb, away_top_pass_avg, away_last_week_pass_yds, away_pass_yds_diff = team_metrics(away_team, passing_awayteam, "Passing_Yds", "Passer")
        away_top_rush, away_top_rush_rb, away_top_rush_avg, away_last_week_rush_yds, away_rush_yds_diff = team_metrics(away_team, rushing_awayteam, "Rushing_Yds", "Rusher")
        away_top_rec, away_top_rec_wr, away_top_rec_avg, away_last_week_rec_yds, away_rec_yds_diff = team_metrics(away_team, receiving_awayteam, "Receiving_Yds", "Receiver")

    # show three charts in center (passing, rushing, receiving) for away team
    with up_col2:
        player_breakdown_passing_away = player_breakdown(total_passing_away, "Passing_Yds", pass_limit, top_team_color_left, bottom_team_color_left, "left")
        player_breakdown_rushing_away = player_breakdown(total_rushing_away, "Rushing_Yds", rush_limit, top_team_color_left, bottom_team_color_left, "left")
        player_breakdown_receiving_away = player_breakdown(total_rec_away, "Receiving_Yds", rec_limit, top_team_color_left, bottom_team_color_left, "left")

    # show three charts in center (passing, rushing, receiving) for home team
    with up_col3:
        player_breakdown_passing_home = player_breakdown(total_passing_home, "Passing_Yds", pass_limit, top_team_color_right, bottom_team_color_right, "right")
        player_breakdown_rushing_home = player_breakdown(total_rushing_home, "Rushing_Yds", rush_limit, top_team_color_right, bottom_team_color_right, "right")
        player_breakdown_receiving_home = player_breakdown(total_rec_home, "Receiving_Yds", rec_limit, top_team_color_right, bottom_team_color_right, "right")

    # show trends for home team (passing, rushing, receiving)
    with up_col4:
        home_top_pass, home_top_pass_qb, home_top_pass_avg, home_last_week_pass_yds, home_pass_yds_diff = team_metrics(home_team, passing_hometeam, "Passing_Yds", "Passer")
        home_top_rush, home_top_rush_rb, home_top_rush_avg, home_last_week_rush_yds, home_rush_yds_diff = team_metrics(home_team, rushing_hometeam, "Rushing_Yds", "Rusher")
        home_top_rec, home_top_rec_wr, home_top_rec_avg, home_last_week_rec_yds, home_rec_yds_diff = team_metrics(home_team, receiving_hometeam, "Receiving_Yds", "Receiver")

    st.success("Upcoming Games loaded.")
