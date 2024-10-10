import pandas as pd
import numpy as np
import streamlit as st
import os
import altair as alt
import seaborn as sns
from datetime import datetime

# process files
### Configuration setup
st.set_page_config(layout="wide")

path = os.getcwd()
data_path = os.path.join(path, 'data/')
files = os.listdir(data_path)
df = pd.DataFrame()
for file in files:
    new_file = pd.read_csv(data_path + file)
    new_file['week_padded'] = new_file['week'].apply(lambda x: f'{x:02d}') 
    new_file['year'] = file[:4]
    df = pd.concat([df,new_file],axis=0)

# grab current date
current_date = datetime.now()
year = current_date.year
month = current_date.month

# If current month is between January and May (inclusive), add 1 to the year
if 1 <= month <= 5:
    new_year = year + 1
else:
    new_year = year

### Dataframe changes

# year_week
df['year_week'] =df['year'] + '_' + df['week_padded'].astype(str)
# add additional fields
df['Passing_Rushing_Yds'] = df['Passing_Yds'] + df['Rushing_Yds']
df['Rushing_Receiving_Yds'] = df['Rushing_Yds'] + df['Receiving_Yds']
df['Passing_Rushing_Receiving_Yds'] = df['Passing_Yds'] + df['Rushing_Yds'] + df['Receiving_Yds']
df['Rushing_Receiving_TD'] = df['Rushing_TD'] + df['Receiving_TD']


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

# Title of the app
st.title('NFL Stats Dashboard')


# distinct teams
teams = sorted(list(df['Team'].unique()))

### SIDEBAR FILTERS
page = st.sidebar.selectbox("Choose a page", ["Home", "Team", "Player"])
team_selected = st.sidebar.selectbox("Select a team", teams)
year_list = sorted(list(df['year'].unique()))



### YEAR SELECTION ###
with st.sidebar.expander("Select year(s)", expanded=False):
    selected_options = st.multiselect(
        'Years',
        year_list,
        default=year_list
    )
    

# filter to selected team
filtered_df = df[df['Team'].str.contains(team_selected)].reset_index()

# In the second column, you can display Passing visuals/data
# passing = filtered_df[filtered_df['Passing_Yds']>0]
# rushing = filtered_df[filtered_df['Rushing_Yds']>0]
# receiving = filtered_df[filtered_df['Receiving_Yds']>0]
passing = df[df['Passing_Yds']>0]
rushing = df[df['Rushing_Yds']>0]
receiving = df[df['Receiving_Yds']>0]

passing = passing.loc[passing['year'].isin(selected_options)]
rushing = rushing.loc[rushing['year'].isin(selected_options)]
receiving = receiving.loc[receiving['year'].isin(selected_options)]

# Generate a color palette based on the number of unique players
unique_players = filtered_df['Player'].unique()
palette = sns.color_palette("husl", len(unique_players))  # or any other palette
color_mapping = dict(zip(unique_players, palette))

team_roster = sorted(list(df.loc[df['Team']==team_selected,'Player'].unique()))
active_roster = sorted(list(df.loc[(df['year']==str(new_year)) & (df['Team']==team_selected),'Player'].unique()))
space = ' '
st.write("Team:",team_selected, "  |  ", "Active Roster:", ', '.join(active_roster))

### TOP TEN LISTS ###
df_sum = df.groupby(['Player','year']).sum().reset_index()
df_sum = df_sum[df_sum['year']==str(new_year)]
df_sum['Team'] = df_sum['Team'].str[:3]


