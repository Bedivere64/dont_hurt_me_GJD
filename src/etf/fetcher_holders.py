"""
ETF十大持有人数据采集模块 - 从新浪财经爬取
"""
import requests
from bs4 import BeautifulSoup
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Optional

from .database import init_db, get_connection, save_holders_to_db


_session = None

def _get_session():
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'http://stock.finance.sina.com.cn/'
        })
    return _session


def fetch_top_holders(sec_code: str) -> Optional[Tuple[str, List]]:
    """
    获取单个ETF的十大持有人数据

    Args:
        sec_code: ETF代码，如 512880

    Returns:
        (stat_date, [(rank, holder_name, holder_share, holder_pct), ...]) 或 None
    """
    url = f'http://stock.finance.sina.com.cn/fundInfo/view/FundInfo_JJCYR.php?symbol={sec_code}'
    session = _get_session()

    try:
        resp = session.get(url, timeout=15)
        if resp.status_code == 456:
            # IP被封，等待后重试一次
            import time
            time.sleep(30)
            resp = session.get(url, timeout=15)
        resp.encoding = 'gbk'

        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, 'html.parser')
        tables = soup.find_all('table')
        if len(tables) < 9:
            return None

        table = tables[8]
        rows = table.find_all('tr')
        if len(rows) < 4:
            return None

        # Row 1: 报告期日期（所有日期连在一起）
        row1_cells = rows[1].find_all('td')
        if not row1_cells:
            return None
        dates_text = row1_cells[0].get_text(strip=True)
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', dates_text)
        if not dates:
            return None
        stat_date = dates[0]  # 最新一期报告期

        # Row 3: 完整的10个持有人数据（每行4格：序号、名称、份额、占比）
        row3_cells = rows[3].find_all('td')
        if len(row3_cells) < 40:  # 不足10个持有人
            return None

        holders = []
        for i in range(0, len(row3_cells), 4):
            chunk = row3_cells[i:i+4]
            if len(chunk) != 4:
                continue
            rank_str = chunk[0].get_text(strip=True)
            if not rank_str.isdigit():
                continue
            rank = int(rank_str)
            if rank > 10:
                continue

            name = chunk[1].get_text(strip=True)
            share_str = chunk[2].get_text(strip=True).replace(',', '')
            pct_str = chunk[3].get_text(strip=True).replace(',', '')

            try:
                holder_share = float(share_str)
            except ValueError:
                holder_share = 0.0
            try:
                holder_pct = float(pct_str)
            except ValueError:
                holder_pct = 0.0

            holders.append((rank, name, holder_share, holder_pct))

        if len(holders) == 10:
            return stat_date, holders
        return None

    except Exception:
        return None


def fetch_all_holders(sec_codes: List[str] = None, max_workers: int = 5) -> dict:
    """
    批量获取ETF十大持有人数据

    Args:
        sec_codes: ETF代码列表，None则从数据库读取所有上交所ETF
        max_workers: 最大并发数

    Returns:
        {sec_code: (stat_date, holders_list), ...}
    """
    if sec_codes is None:
        conn = get_connection()
        cursor = conn.cursor()
        # 获取所有ETF代码（优先从etf_info）
        cursor.execute("SELECT sec_code FROM etf_info")
        codes = [row[0] for row in cursor.fetchall()]
        # 如果etf_info为空，从daily_share获取
        if not codes:
            cursor.execute("SELECT DISTINCT sec_code FROM etf_daily_share")
            codes = [row[0] for row in cursor.fetchall()]
        conn.close()
        # 只保留上交所ETF（51/58/50/56/59/60开头）
        sec_codes = [c for c in codes if c and c.startswith(('51', '58', '50', '56', '59', '60'))]

    results = {}
    total = len(sec_codes)
    done = 0
    failed = 0

    def worker(code):
        result = fetch_top_holders(code)
        return code, result

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(worker, code): code for code in sec_codes}
        for future in as_completed(futures):
            code, result = future.result()
            done += 1
            if result:
                results[code] = result
            else:
                failed += 1

            if done % 50 == 0 or done == total:
                print(f'  Progress: {done}/{total} | Success: {len(results)} | Failed: {failed}', flush=True)

    return results


def update_holders() -> int:
    """
    更新所有ETF十大持有人数据到数据库

    Returns:
        更新了多少只ETF的数据
    """
    conn = init_db()
    print('Fetching ETF top 10 holders from Sina Finance...')

    results = fetch_all_holders()

    saved = 0
    for sec_code, (stat_date, holders) in results.items():
        save_holders_to_db(conn, sec_code, stat_date, holders)
        saved += 1

    conn.close()
    print(f'Done: {saved} ETFs holders data saved')
    return saved


if __name__ == '__main__':
    update_holders()
