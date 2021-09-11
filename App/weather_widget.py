import dash
import json
import pyowm
import pytz
import requests

import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objects as go

from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from datetime import datetime, timedelta
from flask import request
from urllib.request import urlopen

#%% Helper Functions

'''Initialize and return basic weather objects

manager and weather are used to retrieve current and forecasted weather data
location and time data are used for data retrieval and output
'''
def initialize_weather(location):
    # check if location is available, esle set default to Dayton, OH
    try:
        city, state, country, timezone_name = location['city'], location['region'], location['country'], location['timezone']
        lat, lon = float(location['loc'].split(',')[0]), float(location['loc'].split(',')[1])
    except:
        city, state, country, timezone_name = DAYTON['city'], DAYTON['region'], DAYTON['country'], DAYTON['timezone']
        lat, lon = float(DAYTON['loc'].split(',')[0]), float(DAYTON['loc'].split(',')[1])

    owm = pyowm.OWM(API_KEY)
    manager = owm.weather_manager()
    observation = manager.weather_at_place(f'{city}, {state}, {country}')
    weather = observation.weather

    reg = owm.city_id_registry()
    state_abbr = states_df[states_df['State']==state]['Abbreviation'].values[0]
    city_id, city, state = reg.ids_for(city, state_abbr)[0]

    timezone = pytz.timezone(timezone_name)
    time = datetime.today().astimezone(timezone).strftime('%I:%M %p')
    weekday = datetime.today().astimezone(timezone).strftime('%A')

    return manager, weather, city, state, country, timezone_name, lat, lon, time, weekday

'''Return a dictionary of formatted weather data

For pretty printing
'''
def get_weather_fmt(weather):
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
def get_forecast(manager, city, state, country, timezone_name):
    timezone = pytz.timezone(timezone_name)
    now = datetime.now().astimezone(timezone)

    times = [now + timedelta(hours=3*i) for i in range(8)]
    times_fmt = [t.strftime('%I %p').lstrip('0') for t in times]

    forecast_hourly = manager.forecast_at_place(f'{city}, {state}, {country}', '3h')

    temps = [w.temperature('fahrenheit')['temp'] for w in forecast_hourly.forecast.weathers][:8]
    precip = [w.rain[list(w.rain.keys())[0]] if w.rain else 0 for w in forecast_hourly.forecast.weathers][:8]
    humid = [w.humidity for w in forecast_hourly.forecast.weathers][:8]

    return times_fmt, temps, precip, humid

'''Return a plot of forecasted temperature data'''
def plot_temp_forecast(times, temps):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(temps))),
        y=temps,
        line_shape='spline',
        fill='tozeroy',
        mode='text',
        # Display rounded temperatures above all points but the first and last
        text=[round(temps[i]) if i in range(1,len(temps)-1) else None for i in range(len(temps))],
        textfont=dict(size=14),
        textposition='top center',
        fillcolor='rgba(117,250,202,0.5)'
    ))
    fig.update_layout(
        template='plotly_white',
        yaxis_title='Temperature \u00b0F',
        xaxis = dict(
            tickvals = list(range(len(times))),
            ticktext = times,
        ),
        margin = {
            't': 50,
            'b': 50
        },
        yaxis_range=(0.5*(3*min(temps) - max(temps)), 0.5*(3*max(temps) - min(temps))),
        font = dict(size=14)
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)

    return fig

'''Return a plot of forecasted precipitation data'''
def plot_precip_forecast(times, precip):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(precip))),
        y=precip,
        line_shape='spline',
        fill='tozeroy',
        mode='text',
        # Display rounded temperatures above all points but the first and last
        text=[round(precip[i], 2) if i in range(1,len(precip)-1) else None for i in range(len(precip))],
        textfont=dict(size=14),
        textposition='top center',
        fillcolor='rgba(85,157,218,0.5)'

    ))
    fig.update_layout(
        template='plotly_white',
        yaxis_title='Precipitation (mm)',
        xaxis = dict(
            tickvals = list(range(len(times))),
            ticktext = times,
        ),
        margin = {
            't': 50,
            'b': 50
        },
        yaxis_range=(max(0, 0.5*(3*min(precip) - max(precip))), 0.5*(3*max(precip) - min(precip))),
        font = dict(size=14)
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)

    return fig

'''Return a plot of forecasted humidity data'''
def plot_humid_forecast(times, humid):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(humid))),
        y=humid,
        line_shape='spline',
        fill='tozeroy',
        mode='text',
        # Display rounded temperatures above all points but the first and last
        text=[round(humid[i]) if i in range(1,len(humid)-1) else None for i in range(len(humid))],
        textfont=dict(size=14),
        textposition='top center',
        fillcolor='rgba(225, 204, 255, 0.5)'
    ))
    fig.update_layout(
        template='plotly_white',
        yaxis_title='Humidity %',
        xaxis = dict(
            tickvals = list(range(len(times))),
            ticktext = times,
        ),
        margin = {
            't': 50,
            'b': 50
        },
        yaxis_range=(max(0, 0.5*(3*min(humid) - max(humid))), 0.5*(3*max(humid) - min(humid))),
        font = dict(size=14)
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)

    return fig

