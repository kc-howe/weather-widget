import dash
import pyowm
import pytz

import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go

from dash.dependencies import Input, Output
from datetime import datetime, timedelta

#%% Helper Functions

'''Initialize and return basic weather objects

manager and weather are used to retrieve current and forecasted weather data
location and time data are used for data retrieval and output
'''
def initialize_weather():
    owm = pyowm.OWM('87d1e91aebccc414e8d2139c6461decd')
    manager = owm.weather_manager()
    observation = manager.weather_at_place('Dayton, Ohio, USA')
    weather = observation.weather

    reg = owm.city_id_registry()
    city_id, city_name, state = reg.ids_for('Dayton', country='OH')[0]

    timezone = pytz.timezone('America/New_York')
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
        humidity = f'{weather.humidity}%',
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

    return times_fmt, temps

'''Return a plot of forecasted temperature data'''
def plot_temp_forecast(forecast):
    times, temps = forecast
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(len(temps))), y=temps, line_shape='spline', line=dict(color='steelBlue'), fill='tozeroy'))
    fig.update_layout(
        title='Temperature Forecast',
        yaxis_title='Temperature \u00b0F',
        xaxis_title='Time',
        xaxis = dict(
            tickvals = list(range(len(times))),
            ticktext = times,
        ),
        yaxis_range=(max(temps) - .33*min(temps), .33*max(temps) + min(temps))
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

'''Define the layout of the Dash application'''
def layout_function():

    manager, weather, city_name, state, time, weekday = initialize_weather()
    wtr = get_weather_fmt(weather)
    forecast = get_temp_forecast(manager)
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
        html.Center(
            dcc.Graph(id='temperature-forecast', figure=plot_temp_forecast(forecast)),
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

    ], style={'width':'1024px'}))

app.layout = layout_function

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
    ],
    
    Input(component_id='interval-component', component_property='n_intervals')
)
def refresh_page(n_intervals):
    manager, weather, city_name, state, time, weekday = initialize_weather()
    wtr = get_weather_fmt(weather)
    forecast = get_temp_forecast(manager)

    icon = weather.weather_icon_url(size='4x')

    temp = f'## {wtr["temperature"]}'

    status = f'Precipitation: {wtr["precipitation"]}\n\nHumidity: {wtr["humidity"]}%\n\nWind: {wtr["wind"]}'
    
    location = f'##### {city_name}, {state}'
    
    date_time_status = children = f'{weekday} {time}\n\n{wtr["status"]}'

    figure = plot_temp_forecast(forecast)

    return icon, temp, status, location, date_time_status, figure

'''Update daily forecast weekday names'''
@app.callback(
    [
        Output(component_id=f'weekday-{i}', component_property='children')
        for i in range(7)
    ],

    Input(component_id='interval-component', component_property='n_intervals')
)
def update_weekdays(n_intervals):
    manager, weather, city_name, state, time, weekday = initialize_weather()
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

    Input(component_id='interval-component', component_property='n_intervals')
)
def update_daily_icons(n_intervals):
    manager, weather, city_name, state, time, weekday = initialize_weather()
    weekdays, daily_hi, daily_lo, daily_icon = get_daily_forecast(manager)

    return tuple(daily_icon[i] for i in range(len(weekdays)))

'''Update daily forecast high/low temperatures'''
@app.callback(
    [
        Output(component_id=f'hi-lo-{i}', component_property='children')
        for i in range(7)
    ],

    Input(component_id='interval-component', component_property='n_intervals')
)
def update_daily_hi_lo(n_intervals):
    manager, weather, city_name, state, time, weekday = initialize_weather()
    weekdays, daily_hi, daily_lo, daily_icon = get_daily_forecast(manager)

    return tuple(f'**{daily_hi[i]}\u00b0** {daily_lo[i]}' for i in range(len(weekdays)))

# %%
