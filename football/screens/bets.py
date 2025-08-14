# pages/bets.py
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
    new_year = data['current_year']
    path = data['path']
    logo_path = data['logo_path']

    st.title("Bets")
    # year multiselect
    year_list = sorted(list(df['year'].unique()))
    with st.sidebar.expander("Select year(s)", expanded=False):
        selected_options = st.multiselect('Years', year_list, default=year_list)

    co1, co2, co3, co4= st.columns([0.5,2,0.5,2])
    ht_df = 140
        # Betting inputs
    with co1:
        pass_yd_input = st.number_input('Passing Yards Target:', min_value=0, max_value=500, value=0)
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
        rush_yd_input = st.number_input('Rushing Yards Target:', min_value=0, max_value=200, value=0)
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
        rec_yd_input = st.number_input('Receiving Yards Target:', min_value=0, max_value=200, value=0)
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
        rush_rec_yd_input = st.number_input('Rushing + Receiving Yards Target:', min_value=0, max_value=300, value=0)

        selected_years_df = df.loc[df['year'].isin(selected_options)]
        num_games_bets = selected_years_df['year_week'].nunique()

        def color_gradient(val):
            if val >= 50:
                # Transition from green to yellow as value goes from 66 to 100
                red = int(255 * (1 - (val - 50) / 50))  # Red increases as val decreases from 100 to 66
                green = 255  # Full green for values >= 66
            elif 25 <= val < 50:
                # Transition from yellow to red as value goes from 33 to 66
                red = 255  # Full red
                green = int(255 * ((val - 25) / 25))  # Green decreases as val decreases from 66 to 33
            else:
                # Full red for values below 33
                red = 255
                green = 0

            color = f'rgba({red}, {green}, 0, 1)'  # RGB color from green to yellow to red
            return f'background-color: {color}; color: black;'

        def bet_df(stat, target_input):

            max_year_df = selected_years_df.groupby('Player').agg({'year': 'max'}).reset_index()
            max_year_df = max_year_df.rename({'year':'year_max'},
                                            axis=1)
            df_count = selected_years_df.groupby('Player').count().reset_index()
            df_count = df_count.rename({'year_week':'Total_games'},
                                    axis=1)
            df_stat = selected_years_df.loc[selected_years_df[stat]>=target_input]
            df_stat = df_stat.groupby('Player').count().reset_index()
            df_stat = df_stat.rename({'year_week':'Count_games'},
                                    axis=1)
            df_stat = pd.merge(df_stat, df_count[['Player','Total_games']],how='left',on='Player')
            df_stat = pd.merge(df_stat, max_year_df[['Player','year_max']],how='left',on='Player')
            df_stat = df_stat.loc[df_stat['year_max']==str(new_year)]
            df_stat['% of Games'] = round((df_stat['Count_games'] / df_stat['Total_games']) * 100, 1)
            df_stat = df_stat.sort_values(['Count_games','% of Games'], ascending=False).reset_index()
            df_final = df_stat[['Player','Count_games','Total_games','% of Games']]
            df_final = df_final.style.applymap(color_gradient,subset=['% of Games']).format({'% of Games': '{:.1f}'})
            return df_final
        

        
        df_pass = bet_df('Passing_Yds',pass_yd_input)
        df_rush = bet_df('Rushing_Yds',rush_yd_input)
        df_rec = bet_df('Receiving_Yds',rec_yd_input)
        df_rush_rec = bet_df('Rushing_Receiving_Yds',rush_rec_yd_input)


    with co2:
        st.write('Passing Yards')
        st.dataframe(df_pass, height=ht_df, use_container_width=True)
        st.write('Rushing Yards')
        st.dataframe(df_rush, height=ht_df, use_container_width=True)
        st.write('Receiving Yards')
        st.dataframe(df_rec, height=ht_df, use_container_width=True)
        st.write('Rushing + Receiving Yards')
        st.dataframe(df_rush_rec, height=ht_df, use_container_width=True)




    with co3:
        reception_input = st.number_input("Reception Target:", min_value=0, max_value=15, value=0)
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)

        passing_td_input = st.number_input("Passing Touchdown Target:", min_value=0, max_value=5, value=0)
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)

        touchdown_input = st.number_input("Touchdown Target:", min_value=0, max_value=3, value=0)
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)

        longest_yd_input = st.number_input("Longest Reception Target:", min_value=0, max_value=30, value=0)
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)

        df_rec_comp = bet_df('Receiving_Rec',reception_input)
        df_pass_td = bet_df('Passing_TD',passing_td_input)
        df_rush_rec_td = bet_df('Rushing_Receiving_TD',touchdown_input)
        df_rec_long = bet_df('Receiving_Lng',longest_yd_input)

    with co4:
        st.write('Receptions')
        st.dataframe(df_rec_comp, height=ht_df, use_container_width=True)
        st.write('Passing Touchdowns')
        st.dataframe(df_pass_td, height=ht_df, use_container_width=True)
        st.write('Rushing + Receiving Touchdowns')
        st.dataframe(df_rush_rec_td, height=ht_df, use_container_width=True)
        st.write('Longest Reception')
        st.dataframe(df_rec_long, height=ht_df, use_container_width=True)