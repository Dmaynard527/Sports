import pandas as pd
import numpy as np
import streamlit as st
import os
import altair as alt
import seaborn as sns
from datetime import datetime
import matplotlib.pyplot as plt
import streamlit as st
import folium
from streamlit_folium import st_folium
import plotly.express as px

# Functions


def target_lines(input_value,perc_of_games):
    target_line = alt.Chart(pd.DataFrame({'y': [input_value], 'label': [f'Target: {input_value}, {perc_of_games} of games']})).mark_rule(color='purple').encode(
                y='y:Q'
            ).properties(
                title='Target:'
            )
    target_label = target_line.mark_text(
            align='right',
            baseline='middle',
            dx=-140,
            dy=-10,
        ).encode(
            text='label:N',
            size=alt.value(16)
        )
    return target_line, target_label
# Function to highlight rows where NFL_Team matches the selected team
def highlight_team(row):
    color = f'background-color: yellow' if row['NFL_Team'] == team_selected else ''
    return [color] * len(row)

# grab current date
current_date = datetime.now()
year = current_date.year
month = current_date.month

# If current month is between January and May (inclusive), add 1 to the year
if 1 <= month <= 5:
    new_year = year + 1
else:
    new_year = year

# process files
### Configuration setup
st.set_page_config(layout="wide")
path = os.getcwd()
data_path = os.path.join(path, 'data/')
upcoming_path = os.path.join(path, 'games/')
upcoming_games_path = os.path.join(upcoming_path, f'upcoming_games_{new_year}.csv')
completed_games_path = os.path.join(upcoming_path, f'completed_games_{new_year}.csv')
metadata_path = os.path.join(path, 'metadata/')
files = os.listdir(data_path)
df = pd.DataFrame()
for file in files:
    new_file = pd.read_csv(data_path + file)
    new_file['week_padded'] = new_file['week'].apply(lambda x: f'{x:02d}') 
    new_file['year'] = file[:4]
    df = pd.concat([df,new_file],axis=0)


### GAMES
upcoming_games = pd.read_csv(upcoming_games_path)
completed_games = pd.read_csv(completed_games_path)
completed_games['opp_name'] = completed_games['opp_name'].str.replace('Football Team','Commanders')
completed_games['tm_name'] = completed_games['tm_name'].str.replace('Football Team','Commanders')
completed_games['year_week'] = completed_games['season'].astype(str) + '_' + completed_games['week'].apply(lambda x: f'{x:02d}') 
completed_games['team1'] = completed_games['tm_market'] + ' ' + completed_games['tm_name']
completed_games['team2'] = completed_games['opp_market'] + ' ' + completed_games['opp_name']

### TEAM COLORS
team_colors = os.path.join(metadata_path, 'team_colors.csv')
color_df = pd.read_csv(team_colors)

### TEAM LOCATION
team_location = os.path.join(metadata_path, 'team_location.csv')
location_df = pd.read_csv(team_location)
logo_path = os.path.join(path, 'logo')
location_df['logo_path'] = location_df['logo'].apply(lambda row: os.path.join(logo_path, row))
location_df['city_team'] = location_df['City'] + ' ' + location_df['Team']

# Create a Folium map
m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)

# Add markers with custom icons (local SVG logos)
for index,loc in location_df.iterrows():
    icon = folium.CustomIcon(loc["logo_path"], icon_size=(50, 50))
    folium.Marker(
        location=[loc["latitude"], loc["longitude"]],
        icon=icon,
        popup=loc['city_team']
    ).add_to(m)

# # Display the map and capture the map data
# returned_map_data = st_folium(m, width=1800, height=600)

### Dataframe changes

# year_week
df['year_week'] =df['year'] + '_' + df['week_padded'].astype(str)
# add additional fields
df['Passing_Rushing_Yds'] = df['Passing_Yds'] + df['Rushing_Yds']
df['Rushing_Receiving_Yds'] = df['Rushing_Yds'] + df['Receiving_Yds']
df['Passing_Rushing_Receiving_Yds'] = df['Passing_Yds'] + df['Rushing_Yds'] + df['Receiving_Yds']
df['Rushing_Receiving_TD'] = df['Rushing_TD'] + df['Receiving_TD']
df['Targets_not_caught'] = df['Receiving_Tgt'] - df['Receiving_Rec']

### ADD REAL TEAM NAME ###
real_teams = {
    'ARI':'Arizona Cardinals',
    'ATL':'Atlanta Falcons',
    'BAL':'Baltimore Ravens',
    'BUF':'Buffalo Bills',
    'CAR':'Carolina Panthers',
    'CHI':'Chicago Bears',
    'CIN':'Cincinnati Bengals',
    'CLE':'Cleveland Browns',
    'DAL':'Dallas Cowboys',
    'DEN':'Denver Broncos',
    'DET':'Detroit Lions',
    'GNB':'Green Bay Packers',
    'HOU':'Houston Texans',
    'IND':'Indianapolis Colts',
    'JAX':'Jacksonville Jaguars',
    'KAN':'Kansas City Chiefs',
    'LAC':'Los Angeles Chargers',
    'LAR':'Los Angeles Rams',
    'LVR':'Las Vegas Raiders',
    'MIA':'Miami Dolphins',
    'MIN':'Minnesota Vikings',
    'NOR':'New Orleans Saints',
    'NWE':'New England Patriots',
    'NYG':'New York Giants',
    'NYJ':'New York Jets',
    'OAK':'Las Vegas Raiders',
    'PHI':'Philadelphia Eagles',
    'PIT':'Pittsburgh Steelers',
    'SEA':'Seattle Seahawks',
    'SFO':'San Francisco 49ers',
    'TAM':'Tampa Bay Buccaneers',
    'TEN':'Tennessee Titans',
    'WAS':'Washington Commanders'}
df['Real_Team'] = df['Team'].map(real_teams)
upcoming_games['opp_name'] = upcoming_games['opp_name'].str.replace('Football Team','Commanders')
upcoming_games['tm_name'] = upcoming_games['tm_name'].str.replace('Football Team','Commanders')

upcoming_games['Away_Team'] = upcoming_games['tm_market'] + ' ' + upcoming_games['tm_name']
# upcoming_games.loc[]
upcoming_games['Home_Team'] = upcoming_games['opp_market'] + ' ' + upcoming_games['opp_name']
upcoming_games['Game'] = upcoming_games['Away_Team'] + ' @ ' + upcoming_games['Home_Team']

# season aggregates for legend
df_aggregates= df.groupby(['Player','year']).sum().reset_index()
df_aggregates = df_aggregates[['Player','Team','year','Passing_Yds','Rushing_Yds','Receiving_Yds']]
df_aggregates = df_aggregates.rename({'Passing_Yds':'Season_Passing_Yds',
                                      'Rushing_Yds':'Season_Rushing_Yds',
                                      'Receiving_Yds':'Season_Receiving_Yds'}, axis=1)
df_aggregates['Team'] = df_aggregates['Team'].str[:3]

df = pd.merge(df,df_aggregates, how='left',on=['Team','year','Player'])

# Categorize players
df['Player_Category'] = 'Receiver'
df.loc[(df['Season_Passing_Yds'] > df['Season_Rushing_Yds']) & (df['Season_Passing_Yds'] > df['Season_Receiving_Yds']),
       'Player_Category'] = 'Quarterback'
df.loc[(df['Season_Rushing_Yds'] > df['Season_Passing_Yds']) & (df['Season_Rushing_Yds'] > df['Season_Receiving_Yds']),
       'Player_Category'] = 'Running Back'

# distinct teams
teams = sorted(list(df['Real_Team'].unique()))

# Title of the app
title_col1, title_col2,title_col3,title_col4= st.columns([3,1,0.9,8])
top1, top2 = st.columns([10,0.01])
middle1,middle2,middle3 = st.columns([0.75,5,5])
page = st.sidebar.selectbox("Choose a page", ["Home", "Upcoming Games", "Team", "Player"])

if page =='Home':
    with middle1:
        page1_options = ['Passing','Rushing','Receiving']
        page1_selection = st.selectbox("Options", page1_options)
    with middle2:
        # Display the map and capture the map data
        returned_map_data = st_folium(m, width=1200, height=370)
            # Check if a marker was clicked
        if returned_map_data["last_object_clicked"]:
            lat = returned_map_data["last_object_clicked"]['lat']
            map_selection = location_df.loc[location_df['latitude']==lat,'city_team'].values[0]
            map_selection_index = teams.index(map_selection)
        else:
            map_selection_index = 0
else:
    map_selection_index = 0

### SIDEBAR FILTERS
team_selected = st.sidebar.selectbox("Select a team", teams,index=map_selection_index)
team_color = color_df[color_df['NFL Team Name']==team_selected]['Color 1'].values[0]


### RECORD
winner_ct = len(completed_games[completed_games['team1']==team_selected])
loser_ct = len(completed_games[completed_games['team2']==team_selected])
record = str(winner_ct) + ' - ' + str(loser_ct)
year_list = sorted(list(df['year'].unique()))

