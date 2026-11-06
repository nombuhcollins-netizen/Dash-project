import base64
import io
import pandas as pd
import dash
from dash import html, dcc, dash_table, Input, Output, State

app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True
app.title = "SmartDash"

app.layout = html.Div([
    html.H1("SmartDash - No Code Data Analyst", style ={"textAlign": 'center', "fontWeight": "bold"}),
    html.P("Start by Uploading your dataset (CSV / Excel) file", style={"textAlign": "center", "fontFamily": "Helvetical"}),
    html.P("STATUS: Waiting for file...", id= "status-text", style={"textalign": 'center', "fontWeight": "bold"}),
    dcc.Upload(
        id = 'upload-data',
        children=html.Div(['Drag and Drop or ', html.A('Select File')]),
        style ={
            'width': '80%', 'height': '80px', 'lineHeight': '80px',
            'dorderWidth': '2px', 'borderStyle': 'dashed',
            'borderRadius': '10px', 'textAlign': 'center', 'margin': 'auto'
        },
        multiple=False
    ),
    html.Br(),
    html.Div([
        html.Button("Remove Missing Values", id= "btn-missing", n_clicks=0),
        html.Button("Remove Duplicates", id= "btn-duplicates", n_clicks=0),
        html.Button("Reset", id="btn-reset", n_clicks=0),
    ], style={
        "textAlign": "center"
    }),
    html.Br(),
    html.Div(id="output-info"),
    html.Div(id='output-table'),
    dcc.Store(id='stored-data'),
    dcc.Store(id='original-data')
], style = {"fontFamily": "Arial", "padding": "20px"})

@app.callback(
    [Output('output-info', 'children'),
     Output('output-table', 'children'),
     Output('status-text', 'children'),
     Output('stored-data', 'data'),
     Output('original-data', 'data')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)

def update_output(contents, filename):
    print("CALLBACK FIRED", filename)
    print("content lenght:", len(contents) if contents else 0)

    if contents is None:
        return "No file selected", "", "", "STATUS: No file }"

    try: 
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        if 'csv' in filename.lower():
            df = pd.read_csv(io.BytesIO(decoded))
        else:
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print("ERROR READING FILE:", e)
        return f"Error reading file: {e}", "", "STATUS: Error!"

    print("FILE OK - Rows:", len(df))

    cols_df = pd.DataFrame({
        "Column Name": df.columns,
        "Data Type": [str(t) for t in df.dtypes],
        "Missing Values": df.isnull().sum().values,
    })
    info = html.Div([
        html.H3(f"File: {filename}"),
        html.P(f"Rows: {len(df)} | Columns: {len(df.columns)} | Missing Values: {int(df.isnull().sum().sum())} | Duplicates: {df.duplicated().sum()}"),
        html.H3("Columns Info:"),
        dash_table.DataTable(
            data = cols_df.to_dict('records'),
            columns = [{"name": i, "id": i} for i in cols_df.columns]
        ),
        html.H4("Preview - First 10 Rows :"),

    ])

    table = dash_table.DataTable(
        data = df.head(10).to_dict('records'),
        columns =[{"name": i, "id": i} for i in df.columns],
        page_size =10,
        style_table = {'overflowX': 'auto'},
        style_cell = {'textalign': 'left', 'padding': '8px'},
        style_header = {'backgroundColor': '#007bff', 'color': 'white', 'fontweight': 'bold'}
    )
    data = df.to_json(date_format='iso', orient ='split')
    return info, table, f"STATUS: Loaded {filename} - SUCCESS!", data, data


@app.callback(
    [Output('output-info', 'children', allow_duplicate=True),
     Output('output-table', 'children', allow_duplicate=True),
     Output('stored-data', 'data', allow_duplicate=True)],
    [Input('btn-missing', 'n_clicks'),
     Input('btn-duplicates', 'n_clicks'),
     Input('btn-reset', 'n_clicks')],
    [State('stored-data', 'data'), State('original-data', 'data')],
    prevent_initial_call=True


    )

def clean_data(n_missing, n_dup, n_reset, stored, original):
    ctx = dash.callback_context
    if not ctx.triggered or stored is None:
        return "", "", stored

    button_id = ctx.triggered[0]['prop_id'].split(',')[0]
    df =pd.read_json(io.StringIO(stored), orient='split')
    original_df = pd.read_json(io.StringIO(original), orient='split')
    msg = ""
    if button_id == "btn_missing":
        before = len(df)
        df = pd.dropna()
        msg = f"Removed {before - len(df)} rows with missing values"
    elif button_id == "btn_duplicates" :
        before  =len(df)
        df = df.duplicaties()
        msg = f"Removed {before - len(df)} duplicate rows"
    elif button_id == "btn-reset":
        df = original_df
        msg = f"Reset to original file"
    info = html.Div([
        html.H3(f"Rows: {len(df)} | Columns: {len(df.columns)} | Missing: {int(df.isnull().sum().sum())}"),
        html.P(msg, style={"color":"green", "fontWieght": "bold"}),
    ])

    table = dash_table.DataTable(data= df.head(10).to_dict('records'), columns =[{"name": i, 'id': i} for i in df.columns])

    return info, table, df.to_json(date_format ='iso', orient ='split')


if __name__== '__main__': app.run(debug=True, port=8050)
