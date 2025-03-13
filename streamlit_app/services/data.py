import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class StockDataService:
    def get_nikkei_data(self, period='1y'):
        # 実際のプロジェクトではYahoo Financeなどから実データを取得
        # ここではサンプルデータを返す
        end_date = datetime.now()
        
        if period == '1mo':
            days = 30
        elif period == '3mo':
            days = 90
        elif period == '6mo':
            days = 180
        elif period == '1y':
            days = 365
        elif period == '2y':
            days = 365 * 2
        elif period == '5y':
            days = 365 * 5
        elif period == '10y':
            days = 365 * 10
        else:  # max
            days = 365 * 20
        
        start_date = end_date - timedelta(days=days)
        dates = pd.date_range(start=start_date, end=end_date, freq='B')
        
        # トレンドを持つランダムなデータを生成
        base = 30000
        trend = np.linspace(0, 3000, len(dates))
        noise = np.random.normal(0, 500, len(dates))
        
        closes = base + trend + noise
        opens = closes - np.random.normal(0, 100, len(dates))
        highs = np.maximum(opens, closes) + np.random.normal(100, 50, len(dates))
        lows = np.minimum(opens, closes) - np.random.normal(100, 50, len(dates))
        volumes = np.random.normal(1000000, 200000, len(dates))
        
        df = pd.DataFrame({
            'Open': opens,
            'High': highs,
            'Low': lows,
            'Close': closes,
            'Volume': volumes
        }, index=dates)
        
        return df 