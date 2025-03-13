import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class TechnicalAnalysis:
    """オリジナルの技術分析クラス"""
    
    @staticmethod
    def calculate_rsi(data, window=14):
        """RSI (相対力指数) の計算"""
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=window).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=window).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
        """MACD (移動平均収束拡散法) の計算"""
        ema_fast = data['Close'].ewm(span=fast_period, adjust=False).mean()
        ema_slow = data['Close'].ewm(span=slow_period, adjust=False).mean()
        
        macd = ema_fast - ema_slow
        signal = macd.ewm(span=signal_period, adjust=False).mean()
        histogram = macd - signal
        
        return pd.DataFrame({
            'MACD': macd,
            'Signal': signal,
            'Histogram': histogram
        })
    
    @staticmethod
    def calculate_trend(data, short_period=20, medium_period=50, long_period=200):
        """トレンド分析 (短期/中期/長期移動平均線に基づく)"""
        df = pd.DataFrame()
        
        # 移動平均線の計算
        df['MA_Short'] = data['Close'].rolling(window=short_period).mean()
        df['MA_Medium'] = data['Close'].rolling(window=medium_period).mean()
        df['MA_Long'] = data['Close'].rolling(window=long_period).mean()
        
        # 現在の価格
        latest_price = data['Close'].iloc[-1]
        
        # 移動平均線からのトレンド判定
        short_trend = "上昇" if latest_price > df['MA_Short'].iloc[-1] else "下降"
        medium_trend = "上昇" if latest_price > df['MA_Medium'].iloc[-1] else "下降"
        long_trend = "上昇" if latest_price > df['MA_Long'].iloc[-1] else "下降"
        
        # ゴールデンクロス/デッドクロスの検出
        golden_cross = df['MA_Short'].iloc[-1] > df['MA_Medium'].iloc[-1] and df['MA_Short'].iloc[-2] <= df['MA_Medium'].iloc[-2]
        dead_cross = df['MA_Short'].iloc[-1] < df['MA_Medium'].iloc[-1] and df['MA_Short'].iloc[-2] >= df['MA_Medium'].iloc[-2]
        
        # 移動平均乖離率
        deviation_short = (latest_price / df['MA_Short'].iloc[-1] - 1) * 100
        deviation_medium = (latest_price / df['MA_Medium'].iloc[-1] - 1) * 100
        deviation_long = (latest_price / df['MA_Long'].iloc[-1] - 1) * 100
        
        return {
            'trends': {
                'short': short_trend,
                'medium': medium_trend,
                'long': long_trend
            },
            'signals': {
                'golden_cross': golden_cross,
                'dead_cross': dead_cross
            },
            'deviation': {
                'short': deviation_short,
                'medium': deviation_medium,
                'long': deviation_long
            },
            'moving_averages': {
                'short': df['MA_Short'].iloc[-1],
                'medium': df['MA_Medium'].iloc[-1],
                'long': df['MA_Long'].iloc[-1]
            }
        }
    
    @staticmethod
    def analyze_volatility(data, window=20):
        """ボラティリティ分析"""
        # 日次リターンの計算
        returns = data['Close'].pct_change()
        
        # ボラティリティ（標準偏差）
        volatility = returns.rolling(window=window).std() * np.sqrt(window)
        
        # 現在のボラティリティ
        current_volatility = volatility.iloc[-1] * 100  # パーセント表示
        
        # 過去1年の平均と比較
        avg_volatility = volatility.tail(252).mean() * 100
        
        # ボラティリティのレベル判定
        if current_volatility < avg_volatility * 0.7:
            level = "低い"
        elif current_volatility > avg_volatility * 1.3:
            level = "高い"
        else:
            level = "普通"
            
        return {
            'current': current_volatility,
            'average': avg_volatility,
            'level': level
        }

