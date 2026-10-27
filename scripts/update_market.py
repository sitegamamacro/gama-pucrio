import urllib.request
import json
import os
import sys

SYMBOLS = {
    'IBOV': '^BVSP',
    'SPX': '^GSPC',
    'BRENT': 'BZ=F',
    'GOLD': 'GC=F'
}

def fetch_market_data():
    cache = {}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for key, sym in SYMBOLS.items():
        url_5y = f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=5y'
        url_1d = f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=15m&range=1d'
        
        try:
            req_5y = urllib.request.Request(url_5y, headers=headers)
            req_1d = urllib.request.Request(url_1d, headers=headers)
            
            with urllib.request.urlopen(req_1d, timeout=15) as r_1d:
                data_1d = json.loads(r_1d.read().decode('utf-8'))
                res_1d = data_1d['chart']['result'][0]
                meta_1d = res_1d['meta']
                price = meta_1d['regularMarketPrice']
                prev = meta_1d.get('chartPreviousClose') or meta_1d.get('previousClose')
                day_chg = ((price - prev) / prev) * 100 if prev else 0.0

                ts_1d = res_1d.get('timestamp', [])
                quotes_1d = res_1d['indicators']['quote'][0].get('close', [])
                intraday = []
                for t, c in zip(ts_1d, quotes_1d):
                    if c is not None:
                        intraday.append({'t': t, 'c': round(c, 2)})

            with urllib.request.urlopen(req_5y, timeout=20) as r_5y:
                data_5y = json.loads(r_5y.read().decode('utf-8'))
                res_5y = data_5y['chart']['result'][0]
                timestamps = res_5y.get('timestamp', [])
                quotes = res_5y['indicators']['quote'][0]
                closes = quotes.get('close', [])

                points = []
                for t, c in zip(timestamps, closes):
                    if c is not None:
                        points.append({'t': t, 'c': round(c, 2)})

            cache[key] = {
                'price': round(price, 2),
                'pctChange': round(day_chg, 2),
                'previousClose': round(prev, 2) if prev else None,
                'intraday': intraday,
                'points': points
            }
            print(f"[{key}] Atualizado: {price:.2f} ({day_chg:+.2f}% no dia, {len(intraday)} pontos 1D, {len(points)} pontos históricos)")
        except Exception as e:
            print(f"[{key}] Erro ao buscar cotação: {e}", file=sys.stderr)

    if len(cache) == len(SYMBOLS):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out_path = os.path.join(repo_root, 'market_cache.json')
        with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(cache, f, separators=(',', ':'))
        print("market_cache.json gravado com sucesso.")
    else:
        print("Aviso: nem todos os ativos retornaram dados. Mantendo cache anterior para evitar corrupção.", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    fetch_market_data()
