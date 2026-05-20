"""
ETF数据获取模块 - 从上海证券交易所API拉取数据
"""
import urllib.request
import json
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional

try:
    from chinese_calendar import is_workday
except ImportError:
    def is_workday(date) -> bool:
        return date.weekday() < 5


def get_etf_market_code(sec_code: str) -> str:
    """
    根据ETF代码获取东方财富的市场代码

    Args:
        sec_code: ETF代码，如 510300

    Returns:
        东方财富格式的市场代码，如 "1.510300"（1=上海，0=深圳）
    """
    # 上海ETF代码以51/58/50开头
    sh_prefixes = ('51', '58', '50', '56', '59')
    if sec_code.startswith(sh_prefixes):
        return f"1.{sec_code}"
    else:
        return f"0.{sec_code}"


def fetch_etf_close_prices(sec_codes: List[str], dates: List[str]) -> Dict[str, Dict[str, float]]:
    """
    从新浪财经获取ETF收盘价数据

    Args:
        sec_codes: ETF代码列表
        dates: 日期列表

    Returns:
        {sec_code: {date: close_price}} 字典
    """
    if not sec_codes or not dates:
        return {}

    dates_set = set(dates)
    # 计算需要获取的历史数据天数（留一些余量）
    date_list = sorted(dates_set)
    days_needed = max(30, len(dates_set) + 10)  # 至少获取30天或所有日期

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://finance.sina.com.cn/'
    }

    result = {}

    for i, sec_code in enumerate(sec_codes):
        # 上海ETF用sh前缀，深圳ETF用sz前缀
        if sec_code.startswith(('51', '58', '50', '56', '59')):
            symbol = f'sh{sec_code}'
        else:
            symbol = f'sz{sec_code}'

        url = (f'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/'
               f'CN_MarketData.getKLineData?symbol={symbol}&scale=240&ma=5&datalen={days_needed}')

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

                sec_result = {}
                for item in data:
                    day = item.get('day', '')
                    close = item.get('close')
                    if day and close:
                        sec_result[day] = float(close)

                if sec_result:
                    result[sec_code] = sec_result

        except Exception:
            pass

        # 添加延迟避免触发反爬
        if i < len(sec_codes) - 1:
            time.sleep(0.3)

    return result


def fetch_etf_data(date_str: str) -> List[Dict[str, Any]]:
    """
    获取指定日期的全量ETF份额数据（自动处理分页）

    Args:
        date_str: 日期字符串，格式 YYYY-MM-DD

    Returns:
        ETF数据列表
    """
    all_results = []
    page_no = 1
    page_size = 100

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Referer': 'https://www.sse.com.cn/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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
        except Exception:
            break

    return all_results


def fetch_etf_expand_name(sec_codes: List[str]) -> Dict[str, str]:
    """
    从上交所接口获取ETF完整名称（含公司名）

    Args:
        sec_codes: ETF代码列表

    Returns:
        {sec_code: expand_name} 字典
    """
    if not sec_codes:
        return {}

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'Referer': 'https://www.sse.com.cn/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    sec_codes_str = ','.join(sec_codes)
    url = f'https://query.sse.com.cn/security/stock/queryExpandName.do?jsonCallBack=cb&secCodes={sec_codes_str}&_={int(time.time() * 1000)}'

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as response:
            text = response.read().decode('utf-8')
            json_str = text[text.index('(') + 1 : text.rindex(')')]
            data = json.loads(json_str)
            result = {}
            for item in data.get('result', []):
                if len(item) >= 2:
                    result[item[0]] = item[1]
            return result
    except Exception:
        return {}


def get_trading_days(days: int = 130) -> List[str]:
    """
    获取最近days个交易日的日期列表

    Args:
        days: 需要获取的交易日数量

    Returns:
        日期字符串列表
    """
    today = datetime.now()
    trading_days = []
    for i in range(days * 2):
        date = today - timedelta(days=i)
        if is_workday(date):
            trading_days.append(date.strftime('%Y-%m-%d'))
            if len(trading_days) >= days:
                break
    return trading_days