logo_selected = team_selected.lower()
logo_selected = logo_selected.replace(' ','-')
logo_selected = logo_selected + '-logo.svg'

### Add in logo ###
logo_path = os.path.join(path, 'logo')
svg_path = os.path.join(logo_path,logo_selected)
with open(svg_path, 'r') as f:
    svg_content = f.read()
    svg_content = svg_content.replace('width="700"', 'width="100"').replace('height="400"', 'height="100"')

with title_col1:    
    st.title('NFL Stats Dashboard')
with title_col2:
    st.markdown(f'''<div style="width: 100px; height: 100px; overflow: hidden; display: flex; align-items: center; justify-content: center;text-align: right;">{svg_content}</div>
    ''', unsafe_allow_html=True)
with title_col3:
        st.metric('',record)

# Display the map and capture the map data
# returned_map_data = st_folium(m, width=900, height=425)
### YEAR SELECTION ###
with st.sidebar.expander("Select year(s)", expanded=False):
    selected_options = st.multiselect(
        'Years',
        year_list,
        default=year_list
    )
    

# filter to selected team
with top1:
    filtered_df = df[df['Real_Team'].str.contains(team_selected)].reset_index()
    upcoming_games = upcoming_games[upcoming_games['Home_Team'].str.contains(team_selected) | upcoming_games['Away_Team'].str.contains(team_selected)].reset_index()

    # In the second column, you can display Passing visuals/data

    passing = df[df['Passing_Yds']>0]
    rushing = df[df['Rushing_Yds']>0]
    receiving = df[df['Receiving_Yds']>0]

    passing = passing.loc[passing['year'].isin(selected_options)]
    rushing = rushing.loc[rushing['year'].isin(selected_options)]
    receiving = receiving.loc[receiving['year'].isin(selected_options)]

    team_roster = sorted(list(df.loc[df['Real_Team']==team_selected,'Player'].unique()))
    active_roster = sorted(list(df.loc[(df['year']==str(new_year)) & (df['Real_Team']==team_selected),'Player'].unique()))
    space = ' '
    active_roster_value = ', '.join(active_roster)
    active_roster_header = f"Team: {team_selected} | Active Roster:{active_roster_value}"
    
    st.markdown(f"<h5 style='font-size: 14px;'>{active_roster_header}</h5>", unsafe_allow_html=True)


### TOP TEN LISTS ###
df_sum = df.groupby(['Player','year']).sum().reset_index()
df_sum = df_sum.rename({'Passing_Int':'Int',
                        'Passing_TD':'Pass_TD'
                        }, axis=1)
df_sum = df_sum[df_sum['year']==str(new_year)]
df_sum['Team'] = df_sum['Team'].str[:3]

### AVERAGE Df
df_avg = df.groupby(['Player','Team','year']).mean(numeric_only=True).reset_index()
df_avg = df_avg.rename({'Passing_Yds':'Avg_Pass_Yds',
                        'Passing_Rate':'Avg_Passer_Rating',
                        'Rushing_Yds':'Avg_Rush_Yds',
                        'Receiving_Yds':'Avg_Rec_Yds'
                        }, axis=1)
df_avg = df_avg[df_avg['year']==str(new_year)]
df_avg['Avg_Pass_Yds'] = df_avg['Avg_Pass_Yds'].apply(lambda x: round(x,1))
df_avg['Avg_Passer_Rating'] = df_avg['Avg_Passer_Rating'].apply(lambda x: round(x,1))
df_avg['Avg_Rush_Yds'] = df_avg['Avg_Rush_Yds'].apply(lambda x: round(x,1))
df_avg['Avg_Rec_Yds'] = df_avg['Avg_Rec_Yds'].apply(lambda x: round(x,1))

df_sum = pd.merge(df_sum, df_avg[['Player','Team','Avg_Pass_Yds', 'Avg_Passer_Rating', 'Avg_Rush_Yds','Avg_Rec_Yds']], how='left',on=['Player','Team'])

### PROJECTED STATS ###
max_week = df.groupby(['Team','year']).max().reset_index()
max_week = max_week[max_week['year']==str(new_year)]
max_week = max_week.rename({'week':'max_week'},axis=1)
df_sum = pd.merge(df_sum,max_week[['Team','max_week']],how='left',on='Team')
df_sum['Projected_Pass_Yds'] = round((df_sum['Passing_Yds'] / df_sum['max_week']) * 17,0)
df_sum['Projected_Rush_Yds'] = round((df_sum['Rushing_Yds'] / df_sum['max_week']) * 17,0)
df_sum['Projected_Rec_Yds'] = round((df_sum['Receiving_Yds'] / df_sum['max_week']) * 17,0)
df_sum['Projected_TDs'] = round((df_sum['Rushing_Receiving_TD'] / df_sum['max_week']) * 17,0)


# Generate colors using a colormap
num_players = len(active_roster)
colors = plt.cm.tab20(np.linspace(0, 1, num_players))

# Create a color mapping
color_mapping = {player: f'#{int(color[0]*255):02x}{int(color[1]*255):02x}{int(color[2]*255):02x}' for player, color in zip(active_roster, colors)}

# Create four columns
col1, col2, col3, col4= st.columns([0.5,2,2,2])

