import base64
import io
import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.graph_objects as go

# 初始化 Dash 应用
app = dash.Dash(__name__, title="Proffast Data Visualizer")

# 数据解析工具函数
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        # 假设用户上传的是 UTF-8 编码的 CSV
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        return df
    except Exception as e:
        print(f"Error parsing {filename}: {e}")
        return None

# 定义应用布局
app.layout = html.Div(className='grid-container', children=[
    
    # 0. 数据存储组件 (不可见)
    dcc.Store(id='stored-data'),

    # 1. 左上角：上传组件区域
    html.Div(id='upload-data-container', className='layout-box', children=[
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select CSV File')
            ]),
            style={
                'width': '100%',
                'height': '100%',
                'lineHeight': '40px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'cursor': 'pointer'
            },
            # 允许上传单个文件
            multiple=False
        )
    ]),

    # 2. 中央上方：坐标轴控制区域
    html.Div(id='axis-controls', className='layout-box', children=[
        html.Div([
            html.Label("Min X: "),
            dcc.Input(id='input-min-x', type='number', placeholder='Auto', className='control-input')
        ]),
        html.Div([
            html.Label("Max X: "),
            dcc.Input(id='input-max-x', type='number', placeholder='Auto', className='control-input')
        ]),
        html.Div([
            html.Label("Min Y: "),
            dcc.Input(id='input-min-y', type='number', placeholder='Auto', className='control-input')
        ]),
        html.Div([
            html.Label("Max Y: "),
            dcc.Input(id='input-max-y', type='number', placeholder='Auto', className='control-input')
        ]),
    ]),

    # 3. 右侧：元数据显示区域
    html.Div(id='meta-info-display', className='layout-box', children=[
        html.H3("File Metadata"),
        html.Hr(),
        html.Div("Waiting for file upload...", style={'color': '#888'})
    ]),

    # 4. 中央：主图表显示区域
    html.Div(id='main-graph-container', className='layout-box', children=[
        dcc.Graph(
            id='main-graph',
            style={'height': '100%', 'width': '100%'},
            figure=go.Figure(layout={'title': 'Please upload data', 'xaxis': {'visible': False}, 'yaxis': {'visible': False}})
        )
    ]),

    # 5. 中央下方：统计数据区域
    html.Div(id='stats-display', className='layout-box', children=[
        html.Div(className='stat-box', children=[
            html.Div("N/A", className='stat-value'),
            html.Div("Mean Value", className='stat-label')
        ]),
        html.Div(className='stat-box', children=[
            html.Div("N/A", className='stat-value'),
            html.Div("Std Dev", className='stat-label')
        ]),
        html.Div(className='stat-box', children=[
            html.Div("0", className='stat-value'),
            html.Div("Data Points", className='stat-label')
        ])
    ])
])

# ------------------------------------------------------------------------------
# Callbacks
# ------------------------------------------------------------------------------

@app.callback(
    [Output('stored-data', 'data'),
     Output('meta-info-display', 'children')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_data_store(contents, filename):
    if contents is None:
        # 初始状态，不更新
        return dash.no_update, dash.no_update

    df = parse_contents(contents, filename)

    if df is not None:
        # 提取元数据 (假设CSV包含 temperature, latitude, longitude 列)
        # 如果列不存在，使用 "N/A" 避免报错
        try:
            temp = df['temperature'].iloc[0] if 'temperature' in df.columns else "N/A"
            lat = df['latitude'].iloc[0] if 'latitude' in df.columns else "N/A"
            lon = df['longitude'].iloc[0] if 'longitude' in df.columns else "N/A"
            rows = len(df)
        except Exception as e:
            return None, html.Div(f"Error reading metadata: {e}", style={'color': 'red'})

        # 构建右侧元数据面板的 HTML
        meta_html = html.Div([
            html.H3("File Metadata"),
            html.Hr(),
            html.P([html.Strong("Filename: "), filename]),
            html.P([html.Strong("Temp: "), str(temp)]),
            html.P([html.Strong("Lat: "), str(lat)]),
            html.P([html.Strong("Lon: "), str(lon)]),
            html.P([html.Strong("Rows: "), str(rows)], style={'color': '#666', 'fontSize': '0.9em'})
        ])

        # 将 DataFrame 转换为字典列表存储 (records format)
        return df.to_dict('records'), meta_html
    else:
        return None, html.Div("Error parsing file format.", style={'color': 'red'})


if __name__ == '__main__':
    # 按照指示使用 app.run() 替代 app.run_server()
    app.run(debug=True, port=8050)