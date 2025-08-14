# pages/player.py
import streamlit as st
import pandas as pd
import plotly.express as px
from utils import real_teams
import altair as alt

def render(data):
    """
    Player page: show per-player time series and season summary.
    """
    df = data['df'].copy()
    new_year = data['current_year']
    teams = data['teams']
    color_df = data['color_df'].copy()

    title_col1, title_col2, title_col3, title_col4 = st.columns([4,1,0.9,8])
    with title_col1:
        st.title("Player Page")

    # Team selection (optional)
    team_selected = st.sidebar.selectbox("Team (optional)", ["All"] + teams, index=0)
    # team_selected = st.sidebar.selectbox("Select a team", teams, index=0)
    team_color = '#1f77b4'

    try:
        team_color = color_df[color_df['NFL Team Name'] == team_selected]['Color 1'].values[0]
    except Exception:
        pass
    
    if team_selected in list(df['Real_Team'].unique()):
        all_players = sorted(list(df.loc[ 
                                    (df['Real_Team']==team_selected) &
                                    (df['year']==str(new_year)),
                                    'Player'].unique()
                                  )
                            )
    else:
        all_players = sorted(df['Player'].dropna().unique())

    # Player selection: get all players available in df
    player = st.sidebar.selectbox("Select player", all_players, index=0)


        # year multiselect
    year_list = sorted(list(df['year'].unique()))
    with st.sidebar.expander("Select year(s)", expanded=False):
        selected_options = st.multiselect('Years', year_list, default=year_list)

    player_stat = df.loc[
                        (df['Player'] == player) &
                        (df['year'].isin(selected_options))
                    ].copy().reset_index()
    
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
    num_games = df.loc[(df['year'].isin(selected_options) & (df['Player']==player)),'year_week'].nunique()

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
    


    col1, col2, col3 = st.columns([0.4,2,2])

    def year_legend(dataframe):
        if not dataframe.empty:
            legend_chart = alt.Chart(dataframe).mark_point().encode(
                    color=alt.Color('year:O', scale=alt.Scale(
                        domain=sorted(dataframe['year'].unique(), reverse=True),  # Sort years in descending order
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
                        domain=sorted(dataframe['year'].unique(), reverse=True),  # Ensure opacity scale matches the years
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
            
            st.altair_chart(legend_chart)
            return legend_chart
    
    def yards_chart(dataframe, yard_input, yard_type, title, position="Other"):
        if not dataframe.empty:
            if yard_type in ['Passing_Yds', 'Rushing_Yds']:
                season_yard_type = 'Season_' + yard_type
            else:
                season_yard_type = yard_type

            if position == 'QB':
                height = 400
            else:
                height = 250
            
            yards_chart = alt.Chart(dataframe).mark_bar().encode(
                x=alt.X('year_week:O',axis=alt.Axis(title=None)),
                y=alt.Y(f'{yard_type}:Q',axis=alt.Axis(title=None)),
                color=alt.value(team_color),
                opacity=alt.Opacity('year:O', scale=alt.Scale(
                        domain=dataframe['year'].unique().tolist(),  # Ensure the scale covers all years in the data
                        range=[0.3, 1]  # Older years lighter (0.4 opacity), newer years fully opaque (1 opacity)
                    ), legend=None),
                order=alt.Order(f'{season_yard_type}', sort='descending'),
                tooltip=['Player', f'{yard_type}', 'year_week']
            ).properties(
                title=f'{title}',
                height=height
            )

            min_value = dataframe[f'{yard_type}'].min()
            avg_value = round(dataframe[f'{yard_type}'].mean(),1)
            max_value = dataframe[f'{yard_type}'].max()
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
            games = dataframe.loc[dataframe[f'{yard_type}']>=yard_input,'year_week'].nunique()
            perc_games = "{:.0f}%".format((games / num_games)* 100)
            target_line, target_label = target_lines(yard_input, perc_games)
            

            # Combine the base chart with the horizontal lines
            final_chart = yards_chart + min_line + avg_line + max_line + target_line + min_label + avg_label + max_label + target_label
            st.altair_chart(final_chart, use_container_width=True)

            return final_chart, games, perc_games, target_line, target_label
    
    with col1:
        st.write(player_pos)

        if player_pos =="Quarterback":
            passing_legend = year_legend(player_stat)
            
            # Betting inputs
            pass_yd_input = st.number_input('Passing Yards Target:', min_value=0, max_value=500, value=0)
            rush_yd_input = st.number_input('Rushing Yards Target:', min_value=0, max_value=200, value=0)
            passing_td_input = st.number_input("Passing Touchdown Target:", min_value=0, max_value=5, value=0)
            completion_input = st.number_input("Completions Target:", min_value=0, max_value=50, value=0)

        else:
            rushing_legend = year_legend(player_stat)

            # Betting inputs
            rush_yd_input = st.number_input('Rushing Yards Target:', min_value=0, max_value=200, value=0)
            rec_yd_input = st.number_input('Receiving Yards Target:', min_value=0, max_value=200, value=0)
            rush_rec_yd_input = st.number_input('Rushing + Receiving Yards Target:', min_value=0, max_value=300, value=0)
            reception_input = st.number_input("Reception Target:", min_value=0, max_value=15, value=0)
            touchdown_input = st.number_input("Touchdown Target:", min_value=0, max_value=3, value=0)
            longest_yd_input = st.number_input("Longest Reception Target:", min_value=0, max_value=30, value=0)


    with col2:
    ### PASSING
        if player_pos =="Quarterback":

            passing_yds_chart, pass_yd_games, pass_perc_games, target_pass_line, target_pass_label = yards_chart(player_stat, pass_yd_input, "Passing_Yds", "Passing Yards", "QB")
            passing_td_chart, pass_td_games, pass_td_perc_games, target_td_line, target_td_label = yards_chart(player_stat, passing_td_input, "Passing_TD", "Passing Touchdowns", "QB")
 
        else:
            rushing_yds_chart, rush_yd_games, rush_perc_games, target_rush_line, target_rush_label = yards_chart(player_stat, rush_yd_input, "Rushing_Yds", "Rushing Yards")
            rush_rec_chart, rush_rec_yd_games, rush_rec_yd_perc_games, target_rush_rec_yd_line, target_rush_rec_yd_label = yards_chart(player_stat, rush_rec_yd_input, "Rushing_Receiving_Yds", "Rushing + Receiving Yards")
            rushing_receiving_td_chart, rush_rec_td_games, rush_rec_td_perc_games, target_rush_rec_td_line, target_rush_rec_td_label = yards_chart(player_stat, touchdown_input, "Rushing_Receiving_TD", "Rushing + Receiving Touchdowns")
            
    with col3:
        if player_pos == "Quarterback":
            rushing_yd_chart, rush_games, rush_perc_games, target_rush_line, target_rush_label = yards_chart(player_stat, rush_yd_input, "Rushing_Yds", "Rushing Yards", "QB")
            passing_cmp_chart, pass_comp_games, pass_comp_perc_games, target_comp_line, target_comp_label = yards_chart(player_stat, completion_input, "Passing_Cmp", "Passing Completions", "QB")

        else:
            receiving_yd_chart, rush_rec_games, rush_rec_perc_games, target_rush_rec_line, target_rush_rec_label = yards_chart(player_stat, rec_yd_input, "Receiving_Yds", "Receiving Yards")

            #  Reception and Target Chart
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
            

            st.altair_chart(target_chart + reception_chart
                            + target_rec_line + target_rec_label
                            , use_container_width=True)
            

            reception_length_chart, longest_yd_games, longest_yd_perc_games, target_longest_line, target_longest_label = yards_chart(player_stat, longest_yd_input, "Receiving_Lng","Longest Reception")

    st.success("Player page loaded.")
