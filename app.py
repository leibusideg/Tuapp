import base64
import io
import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.graph_objects as go

# 初始化 Dash 应用
app = dash.Dash(__name__, title="Proffast Data Visualizer")

# ------------------------------------------------------------------------------
# 辅助函数: 数据解析
# ------------------------------------------------------------------------------
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), skipinitialspace=True)
        df.columns = df.columns.str.strip()
        
        meta = {}
        if not df.empty:
            meta['temp'] = df['gndT'].iloc[0] if 'gndT' in df.columns else "N/A"
            meta['lat'] = df['latdeg'].iloc[0] if 'latdeg' in df.columns else "N/A"
            meta['lon'] = df['londeg'].iloc[0] if 'londeg' in df.columns else "N/A"
        else:
            meta = {'temp': 'N/A', 'lat': 'N/A', 'lon': 'N/A'}

        return df, meta  # 注意：此处改为直接返回 DataFrame 对象，便于后续处理列名
        
    except Exception as e:
        print(f"Error parsing {filename}: {e}")
        return None, None

# ------------------------------------------------------------------------------
# Layout
# ------------------------------------------------------------------------------
app.layout = html.Div(className='grid-container', children=[
    
    # 0. 数据存储组件
    dcc.Store(id='stored-data'),

    # 1. 左上角：上传组件区域
    html.Div(id='upload-data-container', className='layout-box', children=[
        dcc.Upload(
            id='upload-data',
            children=html.Div(['Drag and Drop or ', html.A('Select CSV File')]),
            style={
                'width': '100%', 'height': '100%', 'lineHeight': '40px',
                'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                'textAlign': 'center', 'cursor': 'pointer'
            },
            multiple=False
        )
    ]),

    # 2. 中央上方：轴控制区域 (包含下拉框和输入框)
    html.Div(id='axis-controls', className='layout-box', children=[
        # 第一行：下拉选择框
        html.Div(className='dropdown-row', children=[
            html.Div(className='dropdown-container', children=[
                html.Label("Select X Axis:", style={'fontWeight': 'bold', 'fontSize': '0.9em'}),
                dcc.Dropdown(id='xaxis-selector', placeholder='Select X Axis', style={'fontSize': '0.9em'})
            ]),
            html.Div(className='dropdown-container', children=[
                html.Label("Select Y Axis:", style={'fontWeight': 'bold', 'fontSize': '0.9em'}),
                dcc.Dropdown(id='yaxis-selector', placeholder='Select Y Axis', style={'fontSize': '0.9em'})
            ])
        ]),
        
        # 第二行：范围输入框
        html.Div(className='input-row', children=[
            html.Div(className='input-group', children=[
                html.Label("Min X:"),
                dcc.Input(id='input-min-x', type='number', placeholder='Auto', className='control-input')
            ]),
            html.Div(className='input-group', children=[
                html.Label("Max X:"),
                dcc.Input(id='input-max-x', type='number', placeholder='Auto', className='control-input')
            ]),
            html.Div(className='input-group', children=[
                html.Label("Min Y:"),
                dcc.Input(id='input-min-y', type='number', placeholder='Auto', className='control-input')
            ]),
            html.Div(className='input-group', children=[
                html.Label("Max Y:"),
                dcc.Input(id='input-max-y', type='number', placeholder='Auto', className='control-input')
            ]),
        ])
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
        html.Div(className='stat-box', children=[html.Div("-", className='stat-value'), html.Div("Count", className='stat-label')]),
        html.Div(className='stat-box', children=[html.Div("-", className='stat-value'), html.Div("Mean", className='stat-label')]),
        html.Div(className='stat-box', children=[html.Div("-", className='stat-value'), html.Div("Std Dev", className='stat-label')]),
        html.Div(className='stat-box', children=[html.Div("-", className='stat-value'), html.Div("Min", className='stat-label')]),
        html.Div(className='stat-box', children=[html.Div("-", className='stat-value'), html.Div("Max", className='stat-label')])
    ])
])

# ------------------------------------------------------------------------------
# Callbacks
# ------------------------------------------------------------------------------

