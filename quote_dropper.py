#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import date
import json
import logging

import dateutil.parser
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import my_secrets

from weather import WeatherInfo


Base = declarative_base()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


team2city = {
    u"1. FC Nürnberg": u"Nürnberg",
    "1. FSV Mainz 05": "Mainz",
    "Bayer 04 Leverkusen": "Leverkusen",
    u"Bayern München": u"München",
    u"Borussia Mönchengladbach": u"Mönchengladbach",
    "Borussia Dortmund": "Dortmund",
    "Eintracht Braunschweig": "Braunschweig",
    "Eintracht Frankfurt": "Frankfurt",
    "FC Augsburg": "Augsburg",
    "FC Schalke 04": "Gelsenkirchen",
    "Hamburger SV": "Hamburg",
    "Hannover 96": "Hannover",
    "Hertha BSC": "Berlin",
    "SC Freiburg": "Freiburg",
    "VfB Stuttgart": "Stuttgart",
    "VfL Wolfsburg": "Wolfsburg",
    "Werder Bremen": "Bremen",
    "TSG 1899 Hoffenheim": "Hoffenheim",
    # Letzte Saison in 1. Liga
    "SpVgg Greuther Fuerth": u"Fürth",
    u"Fortuna Düsseldorf": u"Düsseldorf"
}


def calc_weather_index(weather_info):
    temp_idx = 50.0 - 3.0 * abs(weather_info.temperature_cur - 22.0)
    if temp_idx < 0:
        temp_idx = 0.0
    humidity_idx = 25.0 - abs(weather_info.humidity - 40.0)
    if humidity_idx < 0.0:
        humidity_idx = 0.0
    wind_idx = 25.0 - 4.0 * weather_info.wind_speed
    if wind_idx < 0:
        wind_idx = 0.0

    return (temp_idx, humidity_idx, wind_idx)


def convert_weather_indexes_to_goals(host_weather_idx, guest_weather_idx):
    logger.info("  * Host  weather index in %40s: %s", team2city[host_team], host_weather_idx)
    logger.info("  * Guest weather index in %40s: %s", team2city[guest_team], guest_weather_idx)
    relation = sum(host_weather_idx) / sum(guest_weather_idx) - 1.0
    logger.info("   > %.3f", relation)

    # ~~ convert probability into match goals
    goals = "0:0"
    if   relation < 0.05:
        goals = "0:0"
    elif relation < 0.10:
        goals = "1:1"
    elif relation < 0.125:
        goals = "2:2"
    elif relation < 0.15:
        goals = "3:3"
    elif relation < 0.20:
        goals = "1:0"
    elif relation < 0.20:
        goals = "1:0"

    return goals


# -------------------------------------------------

if __name__ == '__main__':

    engine = create_engine('sqlite:///weather.db', echo=False)
    Base.metadata.create_all(engine)

    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    all_games = json.loads(open('data/games_2013.json').read())

    # ~~ get all games for today
    for game in all_games:
        d = dateutil.parser.parse(game['date'])
        if d.date() == date.today():

            host_team = game['hostName']
            guest_team = game['guestName']
            logger.info("%s:  %s : %s", d, host_team, guest_team)

            w_host = WeatherInfo.getLatest(session, team2city[host_team], date.today())
            w_guest = WeatherInfo.getLatest(session, team2city[guest_team], date.today())

            host_weather_idx = calc_weather_index(w_host)
            guest_weather_idx = calc_weather_index(w_guest)
            goals = convert_weather_indexes_to_goals(host_weather_idx, guest_weather_idx)

            # ~~ post our guestimate
            r = requests.post("http://botliga.de/api/guess",
                              params={"match_id": game['id'], "result": goals, "token": my_secrets.BOTLIGA_API_TOKEN})

            logger.info("Response from botliga: %s", r)


# ~~ once per day
# WeatherInfo.updateCities(session, team2city.values())
# session.commit()