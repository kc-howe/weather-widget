from constants import get_constants
from forecast_plotter import ForecastPlotter

import dash_core_components as dcc
import dash_html_components as html

'''Define the layout of the Dash application'''
def layout_function():

    STATES_DF, DAYTON, API_KEY, MGR = get_constants()

    wtr_manager, weather, city, state, country, timezone_name, lat, lon, time, weekday = MGR.initialize_weather(DAYTON, STATES_DF)
    wtr = MGR.get_weather_fmt(weather)
    forecast = MGR.get_forecast(wtr_manager, city, state, country, timezone_name)
    forecast_plotter = ForecastPlotter(forecast)
    weekdays, daily_hi, daily_lo, daily_icon = MGR.get_daily_forecast(wtr_manager, lat, lon, timezone_name)

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
                    dcc.Graph(id='temperature-forecast', figure=forecast_plotter.plot_temp_forecast(), style={'height':'30vw'}),
                ],
                style = {'padding':0, 'line-height':30, 'backgroundColor':'white', 'borderTop':'0px', 'borderLeft':'0px', 'borderBottom':'0px'},
                selected_style={'padding':0, 'line-height':30, 'borderTop':'0px', 'borderLeft':'0px', 'borderBottom':'2px solid tomato'}
                ),

                dcc.Tab(label='Precipitation',children=[
                    dcc.Graph(id='precipitation-forecast', figure=forecast_plotter.plot_precip_forecast(), style={'height':'30vw'}),
                ],

                style = {'padding':0, 'line-height':30, 'backgroundColor':'white', 'borderTop':'0px','borderBottom':'0px'},
                selected_style={'padding':0, 'line-height':30, 'borderTop':'0px', 'borderBottom':'2px solid tomato'}
                ),

                dcc.Tab(label='Humidity',children=[
                    dcc.Graph(id='humidity-forecast', figure=forecast_plotter.plot_humid_forecast(), style={'height':'30vw'}),
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
        dcc.Store(id='memory-output', data=DAYTON)

    ], style={'width':'80%'}))