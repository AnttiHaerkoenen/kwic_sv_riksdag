import os
from functools import lru_cache

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Output, Input
from dash.exceptions import PreventUpdate
import pandas as pd
from sqlalchemy import create_engine


VERSION = 2020.2
PAGE_SIZE = 10
DATA_DIR = 'https://raw.githubusercontent.com/AnttiHaerkoenen/' \
           'grand_duchy/master/data/processed/frequencies_sv_riksdag/'

DATABASE_URL = os.environ.get('database_url')

if DATABASE_URL:
    sql_engine = create_engine(DATABASE_URL)
else:
    sql_engine = None

freq_data_rel = pd.read_csv(DATA_DIR + 'all_rel.csv')
freg_data_abs = pd.read_csv(DATA_DIR + 'all_abs.csv')

keywords = sorted(set(freq_data_rel.columns) - {'year', 'Unnamed: 0'})


@lru_cache(maxsize=32)
def query_kwics(
        keyword,
        years,
):
    sql_query = f"SELECT * FROM kwic_sv_riksdag WHERE term = '{keyword}'"

    if len(years) == 1:
        sql_query += f" AND year = {years[0]}"
    elif len(years) > 1:
        sql_query += f" AND year IN {years}"

    df = pd.read_sql(
        sql_query,
        con=sql_engine,
    )

    return df


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__)
app.title = "Swedish Estates"

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

    html.Div([
        html.H2(children='Keywords in context'),
        dash_table.DataTable(
            id='kwic-table',
            columns=[
                {
                    'name': col.capitalize(),
                    'id': col,
                    'type': 'text',
                    'presentation': 'markdown',
                }
                for col
                in ['file', 'year', 'context']
            ],
            style_cell_conditional=[
                {'if': {'column_id': 'file'}, 'width': '20%'},
                {'if': {'column_id': 'year'}, 'width': '10%'},
                {'if': {'column_id': 'context'}, },
            ],
            page_size=PAGE_SIZE,
            style_data={
                'whiteSpace': 'normal',
                'height': 'auto',
                'text-align': 'left',
            },
            style_header={
                'text-align': 'left',
            },
            export_format='xlsx',
            row_deletable=True,
            sort_action='native',
            filter_action='native',
        ),
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
    [
        Input('keyword-picker', 'value'),
        Input('abs-picker', 'value'),
     ]
)
def update_graph(
        keyword,
        abs_or_rel,
):
    if abs_or_rel == 'absolute':
        data = freg_data_abs
    else:
        data = freq_data_rel

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


@app.callback(
    Output('kwic-table', 'data'),
    [Input('keyword-picker', 'value'),
     Input('bar-plot', 'selectedData')]
)
def update_table(
        keyword,
        selection,
):
    if not keyword or not sql_engine:
        raise PreventUpdate

    if selection is None:
        points = []
    else:
        points = selection.get('points', [])

    years = tuple(point['x'] for point in points)

    data = query_kwics(
        keyword=keyword,
        years=years,
    )

    return data.to_dict('records')


if __name__ == '__main__':
    app.run_server(
        port=8080,
        host='0.0.0.0',
        debug=False,
    )
