from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for

import nba_api
from nba_api.stats.endpoints import playercareerstats
from nba_api.stats.endpoints import commonplayerinfo
from nba_api.stats.static import players as playersapi

import praw

import collections
import datetime
import dateutil.parser
import pytz
import requests
import time

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser

from bs4 import BeautifulSoup
from decimal import Decimal
from collections import Counter

import io
import random
from flask import Response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib as plt
from matplotlib import pyplot as plt
import copy
from base64 import b64encode
import json
import time
app = Flask(__name__)
#proxy='178.128.234.37:3128'


"""
# A function that forces recaching every 10 minutes.
@app.after_request
def add_header(response):
    # Add headers to both force latest IE rendering engine or Chrome Frame,
    # and also to cache the rendered page for 10 minutes.
    
    
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response
"""

@app.route('/')
def index():
    """Main page of the website that by default renders the score page.
    """
    all_active_players = get_active_players()
    return render_template("index.html", all_active_players=all_active_players)
def test_link(link):
    """Test if link is valid.
    """
    r = requests.get(link)
    if (r.status_code != 200):
        return False
    else:
        return True


@app.route('/players/<playerid>')
def players(playerid):
    all_active_players = get_active_players()
    """Specific player pages.
    """
    player1 = get_player_information(playerid)
    plots = ['PTS', 'AST', 'REB', 'BLK', 'GP', 'FG_PCT', 'FG3_PCT', 'FT_PCT']
    plot_titles = {
		"PTS" : '1. Points per game comparison:',
		"AST" : '2. Assists per game comparison:',
		"REB" : '3. Rebounds per game comparison: ',
		"BLK" : '4. Blocks per game comparison:',
		"GP" : '5. Gampes played comparison:',
		"FG_PCT" : '6. Field Goal percentage comparison: ',
        "FG3_PCT" : '7. 3 Point field goal comparison: ',
		"FT_PCT" : '8. Free throw per game comparison: '
	}
    all_plots = get_all_plots(playerid, None, plot_titles, player1['player_summary_info'].iloc[0]["DISPLAY_FIRST_LAST"], None, player1['player_career_regular_season_averages'], None)
    return render_template("players.html",
                           title=player1['player_summary_info'].iloc[0]["DISPLAY_FIRST_LAST"],
                           playerid=playerid,
                           player_games=False,
                           playoffs_player_games=False,
                           player_summary_info=player1['player_summary_info'].iloc[0],
                           headline_stats=player1['headline_stats'].iloc[0],
                           age=player1['age'],
                           pretty_birth_date=player1['pretty_birth_date'],
                           season=player1['season'],
                           player_career_regular_season_totals=player1['player_career_regular_season'],
                           player_career_post_season_totals=player1['player_career_post_season'],
                           player_headshot=player1['player_headshot'],
                           plots=plots,
                           plot_titles=plot_titles,
                           all_plots=all_plots,
                           all_active_players=all_active_players)  

