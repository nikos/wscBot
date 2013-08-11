wscBot
======

Bot for making incredible wise guesses about next soccer games for the botLiga

## botliga & co ##

Einreichen eines Tipps für die botliga:

    curl -X POST --data "match_id=MATCH_ID&result=2:1&token=THE_TOKEN" http://botliga.de/api/guess

Nützliche Resourcen

  * Download des JSON zur aktuellen Saison:
    http://botliga.de/api/matches/2013

  * Liste aller Teams der 1. Bundesliga
    http://openligadb-json.heroku.com/api/teams_by_league_saison?league_saison=2013&league_shortcut=bl1


## Wetterdaten ##

  * OpenWeatherMap Seite für Hamburg: http://openweathermap.org/city/2911298

  * API Abfrage der Wetterwerte für Hamburg:
    http://api.openweathermap.org/data/2.5/weather?q=Hamburg,Germany

  * Dokumentation der API für OpenWeatherMap Zugriff:
    http://bugs.openweathermap.org/projects/api/wiki/


## Zusammenhang Wetter & Sport ##

  * Heat Index: http://en.wikipedia.org/wiki/Heat_index
  * Wind Chill: http://de.wikipedia.org/wiki/Windchill
