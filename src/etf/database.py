"""
ETF数据库操作模块
"""
import sqlite3
import os
from pathlib import Path


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent.parent


def get_db_path() -> str:
    """获取数据库路径"""
    return os.path.join(get_project_root(), 'data', 'etf_data.db')


def init_db() -> sqlite3.Connection:
    """初始化数据库"""
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查是否需要添加 full_name 字段
    cursor.execute("PRAGMA table_info(etf_info)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'full_name' not in columns:
        cursor.execute('ALTER TABLE etf_info ADD COLUMN full_name TEXT')

    # 检查 etf_daily_share 表是否有 close_price 字段
    cursor.execute("PRAGMA table_info(etf_daily_share)")
    share_columns = [col[1] for col in cursor.fetchall()]

    if 'close_price' not in share_columns:
        cursor.execute('ALTER TABLE etf_daily_share ADD COLUMN close_price REAL')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS etf_info (
            sec_code TEXT PRIMARY KEY,
            sec_name TEXT,
            full_name TEXT,
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
            close_price REAL,
            PRIMARY KEY (sec_code, stat_date)
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_stat_date ON etf_daily_share(stat_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sec_code ON etf_daily_share(sec_code)')
    conn.commit()
    return conn


def get_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    return sqlite3.connect(get_db_path())


def save_to_db(conn, results, prices=None):
    """
    保存到数据库

    Args:
        conn: 数据库连接
        results: ETF份额数据列表
        prices: ETF收盘价字典 {sec_code: {date: close_price}}
    """
    cursor = conn.cursor()

    # 构建收盘价查找表
    price_map = {}
    if prices:
        for sec_code, date_prices in prices.items():
            for date, close_price in date_prices.items():
                price_map[(sec_code, date)] = close_price

    data_list = []
    for r in results:
        sec_code = r['SEC_CODE']
        stat_date = r['STAT_DATE']
        tot_vol = float(r['TOT_VOL'])
        num = int(r['NUM'])
        close_price = price_map.get((sec_code, stat_date))
        data_list.append((sec_code, stat_date, tot_vol, num, close_price))

    cursor.executemany(
        'INSERT OR REPLACE INTO etf_daily_share (sec_code, stat_date, tot_vol, num, close_price) VALUES (?, ?, ?, ?, ?)',
        data_list
    )

    # 批量处理ETF信息
    for r in results:
        sec_code = r['SEC_CODE']
        sec_name = r.get('SEC_NAME', '')
        etf_type = r.get('ETF_TYPE', '')

        # 检查现有记录
        cursor.execute('SELECT sec_name, full_name FROM etf_info WHERE sec_code = ?', (sec_code,))
        existing = cursor.fetchone()

        if existing:
            old_sec_name, old_full_name = existing
            # 如果有full_name但sec_name是简称，保持不变
            if old_full_name and old_sec_name != old_full_name:
                # sec_name是简称，不更新
                pass
            else:
                # 更新为原始名称
                cursor.execute(
                    'UPDATE etf_info SET sec_name = ?, etf_type = ? WHERE sec_code = ?',
                    (sec_name, etf_type, sec_code)
                )
        else:
            cursor.execute(
                'INSERT INTO etf_info (sec_code, sec_name, etf_type) VALUES (?, ?, ?)',
                (sec_code, sec_name, etf_type)
            )

    conn.commit()
