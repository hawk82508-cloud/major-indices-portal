import os
import re
import sys
import json
import datetime
import requests
import pandas as pd
import numpy as np

INDEX_CONFIGS = {
    'TAIEX': {
        'yahoo_symbols': ['%5ETWII'],
        'stooq_symbols': ['^twi'],
        'cnbc_symbol': None,
        'is_twse': True,
        'is_cbc_fx': False,
        'is_crypto': False,
        'is_gold': False,
        'tz_offset_hours': 8,
        'weekly_friday_label': False,
        'skip_weekends': True,
        'digits': 2
    },
    'DJI': {
        'yahoo_symbols': ['%5EDJI'],
        'stooq_symbols': ['^dji'],
        'cnbc_symbol': '.DJI',
        'is_twse': False,
        'is_cbc_fx': False,
        'is_crypto': False,
        'is_gold': False,
        'tz_offset_hours': -4,
        'weekly_friday_label': True,
        'skip_weekends': True,
        'digits': 2
    },
    'SPX': {
        'yahoo_symbols': ['%5EGSPC'],
        'stooq_symbols': ['^spx'],
        'cnbc_symbol': '.SPX',
        'is_twse': False,
        'is_cbc_fx': False,
        'is_crypto': False,
        'is_gold': False,
        'tz_offset_hours': -4,
        'weekly_friday_label': True,
        'skip_weekends': True,
        'digits': 2
    },
    'NASDAQ': {
        'yahoo_symbols': ['%5EIXIC'],
        'stooq_symbols': ['^ndq'],
        'cnbc_symbol': '.IXIC',
        'is_twse': False,
        'is_cbc_fx': False,
        'is_crypto': False,
        'is_gold': False,
        'tz_offset_hours': -4,
        'weekly_friday_label': True,
        'skip_weekends': True,
        'digits': 2
    },
    'SOX': {
        'yahoo_symbols': ['%5ESOX'],
        'stooq_symbols': ['^sox'],
        'cnbc_symbol': '.SOX',
        'is_twse': False,
        'is_cbc_fx': False,
        'is_crypto': False,
        'is_gold': False,
        'tz_offset_hours': -4,
        'weekly_friday_label': True,
        'skip_weekends': True,
        'digits': 2
    },
    'DXY': {
        'yahoo_symbols': ['DX-Y.NYB', 'DX%3DF'],
        'stooq_symbols': ['dx.f', '^dxy'],
        'cnbc_symbol': '.DXY',
        'is_twse': False,
        'is_cbc_fx': False,
        'is_crypto': False,
        'is_gold': False,
        'tz_offset_hours': -4,
        'weekly_friday_label': True,
        'skip_weekends': True,
        'digits': 2
    },
    'USDTWD': {
        'yahoo_symbols': ['TWD=X', 'USDTWD=X'],
        'stooq_symbols': ['usdtwd'],
        'cnbc_symbol': None,
        'is_twse': False,
        'is_cbc_fx': True,
        'is_crypto': False,
        'is_gold': False,
        'tz_offset_hours': 8,
        'weekly_friday_label': True,
        'skip_weekends': True,
        'digits': 3
    },
    'BTC': {
        'yahoo_symbols': ['BTC-USD'],
        'stooq_symbols': ['btc.v', 'btcusd'],
        'cnbc_symbol': None,
        'is_twse': False,
        'is_cbc_fx': False,
        'is_crypto': True,
        'is_gold': False,
        'tz_offset_hours': 0,
        'weekly_friday_label': False,
        'skip_weekends': False,
        'digits': 2
    },
    'GOLD': {
        'yahoo_symbols': ['XAUUSD%3DX', 'GC%3DF'],
        'stooq_symbols': ['xauusd'],
        'cnbc_symbol': 'XAU%3D',
        'is_twse': False,
        'is_cbc_fx': False,
        'is_crypto': False,
        'is_gold': True,
        'tz_offset_hours': -4,
        'weekly_friday_label': True,
        'skip_weekends': True,
        'digits': 2
    }
}

HTML_FILES = [
    'index.html',
    '各大指數高低控統整_多週期與跨週期前瞻雙軌通道分析系統_v2.0.html'
]

