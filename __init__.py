from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for

from bballfast_constants import TEAM_NAME_TO_ID
from bballfast_constants import TEAM_ID_TO_NAME
from bballfast_constants import TEAM_ID_DATA
from bballfast_constants import CITY_TO_TEAM

import nba_py
from nba_py.constants import CURRENT_SEASON
from nba_py.constants import TEAMS
from nba_py import constants
from nba_py import game
from nba_py import player
from nba_py import team
from nba_py import league
from nba_py import draftcombine

import nba_py
from nba_py.constants import CURRENT_SEASON
from nba_py.constants import TEAMS
from nba_py import constants
from nba_py import game
from nba_py import player
from nba_py import team
from nba_py import league
from nba_py import draftcombine

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

# YouTube Developer Key
DEVELOPER_KEY = "AIzaSyB1tXw8w9yhd0bK8aiviV2zJNHxQ3kfNY4"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

app = Flask(__name__)

# Time zone that determines when the next day occurs.
hawaii = pytz.timezone("US/Hawaii")

# Reddit API Key
reddit = praw.Reddit(client_id="zH8v4tTPPI-Qlw",
                     client_secret="lM10JJkg9tkfYxSWvQ8fzqoP3fQ",
                     user_agent="bballfast by /u/microwavesam")

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
    print("index")
    datetime_today = datetime.datetime.now(hawaii)
    datestring_today = datetime_today.strftime("%m-%d-%Y")
    print(datetime_today)
    print(datestring_today)
    all_active_players = get_active_players()
    print(all_active_players)
    return render_template("index.html", all_active_players=all_active_players)

@app.route('/standings')
def standings():
    """Default standings page.
    """
    print('standings time')    
    scoreboard = nba_py.Scoreboard()
    east_standings = scoreboard.east_conf_standings_by_day()
    west_standings = scoreboard.west_conf_standings_by_day()
    print(east_standings)
    print(east_standings)    

    return render_template("standings.html",
                           title="standings",
                           east_standings=enumerate(east_standings, 1),
                           west_standings=enumerate(west_standings, 1),
                           team=CITY_TO_TEAM)

@app.route('/standings/season/<season>')
def standings_by_season(season):
    """Standings page by the season year.
    """
    season = int(season) + 1
    scoreboard = nba_py.Scoreboard(month=7,
                                   day=1,
                                   year=season)
    east_standings = scoreboard.east_conf_standings_by_day()
    west_standings = scoreboard.west_conf_standings_by_day()

    return render_template("standings.html",
                           title="standings",
                           east_standings=enumerate(east_standings, 1),
                           west_standings=enumerate(west_standings, 1),
                           team=CITY_TO_TEAM)

@app.route('/standings', methods=["POST"])
def standings_post_request():
    """Standings page after using the datepicker plugin.
    """
    date = request.form["date"]
    datetime_object = datetime.datetime.strptime(date, "%m-%d-%Y")

    scoreboard = nba_py.Scoreboard(month=datetime_object.month,
                                   day=datetime_object.day,
                                   year=datetime_object.year)
    east_standings = scoreboard.east_conf_standings_by_day()
    west_standings = scoreboard.west_conf_standings_by_day()

    return render_template("standings.html",
                           title="standings",
                           east_standings=enumerate(east_standings, 1),
                           west_standings=enumerate(west_standings, 1),
                           team=CITY_TO_TEAM)
    

@app.route('/scores/<datestring>')
def scores(datestring):
    """Link for specific score pages for a certain day.
    """
    return render_score_page("scores.html", datestring, datestring)

@app.route('/scores', methods=["POST"])
def scores_post_request():
    """The score page after using the datepicker plugin.
    """
    date = request.form["date"]
    print(date)
    return render_score_page("scores.html", date, date)

