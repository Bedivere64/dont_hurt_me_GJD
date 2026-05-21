"""
ETF份额趋势图生成脚本 - HTML可视化版本
用法: python scripts/etf_trend.py [ETF代码] [天数]
示例: python scripts/etf_trend.py 512070 500
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from datetime import datetime
from collections import OrderedDict


def get_etf_trend(etf_code, days=500):
    """从数据库获取某ETF最近days天的份额趋势"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'etf_data.db')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute('''
        SELECT d.stat_date, d.tot_vol, i.sec_name
        FROM etf_daily_share d
        JOIN etf_info i ON d.sec_code = i.sec_code
        WHERE d.sec_code = ?
        ORDER BY d.stat_date DESC
        LIMIT ?
    ''', (etf_code, days))

    rows = cur.fetchall()
    conn.close()

    if not rows:
        return OrderedDict()

    trend_data = OrderedDict()
    for row in reversed(rows):
        trend_data[row[0]] = {
            'totVol': float(row[1]),
            'secName': row[2],
        }

    print(f"Got {len(trend_data)} days data from database")
    return trend_data


def generate_html(etf_code, trend_data, output_path):
    """生成HTML可视化图表"""
    import json

    if not trend_data:
        print("No data to generate HTML")
        return None

    dates = list(trend_data.keys())
    volumes = [trend_data[d]['totVol'] for d in dates]
    sec_name = trend_data[dates[0]]['secName'] if dates else etf_code

    max_val = max(volumes)
    min_val = min(volumes)
    avg_val = sum(volumes) / len(volumes)
    current_val = volumes[-1]
    change = ((volumes[-1] - volumes[0]) / volumes[0] * 100) if volumes[0] != 0 else 0

    max_idx = volumes.index(max_val)
    min_idx = volumes.index(min_val)

    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{sec_name}({etf_code}) 份额趋势</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 20px;
            color: #fff;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .header h1 {{
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 8px;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .stat-card {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .stat-card .label {{ font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
        .stat-card .value {{ font-size: 24px; font-weight: 600; color: #fff; }}
        .stat-card .sub {{ font-size: 12px; color: #666; margin-top: 4px; }}
        .change-up {{ color: #00d4ff; }}
        .change-down {{ color: #ff4757; }}
        .chart-container {{
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        #chart {{ width: 100%; height: 500px; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header"><h1>{sec_name} ({etf_code}) 份额趋势</h1></div>
        <div class="stats">
            <div class="stat-card"><div class="label">最新份额</div><div class="value">{current_val/10000:.2f} <span style="font-size:14px">亿</span></div><div class="sub">{dates[-1]}</div></div>
            <div class="stat-card"><div class="label">期间涨跌幅</div><div class="value {"change-up" if change >= 0 else "change-down"}">{change:+.2f}%</div><div class="sub">{dates[0]} ~ {dates[-1]}</div></div>
            <div class="stat-card"><div class="label">最高份额</div><div class="value">{max_val/10000:.2f} <span style="font-size:14px">亿</span></div><div class="sub">{dates[max_idx]}</div></div>
            <div class="stat-card"><div class="label">最低份额</div><div class="value">{min_val/10000:.2f} <span style="font-size:14px">亿</span></div><div class="sub">{dates[min_idx]}</div></div>
            <div class="stat-card"><div class="label">平均份额</div><div class="value">{avg_val/10000:.2f} <span style="font-size:14px">亿</span></div><div class="sub">日均</div></div>
            <div class="stat-card"><div class="label">数据天数</div><div class="value">{len(dates)}</div><div class="sub">交易日</div></div>
        </div>
        <div class="chart-container"><div id="chart"></div></div>
        <div class="footer">数据来源: 上海证券交易所 (SSE) | 更新于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>
    <script>
        var chart = echarts.init(document.getElementById('chart'));
        var option = {{
            backgroundColor: 'transparent',
            tooltip: {{ trigger: 'axis', backgroundColor: 'rgba(50, 50, 50, 0.9)', borderColor: 'rgba(255, 255, 255, 0.1)', textStyle: {{ color: '#fff' }}, formatter: function(params) {{ var data = params[0]; return data.name + '<br/>份额: ' + (data.value / 10000).toFixed(2) + ' 亿'; }} }},
            grid: {{ left: '3%', right: '4%', bottom: '10%', top: '10%', containLabel: true }},
            xAxis: {{ type: 'category', boundaryGap: false, data: {json.dumps(dates)}, axisLine: {{ lineStyle: {{ color: 'rgba(255,255,255,0.2)' }} }}, axisLabel: {{ color: 'rgba(255,255,255,0.6)', formatter: function(value) {{ return value.substring(5); }} }}, splitLine: {{ show: false }} }},
            yAxis: {{ type: 'value', axisLine: {{ show: false }}, axisLabel: {{ color: 'rgba(255,255,255,0.6)', formatter: function(value) {{ return (value / 10000).toFixed(0) + '亿'; }} }}, splitLine: {{ lineStyle: {{ color: 'rgba(255,255,255,0.1)' }} }}, scale: true }},
            dataZoom: [{{ type: 'inside', start: 0, end: 100 }}, {{ type: 'slider', start: 0, end: 100, height: 20, bottom: 0, borderColor: 'rgba(255,255,255,0.1)', backgroundColor: 'rgba(0,0,0,0.3)', fillerColor: 'rgba(255,255,255,0.1)', handleStyle: {{ color: '#00d4ff' }}, textStyle: {{ color: 'rgba(255,255,255,0.6)' }} }}],
            series: [{{
                name: '份额', type: 'line', smooth: true, symbol: 'circle', symbolSize: 4, sampling: 'lttb',
                itemStyle: {{ color: '#00d4ff', borderWidth: 2 }},
                areaStyle: {{ color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{{ offset: 0, color: 'rgba(0, 212, 255, 0.4)' }}, {{ offset: 1, color: 'rgba(0, 212, 255, 0)' }}]) }},
                data: {json.dumps(volumes)},
                markPoint: {{ data: [{{ type: 'max', name: '最大值' }}, {{ type: 'min', name: '最小值' }}], symbolSize: 50, label: {{ color: '#fff', formatter: function(param) {{ return (param.value / 10000).toFixed(2) + '亿'; }} }} }},
                markLine: {{ data: [{{ type: 'average', name: '平均值' }}], lineStyle: {{ color: 'rgba(255, 255, 255, 0.3)' }}, label: {{ color: 'rgba(255,255,255,0.6)', formatter: function(param) {{ return (param.value / 10000).toFixed(2) + '亿'; }} }} }}
            }}]
        }};
        chart.setOption(option);
        window.addEventListener('resize', function() {{ chart.resize(); }});
    </script>
</body>
</html>'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"HTML saved: {output_path}")
    return output_path


if __name__ == '__main__':
    PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    etf_code = sys.argv[1] if len(sys.argv) > 1 else '512070'
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 500

    print(f"Fetching ETF {etf_code} data for {days} days...")
    trend = get_etf_trend(etf_code, days)

    if trend:
        output_path = os.path.join(PROJECT_DIR, 'data', f'etf_{etf_code}_trend.html')
        generate_html(etf_code, trend, output_path)

        print(f"\nData summary (last 5 days):")
        for d, v in list(trend.items())[-5:]:
            print(f"  {d}: {v['secName']} - {v['totVol']/10000:.4f}亿")