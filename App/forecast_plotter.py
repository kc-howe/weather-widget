import plotly.graph_objects as go

'''
Class for plotting forecasts from weather manager.
'''
class ForecastPlotter():

    def __init__(self, forecast):
        self.times = forecast[0]
        self.temps = forecast[1]
        self.precip = forecast[2]
        self.humid = forecast[3]

    '''Return a plot of forecasted temperature data'''
    def plot_temp_forecast(self):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(len(self.temps))),
            y=self.temps,
            line_shape='spline',
            fill='tozeroy',
            mode='text',
            # Display rounded temperatures above all points but the first and last
            text=[round(self.temps[i]) if i in range(1,len(self.temps)-1) else None for i in range(len(self.temps))],
            textfont=dict(size=14),
            textposition='top center',
            fillcolor='rgba(117,250,202,0.5)'
        ))
        fig.update_layout(
            template='plotly_white',
            yaxis_title='Temperature \u00b0F',
            xaxis = dict(
                tickvals = list(range(len(self.times))),
                ticktext = self.times,
            ),
            margin = {
                't': 50,
                'b': 50
            },
            yaxis_range=(0.5*(3*min(self.temps) - max(self.temps)), 0.5*(3*max(self.temps) - min(self.temps))),
            font = dict(size=14)
        )
        fig.update_xaxes(fixedrange=True)
        fig.update_yaxes(fixedrange=True)

        return fig

    '''Return a plot of forecasted self.precipitation data'''
    def plot_precip_forecast(self):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(len(self.precip))),
            y=self.precip,
            line_shape='spline',
            fill='tozeroy',
            mode='text',
            # Display rounded temperatures above all points but the first and last
            text=[round(self.precip[i], 2) if i in range(1,len(self.precip)-1) else None for i in range(len(self.precip))],
            textfont=dict(size=14),
            textposition='top center',
            fillcolor='rgba(85,157,218,0.5)'

        ))
        fig.update_layout(
            template='plotly_white',
            yaxis_title='Precipitation (mm)',
            xaxis = dict(
                tickvals = list(range(len(self.times))),
                ticktext = self.times,
            ),
            margin = {
                't': 50,
                'b': 50
            },
            yaxis_range=(max(0, 0.5*(3*min(self.precip) - max(self.precip))), 0.5*(3*max(self.precip) - min(self.precip))),
            font = dict(size=14)
        )
        fig.update_xaxes(fixedrange=True)
        fig.update_yaxes(fixedrange=True)

        return fig

    '''Return a plot of forecasted self.humidity data'''
    def plot_humid_forecast(self):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(len(self.humid))),
            y=self.humid,
            line_shape='spline',
            fill='tozeroy',
            mode='text',
            # Display rounded temperatures above all points but the first and last
            text=[round(self.humid[i]) if i in range(1,len(self.humid)-1) else None for i in range(len(self.humid))],
            textfont=dict(size=14),
            textposition='top center',
            fillcolor='rgba(225, 204, 255, 0.5)'
        ))
        fig.update_layout(
            template='plotly_white',
            yaxis_title='Humidity %',
            xaxis = dict(
                tickvals = list(range(len(self.times))),
                ticktext = self.times,
            ),
            margin = {
                't': 50,
                'b': 50
            },
            yaxis_range=(max(0, 0.5*(3*min(self.humid) - max(self.humid))), 0.5*(3*max(self.humid) - min(self.humid))),
            font = dict(size=14)
        )
        fig.update_xaxes(fixedrange=True)
        fig.update_yaxes(fixedrange=True)

        return fig