### PROJECTED STATS ###
max_week = df.groupby(['Team','year']).max().reset_index()
max_week = max_week[max_week['year']==str(new_year)]
max_week = max_week.rename({'week':'max_week'},axis=1)
df_sum = pd.merge(df_sum,max_week[['Team','max_week']],how='left',on='Team')
df_sum['Projected_Pass_Yds'] = (df_sum['Passing_Yds'] / df_sum['max_week']) * 17
df_sum['Projected_Rush_Yds'] = (df_sum['Rushing_Yds'] / df_sum['max_week']) * 17
df_sum['Projected_Rec_Yds'] = (df_sum['Receiving_Yds'] / df_sum['max_week']) * 17
df_sum['Projected_TDs'] = (df_sum['Rushing_Receiving_TD'] / df_sum['max_week']) * 17

# Create four columns
col1, col2, col3, col4= st.columns([0.5,2,2,2])

if page =='Home':
    st.write("TOP TEN")
    home_col1, home_col2, home_col3, home_col4= st.columns([2.5,2.5,2.5,2.5])
    with home_col1:
        passing_top_df = df_sum.sort_values('Passing_Yds',ascending=False).reset_index()
        passing_top_df = passing_top_df.rename({"Passing_Yds":'Pass_Yds'},axis=1)

        passing_top_df['Rank'] = (passing_top_df.index + 1).astype(str) + ': ' + passing_top_df['Player']
        st.dataframe(passing_top_df[['Rank','Team','Pass_Yds','Projected_Pass_Yds']].set_index('Rank'),
                     use_container_width=True,
                     height=210)
    with home_col2:
        rushing_top_df = df_sum.sort_values('Rushing_Yds',ascending=False).reset_index()
        rushing_top_df = rushing_top_df.rename({"Rushing_Yds":'Rush_Yds'},axis=1)

        rushing_top_df['Rank'] = (rushing_top_df.index + 1).astype(str) + ': ' + rushing_top_df['Player']
        st.dataframe(rushing_top_df[['Rank','Team','Rush_Yds','Projected_Rush_Yds']].set_index('Rank'),
                     use_container_width=True,
                     height=210)
    with home_col3:
        receiving_top_df = df_sum.sort_values('Receiving_Yds',ascending=False).reset_index()
        receiving_top_df = receiving_top_df.rename({"Receiving_Yds":'Rec_Yds'},axis=1)

        receiving_top_df['Rank'] = (receiving_top_df.index + 1).astype(str) + ': ' + receiving_top_df['Player']
        st.dataframe(receiving_top_df[['Rank','Team','Rec_Yds','Projected_Rec_Yds']].set_index('Rank'),
                     use_container_width=True,
                     height=210)
    with home_col4:
        rush_rec_top_df = df_sum.sort_values('Rushing_Receiving_TD',ascending=False).reset_index()
        rush_rec_top_df['Rank'] = (rush_rec_top_df.index + 1).astype(str) + ': ' + rush_rec_top_df['Player']
        rush_rec_top_df = rush_rec_top_df.rename({"Rushing_Receiving_TD":'TDs'},axis=1)
        st.dataframe(rush_rec_top_df[['Rank','Team','TDs','Projected_TDs']].set_index('Rank'),
                     use_container_width=True,
                     height=210)