def render_score_page(page, datestring, title):
    """
    Args:
        page: Name of the template html page.
        datestring: The date of the boxscores that we want.
    """
    datetime_today = dateutil.parser.parse(datestring)
    pretty_today = datetime_today.strftime("%b %d, %Y")
    datetime_yesterday = datetime_today - datetime.timedelta(1)
    datetime_tomorrow = datetime_today + datetime.timedelta(1)
    datestring_yesterday = datetime_yesterday.strftime("%m-%d-%Y")
    pretty_yesterday = datetime_yesterday.strftime("%b %d, %Y")
    datestring_tomorrow = datetime_tomorrow.strftime("%m-%d-%Y")
    pretty_tomorrow = datetime_tomorrow.strftime("%b %d, %Y")

    return_tuple = get_games(datetime_today)
    games = return_tuple[0]
    east_standings = return_tuple[1]
    west_standings = return_tuple[2]

    winners = []
    for i in games:
        if (i["HOME_TEAM_PTS"] > i["AWAY_TEAM_PTS"]):
            winners.append(i["HOME_TEAM"])
        elif (i["HOME_TEAM_PTS"] < i["AWAY_TEAM_PTS"]):
            winners.append(i["AWAY_TEAM"])
        else:
            winners.append(None)

    if (page == "index.html"):
        # An extra second of computation that is unnecessary for now. Commenting.
        # latest_power_ranking = get_reddit_power_ranking()
        latest_power_ranking = (False, False)
        hot_nba_posts = get_hot_nba_post()
        bball_breakdown_posts = get_bball_breakdown_articles()
        fansided_posts = get_fansided_articles()
        # hot_nba_post = (False, False)
        #youtube_url = youtube_search("freedawkins", 2, True)

        pts_leaders_tiles = league.LeadersTiles()
        # Other stats that are commented because the extra computation time is not worth it.
        # rebs_leaders_tiles = league.LeadersTiles(stat_category="REB")
        # asts_leaders_tiles = league.LeadersTiles(stat_category="AST")

        # season_high_pts = pts_leaders_tiles.current_season_high()
        # season_high_rebs = rebs_leaders_tiles.current_season_high()
        # season_high_asts = asts_leaders_tiles.current_season_high()
        season_high_pts = False
        season_high_rebs = False
        season_high_asts = False
    else:
        latest_power_ranking = (False, False)
        hot_nba_posts = None
        bball_breakdown_posts = None
        fansided_posts = None
        youtube_url = False
        season_high_pts = False
        season_high_rebs = False
        season_high_asts = False

    return render_template(page, 
                           title=title,
                           date=datestring,
                           yesterday=datestring_yesterday,
                           tomorrow=datestring_tomorrow,
                           pretty_today=pretty_today,
                           pretty_yesterday=pretty_yesterday,
                           pretty_tomorrow=pretty_tomorrow,
                           games=enumerate(games),
                           winners=winners,
                           power_ranking_url=latest_power_ranking[0],
                           power_ranking_title=latest_power_ranking[1],
                           east_standings=enumerate(east_standings, 1),
                           west_standings=west_standings,
                           team=CITY_TO_TEAM,
                           hot_nba_posts=hot_nba_posts,
                           bball_breakdown_posts=bball_breakdown_posts,
                           fansided_posts=fansided_posts,
                           youtube_url=youtube_url,
                           season_high_pts=season_high_pts,
                           season_high_rebs=season_high_rebs,
                           season_high_asts=season_high_asts)

def get_reddit_power_ranking():
    """Gets latest /r/NBA Power Ranking from reddit.
    """
    subreddit = reddit.subreddit("nba")
    for submission in subreddit.search("Official /r/NBA Power Rankings", sort="new", limit=1):
        if (submission):
            return (submission.url, submission.title)
        else:
            return ("http://www.redditstatus.com/", "Reddit Status?")

def get_hot_nba_post():
    """Gets hottest /r/NBA post from reddit.
    """
    subreddit = reddit.subreddit("nba")
    submissions = []
    for submission in subreddit.top("day", limit=11):
        submissions.append(submission)
        
    return submissions
    """
        if (submission):
            return (submission.permalink, submission.title)
        else:
            return ("http://www.redditstatus.com/", "Reddit Status?")
    """

