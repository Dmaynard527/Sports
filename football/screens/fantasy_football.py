# pages/fantasy_football.py
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import plotly.express as px
import matplotlib.pyplot as plt
import os
from utils import highlight_team, real_teams, target_lines

def render(data):
    df = data['df'].copy()
    # new_year = data['current_year']
    # path = data['path']
    # logo_path = data['logo_path']

    st.title("Fantasy Football")
    # year multiselect
    year_list = sorted(list(df['year'].unique()))
    with st.sidebar.expander("Select year(s)", expanded=False):
        selected_options = st.multiselect('Years', year_list, default=year_list)
   
    col1, co12, col3 = st.columns([2, 0.1, 2])
    col11, col22 = st.columns([2, 2])
    ht_df = 640
    def calculate_fantasy_points(df):
        """
        Adds a `fantasy_points` column to the DataFrame based on common scoring rules:
        - 1 pt per 25 passing yards
        - 4 pts per passing TD
        - 0.1 pt per rushing yard
        """
        df = df.copy()
        df["half_ppr"] = (
            df["Passing_Yds"] / 25 +
            df["Passing_TD"] * 4 -
            df["Passing_Int"] * 2 +
            df["Rushing_Yds"] * 0.1 +
            df["Rushing_TD"] * 6 +
            df["Receiving_Rec"] * 0.5 +
            df["Receiving_Yds"] * 0.1 +
            df["Receiving_TD"] * 6 -
            df["Fumbles_FL"] * 2
        )

        df["ppr"] = (
            df["Passing_Yds"] / 25 +
            df["Passing_TD"] * 4 -
            df["Passing_Int"] * 2 +
            df["Rushing_Yds"] * 0.1 +
            df["Rushing_TD"] * 6 +
            df["Receiving_Rec"] * 1 +
            df["Receiving_Yds"] * 0.1 +
            df["Receiving_TD"] * 6 -
            df["Fumbles_FL"] * 2
        )
        # return df
        return df[[
                'Player',
                'Player_team',
                'Player_Category',
                'Opposing_team',
                'year',
                'week',
                'Passing_Yds',
                'Passing_TD',
                'Passing_Int',
                'Rushing_Yds',
                'Rushing_TD',
                'Receiving_Rec',
                'Receiving_Yds',
                'Receiving_TD',
                'Fumbles_FL',
                'half_ppr',
                'ppr'
                ]]

    def identify_opponent(df):
        df = df.copy()

                # Create 'Player_team' column
        df['Player_team'] = np.where((df['Team'] == df['tm_alias']) | (df['Team'].str.lower() == df['tm_alt_alias']), 
                                    df['tm_market'] + ' ' + df['tm_name'], 
                                    df['opp_market'] + ' ' + df['opp_name']
                                    )

        # Create 'Opposing_team' column
        df['Opposing_team'] = np.where((df['Team'] == df['tm_alias']) | (df['Team'].str.lower() == df['tm_alt_alias']), 
                                    df['opp_market'] + ' ' + df['opp_name'], 
                                    df['tm_market'] + ' ' + df['tm_name']
                                    )
        return df
    df = identify_opponent(df)
    selected_df = df.loc[(df['year'].isin(selected_options))]

    calc_df = calculate_fantasy_points(selected_df)

    sum_half_ppr_year = calc_df.groupby(['Player','year'], as_index=False).sum()[['Player','year','half_ppr']]
    sum_half_ppr_year = sum_half_ppr_year.rename({'half_ppr':'total_half_ppr'}, axis=1)
    calc_df = pd.merge(calc_df, sum_half_ppr_year, how='left', on=['Player','year'])

    avg_half_ppr = sum_half_ppr_year.groupby(['Player'], as_index=False).mean(numeric_only=True)[['Player','total_half_ppr']]
    avg_half_ppr = avg_half_ppr.rename({'total_half_ppr':'avg_half_ppr'}, axis=1)
    calc_df = pd.merge(calc_df, avg_half_ppr, how='left', on='Player')

    # Filter by position
    with col1:
        position = st.selectbox("Choose position", calc_df['Player_Category'].unique())
        top_rank = st.selectbox("Top rank:", list(range(1, 101)))

    filtered_df = calc_df[calc_df['Player_Category'] == position]

    # Sort by fantasy score
    top_players = filtered_df.sort_values(by='total_half_ppr', ascending=False)

    yearly_totals = (
        top_players
        .drop_duplicates(subset=['Player', 'year'])
        [['Player', 'Player_team', 'year', 'total_half_ppr', 'avg_half_ppr']]
        .sort_values(['year', 'total_half_ppr'], ascending=[True, False]) 
    )

    # Find the most recent year in your data
    latest_year = top_players['year'].max()


    last_year_top_players = yearly_totals[yearly_totals['year'] == latest_year]
    last_year_top_players['rank'] = last_year_top_players.groupby('year')['total_half_ppr'] \
        .rank(method='first', ascending=False)


    # Determine player order based on last year's rank
    player_order = last_year_top_players.sort_values('total_half_ppr', ascending=True)['Player']
    player_order = list(player_order[::-1])
    with col3:
        exclude_player = list(st.multiselect("Exclude Players:", player_order, default=None))
        bottom_rank = st.selectbox("Bottom rank:", list(range(1, 101)), index=29)

    # combined_player_list =  [x for x in player_order if x not in exclude_player]

    top_ranked_players = (
       last_year_top_players[
            (last_year_top_players['rank'] >= top_rank) & 
            (last_year_top_players['rank'] <= bottom_rank)
        ]
    ) 
    player_order_top_ranked = list(top_ranked_players['Player'])


    combined_player_list =  [x for x in player_order_top_ranked if x not in exclude_player]


    # Filter to only those players (for all years)
    yearly_totals_top50 = yearly_totals[yearly_totals['Player'].isin(combined_player_list)]

    yearly_totals_top50['label_to_show'] = yearly_totals_top50.apply(
        lambda row: round(row['avg_half_ppr'], 0) if row['year'] == latest_year else np.nan,
        axis=1
    )
    # Plot
    ######### BAR PLOT ##########
    fig = px.bar(
        yearly_totals_top50,
        x='total_half_ppr',
        y='Player',
        color='year',
        orientation='h',
        title=f'Fantasy Points - {position}s',
        text='label_to_show',
        labels={
            'total_half_ppr': 'Fantasy Points',
            'Player': 'Player',
            'year': 'Year'
        },
        category_orders={
            'year': sorted(yearly_totals_top50['year'].unique()),
            'Player': list(combined_player_list)  # order by last year's rank
        }
        # ,
        # barmode='group'          # show side-by-side bars for different years
    )
    fig.update_traces(
        texttemplate='%{text:.0f}',  # show as integer, no decimals
        textposition='outside'      # place text at the end (outside) of the bar
    )

    fig.update_layout(
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )
    
    fig.update_layout(height=ht_df)
    st.plotly_chart(fig)
    year_list = [
                    latest_year,
                    str(int(latest_year) - 1),
                    str(int(latest_year) - 2),
                    str(int(latest_year) - 3),
                    str(int(latest_year) - 4)
                ]
    yearly_totals_top50_recent_year = yearly_totals_top50[yearly_totals_top50['year'].isin(year_list)]
    yearly_totals_top50_recent_year = yearly_totals_top50_recent_year.sort_values("total_half_ppr", ascending=False)
    yearly_totals_top50_recent_year["Rank"] = yearly_totals_top50_recent_year.groupby('year')["total_half_ppr"].rank(ascending=False, method="first")   

    # -----------------------
    # Scatter plot
    # -----------------------

    # Line chart showing gaps between ranks
    st.subheader("Gaps Between Players")
    hover_columns = ["year", "Rank", "Player", "Player_team", "total_half_ppr"]
    line_fig = px.line(
        yearly_totals_top50_recent_year,
        x="Rank",
        y="total_half_ppr",
        color="year",
        facet_col="year",
        markers=True,
        text='Player',
        hover_data={col: True for col in hover_columns},
        title=f"Fantasy Points Gap by Player ({', '.join(year_list)})"
    )
    line_fig.update_traces(textposition="top center")
    st.plotly_chart(line_fig, use_container_width=True)
    #### DEEPER DIVE per Player ####
    
    selected_player = st.selectbox("Choose a Player For a Deeper Dive", combined_player_list)

    filtered_player_df = filtered_df.loc[filtered_df['Player']==selected_player]

    ######## DISTRIBUTION PLOTS ########
    # Calculate stats per year
    stats = (
        filtered_player_df
        .groupby('year')['half_ppr']
        .describe(percentiles=[0.25, 0.5, 0.75])
        .reset_index()
    )

    # Rename columns for clarity
    stats = stats.rename(columns={
        'min': 'min',
        '25%': 'q1',
        '50%': 'median',
        '75%': 'q3',
        'max': 'max'
    })

    fig = px.box(
                filtered_player_df, 
                x='year', 
                y='half_ppr', 
                points="all", 
                title=f"Fantasy Score Distribution by Year for {selected_player}"
                )

    # Add annotations for max, median, and min per year
    for _, row in stats.iterrows():
        x = row['year']
        for label, y_val, yshift in [
            ('Max', row['max'], 10),
            ('Median', row['median'], 0),
            ('Min', row['min'], -10),
        ]:
            fig.add_annotation(
                x=x,
                y=y_val,
                text=f"<b>{label}: {y_val:.1f}</b>",
                showarrow=False,
                yshift=yshift,
                font=dict(size=14),
                align='center'
            )

        # Change box color to orange
    fig.update_traces(
        marker_color='orange',       # points color
        line_color='orange',         # box outline color
        fillcolor='rgba(255,165,0,0.3)'  # transparent orange fill inside box
    )


    fig.update_layout(height=ht_df - 240)
    st.plotly_chart(fig)

    # Create dataframe for player specific stat
    st.dataframe(filtered_player_df)

