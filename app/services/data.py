import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, timedelta
import json

class StockDataService:
    def __init__(self):
        # 正しいティッカーシンボルを設定
        self.ticker = "^N225"  # 日経平均の標準的なティッカーシンボル
        # バックアップティッカー
        self.backup_tickers = ["^NKX", "NKY", "NIKKEI225.INDX", "NIKKEI225"]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def get_nikkei_data(self, period="1y"):
        """日経平均の株価データを取得"""
        try:
            # 期間から日付範囲を計算
            end_date = datetime.now()
            if period == "1mo":
                start_date = end_date - timedelta(days=30)
            elif period == "3mo":
                start_date = end_date - timedelta(days=90)
            elif period == "6mo":
                start_date = end_date - timedelta(days=180)
            elif period == "1y":
                start_date = end_date - timedelta(days=365)
            elif period == "2y":
                start_date = end_date - timedelta(days=365*2)
            elif period == "5y":
                start_date = end_date - timedelta(days=365*5)
            elif period == "10y":
                start_date = end_date - timedelta(days=365*10)
            elif period == "max":
                start_date = datetime(1990, 1, 1)
            else:
                start_date = end_date - timedelta(days=365)
            
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            print(f"検索期間: {start_str} から {end_str}")
            
            # YFinance APIを使用する場合は期間パラメータを直接使用
            print(f"Yahoo Finance API経由でティッカー {self.ticker} からデータ取得を試みています...")
            data = yf.download(self.ticker, start=start_str, end=end_str)
            
            print(f"取得データサイズ: {len(data)}")
            
            if len(data) > 0:
                return data
            
            # 最初の方法が失敗した場合、バックアップティッカーを試す
            for backup in self.backup_tickers:
                print(f"バックアップティッカー {backup} からデータ取得を試みています...")
                data = yf.download(backup, period=period)
                if len(data) > 0:
                    return data
            
            # 方法2: Stooq.comからデータ取得
            print("代替ソースからデータ取得を試みています...")
            try:
                # Stooq.comのCSVエンドポイント
                start_str_stooq = start_date.strftime('%Y%m%d')  # Stooq用フォーマット（YYYYMMDDが必要）
                end_str_stooq = end_date.strftime('%Y%m%d')  # Stooq用フォーマット
                url = f"https://stooq.com/q/d/l/?s=^nkx&d1={start_str_stooq}&d2={end_str_stooq}&i=d"
                
                print(f"Stooqからデータ取得: {url}")
                df = pd.read_csv(url)
                if len(df) > 0:
                    df['Date'] = pd.to_datetime(df['Date'])
                    df.set_index('Date', inplace=True)
                    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                    print(f"Stooqからデータ取得成功: {len(df)}行")
                    return df
            except Exception as e:
                print(f"Stooqからのデータ取得エラー: {e}")
            
            # すべての方法が失敗した場合
            print("すべてのデータソースからの取得に失敗。サンプルデータを生成します。")
            return self._get_sample_data(period)
            
        except Exception as e:
            print(f"データ取得エラー: {e}")
            return self._get_sample_data(period)
    
    def _get_sample_data(self, period="1y"):
        """期間に応じたサンプルデータを生成"""
        # 期間に基づいて日付範囲を計算
        end = datetime.now()
        
        # 期間に基づいて開始日を設定
        if period == "1mo":
            start = end - timedelta(days=30)
        elif period == "3mo":
            start = end - timedelta(days=90)
        elif period == "6mo":
            start = end - timedelta(days=180)
        elif period == "2y":
            start = end - timedelta(days=365*2)
        elif period == "5y":
            start = end - timedelta(days=365*5)
        elif period == "10y":
            start = end - timedelta(days=365*10)
        elif period == "max":
            start = datetime(1990, 1, 1)
        else:  # デフォルト1年
            start = end - timedelta(days=365)
        
        # 営業日のみの日付範囲を生成
        dates = pd.date_range(start=start, end=end, freq='B')
        
        # 簡易的な株価データを生成
        import random
        base = 30000
        prices = [base]
        for _ in range(1, len(dates)):
            # 長期間の場合はトレンドをより現実的に
            if period in ["5y", "10y", "max"]:
                change = random.uniform(-200, 250)  # より大きなトレンドの可能性
            else:
                change = random.uniform(-500, 500)
            prices.append(max(10000, min(50000, prices[-1] + change)))
        
        df = pd.DataFrame({
            'Open': prices,
            'High': [p + random.uniform(0, 200) for p in prices],
            'Low': [p - random.uniform(0, 200) for p in prices],
            'Close': prices,
            'Volume': [random.randint(1000000, 5000000) for _ in prices]
        }, index=dates)
        
        return df
    
    def process_data(self, data):
        """データの前処理"""
        # 必要に応じてデータクリーニングを行う
        return data.dropna() 