def fetch_cbc_closing_rate():
    """Fetch official Central Bank of Taiwan (Taipei Forex Inc.) interbank closing rate if available."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    try:
        url = "https://www.cbc.gov.tw/tw/lp-645-1.html"
        r = requests.get(url, headers=headers, timeout=12)
        if r.status_code == 200:
            m = re.search(r'(202\d)/(\d{1,2})/(\d{1,2})\s*(?:</[^>]+>\s*)*(\d{2}\.\d{2,4})', r.text)
            if m:
                y, mo, d, val = m.groups()
                dt_str = f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
                return dt_str, round(float(val), 3)
    except Exception as e:
        print(f"[USDTWD] CBC Official Rate Notice: {e}")
    return None, None

def fetch_recent_bars(sym, cfg):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*'
    }
    digits = cfg.get('digits', 2)
    bars = []

    cbc_date, cbc_close = (None, None)
    if cfg.get('is_cbc_fx'):
        cbc_date, cbc_close = fetch_cbc_closing_rate()

    # For GOLD, prefer Stooq xauusd first for pure Spot Gold USD/oz before Yahoo
    if cfg.get('is_gold'):
        for stooq_sym in cfg.get('stooq_symbols', []):
            try:
                s_url = f"https://stooq.com/q/d/l/?s={stooq_sym}&i=d"
                r = requests.get(s_url, headers=headers, timeout=12)
                if r.status_code == 200 and 'Date' in r.text:
                    lines = [line.strip() for line in r.text.strip().split('\n') if line.strip()]
                    for line in lines[1:][-30:]:
                        parts = line.split(',')
                        if len(parts) >= 5:
                            d_str = parts[0]
                            d_dt = datetime.datetime.strptime(d_str, '%Y-%m-%d').date()
                            if cfg.get('skip_weekends', True) and d_dt.weekday() >= 5:
                                continue
                            o, h, l, c = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                            v = float(parts[5]) if len(parts) > 5 and parts[5] != '' else 0.0
                            bars.append({
                                '時間': d_str,
                                '開盤價': round(o, digits),
                                '最高價': round(max(h, o, c), digits),
                                '最低價': round(min(l, o, c), digits),
                                '收盤價': round(c, digits),
                                '成交量': round(v / 1000.0, 2) if v > 0 else 0.0
                            })
                    if bars:
                        print(f"[{sym}] Stooq ({stooq_sym}): retrieved {len(bars)} recent bars, latest={bars[-1]['時間']} Close={bars[-1]['收盤價']}")
                        return bars
            except Exception as e:
                print(f"[{sym}] Stooq ({stooq_sym}) Notice: {e}")

    # Engine 1: Yahoo Finance Global CDN (query1 & query2 fallback)
    for y_sym in cfg.get('yahoo_symbols', []):
        for host in ['query1.finance.yahoo.com', 'query2.finance.yahoo.com']:
            try:
                y_url = f"https://{host}/v8/finance/chart/{y_sym}?interval=1d&range=1mo"
                r = requests.get(y_url, headers=headers, timeout=12)
                if r.status_code == 200:
                    res = r.json()
                    result = res['chart']['result'][0]
                    timestamps = result.get('timestamp', [])
                    quote = result['indicators']['quote'][0]
                    if cfg.get('is_crypto'):
                        tz_info = datetime.timezone.utc
                    elif cfg.get('is_cbc_fx') or cfg.get('is_twse'):
                        tz_info = datetime.timezone(datetime.timedelta(hours=8))
                    else:
                        gmtoffset = result.get('meta', {}).get('gmtoffset', cfg['tz_offset_hours'] * 3600)
                        tz_info = datetime.timezone(datetime.timedelta(seconds=gmtoffset))

                    for i in range(len(timestamps)):
                        c = quote['close'][i]
                        o = quote['open'][i]
                        h = quote['high'][i]
                        l = quote['low'][i]
                        v = quote.get('volume', [0])[i] if quote.get('volume') else 0
                        if c is not None and o is not None and h is not None and l is not None and not np.isnan(c):
                            d_dt = datetime.datetime.fromtimestamp(timestamps[i], tz=tz_info).date()
                            if cfg.get('skip_weekends', True) and d_dt.weekday() >= 5:
                                continue
                            d_str = d_dt.strftime('%Y-%m-%d')
                            c_val = cbc_close if (cbc_date == d_str and cbc_close is not None) else float(c)
                            o_val = float(o)
                            h_val = max(float(h), o_val, float(c), c_val)
                            l_val = min(float(l), o_val, float(c), c_val)
                            div_factor = 1000.0 if cfg.get('is_gold') else 100000000.0
                            vol_val = 0.0 if cfg.get('is_cbc_fx') else (round(float(v) / div_factor, 2) if v else 0.0)
                            bars.append({
                                '時間': d_str,
                                '開盤價': round(o_val, digits),
                                '最高價': round(h_val, digits),
                                '最低價': round(l_val, digits),
                                '收盤價': round(c_val, digits),
                                '成交量': vol_val
                            })
                    if bars:
                        print(f"[{sym}] Yahoo Finance ({host}/{y_sym}): retrieved {len(bars)} recent bars, latest={bars[-1]['時間']} Close={bars[-1]['收盤價']}")
                        return bars
            except Exception as e:
                print(f"[{sym}] Yahoo Finance ({host}/{y_sym}) Notice: {e}")

    # Engine 2 (Crypto): Binance & CoinGecko Fallback for BTC
    if cfg.get('is_crypto'):
        for b_host in ['https://data-api.binance.vision', 'https://api.binance.com']:
            try:
                b_url = f"{b_host}/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=14"
                r = requests.get(b_url, headers=headers, timeout=12)
                if r.status_code == 200:
                    klines = r.json()
                    for k in klines:
                        d_dt = datetime.datetime.fromtimestamp(int(k[0]) / 1000.0, tz=datetime.timezone.utc).date()
                        d_str = d_dt.strftime('%Y-%m-%d')
                        o, h, l, c = float(k[1]), float(k[2]), float(k[3]), float(k[4])
                        q_vol = float(k[7])
                        bars.append({
                            '時間': d_str,
                            '開盤價': round(o, digits),
                            '最高價': round(h, digits),
                            '最低價': round(l, digits),
                            '收盤價': round(c, digits),
                            '成交量': round(q_vol / 100000000.0, 2)
                        })
                    if bars:
                        print(f"[{sym}] Binance ({b_host}): retrieved {len(bars)} bars, latest={bars[-1]['時間']} Close={bars[-1]['收盤價']}")
                        return bars
            except Exception as e:
                print(f"[{sym}] Binance ({b_host}) Notice: {e}")

        try:
            cg_url = "https://api.coingecko.com/api/v3/coins/bitcoin/ohlc?vs_currency=usd&days=14"
            r = requests.get(cg_url, headers=headers, timeout=12)
            if r.status_code == 200:
                data = r.json()
                for item in data:
                    d_dt = datetime.datetime.fromtimestamp(item[0] / 1000.0, tz=datetime.timezone.utc).date()
                    d_str = d_dt.strftime('%Y-%m-%d')
                    bars.append({
                        '時間': d_str,
                        '開盤價': round(float(item[1]), digits),
                        '最高價': round(float(item[2]), digits),
                        '最低價': round(float(item[3]), digits),
                        '收盤價': round(float(item[4]), digits),
                        '成交量': 0.0
                    })
                if bars:
                    print(f"[{sym}] CoinGecko: retrieved {len(bars)} bars, latest={bars[-1]['時間']} Close={bars[-1]['收盤價']}")
                    return bars
        except Exception as e:
            print(f"[{sym}] CoinGecko Notice: {e}")

    # Engine 3: Stooq International Financial Data Feed
    for stooq_sym in cfg.get('stooq_symbols', []):
        try:
            s_url = f"https://stooq.com/q/d/l/?s={stooq_sym}&i=d"
            r = requests.get(s_url, headers=headers, timeout=12)
            if r.status_code == 200 and 'Date' in r.text:
                lines = [line.strip() for line in r.text.strip().split('\n') if line.strip()]
                for line in lines[1:][-30:]:
                    parts = line.split(',')
                    if len(parts) >= 5:
                        d_str = parts[0]
                        o, h, l, c = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                        v = float(parts[5]) if len(parts) > 5 and parts[5] != '' else 0.0
                        c_val = cbc_close if (cbc_date == d_str and cbc_close is not None) else c
                        bars.append({
                            '時間': d_str,
                            '開盤價': round(o, digits),
                            '最高價': round(max(h, o, c, c_val), digits),
                            '最低價': round(min(l, o, c, c_val), digits),
                            '收盤價': round(c_val, digits),
                            '成交量': round(v / 100000000.0, 2) if v > 0 else 0.0
                        })
                if bars:
                    print(f"[{sym}] Stooq ({stooq_sym}): retrieved {len(bars)} recent bars, latest={bars[-1]['時間']} Close={bars[-1]['收盤價']}")
                    return bars
        except Exception as e:
            print(f"[{sym}] Stooq ({stooq_sym}) Notice: {e}")

    # Engine 4: TWSE / CBC / CNBC / GoldPrice.org Direct Fallback
    if cfg.get('is_twse'):
        try:
            tz_taipei = datetime.timezone(datetime.timedelta(hours=8))
            today_dt = datetime.datetime.now(tz=tz_taipei).date()
            today_str = today_dt.strftime('%Y%m%d')
            twse_url = f"https://www.twse.com.tw/exchangeReport/FMTQIK?response=json&date={today_str}"
            r = requests.get(twse_url, headers=headers, timeout=12)
            if r.status_code == 200:
                data = r.json()
                if 'data' in data and len(data['data']) > 0:
                    last_row = data['data'][-1]
                    close_p = float(str(last_row[4]).replace(',', ''))
                    amt_val = float(str(last_row[2]).replace(',', '')) / 100000000.0
                    bars.append({
                        '時間': today_dt.strftime('%Y-%m-%d'),
                        '開盤價': round(close_p, digits),
                        '最高價': round(close_p, digits),
                        '最低價': round(close_p, digits),
                        '收盤價': round(close_p, digits),
                        '成交量': round(amt_val, 2)
                    })
                    return bars
        except Exception as e:
            print(f"[{sym}] TWSE Notice: {e}")
    elif cfg.get('is_cbc_fx') and cbc_date and cbc_close:
        bars.append({
            '時間': cbc_date,
            '開盤價': round(cbc_close, digits),
            '最高價': round(cbc_close + 0.035, digits),
            '最低價': round(cbc_close - 0.035, digits),
            '收盤價': round(cbc_close, digits),
            '成交量': 0.0
        })
        return bars
    elif cfg.get('cnbc_symbol'):
        try:
            cnbc_url = f"https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols={cfg['cnbc_symbol']}&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=1&output=json&events=1"
            r = requests.get(cnbc_url, headers=headers, timeout=12)
            if r.status_code == 200:
                q = r.json()['FormattedQuoteResult']['FormattedQuote'][0]
                c = float(str(q['last']).replace(',', ''))
                o = float(str(q.get('open', c)).replace(',', ''))
                h = float(str(q.get('high', c)).replace(',', ''))
                l = float(str(q.get('low', c)).replace(',', ''))
                tz_ny = datetime.timezone(datetime.timedelta(hours=-4))
                d_dt = datetime.datetime.now(tz=tz_ny).date()
                if cfg.get('skip_weekends', True):
                    while d_dt.weekday() >= 5:
                        d_dt -= datetime.timedelta(days=1)
                d_str = d_dt.strftime('%Y-%m-%d')
                bars.append({
                    '時間': d_str,
                    '開盤價': round(o, digits),
                    '最高價': round(max(h, o, c), digits),
                    '最低價': round(min(l, o, c), digits),
                    '收盤價': round(c, digits),
                    '成交量': 0.0
                })
                return bars
        except Exception as e:
            print(f"[{sym}] CNBC Notice: {e}")

    if cfg.get('is_gold'):
        try:
            gp_url = "https://data-asg.goldprice.org/dbXRates/USD"
            r = requests.get(gp_url, headers=headers, timeout=12)
            if r.status_code == 200:
                items = r.json().get('items', [])
                if items:
                    it = items[0]
                    c = float(it['xauPrice'])
                    o = float(it.get('xauClose', c))
                    h = max(o, c) + abs(c - o) * 0.35
                    l = min(o, c) - abs(c - o) * 0.35
                    tz_ny = datetime.timezone(datetime.timedelta(hours=-4))
                    d_dt = datetime.datetime.now(tz=tz_ny).date()
                    while d_dt.weekday() >= 5:
                        d_dt -= datetime.timedelta(days=1)
                    d_str = d_dt.strftime('%Y-%m-%d')
                    bars.append({
                        '時間': d_str,
                        '開盤價': round(o, digits),
                        '最高價': round(h, digits),
                        '最低價': round(l, digits),
                        '收盤價': round(c, digits),
                        '成交量': 0.0
                    })
                    return bars
        except Exception as e:
            print(f"[{sym}] GoldPrice.org Notice: {e}")

    return bars

def update_single_index_csvs(sym, cfg):
    data_dir = os.path.join('data', sym)
    daily_csv = os.path.join(data_dir, 'raw_daily.csv')
    weekly_csv = os.path.join(data_dir, 'raw_weekly.csv')
    monthly_csv = os.path.join(data_dir, 'raw_monthly.csv')
    digits = cfg.get('digits', 2)

    if not os.path.exists(daily_csv):
        return

    recent_bars = fetch_recent_bars(sym, cfg)
    if not recent_bars:
        print(f"[{sym}] Notice: No live network data retrieved; calculating with existing CSV.")
        return

    daily_df = pd.read_csv(daily_csv)
    weekly_df = pd.read_csv(weekly_csv) if os.path.exists(weekly_csv) else None
    monthly_df = pd.read_csv(monthly_csv) if os.path.exists(monthly_csv) else None

    last_existing_date = str(daily_df.iloc[-1]['時間'])
    new_or_curr_bars = [b for b in recent_bars if str(b['時間']) >= last_existing_date]

    for bar in new_or_curr_bars:
        target_date = str(bar['時間'])
        if target_date not in daily_df['時間'].astype(str).values:
            prev_close = float(daily_df.iloc[-1]['收盤價'])
            chg = round(bar['收盤價'] - prev_close, digits)
            pct = round((chg / prev_close) * 100.0, 2) if prev_close else 0.0
            row_to_add = dict(bar)
            if '漲跌' in daily_df.columns:
                row_to_add['漲跌'] = chg
                row_to_add['漲跌幅'] = pct
            daily_df = pd.concat([daily_df, pd.DataFrame([row_to_add])], ignore_index=True)
            print(f"[{sym}] Appended new daily bar: {target_date} Close={bar['收盤價']} ({chg:+.{digits}f}, {pct:+.2f}%)")
        else:
            idx = daily_df[daily_df['時間'].astype(str) == target_date].index[0]
            prev_close = float(daily_df.iloc[idx - 1]['收盤價']) if idx > 0 else float(bar['開盤價'])
            daily_df.at[idx, '開盤價'] = round(float(bar['開盤價']), digits)
            daily_df.at[idx, '最高價'] = round(max(float(daily_df.at[idx, '最高價']), float(bar['最高價'])), digits)
            daily_df.at[idx, '最低價'] = round(min(float(daily_df.at[idx, '最低價']), float(bar['最低價'])), digits)
            daily_df.at[idx, '收盤價'] = round(float(bar['收盤價']), digits)
            if '漲跌' in daily_df.columns:
                chg = round(float(bar['收盤價']) - prev_close, digits)
                pct = round((chg / prev_close) * 100.0, 2) if prev_close else 0.0
                daily_df.at[idx, '漲跌'] = chg
                daily_df.at[idx, '漲跌幅'] = pct
            if bar.get('成交量', 0) > 0 and '成交量' in daily_df.columns:
                daily_df.at[idx, '成交量'] = bar['成交量']

        # Update Weekly CSV
        if weekly_df is not None:
            target_dt = datetime.datetime.strptime(target_date, '%Y-%m-%d').date()
            mon_dt = target_dt - datetime.timedelta(days=target_dt.weekday())
            fri_dt = mon_dt + datetime.timedelta(days=4)
            w_label_str = fri_dt.strftime('%Y-%m-%d') if cfg['weekly_friday_label'] else mon_dt.strftime('%Y-%m-%d')

            matched_w_idx = None
            for w_idx, r in weekly_df.iterrows():
                r_dt = datetime.datetime.strptime(str(r['時間']), '%Y-%m-%d').date()
                r_mon = r_dt - datetime.timedelta(days=r_dt.weekday())
                if r_mon == mon_dt:
                    matched_w_idx = w_idx
                    break

            if matched_w_idx is None:
                prev_w_close = float(weekly_df.iloc[-1]['收盤價'])
                chg = round(bar['收盤價'] - prev_w_close, digits)
                pct = round((chg / prev_w_close) * 100.0, 2) if prev_w_close else 0.0
                w_row = {
                    '時間': w_label_str,
                    '開盤價': round(float(bar['開盤價']), digits),
                    '最高價': round(float(bar['最高價']), digits),
                    '最低價': round(float(bar['最低價']), digits),
                    '收盤價': round(float(bar['收盤價']), digits),
                    '成交量': bar.get('成交量', 0.0)
                }
                if '漲跌' in weekly_df.columns:
                    w_row['漲跌'] = chg
                    w_row['漲跌幅'] = pct
                weekly_df = pd.concat([weekly_df, pd.DataFrame([w_row])], ignore_index=True)
            else:
                prev_w_close = float(weekly_df.iloc[matched_w_idx - 1]['收盤價']) if matched_w_idx > 0 else float(weekly_df.at[matched_w_idx, '開盤價'])
                weekly_df.at[matched_w_idx, '最高價'] = round(max(float(weekly_df.at[matched_w_idx, '最高價']), float(bar['最高價'])), digits)
                weekly_df.at[matched_w_idx, '最低價'] = round(min(float(weekly_df.at[matched_w_idx, '最低價']), float(bar['最低價'])), digits)
                weekly_df.at[matched_w_idx, '收盤價'] = round(float(bar['收盤價']), digits)
                if '漲跌' in weekly_df.columns:
                    chg = round(float(bar['收盤價']) - prev_w_close, digits)
                    pct = round((chg / prev_w_close) * 100.0, 2) if prev_w_close else 0.0
                    weekly_df.at[matched_w_idx, '漲跌'] = chg
                    weekly_df.at[matched_w_idx, '漲跌幅'] = pct

        # Update Monthly CSV
        if monthly_df is not None:
            ym_str = target_date[:7]
            m_matches = monthly_df[monthly_df['時間'].astype(str).str.startswith(ym_str)].index
            if len(m_matches) > 0:
                m_idx = m_matches[0]
                prev_m_close = float(monthly_df.iloc[m_idx - 1]['收盤價']) if m_idx > 0 else float(monthly_df.at[m_idx, '開盤價'])
                monthly_df.at[m_idx, '最高價'] = round(max(float(monthly_df.at[m_idx, '最高價']), float(bar['最高價'])), digits)
                monthly_df.at[m_idx, '最低價'] = round(min(float(monthly_df.at[m_idx, '最低價']), float(bar['最低價'])), digits)
                monthly_df.at[m_idx, '收盤價'] = round(float(bar['收盤價']), digits)
                if '漲跌' in monthly_df.columns:
                    chg = round(float(bar['收盤價']) - prev_m_close, digits)
                    pct = round((chg / prev_m_close) * 100.0, 2) if prev_m_close else 0.0
                    monthly_df.at[m_idx, '漲跌'] = chg
                    monthly_df.at[m_idx, '漲跌幅'] = pct
            else:
                prev_m_close = float(monthly_df.iloc[-1]['收盤價'])
                chg = round(bar['收盤價'] - prev_m_close, digits)
                pct = round((chg / prev_m_close) * 100.0, 2) if prev_m_close else 0.0
                m_row = {
                    '時間': f"{ym_str}-01",
                    '開盤價': round(float(bar['開盤價']), digits),
                    '最高價': round(float(bar['最高價']), digits),
                    '最低價': round(float(bar['最低價']), digits),
                    '收盤價': round(float(bar['收盤價']), digits),
                    '成交量': bar.get('成交量', 0.0)
                }
                if '漲跌' in monthly_df.columns:
                    m_row['漲跌'] = chg
                    m_row['漲跌幅'] = pct
                monthly_df = pd.concat([monthly_df, pd.DataFrame([m_row])], ignore_index=True)

    daily_df.to_csv(daily_csv, index=False)
    if weekly_df is not None:
        weekly_df.to_csv(weekly_csv, index=False)
    if monthly_df is not None:
        monthly_df.to_csv(monthly_csv, index=False)

def compute_12_period(df, lookback_path, digits):
    if lookback_path and os.path.exists(lookback_path):
        lb_df = pd.read_csv(lookback_path)
        combined = pd.concat([lb_df, df], ignore_index=True)
        combined['high_12'] = combined['最高價'].rolling(12, min_periods=1).max().round(digits)
        combined['low_12'] = combined['最低價'].rolling(12, min_periods=1).min().round(digits)
        combined['point1'] = ((combined['high_12'] * 2 + combined['low_12']) / 3.0).round(digits)
        combined['point2'] = ((combined['high_12'] + combined['low_12'] * 2) / 3.0).round(digits)
        return combined.iloc[len(lb_df):].reset_index(drop=True)
    else:
        out = df.copy()
        out['high_12'] = out['最高價'].rolling(12).max().round(digits)
        out['low_12'] = out['最低價'].rolling(12).min().round(digits)
        out['point1'] = ((out['high_12'] * 2 + out['low_12']) / 3.0).round(digits)
        out['point2'] = ((out['high_12'] + out['low_12'] * 2) / 3.0).round(digits)
        return out

def build_single_payload(sym, cfg):
    digits = cfg.get('digits', 2)
    data_dir = os.path.join('data', sym)
    daily_raw = pd.read_csv(os.path.join(data_dir, 'raw_daily.csv'))
    weekly_raw = pd.read_csv(os.path.join(data_dir, 'raw_weekly.csv'))
    monthly_raw = pd.read_csv(os.path.join(data_dir, 'raw_monthly.csv'))

    daily_df = compute_12_period(daily_raw, os.path.join(data_dir, 'lookback_daily.csv'), digits)
    weekly_df = compute_12_period(weekly_raw, os.path.join(data_dir, 'lookback_weekly.csv'), digits)
    monthly_df = compute_12_period(monthly_raw, os.path.join(data_dir, 'lookback_monthly.csv'), digits)

    weekly_lookup = []
    for idx, r in weekly_df.iterrows():
        w_dt = datetime.datetime.strptime(str(r['時間']), '%Y-%m-%d').date()
        mon_dt = w_dt - datetime.timedelta(days=w_dt.weekday())
        weekly_lookup.append({
            'start_date': mon_dt.strftime('%Y-%m-%d'),
            'high_12': float(r['high_12']) if not pd.isna(r['high_12']) else None,
            'low_12': float(r['low_12']) if not pd.isna(r['low_12']) else None,
            'point1': float(r['point1']) if not pd.isna(r['point1']) else None,
            'point2': float(r['point2']) if not pd.isna(r['point2']) else None
        })

    monthly_lookup = []
    for idx, r in monthly_df.iterrows():
        monthly_lookup.append({
            'ym': str(r['時間'])[:7],
            'start_date': str(r['時間']),
            'high_12': float(r['high_12']) if not pd.isna(r['high_12']) else None,
            'low_12': float(r['low_12']) if not pd.isna(r['low_12']) else None,
            'point1': float(r['point1']) if not pd.isna(r['point1']) else None,
            'point2': float(r['point2']) if not pd.isna(r['point2']) else None
        })

    def get_weekly_point(date_str):
        matched = None
        for w in weekly_lookup:
            if date_str >= w['start_date']:
                matched = w
            else:
                break
        if matched:
            return matched['point1'], matched['point2']
        return None, None

    def get_monthly_point(date_str):
        d_ym = date_str[:7]
        matched = None
        for m in monthly_lookup:
            if m['ym'] == d_ym:
                matched = m
                break
            elif date_str >= m['start_date']:
                matched = m
        if matched:
            return matched['point1'], matched['point2']
        return None, None

    daily_list = []
    multi_list = []

    for idx, r in daily_df.iterrows():
        d_str = str(r['時間'])
        p1_d = float(r['point1']) if not pd.isna(r['point1']) else None
        p2_d = float(r['point2']) if not pd.isna(r['point2']) else None
        h12_d = float(r['high_12']) if not pd.isna(r['high_12']) else None
        l12_d = float(r['low_12']) if not pd.isna(r['low_12']) else None

        w_p1, w_p2 = get_weekly_point(d_str)
        m_p1, m_p2 = get_monthly_point(d_str)

        prev_c = float(daily_df.iloc[idx - 1]['收盤價']) if idx > 0 else float(r['開盤價'])
        chg_val = round(float(r['漲跌']), digits) if '漲跌' in r and not pd.isna(r['漲跌']) else round(float(r['收盤價']) - prev_c, digits)
        chg_pct = round(float(r['漲跌幅']), 2) if '漲跌幅' in r and not pd.isna(r['漲跌幅']) else (round((chg_val / prev_c) * 100.0, 2) if prev_c else 0.0)

        item_base = {
            'date': d_str,
            'open': round(float(r['開盤價']), digits),
            'high': round(float(r['最高價']), digits),
            'low': round(float(r['最低價']), digits),
            'close': round(float(r['收盤價']), digits),
            'change': chg_val,
            'change_pct': chg_pct,
            'volume': float(r['成交量']) if '成交量' in r and not pd.isna(r['成交量']) else 0.0,
            'high_12': h12_d,
            'low_12': l12_d,
            'point1': p1_d,
            'point2': p2_d,
            'is_future': False
        }
        daily_list.append(item_base)
        multi_list.append({
            **item_base,
            'w_point1': w_p1,
            'w_point2': w_p2,
            'm_point1': m_p1,
            'm_point2': m_p2
        })

    weekly_list = []
    for idx, r in weekly_df.iterrows():
        prev_c = float(weekly_df.iloc[idx - 1]['收盤價']) if idx > 0 else float(r['開盤價'])
        chg_val = round(float(r['漲跌']), digits) if '漲跌' in r and not pd.isna(r['漲跌']) else round(float(r['收盤價']) - prev_c, digits)
        chg_pct = round(float(r['漲跌幅']), 2) if '漲跌幅' in r and not pd.isna(r['漲跌幅']) else (round((chg_val / prev_c) * 100.0, 2) if prev_c else 0.0)
        weekly_list.append({
            'label': str(r['時間']),
            'date': str(r['時間']),
            'open': round(float(r['開盤價']), digits),
            'high': round(float(r['最高價']), digits),
            'low': round(float(r['最低價']), digits),
            'close': round(float(r['收盤價']), digits),
            'change': chg_val,
            'change_pct': chg_pct,
            'volume': float(r['成交量']) if '成交量' in r and not pd.isna(r['成交量']) else 0.0,
            'high_12': float(r['high_12']) if not pd.isna(r['high_12']) else None,
            'low_12': float(r['low_12']) if not pd.isna(r['low_12']) else None,
            'point1': float(r['point1']) if not pd.isna(r['point1']) else None,
            'point2': float(r['point2']) if not pd.isna(r['point2']) else None,
            'is_future': False
        })

    monthly_list = []
    for idx, r in monthly_df.iterrows():
        prev_c = float(monthly_df.iloc[idx - 1]['收盤價']) if idx > 0 else float(r['開盤價'])
        chg_val = round(float(r['漲跌']), digits) if '漲跌' in r and not pd.isna(r['漲跌']) else round(float(r['收盤價']) - prev_c, digits)
        chg_pct = round(float(r['漲跌幅']), 2) if '漲跌幅' in r and not pd.isna(r['漲跌幅']) else (round((chg_val / prev_c) * 100.0, 2) if prev_c else 0.0)
        monthly_list.append({
            'month': str(r['時間'])[:7],
            'date': str(r['時間'])[:7],
            'open': round(float(r['開盤價']), digits),
            'high': round(float(r['最高價']), digits),
            'low': round(float(r['最低價']), digits),
            'close': round(float(r['收盤價']), digits),
            'change': chg_val,
            'change_pct': chg_pct,
            'volume': float(r['成交量']) if '成交量' in r and not pd.isna(r['成交量']) else 0.0,
            'high_12': float(r['high_12']) if not pd.isna(r['high_12']) else None,
            'low_12': float(r['low_12']) if not pd.isna(r['low_12']) else None,
            'point1': float(r['point1']) if not pd.isna(r['point1']) else None,
            'point2': float(r['point2']) if not pd.isna(r['point2']) else None,
            'is_future': False
        })

    last_11_d = daily_df.tail(11)
    h11_d = round(float(last_11_d['最高價'].max()), digits)
    l11_d = round(float(last_11_d['最低價'].min()), digits)
    p1_d_future = round((h11_d * 2 + l11_d) / 3.0, digits)
    p2_d_future = round((h11_d + l11_d * 2) / 3.0, digits)

    last_date = datetime.datetime.strptime(str(daily_df.iloc[-1]['時間']), '%Y-%m-%d').date()
    next_day = last_date + datetime.timedelta(days=1)
    if cfg.get('skip_weekends', True):
        while next_day.weekday() >= 5:
            next_day += datetime.timedelta(days=1)
    next_day_label = f"{next_day.strftime('%Y-%m-%d')} (次日預測)"

    daily_future = {
        'label': next_day_label,
        'date': next_day_label,
        'open': None, 'high': None, 'low': None, 'close': None, 'volume': None,
        'high_12': h11_d,
        'low_12': l11_d,
        'point1': p1_d_future,
        'point2': p2_d_future,
        'is_future': True
    }

    last_11_w = weekly_df.tail(11)
    h11_w = round(float(last_11_w['最高價'].max()), digits)
    l11_w = round(float(last_11_w['最低價'].min()), digits)
    p1_w_future = round((h11_w * 2 + l11_w) / 3.0, digits)
    p2_w_future = round((h11_w + l11_w * 2) / 3.0, digits)

    weekly_future = {
        'label': '次週預測',
        'date': '次週預測',
        'open': None, 'high': None, 'low': None, 'close': None, 'volume': None,
        'high_12': h11_w,
        'low_12': l11_w,
        'point1': p1_w_future,
        'point2': p2_w_future,
        'is_future': True
    }

    last_11_m = monthly_df.tail(11)
    h11_m = round(float(last_11_m['最高價'].max()), digits)
    l11_m = round(float(last_11_m['最低價'].min()), digits)
    p1_m_future = round((h11_m * 2 + l11_m) / 3.0, digits)
    p2_m_future = round((h11_m + l11_m * 2) / 3.0, digits)

    monthly_future = {
        'label': '次月預測',
        'month': '次月預測',
        'date': '次月預測',
        'open': None, 'high': None, 'low': None, 'close': None, 'volume': None,
        'high_12': h11_m,
        'low_12': l11_m,
        'point1': p1_m_future,
        'point2': p2_m_future,
        'is_future': True
    }

    multi_future = {
        'label': f"{next_day.strftime('%Y-%m-%d')} (次期前瞻)",
        'date': f"{next_day.strftime('%Y-%m-%d')} (次期前瞻)",
        'open': None, 'high': None, 'low': None, 'close': None, 'volume': None,
        'high_12': h11_d,
        'low_12': l11_d,
        'point1': p1_d_future,
        'point2': p2_d_future,
        'w_point1': p1_w_future,
        'w_point2': p2_w_future,
        'm_point1': p1_m_future,
        'm_point2': p2_m_future,
        'is_future': True
    }

    return {
        'daily': daily_list,
        'daily_future': daily_future,
        'weekly': weekly_list,
        'weekly_future': weekly_future,
        'monthly': monthly_list,
        'monthly_future': monthly_future,
        'multi': multi_list,
        'multi_future': multi_future
    }

def main(skip_network=False):
    all_payloads = {}
    for sym, cfg in INDEX_CONFIGS.items():
        if not skip_network:
            update_single_index_csvs(sym, cfg)
        all_payloads[sym] = build_single_payload(sym, cfg)

    payloads_json = json.dumps(all_payloads, ensure_ascii=False)

    for hfile in HTML_FILES:
        if os.path.exists(hfile):
            with open(hfile, 'r', encoding='utf-8') as f:
                html = f.read()
            new_html = re.sub(
                r'const allIndicesPayloads = (\{.*?\});',
                lambda m: f'const allIndicesPayloads = {payloads_json};',
                html,
                flags=re.DOTALL
            )
            with open(hfile, 'w', encoding='utf-8') as f:
                f.write(new_html)
            print(f"Updated {hfile} successfully.")

if __name__ == '__main__':
    try:
        skip_net = '--offline' in sys.argv
        main(skip_network=skip_net)
    except Exception as e:
        print(f"Error in update_all_indices.py: {e}")
        sys.exit(0)
