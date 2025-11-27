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

        return df, meta
        
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
            children=html.Div([
                html.Div("📂", style={'fontSize': '40px', 'marginBottom': '10px'}),
                html.Div(['Drag and Drop or ', html.A('Select CSV File', style={'fontWeight': 'bold'})])
            ]),
            style={
                'width': '100%', 'height': '100%', 
                'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'center', 'alignItems': 'center',
                'cursor': 'pointer'
            },
            multiple=False
        )
    ]),

    # 2. 中央上方：轴控制区域
    html.Div(id='axis-controls', className='layout-box', children=[
        
        # 左侧：X轴配置
        html.Div(className='control-column', children=[
            html.H4("X Axis Configuration"),
            dcc.Dropdown(id='xaxis-selector', placeholder='Select X Axis', style={'fontSize': '0.9em'}),
            html.Div(className='range-inputs-row', children=[
                html.Div(className='input-wrapper', children=[
                    html.Label("Min Range", className='input-label'),
                    dcc.Input(id='input-min-x', type='text', placeholder='Auto', debounce=True, className='control-input')
                ]),
                html.Div(className='input-wrapper', children=[
                    html.Label("Max Range", className='input-label'),
                    dcc.Input(id='input-max-x', type='text', placeholder='Auto', debounce=True, className='control-input')
                ])
            ])
        ]),

        # 右侧：Y轴配置
        html.Div(className='control-column', children=[
            html.H4("Y Axis Configuration"),
            dcc.Dropdown(id='yaxis-selector', placeholder='Select Y Axis', style={'fontSize': '0.9em'}),
            html.Div(className='range-inputs-row', children=[
                html.Div(className='input-wrapper', children=[
                    html.Label("Min Range", className='input-label'),
                    dcc.Input(id='input-min-y', type='number', placeholder='Auto', debounce=True, className='control-input')
                ]),
                html.Div(className='input-wrapper', children=[
                    html.Label("Max Range", className='input-label'),
                    dcc.Input(id='input-max-y', type='number', placeholder='Auto', debounce=True, className='control-input')
                ])
            ])
        ])
    ]),

    # 3. 右侧：元数据显示区域
    html.Div(id='meta-info-display', className='layout-box', children=[
        html.H3("File Metadata"),
        html.Hr(style={'borderTop': '1px solid #b3e5fc'}),
        html.Div("Waiting for file upload...", style={'color': '#546e7a', 'fontStyle': 'italic'})
    ]),

    # 4. [修改] 主要内容区域 (合并图表和统计)
    html.Div(id='main-content-container', className='layout-box', children=[
        
        # 图表区域
        dcc.Loading(
            id="loading-graph",
            type="circle",
            color="#3498db",
            children=[
                dcc.Graph(
                    id='main-graph',
                    style={'height': '60vh', 'minHeight': '400px', 'width': '100%'}, # 使用 minHeight 确保显示
                    config={'scrollZoom': True, 'displayModeBar': True, 'displaylogo': False},
                    figure=go.Figure(layout={'title': 'Please upload data', 'xaxis': {'visible': False}, 'yaxis': {'visible': False}})
                )
            ]
        ),
        
        # 统计区域
        html.Div(id='stats-display', className='stats-container', children=[
            html.Div(className='stat-box', children=[html.Div("-", className='stat-value'), html.Div("Count", className='stat-label')]),
            html.Div(className='stat-box', children=[html.Div("-", className='stat-value'), html.Div("Mean", className='stat-label')]),
            html.Div(className='stat-box', children=[html.Div("-", className='stat-value'), html.Div("Std Dev", className='stat-label')]),
            html.Div(className='stat-box', children=[html.Div("-", className='stat-value'), html.Div("Min", className='stat-label')]),
            html.Div(className='stat-box', children=[html.Div("-", className='stat-value'), html.Div("Max", className='stat-label')])
        ])
    ]),
])

# ------------------------------------------------------------------------------
# Callbacks
# ------------------------------------------------------------------------------

# 1. 上传回调 (保持不变)
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
        meta_display = html.Div([
            html.H3("File Metadata"),
            html.Hr(style={'borderTop': '1px solid #b3e5fc'}),
            html.P([html.Strong("Filename: "), html.Br(), filename], style={'marginBottom': '10px'}),
            html.P([html.Strong("Temp (gndT): "), html.Br(), f"{meta.get('temp', 'N/A')} K"], style={'marginBottom': '10px'}),
            html.P([html.Strong("Location: "), html.Br(), f"{meta.get('lat', 'N/A')}, {meta.get('lon', 'N/A')}"], style={'marginBottom': '10px'}),
        ])
        
        columns = df.columns.tolist()
        options = [{'label': col, 'value': col} for col in columns]
        x_options = [{'label': 'Data Point Index', 'value': 'index'}] + options
        
        default_x = 'index'
        if 'LocalTime' in columns:
            default_x = 'LocalTime'
        elif 'time' in columns:
            default_x = 'time'
            
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


