#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime, time
import logging
from optparse import OptionParser

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, desc

import my_secrets

# ~~

Base = declarative_base()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeatherInfo(Base):
    """
      Holds weather details about one city retrieved at a specific
      point in time. Thanks to openweathermap there is only a small
      delay about 1-10 minutes to the current weather situation.
    """

    __tablename__ = 'weatherinfo'

    id = Column(Integer, primary_key=True)
    city = Column(String, index=True)
    summary = Column(String)
    icon = Column(String)
    rain_3h = Column(Float)            # rain in recent 3 hours
    wind_speed = Column(Float)         # Wind speed in mps (m/s)
    wind_direction = Column(Float)     # Wind direction in degrees (meteorological)
    temperature_cur = Column(Float)
    temperature_min = Column(Float)
    temperature_max = Column(Float)
    pressure = Column(Float)           # Atmospheric pressure in kPa
    humidity = Column(Float)
    weatherstation_timestamp = Column(DateTime, index=True)
    retrieved_at = Column(DateTime, index=True)

    def __repr__(self):
        return "<WeatherInfo('%s', T: %.1f C (min: %.1f C, max: %.1f C), H: %d%%, W: %.1f m/s)>" \
               % (self.summary, self.temperature_cur, self.temperature_min, self.temperature_max, self.humidity, self.wind_speed)

    @staticmethod
    def getLatest(session, city, date):
        """ Get most current weather record for given city and date
        """
        start_date = datetime.combine(date, time(0, 0))
        end_date = datetime.combine(date, time(23, 59, 59))
        return session.query(WeatherInfo) \
            .filter_by(city=city) \
            .filter(WeatherInfo.retrieved_at.between(start_date, end_date)) \
            .order_by(desc(WeatherInfo.retrieved_at)) \
            .first()

    @staticmethod
    def retrieveHistoricWeather(city, starttime, endtime):
        params = {"q": "%s,Germany" % city, "units": "metric", "cnt": 1,
                  "start": starttime.strftime("%s"), "end": endtime.strftime("%s")}
        headers = {"x-api-key": my_secrets.OPENWEATHERMAP_API_KEY}

        r = requests.get("http://api.openweathermap.org/data/2.5/history/city", params=params, headers=headers)
        logger.info("--> [%s, %s] Response %s", city, starttime, r)
        json = r.json()
        #logger.info("Anz. Eintraege %d", len(json['list']))
        if len(json['list']) > 0:
            return convertOpenWeatherMap2WeatherInfo(city, json['list'][0], metric=False)
        else:
            return None

    @staticmethod
    def retrieveCurrentWeather(city):

        params = {"q": "%s,Germany" % city, "units": "metric"}
        headers = {"x-api-key": my_secrets.OPENWEATHERMAP_API_KEY}

        r = requests.get("http://api.openweathermap.org/data/2.5/find", params=params, headers=headers)
        logger.info("Response", r)
        json = r.json()
        return convertOpenWeatherMap2WeatherInfo(city, json['list'][0])

    @staticmethod
    def updateCities(session, cities):
        for city in cities:
            logger.info("Get weather information for %s ...", city)
            weather = WeatherInfo.retrieveCurrentWeather(city)
            logger.info("   %s ", weather)
            session.add(weather)

# -- -- -- -- --


def convertOpenWeatherMap2WeatherInfo(city, w, metric = True):
    #json = {u'count': 1, u'message': u'accurate', u'list': [{u'clouds': {u'all': 75}, u'name': u'Hamburg', u'coord': {u'lat': 53.549999, u'lon': 10}, u'sys': {u'country': u'DE'}, u'weather': [{u'main': u'Clouds', u'id': 803, u'icon': u'04d', u'description': u'broken clouds'}], u'rain': {u'3h': 0.5}, u'dt': 1376211000, u'main': {u'pressure': 1016, u'temp_min': 15, u'temp_max': 20, u'temp': 17.35, u'humidity': 77}, u'id': 2911298, u'wind': {u'var_end': 290, u'var_beg': 220, u'speed': 5.7, u'deg': 260}}], u'cod': u'200'}
    rain_3h = 0.0
    if 'rain' in w:
        if '3h' in w['rain']:
            rain_3h = w['rain']['3h']
        else:
            logger.warn("rain has no 3h entry, but: %s", w['rain'])

    if not metric:
        w['main']['temp'] -= 273.15
        w['main']['temp_min'] -= 273.15
        w['main']['temp_max'] -= 273.15

    return WeatherInfo(city=city, summary=w['weather'][0]['description'], icon=w['weather'][0]['icon'],
                       rain_3h=rain_3h,
                       temperature_cur=w['main']['temp'],
                       temperature_min=w['main']['temp_min'],
                       temperature_max=w['main']['temp_max'],
                       pressure=w['main']['pressure'] if 'pressure' in w['main'] else 0.0,
                       humidity=w['main']['humidity'] if 'humidity' in w['main'] else 0.0,
                       wind_speed=w['wind']['speed'], wind_direction=w['wind']['deg'],
                       weatherstation_timestamp=datetime.fromtimestamp(w['dt']), retrieved_at=datetime.now())


# -----------------------------------------------------------------------------

if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option("-u", "--update",
                      action="store_true", dest="update", default=False,
                      help="update the current weather for all cities")
    (options, args) = parser.parse_args()

    if options.update:
        engine = create_engine('sqlite:///weather.db', echo=False)
        Base.metadata.create_all(engine)

        DBSession = sessionmaker(bind=engine)
        session = DBSession()
        #WeatherInfo.updateCities(session, quote_dropper.team2city.values())
        session.commit()
    else:
        # History of OpenWeatherMap seems to start 3-Oct-2012
        starttime = datetime(2012, 10, 3, 12, 30, 0)
        endtime = datetime(2012, 10, 3, 13, 30, 0)

        for city in ['Hamburg', 'Berlin', 'Freiburg']:
            w = WeatherInfo.retrieveHistoricWeather(city, starttime, endtime)
            if w:
                logger.info("Wetter in %s am %s: %s", city, w.weatherstation_timestamp, w)