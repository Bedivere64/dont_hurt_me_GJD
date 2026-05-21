"""
ETF命令行工具
"""
import sys
from .fetcher import fetch_data, update_full_names
from .queries import (
    query_rising_etfs,
    query_etf_trend,
    query_securities_etf,
    query_top_etfs,
    check_data_completeness, query_etf_info
)


def print_rising_etfs(results):
    """打印份额上升的ETF列表"""
    print("=" * 90)
    print(f"{'Code':<10} {'Name':<14} {'Days':<5} {'Start(亿)':<12} {'End(亿)':<12} {'Change%':<10} {'Period'}")
    print("-" * 90)

    for row in results:
        sec_code, sec_name, data_days, start_vol, latest_vol, change_pct, start_date, end_date = row
        name = sec_name[:12] if sec_name else sec_code
        period = f"{start_date[-5:]}~{end_date[-5:]}"
        print(f"{sec_code:<10} {name:<14} {data_days:<5} {start_vol/10000:<12.2f} {latest_vol/10000:<12.2f} {change_pct:>+8.2f}%  {period}")

    print("-" * 90)
    print(f"Total: {len(results)} ETFs with rising shares")


def main():
    if len(sys.argv) < 2:
        print("""
ETF份额数据分析工具

用法:
    python -m src.etf.cli fetch [天数]     # 采集数据
    python -m src.etf.cli query            # 查询份额上升的ETF
    python -m src.etf.cli trend [代码]     # 查看某ETF趋势
    python -m src.etf.cli check            # 检查数据完整性
    python -m src.etf.cli securities       # 查看证券ETF份额变化
    python -m src.etf.cli top [n]         # 查看份额增加最多的n只ETF
    python -m src.etf.cli top_pct [n]     # 查看份额增幅最多的n只ETF
    python -m src.etf.cli update_names     # 更新ETF完整名称
""")
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
        etf_info = query_etf_info(sec_code)
        if etf_info is None:
            print("ETF {} not found".format(sec_code))
            return
        results = query_etf_trend(sec_code, days)
        print(f"\nETF {sec_code} {etf_info['full_name']} {etf_info['sec_name']} {etf_info['etf_type']} trend (last {days} days):")
        print(f"{'Date':<12} {'Volume(万份)':>18}")
        print("-" * 35)
        for date, vol in results[-20:]:
            print(f"{date:<12} {vol:>18.2f}")
    elif cmd == 'check':
        daily_counts = check_data_completeness()
        print("Data Completeness Check:")
        print("=" * 50)
        print(f"{'Date':<15} {'ETF Count':<10} {'Status'}")
        print("-" * 50)
        for date, cnt in daily_counts:
            status = "OK" if cnt > 800 else "LOW"
            print(f"{date:<15} {cnt:<10} {status}")
    elif cmd == 'securities':
        results, latest_date, prev_date = query_securities_etf('volume')
        if not results:
            print('数据不足')
            return
        print(f'\n证券/保险ETF份额变化 按份额从高到低 ({prev_date} -> {latest_date}):')
        print('=' * 120)
        print(f'{"代码":<10} {"名称":<20} {"上日份额(万)":>14} {"最新份额(万)":>14} {"变化(万)":>12} {"增幅":>10}')
        print('-' * 120)
        for row in results:
            print(f'{row[0]:<10} {row[1]:<20} {row[3]:>14.2f} {row[2]:>14.2f} {row[4]:>+12.2f} {row[5]:>+9.2f}%')
        print('=' * 120)
    elif cmd == 'top':
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        results, latest_date, prev_date = query_top_etfs(n, 'change')
        if not results:
            return
        print(f'\n份额增加前{n}名 ({prev_date} -> {latest_date}):')
        print('=' * 120)
        print(f'{"排名":<4} {"代码":<10} {"名称":<20} {"最新份额(万)":>16} {"变化(万)":>12} {"增幅":>10}')
        print('-' * 120)
        for i, row in enumerate(results, 1):
            print(f'{i:<4} {row[0]:<10} {row[1]:<20} {row[2]:>16.2f} {row[4]:>+12.2f} {row[5]:>+9.2f}%')
        print('=' * 120)
    elif cmd == 'top_pct':
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        results, latest_date, prev_date = query_top_etfs(n, 'pct')
        if not results:
            return
        print(f'\n份额增幅前{n}名 ({prev_date} -> {latest_date}):')
        print('=' * 120)
        print(f'{"排名":<4} {"代码":<10} {"名称":<20} {"最新份额(万)":>16} {"变化(万)":>12} {"增幅":>10}')
        print('-' * 120)
        for i, row in enumerate(results, 1):
            print(f'{i:<4} {row[0]:<10} {row[1]:<20} {row[2]:>16.2f} {row[4]:>+12.2f} {row[5]:>+9.2f}%')
        print('=' * 120)
    elif cmd == 'update_names':
        update_full_names()
    else:
        print(f"Unknown command: {cmd}")
        print("Run without arguments to see usage")


if __name__ == '__main__':
    main()