#######################################################################
#######################################################################
########################## HOME PAGE ##################################
#######################################################################
#######################################################################   
if page =='Home':
    # st.write("Top Players")
    home_col1, home_col2, home_col3= st.columns([1,5,5])

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


        # st.plotly_chart(fig_rec) 
        
    if page1_selection =='Passing':
        with middle3:
            passing_top_df['NFL_Team'] = passing_top_df['Team'].map(real_teams)
            # passing_top_df['color'] = passing_top_df['team_to_use'].apply(lambda x: team_color if x == team_selected else 'darkgray')

            color_condition = alt.condition(
                    alt.datum.NFL_Team == team_selected,  # Condition: Team matches team_selected
                    alt.value(team_color),            # If True: Use team_color
                    alt.value('darkgrey')             # If False: Use dark grey
                    )

            passing_top = pd.concat([passing_top_df.iloc[:5],passing_top_df.loc[passing_top_df['NFL_Team']== team_selected]],axis=0)
            passing_top = passing_top.drop_duplicates() # drop duplicates if they are already in df
            passing_top = passing_top[passing_top['Pass_Yds']>0]

            player_breakdown_projected_passing = alt.Chart(passing_top).mark_bar().encode(
                x=alt.X('sum(Projected_Pass_Yds):Q',axis=alt.Axis(title=None)),
                y=alt.Y('Player:N',sort=alt.EncodingSortField(field='Pass_Yds', op='sum', order='descending'),axis=alt.Axis(title=None)),
                color=alt.value('lightgrey'),
                tooltip=[
                    'Player:N',
                    'Projected_Pass_Yds:Q',
                    'NFL_Team:N'
                     ]
            ).properties(
                title='Cumulative Passing Yards',
                height=400
            )


            player_breakdown_passing = alt.Chart(passing_top).mark_bar().encode(
                x=alt.X('sum(Pass_Yds):Q',axis=alt.Axis(title=None)),
                y=alt.Y('Player:N',sort=alt.EncodingSortField(field='Pass_Yds', op='sum', order='descending'),axis=alt.Axis(title=None)),
                color=color_condition,
                tooltip=[
                    'Player:N',
                    'Pass_Yds:Q',
                    'NFL_Team:N'
                     ]
            )

            st.altair_chart(player_breakdown_projected_passing + player_breakdown_passing, use_container_width=True)


            passing_top_df = passing_top_df[passing_top_df['Pass_Yds']>0]
            
            passing_top_df_short = passing_top_df[[
                                         'Rank',
                                         'NFL_Team',
                                         'Pass_Yds',
                                         'Projected_Pass_Yds',
                                         'Pass_TD',
                                         'Int',
                                         'Avg_Pass_Yds',
                                         'Avg_Passer_Rating']].set_index('Rank')
   
            only_team = st.toggle("Show only selected team players")
            if only_team:
                passing_top_df_short = passing_top_df_short.loc[passing_top_df_short['NFL_Team']==team_selected]
            # Apply the styling
            styled_passing = passing_top_df_short.style.apply(highlight_team, axis=1)
            st.dataframe(styled_passing,
                width=900,
                height=400)
   
        with middle2:
            st.plotly_chart(fig_passing)
            
    elif page1_selection=='Rushing':
        with middle3:
            rushing_top_df['NFL_Team'] = rushing_top_df['Team'].map(real_teams)

            color_condition = alt.condition(
                    alt.datum.NFL_Team == team_selected,  # Condition: Team matches team_selected
                    alt.value(team_color),            # If True: Use team_color
                    alt.value('darkgrey')             # If False: Use dark grey
                    )

            rushing_top = pd.concat([rushing_top_df.iloc[:5],rushing_top_df.loc[rushing_top_df['NFL_Team']== team_selected]],axis=0)
            rushing_top = rushing_top.drop_duplicates() # drop duplicates if they are already in df
            rushing_top = rushing_top[rushing_top['Rush_Yds']>0]

            player_breakdown_projected_rushing = alt.Chart(rushing_top).mark_bar().encode(
                x=alt.X('sum(Projected_Rush_Yds):Q',axis=alt.Axis(title=None)),
                y=alt.Y('Player:N',sort=alt.EncodingSortField(field='Rush_Yds', op='sum', order='descending'),axis=alt.Axis(title=None)),
                color=alt.value('lightgrey'),
                tooltip=[
                    'Player:N',
                    'Projected_Rush_Yds:Q',
                    'NFL_Team:N'
                     ]
            ).properties(
                title='Cumulative Rushing Yards',
                height=400
            )


            player_breakdown_rushing = alt.Chart(rushing_top).mark_bar().encode(
                x=alt.X('sum(Rush_Yds):Q',axis=alt.Axis(title=None)),
                y=alt.Y('Player:N',sort=alt.EncodingSortField(field='Rush_Yds', op='sum', order='descending'),axis=alt.Axis(title=None)),
                color=color_condition,
                tooltip=[
                    'Player:N',
                    'Rush_Yds:Q',
                    'NFL_Team:N'
                     ]
            )

            st.altair_chart(player_breakdown_projected_rushing + player_breakdown_rushing, use_container_width=True)


            rushing_top_df = rushing_top_df[rushing_top_df['Rush_Yds']>0]
            rushing_top_df_short = rushing_top_df[[
                                         'Rank',
                                         'NFL_Team',
                                         'Rush_Yds',
                                         'Projected_Rush_Yds',
                                         'Rushing_Receiving_TD',
                                         'Avg_Rush_Yds',
                                         'Avg_Rec_Yds']].set_index('Rank')

            only_team = st.toggle("Show only selected team players")
            if only_team:
                rushing_top_df_short = rushing_top_df_short.loc[rushing_top_df_short['NFL_Team']==team_selected]

            # Apply the styling
            styled_rushing = rushing_top_df_short.style.apply(highlight_team, axis=1)
        
            st.dataframe(styled_rushing,
                width=900,
                height=400)

        with middle2:
            st.plotly_chart(fig_rushing)
    else:
        with middle3:
            receiving_top_df['NFL_Team'] = receiving_top_df['Team'].map(real_teams)

            color_condition = alt.condition(
                    alt.datum.NFL_Team == team_selected,  # Condition: Team matches team_selected
                    alt.value(team_color),            # If True: Use team_color
                    alt.value('darkgrey')             # If False: Use dark grey
                    )

            receiving_top = pd.concat([receiving_top_df.iloc[:5],receiving_top_df.loc[receiving_top_df['NFL_Team']== team_selected]],axis=0)
            receiving_top = receiving_top.drop_duplicates() # drop duplicates if they are already in df
            receiving_top = receiving_top[receiving_top['Rec_Yds']>0]

            player_breakdown_projected_receiving = alt.Chart(receiving_top).mark_bar().encode(
                x=alt.X('sum(Projected_Rec_Yds):Q',axis=alt.Axis(title=None)),
                y=alt.Y('Player:N',sort=alt.EncodingSortField(field='Rec_Yds', op='sum', order='descending'),axis=alt.Axis(title=None)),
                color=alt.value('lightgrey'),
                tooltip=[
                    'Player:N',
                    'Projected_Rec_Yds:Q',
                    'NFL_Team:N'
                     ]
            ).properties(
                title='Cumulative Receiving Yards',
                height=400
            )


            player_breakdown_receiving = alt.Chart(receiving_top).mark_bar().encode(
                x=alt.X('sum(Rec_Yds):Q',axis=alt.Axis(title=None)),
                y=alt.Y('Player:N',sort=alt.EncodingSortField(field='Rec_Yds', op='sum', order='descending'),axis=alt.Axis(title=None)),
                color=color_condition,
                tooltip=[
                    'Player:N',
                    'Rec_Yds:Q',
                    'NFL_Team:N'
                     ]
            )

            st.altair_chart(player_breakdown_projected_receiving + player_breakdown_receiving, use_container_width=True)


            receiving_top_df = receiving_top_df[receiving_top_df['Rec_Yds']>0]
            receiving_top_df_short = receiving_top_df[[
                                         'Rank',
                                         'NFL_Team',
                                         'Rec_Yds',
                                         'Projected_Rec_Yds',
                                         'Rushing_Receiving_TD',
                                         'Avg_Rec_Yds',
                                         'Avg_Rush_Yds']].set_index('Rank')
   

            only_team = st.toggle("Show only selected team players")
            if only_team:
                receiving_top_df_short = receiving_top_df_short.loc[receiving_top_df_short['NFL_Team']==team_selected]
            # Apply the styling
            styled_receiving = receiving_top_df_short.style.apply(highlight_team, axis=1)
            st.dataframe(styled_receiving,
                width=900,
                height=400)
        with middle2:
            st.plotly_chart(fig_rec)


