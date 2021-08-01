import dash
import json
import pyowm
import pytz
import re

import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objects as go

from dash.dependencies import Input, Output, State
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
    except:
        city, state, country, timezone_name = DAYTON['city'], DAYTON['region'], DAYTON['country'], DAYTON['timezone']

    owm = pyowm.OWM('87d1e91aebccc414e8d2139c6461decd')
    manager = owm.weather_manager()
    observation = manager.weather_at_place(f'{city}, {state}, {country}')
    weather = observation.weather

    reg = owm.city_id_registry()
    state_abbr = states_df[states_df['State']==state]['Abbreviation'].values[0]
    city_id, city_name, state = reg.ids_for(city, state_abbr)[0]

    timezone = pytz.timezone(timezone_name)
    time = datetime.today().astimezone(timezone).strftime('%I:%M %p')
    weekday = datetime.today().astimezone(timezone).strftime('%A')

    return manager, weather, city_name, state, time, weekday

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
def get_temp_forecast(manager):
    timezone = pytz.timezone('America/New_York')
    now = datetime.now().astimezone(timezone)

    times = [now + timedelta(hours=3*i) for i in range(8)]
    times_fmt = [t.strftime('%I:00 %p') for t in times]

    forecast_hourly = manager.forecast_at_place('Dayton, Ohio, USA', '3h')

    temps = [w.temperature('fahrenheit')['temp'] for w in forecast_hourly.forecast.weathers][:8]
    precip = [w.rain[list(w.rain.keys())[0]] if w.rain else 0 for w in forecast_hourly.forecast.weathers][:8]
    humid = [w.humidity for w in forecast_hourly.forecast.weathers][:8]

    return times_fmt, temps, precip, humid

'''Return a plot of forecasted temperature data'''
def plot_temp_forecast(times, temps):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(len(temps))), y=temps, line_shape='spline', line=dict(color='steelBlue'), fill='tozeroy'))
    fig.update_layout(
        yaxis_title='Temperature \u00b0F',
        xaxis_title='Time',
        xaxis = dict(
            tickvals = list(range(len(times))),
            ticktext = times,
        ),
        margin = {
            't': 50
        },
        yaxis_range=(0.5*(3*min(temps) - max(temps)), 0.5*(3*max(temps) - min(temps)))
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)

    return fig

'''Return a plot of forecasted precipitation data'''
def plot_precip_forecast(times, precip):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(len(precip))), y=precip, line_shape='spline', line=dict(color='steelBlue'), fill='tozeroy'))
    fig.update_layout(
        yaxis_title='Precipitation (mm)',
        xaxis_title='Time',
        xaxis = dict(
            tickvals = list(range(len(times))),
            ticktext = times,
        ),
        margin = {
            't': 50
        },
        yaxis_range=(max(0, 0.5*(3*min(precip) - max(precip))), 0.5*(3*max(precip) - min(precip)))
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)

    return fig

'''Return a plot of forecasted humidity data'''
def plot_humid_forecast(times, humid):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(len(humid))), y=humid, line_shape='spline', line=dict(color='steelBlue'), fill='tozeroy'))
    fig.update_layout(
        yaxis_title='Humidity %',
        xaxis_title='Time',
        xaxis = dict(
            tickvals = list(range(len(times))),
            ticktext = times,
        ),
        margin = {
            't': 50
        },
        yaxis_range=(max(0, 0.5*(3*min(humid) - max(humid))), 0.5*(3*max(humid) - min(humid)))
    )
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)

    return fig

'''Return daily forecast weather data

Formatted times, daily high/low temperatures, and weather icons used for week-long daily forecast display
'''
def get_daily_forecast(manager):
    now = datetime.now().astimezone()

    times = [now + timedelta(days=i) for i in range(7)]
    times_fmt = [t.strftime('%A') for t in times]
    
    forecast_daily = manager.one_call(lat=39.7589, lon=-84.1916).forecast_daily
    temps_hi =  [round(w.temperature('fahrenheit')['max']) for w in forecast_daily][:7]
    temps_lo =  [round(w.temperature('fahrenheit')['min']) for w in forecast_daily][:7]
    icons = [w.weather_icon_url(size='4x') for w in forecast_daily[:7]]

    return times_fmt, temps_hi, temps_lo, icons

#%% Build Dash App

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.title = 'Weather Data'

states_df = pd.read_csv('https://raw.githubusercontent.com/jasonong/List-of-US-States/master/states.csv')

DAYTON = {'city': 'Dayton', 'region': 'Ohio', 'country': 'US', 'timezone': 'America/New_York'}