@app.route('/playervsplayer/<playerid>/<playerid2>')
def player_vs_player(playerid, playerid2):
    player1 = get_player_information(playerid)
    time.sleep(5)
    player2 = get_player_information(playerid2) 
    placeholder = copy.deepcopy(player1['player_career_regular_season_totals'])
    for key in placeholder:
        for state, value in key.items():
            if value > player2['player_career_regular_season_totals'][0][state]:
                player1['player_career_regular_season_totals'][0][state + 'C'] = '#00FF00'
                player2['player_career_regular_season_totals'][0][state + 'C'] = '#FFFFFF'
            else:
                player1['player_career_regular_season_totals'][0][state + 'C'] = '#FFFFFF'
                player2['player_career_regular_season_totals'][0][state + 'C'] = '#00FF00'
    
    placeholder = copy.deepcopy(player1['player_career_post_season_totals'])
    for key in placeholder:
        for state, value in key.items():
            if value > player2['player_career_post_season_totals'][0][state]:
                player1['player_career_post_season_totals'][0][state + 'C'] = '#00FF00'
                player2['player_career_post_season_totals'][0][state + 'C'] = '#FFFFFF'
            else:
                player1['player_career_post_season_totals'][0][state + 'C'] = '#FFFFFF'
                player2['player_career_post_season_totals'][0][state + 'C'] = '#00FF00'            
                

    plots = ['PTS', 'AST', 'REB', 'BLK', 'GP', 'FG_PCT', 'FG3_PCT', 'FT_PCT']
    plot_titles = {
		"PTS" : '1. Points per game comparison:',
		"AST" : '2. Assists per game comparison:',
		"REB" : '3. Rebounds per game comparison: ',
		"BLK" : '4. Blocks per game comparison:',
		"GP" : '5. Gampes played comparison:',
		"FG_PCT" : '6. Field Goal percentage comparison: ',
        "FG3_PCT" : '7. 3 Point field goal comparison: ',
		"FT_PCT" : '8. Free throw per game comparison: '
	}
    
    all_plots = get_all_plots(playerid, playerid2, plot_titles, player1['player_summary_info'].iloc[0]["DISPLAY_FIRST_LAST"], player2['player_summary_info'].iloc[0]["DISPLAY_FIRST_LAST"], player1['player_career_regular_season_averages'], player2['player_career_regular_season_averages'])
    all_active_players = get_active_players()
    return render_template("playervsplayer.html",
                           title=player1['player_summary_info'].iloc[0]["DISPLAY_FIRST_LAST"],
                           playerid=playerid,
                           player_games=False,
                           playoffs_player_games=False,
                           player_summary_info=player1['player_summary_info'].iloc[0],
                           player_summary_info2=player2['player_summary_info'].iloc[0],
                           headline_stats=player1['headline_stats'].iloc[0],
                           headline_stats2=player2['headline_stats'].iloc[0],
                           age=player1['age'],
                           pretty_birth_date=player1['pretty_birth_date'],
                           age2=player2['age'],
                           pretty_birth_date2=player2['pretty_birth_date'],
                           season=player1['season'],
                           player_career_regular_season_totals=player1['player_career_regular_season_totals'],
                           player_career_post_season_totals=player1['player_career_post_season_totals'],
                           player_career_regular_season_totals2=player2['player_career_regular_season_totals'],
                           player_career_post_season_totals2=player2['player_career_post_season_totals'],
                           player_headshot=player1['player_headshot'],
                           player_headshot2=player2['player_headshot'],
                           plots=plots,
                           plot_titles=plot_titles,
                           all_plots=all_plots,
                           all_active_players=all_active_players)  

