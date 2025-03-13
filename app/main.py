from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
from datetime import datetime, timedelta

import pandas as pd
from services.data import StockDataService
from models.analysis import TechnicalAnalysis
from services.signals import SignalService
from services.analysis_service import MarketAnalysisService

app = FastAPI(title="日経平均分析アプリ")

# 現在のファイルが存在するディレクトリを取得
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# 静的ファイルのマウント
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def read_root():
    return {"message": "日経平均分析APIへようこそ"}

@app.get("/api/nikkei/analysis")
async def get_nikkei_analysis(period: str = "1y"):
    """日経平均の基本的な分析結果を取得するエンドポイント"""
    try:
        print(f"リクエストされた期間: {period}")  # デバッグ用

        # データ取得
        data_service = StockDataService()
        data = data_service.get_nikkei_data(period=period)
        
        print(f"取得データ行数: {len(data)}, 期間: {data.index[0]} から {data.index[-1]}")  # デバッグ用
        
        if data.empty:
            return JSONResponse(
                status_code=200,
                content={"message": "サンプルデータを使用しています", "sample": True}
            )
        
        # 技術的分析の実施
        analyzer = TechnicalAnalysis()
        rsi = analyzer.calculate_rsi(data)
        macd_data = analyzer.calculate_macd(data)
        
        # 最新の結果を返す
        latest_data = {}
        latest_data['price'] = data['Close'].iloc[-1]
        latest_data['rsi'] = rsi.iloc[-1]
        latest_data['macd'] = macd_data['MACD'].iloc[-1]
        latest_data['signal'] = macd_data['Signal'].iloc[-1]
        latest_data['date'] = data.index[-1].strftime('%Y-%m-%d')
        
        # チャートデータの準備
        chart_data = data[['Close']].tail(200).copy()
        chart_data['RSI'] = rsi
        chart_data['MACD'] = macd_data['MACD']
        chart_data['Signal'] = macd_data['Signal']
        chart_data = chart_data.reset_index()
        
        # 日付フォーマット変換
        chart_data['date'] = chart_data['Date'].dt.strftime('%Y-%m-%d') if 'Date' in chart_data.columns else chart_data.index.strftime('%Y-%m-%d')
        chart_data = chart_data.rename(columns={'Close': 'Price'})
        
        # 必要な列だけを取得
        needed_columns = ['date', 'Price', 'RSI', 'MACD', 'Signal']
        available_columns = [col for col in needed_columns if col in chart_data.columns]
        chart_data = chart_data[available_columns]
        
        return {
            "latest": latest_data,
            "chart_data": chart_data.to_dict(orient='records'),
            "period": period
        }
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"エラー詳細: {error_details}")
        
        # サンプルデータを返す
        return {
            "error": str(e),
            "message": "エラーが発生したため、サンプルデータを表示しています",
            "sample": True,
            "latest": {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "price": 30000,
                "rsi": 50,
                "macd": 0,
                "signal": 0
            },
            "chart_data": _generate_sample_chart_data()
        }

@app.get("/api/nikkei/market-analysis")
async def get_market_analysis(period: str = "1y"):
    """市場分析レポートを取得するエンドポイント"""
    try:
        print(f"市場分析APIがリクエストされました: 期間={period}")
        
        # データ取得
        data_service = StockDataService()
        data = data_service.get_nikkei_data(period=period)
        
        print(f"データ取得完了: {len(data)}行")
        
        if data.empty:
            print("空のデータフレーム - サンプルデータを返します")
            return JSONResponse(
                status_code=200,
                content={
                    "message": "サンプルデータを使用しています", 
                    "sample": True,
                    "analysis": {
                        "date": datetime.now().strftime('%Y-%m-%d'),
                        "price": 30000,
                        "summary": {
                            "signal": "中立",
                            "confidence": "低",
                            "short_prediction": "データなし"
                        }
                    }
                }
            )
        
        # 技術的分析の実施
        analyzer = TechnicalAnalysis()
        rsi = analyzer.calculate_rsi(data)
        macd_data = analyzer.calculate_macd(data)
        trend_data = analyzer.calculate_trend(data)
        volatility_data = analyzer.analyze_volatility(data)
        
        print("分析計算完了")
        
        # 市場分析レポート生成
        signal_service = SignalService()
        analysis = signal_service.generate_market_analysis(
            data, rsi, macd_data, trend_data, volatility_data
        )
        
        print("分析レポート生成完了")
        
        return {
            "analysis": analysis,
            "sample": False
        }
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"詳細なエラー情報: {error_details}")
        
        # サンプルデータを返す
        return {
            "error": str(e),
            "message": "エラーが発生したため、サンプルデータを表示しています",
            "sample": True,
            "analysis": {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "price": 30000,
                "summary": {
                    "signal": "中立",
                    "confidence": "低",
                    "short_prediction": "データなし"
                }
            }
        }

