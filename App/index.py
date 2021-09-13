from app import app
from layout import layout_function

import callbacks

app.title = 'Weather Data'
app.layout = layout_function

if __name__ == '__main__':
    # Run the server
    app.run_server(debug=False, port=80, host='0.0.0.0')