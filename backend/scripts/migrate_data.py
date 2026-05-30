import sqlite3
import sys
sys.path.insert(0, '/opt/etf-dashboard/backend')

from app import create_app, db
from app.models import ETFInfo, ETFDailyShare

app = create_app()

sqlite_db = '/tmp/etf_data.db'

print('开始数据迁移...')

conn = sqlite3.connect(sqlite_db)
cur = conn.cursor()

# 获取所有表
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print(f'SQLite表: {[t[0] for t in tables]}')

with app.app_context():
    # 迁移 etf_info
    cur.execute('SELECT * FROM etf_info')
    rows = cur.fetchall()
    print(f'迁移 {len(rows)} 条 etf_info...')
    for row in rows:
        try:
            etf = ETFInfo(
                sec_code=row[0],
                sec_name=row[1],
                full_name=row[2] if len(row) > 2 else None,
                list_date=row[3] if len(row) > 3 else None,
                fund_manager=row[4] if len(row) > 4 else None
            )
            db.session.merge(etf)
        except Exception as e:
            print(f'Error: {e}')
    db.session.commit()

    # 迁移 etf_daily_share
    cur.execute('SELECT * FROM etf_daily_share')
    rows = cur.fetchall()
    print(f'迁移 {len(rows)} 条 etf_daily_share...')
    for i, row in enumerate(rows):
        try:
            share = ETFDailyShare(
                sec_code=row[0],
                stat_date=row[1],
                tot_vol=row[2],
                num=row[3] if len(row) > 3 else None,
                close_price=row[4] if len(row) > 4 else None,
                market=row[5] if len(row) > 5 else 'SH'
            )
            db.session.add(share)
            if (i + 1) % 10000 == 0:
                db.session.commit()
                print(f'已提交 {i + 1} 条...')
        except Exception as e:
            pass
    db.session.commit()

conn.close()
print('数据迁移完成！')

# 验证
with app.app_context():
    info_count = db.session.query(ETFInfo).count()
    share_count = db.session.query(ETFDailyShare).count()
    print(f'PostgreSQL 中: etf_info={info_count}, etf_daily_share={share_count}')