def get_games(date):
    """Get list of games in daily scoreboard.
    """
    scoreboard = nba_py.Scoreboard(month=date.month,
                                   day=date.day,
                                   year=date.year)
    line_score = scoreboard.line_score()
    game_header = scoreboard.game_header()

    games = []
    current_game = {}
    game_sequence = 0
    game_sequence_counter = 0

    # Get HOME TEAM and AWAY TEAM data for each boxscore game in line_score.
    for i, value in enumerate(line_score):
        if (value["GAME_SEQUENCE"] != game_sequence):
            game_sequence += 1

            current_game["GAME_ID"] = value["GAME_ID"]
            home_team_id = game_header[game_sequence - 1]["HOME_TEAM_ID"]

            if (home_team_id == value["TEAM_ID"]):
              current_game["HOME_TEAM"] = value["TEAM_ABBREVIATION"]
              current_game["HOME_TEAM_WINS_LOSSES"] = value["TEAM_WINS_LOSSES"]
              current_game["HOME_TEAM_PTS"] = value["PTS"]
              current_game["HOME_TEAM_ID"] = value["TEAM_ID"]
              if (current_game["HOME_TEAM"] in TEAM_ID_DATA):
                current_game["HOME_TEAM_IMG"] = TEAM_ID_DATA[current_game["HOME_TEAM"]]["img"]
            else:
              current_game["AWAY_TEAM"] = value["TEAM_ABBREVIATION"]
              current_game["AWAY_TEAM_WINS_LOSSES"] = value["TEAM_WINS_LOSSES"]
              current_game["AWAY_TEAM_PTS"] = value["PTS"]
              current_game["AWAY_TEAM_ID"] = value["TEAM_ID"]
              if (current_game["AWAY_TEAM"] in TEAM_ID_DATA):
                current_game["AWAY_TEAM_IMG"] = TEAM_ID_DATA[current_game["AWAY_TEAM"]]["img"]

            if (value["TEAM_ABBREVIATION"] in TEAMS):
                if (home_team_id == value["TEAM_ID"]):
                    current_game["HOME_TEAM_FULL_NAME"] = TEAMS[value["TEAM_ABBREVIATION"]]["city"] + \
                                                          " " + TEAMS[value["TEAM_ABBREVIATION"]]["name"]
                else:
                    current_game["AWAY_TEAM_FULL_NAME"] = TEAMS[value["TEAM_ABBREVIATION"]]["city"] + \
                                                          " " + TEAMS[value["TEAM_ABBREVIATION"]]["name"]
            
            game_sequence = value["GAME_SEQUENCE"]
            game_sequence_counter += 1
        elif game_sequence_counter == 1:
            if ("AWAY_TEAM" in current_game):
              current_game["HOME_TEAM"] = value["TEAM_ABBREVIATION"]
              current_game["HOME_TEAM_WINS_LOSSES"] = value["TEAM_WINS_LOSSES"]
              current_game["HOME_TEAM_PTS"] = value["PTS"]
              current_game["HOME_TEAM_ID"] = value["TEAM_ID"]
              if (current_game["HOME_TEAM"] in TEAM_ID_DATA):
                current_game["HOME_TEAM_IMG"] = TEAM_ID_DATA[current_game["HOME_TEAM"]]["img"]
            else:
              current_game["AWAY_TEAM"] = value["TEAM_ABBREVIATION"]
              current_game["AWAY_TEAM_WINS_LOSSES"] = value["TEAM_WINS_LOSSES"]
              current_game["AWAY_TEAM_PTS"] = value["PTS"]
              current_game["AWAY_TEAM_ID"] = value["TEAM_ID"]
              if (current_game["AWAY_TEAM"] in TEAM_ID_DATA):
                current_game["AWAY_TEAM_IMG"] = TEAM_ID_DATA[current_game["AWAY_TEAM"]]["img"]

            if (value["TEAM_ABBREVIATION"] in TEAMS):
                if ("AWAY_TEAM" in current_game):
                  current_game["HOME_TEAM_FULL_NAME"] = TEAMS[value["TEAM_ABBREVIATION"]]["city"] + \
                                                        " " + TEAMS[value["TEAM_ABBREVIATION"]]["name"]
                else:
                  current_game["AWAY_TEAM_FULL_NAME"] = TEAMS[value["TEAM_ABBREVIATION"]]["city"] + \
                                                        " " + TEAMS[value["TEAM_ABBREVIATION"]]["name"]

            current_game["GAME_STATUS_TEXT"] = game_header[game_sequence - 1]["GAME_STATUS_TEXT"]
            if not game_header[game_sequence - 1]["NATL_TV_BROADCASTER_ABBREVIATION"]:
                current_game["BROADCASTER"] = ""
            else:
                current_game["BROADCASTER"] = game_header[game_sequence - 1]["NATL_TV_BROADCASTER_ABBREVIATION"]

            games.append(current_game)

            current_game = {}

            game_sequence = value["GAME_SEQUENCE"]
            game_sequence_counter -= 1

    east_standings = scoreboard.east_conf_standings_by_day()
    west_standings = scoreboard.west_conf_standings_by_day()

    return (games, east_standings, west_standings)

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
    """Specific player pages.
    """
    player_summary = commonplayerinfo.CommonPlayerInfo(player_id=playerid)
    player_summary_info = player_summary.get_data_frames()[0]
    headline_stats = player_summary.get_data_frames()[1]

    to_year = int(player_summary_info.iloc[0]["TO_YEAR"])
    next_year = to_year + 1

    season = str(to_year) + "-" + str(next_year)[2:4]

    birth_datestring = player_summary_info.iloc[0]["BIRTHDATE"][:10]
    birth_date = datetime.datetime.strptime(birth_datestring, "%Y-%m-%d")
    pretty_birth_date = birth_date.strftime("%m-%d-%Y")
    age = calculate_age(birth_date)

    #player_game_logs = player.PlayerGameLogs(playerid, season=season)
    #player_games = player_game_logs.info()

    #playoffs_playergamelogs = player.PlayerGameLogs(playerid, season=season, season_type="Playoffs")
    #layoffs_player_games = playoffs_playergamelogs.info()

    career = playercareerstats.PlayerCareerStats(player_id=playerid)
    player_career_regular_season_totals =career.get_data_frames()[0].to_dict('records') 
    player_career_post_season_totals = career.get_data_frames()[2].to_dict('records') 
    print(career.get_data_frames())
    
    for state in player_career_regular_season_totals:      
        state['FG_PCT'] = round(Decimal(state['FG_PCT']) * Decimal(100.0),1) 
        state['FG3_PCT'] = round(Decimal(state['FG3_PCT']) * Decimal(100.0),1) 
        state['FT_PCT'] = round(Decimal(state['FT_PCT']) * Decimal(100.0),1) 
        
    for state in player_career_post_season_totals:
        state['FG_PCT'] = round(Decimal(state['FG_PCT']) * Decimal(100.0),1) 
        state['FG3_PCT'] = round(Decimal(state['FG3_PCT']) * Decimal(100.0),1) 
        state['FT_PCT'] = round(Decimal(state['FT_PCT']) * Decimal(100.0),1) 
    i = 0
    xs = []
    ys = []
    for state in player_career_regular_season_totals:      
        xs.append(i)
        ys.append(state['FG_PCT'])
        i = i + 1
    plt.plot(xs, ys)
    player_headshot = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/" + playerid + ".png"
    if (not test_link(player_headshot)):
        player_headshot = False

    return render_template("players.html",
                           title=player_summary_info.iloc[0]["DISPLAY_FIRST_LAST"],
                           playerid=playerid,
                           player_games=False,
                           playoffs_player_games=False,
                           player_summary_info=player_summary_info.iloc[0],
                           headline_stats=headline_stats.iloc[0],
                           age=age,
                           pretty_birth_date=pretty_birth_date,
                           season=season,
                           player_career_regular_season_totals=player_career_regular_season_totals,
                           player_career_post_season_totals=player_career_post_season_totals,
                           team_img=TEAM_ID_DATA,
                           player_headshot=player_headshot)