class AdvancedAnalysis:
    """AIを活用した高度な市場分析クラス"""
    
    @staticmethod
    def calculate_all_indicators(data):
        """複数の技術的指標を一括計算"""
        indicators = {}
        
        # 基本データ
        indicators['price'] = data['Close'].iloc[-1]
        indicators['volume'] = data['Volume'].iloc[-1] if 'Volume' in data else None
        
        # トレンド指標
        indicators['sma_20'] = data['Close'].rolling(window=20).mean().iloc[-1]
        indicators['sma_50'] = data['Close'].rolling(window=50).mean().iloc[-1]
        indicators['sma_200'] = data['Close'].rolling(window=200).mean().iloc[-1]
        
        # 移動平均収束拡散指標（MACD）
        ema_12 = data['Close'].ewm(span=12, adjust=False).mean()
        ema_26 = data['Close'].ewm(span=26, adjust=False).mean()
        indicators['macd'] = ema_12.iloc[-1] - ema_26.iloc[-1]
        indicators['macd_signal'] = (ema_12 - ema_26).ewm(span=9, adjust=False).mean().iloc[-1]
        
        # RSI（相対力指数）
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        indicators['rsi'] = 100 - (100 / (1 + rs.iloc[-1]))
        
        # ボリンジャーバンド
        sma_20 = data['Close'].rolling(window=20).mean()
        std_20 = data['Close'].rolling(window=20).std()
        indicators['bb_upper'] = (sma_20 + (std_20 * 2)).iloc[-1]
        indicators['bb_middle'] = sma_20.iloc[-1]
        indicators['bb_lower'] = (sma_20 - (std_20 * 2)).iloc[-1]
        
        # ストキャスティクス
        high_14 = data['High'].rolling(window=14).max() if 'High' in data else data['Close'].rolling(window=14).max()
        low_14 = data['Low'].rolling(window=14).min() if 'Low' in data else data['Close'].rolling(window=14).min()
        k = 100 * ((data['Close'] - low_14) / (high_14 - low_14))
        indicators['stoch_k'] = k.iloc[-1]
        indicators['stoch_d'] = k.rolling(window=3).mean().iloc[-1]
        
        # 平均方向性指数（ADX）- トレンドの強さを測定
        if 'High' in data and 'Low' in data:
            high_diff = data['High'].diff()
            low_diff = -data['Low'].diff()
            tr1 = data['High'] - data['Low']
            tr2 = abs(data['High'] - data['Close'].shift(1))
            tr3 = abs(data['Low'] - data['Close'].shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr_14 = tr.rolling(window=14).mean()
            
            # +DI と -DI
            plus_dm = ((high_diff > low_diff) & (high_diff > 0)) * high_diff
            minus_dm = ((low_diff > high_diff) & (low_diff > 0)) * low_diff
            plus_di_14 = 100 * (plus_dm.rolling(window=14).mean() / atr_14)
            minus_di_14 = 100 * (minus_dm.rolling(window=14).mean() / atr_14)
            
            # ADX
            dx = 100 * abs(plus_di_14 - minus_di_14) / (plus_di_14 + minus_di_14)
            indicators['adx'] = dx.rolling(window=14).mean().iloc[-1]
            indicators['plus_di'] = plus_di_14.iloc[-1]
            indicators['minus_di'] = minus_di_14.iloc[-1]
        
        # フィボナッチリトレースメント
        recent_high = data['Close'].tail(90).max()
        recent_low = data['Close'].tail(90).min()
        diff = recent_high - recent_low
        indicators['fib_236'] = recent_high - (diff * 0.236)
        indicators['fib_382'] = recent_high - (diff * 0.382)
        indicators['fib_500'] = recent_high - (diff * 0.5)
        indicators['fib_618'] = recent_high - (diff * 0.618)
        
        # ボラティリティ指標
        indicators['volatility'] = data['Close'].pct_change().rolling(window=20).std().iloc[-1] * 100
        
        return indicators
    
    @staticmethod
    def predict_trend(data, days_ahead=14):
        """AIを使用した短期予測"""
        try:
            # 最低限のデータポイント数を確保
            if len(data) < 60:
                return {"prediction": "データ不足", "confidence": 0.0, "direction": "不明"}
                
            # 特徴量エンジニアリング
            df = pd.DataFrame()
            
            # 価格データ
            df['price'] = data['Close']
            
            # 技術的指標を特徴量として追加
            df['sma_5'] = data['Close'].rolling(window=5).mean()
            df['sma_10'] = data['Close'].rolling(window=10).mean()
            df['sma_20'] = data['Close'].rolling(window=20).mean()
            
            # RSI
            delta = data['Close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            ema_12 = data['Close'].ewm(span=12, adjust=False).mean()
            ema_26 = data['Close'].ewm(span=26, adjust=False).mean()
            df['macd'] = ema_12 - ema_26
            
            # ボラティリティ
            df['volatility'] = data['Close'].pct_change().rolling(window=20).std()
            
            # ラグ特徴量（過去の価格変動）
            for i in range(1, 6):
                df[f'price_lag_{i}'] = df['price'].shift(i)
                df[f'return_lag_{i}'] = df['price'].pct_change(i)
            
            # 移動平均乖離率
            df['ma_ratio_5_20'] = df['sma_5'] / df['sma_20']
            
            # 欠損値の除去
            df = df.dropna()
            
            if len(df) < 30:
                return {"prediction": "データ不足", "confidence": 0.0, "direction": "不明"}
            
            # 目的変数（N日後の価格変化率）
            df['target'] = df['price'].shift(-days_ahead) / df['price'] - 1
            
            # 学習データとテストデータの分割
            train_size = int(len(df) * 0.8)
            train_data = df.iloc[:train_size].copy()
            
            # 欠損値の除去
            train_data = train_data.dropna()
            
            if len(train_data) < 20:
                return {"prediction": "データ不足", "confidence": 0.0, "direction": "不明"}
            
            # 特徴量とターゲットを分離
            X_train = train_data.drop(['target', 'price'], axis=1)
            y_train = train_data['target']
            
            # データ標準化
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            
            # モデルのトレーニング
            model = LinearRegression()
            model.fit(X_train_scaled, y_train)
            
            # 最新データを使って予測
            latest_data = df.iloc[-1:].copy()
            if 'target' in latest_data:
                latest_data = latest_data.drop('target', axis=1)
            latest_features = latest_data.drop('price', axis=1)
            latest_scaled = scaler.transform(latest_features)
            
            # 予測
            prediction = model.predict(latest_scaled)[0]
            
            # 予測の方向性と信頼性を計算
            direction = "上昇" if prediction > 0 else "下降" if prediction < 0 else "横ばい"
            abs_prediction = abs(prediction)
            confidence = 0.7  # デフォルト値
            
            # 予測値の絶対値が大きいほど信頼性が高いと仮定
            if abs_prediction > 0.05:
                confidence = 0.9
            elif abs_prediction > 0.02:
                confidence = 0.8
            elif abs_prediction > 0.01:
                confidence = 0.7
            else:
                confidence = 0.6
                
            # 現在の価格と予測価格
            current_price = latest_data['price'].values[0]
            predicted_price = current_price * (1 + prediction)
            
            return {
                "direction": direction,
                "prediction": prediction * 100,  # パーセント表示に変換
                "confidence": confidence,
                "current_price": current_price,
                "predicted_price": predicted_price,
                "days_ahead": days_ahead
            }
            
        except Exception as e:
            print(f"予測エラー: {e}")
            return {"prediction": "計算エラー", "confidence": 0.0, "direction": "不明"}
    
    @staticmethod
    def analyze_market_condition(data, indicators):
        """総合的な市場状況分析"""
        # 市場フェーズの識別
        current_price = data['Close'].iloc[-1]
        sma_50 = data['Close'].rolling(window=50).mean().iloc[-1]
        sma_200 = data['Close'].rolling(window=200).mean().iloc[-1]
        
        # 強気/弱気市場の判断
        if current_price > sma_200 and sma_50 > sma_200:
            market_phase = "強気相場（ブル・マーケット）"
        elif current_price < sma_200 and sma_50 < sma_200:
            market_phase = "弱気相場（ベア・マーケット）"
        else:
            market_phase = "移行期"
        
        # トレンドの強さ判定
        adx = indicators.get('adx')
        trend_strength = "不明"
        if adx is not None:
            if adx > 50:
                trend_strength = "非常に強い"
            elif adx > 40:
                trend_strength = "強い"
            elif adx > 30:
                trend_strength = "中程度"
            elif adx > 20:
                trend_strength = "弱い"
            else:
                trend_strength = "トレンドなし（レンジ相場）"
        
        # サポートとレジスタンスの計算
        recent_data = data['Close'].tail(60)
        sorted_prices = sorted(recent_data)
        price_clusters = []
        
        # 価格クラスタリングでサポート/レジスタンスを特定
        for price in sorted_prices:
            found_cluster = False
            for cluster in price_clusters:
                if abs(cluster['center'] - price) / cluster['center'] < 0.01:  # 1%以内の価格を同じクラスタと見なす
                    cluster['count'] += 1
                    cluster['prices'].append(price)
                    cluster['center'] = sum(cluster['prices']) / len(cluster['prices'])
                    found_cluster = True
                    break
            
            if not found_cluster:
                price_clusters.append({
                    'center': price,
                    'count': 1,
                    'prices': [price]
                })
        
        # 重要度でソート
        price_clusters.sort(key=lambda x: x['count'], reverse=True)
        
        # 上位のクラスタをサポート/レジスタンスとして抽出
        key_levels = []
        for cluster in price_clusters[:5]:  # 上位5つのクラスタ
            if cluster['count'] >= 3:  # 少なくとも3回出現
                level_type = "サポート" if cluster['center'] < current_price else "レジスタンス"
                key_levels.append({
                    'price': cluster['center'],
                    'type': level_type,
                    'strength': cluster['count']
                })
        
        # ボラティリティの状態評価
        volatility = indicators['volatility']
        volatility_state = "普通"
        if volatility > 3:
            volatility_state = "非常に高い"
        elif volatility > 2:
            volatility_state = "高い"
        elif volatility < 0.8:
            volatility_state = "非常に低い"
        elif volatility < 1.2:
            volatility_state = "低い"
        
        # 過熱感/冷え込み判断
        rsi = indicators['rsi']
        if rsi > 80:
            overbought = "極度の過熱感（売られすぎ）"
        elif rsi > 70:
            overbought = "過熱感あり"
        elif rsi < 20:
            overbought = "極度の冷え込み（買われすぎ）"
        elif rsi < 30:
            overbought = "冷え込みあり"
        else:
            overbought = "中立"
        
        return {
            'market_phase': market_phase,
            'trend_strength': trend_strength,
            'key_levels': key_levels,
            'volatility_state': volatility_state,
            'market_sentiment': overbought
        } 