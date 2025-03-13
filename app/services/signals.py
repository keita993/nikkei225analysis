import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class SignalService:
    def __init__(self, rsi_oversold=30, rsi_overbought=70):
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
    
    def generate_buy_signals(self, data, rsi, macd_data):
        """買いシグナルの生成"""
        signals = pd.DataFrame(index=data.index)
        signals['Price'] = data['Close']
        signals['RSI'] = rsi
        signals['MACD'] = macd_data['MACD']
        signals['Signal'] = macd_data['Signal']
        
        # RSIが売られすぎ（30以下）でMACDがシグナルラインを上抜けた場合に買いシグナル
        signals['RSI_Buy'] = (rsi < self.rsi_oversold) & (rsi.shift(1) < self.rsi_oversold)
        signals['MACD_Buy'] = (macd_data['MACD'] > macd_data['Signal']) & (macd_data['MACD'].shift(1) <= macd_data['Signal'].shift(1))
        
        # 両方の条件が揃った場合に強い買いシグナル
        signals['Strong_Buy'] = signals['RSI_Buy'] & signals['MACD_Buy']
        
        return signals 

    def generate_market_analysis(self, data, rsi, macd_data, trend_data, volatility_data):
        """市場分析レポートの生成"""
        # 基本情報
        latest_price = data['Close'].iloc[-1]
        latest_date = data.index[-1]
        one_day_change = (data['Close'].iloc[-1] / data['Close'].iloc[-2] - 1) * 100
        one_week_change = (data['Close'].iloc[-1] / data['Close'].iloc[-6] - 1) * 100 if len(data) > 5 else None
        one_month_change = (data['Close'].iloc[-1] / data['Close'].iloc[-23] - 1) * 100 if len(data) > 22 else None
        
        # RSI判定
        rsi_value = rsi.iloc[-1]
        if rsi_value <= 30:
            rsi_signal = "買い (売られすぎ)"
        elif rsi_value >= 70:
            rsi_signal = "売り (買われすぎ)"
        else:
            rsi_signal = "中立"
        
        # MACD判定
        macd_value = macd_data['MACD'].iloc[-1]
        signal_value = macd_data['Signal'].iloc[-1]
        
        if macd_value > signal_value and macd_data['MACD'].iloc[-2] <= macd_data['Signal'].iloc[-2]:
            macd_signal = "買い (MACD上抜け)"
        elif macd_value < signal_value and macd_data['MACD'].iloc[-2] >= macd_data['Signal'].iloc[-2]:
            macd_signal = "売り (MACD下抜け)"
        elif macd_value > signal_value:
            macd_signal = "弱い買い (MACD > シグナル)"
        elif macd_value < signal_value:
            macd_signal = "弱い売り (MACD < シグナル)"
        else:
            macd_signal = "中立"
        
        # トレンド判定
        short_trend = trend_data['trends']['short']
        medium_trend = trend_data['trends']['medium']
        long_trend = trend_data['trends']['long']
        
        # 総合判断
        signals_count = {
            '買い': 0,
            '売り': 0,
            '中立': 0
        }
        
        # RSI判定
        if '買い' in rsi_signal:
            signals_count['買い'] += 1
        elif '売り' in rsi_signal:
            signals_count['売り'] += 1
        else:
            signals_count['中立'] += 1
            
        # MACD判定
        if '買い' in macd_signal:
            signals_count['買い'] += 1
        elif '売り' in macd_signal:
            signals_count['売り'] += 1
        else:
            signals_count['中立'] += 1
            
        # トレンド判定
        if short_trend == '上昇':
            signals_count['買い'] += 0.5
        elif short_trend == '下降':
            signals_count['売り'] += 0.5
            
        if medium_trend == '上昇':
            signals_count['買い'] += 1
        elif medium_trend == '下降':
            signals_count['売り'] += 1
            
        if long_trend == '上昇':
            signals_count['買い'] += 1.5
        elif long_trend == '下降':
            signals_count['売り'] += 1.5
            
        # ゴールデン/デッドクロス
        if trend_data['signals']['golden_cross']:
            signals_count['買い'] += 2
            golden_cross_signal = "強い買いシグナル: ゴールデンクロス検出"
        else:
            golden_cross_signal = None
            
        if trend_data['signals']['dead_cross']:
            signals_count['売り'] += 2
            dead_cross_signal = "強い売りシグナル: デッドクロス検出"
        else:
            dead_cross_signal = None
        
        # 最終判断
        if signals_count['買い'] > signals_count['売り'] + 1:
            overall_signal = "買い"
            if signals_count['買い'] > signals_count['売り'] + 3:
                confidence = "高"
            else:
                confidence = "中"
        elif signals_count['売り'] > signals_count['買い'] + 1:
            overall_signal = "売り"
            if signals_count['売り'] > signals_count['買い'] + 3:
                confidence = "高"
            else:
                confidence = "中"
        else:
            overall_signal = "様子見"
            confidence = "低"
        
        # 短期予測（簡易的な線形回帰モデル）
        try:
            recent_data = data['Close'].tail(30).reset_index(drop=True)
            x = np.arange(len(recent_data))
            y = recent_data.values
            
            if len(x) > 0 and len(y) > 0:
                z = np.polyfit(x, y, 1)
                slope = z[0]
                
                # 傾きから短期予測
                if slope > 0:
                    short_prediction = "上昇傾向"
                elif slope < 0:
                    short_prediction = "下降傾向"
                else:
                    short_prediction = "横ばい"
            else:
                short_prediction = "データ不足"
        except:
            short_prediction = "計算エラー"
        
        return {
            'date': latest_date.strftime('%Y-%m-%d'),
            'price': latest_price,
            'changes': {
                'daily': one_day_change,
                'weekly': one_week_change,
                'monthly': one_month_change
            },
            'indicators': {
                'rsi': {
                    'value': rsi_value,
                    'signal': rsi_signal
                },
                'macd': {
                    'value': macd_value,
                    'signal_value': signal_value,
                    'signal': macd_signal
                }
            },
            'trends': {
                'short': short_trend,
                'medium': medium_trend,
                'long': long_trend,
                'golden_cross': golden_cross_signal,
                'dead_cross': dead_cross_signal
            },
            'volatility': volatility_data,
            'summary': {
                'signal': overall_signal,
                'confidence': confidence,
                'short_prediction': short_prediction
            }
        } 