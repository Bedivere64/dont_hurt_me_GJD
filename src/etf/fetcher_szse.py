"""
深交所ETF数据获取模块
"""
import urllib.request
import json
import time
import random
import re
import http.cookiejar
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


# 创建Cookie处理器和Opener（模拟浏览器会话）
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))


def get_random() -> str:
    """生成随机数参数"""
    return str(random.random())


def get_headers() -> Dict[str, str]:
    """获取模拟浏览器的请求头"""
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    }


def fetch_with_session(url: str) -> Optional[str]:
    """
    使用Session获取URL内容

    Args:
        url: 请求URL

    Returns:
        响应内容，失败返回None
    """
    headers = get_headers()
    req = urllib.request.Request(url, headers=headers)

    try:
        with opener.open(req, timeout=30) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        return None


def fetch_szse_etf_list() -> List[Dict[str, Any]]:
    """
    获取深交所全部ETF列表

    Returns:
        ETF列表，每项包含 sec_code, sec_name
    """
    all_etfs = []
    page_no = 1
    page_size = 100

    # 先访问首页建立Session
    fetch_with_session('https://fund.szse.cn/marketdata/etf/index.html')
    time.sleep(1)  # 等待Session建立

    while True:
        url = f'https://fund.szse.cn/api/report/ShowReport/data?SHOWTYPE=JSON&CATALOGID=fund_etf&random={get_random()}&pageNo={page_no}&pageSize={page_size}'

        text = fetch_with_session(url)
        if not text:
            print(f"Error fetching ETF list page {page_no}")
            break

        try:
            data = json.loads(text)

            if not data or 'data' not in data[0]:
                break

            metadata = data[0].get('metadata', {})
            total_pages = metadata.get('pagecount', 1)

            for item in data[0]['data']:
                # 解析代码 - 格式如 <a href='...code=159029'><u>159029</u></a>
                code_html = item.get('sys_key', '')
                match = re.search(r'code=(\d+)', code_html)
                sec_code = match.group(1) if match else ''

                # 解析简称
                name_html = item.get('kzjcurl', '')
                match = re.search(r'<u>([^<]+)</u>', name_html)
                sec_name = match.group(1) if match else ''

                if sec_code:
                    all_etfs.append({
                        'sec_code': sec_code,
                        'sec_name': sec_name
                    })

            if page_no >= total_pages:
                break
            page_no += 1
            time.sleep(0.5)  # 页面间延时

        except Exception as e:
            print(f"Error parsing ETF list page {page_no}: {e}")
            break

    return all_etfs


def fetch_szse_etf_history(sec_code: str, start_date: str, end_date: str, retry: int = 3) -> List[Dict[str, Any]]:
    """
    获取深交所ETF历史份额数据

    Args:
        sec_code: ETF代码
        start_date: 开始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD
        retry: 重试次数

    Returns:
        历史数据列表
    """
    url = (f'https://fund.szse.cn/api/report/ShowReport/data?SHOWTYPE=JSON'
           f'&CATALOGID=fund_jjgm&TABKEY=tab1&loading=first'
           f'&txtDm={sec_code}&txtStart={start_date}&txtEnd={end_date}&random={get_random()}')

    for attempt in range(retry):
        time.sleep(0.5)  # 延时0.5秒
        text = fetch_with_session(url)

        if text:
            try:
                data = json.loads(text)

                if not data or 'data' not in data[0]:
                    return []

                results = []
                for item in data[0]['data']:
                    size_str = item.get('current_size', '0').replace(',', '')
                    results.append({
                        'stat_date': item.get('size_date', ''),
                        'sec_code': item.get('fund_code', ''),
                        'sec_name': item.get('security_short_name', ''),
                        'tot_vol': float(size_str) if size_str else 0.0
                    })

                return results

            except Exception as e:
                pass

        if attempt < retry - 1:
            time.sleep(2)  # 重试前等待2秒

    return []


def get_trading_days(days: int = 500) -> List[str]:
    """
    获取最近days个交易日的日期列表（工作日）

    Args:
        days: 需要获取的交易日数量

    Returns:
        日期字符串列表
    """
    today = datetime.now()
    trading_days = []
    for i in range(days * 2):
        date = today - timedelta(days=i)
        # 简单判断工作日（周一到周五）
        if date.weekday() < 5:
            trading_days.append(date.strftime('%Y-%m-%d'))
            if len(trading_days) >= days:
                break
    return trading_days


def fetch_data(days: int = 500, max_workers: int = 1) -> int:
    """
    采集深交所ETF数据

    Args:
        days: 采集多少天的数据
        max_workers: 最大并发数（默认1，避免限流）

    Returns:
        总共采集的记录数
    """
    from .database import init_db, save_to_db

    print(f"Fetching SZSE ETF list...")
    etf_list = fetch_szse_etf_list()
    if not etf_list:
        print("No ETF list fetched")
        return 0

    print(f"Got {len(etf_list)} SZSE ETFs")

    # 计算日期范围
    end_date = datetime.now().strftime('%Y-%m-%d')
    trading_days = get_trading_days(days)
    start_date = trading_days[-1] if len(trading_days) > days else trading_days[0]

    print(f"Fetching history from {start_date} to {end_date} ({days} trading days)...")

    all_results = []
    completed = 0

    # 单线程顺序采集，避免触发限流
    for etf in etf_list:
        results = fetch_szse_etf_history(etf['sec_code'], start_date, end_date)
        completed += 1

        if completed % 50 == 0:
            print(f"  Progress: {completed}/{len(etf_list)}")

        if results:
            all_results.extend(results)

    if not all_results:
        print("No data fetched")
        return 0

    # 保存到数据库
    conn = init_db()
    saved = save_to_db(conn, all_results, market='SZ')
    conn.close()

    print(f"Done: {saved} records saved")
    return saved
