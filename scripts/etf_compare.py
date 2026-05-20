"""
ETF与上证指数对比图生成脚本
用法: python scripts/etf_compare.py [ETF代码] [天数]
示例: python scripts/etf_compare.py 510300 500
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import urllib.request
import json
from datetime import datetime
from collections import OrderedDict

from src.etf.database import get_connection, init_db
from src.etf.fetcher import fetch_etf_data, get_trading_days


def get_etf_from_db(etf_code, days=500):
    """从数据库获取ETF历史数据"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT stat_date, tot_vol, sec_name
        FROM etf_daily_share e
        LEFT JOIN etf_info i ON e.sec_code = i.sec_code
        WHERE e.sec_code = ? AND e.stat_date >= date('now', '-' || ? || ' days')
        ORDER BY e.stat_date
    ''', (etf_code, days))
    results = cursor.fetchall()
    conn.close()

    trend_data = OrderedDict()
    sec_name = etf_code
    for row in results:
        date, vol, name = row
        trend_data[date] = vol
        if name:
            sec_name = name
    return sec_name, trend_data


def fetch_index_data(code='sh000001', days=500):
    """获取上证指数历史数据"""
    print(f"Fetching index data from web...")
    url = f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?_var=kline_dayqfq&param={code},day,,,{days},qfq'
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            text = response.read().decode('utf-8')
            json_str = text[text.index('=') + 1:]
            data = json.loads(json_str)
            index_data = data.get('data', {}).get(code, {}).get('day', [])
            print(f"Got {len(index_data)} days index data")
            return index_data
    except Exception as e:
        print(f"Error fetching index: {e}")
        return []


def generate_html(etf_code, etf_name, etf_data, index_data, output_path):
    """生成对比图"""
    import json

    if not etf_data:
        print("No ETF data")
        return None

    etf_dates = list(etf_data.keys())
    etf_values = list(etf_data.values())

    index_dates = []
    index_closes = []
    for item in index_data:
        if len(item) >= 2:
            index_dates.append(item[0])
            index_closes.append(float(item[1]))

    common_dates = sorted(set(etf_dates) & set(index_dates))
    print(f"Common trading days: {len(common_dates)}")

    etf_values_common = [etf_data[d] for d in common_dates]
    index_values_common = [index_closes[i] for i, d in enumerate(index_dates) if d in common_dates]

    # 计算累计涨跌幅（ETF用百分比）
    etf_pct = []
    for i, v in enumerate(etf_values_common):
        if i == 0:
            etf_pct.append(0)
        else:
            pct = (v - etf_values_common[i-1]) / etf_values_common[i-1] * 100
            etf_pct.append(round(pct, 2))

    etf_cum = []
    for i in range(len(common_dates)):
        if i == 0:
            etf_cum.append(0)
        else:
            etf_cum.append(round(sum(etf_pct[:i+1]), 2))

    # 整体统计
    etf_total_change = round((etf_values_common[-1] - etf_values_common[0]) / etf_values_common[0] * 100, 2)
    index_total_change = round((index_values_common[-1] - index_values_common[0]) / index_values_common[0] * 100, 2)

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{etf_name}({etf_code}) vs 上证指数</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, sans-serif; background: linear-gradient(135deg, #1a1a2e, #16213e); min-height: 100vh; padding: 20px; color: #fff; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 24px; }}
        .header h1 {{ font-size: 24px; background: linear-gradient(90deg, #00d4ff, #7b2cbf); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }}
        .box {{ background: rgba(255,255,255,0.1); border-radius: 12px; padding: 16px; text-align: center; }}
        .box h3 {{ font-size: 12px; color: #888; margin-bottom: 8px; text-transform: uppercase; }}
        .box .value {{ font-size: 28px; font-weight: 600; }}
        .box .sub {{ font-size: 12px; color: #666; margin-top: 4px; }}
        .up {{ color: #00d4ff; }}
        .down {{ color: #ff4757; }}
        .chart {{ background: rgba(255,255,255,0.05); border-radius: 16px; padding: 16px; margin-bottom: 16px; }}
        .chart h3 {{ margin-bottom: 12px; color: #888; font-size: 12px; text-transform: uppercase; }}
        #c1, #c2 {{ width: 100%; height: 300px; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header"><h1>{etf_name} ({etf_code}) vs 上证指数 对比</h1></div>

        <div class="stats">
            <div class="box">
                <h3>{etf_name} 最新份额</h3>
                <div class="value">{etf_values_common[-1]/10000:.2f}<span style="font-size:14px"> 亿</span></div>
                <div class="sub">{common_dates[-1]}</div>
            </div>
            <div class="box">
                <h3>{etf_name} 累计涨跌</h3>
                <div class="value {'up' if etf_total_change >= 0 else 'down'}">{etf_total_change:+.2f}%</div>
                <div class="sub">{common_dates[0]} ~ {common_dates[-1]}</div>
            </div>
            <div class="box">
                <h3>上证指数 点位</h3>
                <div class="value">{index_values_common[-1]:.2f}</div>
                <div class="sub">{common_dates[-1]}</div>
            </div>
            <div class="box">
                <h3>上证指数 累计涨跌</h3>
                <div class="value {'up' if index_total_change >= 0 else 'down'}">{index_total_change:+.2f}%</div>
                <div class="sub">同期对比</div>
            </div>
        </div>

        <div class="chart">
            <h3>累计涨跌幅对比</h3>
            <div id="c1"></div>
        </div>

        <div class="chart">
            <h3>{etf_name} 份额趋势</h3>
            <div id="c2"></div>
        </div>

        <div class="footer">数据来源: SSE + 腾讯财经 | {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
    </div>
    <script>
        var c1 = echarts.init(document.getElementById('c1'));
        var c2 = echarts.init(document.getElementById('c2'));
        var dates = {json.dumps(common_dates)};
        var etfCum = {json.dumps(etf_cum)};
        var idxV = {json.dumps(index_values_common)};
        var etfVol = {json.dumps(etf_values_common)};

        c1.setOption({{
            backgroundColor: 'transparent',
            tooltip: {{ trigger: 'axis', formatter: function(p) {{ return p[0].name + '<br/>' + p.map(x => x.seriesName + ': ' + (x.seriesName == '{etf_name}' ? x.value + '%' : x.value)).join('<br/>'); }} }},
            legend: {{ data: ['{etf_name}', '上证指数'], textStyle: {{ color: '#888' }} }},
            grid: {{ left: '3%', right: '4%', bottom: '15%', top: '10%' }},
            xAxis: {{ type: 'category', data: dates, axisLabel: {{ color: '#666', formatter: v => v.slice(5) }} }},
            yAxis: [
                {{ type: 'value', name: 'ETF涨跌%', axisLabel: {{ color: '#666', formatter: v => v + '%' }}, splitLine: {{ show: false }} }},
                {{ type: 'value', name: '上证指数', min: 3600, axisLabel: {{ color: '#666', formatter: v => v }}}}
            ],
            dataZoom: [{{ type: 'inside' }}, {{ type: 'slider', height: 20, borderColor: 'rgba(255,255,255,0.1)', backgroundColor: 'rgba(0,0,0,0.2)' }}],
            series: [
                {{ name: '{etf_name}', type: 'line', yAxisIndex: 0, data: etfCum, smooth: true, symbol: 'none', itemStyle: {{ color: '#00d4ff' }}, areaStyle: {{ color: 'rgba(0,212,255,0.1)' }} }},
                {{ name: '上证指数', type: 'line', yAxisIndex: 1, data: idxV, smooth: true, symbol: 'none', itemStyle: {{ color: '#ff6b6b' }} }}
            ]
        }});

        c2.setOption({{
            backgroundColor: 'transparent',
            tooltip: {{ trigger: 'axis', formatter: function(p) {{ return p[0].name + '<br/>' + p[0].seriesName + ': ' + (p[0].value/10000).toFixed(2) + ' 亿'; }} }},
            grid: {{ left: '3%', right: '4%', bottom: '15%', top: '10%' }},
            xAxis: {{ type: 'category', data: dates, axisLabel: {{ color: '#666', formatter: v => v.slice(5) }} }},
            yAxis: {{ type: 'value', axisLabel: {{ color: '#666', formatter: v => (v/10000).toFixed(0) + '亿' }}, splitLine: {{ lineStyle: {{ color: 'rgba(255,255,255,0.1)' }} }} }},
            dataZoom: [{{ type: 'inside' }}, {{ type: 'slider', height: 20, borderColor: 'rgba(255,255,255,0.1)', backgroundColor: 'rgba(0,0,0,0.2)' }}],
            series: [{{
                name: '{etf_name}', type: 'line', data: etfVol,
                smooth: true, symbol: 'circle', symbolSize: 3,
                itemStyle: {{ color: '#00d4ff', borderWidth: 2 }},
                areaStyle: {{ color: 'rgba(0,212,255,0.2)' }},
                markPoint: {{ data: [{{ type: 'max' }}, {{ type: 'min' }}], label: {{ formatter: function(p) {{ return (p.value/10000).toFixed(2) + '亿'; }} }} }},
                markLine: {{ data: [{{ type: 'average' }}], label: {{ formatter: function(p) {{ return (p.value/10000).toFixed(2) + '亿'; }} }} }}
            }}]
        }});

        window.addEventListener('resize', () => {{ c1.resize(); c2.resize(); }});
    </script>
</body>
</html>'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Saved: {output_path}")


if __name__ == '__main__':
    PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    etf_code = sys.argv[1] if len(sys.argv) > 1 else '510300'
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 500

    print(f"Loading {etf_code} data from database...")
    etf_name, etf_data = get_etf_from_db(etf_code, days)
    print(f"Got {len(etf_data)} days ETF data: {etf_name}")

    if not etf_data:
        print("No ETF data found. Run 'python -m src.etf.cli fetch' first.")
        exit(1)

    index_data = fetch_index_data('sh000001', days)

    if etf_data and index_data:
        output = os.path.join(PROJECT_DIR, 'data', f'etf_{etf_code}_vs_index.html')
        generate_html(etf_code, etf_name, etf_data, index_data, output)