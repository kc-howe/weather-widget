from matplotlib.font_manager import json_dump
from weather_map import WeatherMap
from constants import get_constants
from forecast_plotter import ForecastPlotter

from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from flask import request
from urllib.request import urlopen

from app import app

import json
import dash

import dash_leaflet as dl

STATES_DF, DAYTON, OWM_KEY, IP_KEY, MGR = get_constants()

'''Store location JSON data in Store object'''
@app.callback(
    Output(component_id='memory-output', component_property='data'),
    Input(component_id='url', component_property='pathname')
)
def update_location(pathname):
    ip = request.remote_addr

    url = f'http://ipinfo.io/{ip}?token={IP_KEY}'
    response = urlopen(url)
    data = json.load(response)

    return data

'''Updates page data

Interval object used to update the time/temperature/status data every minute
'''
@app.callback(
    [
        Output(component_id='icon', component_property='src'),
        Output(component_id='temp', component_property='children'),
        Output(component_id='status', component_property='children'),
        Output(component_id='location', component_property='children'),
        Output(component_id='date-time-status', component_property='children'),
        Output(component_id='temperature-forecast', component_property='figure'),
        Output(component_id='precipitation-forecast', component_property='figure'),
        Output(component_id='humidity-forecast', component_property='figure'),
        Output(component_id='map', component_property='children'),
        Output(component_id='map', component_property='center')
    ],
    
    [
        Input(component_id='url', component_property='pathname'),
        Input(component_id='minute-interval', component_property='n_intervals'),
        Input(component_id='memory-output', component_property='data'),
        Input(component_id='map', component_property='bounds')
    ],
    prevent_initial_callback=False
)
def refresh_page(pathname, n_intervals, location, bounds_json):
    log = f'Refresh called. ({n_intervals})'
    manager, weather, city, state, country, timezone_name, lat, lon, time, weekday = MGR.initialize_weather(location, STATES_DF)
    wtr = MGR.get_weather_fmt(weather)
    forecast = MGR.get_forecast(manager, city, state, country, timezone_name)
    forecast_plotter = ForecastPlotter(forecast)

    icon = weather.weather_icon_url(size='4x')

    temp = f'## {wtr["temperature"]}'

    status = f'Precipitation: {wtr["precipitation"]}\n\nHumidity: {wtr["humidity"]}%\n\nWind: {wtr["wind"]}'
    
    location = f'##### {city}, {state}'
    
    date_time_status = f'{weekday} {time}\n\n{wtr["status"]}'

    temp_fig = forecast_plotter.plot_temp_forecast()
    precip_fig = forecast_plotter.plot_precip_forecast()
    humid_fig = forecast_plotter.plot_humid_forecast()

    center = (lat, lon)

    # Try to read JSON data from bounds object
    try:
        bounds = eval(json.dumps(bounds_json))
        weather_map = WeatherMap(center, 11, bounds, OWM_KEY)
        layers = weather_map.layers
    # Null JSON object should trigger an exception
    except:
        layers = [dl.TileLayer()]

    return icon, temp, status, location, date_time_status, temp_fig, precip_fig, humid_fig, layers, center

'''Update daily forecast weekday names'''
@app.callback(
    [
        Output(component_id=f'weekday-{i}', component_property='children')
        for i in range(7)
    ],

    [
        Input(component_id='minute-interval', component_property='n_intervals'),
        Input(component_id='date-time-status', component_property='children'),
        Input(component_id='memory-output', component_property='data')
    ]
)
def update_weekdays(n_intervals, datetime, location):
    # Check which input triggered the callback
    context = dash.callback_context
    if context.triggered:
        input_id = context.triggered[0]['prop_id'].split('.')[0]

    loc_triggered = (input_id == 'memory-output')

    # Only check for new daily forecasts at midnight or on page load
    if loc_triggered or datetime.split()[1] == '12:00':
        if loc_triggered or datetime.split()[2] == 'AM':

            manager, weather, city, state, country, timezone_name, lat, lon, time, weekday = MGR.initialize_weather(location, STATES_DF)
            weekdays, daily_hi, daily_lo, daily_icon = MGR.get_daily_forecast(manager, lat, lon, timezone_name)
            weekdays = [w[:3] for w in weekdays] # just the first three letters

            return tuple(weekdays)

    raise PreventUpdate