def fetch_data(days: int = 126, max_workers: int = 50) -> int:
    """
    采集数据（份额+收盘价）

    Args:
        days: 采集多少个交易日的数据
        max_workers: 最大并发数

    Returns:
        总共采集的记录数
    """
    from .database import init_db, save_to_db

    conn = init_db()
    trading_days = get_trading_days(days)
    print(f"Fetching {len(trading_days)} trading days data (with pagination)...")

    # 第一阶段：获取份额数据
    all_results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_etf_data, d): d for d in trading_days}
        for future in as_completed(futures):
            results = future.result()
            if results:
                all_results.extend(results)

    if not all_results:
        conn.close()
        print("No data fetched")
        return 0

    # 收集所有ETF代码和日期
    sec_codes = list(set(r['SEC_CODE'] for r in all_results))
    dates = list(set(r['STAT_DATE'] for r in all_results))
    print(f"Fetching close prices for {len(sec_codes)} ETFs over {len(dates)} days...")

    # 第二阶段：获取收盘价数据
    prices = fetch_etf_close_prices(sec_codes, dates)

    # 第三阶段：保存数据
    save_to_db(conn, all_results, prices)
    total = len(all_results)

    conn.close()
    print(f"Done: {total} records saved (with close prices)")
    return total


def update_full_names() -> int:
    """
    从上交所接口更新所有ETF的完整名称

    Returns:
        更新的数量
    """
    from .database import init_db, get_connection

    conn = init_db()
    cursor = conn.cursor()

    # 获取所有ETF代码
    cursor.execute('SELECT sec_code FROM etf_info')
    all_codes = [row[0] for row in cursor.fetchall()]

    if not all_codes:
        print('没有ETF数据，请先运行 fetch 命令')
        conn.close()
        return 0

    print(f'开始获取 {len(all_codes)} 只ETF的完整名称...')

    # 分批获取
    batch_size = 50
    all_expand_names = {}
    for i in range(0, len(all_codes), batch_size):
        batch = all_codes[i:i+batch_size]
        names = fetch_etf_expand_name(batch)
        all_expand_names.update(names)
        print(f'  已获取 {min(i+batch_size, len(all_codes))}/{len(all_codes)}')

    # 提取简称（去掉公司后缀）
    company_suffixes = {
        '华泰柏瑞', '易方达', '华夏', '南方', '广发', '建信', '招商', '国泰', '博时',
        '鹏华', '富国', '银华', '中金', '中信', '银河', '国联安', '华安', '汇添富',
        '工银', '平安', '兴业', '国寿', '大成', '嘉实', '景顺', '诺安', '长盛', '华宝',
        '中银', '海富通', '华商', '天弘', '泰康', '中欧', '兴全', '农银', '民生', '光大',
        '中邮', '交银', '浦银', '睿远', '香港', '国际', '先锋', '摩根', '野村',
        '法巴', '申万', '瑞银', '高盛', '美林', '贝莱德', '汇安', '华西', '万家',
        '恒生', '华鑫', '华福', '华龙', '华融', '国元', '国都', '国海', '国金', '国联',
        '华润', '华泰', '华宝', '华商', '华亿', '汇丰', '金信', '金鹰', '金元', '金塔',
        '开源', '凯石', '康力', '利得', '路博', '麦高', '美畅', '民享', '宁沪', '欧瑞',
        '磐安', '乾元', '趣时', '全威', '人保', '人福', '瑞士', '山西', '上汽', '深高',
        '石投', '首选', '双汇', '太保', '泰信', '天安', '天治', '同泰', '瓦尔多', '万利',
        '五矿', '西部', '西藏', '新华', '鑫元', '信达', '星徽', '兴银', '玄元', '循理',
        '亚太', '衍航', '阳光', '伊利', '银基', '英大', '永赢', '元葵', '远洋', '泽熙',
        '长江', '招银', '浙商', '正心', '中创', '中电', '中钢', '中国', '中航', '中沪',
        '中化', '中汇', '中建', '中村', '中配', '中燃', '中泰', '中天', '中铁', '中万',
        '中物', '中新', '中鑫', '中盐', '中衍', '中亿', '众安', '珠海', '朱雀', '准信',
        '左安', '民生加银', '申万菱信', '东财', '创金合信', 'DB', 'TOP', 'MSCI', 'AH'
    }

    def extract_short_name(full_name: str) -> str:
        if not full_name:
            return full_name
        for suffix in sorted(company_suffixes, key=len, reverse=True):
            if full_name.endswith(suffix):
                short = full_name[:-len(suffix)]
                if short.endswith('ETF') and not short.endswith('中国ETF'):
                    short = short[:-3]
                return short.rstrip('EFT')
        return full_name

    # 更新数据库
    updated = 0
    for code in all_codes:
        if code in all_expand_names:
            full_name = all_expand_names[code]
            short_name = extract_short_name(full_name)
            cursor.execute(
                'UPDATE etf_info SET sec_name = ?, full_name = ? WHERE sec_code = ?',
                (short_name, full_name, code)
            )
            updated += 1

    conn.commit()
    conn.close()
    print(f'完成，共更新 {updated} 只ETF名称')
    return updated