'''Define the layout of the Dash application'''
def layout_function():

    # set default location
    location = DAYTON

    manager, weather, city_name, state, time, weekday = initialize_weather(location)
    wtr = get_weather_fmt(weather)
    times, temps, precip, humid = get_temp_forecast(manager)
    weekdays, daily_hi, daily_lo, daily_icon = get_daily_forecast(manager)

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
                        dcc.Markdown(id='location', children=f'##### {city_name}, {state}'),

                        html.Div(
                            
                            dcc.Markdown(
                                id = 'date-time-status',

                                children = f'{weekday} {time}\n\n' +
                                f'{wtr["status"]}'
                            ),

                            style = {'color':'darkGrey', 'line-height':'0.75'}
                        ),  
                    ],

                    style = {'float':'right', 'padding-right':'50px', 'text-align':'right'}
                ),
            ]
        ),
        
        # Temp Forecast
        html.Div(
            dcc.Tabs(id='forecast-tabs', children=[
                dcc.Tab(label='Temperature',children=[
                    dcc.Graph(id='temperature-forecast', figure=plot_temp_forecast(times, temps)),
                ],
                style = {'padding':0, 'line-height':30, 'backgroundColor':'white', 'borderTop':'0px', 'borderLeft':'0px', 'borderBottom':'0px'},
                selected_style={'padding':0, 'line-height':30, 'borderTop':'0px', 'borderLeft':'0px', 'borderBottom':'2px solid tomato'}
                ),

                dcc.Tab(label='Precipitation',children=[
                    dcc.Graph(id='precipitation-forecast', figure=plot_precip_forecast(times, precip)),
                ],
                style = {'padding':0, 'line-height':30, 'backgroundColor':'white', 'borderTop':'0px','borderBottom':'0px'},
                selected_style={'padding':0, 'line-height':30, 'borderTop':'0px', 'borderBottom':'2px solid tomato'}
                ),

                dcc.Tab(label='Humidity',children=[
                    dcc.Graph(id='humidity-forecast', figure=plot_humid_forecast(times, humid)),
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

        dcc.Interval(
            id='interval-component',
            interval= 60*1000, # every minute
            n_intervals=0
        ),

        dcc.Location(id='url', refresh='False'),

        # Storing client ip in a Store object
        dcc.Store(id='memory-output', data=location)

    ], style={'width':'1024px'}))

app.layout = layout_function

'''Store location JSON data in Store object'''
@app.callback(
    Output(component_id='memory-output', component_property='data'),
    Input(component_id='url', component_property='pathname')
)
def update_location(pathname):
    ip = request.remote_addr
    url = f'http://ipinfo.io/{ip}'
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
        Input(component_id='interval-component', component_property='n_intervals'),
        Input(component_id='memory-output', component_property='data')
    ]
)
def refresh_page(n_intervals, location):
    manager, weather, city_name, state, time, weekday = initialize_weather(location)
    wtr = get_weather_fmt(weather)
    times, temps, precip, humid = get_temp_forecast(manager)

    icon = weather.weather_icon_url(size='4x')

    temp = f'## {wtr["temperature"]}'

    status = f'Precipitation: {wtr["precipitation"]}\n\nHumidity: {wtr["humidity"]}%\n\nWind: {wtr["wind"]}'
    
    location = f'##### {city_name}, {state}'
    
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
        Input(component_id='interval-component', component_property='n_intervals'),
        Input(component_id='memory-output', component_property='data')
    ]
)
def update_weekdays(n_intervals, location):
    manager, weather, city_name, state, time, weekday = initialize_weather(location)
    weekdays, daily_hi, daily_lo, daily_icon = get_daily_forecast(manager)
    weekdays = [w[:3] for w in weekdays] # just the first three letters

    return tuple(weekdays)

if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0')

'''Update daily forecast weather icons'''
@app.callback(
    [
        Output(component_id=f'daily-forecast-{i}', component_property='children')
        for i in range(7)
    ],

    [
        Input(component_id='interval-component', component_property='n_intervals'),
        Input(component_id='memory-output', component_property='data')
    ]
    
)
def update_daily_icons(n_intervals, location):
    manager, weather, city_name, state, time, weekday = initialize_weather(location)
    weekdays, daily_hi, daily_lo, daily_icon = get_daily_forecast(manager)

    return tuple(daily_icon[i] for i in range(len(weekdays)))

'''Update daily forecast high/low temperatures'''
@app.callback(
    [
        Output(component_id=f'hi-lo-{i}', component_property='children')
        for i in range(7)
    ],

    [
        Input(component_id='interval-component', component_property='n_intervals'),
        Input(component_id='memory-output', component_property='data')
    ]
)
def update_daily_hi_lo(n_intervals, location):
    manager, weather, city_name, state, time, weekday = initialize_weather(location)
    weekdays, daily_hi, daily_lo, daily_icon = get_daily_forecast(manager)

    return tuple(f'**{daily_hi[i]}\u00b0** {daily_lo[i]}' for i in range(len(weekdays)))