def get_player_information(playerid):
    playerinfo = {}
        
    # Retrieve player 1 information and stats
    ##player_summary = commonplayerinfo.CommonPlayerInfo(player_id=playerid, proxy=proxy, timeout=100)
    player_summary = commonplayerinfo.CommonPlayerInfo(player_id=playerid, timeout=500)
    player_summary_info = player_summary.get_data_frames()[0]
    headline_stats = player_summary.get_data_frames()[1]
    playerinfo['headline_stats'] = headline_stats
    playerinfo['player_summary_info'] = player_summary_info
    # Get last year that he played in
    to_year = int(player_summary_info.iloc[0]["TO_YEAR"])
    next_year = to_year + 1
    season = str(to_year) + "-" + str(next_year)[2:4]
    playerinfo['season'] = season

    time.sleep(5)
    # Get birth date for the player 1
    birth_datestring = player_summary_info.iloc[0]["BIRTHDATE"][:10]
    birth_date = datetime.datetime.strptime(birth_datestring, "%Y-%m-%d")
    playerinfo['pretty_birth_date'] = birth_date.strftime("%m-%d-%Y")
    playerinfo['age'] = calculate_age(birth_date)


    #career = playercareerstats.PlayerCareerStats(player_id=playerid, proxy=proxy, timeout=100)
    career = playercareerstats.PlayerCareerStats(player_id=playerid, timeout=100)
    player_career_regular_season_totals =career.get_data_frames()[1].to_dict('records') 
    player_career_post_season_totals = career.get_data_frames()[3].to_dict('records') 
    player_career_regular_season = career.get_data_frames()[0].to_dict('records') 
    player_career_post_season = career.get_data_frames()[2].to_dict('records')     
    playerinfo['player_career_regular_season_averages'] = get_average_stats(player_career_regular_season)
    playerinfo['player_career_post_season_averages'] = get_average_stats(player_career_post_season)
    playerinfo['player_career_regular_season'] = player_career_regular_season
    playerinfo['player_career_post_season'] = player_career_post_season
    playerinfo['player_career_regular_season_totals'] = get_shooting_percentage(player_career_regular_season_totals)
    playerinfo['player_career_post_season_totals'] = get_shooting_percentage(player_career_post_season_totals)         
        
    player_headshot = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/" + playerid + ".png"
    if (not test_link(player_headshot)):
        player_headshot = False
    
    playerinfo['player_headshot'] = player_headshot
    return playerinfo
    
 
def get_shooting_percentage(stats):
    for state in stats:     
        state['FG_PCT'] = round(Decimal(state['FG_PCT']) * Decimal(100.0),1) 
        state['FG3_PCT'] = round(Decimal(state['FG3_PCT']) * Decimal(100.0),1) 
        state['FT_PCT'] = round(Decimal(state['FT_PCT']) * Decimal(100.0),1) 
    return stats    

@app.route('/plot/<playerid>.png')
def plot_png(playerid):
    fig = create_figure(playerid)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

def get_all_plots(playerid, playerid2, plot_titles, playername, playername2, player_career_regular_season_averages, player_career_regular_season_averages2):
    all_plots = {}
    for key, value in plot_titles.items():
        fig = create_figure2(key, playerid, playerid2, player_career_regular_season_averages, player_career_regular_season_averages2, playername, playername2)
        all_plots[value] = fig
        
    return all_plots

def create_figure(graph_type,playerid, playerid2):
    axis = fig.add_subplot(1, 1, 1)
    career = playercareerstats.PlayerCareerStats(player_id=playerid)
    player_career_regular_season_totals =career.get_data_frames()[0].to_dict('records') 
    player_career_post_season_totals = career.get_data_frames()[2].to_dict('records')     
    
    player_career_regular_season_totals = get_average_stats(player_career_regular_season_totals)
    #player_career_post_season_totals  = get_average_stats(player_career_post_season_totals)
    
    i = 0
    xs = []
    ys = []
    for state in player_career_regular_season_totals:      
        xs.append(i)
        ys.append(state[graph_type])
        i = i + 1
    axis.title.set_text(graph_type)
    axis.set_xlabel('nth seasons in the nba')
    axis.set_ylabel(graph_type)

    axis.plot(xs, ys, 'r', label=playerid)
    if playerid2: 
        career = playercareerstats.PlayerCareerStats(player_id=playerid2)
        player_career_regular_season_totals =career.get_data_frames()[0].to_dict('records') 
        player_career_post_season_totals = career.get_data_frames()[2].to_dict('records')     
        
        player_career_regular_season_totals = get_average_stats(player_career_regular_season_totals)
        player_career_post_season_totals  = get_average_stats(player_career_post_season_totals)
        i = 1
        xs2 = []
        ys2 = []
        for state in player_career_regular_season_totals:      
            xs2.append(i)
            ys2.append(state[graph_type])
            i = i + 1
        axis.plot(xs2, ys2, 'b', label=playerid2)

    axis.legend()
    axis.savefig(output, format='png')
    output.seek(0)
    plot_data = base64.b64encode(output.getvalue()).decode()
    return plot_data