@app.route('/playervsplayer/<playerid>/<playerid2>')
def player_vs_player(playerid, playerid2):
    player_summary = commonplayerinfo.CommonPlayerInfo(player_id=playerid)
    player_summary_info = player_summary.get_data_frames()[0]
    player_summary2 = commonplayerinfo.CommonPlayerInfo(player_id=playerid2)
    player_summary_info2 = player_summary2.get_data_frames()[0]
    headline_stats = player_summary.get_data_frames()[1]
    headline_stats2 = player_summary2.get_data_frames()[1]

    to_year = int(player_summary_info.iloc[0]["TO_YEAR"])
    next_year = to_year + 1

    season = str(to_year) + "-" + str(next_year)[2:4]

    birth_datestring = player_summary_info.iloc[0]["BIRTHDATE"][:10]
    birth_date = datetime.datetime.strptime(birth_datestring, "%Y-%m-%d")
    pretty_birth_date = birth_date.strftime("%m-%d-%Y")
    age = calculate_age(birth_date)

    birth_datestring2 = player_summary_info2.iloc[0]["BIRTHDATE"][:10]
    birth_date2 = datetime.datetime.strptime(birth_datestring2, "%Y-%m-%d")
    pretty_birth_date2 = birth_date2.strftime("%m-%d-%Y")
    age2 = calculate_age(birth_date2)

    #player_game_logs = player.PlayerGameLogs(playerid, season=season)
    #player_games = player_game_logs.info()

    #playoffs_playergamelogs = player.PlayerGameLogs(playerid, season=season, season_type="Playoffs")
    #layoffs_player_games = playoffs_playergamelogs.info()

    career = playercareerstats.PlayerCareerStats(player_id=playerid)
    player_career_regular_season_totals =career.get_data_frames()[1].to_dict('records') 
    player_career_post_season_totals = career.get_data_frames()[3].to_dict('records') 
    career2 = playercareerstats.PlayerCareerStats(player_id=playerid2)
    player_career_regular_season_totals2 =career2.get_data_frames()[1].to_dict('records') 
    player_career_post_season_totals2 = career2.get_data_frames()[3].to_dict('records') 
    
    for state in player_career_regular_season_totals:      
        state['FG_PCT'] = round(Decimal(state['FG_PCT']) * Decimal(100.0),1) 
        state['FG3_PCT'] = round(Decimal(state['FG3_PCT']) * Decimal(100.0),1) 
        state['FT_PCT'] = round(Decimal(state['FT_PCT']) * Decimal(100.0),1) 
        
    for state in player_career_post_season_totals:
        state['FG_PCT'] = round(Decimal(state['FG_PCT']) * Decimal(100.0),1) 
        state['FG3_PCT'] = round(Decimal(state['FG3_PCT']) * Decimal(100.0),1) 
        state['FT_PCT'] = round(Decimal(state['FT_PCT']) * Decimal(100.0),1) 
        
        
    for state in player_career_regular_season_totals2:      
        state['FG_PCT'] = round(Decimal(state['FG_PCT']) * Decimal(100.0),1) 
        state['FG3_PCT'] = round(Decimal(state['FG3_PCT']) * Decimal(100.0),1) 
        state['FT_PCT'] = round(Decimal(state['FT_PCT']) * Decimal(100.0),1) 
        
    for state in player_career_post_season_totals2:
        state['FG_PCT'] = round(Decimal(state['FG_PCT']) * Decimal(100.0),1) 
        state['FG3_PCT'] = round(Decimal(state['FG3_PCT']) * Decimal(100.0),1) 
        state['FT_PCT'] = round(Decimal(state['FT_PCT']) * Decimal(100.0),1) 
        
        
    for state in player_career_post_season_totals:
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
        
    for state in player_career_regular_season_totals:
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

        
    for state in player_career_post_season_totals2:
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

        
    for state in player_career_regular_season_totals2:
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


    
    placeholder = copy.deepcopy(player_career_regular_season_totals)
    for key in placeholder:
        for state, value in key.items():
            print(state)
            if value > player_career_regular_season_totals2[0][state]:
                player_career_regular_season_totals[0][state + 'C'] = '#00FF00'
                player_career_regular_season_totals2[0][state + 'C'] = '#FFFFFF'
            else:
                player_career_regular_season_totals[0][state + 'C'] = '#FFFFFF'
                player_career_regular_season_totals2[0][state + 'C'] = '#00FF00'
        
    placeholder = copy.deepcopy(player_career_post_season_totals)
    for key in placeholder:
        for state, value in key.items():
            print(state)
            if value > player_career_post_season_totals2[0][state]:
                player_career_post_season_totals[0][state + 'C'] = '#00FF00'
                player_career_post_season_totals2[0][state + 'C'] = '#FFFFFF'
            else:
                player_career_post_season_totals[0][state + 'C'] = '#FFFFFF'
                player_career_post_season_totals2[0][state + 'C'] = '#00FF00'           
         


    plots = ['PTS', 'AST', 'REB', 'BLK', 'GP', 'FG_PCT', 'FG3_PCT', 'FT_PCT']
    plot_titles = {
		"PTS" : 'Point per game comparison',
		"AST" : 'Point per game comparison',
		"REB" : 'Point per game comparison',
		"BLK" : 'Point per game comparison',
		"GP" : 'Point per game comparison',
		"FG_PCT" : 'Point per game comparison',
        "FG3_PCT" : 'Point per game comparison',
		"FT_PCT" : 'Point per game comparison'
	}
    i = 0
    xs = []
    ys = []
    for state in player_career_regular_season_totals:      
        xs.append(i)
        ys.append(state['FG_PCT'])
        i = i + 1
    plt.plot(xs, ys)
    player_headshot = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/" + playerid + ".png"
    player_headshot2 = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/" + playerid2 + ".png"
    if (not test_link(player_headshot)):
        player_headshot = False

    all_plots = get_all_plots(playerid, playerid2, plots, player_summary_info.iloc[0]["DISPLAY_FIRST_LAST"], player_summary_info2.iloc[0]["DISPLAY_FIRST_LAST"])
    return render_template("playervsplayer.html",
                           title=player_summary_info.iloc[0]["DISPLAY_FIRST_LAST"],
                           playerid=playerid,
                           player_games=False,
                           playoffs_player_games=False,
                           player_summary_info=player_summary_info.iloc[0],
                           player_summary_info2=player_summary_info2.iloc[0],
                           headline_stats=headline_stats.iloc[0],
                           headline_stats2=headline_stats2.iloc[0],
                           age=age,
                           pretty_birth_date=pretty_birth_date,
                           age2=age2,
                           pretty_birth_date2=pretty_birth_date2,
                           season=season,
                           player_career_regular_season_totals=player_career_regular_season_totals,
                           player_career_post_season_totals=player_career_post_season_totals,
                           player_career_regular_season_totals2=player_career_regular_season_totals2,
                           player_career_post_season_totals2=player_career_post_season_totals2,
                           team_img=TEAM_ID_DATA,
                           player_headshot=player_headshot,
                           player_headshot2=player_headshot2,
                           plots=plots,
                           plot_titles=plot_titles,
                           all_plots=all_plots)  
                           
