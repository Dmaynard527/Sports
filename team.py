import pandas as pd
import numpy as np
import streamlit as st
import os
import altair as alt
import seaborn as sns


# In the first column, place filters (you can customize based on your needs)
def main():
    with col1:
        st.text("Filters")
        # Example filter
        team_selected = st.selectbox("Select a team", teams)

    filtered_df = df[df['Team']==team_selected]
    # In the second column, you can display Passing visuals/data
    passing = filtered_df[filtered_df['Passing_Yds']>0]
    rushing = filtered_df[filtered_df['Rushing_Yds']>0]
    receiving = filtered_df[filtered_df['Receiving_Yds']>0]

    # Generate a color palette based on the number of unique players
    unique_players = filtered_df['Player'].unique()
    palette = sns.color_palette("husl", len(unique_players))  # or any other palette
    color_mapping = dict(zip(unique_players, palette))


    with col2:

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

    with col3:
    ### PASSING
        passing_yds_chart = alt.Chart(passing).mark_bar().encode(
            x='week:O',
            y='Passing_Yds:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Season_Passing_Yds', order='descending'), legend=None),
            order=alt.Order('Season_Passing_Yds', sort='descending'),
            tooltip=['Player', 'Passing_Yds', 'week']
        ).properties(
            title='Passing Yards',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(passing_yds_chart, use_container_width=True)  # Example data

    ### RUSHING
        rushing_yds_chart = alt.Chart(rushing).mark_bar().encode(
            x='week:O',
            y='Rushing_Yds:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Season_Rushing_Yds', order='descending'), legend=None),
            order=alt.Order('Season_Rushing_Yds', sort='descending'),
            tooltip=['Player', 'Rushing_Yds', 'week']
        ).properties(
            title='Rushing Yards',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(rushing_yds_chart, use_container_width=True)
        
    ### RECEIVING
        receiving_yds_chart = alt.Chart(receiving).mark_bar().encode(
            x='week:O',
            y='Receiving_Yds:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Season_Receiving_Yds', order='descending'), legend=None),
            order=alt.Order('Season_Receiving_Yds', sort='descending'),
            tooltip=['Player', 'Receiving_Yds', 'week']
        ).properties(
            title='Receiving Yards',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(receiving_yds_chart, use_container_width=True) 

        ### TEST
        test_chart = alt.Chart(filtered_df).mark_bar().encode(
            x='week:O',
            y='Passing_Yds:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Passing_Rushing_Receiving_Yds', order='descending')),
            order=alt.Order('Season_Passing_Yds', sort='descending'),
            tooltip=['Player', 'Passing_Yds', 'week']
        ).properties(
            title='Passing Yards',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(test_chart, use_container_width=True) 

    with col4:
    ### PASSING
        passing_td_chart = alt.Chart(passing).mark_bar().encode(
            x='week:O',
            y='Passing_TD:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Season_Passing_Yds', order='descending'),legend=None),
            order=alt.Order('Season_Passing_Yds', sort='descending'),
            tooltip=['Player', 'Passing_TD', 'week']
        ).properties(
            title='Passing Touchdowns',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(passing_td_chart, use_container_width=True) 

    ### RUSHING
        rushing_td_chart = alt.Chart(rushing).mark_bar().encode(
            x='week:O',
            y='Rushing_TD:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Season_Rushing_Yds', order='descending'),legend=None),
            order=alt.Order('Season_Rushing_Yds', sort='descending'),
            tooltip=['Player', 'Rushing_TD', 'week']
        ).properties(
            title='Rushing Touchdowns',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(rushing_td_chart, use_container_width=True)

    ### RECEIVING
        receiving_td_chart = alt.Chart(receiving).mark_bar().encode(
            x='week:O',
            y='Receiving_TD:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Season_Receiving_Yds', order='descending'),legend=None),
            order=alt.Order('Season_Receiving_Yds', sort='descending'),
            tooltip=['Player', 'Receiving_TD', 'week']
        ).properties(
            title='Receiving Touchdowns',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(receiving_td_chart, use_container_width=True) 

            ### TEST
        test_chart = alt.Chart(filtered_df).mark_bar().encode(
            x='week:O',
            y='Rushing_Yds:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Passing_Rushing_Receiving_Yds', order='descending')),
            order=alt.Order('Season_Rushing_Yds', sort='descending'),
            tooltip=['Player', 'Rushing_Yds', 'week']
        ).properties(
            title='Rushing Yards',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(test_chart, use_container_width=True)  

    with col5:
    ### PASSING
        passing_rushing_yds_chart = alt.Chart(passing).mark_bar().encode(
            x='week:O',
            y='Passing_Rushing_Yds:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Season_Passing_Yds', order='descending'),legend=None),
            order=alt.Order('Season_Passing_Yds', sort='descending'),
            tooltip=['Player', 'Passing_Rushing_Yds', 'week']
        ).properties(
            title='Passing + Rushing Yards',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(passing_rushing_yds_chart, use_container_width=True) 

    ### RUSHING
        rushing_receiving_yds_chart = alt.Chart(rushing).mark_bar().encode(
            x='week:O',
            y='Rushing_Receiving_Yds:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Season_Rushing_Yds', order='descending'),legend=None),
            order=alt.Order('Season_Rushing_Yds', sort='descending'),
            tooltip=['Player', 'Rushing_Receiving_Yds', 'week']
        ).properties(
            title='Rushing + Receiving Yards',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(rushing_receiving_yds_chart, use_container_width=True) 

    ### RECEIVING
        receiving_target_chart = alt.Chart(receiving).mark_bar().encode(
            x='week:O',
            y='Receiving_Rec:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Passing_Rushing_Receiving_Yds', order='descending'),legend=None),
            order=alt.Order('Season_Receiving_Yds', sort='descending'),
            tooltip=['Player', 'Receiving_Rec', 'week']
        ).properties(
            title='Receiving Receptions',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(receiving_target_chart, use_container_width=True) 
                ### TEST
        
        test_chart = alt.Chart(filtered_df).mark_bar().encode(
            x='week:O',
            y='Receiving_Yds:Q',
            color=alt.Color('Player:N', sort=alt.EncodingSortField(field='Season_Passing_Yds', order='descending')),
            order=alt.Order('Season_Receiving_Yds', sort='descending'),
            tooltip=['Player', 'Receiving_Yds', 'week']
        ).properties(
            title='Receiving Yards',
            width=600,
            height=400
        )

        # Display the chart in Streamlit
        st.altair_chart(test_chart, use_container_width=True)  
    return None