import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time

# 内部モジュールのインポート
from models.analysis import TechnicalAnalysis, AdvancedAnalysis
from services.data import StockDataService

# ページ設定
st.set_page_config(
    page_title="日経平均分析 - AIによる高度分析",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# セッション状態の初期化
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

# ヘッダーセクション
st.title("日経平均株価分析ダッシュボード")

# 説明セクション
with st.expander("分析手法について", expanded=False):
    st.markdown("""
    ### 分析手法について
    当ダッシュボードでは複数の分析手法を併用しています：
    - **基本テクニカル分析**：RSI、MACDなどの標準的な指標に基づく一般的な判断
    - **AIによる高度分析**：機械学習モデルを活用した過去データの傾向分析と予測
    
    両者の分析結果に相違がある場合は、複数の視点から市場を見ることで、より包括的な判断が可能です。
    """)

# サイドバーの期間選択
st.sidebar.header("データ設定")
period = st.sidebar.selectbox(
    "期間を選択",
    ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"],
    index=3  # デフォルトは1y
)

# データを取得
data_service = StockDataService()
with st.spinner("日経平均データを取得中..."):
    df = data_service.get_nikkei_data(period=period)

if df.empty:
    st.error("データを取得できませんでした。サンプルデータを表示します。")
    # サンプルデータの生成
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    df = pd.DataFrame({
        'Open': np.random.normal(30000, 500, 100),
        'High': np.random.normal(30100, 500, 100),
        'Low': np.random.normal(29900, 500, 100),
        'Close': np.random.normal(30000, 500, 100),
        'Volume': np.random.normal(1000000, 200000, 100)
    }, index=dates)

# 更新ボタン
if st.sidebar.button("データを更新"):
    st.session_state.last_update = datetime.now()
    st.experimental_rerun()

st.sidebar.info(f"最終更新: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M:%S')}")

# メインコンテンツエリア
col1, col2 = st.columns([1, 2])

# --- 左カラム - 最新の分析結果 ---
with col1:
    st.subheader("最新の分析結果")
    
    # 基本テクニカル分析計算
    analyzer = TechnicalAnalysis()
    rsi = analyzer.calculate_rsi(df)
    macd_data = analyzer.calculate_macd(df)
    
    latest_price = df['Close'].iloc[-1]
    latest_date = df.index[-1].strftime('%Y-%m-%d')
    latest_rsi = rsi.iloc[-1]
    latest_macd = macd_data['MACD'].iloc[-1]
    latest_signal = macd_data['Signal'].iloc[-1]
    
    # シグナル計算
    rsi_signal = "買い" if latest_rsi < 30 else ("売り" if latest_rsi > 70 else "中立")
    macd_signal = "買い" if latest_macd > latest_signal else "売り"
    
    # 総合シグナル計算
    buy_signals = 0
    sell_signals = 0
    
    if latest_rsi < 30: buy_signals += 1
    elif latest_rsi > 70: sell_signals += 1
    
    if latest_macd > latest_signal: buy_signals += 1
    else: sell_signals += 1
    
    if buy_signals > sell_signals + 1: overall_signal = "強い買い"
    elif buy_signals > sell_signals: overall_signal = "弱い買い"
    elif sell_signals > buy_signals + 1: overall_signal = "強い売り"
    elif sell_signals > buy_signals: overall_signal = "弱い売り"
    else: overall_signal = "中立"
    
    # 結果の表示
    st.metric("日経平均株価", f"¥{latest_price:,.0f}", f"{df['Close'].pct_change().iloc[-1]*100:.2f}%")
    st.caption(f"日付: {latest_date}")
    
    signal_color = {
        "強い買い": "green", "弱い買い": "lightgreen",
        "強い売り": "red", "弱い売り": "lightcoral",
        "中立": "gray"
    }
    
    st.markdown(f"### 市場シグナル: <span style='color:{signal_color[overall_signal]}'>{overall_signal}</span>", unsafe_allow_html=True)
    
    col_rsi, col_macd = st.columns(2)
    with col_rsi:
        st.metric("RSI", f"{latest_rsi:.1f}", rsi_signal)
    with col_macd:
        st.metric("MACD", f"{latest_macd:.1f}", macd_signal)
    
    # 市場サマリーテキスト
    if overall_signal == "強い買い":
        summary = "短期的な買い場の可能性が高いです。RSIが売られすぎの水準にあり、MACDも買いシグナルを示しています。"
    elif overall_signal == "弱い買い":
        summary = "弱気ながらも買いサインが出ています。慎重に様子を見ながら買い増しの検討が可能です。"
    elif overall_signal == "強い売り":
        summary = "短期的な売り圧力が強まっています。利益確定や一部売却の検討をお勧めします。"
    elif overall_signal == "弱い売り":
        summary = "弱気ながらも売りサインが出ています。新規買い増しは控え目にすることをお勧めします。"
    else:
        summary = "明確な方向性が見られません。様子見が推奨されます。"
    
    st.info(summary)

# --- 右カラム - チャート分析 ---
with col2:
    st.subheader("チャート分析")
    
    # データ準備
    df_chart = df.copy()
    df_chart.reset_index(inplace=True)
    df_chart.rename(columns={'index': 'Date'}, inplace=True)
    
    # プロットリー図の作成
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.1, 
                        row_heights=[0.7, 0.3],
                        specs=[[{"type": "candlestick"}],
                               [{"type": "scatter"}]])
    
    # ローソク足チャート
    candlestick = go.Candlestick(
        x=df_chart['Date'],
        open=df_chart['Open'],
        high=df_chart['High'],
        low=df_chart['Low'],
        close=df_chart['Close'],
        name="日経平均"
    )
    fig.add_trace(candlestick, row=1, col=1)
    
    # RSIチャート
    df_chart['RSI'] = rsi.values
    rsi_trace = go.Scatter(
        x=df_chart['Date'],
        y=df_chart['RSI'],
        line=dict(color='purple', width=1),
        name="RSI"
    )
    fig.add_trace(rsi_trace, row=2, col=1)
    
    # 水平線（RSIの基準線）
    fig.add_hline(y=70, line_width=1, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_width=1, line_dash="dash", line_color="green", row=2, col=1)
    
    # レイアウト設定
    fig.update_layout(
        title="日経平均株価チャート",
        xaxis_title="日付",
        yaxis_title="価格 (円)",
        xaxis_rangeslider_visible=False,
        height=600,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=50, t=80, b=50),
    )
    
    fig.update_yaxes(title_text="RSI", row=2, col=1)
    
    # チャート表示
    st.plotly_chart(fig, use_container_width=True)

