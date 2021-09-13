from forecast_manager import ForecastManager

import pandas as pd

def get_constants():
    
    STATES_DF = pd.read_csv('https://raw.githubusercontent.com/jasonong/List-of-US-States/master/states.csv')

    DAYTON = {'city': 'Dayton', 'region': 'Ohio', 'country': 'US', 'timezone': 'America/New_York', 'loc':'39.7589,-84.1916'}

    with open('./api_keys/owm_key.txt', 'r') as f:
        API_KEY = f.read()

    MGR = ForecastManager(DAYTON, API_KEY)

    return STATES_DF, DAYTON, API_KEY, MGR