def _generate_sample_chart_data():
    """サンプルチャートデータを生成"""
    import random
    
    data = []
    base_price = 30000
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(30):
        date = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
        price = base_price + random.uniform(-500, 500)
        base_price = price
        
        data.append({
            "date": date,
            "Price": price,
            "RSI": random.uniform(30, 70),
            "MACD": random.uniform(-200, 200),
            "Signal": random.uniform(-100, 100),
            "Strong_Buy": random.random() > 0.8
        })
    
    return data

@app.get("/api/nikkei/ai-analysis")
async def get_ai_analysis(period: str = "1y"):
    """AIによる高度な市場分析を取得するエンドポイント"""
    try:
        print(f"AI分析がリクエストされました: 期間={period}")
        
        # データ取得
        data_service = StockDataService()
        data = data_service.get_nikkei_data(period=period)
        
        print(f"AI分析: データ取得完了 ({len(data)}行)")
        
        if data.empty or len(data) < 50:
            return JSONResponse(
                status_code=200,
                content={
                    "message": "分析に十分なデータがありません。サンプルデータを使用します。",
                    "sample": True,
                    "analysis": _generate_sample_ai_analysis()
                }
            )
        
        # 市場分析サービスを使用して包括的な分析を実行
        analysis_service = MarketAnalysisService()
        analysis_result = analysis_service.generate_comprehensive_analysis(data)
        
        print("AI分析: 分析完了")
        
        return {
            "analysis": analysis_result,
            "sample": False,
            "period": period
        }
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"AI分析エラー: {e}")
        print(f"詳細: {error_details}")
        
        return JSONResponse(
            status_code=200,
            content={
                "error": str(e),
                "message": "分析中にエラーが発生しました。サンプルデータを使用します。",
                "sample": True,
                "analysis": _generate_sample_ai_analysis()
            }
        )

def _generate_sample_ai_analysis():
    """サンプルAI分析結果を生成"""
    return {
        "date": datetime.now().strftime('%Y-%m-%d'),
        "price": 32500,
        "indicators": {
            "rsi": 52.5,
            "macd": 15.3,
            "macd_signal": 10.8,
            "bollinger": {
                "upper": 33000,
                "middle": 32200,
                "lower": 31400
            },
            "stochastic": {
                "k": 65.2,
                "d": 60.1
            },
            "adx": 22.5,
            "volatility": 1.8
        },
        "market_condition": {
            "market_phase": "強気相場（ブル・マーケット）",
            "trend_strength": "中程度",
            "volatility_state": "普通",
            "market_sentiment": "中立"
        },
        "predictions": {
            "short_term": {
                "direction": "上昇",
                "prediction": 1.2,
                "confidence": 0.7
            },
            "medium_term": {
                "direction": "横ばい",
                "prediction": 0.3,
                "confidence": 0.6
            }
        },
        "recommendation": {
            "action": "様子見",
            "confidence": "中",
            "explanation": "市場は強気相場の中で推移していますが、短期的な上昇予測の信頼性が限られています。様子見が推奨されます。"
        }
    }

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """すべての例外をキャッチしてJSONレスポンスを返す"""
    print(f"エラーが発生しました: {exc}")
    import traceback
    traceback.print_exc()
    
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "message": "サーバーエラーが発生しました",
            "sample": True,
            "analysis": {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "price": 30000,
                "summary": {
                    "signal": "中立",
                    "confidence": "低",
                    "short_prediction": "データなし"
                }
            }
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 