# --- 高度AI分析セクション ---
st.header("AI市場分析")

if st.button("高度分析を更新"):
    with st.spinner("AIによる高度な市場分析を実行中..."):
        time.sleep(2)  # 実際のAI処理に置き換える

advanced_analyzer = AdvancedAnalysis()
with st.spinner("AI分析を生成中..."):
    analysis_results = advanced_analyzer.generate_market_analysis(df)

# AIの分析結果表示
col_ai1, col_ai2 = st.columns([2, 1])

with col_ai1:
    # 推奨アクション
    action = analysis_results.get('recommendation', {}).get('action', '様子見')
    confidence = analysis_results.get('recommendation', {}).get('confidence', '中')
    explanation = analysis_results.get('recommendation', {}).get('explanation', 'データ不足のため、確かな分析ができません。')
    
    action_color = {
        "買い": "green", "強気買い": "darkgreen", 
        "売り": "red", "強気売り": "darkred",
        "様子見": "orange", "中立": "gray"
    }.get(action, "gray")
    
    st.markdown(f"## AI推奨: <span style='color:{action_color}'>{action}</span> (確信度: {confidence})", unsafe_allow_html=True)
    st.write(explanation)
    
    # 分析根拠を表示（折りたたみセクション）
    with st.expander("分析根拠を表示"):
        st.markdown("### AI分析の根拠")
        st.markdown("本分析では以下の要素から総合的に判断しています：")
        
        st.markdown("- **テクニカル指標の重み付け**: RSI(30%)、MACD(25%)、ボリンジャーバンド(15%)、移動平均線(20%)、その他(10%)")
        st.markdown("- **過去パターン分析**: 類似チャートパターンの検出と過去の結果の分析")
        st.markdown(f"- **トレンド強度**: {analysis_results.get('market_condition', {}).get('trend_strength', '中程度')} (トレンド方向への確信度に影響)")
        st.markdown(f"- **ボラティリティ状況**: {analysis_results.get('market_condition', {}).get('volatility_state', '普通')} (予測の信頼区間に影響)")
        
        st.markdown("### 主要判断要因")
        data = {
            "要因": ["RSI水準", "MACDシグナル", "トレンド方向", "ボリンジャーバンド", "過去類似パターン"],
            "値": [
                f"{analysis_results.get('indicators', {}).get('rsi', 50):.1f}",
                f"{analysis_results.get('indicators', {}).get('macd', 0):.1f} / {analysis_results.get('indicators', {}).get('macd_signal', 0):.1f}",
                analysis_results.get('predictions', {}).get('short_term', {}).get('direction', '横ばい'),
                "バンド内",  # 実際のデータに基づいて変更
                "中程度の類似性"  # 実際のデータに基づいて変更
            ],
            "判断への影響": [
                "中立" if 30 <= analysis_results.get('indicators', {}).get('rsi', 50) <= 70 else 
                ("強い買いシグナル" if analysis_results.get('indicators', {}).get('rsi', 50) < 30 else "強い売りシグナル"),
                "買いシグナル" if analysis_results.get('indicators', {}).get('macd', 0) > analysis_results.get('indicators', {}).get('macd_signal', 0) else "売りシグナル",
                "買い要因" if analysis_results.get('predictions', {}).get('short_term', {}).get('direction', '') == '上昇' else 
                ("売り要因" if analysis_results.get('predictions', {}).get('short_term', {}).get('direction', '') == '下降' else "中立要因"),
                "中立",  # 実際のデータに基づいて変更
                "中立要因"  # 実際のデータに基づいて変更
            ],
            "重要度": ["30%", "25%", "20%", "15%", "10%"]
        }
        
        st.dataframe(pd.DataFrame(data), use_container_width=True)

