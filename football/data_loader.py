# data_loader.py
import os
import pandas as pd
import numpy as np
from datetime import datetime
from utils import real_teams, reversed_real_teams

def _read_player_files(data_path):
    files = sorted([f for f in os.listdir(data_path) if f.lower().endswith('.csv')])
    df = pd.DataFrame()
    for file in files:
        fp = os.path.join(data_path, file)
        new_file = pd.read_csv(fp)
        if 'week' in new_file.columns:
            new_file['week_padded'] = new_file['week'].apply(lambda x: f'{int(x):02d}')
        else:
            new_file['week_padded'] = new_file.get('week_padded', '')
        new_file['year'] = file[:4]
        df = pd.concat([df, new_file], axis=0, ignore_index=True)
    return df

def load_data():
    path = os.getcwd()
    data_path = os.path.join(path, 'data')
    upcoming_path = os.path.join(path, 'games')
    metadata_path = os.path.join(path, 'metadata')
    logo_path = os.path.join(path, 'logo')

    # year logic (same as original)
    current_date = datetime.now()
    year = current_date.year
    month = current_date.month
    if 3 <= month <= 5:
        new_year = year + 1
    else:
        new_year = year - 1

    # read player files
    df = _read_player_files(data_path)

    # upcoming/completed games (safe load)
    upcoming_games = pd.DataFrame()
    completed_games = pd.DataFrame()
    upcoming_games_fp = os.path.join(upcoming_path, f'upcoming_games_{new_year}.csv')
    completed_games_fp = os.path.join(upcoming_path, f'completed_games_{new_year}.csv')
    if os.path.exists(upcoming_games_fp):
        upcoming_games = pd.read_csv(upcoming_games_fp)
    if os.path.exists(completed_games_fp):
        completed_games = pd.read_csv(completed_games_fp)

    # normalize Football Team -> Commanders (same as original)
    for gdf in [upcoming_games, completed_games]:
        if not gdf.empty:
            if 'opp_name' in gdf.columns:
                gdf['opp_name'] = gdf['opp_name'].str.replace('Football Team', 'Commanders')
            if 'tm_name' in gdf.columns:
                gdf['tm_name'] = gdf['tm_name'].str.replace('Football Team', 'Commanders')

    # metadata
    color_df = pd.DataFrame()
    location_df = pd.DataFrame()
    team_colors_fp = os.path.join(metadata_path, 'team_colors.csv')
    team_location_fp = os.path.join(metadata_path, 'team_location.csv')
    if os.path.exists(team_colors_fp):
        color_df = pd.read_csv(team_colors_fp)
    if os.path.exists(team_location_fp):
        location_df = pd.read_csv(team_location_fp)
        if 'logo' in location_df.columns:
            location_df['logo_path'] = location_df['logo'].apply(lambda n: os.path.join(logo_path, n))
        location_df['city_team'] = location_df.get('City', '') + ' ' + location_df.get('Team', '')

    # build derived fields exactly like original
    if 'week_padded' in df.columns and 'year' in df.columns:
        df['year_week'] = df['year'].astype(str) + '_' + df['week_padded'].astype(str)
    # safety: treat missing numeric columns as zero for arithmetic
    for col in ['Passing_Yds','Rushing_Yds','Receiving_Yds','Rushing_TD','Receiving_TD','Receiving_Tgt','Receiving_Rec']:
        if col not in df.columns:
            df[col] = 0

    df['Passing_Rushing_Yds'] = df['Passing_Yds'] + df['Rushing_Yds']
    df['Rushing_Receiving_Yds'] = df['Rushing_Yds'] + df['Receiving_Yds']
    df['Passing_Rushing_Receiving_Yds'] = df['Passing_Yds'] + df['Rushing_Yds'] + df['Receiving_Yds']
    df['Rushing_Receiving_TD'] = df['Rushing_TD'] + df['Receiving_TD']
    df['Targets_not_caught'] = df['Receiving_Tgt'] - df['Receiving_Rec']

    # map to real team names
    if 'Team' in df.columns:
        df['Real_Team'] = df['Team'].map(real_teams)
    else:
        df['Real_Team'] = df.get('Real_Team', np.nan)

    # games formatting
    if not completed_games.empty:
        completed_games['year_week'] = completed_games['season'].astype(str) + '_' + completed_games['week'].apply(lambda x: f'{int(x):02d}')
        completed_games['team1'] = completed_games['tm_market'] + ' ' + completed_games['tm_name']
        completed_games['team2'] = completed_games['opp_market'] + ' ' + completed_games['opp_name']

    if not upcoming_games.empty:
        upcoming_games['Away_Team'] = upcoming_games['tm_market'] + ' ' + upcoming_games['tm_name']
        upcoming_games['Home_Team'] = upcoming_games['opp_market'] + ' ' + upcoming_games['opp_name']
        upcoming_games['Game'] = upcoming_games['Away_Team'] + ' @ ' + upcoming_games['Home_Team']

    # season aggregates used across pages
    try:
        df_aggregates = df.groupby(['Player','year']).sum().reset_index()
        df_aggregates = df_aggregates[['Player','Team','year','Passing_Yds','Rushing_Yds','Receiving_Yds']]
        df_aggregates = df_aggregates.rename({'Passing_Yds':'Season_Passing_Yds',
                                              'Rushing_Yds':'Season_Rushing_Yds',
                                              'Receiving_Yds':'Season_Receiving_Yds'}, axis=1)
        df_aggregates['Team'] = df_aggregates['Team'].astype(str)
        df = pd.merge(df, df_aggregates, how='left', on=['Team','year','Player'])
    except Exception:
        pass

    try:
        df_total = df.groupby(['Player','Team']).sum().reset_index()
        df_total = df_total[['Player','Team','Passing_Yds','Rushing_Yds','Receiving_Yds']]
        df_total = df_total.rename({'Passing_Yds':'Total_Passing_Yds',
                                    'Rushing_Yds':'Total_Rushing_Yds',
                                    'Receiving_Yds':'Total_Receiving_Yds'}, axis=1)
        df_total['Team'] = df_total['Team'].astype(str)
        df = pd.merge(df, df_total, how='left', on=['Team','Player'])
    except Exception:
        pass

    # categorize players
    df['Player_Category'] = 'Receiver'
    df.loc[(df['Total_Passing_Yds'] > df['Total_Rushing_Yds']) & (df['Total_Passing_Yds'] > df['Total_Receiving_Yds']), 'Player_Category'] = 'Quarterback'
    df.loc[(df['Total_Rushing_Yds'] > df['Total_Passing_Yds']) & (df['Total_Rushing_Yds'] > df['Total_Receiving_Yds']), 'Player_Category'] = 'Running Back'

    # build team list
    teams = sorted(list(df['Real_Team'].dropna().unique()))

    return {
        "df": df,
        "upcoming_games": upcoming_games,
        "completed_games": completed_games,
        "color_df": color_df,
        "location_df": location_df,
        "teams": teams,
        "current_year": new_year,
        "path": path,
        "logo_path": logo_path
    }