# 1. 上传回调：解析数据，更新 Store、元数据和下拉框选项
@app.callback(
    [Output('stored-data', 'data'),
     Output('meta-info-display', 'children'),
     Output('xaxis-selector', 'options'),
     Output('xaxis-selector', 'value'),
     Output('yaxis-selector', 'options'),
     Output('yaxis-selector', 'value')],
    [Input('upload-data', 'contents')],
    [State('upload-data', 'filename')]
)
def update_data_store(contents, filename):
    if contents is None:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    df, meta = parse_contents(contents, filename)

    if df is not None and meta is not None:
        # 构造元数据展示文本
        meta_display = html.Div([
            html.H3("File Metadata"),
            html.Hr(),
            html.P([html.Strong("Filename: "), filename]),
            html.P([html.Strong("Temp (gndT): "), f"{meta.get('temp', 'N/A')} K"]),
            html.P([html.Strong("Lat: "), f"{meta.get('lat', 'N/A')}"]),
            html.P([html.Strong("Lon: "), f"{meta.get('lon', 'N/A')}"]),
        ])
        
        # 构造下拉框选项
        columns = df.columns.tolist()
        options = [{'label': col, 'value': col} for col in columns]
        
        # X轴选项：增加 Index 选项
        x_options = [{'label': 'Data Point Index', 'value': 'index'}] + options
        
        # 默认选中逻辑
        # X轴：优先 LocalTime > time > index
        default_x = 'index'
        if 'LocalTime' in columns:
            default_x = 'LocalTime'
        elif 'time' in columns:
            default_x = 'time'
            
        # Y轴：优先 XCO2 > XCH4 > 第二列
        default_y = None
        if 'XCO2' in columns:
            default_y = 'XCO2'
        elif 'XCH4' in columns:
            default_y = 'XCH4'
        elif len(columns) > 1:
            default_y = columns[1]
        
        return df.to_dict('records'), meta_display, x_options, default_x, options, default_y
    else:
        return None, html.Div("Error parsing file.", style={'color': 'red'}), [], None, [], None

# 2. 绘图与统计回调：监听数据与下拉框变化
@app.callback(
    [Output('main-graph', 'figure'),
     Output('stats-display', 'children')],
    [Input('stored-data', 'data'),
     Input('xaxis-selector', 'value'),
     Input('yaxis-selector', 'value')]
)
def update_graph_and_stats(data, x_col, y_col):
    if data is None:
        empty_fig = go.Figure(layout={'title': 'No Data Loaded', 'xaxis': {'visible': False}, 'yaxis': {'visible': False}})
        return empty_fig, dash.no_update
    
    if x_col is None or y_col is None:
        return dash.no_update, dash.no_update

    df = pd.DataFrame(data)

    # 1. 提取绘图数据
    try:
        # 获取 X 数据
        if x_col == 'index':
            x_data = df.index
            x_label = "Index"
        else:
            x_data = df[x_col]
            x_label = x_col
            # 尝试转为时间格式，如果是 LocalTime
            if 'Time' in x_col or 'Date' in x_col:
                try:
                    x_data = pd.to_datetime(x_data)
                except:
                    pass

        # 获取 Y 数据
        y_data = df[y_col]
        
        # 确保数据是数值型以便统计 (如果选了非数值列可能会报错，简单处理)
        y_data_numeric = pd.to_numeric(y_data, errors='coerce')
        
    except KeyError:
        return go.Figure(layout={'title': 'Column not found'}), dash.no_update

    # 2. 计算统计数据
    try:
        valid_y = y_data_numeric.dropna()
        stats = {
            'count': len(valid_y),
            'mean': valid_y.mean(),
            'std': valid_y.std(),
            'min': valid_y.min(),
            'max': valid_y.max()
        }
    except Exception:
        stats = {'count': 0, 'mean': 0, 'std': 0, 'min': 0, 'max': 0}

    # 3. 构建图表
    fig = go.Figure()
    
    # 散点图
    fig.add_trace(go.Scatter(
        x=x_data,
        y=y_data,
        mode='markers',
        name=y_col,
        marker=dict(size=6, color='#2980b9', opacity=0.7)
    ))

    # 均值线 (仅当均值为数字时)
    if not pd.isna(stats['mean']):
        fig.add_hline(
            y=stats['mean'], 
            line_dash="dash", 
            line_color="#e74c3c", 
            annotation_text=f"Mean: {stats['mean']:.2f}", 
            annotation_position="bottom right"
        )

    # 布局设置
    fig.update_layout(
        title=f"{y_col} vs {x_label}",
        xaxis_title=x_label,
        yaxis_title=y_col,
        hovermode='closest',
        plot_bgcolor='white',
        margin=dict(l=50, r=30, t=50, b=50),
        xaxis=dict(showgrid=True, gridcolor='#f0f0f0'),
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0')
    )

    # 4. 构建统计 HTML
    stats_html = [
        html.Div(className='stat-box', children=[
            html.Div(f"{stats['count']}", className='stat-value'),
            html.Div("Count", className='stat-label')
        ]),
        html.Div(className='stat-box', children=[
            html.Div(f"{stats['mean']:.2f}", className='stat-value'),
            html.Div("Mean", className='stat-label')
        ]),
        html.Div(className='stat-box', children=[
            html.Div(f"{stats['std']:.3f}", className='stat-value'),
            html.Div("Std Dev", className='stat-label')
        ]),
        html.Div(className='stat-box', children=[
            html.Div(f"{stats['min']:.2f}", className='stat-value'),
            html.Div("Min", className='stat-label')
        ]),
        html.Div(className='stat-box', children=[
            html.Div(f"{stats['max']:.2f}", className='stat-value'),
            html.Div("Max", className='stat-label')
        ])
    ]

    return fig, stats_html

if __name__ == '__main__':
    app.run(debug=True, port=8050)