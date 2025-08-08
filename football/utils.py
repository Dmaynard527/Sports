# utils.py
import altair as alt
import pandas as pd

# Small mapping used in original
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
    'WAS':'Washington Commanders'
}
reversed_real_teams = {v:k for k,v in real_teams.items()}

def target_lines(input_value, perc_of_games):
    """
    Returns an altair rule and label similar to original
    """
    df = pd.DataFrame({'y': [input_value], 'label': [f'Target: {input_value}, {perc_of_games} of games']})
    target_line = alt.Chart(df).mark_rule(color='purple').encode(y='y:Q').properties(title='Target:')
    target_label = target_line.mark_text(align='right', baseline='middle', dx=-140, dy=-10).encode(
        text='label:N', size=alt.value(16)
    )
    return target_line, target_label

def highlight_team(df_row, team_selected):
    """
    Return a list of style strings for pandas styler (used before .style.apply)
    Keep simple: highlight row if NFL_Team equals team_selected
    """
    try:
        color = 'background-color: yellow' if df_row.get('NFL_Team', '') == team_selected else ''
        return [color] * len(df_row)
    except Exception:
        return [''] * len(df_row)
