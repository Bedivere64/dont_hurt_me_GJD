"""
ETF数据采集与分析工具
基于SQLite数据库存储历史数据

用法:
    python etf_db.py fetch [天数]     # 采集数据
    python etf_db.py query            # 查询份额上升的ETF
    python etf_db.py trend [代码]     # 查看某ETF趋势
    python etf_db.py check            # 检查数据完整性
"""
import urllib.request
import json
import sqlite3
import os
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    from chinese_calendar import is_workday
except ImportError:
    def is_workday(date):
        return date.weekday() < 5

# 数据库放在项目目录下
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, 'etf_data.db')


def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS etf_info (
            sec_code TEXT PRIMARY KEY,
            sec_name TEXT,
            etf_type TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS etf_daily_share (
            sec_code TEXT,
            stat_date TEXT,
            tot_vol REAL,
            num INTEGER,
            PRIMARY KEY (sec_code, stat_date)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_stat_date ON etf_daily_share(stat_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sec_code ON etf_daily_share(sec_code)')
    conn.commit()
    return conn


def save_to_db(conn, results):
    """保存到数据库"""
    cursor = conn.cursor()
    data_list = [(r['SEC_CODE'], r['STAT_DATE'], float(r['TOT_VOL']), int(r['NUM'])) for r in results]
    cursor.executemany(
        'INSERT OR REPLACE INTO etf_daily_share (sec_code, stat_date, tot_vol, num) VALUES (?, ?, ?, ?)',
        data_list
    )
    etf_infos = {(r['SEC_CODE'], r.get('SEC_NAME'), r.get('ETF_TYPE')) for r in results}
    cursor.executemany(
        'INSERT OR REPLACE INTO etf_info (sec_code, sec_name, etf_type) VALUES (?, ?, ?)',
        etf_infos
    )
    conn.commit()


def fetch_etf_data(date_str):
    """获取指定日期的全量ETF份额数据（自动处理分页）"""
    all_results = []
    page_no = 1
    page_size = 100

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Referer': 'https://www.sse.com.cn/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64, x64) AppleWebKit/537.36'
    }

    while True:
        url = (f'https://query.sse.com.cn/commonQuery.do?jsonCallBack=cb&isPagination=true'
               f'&pageHelp.pageSize={page_size}&pageHelp.pageNo={page_no}&pageHelp.beginPage={page_no}'
               f'&pageHelp.cacheSize=1&pageHelp.endPage={page_no}'
               f'&sqlId=COMMON_SSE_ZQPZ_ETFZL_XXPL_ETFGM_SEARCH_L'
               f'&STAT_DATE={date_str}&_={int(time.time() * 1000)}')
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
        except Exception as e:
            break

    return all_results


def get_trading_days(days=130):
    """获取最近days个交易日的日期列表"""
    today = datetime.now()
    trading_days = []
    for i in range(days * 2):
        date = today - timedelta(days=i)
        if is_workday(date):
            trading_days.append(date.strftime('%Y-%m-%d'))
            if len(trading_days) >= days:
                break
    return trading_days


def fetch_data(days=126, max_workers=50):
    """采集数据"""
    conn = init_db()
    trading_days = get_trading_days(days)
    print(f"Fetching {len(trading_days)} trading days data (with pagination)...")

    total = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_etf_data, d): d for d in trading_days}
        for future in as_completed(futures):
            results = future.result()
            if results:
                save_to_db(conn, results)
                total += len(results)

    conn.close()
    print(f"Done: {total} records saved to {DB_PATH}")
    return total


def query_rising_etfs(days=126):
    """查询最近days天份额上升的ETF"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = '''
        WITH period AS (
            SELECT sec_code, stat_date, tot_vol
            FROM etf_daily_share
            WHERE stat_date >= date('now', '-' || ? || ' days')
        ),
        first_last AS (
            SELECT p1.sec_code,
                COUNT(*) as data_days,
                (SELECT tot_vol FROM period p2 WHERE p2.sec_code = p1.sec_code ORDER BY stat_date ASC LIMIT 1) as start_vol,
                (SELECT tot_vol FROM period p3 WHERE p3.sec_code = p1.sec_code ORDER BY stat_date DESC LIMIT 1) as latest_vol,
                (SELECT stat_date FROM period p4 WHERE p4.sec_code = p1.sec_code ORDER BY stat_date ASC LIMIT 1) as start_date,
                (SELECT stat_date FROM period p5 WHERE p5.sec_code = p1.sec_code ORDER BY stat_date DESC LIMIT 1) as end_date
            FROM period p1
            GROUP BY sec_code
        )
        SELECT
            f.sec_code,
            i.sec_name,
            f.data_days,
            f.start_vol,
            f.latest_vol,
            ROUND((f.latest_vol - f.start_vol) / f.start_vol * 100, 2) as change_pct,
            f.start_date,
            f.end_date
        FROM first_last f
        LEFT JOIN etf_info i ON f.sec_code = i.sec_code
        WHERE f.start_vol > 0 AND f.latest_vol > f.start_vol
        ORDER BY change_pct DESC
    '''
    cursor.execute(query, (days,))
    results = cursor.fetchall()
    conn.close()
    return results


def query_etf_trend(sec_code, days=100):
    """查询某ETF的历史趋势"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT stat_date, tot_vol
        FROM etf_daily_share
        WHERE sec_code = ? AND stat_date >= date('now', '-' || ? || ' days')
        ORDER BY stat_date
    ''', (sec_code, days))
    results = cursor.fetchall()
    conn.close()
    return results


def check_data_completeness():
    """检查数据库数据完整性"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 检查每天的ETF数量
    cursor.execute('''
        SELECT stat_date, COUNT(*) as cnt
        FROM etf_daily_share
        GROUP BY stat_date
        ORDER BY stat_date DESC
        LIMIT 20
    ''')
    daily_counts = cursor.fetchall()

    print("Data Completeness Check:")
    print("=" * 50)
    print(f"{'Date':<15} {'ETF Count':<10} {'Status'}")
    print("-" * 50)

    for date, cnt in daily_counts:
        status = "OK" if cnt > 800 else "LOW"
        print(f"{date:<15} {cnt:<10} {status}")

    conn.close()


def print_rising_etfs(results):
    """打印份额上升的ETF列表"""
    print("=" * 90)
    print(f"{'Code':<10} {'Name':<14} {'Days':<5} {'Start(W)':<12} {'End(W)':<12} {'Change%':<10} {'Period'}")
    print("-" * 90)

    for row in results:
        sec_code, sec_name, data_days, start_vol, latest_vol, change_pct, start_date, end_date = row
        name = sec_name[:12] if sec_name else sec_code
        period = f"{start_date[-5:]}~{end_date[-5:]}"
        print(f"{sec_code:<10} {name:<14} {data_days:<5} {start_vol/10000:<12.2f} {latest_vol/10000:<12.2f} {change_pct:>+8.2f}%  {period}")

    print("-" * 90)
    print(f"Total: {len(results)} ETFs with rising shares")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == 'fetch':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 126
        fetch_data(days)
    elif cmd == 'query':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 126
        results = query_rising_etfs(days)
        print_rising_etfs(results)
    elif cmd == 'trend':
        sec_code = sys.argv[2] if len(sys.argv) > 2 else '510050'
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        results = query_etf_trend(sec_code, days)
        print(f"\nETF {sec_code} trend (last {days} days):")
        print(f"{'Date':<12} {'Volume':>15}")
        print("-" * 30)
        for date, vol in results[-20:]:
            print(f"{date:<12} {vol/10000:>15.2f}万")
    elif cmd == 'check':
        check_data_completeness()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)