def create_figure2(graph_type, playerid, playerid2,player_career_regular_season_totals, player_career_regular_season_totals2, playername, playername2):
    output = io.BytesIO()
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    
    i = 1
    xs = []
    ys = []
    for state in player_career_regular_season_totals:      
        xs.append(i)
        ys.append(state[graph_type])
        i = i + 1

    axis.title.set_text(graph_type + ' in each nba season')
    axis.set_xlabel('number of seasons in the nba')
    axis.set_ylabel(graph_type)

    axis.plot(xs, ys, 'ro-', label=playername)

    if playerid2:       
        i = 1
        xs2 = []
        ys2 = []
        for state in player_career_regular_season_totals2:      
            xs2.append(i)
            ys2.append(state[graph_type])
            i = i + 1
        axis.plot(xs2, ys2, 'bo-', label=playername2)

    axis.legend()
    FigureCanvas(fig).print_png(output)
    plot_data = b64encode(output.getvalue()).decode('ascii')
    output.seek(0)
    return plot_data


def get_average_stats(player_totals):
    for state in player_totals:
        state['PTS'] = round(Decimal(state['PTS'] / state['GP']), 1)
        state['REB'] = round(Decimal(state['REB'] / state['GP']), 1)
        state['AST'] = round(Decimal(state['AST'] / state['GP']), 1)
        state['STL'] = round(Decimal(state['STL'] / state['GP']), 1)
        state['BLK'] = round(Decimal(state['BLK'] / state['GP']), 1)
        state['TOV'] = round(Decimal(state['TOV'] / state['GP']), 1)
        state['OREB'] = round(Decimal(state['OREB'] / state['GP']), 1)
        state['MIN'] = round(Decimal(state['MIN'] / state['GP']), 1)
        state['PF'] = round(Decimal(state['PF'] / state['GP']), 1)
        state['DREB'] = round(Decimal(state['DREB'] / state['GP']), 1)
    return player_totals

def calculate_age(born):
    """Calculates the person's age by subtracting DOB by today's date.
    """
    today = datetime.date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def get_active_players():
    allplayers = playersapi.get_active_players()
    players_list = []
    for player in allplayers:
        players_list.append(player['full_name'])
        
    #players_list = json.dumps(players_list)
    return players_list

@app.route('/search', methods=["POST"])
def search():
    """Search post request when searching for a specific player or team.
    """
    name = request.form["searchname"]
    split_name = name.split(" ", 1)
    fullname = name.lower()
    if name.upper() == "YAO MING":
        return redirect(url_for("players", playerid="2397"))
    
    player = playersapi.find_players_by_full_name(fullname)
    try:
        getplayerid = player[0]['id']
        get_player = True
    except:
        get_player = False

    if get_player:
        return redirect(url_for("players", playerid=getplayerid))
    else:
        return render_template("search.html")

@app.route('/search2', methods=["POST"])
def search2():
    """Search post request when searching for a specific player or team.
    """
    name = request.form["searchname"]
    name2 = request.form["searchname2"]
    get_player1 = False
    get_player2 = False
    
    fullname = name.lower()
    
    player = playersapi.find_players_by_full_name(fullname)
    try:
        getplayerid = player[0]['id']
        get_player1 = True
    except:
        get_player1 = False

    fullname = name2.lower()
    
    player = playersapi.find_players_by_full_name(fullname)
    try:
        getplayerid2 = player[0]['id']
        get_player2 = True
    except:
        get_player2 = False
        
    if get_player1 == True and get_player2 == True:
        return redirect(url_for("player_vs_player", playerid=getplayerid, playerid2=getplayerid2))
    else:
        return render_template("search.html")
      
if __name__ == "__main__":
    # Run officially on a web server.
    app.run(host='127.0.0.1', port=8080)
    # Run on localhost with port 8080.
    #app.run(host='0.0.0.0', port=4000, threaded=True, debug = True)
