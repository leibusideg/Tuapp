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

    # 2. 中央上方：轴控制区域 (重构为左右两栏)
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

    # 4. 中央：主图表显示区域 (添加 Loading)
    html.Div(id='main-graph-container', className='layout-box', children=[
        dcc.Loading(
            id="loading-graph",
            type="circle",
            color="#3498db",
            children=[
                dcc.Graph(
                    id='main-graph',
                    style={'height': '100%', 'width': '100%'},
                    config={'scrollZoom': True, 'displayModeBar': True, 'displaylogo': False},
                    figure=go.Figure(layout={'title': 'Please upload data', 'xaxis': {'visible': False}, 'yaxis': {'visible': False}})
                )
            ]
        )
    ]),

    # 5. 中央下方：统计数据区域 (添加 Loading)
    html.Div(id='stats-display-container', className='layout-box', style={'background': 'transparent', 'border': 'none', 'boxShadow': 'none', 'padding': '0'}, children=[
        dcc.Loading(
             id="loading-stats",
             type="dot",
             color="#3498db",
             children=html.Div(id='stats-display', children=[
                html.Div(className='stat-box', children=[html.Div("-", className='stat-value'), html.Div("Count", className='stat-label')]),
                html.Div(className='stat-box', children=[html.Div("-", className='stat-value'), html.Div("Mean", className='stat-label')]),
                html.Div(className='stat-box', children=[html.Div("-", className='stat-value'), html.Div("Std Dev", className='stat-label')]),
                html.Div(className='stat-box', children=[html.Div("-", className='stat-value'), html.Div("Min", className='stat-label')]),
                html.Div(className='stat-box', children=[html.Div("-", className='stat-value'), html.Div("Max", className='stat-label')])
            ])
        )
    ])
])

# ------------------------------------------------------------------------------
# Callbacks
# ------------------------------------------------------------------------------

# 1. 上传回调
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


# 2. Auto-Range 回调
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


# 3. 绘图与统计回调
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
        if x_col == 'index':
            x_data = df.index
            x_label = "Index"
        else:
            x_data = df[x_col]
            x_label = x_col
            if 'Time' in x_col or 'Date' in x_col:
                try:
                    x_data = pd.to_datetime(x_data)
                except:
                    pass

        y_data = df[y_col]
        y_data_numeric = pd.to_numeric(y_data, errors='coerce')
        
    except KeyError:
        return go.Figure(layout={'title': 'Column not found'}), dash.no_update

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

    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=x_data,
        y=y_data,
        mode='markers',
        name=y_col,
        marker=dict(size=6, color='#2980b9', opacity=0.7)
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

    # 锁定 X 轴，开放 Y 轴缩放
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=False)

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