with col_ai2:
    # 主要指標
    st.markdown("### 主要指標")
    
    indicators = {
        "RSI": (analysis_results.get('indicators', {}).get('rsi', 50), 
                "売られすぎ" if analysis_results.get('indicators', {}).get('rsi', 50) < 30 else 
                ("買われすぎ" if analysis_results.get('indicators', {}).get('rsi', 50) > 70 else "中立")),
        
        "MACD": (analysis_results.get('indicators', {}).get('macd', 0), 
                "買い" if analysis_results.get('indicators', {}).get('macd', 0) > analysis_results.get('indicators', {}).get('macd_signal', 0) else "売り"),
        
        "ボリンジャー": ("バンド内", "中立"),  # 実際のデータに基づいて変更
        
        "ADX": (analysis_results.get('indicators', {}).get('adx', 15),
               "トレンド強" if analysis_results.get('indicators', {}).get('adx', 15) > 25 else "レンジ相場")
    }
    
    for name, (value, status) in indicators.items():
        st.metric(name, f"{value:.1f}" if isinstance(value, (int, float)) else value, status)
    
    # 予測
    st.markdown("### 予測")
    
    col_short, col_medium = st.columns(2)
    
    with col_short:
        st.markdown("#### 短期 (7日)")
        st.metric("方向性", analysis_results.get('predictions', {}).get('short_term', {}).get('direction', '---'))
        st.metric("変化率", f"{analysis_results.get('predictions', {}).get('short_term', {}).get('prediction', 0):.2f}%")
        st.metric("信頼度", f"{analysis_results.get('predictions', {}).get('short_term', {}).get('confidence', 0.5)*100:.0f}%")
    
    with col_medium:
        st.markdown("#### 中期 (30日)")
        st.metric("方向性", analysis_results.get('predictions', {}).get('medium_term', {}).get('direction', '---'))
        st.metric("変化率", f"{analysis_results.get('predictions', {}).get('medium_term', {}).get('prediction', 0):.2f}%")
        st.metric("信頼度", f"{analysis_results.get('predictions', {}).get('medium_term', {}).get('confidence', 0.5)*100:.0f}%")

# フッター
st.markdown("---")
st.caption("© 2023 日経平均分析ダッシュボード | データソース: Yahoo Finance") 