'''Update daily forecast weather icons'''
@app.callback(
    [
        Output(component_id=f'daily-forecast-{i}', component_property='children')
        for i in range(7)
    ],

    [
        Input(component_id='minute-interval', component_property='n_intervals'),
        Input(component_id='date-time-status', component_property='children'),
        Input(component_id='memory-output', component_property='data')
    ]
    
)
def update_daily_icons(n_intervals, datetime, location):
    # Check which input triggered the callback
    context = dash.callback_context
    if context.triggered:
        input_id = context.triggered[0]['prop_id'].split('.')[0]

    loc_triggered = (input_id == 'memory-output')

    # Only check for new daily forecasts at midnight or on page load
    if loc_triggered or datetime.split()[1] == '12:00':
        if loc_triggered or datetime.split()[2] == 'AM':
        
            manager, weather, city, state, country, timezone_name, lat, lon, time, weekday = MGR.initialize_weather(location, STATES_DF)
            weekdays, daily_hi, daily_lo, daily_icon = MGR.get_daily_forecast(manager, lat, lon, timezone_name)

            return tuple(daily_icon[i] for i in range(len(weekdays)))
    
    raise PreventUpdate

'''Update daily forecast high/low temperatures'''
@app.callback(
    [
        Output(component_id=f'hi-lo-{i}', component_property='children')
        for i in range(7)
    ],

    [
        Input(component_id='minute-interval', component_property='n_intervals'),
        Input(component_id='date-time-status', component_property='children'),
        Input(component_id='memory-output', component_property='data')
    ]
)
def update_daily_hi_lo(n_intervals, datetime, location):
    # Check which input triggered the callback
    context = dash.callback_context
    if context.triggered:
        input_id = context.triggered[0]['prop_id'].split('.')[0]

    loc_triggered = (input_id == 'memory-output')

    # Only check for new daily forecasts at midnight or on page load
    if loc_triggered or n_intervals > 0 and datetime.split()[1] == '12:00':
        if loc_triggered or datetime.split()[2] == 'AM':

            manager, weather, city, state, country, timezone_name, lat, lon, time, weekday = MGR.initialize_weather(location, STATES_DF)
            weekdays, daily_hi, daily_lo, daily_icon = MGR.get_daily_forecast(manager, lat, lon, timezone_name)

            return tuple(f'**{daily_hi[i]}\u00b0** {daily_lo[i]}' for i in range(len(weekdays)))
    
    raise PreventUpdate

@app.callback(
    [
        Output(component_id='emergency-alert-div', component_property='style'),
        Output(component_id='emergency-alert', component_property='children'),

        Output(component_id='tabs-div', component_property='style')
    ],

    [
        Input(component_id='thirty-minute-interval', component_property='n_intervals'),
        Input(component_id='memory-output', component_property='data')
    ]
)
def update_emergency_alert(n_intervals, location):
    manager, weather, city, state, country, timezone_name, lat, lon, time, weekday = MGR.initialize_weather(location, STATES_DF)

    senders, events, starts, ends, descriptions = MGR.get_emergency_alerts(manager, lat, lon, timezone_name)

    alert_style = {'display':'none'}
    tabs_style={'float':'bottom', 'padding-top':'100px', 'width':'100%'}

    message = ''

    if senders:

        alert_style = {
            'color':'white',
            'background-color':'crimson',
            'text-align':'justify',
            'border-radius':'5px',
            'width':'100%',
            'display':'inline-block',
            'padding-top':'2px',
            'padding-bottom':'2px',
            'padding-left':'10px',
            'margin-right':'10px',
        }

        tabs_style={'float':'bottom', 'padding-top':'30px', 'width':'100%'}

        for i in range(len(senders)):
            message = f'\n\n{senders[i]} has issued a {events[i]} in effect from {starts[i]} until {ends[i]}.\n\n{descriptions[i]}'

    return alert_style, message, tabs_style