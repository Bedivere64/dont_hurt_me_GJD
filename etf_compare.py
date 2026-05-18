"""
ETF与上证指数对比图生成脚本
用法: python etf_compare.py [ETF代码] [天数]
示例: python etf_compare.py 510300 500
"""
import urllib.request
import json
import sqlite3
from datetime import datetime, timedelta
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

try:
    from chinese_calendar import is_workday
except ImportError:
    def is_workday(date):
        return date.weekday() < 5

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, 'etf_data.db')


def get_latest_date_in_db():
    """获取数据库中最新的日期"""
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(stat_date) FROM etf_daily_share")
    result = cursor.fetchone()[0]
    conn.close()
    return result


def get_all_dates_in_db():
    """获取数据库中所有日期"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT stat_date FROM etf_daily_share ORDER BY stat_date")
    dates = [row[0] for row in cursor.fetchall()]
    conn.close()
    return set(dates)


def sync_to_latest():
    """检查并补全数据库到最新交易日"""
    today = datetime.now()

    # 找到最近的交易日
    latest_trading_day = today
    if not is_workday(latest_trading_day):
        for i in range(1, 10):
            d = today - timedelta(days=i)
            if is_workday(d):
                latest_trading_day = d
                break

    latest_date_str = latest_trading_day.strftime('%Y-%m-%d')
    db_latest = get_latest_date_in_db()

    if db_latest is None:
        print("Database is empty, need to run: python etf_db.py fetch")
        return False

    if db_latest >= latest_date_str:
        print(f"Database is up to date (latest: {db_latest})")
        return True

    print(f"Database is outdated. Latest: {db_latest}, should be: {latest_date_str}")

    # 计算需要补的日期
    db_dates = get_all_dates_in_db()
    dates_to_fetch = []

    current = datetime.strptime(db_latest, '%Y-%m-%d')
    while current < latest_trading_day:
        current += timedelta(days=1)
        if is_workday(current):
            date_str = current.strftime('%Y-%m-%d')
            if date_str not in db_dates:
                dates_to_fetch.append(date_str)

    if not dates_to_fetch:
        print("No missing dates found")
        return True

    print(f"Fetching {len(dates_to_fetch)} missing days: {dates_to_fetch[:3]}...")
    fetch_missing_data(dates_to_fetch)
    print("Sync completed")
    return True


def fetch_missing_data(dates):
    """补采缺失日期的数据"""
    def fetch_one(date_str):
        all_results = []
        page_no = 1
        page_size = 100
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://www.sse.com.cn/',
            'User-Agent': 'Mozilla/5.0'
        }
        while True:
            url = (f'https://query.sse.com.cn/commonQuery.do?jsonCallBack=cb&isPagination=true'
                   f'&pageHelp.pageSize={page_size}&pageHelp.pageNo={page_no}&pageHelp.beginPage={page_no}'
                   f'&pageHelp.cacheSize=1&pageHelp.endPage={page_no}'
                   f'&sqlId=COMMON_SSE_ZQPZ_ETFZL_XXPL_ETFGM_SEARCH_L'
                   f'&STAT_DATE={date_str}&_=1779034630785')
            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=15) as response:
                    text = response.read().decode('utf-8')
                    json_str = text[text.index('(') + 1 : text.rindex(')')]
                    data = json.loads(json_str)
                    results = data.get('result', [])
                    page_help = data.get('pageHelp', {})
                    all_results.extend(results)
                    if page_no >= page_help.get('pageCount', 1):
                        break
                    page_no += 1
            except:
                break
        return date_str, all_results

    # 初始化数据库表
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS etf_info (
            sec_code TEXT PRIMARY KEY, sec_name TEXT, etf_type TEXT, created_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS etf_daily_share (
            sec_code TEXT, stat_date TEXT, tot_vol REAL, num INTEGER, PRIMARY KEY (sec_code, stat_date)
        )
    ''')
    conn.commit()

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_one, d): d for d in dates}
        for future in as_completed(futures):
            date_str, results = future.result()
            if results:
                data_list = [(r['SEC_CODE'], r['STAT_DATE'], float(r['TOT_VOL']), int(r['NUM'])) for r in results]
                cursor.executemany('INSERT OR REPLACE INTO etf_daily_share VALUES (?,?,?,?)', data_list)
                etf_infos = {(r['SEC_CODE'], r.get('SEC_NAME'), r.get('ETF_TYPE')) for r in results}
                cursor.executemany('INSERT OR REPLACE INTO etf_info VALUES (?,?,?,?)', etf_infos)
                conn.commit()
                print(f"  {date_str}: {len(results)} records")

    conn.close()


def get_etf_from_db(etf_code, days=500):
    """从数据库获取ETF历史数据"""
    conn = sqlite3.connect(DB_PATH)
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

    # 上证指数用点数，直接原始数据
    index_base = index_values_common[0]  # 期初点数

    # 整体统计
    etf_total_change = round((etf_values_common[-1] - etf_values_common[0]) / etf_values_common[0] * 100, 2)
    index_total_change = round((index_values_common[-1] - index_values_common[0]) / index_values_common[0] * 100, 2)
    etf_max_vol = max(etf_values_common)
    etf_min_vol = min(etf_values_common)

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
    import sys
    etf_code = sys.argv[1] if len(sys.argv) > 1 else '510300'
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 500

    print(f"Checking database for {etf_code}...")
    if not sync_to_latest():
        print("Please run: python etf_db.py fetch first")
        exit(1)

    print(f"\nLoading {etf_code} data from database...")
    etf_name, etf_data = get_etf_from_db(etf_code, days)
    print(f"Got {len(etf_data)} days ETF data: {etf_name}")

    if not etf_data:
        print("No ETF data found. Run 'python etf_db.py fetch' first.")
        exit(1)

    index_data = fetch_index_data('sh000001', days)

    if etf_data and index_data:
        output = os.path.join(PROJECT_DIR, f'etf_{etf_code}_vs_index.html')
        generate_html(etf_code, etf_name, etf_data, index_data, output)