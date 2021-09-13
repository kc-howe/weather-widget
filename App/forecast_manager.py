import pyowm
import pytz
import requests

from datetime import datetime, timedelta

'''
Class for managing forcasts, weather, and related functions.
'''
class ForecastManager():

    def __init__(self, location, key):
        self.location = location
        self.key = key

    '''Initialize and return basic weather objects

    manager and weather are used to retrieve current and forecasted weather data
    location and time data are used for data retrieval and output
    '''
    def initialize_weather(self, location, states):
        # check if location is available, esle set default to Dayton, OH
        try:
            city, state, country, timezone_name = location['city'], location['region'], location['country'], location['timezone']
            lat, lon = float(location['loc'].split(',')[0]), float(location['loc'].split(',')[1])
        except:
            city, state, country, timezone_name = 'Dayton', 'Ohio', 'US', 'America/New_York'
            lat, lon = 39.7589, -84.1916

        owm = pyowm.OWM(self.key)
        manager = owm.weather_manager()
        observation = manager.weather_at_place(f'{city}, {state}, {country}')
        weather = observation.weather

        reg = owm.city_id_registry()
        state_abbr = states[states['State']==state]['Abbreviation'].values[0]
        city_id, city, state = reg.ids_for(city, state_abbr)[0]

        timezone = pytz.timezone(timezone_name)
        time = datetime.today().astimezone(timezone).strftime('%I:%M %p')
        weekday = datetime.today().astimezone(timezone).strftime('%A')

        return manager, weather, city, state, country, timezone_name, lat, lon, time, weekday

    '''Return a dictionary of formatted weather data

    For pretty printing
    '''
    def get_weather_fmt(self, weather):
        weather_dict = dict(
            temperature = f'{round(weather.temperature("fahrenheit")["temp"])} \u00b0F',
            hi = f'{round(weather.temperature("fahrenheit")["temp_max"])} \u00b0F',
            lo = f'{round(weather.temperature("fahrenheit")["temp_min"])} \u00b0F',
            precipitation = f'{weather.precipitation_probability or 0}%',
            humidity = f'{weather.humidity}',
            wind = f'{round(weather.wind(unit="miles_hour")["speed"])} mph',
            status = f'{weather.detailed_status.title()}'
        )

        return weather_dict

    '''Return formatted times and forecasted temperatures

    temperatures and times used to plot forecasted temperature data
    '''
    def get_forecast(self, manager, city, state, country, timezone_name):
        timezone = pytz.timezone(timezone_name)
        now = datetime.now().astimezone(timezone)

        times = [now + timedelta(hours=3*i) for i in range(8)]
        times_fmt = [t.strftime('%I %p').lstrip('0') for t in times]

        forecast_hourly = manager.forecast_at_place(f'{city}, {state}, {country}', '3h')

        temps = [w.temperature('fahrenheit')['temp'] for w in forecast_hourly.forecast.weathers][:8]
        precip = [w.rain[list(w.rain.keys())[0]] if w.rain else 0 for w in forecast_hourly.forecast.weathers][:8]
        humid = [w.humidity for w in forecast_hourly.forecast.weathers][:8]

        return times_fmt, temps, precip, humid

    '''Return daily forecast weather data

    Formatted times, daily high/low temperatures, and weather icons used for week-long daily forecast display
    '''
    def get_daily_forecast(self, manager, lat, lon, timezone_name):
        timezone = pytz.timezone(timezone_name)
        now = datetime.now().astimezone(timezone)

        times = [now + timedelta(days=i) for i in range(7)]
        times_fmt = [t.strftime('%A') for t in times]

        forecast_daily = manager.one_call(lat, lon).forecast_daily
        temps_hi =  [round(w.temperature('fahrenheit')['max']) for w in forecast_daily][:7]
        temps_lo =  [round(w.temperature('fahrenheit')['min']) for w in forecast_daily][:7]
        icons = [w.weather_icon_url(size='4x') for w in forecast_daily[:7]]

        return times_fmt, temps_hi, temps_lo, icons

    def get_emergency_alerts(self, manager, lat, lon, timezone_name):
        timezone = pytz.timezone(timezone_name)

        response = requests.get(f'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=current,minutely,hourly,daily&appid={self.key}')
        response_dict = response.json()

        if 'alerts' in response_dict.keys():
            alerts = response_dict['alerts']

            senders = [alert['sender_name'] for alert in alerts]
            events = [alert['event'] for alert in alerts]
            starts = [datetime.utcfromtimestamp(alert['start']).astimezone(timezone).strftime('%I:%M %p') for alert in alerts] # ugly
            ends = [datetime.utcfromtimestamp(alert['end']).astimezone(timezone).strftime('%I:%M %p') for alert in alerts]
            descriptions = [alert['description'] for alert in alerts]

            return senders, events, starts, ends, descriptions
        
        return None, None, None, None, None