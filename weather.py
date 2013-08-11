from datetime import datetime, time
import logging

import requests
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
        return "<WeatherInfo('%s','%s', '%s')>" % (self.summary, self.temperature_cur, self.rain_3h)

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
    def retrieveCurrentWeather(city):

        params = {"q": "%s,Germany" % city, "units": "metric"}
        headers = {"x-api-key": my_secrets.OPENWEATHERMAP_API_KEY}

        r = requests.get("http://api.openweathermap.org/data/2.5/find", params=params, headers=headers)
        logger.info("Response", r)
        json = r.json()
        logger.debug(json)

        #json = {u'count': 1, u'message': u'accurate', u'list': [{u'clouds': {u'all': 75}, u'name': u'Hamburg', u'coord': {u'lat': 53.549999, u'lon': 10}, u'sys': {u'country': u'DE'}, u'weather': [{u'main': u'Clouds', u'id': 803, u'icon': u'04d', u'description': u'broken clouds'}], u'rain': {u'3h': 0.5}, u'dt': 1376211000, u'main': {u'pressure': 1016, u'temp_min': 15, u'temp_max': 20, u'temp': 17.35, u'humidity': 77}, u'id': 2911298, u'wind': {u'var_end': 290, u'var_beg': 220, u'speed': 5.7, u'deg': 260}}], u'cod': u'200'}
        w = json['list'][0]

        rain_3h = 0.0
        if 'rain' in w:
            rain_3h = w['rain']['3h']

        return WeatherInfo(city=city, summary=w['weather'][0]['description'], icon=w['weather'][0]['icon'],
                           rain_3h=rain_3h,
                           temperature_cur=w['main']['temp'],
                           temperature_min=w['main']['temp_min'], temperature_max=w['main']['temp_max'],
                           pressure=w['main']['pressure'], humidity=w['main']['humidity'],
                           wind_speed=w['wind']['speed'], wind_direction=w['wind']['deg'],
                           weatherstation_timestamp=datetime.fromtimestamp(w['dt']), retrieved_at=datetime.now())

    @staticmethod
    def updateCities(session, cities):
        for city in cities:
            logger.info("Get weather information for %s ...", city)
            weather = WeatherInfo.retrieveCurrentWeather(city)
            logger.info("   %s ", weather)
            session.add(weather)