@app.route('/plot/<playerid>.png')
def plot_png(playerid):
    fig = create_figure(playerid)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')
 
@app.route('/plot/<graph_type>/<playerid>/<playerid2>.png')
def plot_png2(graph_type,playerid, playerid2):
    fig = create_figure(graph_type,playerid, playerid2)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    FigureCanvas(fig).print_png(output)
    print(output.getvalue())
    return Response(output.getvalue(), mimetype='image/png')

def get_all_plots(playerid, playerid2, plots, playername, playername2):
    all_plots = []
    
    career = playercareerstats.PlayerCareerStats(player_id=playerid)
    player_career_regular_season_totals =career.get_data_frames()[0].to_dict('records') 
    player_career_post_season_totals = career.get_data_frames()[2].to_dict('records')     
    player_career_regular_season_totals = get_average_stats(player_career_regular_season_totals)
    
    career = playercareerstats.PlayerCareerStats(player_id=playerid2)
    player_career_regular_season_totals2 =career.get_data_frames()[0].to_dict('records')     
    player_career_regular_season_totals2 = get_average_stats(player_career_regular_season_totals2)

    for plot in plots:
        fig = create_figure2(plot, playerid, playerid2, player_career_regular_season_totals, player_career_regular_season_totals2, playername, playername2)
        all_plots.append(fig)
        
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
        
    career = playercareerstats.PlayerCareerStats(player_id=playerid2)
    player_career_regular_season_totals =career.get_data_frames()[0].to_dict('records') 
    player_career_post_season_totals = career.get_data_frames()[2].to_dict('records')     
    
    player_career_regular_season_totals = get_average_stats(player_career_regular_season_totals)
    player_career_post_season_totals  = get_average_stats(player_career_post_season_totals)
    i = 0
    xs2 = []
    ys2 = []
    for state in player_career_regular_season_totals:      
        xs2.append(i)
        ys2.append(state[graph_type])
        i = i + 1
        
    axis.title.set_text(graph_type)
    axis.set_xlabel('number of seasons in the nba')
    axis.set_ylabel('FG%')

    axis.plot(xs, ys, 'r', label=playerid)
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
    print(player_career_regular_season_totals)
    
    i = 0
    xs = []
    ys = []
    for state in player_career_regular_season_totals:      
        xs.append(i)
        ys.append(state[graph_type])
        i = i + 1
        
    i = 0
    xs2 = []
    ys2 = []
    for state in player_career_regular_season_totals2:      
        xs2.append(i)
        ys2.append(state[graph_type])
        i = i + 1
        
    axis.title.set_text(graph_type)
    axis.set_xlabel('number of seasons in the nba')
    axis.set_ylabel('FG%')

    axis.plot(xs, ys, 'ro-', label=playername)
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