#######################################################################
#######################################################################
##################### UPCOMING GAMES PAGE #############################
#######################################################################
#######################################################################   
elif page == "Upcoming Games":
    game = st.sidebar.selectbox('Game:', upcoming_games['Game'].unique())
    away_team = game.split('@')[0].strip()
    home_team = game.split('@')[1].strip() 

    ### Completed Games
    completed_games['opponent_team'] = np.nan
    completed_games['searched_team'] = np.nan
    completed_games['opponent_score'] = np.nan
    completed_games['team_score'] = np.nan
  
    completed_games.loc[completed_games['team1']==away_team,'opponent_team'] = completed_games.loc[completed_games['team1']==away_team,'team2']
    completed_games.loc[completed_games['team2']==away_team,'opponent_team'] = completed_games.loc[completed_games['team2']==away_team,'team1']
    completed_games.loc[completed_games['team1']==away_team,'searched_team'] = completed_games.loc[completed_games['team1']==away_team,'team1']
    completed_games.loc[completed_games['team2']==away_team,'searched_team'] = completed_games.loc[completed_games['team2']==away_team,'team2']

    completed_games.loc[completed_games['team1']==home_team,'opponent_team'] = completed_games.loc[completed_games['team1']==home_team,'team2']
    completed_games.loc[completed_games['team2']==home_team,'opponent_team'] = completed_games.loc[completed_games['team2']==home_team,'team1']
    completed_games.loc[completed_games['team1']==home_team,'searched_team'] = completed_games.loc[completed_games['team1']==home_team,'team1']
    completed_games.loc[completed_games['team2']==home_team,'searched_team'] = completed_games.loc[completed_games['team2']==home_team,'team2']
    
    completed_games.loc[completed_games['team1']==away_team,'opponent_score'] = completed_games.loc[completed_games['team1']==away_team,'opp_score']
    completed_games.loc[completed_games['team2']==away_team,'opponent_score'] = completed_games.loc[completed_games['team2']==away_team,'tm_score']
    completed_games.loc[completed_games['team1']==away_team,'team_score'] = completed_games.loc[completed_games['team1']==away_team,'tm_score']
    completed_games.loc[completed_games['team2']==away_team,'team_score'] = completed_games.loc[completed_games['team2']==away_team,'opp_score']

    completed_games.loc[completed_games['team1']==home_team,'opponent_score'] = completed_games.loc[completed_games['team1']==home_team,'opp_score']
    completed_games.loc[completed_games['team2']==home_team,'opponent_score'] = completed_games.loc[completed_games['team2']==home_team,'tm_score']
    completed_games.loc[completed_games['team1']==home_team,'team_score'] = completed_games.loc[completed_games['team1']==home_team,'tm_score']
    completed_games.loc[completed_games['team2']==home_team,'team_score'] = completed_games.loc[completed_games['team2']==home_team,'opp_score']
    completed_games_sub = completed_games[['year_week','opponent_team','searched_team','opponent_score','team_score']]

    completed_scores = completed_games_sub[completed_games_sub['opponent_team'].notnull()]
    completed_scores['WinLoss'] = 'Loss'
    completed_scores.loc[(completed_scores['opponent_score'] - completed_scores['team_score']) < 0, 'WinLoss'] = 'Win' 
    avg_scores = completed_scores.groupby(['searched_team']).agg({'team_score': 'mean',
                                                                  'opponent_score':'mean'}).reset_index()
    ######### Defense ###############

    ### PASSING
    passing_def = pd.merge(passing,completed_games_sub, how='inner', left_on=['year_week','Real_Team'], right_on=['year_week','opponent_team'])
    passing_def['team_category'] = 'Defense ' + passing_def['searched_team']
    passing_off = pd.merge(passing,completed_games_sub, how='inner', left_on=['year_week','Real_Team'], right_on=['year_week','searched_team'])
    passing_off['team_category'] = 'Offense ' + passing_off['searched_team']
    passing_past = pd.concat([passing_off,passing_def],axis=0)
            
    passing_awayteam = passing_past.loc[passing_past['team_category'].isin(['Offense ' + away_team, 'Defense ' + home_team])]
    passing_hometeam = passing_past.loc[passing_past['team_category'].isin(['Offense ' + home_team, 'Defense ' + away_team])]

    # Aggregate data to get total rushing yards per player per week
    total_passing_away = passing_awayteam.groupby(['year_week', 'Player','team_category']).agg({'Passing_Yds': 'sum'}).reset_index()
    # Sort by year_week and then by Rushing_Yds in descending order
    total_passing_away = total_passing_away.sort_values(by=['year_week', 'Passing_Yds'], ascending=[True, False])

    # Aggregate data to get total rushing yards per player per week
    total_passing_home = passing_hometeam.groupby(['year_week', 'Player','team_category']).agg({'Passing_Yds': 'sum'}).reset_index()
    # Sort by year_week and then by Rushing_Yds in descending order
    total_passing_home = total_passing_home.sort_values(by=['year_week', 'Passing_Yds'], ascending=[True, False])


    ## RUSHING
    rushing_def = pd.merge(rushing,completed_games_sub, how='inner', left_on=['year_week','Real_Team'], right_on=['year_week','opponent_team'])
    rushing_def['team_category'] = 'Defense ' + rushing_def['searched_team']
    rushing_off = pd.merge(rushing,completed_games_sub, how='inner', left_on=['year_week','Real_Team'], right_on=['year_week','searched_team'])
    rushing_off['team_category'] = 'Offense ' + rushing_off['searched_team']
    rushing_past = pd.concat([rushing_off,rushing_def],axis=0)

    rushing_awayteam = rushing_past.loc[rushing_past['team_category'].isin(['Offense ' + away_team, 'Defense ' + home_team])]
    rushing_hometeam = rushing_past.loc[rushing_past['team_category'].isin(['Offense ' + home_team, 'Defense ' + away_team])]

    # Aggregate data to get total rushing yards per player per week
    total_rushing_away = rushing_awayteam.groupby(['year_week', 'Player','team_category']).agg({'Rushing_Yds': 'sum'}).reset_index()
    # Sort by year_week and then by Rushing_Yds in descending order
    total_rushing_away = total_rushing_away.sort_values(by=['year_week', 'Rushing_Yds'], ascending=[True, False])

    # Aggregate data to get total rushing yards per player per week
    total_rushing_home= rushing_hometeam.groupby(['year_week', 'Player','team_category']).agg({'Rushing_Yds': 'sum'}).reset_index()
    # Sort by year_week and then by Rushing_Yds in descending order
    total_rushing_home = total_rushing_home.sort_values(by=['year_week', 'Rushing_Yds'], ascending=[True, False])

    ### RECEIVING
    receiving_def = pd.merge(receiving,completed_games_sub, how='inner', left_on=['year_week','Real_Team'], right_on=['year_week','opponent_team'])
    receiving_def['team_category'] = 'Defense ' + receiving_def['searched_team']
    receiving_off = pd.merge(receiving,completed_games_sub, how='inner', left_on=['year_week','Real_Team'], right_on=['year_week','searched_team'])
    receiving_off['team_category'] = 'Offense ' + receiving_off['searched_team']
    receiving_past = pd.concat([receiving_off,receiving_def],axis=0)

    receiving_awayteam = receiving_past.loc[receiving_past['team_category'].isin(['Offense ' + away_team, 'Defense ' + home_team])]
    receiving_hometeam = receiving_past.loc[receiving_past['team_category'].isin(['Offense ' + home_team, 'Defense ' + away_team])]

    # Aggregate data to get total rushing yards per player per week
    total_rec_away = receiving_awayteam.groupby(['year_week', 'Player','team_category']).agg({'Receiving_Yds': 'sum'}).reset_index()
    # Sort by year_week and then by Rushing_Yds in descending order
    total_rec_away = total_rec_away.sort_values(by=['year_week', 'Receiving_Yds'], ascending=[True, False])

    # Aggregate data to get total rushing yards per player per week
    total_rec_home = receiving_hometeam.groupby(['year_week', 'Player','team_category']).agg({'Receiving_Yds': 'sum'}).reset_index()
    # Sort by year_week and then by Rushing_Yds in descending order
    total_rec_home = total_rec_home.sort_values(by=['year_week', 'Receiving_Yds'], ascending=[True, False])

    ### LOGOS ###
    away_team_logo = away_team.lower().replace(' ','-') + '-logo.svg'
    home_team_logo = home_team.lower().replace(' ','-') + '-logo.svg'
    away_svg_path = os.path.join(logo_path,away_team_logo)
    home_svg_path = os.path.join(logo_path,home_team_logo)
    with open(away_svg_path, 'r') as f:
        away_svg_content = f.read()
        away_svg_content = away_svg_content.replace('width="700"', 'width="100"').replace('height="400"', 'height="100"')
    
    with open(home_svg_path, 'r') as f:
        home_svg_content = f.read()
        home_svg_content = home_svg_content.replace('width="700"', 'width="100"').replace('height="400"', 'height="100"')
    othercol1, othercol2, othercol3, othercol4,othercol5,othercol6,othercol7 = st.columns([3.5,1.6,1.5,1.2,1,1.5,3])

    with othercol1:
        event_date = upcoming_games.loc[upcoming_games['Game']==game,'event_date'].values[0]
        formatted_event = datetime.strptime(event_date, '%Y-%m-%d').strftime('%B %d, %Y')
        st.metric('',formatted_event)

    with othercol2:
        away_score = round(avg_scores.loc[avg_scores['searched_team']==away_team,'team_score'].values[0],1)
        away_score_against = round(avg_scores.loc[avg_scores['searched_team']==away_team,'opponent_score'].values[0],1)
        away_vs = round(away_score - away_score_against,1)
        st.metric("Average Score",away_score,str(away_vs) +', Avg Differential')
    with othercol3:
        st.markdown(f'''<div style="width: 75px; height: 75px; overflow: hidden; display: flex; align-items: center; justify-content: center;text-align: right;">{away_svg_content}</div>''', unsafe_allow_html=True)
        away_wins = completed_scores[(completed_scores['WinLoss']=='Win') & (completed_scores['searched_team']==away_team)]['year_week'].count()
        away_losses = completed_scores[(completed_scores['WinLoss']=='Loss') & (completed_scores['searched_team']==away_team)]['year_week'].count()
        away_record = str(away_wins) + "-" + str(away_losses)
        st.markdown(f'''<div style="width: 75px; height: 10px;  justify-content: center;text-align: center;">{away_record}</div>''', unsafe_allow_html=True)
    with othercol4:
        st.metric('',"@")
    with othercol5:
        st.markdown(f'''<div style="width: 75px; height: 75px; overflow: hidden; display: flex; align-items: center; justify-content: center;text-align: left;">{home_svg_content}</div>''', unsafe_allow_html=True)
        home_wins = completed_scores[(completed_scores['WinLoss']=='Win') & (completed_scores['searched_team']==home_team)]['year_week'].count()
        home_losses = completed_scores[(completed_scores['WinLoss']=='Loss') & (completed_scores['searched_team']==home_team)]['year_week'].count()
        home_record = str(home_wins) + "-" + str(home_losses)
        st.markdown(f'''<div style="width: 75px; height: 10px;  justify-content: center;text-align: center;">{home_record}</div>''', unsafe_allow_html=True)

    with othercol6:
        home_score = round(avg_scores.loc[avg_scores['searched_team']==home_team,'team_score'].values[0],1)
        home_score_against = round(avg_scores.loc[avg_scores['searched_team']==home_team,'opponent_score'].values[0],1)
        home_vs = round(home_score - home_score_against,1)
        st.metric("Average Score",home_score, str(home_vs) +', Avg Differential')

    ### left_chart
    top_team_color_left = color_df[color_df['NFL Team Name']==away_team]['Color 1'].values[0]
    bottom_team_color_left = color_df[color_df['NFL Team Name']==home_team]['Color 2'].values[0]

    ### right chart
    top_team_color_right = color_df[color_df['NFL Team Name']==home_team]['Color 1'].values[0]
    bottom_team_color_right = color_df[color_df['NFL Team Name']==away_team]['Color 2'].values[0]


    up_col1, up_col2, up_col3, up_col4 = st.columns([1,5,5,1])

    max_pass_value = passing_past.groupby(['year_week','team_category']).sum()['Passing_Yds'].max()
    pass_limit = round(max_pass_value / 50) * 50
    max_rush_value = rushing_past.groupby(['year_week','team_category']).sum()['Rushing_Yds'].max()
    rush_limit = round(max_rush_value / 50) * 50
    max_rec_value = receiving_past.groupby(['year_week','team_category']).sum()['Receiving_Yds'].max()
    rec_limit = round(max_rec_value / 50) * 50
    chart_ht = 225
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
    with up_col2:

        # Create a chart for player breakdown with sorted values
        player_breakdown_passing_away = alt.Chart(total_passing_away).mark_bar().encode(
            x=alt.X('year_week:O',axis=alt.Axis(title=None)),
            y=alt.Y('Passing_Yds:Q', scale=alt.Scale(domain=[0, pass_limit])),
            xOffset=alt.XOffset('team_category:N', sort='descending'),
            color=alt.Color('team_category:N', scale=alt.Scale(range=[top_team_color_left, bottom_team_color_left]),sort=alt.EncodingSortField(field='team_category', order='descending'),title=None),
            opacity=alt.Opacity('Passing_Yds:Q', scale=alt.Scale(domain=[0, total_passing_away['Passing_Yds'].max()], range=[0.3, 1]),legend=None),  # Fading effect
            tooltip=[
                'Player:N',
                'Passing_Yds:Q',
                'year_week:O'
            ]
        ).properties(
            title='Player Passing Yards per Week',
            height=chart_ht
        ).configure_legend(
            orient='left'  # Position the legend on the left
        )

        st.altair_chart(player_breakdown_passing_away, use_container_width=True)

        # Create a chart for player breakdown with sorted values
        player_breakdown_rushing_away = alt.Chart(total_rushing_away).mark_bar().encode(
            x=alt.X('year_week:O',axis=alt.Axis(title=None)),
            y=alt.Y('Rushing_Yds:Q', scale=alt.Scale(domain=[0, rush_limit])),
            xOffset=alt.XOffset('team_category:N', sort='descending'),
            color=alt.Color('team_category:N', scale=alt.Scale(range=[top_team_color_left, bottom_team_color_left]),sort=alt.EncodingSortField(field='team_category', order='descending'),title=None),
            opacity=alt.Opacity('Rushing_Yds:Q', scale=alt.Scale(domain=[0, total_rushing_away['Rushing_Yds'].max()], range=[0.3, 1]),legend=None),  # Fading effect
            tooltip=[
                'Player:N',
                'Rushing_Yds:Q',
                'year_week:O'
            ]
        ).properties(
            title='Player Rushing Yards per Week',
            height=chart_ht
        ).configure_legend(
            orient='left'  # Position the legend on the left
        )

        st.altair_chart(player_breakdown_rushing_away, use_container_width=True)

        # Create a chart for player breakdown with sorted values
        player_breakdown_receiving_away = alt.Chart(total_rec_away).mark_bar().encode(
            x=alt.X('year_week:O',axis=alt.Axis(title=None)),
            y=alt.Y('Receiving_Yds:Q', scale=alt.Scale(domain=[0, rec_limit])),
            xOffset=alt.XOffset('team_category:N', sort='descending'),
            color=alt.Color('team_category:N', scale=alt.Scale(range=[top_team_color_left, bottom_team_color_left]),sort=alt.EncodingSortField(field='team_category', order='descending'),title=None),
            opacity=alt.Opacity('Receiving_Yds:Q', scale=alt.Scale(domain=[0, total_rec_away['Receiving_Yds'].max()], range=[0.3, 1]),legend=None),  # Fading effect
            tooltip=[
                'Player:N',
                'Receiving_Yds:Q',
                'year_week:O'
            ]
        ).properties(
            title='Player Receiving Yards per Week',
            height=chart_ht
        ).configure_legend(
            orient='left'  # Position the legend on the left
        )

        st.altair_chart(player_breakdown_receiving_away, use_container_width=True)

    with up_col3:

        # Create a chart for player breakdown with sorted values
        player_breakdown_passing_home = alt.Chart(total_passing_home).mark_bar().encode(
            x=alt.X('year_week:O',axis=alt.Axis(title=None)),
            y=alt.Y('Passing_Yds:Q', axis=alt.Axis(title=None), scale=alt.Scale(domain=[0, pass_limit])),
            xOffset=alt.XOffset('team_category:N', sort='descending'),
            color=alt.Color('team_category:N', scale=alt.Scale(range=[top_team_color_right, bottom_team_color_right]),sort=alt.EncodingSortField(field='team_category', order='descending'),title=None),
            opacity=alt.Opacity('Passing_Yds:Q', scale=alt.Scale(domain=[0, total_passing_home['Passing_Yds'].max()], range=[0.3, 1]),legend=None),  # Fading effect

            tooltip=[
                'Player:N',
                'Passing_Yds:Q',
                'year_week:O'
            ]
        ).properties(
            title=' ',
            height=chart_ht
        )

        st.altair_chart(player_breakdown_passing_home, use_container_width=True)
  
        # Create a chart for player breakdown with sorted values
        player_breakdown_rushing_home = alt.Chart(total_rushing_home).mark_bar().encode(
            x=alt.X('year_week:O',axis=alt.Axis(title=None)),
            y=alt.Y('Rushing_Yds:Q', axis=alt.Axis(title=None), scale=alt.Scale(domain=[0, rush_limit])),
            xOffset=alt.XOffset('team_category:N', sort='descending'),
            color=alt.Color('team_category:N', scale=alt.Scale(range=[top_team_color_right, bottom_team_color_right]),sort=alt.EncodingSortField(field='team_category', order='descending'),title=None),
            opacity=alt.Opacity('Rushing_Yds:Q', scale=alt.Scale(domain=[0, total_rushing_home['Rushing_Yds'].max()], range=[0.3, 1]),legend=None),  # Fading effect

            tooltip=[
                'Player:N',
                'Rushing_Yds:Q',
                'year_week:O'
            ]
        ).properties(
            title=' ',
            height=chart_ht
        )

        st.altair_chart(player_breakdown_rushing_home, use_container_width=True)

        # Create a chart for player breakdown with sorted values
        player_breakdown_receiving_home = alt.Chart(total_rec_home).mark_bar().encode(
            x=alt.X('year_week:O',axis=alt.Axis(title=None)),
            y=alt.Y('Receiving_Yds:Q', axis=alt.Axis(title=None), scale=alt.Scale(domain=[0, rec_limit])),
            xOffset=alt.XOffset('team_category:N', sort='descending'),
            color=alt.Color('team_category:N', scale=alt.Scale(range=[top_team_color_right, bottom_team_color_right]),sort=alt.EncodingSortField(field='team_category', order='descending'),title=None),
            opacity=alt.Opacity('Receiving_Yds:Q', scale=alt.Scale(domain=[0, total_rec_home['Receiving_Yds'].max()], range=[0.3, 1]),legend=None),  # Fading effect

            tooltip=[
                'Player:N',
                'Receiving_Yds:Q',
                'year_week:O'
            ]
        ).properties(
            title=' ',
            height=chart_ht
        )

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


