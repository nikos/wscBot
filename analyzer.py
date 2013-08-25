#!/usr/bin/python
# -*- coding: utf-8 -*-

import json

from datetime import datetime, time
import logging
import dateutil

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import quote_dropper
from weather import WeatherInfo

# --

Base = declarative_base()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --

def game2str(game):
    return "%s  -- %s [%d] : %s [%d]" % (game['date'], game['hostName'], game['hostGoals'], game['guestName'], game['guestGoals'])

if __name__ == '__main__':

    engine = create_engine('sqlite:///weather.db', echo=False)
    Base.metadata.create_all(engine)

    DBSession = sessionmaker(bind=engine)
    session = DBSession()

    owm_begintime = datetime(2012, 10, 3, 0, 0)

    last_season_games = json.loads(open('data/games_2012.json').read())

    for game in last_season_games:
        d = dateutil.parser.parse(game['date'])
        host_team = game['hostName']
        guest_team = game['guestName']

        if 'Hamburg' in host_team or 'Hamburg' in guest_team:
            logger.info("Begegnung: %s", game2str(game))
            for city in [quote_dropper.team2city[host_team], quote_dropper.team2city[guest_team]]:
                starttime = datetime.combine(d.date(), time(12, 30))
                endtime = datetime.combine(d.date(), time(13, 30))
                if starttime > owm_begintime:
                    w = WeatherInfo.retrieveHistoricWeather(city, starttime, endtime)
                    if w:
                        logger.info("Wetter in %s am %s: %s", city, w.weatherstation_timestamp, w)
                        #session.add(w)

    #session.commit()