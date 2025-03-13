import pandas as pd
import numpy as np
import random

class TechnicalAnalysis:
    def calculate_rsi(self, df, period=14):
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, df, fast=12, slow=26, signal=9):
        exp1 = df['Close'].ewm(span=fast, adjust=False).mean()
        exp2 = df['Close'].ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        
        return pd.DataFrame({
            'MACD': macd,
            'Signal': signal_line,
            'Histogram': macd - signal_line
        })

class AdvancedAnalysis:
    def generate_market_analysis(self, df):
        # シンプルな分析結果を生成（実際のプロジェクトでは機械学習モデルなどを使用）
        latest_price = df['Close'].iloc[-1]
        rsi = TechnicalAnalysis().calculate_rsi(df).iloc[-1]
        
        actions = ['買い', '売り', '様子見']
        directions = ['上昇', '下降', '横ばい']
        
        # サンプル分析結果を返す
        return {
            'price': latest_price,
            'date': df.index[-1].strftime('%Y-%m-%d'),
            'recommendation': {
                'action': random.choice(actions),
                'confidence': random.choice(['高', '中', '低']),
                'explanation': '直近の価格動向と市場指標に基づく分析では、短期的には方向感が見られます。'
            },
            'predictions': {
                'short_term': {
                    'direction': random.choice(directions),
                    'prediction': random.uniform(-2.0, 2.0),
                    'confidence': random.uniform(0.5, 0.9)
                },
                'medium_term': {
                    'direction': random.choice(directions),
                    'prediction': random.uniform(-5.0, 5.0),
                    'confidence': random.uniform(0.4, 0.8)
                }
            },
            'indicators': {
                'rsi': rsi,
                'macd': random.uniform(-20, 20),
                'macd_signal': random.uniform(-20, 20),
                'adx': random.uniform(10, 30)
            },
            'market_condition': {
                'market_phase': random.choice(['強気相場', '弱気相場', '調整局面', '底打ち']),
                'trend_strength': random.choice(['強い', '中程度', '弱い']),
                'volatility_state': random.choice(['高い', '普通', '低い']),
                'market_sentiment': random.choice(['強気', '弱気', '中立'])
            }
        } 