#######################################################################
#######################################################################
########################### TEAM PAGE #################################
#######################################################################
#######################################################################
elif page == "Team":

    ### PLAYER SELECTION ###
    with st.sidebar.expander("Select player(s)", expanded=False):
        player = st.multiselect('Players',
                                        team_roster, 
                                        default=active_roster)
    passing = passing.loc[passing['Player'].isin(player)]
    rushing = rushing.loc[rushing['Player'].isin(player)]
    receiving = receiving.loc[receiving['Player'].isin(player)]

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
    team_pg_height = 250
    with col1:
 
    ### PASSING
        # Create an Altair chart without displaying the bars, just the legend
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

        # Display the chart in Streamlit
        st.altair_chart(passing_legend, use_container_width=True)

    ### RUSHING
        rushing_legend = alt.Chart(rushing).mark_bar(opacity=0).encode(
            x=alt.X('year_week:O',axis=alt.Axis(title=None)),
            y='Rushing_Yds:Q',
            color=alt.Color('Player:N', scale=alt.Scale(domain=list(rushing_mapping.keys()), 
                                                        range=list(rushing_mapping.values())),
                                        legend=alt.Legend(
                                            title="Rushing",  # Custom legend title
                                            orient='left',  # Position the legend on the left
                                            direction='vertical'  # Make the legend vertical
                                        )),
            order=alt.Order('Season_Rushing_Yds', sort='descending'),
            tooltip=['Player', 'Season_Rushing_Yds', 'week']
        ).properties(
            width=600,
            height=team_pg_height
        ).configure_legend(
            orient='left'  # Position the legend on the left
        )

        # Display the chart in Streamlit
        st.altair_chart(rushing_legend, use_container_width=True)

    ### RECEIVING
        receiving_legend = alt.Chart(receiving).mark_bar(opacity=0).encode(
            x=alt.X('year_week:O',axis=alt.Axis(title=None)),
            y='Receiving_Yds:Q',
            color=alt.Color('Player:N', scale=alt.Scale(domain=list(receiving_mapping.keys()), 
                                                        range=list(receiving_mapping.values())),
                                        legend=alt.Legend(
                                            title="Receiving",  # Custom legend title
                                            orient='left',  # Position the legend on the left
                                            direction='vertical'  # Make the legend vertical
                                        )),
            order=alt.Order('Season_Receiving_Yds', sort='descending'),
            tooltip=['Player', 'Season_Receiving_Yds', 'week']
        ).properties(
            width=600,
            height=team_pg_height + 150
        ).configure_legend(
            orient='left'  # Position the legend on the left
        )

        # Display the chart in Streamlit
        st.altair_chart(receiving_legend, use_container_width=True)

    with col2:
    ### PASSING
        passing_yds_chart = alt.Chart(passing).mark_bar().encode(
            x=alt.X('year_week:O',axis=alt.Axis(title=None)),
            y=alt.Y('Passing_Yds:Q',axis=alt.Axis(title=None)),
            color=alt.Color('Player:N', scale=alt.Scale(domain=list(passing_mapping.keys()), range=list(passing_mapping.values())), legend=None),
            order=alt.Order('Season_Passing_Yds', sort='descending'),
            tooltip=['Player', 'Passing_Yds', 'year_week']
        ).properties(
            title='Passing Yards',
            width=600,
            height=team_pg_height
        )

        # Display the chart in Streamlit
        st.altair_chart(passing_yds_chart, use_container_width=True)  # Example data

    ### RUSHING
        rushing_yds_chart = alt.Chart(rushing).mark_bar().encode(
            x=alt.X('year_week:O',axis=alt.Axis(title=None)),
            y=alt.Y('Rushing_Yds:Q',axis=alt.Axis(title=None)),
            color=alt.Color('Player:N', scale=alt.Scale(domain=list(rushing_mapping.keys()), range=list(rushing_mapping.values())), legend=None),
            order=alt.Order('Season_Rushing_Yds', sort='descending'),
            tooltip=['Player', 'Rushing_Yds', 'year_week']
        ).properties(
            title='Rushing Yards',
            width=600,
            height=team_pg_height
        )

        # Display the chart in Streamlit
        st.altair_chart(rushing_yds_chart, use_container_width=True)
        
    ### RECEIVING
        receiving_yds_chart = alt.Chart(receiving).mark_bar().encode(
            x=alt.X('year_week:O',axis=alt.Axis(title=None)),
            y=alt.Y('Receiving_Yds:Q',axis=alt.Axis(title=None)),
            color=alt.Color('Player:N', scale=alt.Scale(domain=list(receiving_mapping.keys()), range=list(receiving_mapping.values())), legend=None),
            order=alt.Order('Season_Receiving_Yds', sort='descending'),
            tooltip=['Player', 'Receiving_Yds', 'year_week']
        ).properties(
            title='Receiving Yards',
            width=600,
            height=team_pg_height
        )

        st.altair_chart(receiving_yds_chart, use_container_width=True) 

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

