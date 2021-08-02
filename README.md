# weather-widget
A basic weather widget built using the Dash application framework.

## Description
This widget displays current temperature, precipitation, humidity, and wind data for the Dayton, OH area. A (nearly) 24-hour forecast of temperature data is provided, along with a week-long daily forecast. All data is updated every five minutes or upon reloading the page, allowing for a continuous live-stream of weather data.

## Website
The fully deployed application is available [here](http://18.222.202.114:8050/).

## Sources
- All weather data and weather icons are provided by [OpenWeatherMap](https://openweathermap.org/).
- Containerization performed using [Docker](https://www.docker.com/).
- Deployed from an [AWS](https://aws.amazon.com/) instance.
- Location data provided by [https://ipinfo.io/](ipinfo.io).

## Notes
- Location data will not be accurate when using a mobile network, as there is no correlation between mobile IP addresses and physical location.