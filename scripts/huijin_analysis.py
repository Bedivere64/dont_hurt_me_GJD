"""
汇金系ETF买卖趋势分析

假设十大持有人占比不变，用2025-12-31的份额占比，
结合ETF总份额变化，估算汇金系的买卖情况。
"""
import sqlite3
import sys
from pathlib import Path

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DB_PATH = Path(__file__).parent.parent / "data" / "etf_data.db"


def analyze():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. 找出所有汇金系持有的ETF
    cur.execute("""
        SELECT DISTINCT h.sec_code, i.sec_name, i.full_name
        FROM etf_top_holders h
        JOIN etf_info i ON h.sec_code = i.sec_code
        WHERE h.holder_name LIKE '%汇金%'
        ORDER BY h.sec_code
    """)
    huijin_etfs = cur.fetchall()

    if not huijin_etfs:
        print("未找到汇金系持有的ETF")
        conn.close()
        return

    results = []

    for code, name, full_name in huijin_etfs:
        # 2. 获取该ETF的汇金系总占比
        cur.execute("""
            SELECT SUM(holder_pct) FROM etf_top_holders
            WHERE sec_code = ? AND holder_name LIKE '%汇金%'
        """, (code,))
        huijin_pct = cur.fetchone()[0]
        if not huijin_pct or huijin_pct == 0:
            continue

        # 3. 获取2025-12-31的份额
        cur.execute("""
            SELECT tot_vol FROM etf_daily_share
            WHERE sec_code = ? AND stat_date = '2025-12-31'
        """, (code,))
        row = cur.fetchone()
        if not row:
            continue
        dec31_vol = row[0]  # 万份

        # 4. 获取最新份额
        cur.execute("""
            SELECT stat_date, tot_vol FROM etf_daily_share
            WHERE sec_code = ?
            ORDER BY stat_date DESC LIMIT 1
        """, (code,))
        row = cur.fetchone()
        if not row:
            continue
        latest_date, latest_vol = row

        if latest_date == '2025-12-31':
            continue  # 没有更新的数据

        # 5. 计算
        vol_diff = latest_vol - dec31_vol  # 万份
        vol_diff_pct = (vol_diff / dec31_vol) * 100 if dec31_vol != 0 else 0

        # 汇金系估算买卖（份）
        # dec31总份额(份) = dec31_vol * 10000
        # 汇金持有(份) = dec31总份额 * huijin_pct / 100
        # 买卖(份) = vol_diff * 10000 * huijin_pct / 100
        huijin_trade = vol_diff * 10000 * huijin_pct / 100  # 份

        results.append({
            'code': code,
            'name': name,
            'full_name': full_name,
            'huijin_pct': huijin_pct,
            'dec31_vol': dec31_vol,
            'latest_date': latest_date,
            'latest_vol': latest_vol,
            'vol_diff': vol_diff,
            'vol_diff_pct': vol_diff_pct,
            'huijin_trade': huijin_trade,
        })

    conn.close()

    if not results:
        print("没有足够的数据进行分析")
        return

    # ---- 排序输出 ----
    buy_list = sorted(results, key=lambda x: x['huijin_trade'], reverse=True)
    sell_list = sorted(results, key=lambda x: x['huijin_trade'])

    def print_table(title, data, top_n=10):
        print()
        print("=" * 100)
        print(f"  {title}")
        print("=" * 100)
        header = f"{'代码':<8} {'简称':<14} {'汇金占比':>8} {'12-31份额(万)':>16} {'最新份额(万)':>16} {'份额变动%':>9} {'估算买卖(份)':>18}"
        print(header)
        print("-" * 100)
        for r in data[:top_n]:
            trade_str = f"{r['huijin_trade']:+,.0f}"
            print(
                f"{r['code']:<8} {r['name']:<14} {r['huijin_pct']:>7.2f}% "
                f"{r['dec31_vol']:>16,.0f} {r['latest_vol']:>16,.0f} "
                f"{r['vol_diff_pct']:>8.1f}% {trade_str:>18}"
            )
        print("-" * 100)

    print(f"\n分析日期: {results[0]['latest_date']}  基准日: 2025-12-31")
    print(f"共 {len(results)} 只ETF有汇金系持仓数据")

    print_table("汇金系估算净买入 TOP 10", buy_list)
    print_table("汇金系估算净卖出 TOP 10", sell_list)

    # 汇总
    total_trade = sum(r['huijin_trade'] for r in results)
    print(f"\n汇金系全市场合计估算买卖: {total_trade:+,.0f} 份")


if __name__ == '__main__':
    analyze()
