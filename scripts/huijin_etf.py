"""
查询某ETF的汇金系持仓及估算买卖情况

假设十大持有人占比不变，用2025-12-31的份额占比，
结合ETF总份额变化，估算汇金系的买卖情况。

用法: python scripts/huijin_etf.py 510330
"""
import sqlite3
import sys
from pathlib import Path

# 解决Windows终端中文编码问题
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DB_PATH = Path(__file__).parent.parent / "data" / "etf_data.db"


def analyze(code: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1. ETF基本信息
    cur.execute("SELECT sec_code, sec_name, full_name, etf_type FROM etf_info WHERE sec_code=?", (code,))
    info = cur.fetchone()
    if not info:
        print(f"未找到ETF: {code}")
        conn.close()
        return

    print(f"代码: {info[0]}  简称: {info[1]}  全称: {info[2]}  类型: {info[3]}")
    print()

    # 2. 十大持有人
    cur.execute("""
        SELECT rank, holder_name, holder_share, holder_pct
        FROM etf_top_holders WHERE sec_code=? ORDER BY rank
    """, (code,))
    holders = cur.fetchall()
    if not holders:
        print("该ETF暂无十大持有人数据")
        conn.close()
        return

    print("=" * 80)
    print("十大持有人 (报告期: 2025-12-31)")
    print("-" * 80)
    huijin_list = []
    for h in holders:
        tag = " <<< 汇金系" if "汇金" in h[1] else ""
        print(f"{h[0]:>2}. {h[1]:<42} {h[2]:>14,.0f}份  {h[3]:>6.2f}%{tag}")
        if "汇金" in h[1]:
            huijin_list.append(h)

    print("=" * 80)

    total_pct = sum(h[3] for h in huijin_list)
    if huijin_list:
        print(f"\n汇金系持仓明细:")
        for h in huijin_list:
            print(f"  · {h[1]}  占{h[3]:.2f}%")
        print(f"  汇金系合计占比: {total_pct:.2f}%")
    else:
        print(f"\n该ETF十大持有人中未发现汇金系身影")
        conn.close()
        return

    # 3. 份额变化
    cur.execute("""
        SELECT stat_date, tot_vol FROM etf_daily_share
        WHERE sec_code=? AND stat_date>='2025-12-31'
        ORDER BY stat_date
    """, (code,))
    daily = cur.fetchall()
    if not daily:
        print("暂无2025-12-31以来的份额数据")
        conn.close()
        return

    dec31_vol = daily[0][1]
    latest_date, latest_vol = daily[-1]

    if latest_date == '2025-12-31':
        print("暂无2025-12-31之后的数据")
        conn.close()
        return

    vol_diff = latest_vol - dec31_vol
    vol_pct = (vol_diff / dec31_vol) * 100

    print(f"\n份额变化 ({latest_date} vs 2025-12-31):")
    print(f"  2025-12-31:  {dec31_vol:>16,.2f} 万份")
    print(f"  {latest_date}:  {latest_vol:>16,.2f} 万份")
    direction = "+" if vol_diff >= 0 else ""
    print(f"  总变动:      {direction}{vol_diff:>15,.2f} 万份 ({direction}{vol_pct:.2f}%)")

    # 4. 汇金系估算买卖
    huijin_dec31 = dec31_vol * 10000 * total_pct / 100  # 份
    huijin_now = latest_vol * 10000 * total_pct / 100
    huijin_trade = huijin_now - huijin_dec31

    print(f"\n{'=' * 60}")
    print(f"汇金系估算 (假设占比 {total_pct:.2f}% 不变)")
    print(f"{'=' * 60}")
    print(f"  2025-12-31 持有:  {huijin_dec31:>20,.0f} 份")
    print(f"  {latest_date} 持有:  {huijin_now:>20,.0f} 份")
    action = "净买入" if huijin_trade >= 0 else "净卖出"
    print(f"  期间{action}:        {abs(huijin_trade):>20,.0f} 份")

    # 5. 近期趋势
    print(f"\n近期份额趋势 (万份):")
    for d in daily[-10:]:
        marker = " <<< 基准日" if d[0] == '2025-12-31' else ""
        print(f"  {d[0]}  {d[1]:>14,.2f}{marker}")

    conn.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python scripts/huijin_etf.py <ETF代码>")
        print("示例: python scripts/huijin_etf.py 510330")
        sys.exit(1)
    analyze(sys.argv[1])
