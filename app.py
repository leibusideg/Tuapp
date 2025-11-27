import dash
from dash import dcc, html
import plotly.graph_objects as go

# 初始化 Dash 应用
app = dash.Dash(__name__, title="Proffast Data Visualizer")

# 定义应用布局
app.layout = html.Div(className='grid-container', children=[
    
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
            },
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
            # 初始空图表占位
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

if __name__ == '__main__':
    # 开发模式运行
    app.run_server(debug=True, port=8050)