'''Return daily forecast weather data

Formatted times, daily high/low temperatures, and weather icons used for week-long daily forecast display
'''
def get_daily_forecast(manager, lat, lon, timezone_name):
    timezone = pytz.timezone(timezone_name)
    now = datetime.now().astimezone(timezone)

    times = [now + timedelta(days=i) for i in range(7)]
    times_fmt = [t.strftime('%A') for t in times]

    forecast_daily = manager.one_call(lat, lon).forecast_daily
    temps_hi =  [round(w.temperature('fahrenheit')['max']) for w in forecast_daily][:7]
    temps_lo =  [round(w.temperature('fahrenheit')['min']) for w in forecast_daily][:7]
    icons = [w.weather_icon_url(size='4x') for w in forecast_daily[:7]]

    return times_fmt, temps_hi, temps_lo, icons

def get_emergency_alerts(manager, lat, lon, timezone_name):
    timezone = pytz.timezone(timezone_name)

    response = requests.get(f'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=current,minutely,hourly,daily&appid={API_KEY}')
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
#%% Build Dash App

# Copied this stylesheet to a local folder after experiencing hiccups in accessibility
#external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__)#, external_stylesheets=external_stylesheets)

app.title = 'Weather Data'

states_df = pd.read_csv('https://raw.githubusercontent.com/jasonong/List-of-US-States/master/states.csv')

DAYTON = {'city': 'Dayton', 'region': 'Ohio', 'country': 'US', 'timezone': 'America/New_York', 'loc':'39.7589,-84.1916'}

API_KEY = '87d1e91aebccc414e8d2139c6461decd'

'''Define the layout of the Dash application'''
def layout_function():

    # set default location
    location = DAYTON

    manager, weather, city, state, country, timezone_name, lat, lon, time, weekday = initialize_weather(location)
    wtr = get_weather_fmt(weather)
    times, temps, precip, humid = get_forecast(manager, city, state, country, timezone_name)
    weekdays, daily_hi, daily_lo, daily_icon = get_daily_forecast(manager, lat, lon, timezone_name)

    return html.Center(html.Div([
        # Header
        html.Div(
            [
                html.Div(
                    [
                        html.Img(id='icon', src=weather.weather_icon_url(size='4x'), width='100px'),

                        dcc.Markdown(id='temp', children=f'## {wtr["temperature"]}'),

                        html.Div(
                            dcc.Markdown(
                                id = 'status',

                                children = f'Precipitation: {wtr["precipitation"]}\n\n' +
                                    f'Humidity: {wtr["humidity"]}%\n\n' +
                                    f'Wind: {wtr["wind"]}'
                            ),

                            style={'padding-left':'50px', 'color':'darkGrey', 'line-height':'0.75', 'text-align':'left'}
                        ),
                    ],

                    style={'display':'flex', 'align-items':'center', 'float':'left'}     
                ),

                html.Div(
                    [
                        dcc.Markdown(id='location', children=f'##### {city}, {state}'),

                        html.Div(
                            
                            dcc.Markdown(
                                id = 'date-time-status',

                                children = f'{weekday} {time}\n\n' +
                                f'{wtr["status"]}'
                            ),

                            style = {'color':'darkGrey', 'line-height':'0.75'}
                        ),  
                    ],

                    style = {'float':'right', 'padding-right':'10px', 'text-align':'right'}
                ),
            ],
        ),
        
        # National Weather Alerts
        html.Details(
            [
                html.Summary('\u26A0 National Weather Alert:\n\n'),
                dcc.Markdown(id='emergency-alert', children='', style={'padding-right':'10px'})
            ],
            id = 'emergency-alert-div',
            style={'display':'none'}
        ),

        # Temp Forecast
        html.Div(
            id = 'tabs-div',
            children = dcc.Tabs(id='forecast-tabs', children=[
                dcc.Tab(label='Temperature',children=[
                    dcc.Graph(id='temperature-forecast', figure=plot_temp_forecast(times, temps), style={'height':'33vw'}),
                ],
                style = {'padding':0, 'line-height':30, 'backgroundColor':'white', 'borderTop':'0px', 'borderLeft':'0px', 'borderBottom':'0px'},
                selected_style={'padding':0, 'line-height':30, 'borderTop':'0px', 'borderLeft':'0px', 'borderBottom':'2px solid tomato'}
                ),

                dcc.Tab(label='Precipitation',children=[
                    dcc.Graph(id='precipitation-forecast', figure=plot_precip_forecast(times, precip), style={'height':'33vw'}),
                ],

                style = {'padding':0, 'line-height':30, 'backgroundColor':'white', 'borderTop':'0px','borderBottom':'0px'},
                selected_style={'padding':0, 'line-height':30, 'borderTop':'0px', 'borderBottom':'2px solid tomato'}
                ),

                dcc.Tab(label='Humidity',children=[
                    dcc.Graph(id='humidity-forecast', figure=plot_humid_forecast(times, humid), style={'height':'33vw'}),
                ],
                style = {'padding':0, 'line-height':30, 'backgroundColor':'white', 'borderTop':'0px', 'borderRight':'0px', 'borderBottom':'0px'},
                selected_style={'padding':0, 'line-height':30, 'borderTop':'0px', 'borderRight':'0px', 'borderBottom':'2px solid tomato'}
                )
            ],
            style = {'height': 30, 'width':'67%'}
            ),

            style={'float':'bottom', 'padding-top':'100px', 'width':'100%'}
        ),

        html.Center(
            [
                html.Center(
                    [
                        html.Div(
                            dcc.Markdown(id=f'weekday-{i}', children=weekdays[i][:3]),
                            style = {'color':'darkGrey'}
                        ),                        
                        
                        html.Img(id=f'daily-forecast-{i}', src=daily_icon[i], width='100px'),
                        
                        html.Div(
                            dcc.Markdown(id=f'hi-lo-{i}', children=f'**{daily_hi[i]}\u00b0** {daily_lo[i]}\u00b0'),
                            style = {'color':'darkGrey'}
                        )
                       
                    ],

                    style = {'display':'table-cell', 'text-align':'center', 'justify-content':'center', 'padding-top':'30px', 'line-height':'0'}
                )

            for i in range(len(weekdays))],

            style = {'display':'table', 'width':'100%', 'table-layout':'fixed'}
            
        ),

        html.Center(
            dcc.Markdown('Data provided by OpenWeather\u2122.'),
            style = {'padding-top':'100px','font-size':'12px'}
        ),

        html.Br(),

        dcc.Interval(
            id='minute-interval',
            interval= 60*1000, # one minute (ms)
            n_intervals=0
        ),

        dcc.Interval(
            id='thirty-minute-interval',
            interval=30*60*1000, # thirty minutes (ms)
            n_intervals=0
        ),

        # Location object (dummy to trigger location grab)
        dcc.Location(id='url'),

        # Storing client ip in a Store object
        dcc.Store(id='memory-output', data=location)

    ]))

