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
    """
    解析上传的文件内容，返回 DataFrame 字典列表和元数据字典。
    """
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        # 1. 读取 CSV，处理分隔符后的空格 (skipinitialspace=True)
        # 假设文件编码为 utf-8
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), skipinitialspace=True)
        
        # 2. 清洗列名：去除前后空格
        df.columns = df.columns.str.strip()
        
        # 3. 提取元数据 (取第一行数据)
        # 目标列: gndT (温度), latdeg (纬度), londeg (经度)
        meta = {}
        if not df.empty:
            meta['temp'] = df['gndT'].iloc[0] if 'gndT' in df.columns else "N/A"
            meta['lat'] = df['latdeg'].iloc[0] if 'latdeg' in df.columns else "N/A"
            meta['lon'] = df['londeg'].iloc[0] if 'londeg' in df.columns else "N/A"
        else:
            meta = {'temp': 'N/A', 'lat': 'N/A', 'lon': 'N/A'}

        # 4. 准备绘图数据 (标准化列名 x_plot, y_plot)
        # X轴优先: LocalTime
        x_col = 'LocalTime'
        if x_col not in df.columns:
            # 如果找不到 LocalTime，尝试使用第一列
            x_col = df.columns[0] if len(df.columns) > 0 else None

        # Y轴优先: XCO2 -> XCH4 -> 第6列 (spectrum 后的数据) -> 第2列
        y_col = None
        if 'XCO2' in df.columns:
            y_col = 'XCO2'
        elif 'XCH4' in df.columns:
            y_col = 'XCH4'
        elif len(df.columns) > 5:
            y_col = df.columns[5] # 假设索引5是某个数值列
        elif len(df.columns) > 1:
            y_col = df.columns[1]

        # 如果找到对应的列，创建标准化的绘图列，方便前端直接使用
        if x_col and x_col in df.columns:
            df['x_plot'] = df[x_col]
        if y_col and y_col in df.columns:
            df['y_plot'] = df[y_col]
            
        # 记录识别到的列名以便调试
        meta['x_col_name'] = x_col
        meta['y_col_name'] = y_col

        return df.to_dict('records'), meta
        
    except Exception as e:
        print(f"Error parsing {filename}: {e}")
        return None, None

# ------------------------------------------------------------------------------
# Layout
# ------------------------------------------------------------------------------
app.layout = html.Div(className='grid-container', children=[
    
    # 0. 数据存储组件 (浏览器端缓存)
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
        return dash.no_update, dash.no_update

    # 调用解析函数
    data, meta = parse_contents(contents, filename)

    if data is not None and meta is not None:
        # 构造元数据展示文本
        # 格式: 温度: {temp} K | 纬度: {lat} | 经度: {lon}
        meta_display = html.Div([
            html.H3("File Metadata"),
            html.Hr(),
            html.P([html.Strong("Filename: "), filename]),
            html.P([html.Strong("温度 (gndT): "), f"{meta.get('temp', 'N/A')} K"]),
            html.P([html.Strong("纬度 (lat): "), f"{meta.get('lat', 'N/A')}"]),
            html.P([html.Strong("经度 (lon): "), f"{meta.get('lon', 'N/A')}"]),
            html.P([html.Strong("Target Y: "), f"{meta.get('y_col_name', 'Unknown')}"], style={'fontSize': '0.8em', 'color': '#666'}),
            html.P([html.Strong("Records: "), f"{len(data)}"], style={'fontSize': '0.8em', 'color': '#666'})
        ])
        
        return data, meta_display
    else:
        # 错误处理
        error_display = html.Div([
            html.H3("Error"),
            html.Hr(),
            html.P("Failed to parse file.", style={'color': 'red'}),
            html.P("Please ensure the CSV matches Proffastpylot format.")
        ])
        return None, error_display


if __name__ == '__main__':
    app.run(debug=True, port=8050)