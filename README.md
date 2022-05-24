# weather-widget
A basic weather widget built using the Dash application framework.

## Description
This widget displays current weather data and alerts for the user's current location. All data is updated every minute or upon reloading the page, allowing for a continuous live-stream of weather data.

Features included:
- 21-hour hourly forecast of weather data
- 7-day daily forecast
- Local precipitation map
- Local emergency alerts
- Live updates on a minutely basis

## Website
The fully deployed application is available [here](http://18.222.202.114/).

## Sources
- All weather data, alerts, and icons are provided by [OpenWeatherMap](https://openweathermap.org/).
- Location data provided by [ipinfo.io](https://ipinfo.io/).
- Containerization performed using [Docker](https://www.docker.com/).
- Deployed from an [AWS](https://aws.amazon.com/) EC2 instance.
- Stylesheet modified from chriddyp's [Dash stylesheet](https://codepen.io/chriddyp/pen/bWLwgP.css).

## Notes
- Location data may not be accurate when using a mobile network, as there is not necessarily any correlation between mobile IP addresses and a user's physical location.