# 2. Auto-Range 回调 (保持不变)
@app.callback(
    [Output('input-min-x', 'value'),
     Output('input-max-x', 'value'),
     Output('input-min-y', 'value'),
     Output('input-max-y', 'value')],
    [Input('stored-data', 'data'),
     Input('xaxis-selector', 'value'),
     Input('yaxis-selector', 'value')]
)
def auto_update_input_ranges(data, x_col, y_col):
    if data is None or x_col is None or y_col is None:
        return None, None, None, None

    df = pd.DataFrame(data)
    
    if x_col == 'index':
        x_vals = df.index
    else:
        x_vals = df[x_col]
        try:
            x_vals = pd.to_datetime(x_vals)
        except:
            pass

    y_vals = pd.to_numeric(df[y_col], errors='coerce').dropna()

    if len(x_vals) == 0 or len(y_vals) == 0:
        return None, None, None, None

    x_min, x_max = x_vals.min(), x_vals.max()
    y_min, y_max = y_vals.min(), y_vals.max()

    y_range = y_max - y_min
    y_padding = y_range * 0.05 if y_range != 0 else 1.0
    
    y_min_pad = y_min - y_padding
    y_max_pad = y_max + y_padding

    return x_min, x_max, y_min_pad, y_max_pad


# 3. [修改] 绘图与统计回调
@app.callback(
    [Output('main-graph', 'figure'),
     Output('stats-display', 'children')],
    [Input('input-min-x', 'value'),
     Input('input-max-x', 'value'),
     Input('input-min-y', 'value'),
     Input('input-max-y', 'value'),
     Input('stored-data', 'data'),
     Input('xaxis-selector', 'value'),
     Input('yaxis-selector', 'value')]
)
def update_graph_renderer(xmin, xmax, ymin, ymax, data, x_col, y_col):
    if data is None:
        return go.Figure(layout={'title': 'No Data Loaded', 'xaxis': {'visible': False}, 'yaxis': {'visible': False}}), dash.no_update
    
    if x_col is None or y_col is None:
        return dash.no_update, dash.no_update

    df = pd.DataFrame(data)

    try:
        # 1. 提取与预处理
        if x_col == 'index':
            x_raw = df.index
            x_label = "Index"
        else:
            x_raw = df[x_col]
            x_label = x_col
            if 'Time' in x_col or 'Date' in x_col:
                try:
                    x_raw = pd.to_datetime(x_raw)
                except:
                    pass

        y_raw = df[y_col]
        
        # 2. 构造临时 DataFrame 用于排序 (解决折线图杂乱问题)
        temp_df = pd.DataFrame({'x': x_raw, 'y': y_raw})
        # 过滤 Y 轴非数值点
        temp_df['y'] = pd.to_numeric(temp_df['y'], errors='coerce')
        temp_df = temp_df.dropna(subset=['y'])
        
        # 排序
        temp_df = temp_df.sort_values(by='x')
        
        x_data = temp_df['x']
        y_data = temp_df['y']
        
    except KeyError:
        return go.Figure(layout={'title': 'Column not found'}), dash.no_update

    # 3. 统计计算
    try:
        stats = {
            'count': len(y_data),
            'mean': y_data.mean(),
            'std': y_data.std(),
            'min': y_data.min(),
            'max': y_data.max()
        }
    except Exception:
        stats = {'count': 0, 'mean': 0, 'std': 0, 'min': 0, 'max': 0}

    # 4. 构建图表
    fig = go.Figure()
    
    # [修改] Mode 改为 lines+markers
    fig.add_trace(go.Scatter(
        x=x_data,
        y=y_data,
        mode='lines+markers', 
        name=y_col,
        line=dict(width=2, color='#2980b9'),
        marker=dict(size=5, color='#3498db', opacity=0.8)
    ))

    if not pd.isna(stats['mean']):
        fig.add_hline(
            y=stats['mean'], 
            line_dash="dash", 
            line_color="#e74c3c", 
            annotation_text=f"Mean: {stats['mean']:.2f}", 
            annotation_position="bottom right"
        )

    fig.update_layout(
        title=dict(text=f"{y_col} vs {x_label}", x=0.05),
        xaxis_title=x_label,
        yaxis_title=y_col,
        hovermode='closest',
        plot_bgcolor='white',
        margin=dict(l=60, r=40, t=60, b=60),
        xaxis_range=[xmin, xmax] if (xmin is not None and xmax is not None) else None,
        yaxis_range=[ymin, ymax] if (ymin is not None and ymax is not None) else None,
        xaxis=dict(showgrid=True, gridcolor='#f0f0f0', zeroline=True, zerolinecolor='#dcdcdc'),
        yaxis=dict(showgrid=True, gridcolor='#f0f0f0', zeroline=True, zerolinecolor='#dcdcdc')
    )

    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=False)

    # 5. 生成统计 HTML
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