# In the first column, place filters (you can customize based on your needs)
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



    with col1:

    ### PASSING
        st.text("Passing")
        # Create an Altair chart without displaying the bars, just the legend
        passing_legend = alt.Chart(passing).mark_bar(opacity=0).encode(
            x='week:O',
            y='Passing_Yds:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Season_Passing_Yds', order='descending')),
            tooltip=['Player', 'Season_Passing_Yds', 'week']
        ).properties(
            width=600,
            height=400
        ).configure_legend(
            orient='left'  # Position the legend on the left
        )

        # Display the chart in Streamlit
        st.altair_chart(passing_legend, use_container_width=True)

    ### RUSHING
        st.text("Rushing")

        rushing_legend = alt.Chart(rushing).mark_bar(opacity=0).encode(
            x='week:O',
            y='Rushing_Yds:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Season_Rushing_Yds', order='descending')),
            tooltip=['Player', 'Season_Rushing_Yds', 'week']
        ).properties(
            width=600,
            height=400
        ).configure_legend(
            orient='left'  # Position the legend on the left
        )

        # Display the chart in Streamlit
        st.altair_chart(rushing_legend, use_container_width=True)

    ### RECEIVING
        st.text("Receiving")

        receiving_legend = alt.Chart(receiving).mark_bar(opacity=0).encode(
            x='week:O',
            y='Receiving_Yds:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Season_Receiving_Yds', order='descending')),
            tooltip=['Player', 'Season_Receiving_Yds', 'week']
        ).properties(
            width=600,
            height=400
        ).configure_legend(
            orient='left'  # Position the legend on the left
        )

        # Display the chart in Streamlit
        st.altair_chart(receiving_legend, use_container_width=True)

    with col2:
    ### PASSING
        passing_yds_chart = alt.Chart(passing).mark_bar().encode(
            x='year_week:O',
            y='Passing_Yds:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Season_Passing_Yds', order='descending'), legend=None),
            order=alt.Order('Season_Passing_Yds', sort='descending'),
            tooltip=['Player', 'Passing_Yds', 'year_week']
        ).properties(
            title='Passing Yards',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(passing_yds_chart, use_container_width=True)  # Example data

    ### RUSHING
        rushing_yds_chart = alt.Chart(rushing).mark_bar().encode(
            x='year_week:O',
            y='Rushing_Yds:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Season_Rushing_Yds', order='descending'), legend=None),
            order=alt.Order('Season_Rushing_Yds', sort='descending'),
            tooltip=['Player', 'Rushing_Yds', 'year_week']
        ).properties(
            title='Rushing Yards',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(rushing_yds_chart, use_container_width=True)
        
    ### RECEIVING
        receiving_yds_chart = alt.Chart(receiving).mark_bar().encode(
            x='year_week:O',
            y='Receiving_Yds:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Season_Receiving_Yds', order='descending'), legend=None),
            order=alt.Order('Season_Receiving_Yds', sort='descending'),
            tooltip=['Player', 'Receiving_Yds', 'year_week']
        ).properties(
            title='Receiving Yards',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(receiving_yds_chart, use_container_width=True) 

        ### TEST
        test_chart = alt.Chart(filtered_df).mark_bar().encode(
            x='year_week:O',
            y='Passing_Yds:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Passing_Rushing_Receiving_Yds', order='descending')),
            order=alt.Order('Season_Passing_Yds', sort='descending'),
            tooltip=['Player', 'Passing_Yds', 'year_week']
        ).properties(
            title='Passing Yards',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(test_chart, use_container_width=True) 

    with col3:
    ### PASSING
        passing_td_chart = alt.Chart(passing).mark_bar().encode(
            x='year_week:O',
            y='Passing_TD:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Season_Passing_Yds', order='descending'),legend=None),
            order=alt.Order('Season_Passing_Yds', sort='descending'),
            tooltip=['Player', 'Passing_TD', 'year_week']
        ).properties(
            title='Passing Touchdowns',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(passing_td_chart, use_container_width=True) 

    ### RUSHING
        rushing_td_chart = alt.Chart(rushing).mark_bar().encode(
            x='year_week:O',
            y='Rushing_TD:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Season_Rushing_Yds', order='descending'),legend=None),
            order=alt.Order('Season_Rushing_Yds', sort='descending'),
            tooltip=['Player', 'Rushing_TD', 'year_week']
        ).properties(
            title='Rushing Touchdowns',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(rushing_td_chart, use_container_width=True)

    ### RECEIVING
        receiving_td_chart = alt.Chart(receiving).mark_bar().encode(
            x='year_week:O',
            y='Receiving_TD:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Season_Receiving_Yds', order='descending'),legend=None),
            order=alt.Order('Season_Receiving_Yds', sort='descending'),
            tooltip=['Player', 'Receiving_TD', 'year_week']
        ).properties(
            title='Receiving Touchdowns',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(receiving_td_chart, use_container_width=True) 

            ### TEST
        test_chart = alt.Chart(filtered_df).mark_bar().encode(
            x='year_week:O',
            y='Rushing_Yds:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Passing_Rushing_Receiving_Yds', order='descending')),
            order=alt.Order('Season_Rushing_Yds', sort='descending'),
            tooltip=['Player', 'Rushing_Yds', 'year_week']
        ).properties(
            title='Rushing Yards',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(test_chart, use_container_width=True)  

    with col4:
    ### PASSING
        passing_rushing_yds_chart = alt.Chart(passing).mark_bar().encode(
            x='year_week:O',
            y='Passing_Rushing_Yds:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Season_Passing_Yds', order='descending'),legend=None),
            order=alt.Order('Season_Passing_Yds', sort='descending'),
            tooltip=['Player', 'Passing_Rushing_Yds', 'year_week']
        ).properties(
            title='Passing + Rushing Yards',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(passing_rushing_yds_chart, use_container_width=True) 

    ### RUSHING
        rushing_receiving_yds_chart = alt.Chart(rushing).mark_bar().encode(
            x='year_week:O',
            y='Rushing_Receiving_Yds:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Season_Rushing_Yds', order='descending'),legend=None),
            order=alt.Order('Season_Rushing_Yds', sort='descending'),
            tooltip=['Player', 'Rushing_Receiving_Yds', 'year_week']
        ).properties(
            title='Rushing + Receiving Yards',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(rushing_receiving_yds_chart, use_container_width=True) 

    ### RECEIVING
        receiving_target_chart = alt.Chart(receiving).mark_bar().encode(
            x='year_week:O',
            y='Receiving_Rec:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Passing_Rushing_Receiving_Yds', order='descending'),legend=None),
            order=alt.Order('Season_Receiving_Yds', sort='descending'),
            tooltip=['Player', 'Receiving_Rec', 'year_week']
        ).properties(
            title='Receiving Receptions',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(receiving_target_chart, use_container_width=True) 
                ### TEST
        
        test_chart = alt.Chart(filtered_df).mark_bar().encode(
            x='year_week:O',
            y='Receiving_Yds:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Season_Passing_Yds', order='descending')),
            order=alt.Order('Season_Receiving_Yds', sort='descending'),
            tooltip=['Player', 'Receiving_Yds', 'year_week']
        ).properties(
            title='Receiving Yards',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(test_chart, use_container_width=True)  

elif page == "Player":
    col1, col2, col3 = st.columns([0.5,2,2])

    team_roster = sorted(list(df.loc[df['Team']==team_selected,'Player'].unique()))
    player = st.sidebar.selectbox("Select a player", team_roster)

    player_stat = df.loc[df['Player']==player].reset_index()

    player_stat = player_stat.loc[player_stat['year'].isin(selected_options)].reset_index()
    season_pass = player_stat['Season_Passing_Yds'][0] 
    season_rush = player_stat['Season_Rushing_Yds'][0] 
    season_rec = player_stat['Season_Receiving_Yds'][0] 

    ### ADDED INFO TO SIDEBAR ###
    qb_active_list = sorted(list(df.loc[(df['Player_Category']=='Quarterback') & 
                                  (df['Team']==team_selected) &
                                  (df['year']==str(new_year)),'Player'].unique()))
    rb_active_list = sorted(list(df[(df['Player_Category']=='Running Back') & 
                                  (df['Team']==team_selected) &
                                  (df['year']==str(new_year))]['Player'].unique()))
    rec_active_list = sorted(list(df[(df['Player_Category']=='Receiver') & 
                                  (df['Team']==team_selected) &
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


    if player_pos =="Quarterback":
        with col1:
            st.write(player_pos)
            passing_legend = alt.Chart(player_stat).mark_point(opacity=0).encode(
                x='week:O',
                y='year:Q',
                color=alt.Color('year:N', sort=alt.EncodingSortField(field='year', order='descending')),
                order=alt.Order('year', sort='descending'),
                tooltip=['Player', 'year', 'week']
            ).properties(
                width=0,
                height=0
            ).configure_legend(
                orient='left' # Position the legend on the left
            ).configure_axis(
                grid=False,  # Remove gridlines
                labels=False,  # Remove axis labels
                ticks=False,
                title=None # Remove axis ticks
            )

            # Display the chart in Streamlit
            st.altair_chart(passing_legend, use_container_width=True)


        with col2:
        ### PASSING
            passing_yds_chart = alt.Chart(player_stat).mark_line().encode(
                x='year_week:O',
                y='Passing_Yds:Q',
                color=alt.Color('year:N', sort=alt.EncodingSortField(field='year', order='descending'),legend=None),
                order=alt.Order('Season_Passing_Yds', sort='descending'),
                tooltip=['Player', 'Passing_Yds', 'year_week']
            ).properties(
                title='Passing Yards',
                height=400
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

            # Combine the base chart with the horizontal lines
            final_chart = passing_yds_chart + min_line + avg_line + max_line + min_label + avg_label + max_label

            # Display the chart in Streamlit
            st.altair_chart(final_chart, use_container_width=True)

            passing_td_chart = alt.Chart(player_stat).mark_bar().encode(
                x='year_week:O',
                y='Passing_TD:Q',
                color=alt.Color('year:N', sort=alt.EncodingSortField(field='year', order='descending'),legend=None),
                order=alt.Order('Passing_TD', sort='descending'),
                tooltip=['Player', 'Passing_TD', 'year_week']
            ).properties(
                title='Passing Touchdowns',
                width=600,
                height=400
            )

            st.altair_chart(passing_td_chart, use_container_width=True)

        with col3:
            rushing_yd_chart = alt.Chart(player_stat).mark_line().encode(
                x='year_week:O',
                y='Rushing_Yds:Q',
                color=alt.Color('year:N', sort=alt.EncodingSortField(field='year', order='descending'),legend=None),
                order=alt.Order('year', sort='descending'),
                tooltip=['Player', 'Rushing_Yds', 'year_week']
            ).properties(
                title='Rushing Yards',
                width=600,
                height=400
            )

            st.altair_chart(rushing_yd_chart, use_container_width=True)

            passing_cmp_chart = alt.Chart(player_stat).mark_bar().encode(
                x='year_week:O',
                y='Passing_Cmp:Q',
                color=alt.Color('year:N', sort=alt.EncodingSortField(field='year', order='descending'),legend=None),
                order=alt.Order('Passing_Cmp', sort='descending'),
                tooltip=['Player', 'Passing_Cmp', 'year_week']
            ).properties(
                title='Passing Completions',
                width=600,
                height=400
            )

            st.altair_chart(passing_cmp_chart, use_container_width=True)


        # with col4:
        #       # Create the bar chart
        #     combined_yards = alt.Chart(melted_stat).mark_bar().encode(
        #         x='year_week:O',
        #         y='Yards:Q',
        #         color=alt.Color('Yard_Type:N', sort=alt.EncodingSortField(field='Yard_Type', order='ascending'), legend=None),
        #         order=alt.Order('Yards', sort='descending'),
        #         tooltip=['Player', 'Yard_Type','Yards', 'year_week']
        #     ).properties(
        #         width=600,
        #         height=400,
        #         title="Passing + Rushing Yards"
        #     )

        #     # Display the chart in Streamlit
        #     st.altair_chart(combined_yards, use_container_width=True)


    else:
        with col1:
            st.write(player_pos)
            passing_legend = alt.Chart(player_stat).mark_point(opacity=0).encode(
                x='week:O',
                y='year:Q',
                color=alt.Color('year:N', sort=alt.EncodingSortField(field='year', order='descending')),
                order=alt.Order('year', sort='descending'),
                tooltip=['Player', 'year', 'week']
            ).properties(
                width=0,
                height=0
            ).configure_legend(
                orient='left' # Position the legend on the left
            ).configure_axis(
                grid=False,  # Remove gridlines
                labels=False,  # Remove axis labels
                ticks=False,
                title=None # Remove axis ticks
            )

            # Display the chart in Streamlit
            st.altair_chart(passing_legend, use_container_width=True)


        with col2:
        ### PASSING
            rushing_yds_chart = alt.Chart(player_stat).mark_line().encode(
                x='year_week:O',
                y='Rushing_Yds:Q',
                color=alt.Color('year:N', sort=alt.EncodingSortField(field='year', order='descending'),legend=None),
                order=alt.Order('Season_Rushing_Yds', sort='descending'),
                tooltip=['Player', 'Rushing_Yds', 'year_week']
            ).properties(
                title='Rushing Yards',
                height=275
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

            # Combine the base chart with the horizontal lines
            final_chart = rushing_yds_chart + min_line + avg_line + max_line + min_label + avg_label + max_label

            # Display the chart in Streamlit
            st.altair_chart(final_chart, use_container_width=True)

            target_chart = alt.Chart(player_stat).mark_bar().encode(
                x='year_week:O',
                y='Receiving_Tgt:Q',
                color=alt.Color('year:N', sort=alt.EncodingSortField(field='year', order='descending'),legend=None),
                order=alt.Order('Receiving_Tgt', sort='descending'),
                tooltip=['Player', 'Receiving_Tgt', 'year_week']
            ).properties(
                title='Targets',
                width=600,
                height=275
            )

            st.altair_chart(target_chart, use_container_width=True)

            rushing_receiving_td_chart = alt.Chart(player_stat).mark_bar().encode(
                x='year_week:O',
                y='Rushing_Receiving_TD:Q',
                color=alt.Color('year:N', sort=alt.EncodingSortField(field='year', order='descending'),legend=None),
                order=alt.Order('Rushing_Receiving_TD', sort='descending'),
                tooltip=['Player', 'Rushing_Receiving_TD', 'year_week']
            ).properties(
                title='Rushing + Receiving Touchdowns',
                width=600,
                height=275
            )

            st.altair_chart(rushing_receiving_td_chart, use_container_width=True)

        with col3:
            receiving_yd_chart = alt.Chart(player_stat).mark_line().encode(
                x='year_week:O',
                y='Receiving_Yds:Q',
                color=alt.Color('year:N', sort=alt.EncodingSortField(field='year', order='descending'),legend=None),
                order=alt.Order('year', sort='descending'),
                tooltip=['Player', 'Receiving_Yds', 'year_week']
            ).properties(
                title='Receiving Yards',
                width=600,
                height=275
            )

            st.altair_chart(receiving_yd_chart, use_container_width=True)

            reception_chart = alt.Chart(player_stat).mark_bar().encode(
                x='year_week:O',
                y='Receiving_Rec:Q',
                color=alt.Color('year:N', sort=alt.EncodingSortField(field='year', order='descending'),legend=None),
                order=alt.Order('Receiving_Rec', sort='descending'),
                tooltip=['Player', 'Receiving_Rec', 'year_week']
            ).properties(
                title='Receptions',
                width=600,
                height=275
            )

            st.altair_chart(reception_chart, use_container_width=True)

            reception_length_chart = alt.Chart(player_stat).mark_bar().encode(
                x='year_week:O',
                y='Receiving_Lng:Q',
                color=alt.Color('year:N', sort=alt.EncodingSortField(field='year', order='descending'),legend=None),
                order=alt.Order('Receiving_Lng', sort='descending'),
                tooltip=['Player', 'Receiving_Lng', 'year_week']
            ).properties(
                title='Longest Reception',
                width=600,
                height=275
            )

            st.altair_chart(reception_length_chart, use_container_width=True)