@app.route('/players/<playerid>/season/<season>/')
def players_and_season(playerid, season):
    # season example: "2016-17"
    # type example: "Regular Season" or "Playoffs" 
    player_game_logs = player.PlayerGameLogs(playerid,
                                             season=season)
    player_games = player_game_logs.info()

    playoffs_playergamelogs = player.PlayerGameLogs(playerid,
                                                    season=season,
                                                    season_type="Playoffs")
    playoffs_player_games = playoffs_playergamelogs.info()

    player_summary = player.PlayerSummary(playerid)
    player_summary_info = player_summary.info()
    headline_stats = player_summary.headline_stats()

    birth_datestring = player_summary_info[0]["BIRTHDATE"][:10]
    birth_date = datetime.datetime.strptime(birth_datestring, "%Y-%m-%d")
    pretty_birth_date = birth_date.strftime("%m-%d-%Y")
    age = calculate_age(birth_date)

    player_headshot = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/" + playerid + ".png"
    if (not test_link(player_headshot)):
        player_headshot = False

    return render_template("players.html",
                           title=player_summary_info[0]["DISPLAY_FIRST_LAST"],
                           player_games=player_games,
                           playoffs_player_games=playoffs_player_games,
                           player_summary_info=player_summary_info[0],
                           headline_stats=headline_stats[0],
                           age=age,
                           pretty_birth_date=pretty_birth_date,
                           season=season,
                           team_img=TEAM_ID_DATA,
                           player_headshot=player_headshot)