#######################################################################
#######################################################################
########################## PLAYER PAGE ################################
#######################################################################
#######################################################################         

elif page == "Player":
    col1, col2, col3 = st.columns([0.5,2,2])

    team_roster = sorted(list(df.loc[(df['Real_Team']==team_selected) & (df['year'].isin(selected_options)),'Player'].unique()))
    player = st.sidebar.selectbox("Select a player", team_roster)

    player_stat = df.loc[df['Player']==player].reset_index()

    player_stat = player_stat.loc[player_stat['year'].isin(selected_options)].reset_index()
    season_pass = player_stat['Season_Passing_Yds'][0] 
    season_rush = player_stat['Season_Rushing_Yds'][0] 
    season_rec = player_stat['Season_Receiving_Yds'][0] 
    qb_ht_page = 400
    player_ht_page = 250

    ### ADDED INFO TO SIDEBAR ###
    qb_active_list = sorted(list(df.loc[(df['Player_Category']=='Quarterback') & 
                                  (df['Real_Team']==team_selected) &
                                  (df['year']==str(new_year)),'Player'].unique()))
    rb_active_list = sorted(list(df[(df['Player_Category']=='Running Back') & 
                                  (df['Real_Team']==team_selected) &
                                  (df['year']==str(new_year))]['Player'].unique()))
    rec_active_list = sorted(list(df[(df['Player_Category']=='Receiver') & 
                                  (df['Real_Team']==team_selected) &
                                  (df['year']==str(new_year))]['Player'].unique()))

    qb_sidebar = st.sidebar.write('QBs:',', '.join(qb_active_list))
    rb_sidebar = st.sidebar.write('RBs:',', '.join(rb_active_list))
    rec_sidebar = st.sidebar.write('Receivers:',', '.join(rec_active_list))

    melted_stat = player_stat.melt(
    id_vars=['Player', 'year_week'], 
    value_vars=['Passing_Yds', 'Rushing_Yds'], 
    var_name='Yard_Type', 
    value_name='Yards'
)

    if season_pass > season_rush and season_pass > season_rec:
        player_pos = "Quarterback"
    elif season_rush > season_pass and season_rush > season_rec:
        player_pos = "Rusher"
    else:
        player_pos = "Receiver"

    # Num of games
    num_games = df.loc[(df['Real_Team']==team_selected ) & (df['year'].isin(selected_options)),'year_week'].nunique()

    if player_pos =="Quarterback":
        with col1:
            st.write(player_pos)
            # old_passing_legend = alt.Chart(player_stat).mark_point(opacity=0).encode(
            #     x='week:O',
            #     y='year:Q',
            #     color=alt.Color('year:N', sort=alt.EncodingSortField(field='year', order='descending')),
            #     order=alt.Order('year', sort='descending'),
            #     tooltip=['Player', 'year', 'week']
            # ).properties(
            #     width=0,
            #     height=150
            # ).configure_legend(
            #     orient='left' # Position the legend on the left
            # ).configure_axis(
            #     grid=False,  # Remove gridlines
            #     labels=False,  # Remove axis labels
            #     ticks=False,
            #     title=None # Remove axis ticks
            # )

            passing_legend = alt.Chart(player_stat).mark_point().encode(
                color=alt.Color('year:O', scale=alt.Scale(
                    domain=sorted(player_stat['year'].unique(), reverse=True),  # Sort years in descending order
                    range=[team_color],  # Use the same color for all years
                ),
                    legend=alt.Legend(
                        title="Year",
                        orient='left',  # Position the legend on the left
                        direction='vertical'  # Make the legend vertical
                    )
                ),
                order=alt.Order('year:O', sort='descending'),  # Sort years in descending order
                opacity=alt.Opacity('year:O', scale=alt.Scale(
                    domain=sorted(player_stat['year'].unique(), reverse=True),  # Ensure opacity scale matches the years
                    range=[1, 0.1]  # Older years lighter, newer years fully opaque
                ), legend=None)
            ).properties(
                width=60,
                height=150
            ).configure_axis(
                grid=False,  # Remove gridlines
                labels=False,  # Remove axis labels
                ticks=False,
                title=None  # Remove axis ticks
            )

            # Display the chart (legend only)
            st.altair_chart(passing_legend)
            
            # Betting inputs
            pass_yd_input = st.number_input('Passing Yards Target:', min_value=0, max_value=500, value=0)
            rush_yd_input = st.number_input('Rushing Yards Target:', min_value=0, max_value=200, value=0)
            passing_td_input = st.number_input("Passing Touchdown Target:", min_value=0, max_value=5, value=0)
            completion_input = st.number_input("Completions Target:", min_value=0, max_value=50, value=0)


        with col2:
        ### PASSING
            passing_yds_chart = alt.Chart(player_stat).mark_bar().encode(
                x=alt.X('year_week:O',axis=alt.Axis(title=None)),
                y=alt.Y('Passing_Yds:Q',axis=alt.Axis(title=None)),
                color=alt.value(team_color),
                opacity=alt.Opacity('year:O', scale=alt.Scale(
                        domain=player_stat['year'].unique().tolist(),  # Ensure the scale covers all years in the data
                        range=[0.3, 1]  # Older years lighter (0.4 opacity), newer years fully opaque (1 opacity)
                    ), legend=None),
                order=alt.Order('Season_Passing_Yds', sort='descending'),
                tooltip=['Player', 'Passing_Yds', 'year_week']
            ).properties(
                title='Passing Yards',
                height=qb_ht_page
            )

            min_value = player_stat['Passing_Yds'].min()
            avg_value = round(player_stat['Passing_Yds'].mean(),1)
            max_value = player_stat['Passing_Yds'].max()
            # Add min, max, average lines
            min_line = alt.Chart(pd.DataFrame({'y': [min_value], 'label': [f'Minimum: {min_value}']})).mark_rule(color='red').encode(
                        y='y:Q'
                    ).properties(
                        title='Minimum'
                    )
            min_label = min_line.mark_text(
                    align='left',
                    baseline='middle',
                    dx=280,
                    dy=-10  # Adjust the position of the text
                ).encode(
                    text='label:N'
                )

            avg_line = alt.Chart(pd.DataFrame({'y': [avg_value], 'label': [f'Average: {avg_value}']})).mark_rule(color='blue').encode(
                        y='y:Q'
                    ).properties(
                        title='Average'
                    )
            
            avg_label = avg_line.mark_text(
                    align='left',
                    baseline='middle',
                    dx=280,
                    dy=-10
                ).encode(
                    text='label:N'
                )

            max_line = alt.Chart(pd.DataFrame({'y': [max_value], 'label': [f'Maximum: {max_value}']})).mark_rule(color='green').encode(
                        y='y:Q'
                    ).properties(
                        title='Maximum'
                    )
            max_label = max_line.mark_text(
                    align='left',
                    baseline='middle',
                    dx=280,
                    dy=-10
                ).encode(
                    text='label:N'
                )
            
            # count of values over target
            pass_games = player_stat.loc[player_stat['Passing_Yds']>=pass_yd_input,'year_week'].nunique()
            pass_perc_games = "{:.0f}%".format((pass_games / num_games)* 100)
            target_pass_line, target_pass_label = target_lines(pass_yd_input,pass_perc_games)

            # Combine the base chart with the horizontal lines
            final_chart = passing_yds_chart + min_line + avg_line + max_line + target_pass_line + min_label + avg_label + max_label + target_pass_label

            # Display the chart in Streamlit
            st.altair_chart(final_chart, use_container_width=True)

            passing_td_chart = alt.Chart(player_stat).mark_bar().encode(
                x=alt.X('year_week:O',axis=alt.Axis(title=None)),
                y=alt.Y('Passing_TD:Q',axis=alt.Axis(title=None)),
                color=alt.value(team_color),
                opacity=alt.Opacity('year:O', scale=alt.Scale(
                        domain=player_stat['year'].unique().tolist(),  # Ensure the scale covers all years in the data
                        range=[0.3, 1]  # Older years lighter (0.4 opacity), newer years fully opaque (1 opacity)
                    ), legend=None),
                order=alt.Order('Passing_TD', sort='descending'),
                tooltip=['Player', 'Passing_TD', 'year_week']
            ).properties(
                title='Passing Touchdowns',
                width=600,
                height=qb_ht_page
            )

            # count of values over target
            pass_td_games = player_stat.loc[player_stat['Passing_TD']>=passing_td_input,'year_week'].nunique()
            pass_td_perc_games = "{:.0f}%".format((pass_td_games / num_games)* 100)
            target_td_line, target_td_label = target_lines(passing_td_input,pass_td_perc_games)

            st.altair_chart(passing_td_chart + target_td_line + target_td_label, use_container_width=True)

        with col3:
            rushing_yd_chart = alt.Chart(player_stat).mark_bar().encode(
                x=alt.X('year_week:O',axis=alt.Axis(title=None)),
                y=alt.Y('Rushing_Yds:Q',axis=alt.Axis(title=None)),
                color=alt.value(team_color),
                opacity=alt.Opacity('year:O', scale=alt.Scale(
                        domain=player_stat['year'].unique().tolist(),  # Ensure the scale covers all years in the data
                        range=[0.3, 1]  # Older years lighter (0.4 opacity), newer years fully opaque (1 opacity)
                    ), legend=None),
                order=alt.Order('year', sort='descending'),
                tooltip=['Player', 'Rushing_Yds', 'year_week']
            ).properties(
                title='Rushing Yards',
                width=600,
                height=qb_ht_page
            )

            # count of values over target
            rush_yds_games = player_stat.loc[player_stat['Rushing_Yds']>=rush_yd_input,'year_week'].nunique()
            rush_yds_perc_games = "{:.0f}%".format((rush_yds_games / num_games)* 100)
            target_rush_line, target_rush_label = target_lines(rush_yd_input,rush_yds_perc_games)

            st.altair_chart(rushing_yd_chart + target_rush_line + target_rush_label, use_container_width=True)

            passing_cmp_chart = alt.Chart(player_stat).mark_bar().encode(
                x=alt.X('year_week:O',axis=alt.Axis(title=None)),
                y=alt.Y('Passing_Cmp:Q',axis=alt.Axis(title=None)),
                color=alt.value(team_color),
                opacity=alt.Opacity('year:O', scale=alt.Scale(
                        domain=player_stat['year'].unique().tolist(),  # Ensure the scale covers all years in the data
                        range=[0.3, 1]  # Older years lighter (0.4 opacity), newer years fully opaque (1 opacity)
                    ), legend=None),
                order=alt.Order('Passing_Cmp', sort='descending'),
                tooltip=['Player', 'Passing_Cmp', 'year_week']
            ).properties(
                title='Passing Completions',
                width=600,
                height=qb_ht_page
            )
            
            # count of values over target
            pass_comp_games = player_stat.loc[player_stat['Passing_Cmp']>=completion_input,'year_week'].nunique()
            pass_comp_perc_games = "{:.0f}%".format((pass_comp_games / num_games)* 100)
            target_comp_line, target_comp_label = target_lines(completion_input,pass_comp_perc_games)

            st.altair_chart(passing_cmp_chart + target_comp_line + target_comp_label, use_container_width=True)

    else:
        with col1:
            st.write(player_pos)
            # old_passing_legend = alt.Chart(player_stat).mark_point(opacity=0).encode(
            #     x='week:O',
            #     y='year:Q',
            #     color=alt.Color('year:N', sort=alt.EncodingSortField(field='year', order='descending')),
            #     order=alt.Order('year', sort='descending'),
            #     tooltip=['Player', 'year', 'week']
            # ).properties(
            #     width=0,
            #     height=150
            # ).configure_legend(
            #     orient='left' # Position the legend on the left
            # ).configure_axis(
            #     grid=False,  # Remove gridlines
            #     labels=False,  # Remove axis labels
            #     ticks=False,
            #     title=None # Remove axis ticks
            # )
            passing_legend = alt.Chart(player_stat).mark_point().encode(
                color=alt.Color('year:O', scale=alt.Scale(
                    domain=sorted(player_stat['year'].unique(), reverse=True),  # Sort years in descending order
                    range=[team_color],  # Use the same color for all years
                ),
                    legend=alt.Legend(
                        title="Year",
                        orient='left',  # Position the legend on the left
                        direction='vertical'  # Make the legend vertical
                    )
                ),
                order=alt.Order('year:O', sort='descending'),  # Sort years in descending order
                opacity=alt.Opacity('year:O', scale=alt.Scale(
                    domain=sorted(player_stat['year'].unique(), reverse=True),  # Ensure opacity scale matches the years
                    range=[1, 0.3]  # Older years lighter, newer years fully opaque
                ), legend=None)
            ).properties(
                width=60,
                height=150
            ).configure_axis(
                grid=False,  # Remove gridlines
                labels=False,  # Remove axis labels
                ticks=False,
                title=None  # Remove axis ticks
            )

            # Display the chart (legend only)
            st.altair_chart(passing_legend)

            # Betting inputs
            rush_yd_input = st.number_input('Rushing Yards Target:', min_value=0, max_value=200, value=0)
            rec_yd_input = st.number_input('Receiving Yards Target:', min_value=0, max_value=200, value=0)
            rush_rec_yd_input = st.number_input('Rushing + Receiving Yards Target:', min_value=0, max_value=300, value=0)
            reception_input = st.number_input("Reception Target:", min_value=0, max_value=15, value=0)
            touchdown_input = st.number_input("Touchdown Target:", min_value=0, max_value=3, value=0)
            longest_yd_input = st.number_input("Longest Reception Target:", min_value=0, max_value=30, value=0)

        with col2:
        ### PASSING
            rushing_yds_chart = alt.Chart(player_stat).mark_bar().encode(
                x=alt.X('year_week:O',axis=alt.Axis(title=None)),
                y=alt.Y('Rushing_Yds:Q',axis=alt.Axis(title=None)),
                color=alt.value(team_color),
                opacity=alt.Opacity('year:O', scale=alt.Scale(
                        domain=player_stat['year'].unique().tolist(),  # Ensure the scale covers all years in the data
                        range=[0.3, 1]  # Older years lighter (0.4 opacity), newer years fully opaque (1 opacity)
                    ), legend=None),
                order=alt.Order('Season_Rushing_Yds', sort='descending'),
                tooltip=['Player', 'Rushing_Yds', 'year_week']
            ).properties(
                title='Rushing Yards',
                height=player_ht_page
            )

            min_value = player_stat['Rushing_Yds'].min()
            avg_value = round(player_stat['Rushing_Yds'].mean(),1)
            max_value = player_stat['Rushing_Yds'].max()
            # Add min, max, average lines
            min_line = alt.Chart(pd.DataFrame({'y': [min_value], 'label': [f'Minimum: {min_value}']})).mark_rule(color='red').encode(
                        y='y:Q'
                    ).properties(
                        title='Minimum'
                    )
            min_label = min_line.mark_text(
                    align='left',
                    baseline='middle',
                    dx=280,
                    dy=-10  # Adjust the position of the text
                ).encode(
                    text='label:N'
                )

            avg_line = alt.Chart(pd.DataFrame({'y': [avg_value], 'label': [f'Average: {avg_value}']})).mark_rule(color='blue').encode(
                        y='y:Q'
                    ).properties(
                        title='Average'
                    )
            
            avg_label = avg_line.mark_text(
                    align='left',
                    baseline='middle',
                    dx=280,
                    dy=-10
                ).encode(
                    text='label:N'
                )

            max_line = alt.Chart(pd.DataFrame({'y': [max_value], 'label': [f'Maximum: {max_value}']})).mark_rule(color='green').encode(
                        y='y:Q'
                    ).properties(
                        title='Maximum'
                    )
            max_label = max_line.mark_text(
                    align='left',
                    baseline='middle',
                    dx=280,
                    dy=-10
                ).encode(
                    text='label:N'
                )
            
            # count of values over target
            rush_games = player_stat.loc[player_stat['Rushing_Yds']>=rush_yd_input,'year_week'].nunique()
            rush_perc_games = "{:.0f}%".format((rush_games / num_games)* 100)
            target_rush_line, target_rush_label = target_lines(rush_yd_input,rush_perc_games)

            # Combine the base chart with the horizontal lines
            final_chart = rushing_yds_chart + min_line + avg_line + target_rush_line+ max_line + min_label + avg_label + max_label + target_rush_label

            # Display the chart in Streamlit
            st.altair_chart(final_chart, use_container_width=True)

            # rush_rec_chart = alt.Chart(player_stat).mark_bar().encode(
            #     x=alt.X('year_week:O',axis=alt.Axis(title=None)),
            #     y=alt.Y('Rushing_Receiving_Yds:Q',axis=alt.Axis(title=None)),
            #     color=alt.Color('year:N', sort=alt.EncodingSortField(field='year', order='descending'),legend=None),
            #     order=alt.Order('Rushing_Receiving_Yds', sort='descending'),
            #     tooltip=['Player', 'Rushing_Receiving_Yds', 'year_week']
            # ).properties(
            #     title='Rushing + Receiving Yards',
            #     width=600,
            #     height=275
            # )

            rush_rec_chart = alt.Chart(player_stat).mark_bar().encode(
                x=alt.X('year_week:O',axis=alt.Axis(title=None)),
                y=alt.Y('Rushing_Receiving_Yds:Q',axis=alt.Axis(title=None)),
                color=alt.value(team_color),
                opacity=alt.Opacity('year:O', scale=alt.Scale(
                        domain=player_stat['year'].unique().tolist(),  # Ensure the scale covers all years in the data
                        range=[0.3, 1]  # Older years lighter (0.4 opacity), newer years fully opaque (1 opacity)
                    ), legend=None),
                order=alt.Order('Rushing_Receiving_Yds', sort='descending'),
                tooltip=['Player', 'Rushing_Receiving_Yds', 'year_week']
            ).properties(
                title='Rushing + Receiving Yards',
                width=600,
                height=player_ht_page
            )


           # count of values over target
            rush_rec_yd_games = player_stat.loc[player_stat['Rushing_Receiving_Yds']>=rush_rec_yd_input,'year_week'].nunique()
            rush_rec_yd_perc_games = "{:.0f}%".format((rush_rec_yd_games / num_games)* 100)
            target_rush_rec_yd_line, target_rush_rec_yd_label = target_lines(rush_rec_yd_input,rush_rec_yd_perc_games)
            st.altair_chart(rush_rec_chart + target_rush_rec_yd_line + target_rush_rec_yd_label, use_container_width=True)

            rushing_receiving_td_chart = alt.Chart(player_stat).mark_bar().encode(
                x=alt.X('year_week:O',axis=alt.Axis(title=None)),
                y=alt.Y('Rushing_Receiving_TD:Q',axis=alt.Axis(title=None)),
                color=alt.value(team_color),
                opacity=alt.Opacity('year:O', scale=alt.Scale(
                        domain=player_stat['year'].unique().tolist(),  # Ensure the scale covers all years in the data
                        range=[0.3, 1]  # Older years lighter (0.4 opacity), newer years fully opaque (1 opacity)
                    ), legend=None),
                order=alt.Order('Rushing_Receiving_TD', sort='descending'),
                tooltip=['Player', 'Rushing_Receiving_TD', 'year_week']
            ).properties(
                title='Rushing + Receiving Touchdowns',
                width=600,
                height=player_ht_page
            )

            # count of values over target
            rush_rec_td_games = player_stat.loc[player_stat['Rushing_Receiving_TD']>=touchdown_input,'year_week'].nunique()
            rush_rec_td_perc_games = "{:.0f}%".format((rush_rec_td_games / num_games)* 100)
            target_rush_rec_td_line, target_rush_rec_td_label = target_lines(touchdown_input,rush_rec_td_perc_games)

            st.altair_chart(rushing_receiving_td_chart + target_rush_rec_td_line + target_rush_rec_td_label, use_container_width=True)

        with col3:
            receiving_yd_chart = alt.Chart(player_stat).mark_bar().encode(
                x=alt.X('year_week:O',axis=alt.Axis(title=None)),
                y=alt.Y('Receiving_Yds:Q',axis=alt.Axis(title=None)),
                color=alt.value(team_color),
                opacity=alt.Opacity('year:O', scale=alt.Scale(
                        domain=player_stat['year'].unique().tolist(),  # Ensure the scale covers all years in the data
                        range=[0.3, 1]  # Older years lighter (0.4 opacity), newer years fully opaque (1 opacity)
                    ), legend=None),
                order=alt.Order('year', sort='descending'),
                tooltip=['Player', 'Receiving_Yds', 'year_week']
            ).properties(
                title='Receiving Yards',
                width=600,
                height=player_ht_page
            )

             # count of values over target
            rec_yd_games = player_stat.loc[player_stat['Receiving_Yds']>=rec_yd_input,'year_week'].nunique()
            rec_yd_perc_games = "{:.0f}%".format((rec_yd_games / num_games)* 100)
            target_rec_yd_line, target_rec_yd_label = target_lines(rec_yd_input,rec_yd_perc_games)

            st.altair_chart(receiving_yd_chart + target_rec_yd_line + target_rec_yd_label, use_container_width=True)


            # Reception and Target Chart
            target_chart = alt.Chart(player_stat).mark_bar(color='lightgray').encode(
                x=alt.X('year_week:O',axis=alt.Axis(title=None)),
                y=alt.Y('Receiving_Tgt:Q',axis=alt.Axis(title=None)),
                order=alt.Order('Receiving_Tgt', sort='descending'),
                tooltip=['Player', 'Receiving_Tgt', 'year_week']
            ).properties(
                title='Receptions',
                width=600,
                height=player_ht_page
            )
            reception_chart = alt.Chart(player_stat).mark_bar().encode(
                x=alt.X('year_week:O',axis=alt.Axis(title=None)),
                y=alt.Y('Receiving_Rec:Q',axis=alt.Axis(title=None)),
                color=alt.value(team_color),
                opacity=alt.Opacity('year:O', scale=alt.Scale(
                        domain=player_stat['year'].unique().tolist(),  # Ensure the scale covers all years in the data
                        range=[0.3, 1]  # Older years lighter (0.4 opacity), newer years fully opaque (1 opacity)
                    ), legend=None),
                order=alt.Order('Receiving_Rec', sort='descending'),
                tooltip=['Player', 'Receiving_Rec', 'year_week']
            )

             # count of values over target
            rec_games = player_stat.loc[player_stat['Receiving_Rec']>=reception_input,'year_week'].nunique()
            rec_perc_games = "{:.0f}%".format((rec_games / num_games)* 100)
            target_rec_line, target_rec_label = target_lines(reception_input,rec_perc_games)

            st.altair_chart(target_chart + reception_chart+ target_rec_line + target_rec_label, use_container_width=True)

            reception_length_chart = alt.Chart(player_stat).mark_bar().encode(
                x=alt.X('year_week:O',axis=alt.Axis(title=None)),
                y=alt.Y('Receiving_Lng:Q',axis=alt.Axis(title=None)),
                color=alt.value(team_color),
                opacity=alt.Opacity('year:O', scale=alt.Scale(
                        domain=player_stat['year'].unique().tolist(),  # Ensure the scale covers all years in the data
                        range=[0.3, 1]  # Older years lighter (0.4 opacity), newer years fully opaque (1 opacity)
                    ), legend=None),
                order=alt.Order('Receiving_Lng', sort='descending'),
                tooltip=['Player', 'Receiving_Lng', 'year_week']
            ).properties(
                title='Longest Reception',
                width=600,
                height=player_ht_page
            )

            
             # count of values over target
            longest_yd_games = player_stat.loc[player_stat['Receiving_Lng']>=longest_yd_input,'year_week'].nunique()
            longest_yd_perc_games = "{:.0f}%".format((longest_yd_games / num_games)* 100)
            target_longest_line, target_longest_label = target_lines(longest_yd_input,longest_yd_perc_games)

            st.altair_chart(reception_length_chart + target_longest_line + target_longest_label, use_container_width=True)