app.layout = layout_function

'''Store location JSON data in Store object'''
@app.callback(
    Output(component_id='memory-output', component_property='data'),
    Input(component_id='url', component_property='pathname')
)
def update_location(pathname):
    ip = request.remote_addr

    url = f'http://ipinfo.io/{ip}?token=00dd9ffb16a928'
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
    ],
    
    [
        Input(component_id='minute-interval', component_property='n_intervals'),
        Input(component_id='memory-output', component_property='data')
    ]
)
def refresh_page(n_intervals, location):
    manager, weather, city, state, country, timezone_name, lat, lon, time, weekday = initialize_weather(location)
    wtr = get_weather_fmt(weather)
    times, temps, precip, humid = get_forecast(manager, city, state, country, timezone_name)

    icon = weather.weather_icon_url(size='4x')

    temp = f'## {wtr["temperature"]}'

    status = f'Precipitation: {wtr["precipitation"]}\n\nHumidity: {wtr["humidity"]}%\n\nWind: {wtr["wind"]}'
    
    location = f'##### {city}, {state}'
    
    date_time_status = children = f'{weekday} {time}\n\n{wtr["status"]}'

    temp_fig = plot_temp_forecast(times, temps)
    precip_fig = plot_precip_forecast(times, precip)
    humid_fig = plot_humid_forecast(times, humid)

    return icon, temp, status, location, date_time_status, temp_fig, precip_fig, humid_fig

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

            manager, weather, city, state, country, timezone_name, lat, lon, time, weekday = initialize_weather(location)
            weekdays, daily_hi, daily_lo, daily_icon = get_daily_forecast(manager, lat, lon, timezone_name)
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
        
            manager, weather, city, state, country, timezone_name, lat, lon, time, weekday = initialize_weather(location)
            weekdays, daily_hi, daily_lo, daily_icon = get_daily_forecast(manager, lat, lon, timezone_name)

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

            manager, weather, city, state, country, timezone_name, lat, lon, time, weekday = initialize_weather(location)
            weekdays, daily_hi, daily_lo, daily_icon = get_daily_forecast(manager, lat, lon, timezone_name)

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
    manager, weather, city, state, country, timezone_name, lat, lon, time, weekday = initialize_weather(location)

    senders, events, starts, ends, descriptions = get_emergency_alerts(manager, lat, lon, timezone_name)

    alert_style = {'display':'none'}
    tabs_style={'float':'bottom', 'padding-top':'100px', 'width':'100%'}

    message = ''

    if senders:

        alert_style = {
            'color':'white',
            'background-color':'crimson',
            'text-align':'justify',
            'border-radius':'5px',
            'width':'1012px',
            'display':'inline-block',
            'padding-top':'5px',
            'padding-left':'10px',
            'margin-right':'10px',
        }

        tabs_style={'float':'bottom', 'padding-top':'30px', 'width':'100%'}

        for i in range(len(senders)):
            message = f'\n\n{senders[i]} has issued a {events[i]} in effect from {starts[i]} until {ends[i]}.\n\n{descriptions[i]}'

    return alert_style, message, tabs_style

if __name__ == '__main__':
    app.run_server(debug=False, port=80, host='0.0.0.0')