@app.route('/teams/<teamid>')
def teams(teamid):
    """Specific team pages.
    """
    team_summary = team.TeamSummary(teamid)
    team_summary_info = team_summary.info()
    team_season_ranks = team_summary.season_ranks()

    team_common_roster = team.TeamCommonRoster(teamid)
    roster = team_common_roster.roster()
    coaches = team_common_roster.coaches()

    season = team_summary_info[0]["SEASON_YEAR"]

    team_game_log = team.TeamGameLogs(teamid,
                                      season=season)
    team_games = team_game_log.info()

    playoffs_teamgamelogs = team.TeamGameLogs(teamid,
                                              season=season,
                                              season_type="Playoffs")
    playoffs_team_games = playoffs_teamgamelogs.info()

    team_season = team.TeamSeasons(teamid)
    team_season_info = team_season.info()

    for i in team_season_info:
        if (i["YEAR"] == season):
            current_season_info = i

    return render_template("teams.html",
                           title=team_summary_info[0]["TEAM_CITY"] + " " + team_summary_info[0]["TEAM_NAME"],
                           teamid=teamid,
                           team_summary_info=team_summary_info,
                           team_season_ranks=team_season_ranks,
                           season=season,
                           team_games=team_games,
                           playoffs_team_games=playoffs_team_games,
                           team_season=team_season_info,
                           roster=roster,
                           coaches=coaches,
                           current_season_info=current_season_info,
                           team_img=TEAM_ID_DATA)

