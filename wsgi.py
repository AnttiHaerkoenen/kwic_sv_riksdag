import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
import pandas as pd

VERSION = 2020.1
data_dir = 'https://raw.githubusercontent.com/AnttiHaerkoenen/grand_duchy/master/data/processed/'

freq_regex_data = pd.read_csv(data_dir + 'frequencies_riksdag_all.csv')
freg_regex_data_abs = pd.read_csv(data_dir + 'frequencies_riksdag_all_abs.csv')

keywords = sorted(set(freq_regex_data.columns) - {'year', 'Unnamed: 0'})

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__)
app.title = "Ståndsriksdagen (1521-1866)"

application = app.server

options = [{'label': k, 'value': k} for k in keywords]

app.layout = html.Div(children=[
    html.H1(children=f'{app.title}'),

    html.H2(children='Keyword'),

    html.Div([
        dcc.Dropdown(
            id='keyword-picker',
            options=options,
            value=options[0]['value'],
        ),
    ]),

    html.H2(children='Frequency'),
    html.Div([
        dcc.RadioItems(
            id='abs-picker',
            options=[
                {'label': i.capitalize(), 'value': i}
                for i in ['absolute', 'relative']
            ],
            value='absolute',
            labelStyle={'display': 'inline-block'}
        ),
    ]),

    html.Div([
        html.H2(children='Frequency plot'),
        dcc.Graph(id='bar-plot'),
    ]),

    html.P(
        children=f"Version {VERSION}",
        style={
            'font-style': 'italic'
        },
    ),
])


@app.callback(
    Output('bar-plot', 'figure'),
    [Input('keyword-picker', 'value'),
     Input('abs-picker', 'value'),]
)
def update_graph(
        keyword,
        abs_or_rel,
):
    if abs_or_rel == 'absolute':
        data = freg_regex_data_abs
    else:
        data = freq_regex_data

    x = data['year']
    y = data[keyword]

    return {
        'data': [{
            'x': x,
            'y': y,
            'type': 'bar',
            'name': keyword,
        }]
    }


if __name__ == '__main__':
    app.run_server(
        port=8080,
        host='0.0.0.0',
        debug=True,
    )
