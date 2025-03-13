import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from models.analysis import AdvancedAnalysis

class MarketAnalysisService:
    """総合的な市場分析サービス"""
    
    def generate_comprehensive_analysis(self, data):
        """包括的な市場分析レポートを生成"""
        # 基本データの確認
        if data.empty or len(data) < 50:
            return {
                "error": "分析に十分なデータがありません",
                "sample": True
            }
        
        # すべての技術的指標を計算
        analyzer = AdvancedAnalysis()
        indicators = analyzer.calculate_all_indicators(data)
        
        # AIモデルによる予測
        short_prediction = analyzer.predict_trend(data, days_ahead=7)
        medium_prediction = analyzer.predict_trend(data, days_ahead=30)
        
        # 市場状況分析
        market_condition = analyzer.analyze_market_condition(data, indicators)
        
        # 過去のパフォーマンス計算
        performance = self._calculate_performance(data)
        
        # トレーディング戦略とシグナル
        trading_signals = self._generate_trading_signals(data, indicators, market_condition)
        
        # リスク評価
        risk_assessment = self._assess_risk(data, indicators, market_condition)
        
        # 最終的な推奨事項
        recommendation = self._generate_recommendation(
            indicators, 
            market_condition, 
            short_prediction, 
            risk_assessment,
            trading_signals
        )
        
        # 分析結果をまとめる
        return {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "price": indicators['price'],
            "indicators": {
                "rsi": indicators['rsi'],
                "macd": indicators['macd'],
                "macd_signal": indicators['macd_signal'],
                "bollinger": {
                    "upper": indicators['bb_upper'],
                    "middle": indicators['bb_middle'],
                    "lower": indicators['bb_lower']
                },
                "stochastic": {
                    "k": indicators['stoch_k'],
                    "d": indicators['stoch_d']
                },
                "adx": indicators.get('adx'),
                "volatility": indicators['volatility']
            },
            "market_condition": market_condition,
            "predictions": {
                "short_term": short_prediction,
                "medium_term": medium_prediction
            },
            "performance": performance,
            "trading_signals": trading_signals,
            "risk_assessment": risk_assessment,
            "recommendation": recommendation
        }
    
    def _calculate_performance(self, data):
        """過去のパフォーマンス指標を計算"""
        current_price = data['Close'].iloc[-1]
        
        # 各期間のリターン計算
        returns = {}
        if len(data) > 1:
            returns['daily'] = (current_price / data['Close'].iloc[-2] - 1) * 100
        
        if len(data) > 5:
            returns['weekly'] = (current_price / data['Close'].iloc[-6] - 1) * 100
            
        if len(data) > 21:
            returns['monthly'] = (current_price / data['Close'].iloc[-22] - 1) * 100
            
        if len(data) > 63:
            returns['quarterly'] = (current_price / data['Close'].iloc[-64] - 1) * 100
            
        if len(data) > 252:
            returns['yearly'] = (current_price / data['Close'].iloc[-253] - 1) * 100
        
        # 最大ドローダウン計算
        if len(data) > 50:
            close = data['Close']
            rolling_max = close.rolling(window=252, min_periods=1).max()
            drawdown = (close / rolling_max - 1) * 100
            max_drawdown = drawdown.min()
        else:
            max_drawdown = None
        
        # 変動性（ボラティリティ）
        if len(data) > 20:
            volatility_daily = data['Close'].pct_change().std() * 100
            volatility_annualized = volatility_daily * np.sqrt(252)
        else:
            volatility_daily = None
            volatility_annualized = None
        
        return {
            'returns': returns,
            'max_drawdown': max_drawdown,
            'volatility': {
                'daily': volatility_daily,
                'annualized': volatility_annualized
            }
        }
    
    def _generate_trading_signals(self, data, indicators, market_condition):
        """AIベースのトレーディングシグナル生成"""
        signals = {}
        
        # RSIシグナル
        if indicators['rsi'] < 30:
            signals['rsi'] = "買い（売られすぎ）"
        elif indicators['rsi'] > 70:
            signals['rsi'] = "売り（買われすぎ）"
        else:
            signals['rsi'] = "中立"
        
        # MACDシグナル
        if indicators['macd'] > indicators['macd_signal'] and indicators['macd'] > 0:
            signals['macd'] = "強い買い"
        elif indicators['macd'] > indicators['macd_signal']:
            signals['macd'] = "弱い買い"
        elif indicators['macd'] < indicators['macd_signal'] and indicators['macd'] < 0:
            signals['macd'] = "強い売り"
        elif indicators['macd'] < indicators['macd_signal']:
            signals['macd'] = "弱い売り"
        else:
            signals['macd'] = "中立"
        
        # ボリンジャーバンドシグナル
        current_price = data['Close'].iloc[-1]
        if current_price > indicators['bb_upper']:
            signals['bollinger'] = "売り（上限超え）"
        elif current_price < indicators['bb_lower']:
            signals['bollinger'] = "買い（下限超え）"
        else:
            position = (current_price - indicators['bb_lower']) / (indicators['bb_upper'] - indicators['bb_lower'])
            if position > 0.8:
                signals['bollinger'] = "弱い売り（上限接近）"
            elif position < 0.2:
                signals['bollinger'] = "弱い買い（下限接近）"
            else:
                signals['bollinger'] = "中立"
        
        # ストキャスティクスシグナル
        if indicators['stoch_k'] < 20 and indicators['stoch_d'] < 20:
            signals['stochastic'] = "買い（売られすぎ）"
        elif indicators['stoch_k'] > 80 and indicators['stoch_d'] > 80:
            signals['stochastic'] = "売り（買われすぎ）"
        elif indicators['stoch_k'] > indicators['stoch_d']:
            signals['stochastic'] = "弱い買い"
        elif indicators['stoch_k'] < indicators['stoch_d']:
            signals['stochastic'] = "弱い売り"
        else:
            signals['stochastic'] = "中立"
        
        # トレンド確認シグナル
        sma_20 = data['Close'].rolling(window=20).mean().iloc[-1]
        sma_50 = data['Close'].rolling(window=50).mean().iloc[-1]
        sma_200 = data['Close'].rolling(window=200).mean().iloc[-1]
        
        if current_price > sma_20 and current_price > sma_50 and current_price > sma_200:
            signals['trend'] = "強い買い（すべての移動平均線の上）"
        elif current_price < sma_20 and current_price < sma_50 and current_price < sma_200:
            signals['trend'] = "強い売り（すべての移動平均線の下）"
        elif current_price > sma_50 and sma_50 > sma_200:
            signals['trend'] = "買い（ゴールデンクロス状態）"
        elif current_price < sma_50 and sma_50 < sma_200:
            signals['trend'] = "売り（デッドクロス状態）"
        elif current_price > sma_20:
            signals['trend'] = "弱い買い"
        elif current_price < sma_20:
            signals['trend'] = "弱い売り"
        else:
            signals['trend'] = "中立"
        
        # 総合シグナル
        buy_signals = sum(1 for s in signals.values() if "買い" in s)
        sell_signals = sum(1 for s in signals.values() if "売り" in s)
        
        if buy_signals >= 3 and buy_signals > sell_signals + 1:
            combined_signal = "買い"
            signal_strength = "強い" if buy_signals >= 4 else "中程度"
        elif sell_signals >= 3 and sell_signals > buy_signals + 1:
            combined_signal = "売り"
            signal_strength = "強い" if sell_signals >= 4 else "中程度"
        elif buy_signals > sell_signals:
            combined_signal = "弱い買い"
            signal_strength = "弱い"
        elif sell_signals > buy_signals:
            combined_signal = "弱い売り"
            signal_strength = "弱い"
        else:
            combined_signal = "中立"
            signal_strength = "なし"
        
        # 市場状況と組み合わせた最終判断
        if market_condition['market_phase'] == "強気相場（ブル・マーケット）" and combined_signal == "買い":
            final_signal = "強い買い（トレンド確認）"
        elif market_condition['market_phase'] == "弱気相場（ベア・マーケット）" and combined_signal == "売り":
            final_signal = "強い売り（トレンド確認）"
        elif market_condition['market_phase'] == "強気相場（ブル・マーケット）" and combined_signal == "売り":
            final_signal = "一時的な調整の可能性（慎重な売り）"
        elif market_condition['market_phase'] == "弱気相場（ベア・マーケット）" and combined_signal == "買い":
            final_signal = "反発の可能性（慎重な買い）"
        else:
            final_signal = combined_signal
        
        return {
            'individual': signals,
            'combined': combined_signal,
            'strength': signal_strength,
            'final': final_signal
        }
    
    def _assess_risk(self, data, indicators, market_condition):
        """リスク評価"""
        # ボラティリティに基づくリスク
        volatility_risk = "低"
        if indicators['volatility'] > 3:
            volatility_risk = "非常に高い"
        elif indicators['volatility'] > 2:
            volatility_risk = "高い"
        elif indicators['volatility'] > 1.5:
            volatility_risk = "中程度"
        
        # トレンド強度に基づくリスク
        trend_risk = "中程度"
        if market_condition['trend_strength'] == "非常に強い":
            trend_risk = "低"  # 強いトレンドは予測可能性が高い
        elif market_condition['trend_strength'] == "トレンドなし（レンジ相場）":
            trend_risk = "高い"  # レンジ相場は方向性が不明確
        
        # 過熱/冷え込み状態に基づくリスク
        sentiment_risk = "中程度"
        if "極度の過熱感" in market_condition['market_sentiment']:
            sentiment_risk = "高い"  # 暴落リスク
        elif "極度の冷え込み" in market_condition['market_sentiment']:
            sentiment_risk = "高い"  # 急騰後の反落リスク
        
        # キーレベル（サポート/レジスタンス）との距離に基づくリスク
        key_level_risk = "中程度"
        current_price = data['Close'].iloc[-1]
        closest_distance_pct = float('inf')
        
        for level in market_condition['key_levels']:
            distance_pct = abs(level['price'] - current_price) / current_price * 100
            if distance_pct < closest_distance_pct:
                closest_distance_pct = distance_pct
        
        if closest_distance_pct < 1:
            key_level_risk = "高い"  # 重要レベル付近ではブレイクアウトまたはリバーサルの可能性
        elif closest_distance_pct < 3:
            key_level_risk = "やや高い"
        
        # 総合リスク評価
        risk_scores = {
            "低": 1,
            "やや低い": 2,
            "中程度": 3,
            "やや高い": 4,
            "高い": 5,
            "非常に高い": 6
        }
        
        risk_factors = [
            risk_scores.get(volatility_risk, 3),
            risk_scores.get(trend_risk, 3),
            risk_scores.get(sentiment_risk, 3),
            risk_scores.get(key_level_risk, 3)
        ]
        
        avg_risk_score = sum(risk_factors) / len(risk_factors)
        
        if avg_risk_score > 5:
            overall_risk = "非常に高い"
        elif avg_risk_score > 4:
            overall_risk = "高い"
        elif avg_risk_score > 3:
            overall_risk = "やや高い"
        elif avg_risk_score > 2:
            overall_risk = "中程度"
        elif avg_risk_score > 1:
            overall_risk = "やや低い"
        else:
            overall_risk = "低い"
        
        return {
            'volatility_risk': volatility_risk,
            'trend_risk': trend_risk,
            'sentiment_risk': sentiment_risk,
            'key_level_risk': key_level_risk,
            'overall_risk': overall_risk
        }
    
    def _generate_recommendation(self, indicators, market_condition, prediction, risk, signals):
        """分析に基づく最終的な推奨事項を生成"""
        # 各要素に基づくスコアリング
        scores = {'buy': 0, 'sell': 0, 'hold': 0}
        
        # 予測に基づくスコア
        if prediction['direction'] == "上昇":
            scores['buy'] += 1 * prediction['confidence']
        elif prediction['direction'] == "下降":
            scores['sell'] += 1 * prediction['confidence']
        else:
            scores['hold'] += 1
        
        # RSIに基づくスコア
        if indicators['rsi'] < 30:
            scores['buy'] += 1
        elif indicators['rsi'] > 70:
            scores['sell'] += 1
        else:
            scores['hold'] += 0.5
        
        # MACDに基づくスコア
        if indicators['macd'] > indicators['macd_signal']:
            scores['buy'] += 0.8
        elif indicators['macd'] < indicators['macd_signal']:
            scores['sell'] += 0.8
        
        # トレンドに基づくスコア
        if market_condition['market_phase'] == "強気相場（ブル・マーケット）":
            scores['buy'] += 1
        elif market_condition['market_phase'] == "弱気相場（ベア・マーケット）":
            scores['sell'] += 1
        
        # 総合シグナルに基づくスコア
        signal_weights = {
            "強い買い": 1.5,
            "買い": 1.0,
            "弱い買い": 0.5,
            "中立": 0,
            "弱い売り": -0.5,
            "売り": -1.0,
            "強い売り": -1.5
        }
        
        signal_score = signal_weights.get(signals['final'], 0)
        if signal_score > 0:
            scores['buy'] += signal_score
        elif signal_score < 0:
            scores['sell'] += abs(signal_score)
        else:
            scores['hold'] += 0.5
        
        # リスク評価に基づく調整
        risk_adjustment = {
            "低い": 1.2,
            "やや低い": 1.1,
            "中程度": 1.0,
            "やや高い": 0.9,
            "高い": 0.8,
            "非常に高い": 0.7
        }
        
        risk_factor = risk_adjustment.get(risk['overall_risk'], 1.0)
        scores['buy'] *= risk_factor  # リスクが高いほど買いスコア減少
        
        # 最終判断
        max_score = max(scores.values())
        if max_score == 0:
            return {
                'action': "様子見",
                'confidence': "低",
                'explanation': "明確なシグナルがありません。様子見が推奨されます。"
            }
        
        if scores['buy'] == max_score and scores['buy'] > scores['sell'] * 1.5:
            action = "買い"
            if scores['buy'] > 3:
                confidence = "高"
            elif scores['buy'] > 2:
                confidence = "中"
            else:
                confidence = "低"
        elif scores['sell'] == max_score and scores['sell'] > scores['buy'] * 1.5:
            action = "売り"
            if scores['sell'] > 3:
                confidence = "高"
            elif scores['sell'] > 2:
                confidence = "中"
            else:
                confidence = "低"
        else:
            action = "様子見"
            confidence = "中"
        
        # 説明文生成
        if action == "買い":
            if market_condition['market_phase'] == "強気相場（ブル・マーケット）":
                explanation = "強気相場の中での買いシグナルです。トレンドに沿った取引が有利です。"
            elif prediction['direction'] == "上昇":
                explanation = f"短期的な上昇予測({prediction['prediction']:.1f}%)と技術的指標が買いを示唆しています。"
            else:
                explanation = "複数の技術的指標が買いシグナルを示しています。"
        elif action == "売り":
            if market_condition['market_phase'] == "弱気相場（ベア・マーケット）":
                explanation = "弱気相場の中での売りシグナルです。下落トレンドが継続する可能性があります。"
            elif prediction['direction'] == "下降":
                explanation = f"短期的な下落予測({-prediction['prediction']:.1f}%)と技術的指標が売りを示唆しています。"
            else:
                explanation = "複数の技術的指標が売りシグナルを示しています。"
        else:
            explanation = "明確な方向性が見られないため、様子見が推奨されます。"
        
        # リスクに関する追加コメント
        if risk['overall_risk'] in ["高い", "非常に高い"]:
            explanation += f" ただし、現在はリスクが{risk['overall_risk']}状態なので、慎重な判断が必要です。"
        
        return {
            'action': action,
            'confidence': confidence,
            'explanation': explanation,
            'scores': scores
        } 