@app.route('/teams/<teamid>/season/<season>/')
def teams_and_season(teamid, season):
    # season example: "2016-17"
    # type example: "Regular Season" or "Playoffs" 
    team_game_log = team.TeamGameLogs(teamid,
                                      season=season)
    team_games = team_game_log.info()

    playoffs_teamgamelogs = team.TeamGameLogs(teamid,
                                              season=season,
                                              season_type="Playoffs")
    playoffs_team_games = playoffs_teamgamelogs.info()

    team_summary = team.TeamSummary(teamid,
                                    season=season)
    team_summary_info = team_summary.info()
    team_season_ranks = team_summary.season_ranks()

    team_common_roster = team.TeamCommonRoster(teamid)
    roster = team_common_roster.roster()
    coaches = team_common_roster.coaches()

    team_season = team.TeamSeasons(teamid)
    team_season_info = team_season.info()

    for i in team_season_info:
        if (i["YEAR"] == season):
            current_season_info = i

    return render_template("teams.html",
                           title=team_summary_info[0]["TEAM_CITY"] + " " + team_summary_info[0]["TEAM_NAME"],
                           teamid=teamid,
                           team_summary_info=team_summary_info,
                           team_season_ranks=team_season_ranks,
                           season=season,
                           team_games=team_games,
                           playoffs_team_games=playoffs_team_games,
                           current_season_info=current_season_info,
                           team_img=TEAM_ID_DATA)

@app.route('/teamvsteam')
def team_vs_team():
    """Comparing team lineups.
    """
    league_dash_lineups = league.Lineups()
    league_dash_lineups_overall = league_dash_lineups.overall()

    for i in league_dash_lineups_overall:
      new_group_name = ""
      split_group_name = i["GROUP_NAME"].split("-")
      for j, value in enumerate(split_group_name):
        first_last = ' '.join(reversed(value.split(',')))
        if (j != len(split_group_name) - 1):
          new_group_name += first_last + " - "
        else:
          new_group_name += first_last
      i["GROUP_NAME"] = new_group_name

    return render_template("teamvsteam.html",
                           title="Team vs Team",
                           league_dash_lineups=league_dash_lineups_overall)

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
    print(name)
    split_name = name.split(" ", 1)
    fullname = name.lower()
    if name.upper() == "YAO MING":
        return redirect(url_for("players", playerid="2397"))
    
    print('try to find the player')
    player = playersapi.find_players_by_full_name(fullname)
    print(player)
    try:
        getplayerid = player[0]['id']
        get_player = True
    except:
        print('couldny find player')
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
    
    print(name)
    fullname = name.lower()
    
    print('try to find the player')
    player = playersapi.find_players_by_full_name(fullname)
    print(player)
    try:
        getplayerid = player[0]['id']
        get_player1 = True
    except:
        print('couldny find player')
        get_player1 = False

    fullname = name2.lower()
    
    print('try to find the player')
    player = playersapi.find_players_by_full_name(fullname)
    try:
        getplayerid2 = player[0]['id']
        get_player2 = True
    except:
        print('couldny find player')
        get_player2 = False
        
    if get_player1 == True and get_player2 == True:
        return redirect(url_for("player_vs_player", playerid=getplayerid, playerid2=getplayerid2))
    else:
        return render_template("search.html")
      
if __name__ == "__main__":
    # Run officially on a web server.
    # app.run(threaded=True)
    # Run on localhost with port 8080.
    app.run(host='0.0.0.0', port=4000, threaded=True, debug = True)
