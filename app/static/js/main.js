// チャートのインスタンスを保持する変数
let priceChart;
let indicatorChart;
let advancedChart;

// カラーパレットの定義
const chartColors = {
    price: 'rgba(75, 192, 192, 1)',
    priceArea: 'rgba(75, 192, 192, 0.2)',
    ema20: 'rgba(255, 99, 132, 1)',
    ema50: 'rgba(54, 162, 235, 1)',
    ema200: 'rgba(255, 159, 64, 1)',
    volume: 'rgba(153, 102, 255, 0.5)',
    rsi: 'rgba(255, 99, 132, 1)',
    macd: 'rgba(54, 162, 235, 1)',
    signal: 'rgba(255, 159, 64, 1)',
    histogram: 'rgba(75, 192, 192, 0.5)',
    bullish: 'rgba(75, 192, 192, 0.7)',
    bearish: 'rgba(255, 99, 132, 0.7)',
    resistance: 'rgba(255, 99, 132, 0.3)',
    support: 'rgba(75, 192, 192, 0.3)',
    prediction: 'rgba(153, 102, 255, 1)',
    predictionArea: 'rgba(153, 102, 255, 0.2)'
};

// ページ読み込み時の処理
document.addEventListener('DOMContentLoaded', () => {
    // 初期データ取得（固定期間）
    fetchData('1y');
    
    // AIベースの詳細分析も初期取得
    fetchAIAnalysis('1y');
    
    // AI分析更新ボタンのイベントリスナー
    document.getElementById('refresh-ai-analysis').addEventListener('click', () => {
        fetchAIAnalysis('1y'); // 固定期間に変更
    });

    // タッチ操作の最適化
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    
    if (isTouchDevice) {
        // タッチデバイス向けの調整
        document.body.classList.add('touch-device');
        
        // ホバー効果の代わりにアクティブ効果を強化
        const interactiveElements = document.querySelectorAll('.btn, .nav-link, select, .card-header');
        interactiveElements.forEach(el => {
            el.addEventListener('touchstart', function() {
                this.classList.add('touch-active');
            });
            el.addEventListener('touchend', function() {
                this.classList.remove('touch-active');
            });
        });
    }
});

// APIからデータを取得する関数
async function fetchData(period) {
    try {
        console.log(`${period} のデータを取得中...`);
        
        // ローディング表示
        document.getElementById('latest-analysis').innerHTML = 
            '<div class="text-center my-4"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">市場データを取得中...</p></div>';
        
        // キャッシュを防止するためのタイムスタンプパラメータを追加
        const timestamp = new Date().getTime();
        const response = await fetch(`/api/nikkei/analysis?period=${period}&_t=${timestamp}`);
        
        if (!response.ok) {
            throw new Error('データの取得に失敗しました');
        }
        
        const data = await response.json();
        console.log("取得したデータ:", data);
        
        // サンプルフラグがある場合は通知
        if (data.sample) {
            console.warn("注意: サンプルデータを表示しています");
            showToast("サンプルデータを表示中", "APIからのデータ取得に問題があり、サンプルデータを表示しています。", "warning");
        }
        
        renderLatestAnalysis(data.latest);
        renderCharts(data.chart_data);
        
        // 基本データ取得後にAI分析も取得して両者を統合
        fetchAIAnalysis(period, data.latest);
    } catch (error) {
        console.error('エラーが発生しました:', error);
        document.getElementById('latest-analysis').innerHTML = 
            `<div class="alert alert-danger">
                <h5>データ取得エラー</h5>
                <p>${error.message}</p>
                <p>再読み込みするには期間を選択し直してください。</p>
            </div>`;
    }
}

// データの前処理
function preprocessChartData(chartData) {
    // 日付を新しい順にソート
    const sortedData = [...chartData].sort((a, b) => new Date(a.date) - new Date(b.date));
    
    // 移動平均線の計算
    const prices = sortedData.map(d => d.Price);
    sortedData.forEach((item, index) => {
        // 20日移動平均
        if (index >= 19) {
            const window = prices.slice(index - 19, index + 1);
            item.EMA20 = window.reduce((sum, val) => sum + val, 0) / 20;
        }
        
        // 50日移動平均
        if (index >= 49) {
            const window = prices.slice(index - 49, index + 1);
            item.EMA50 = window.reduce((sum, val) => sum + val, 0) / 50;
        }
        
        // 200日移動平均（データが十分にある場合）
        if (index >= 199) {
            const window = prices.slice(index - 199, index + 1);
            item.EMA200 = window.reduce((sum, val) => sum + val, 0) / 200;
        }
        
        // ボリンジャーバンド（20日）
        if (index >= 19) {
            const window = prices.slice(index - 19, index + 1);
            const sma = window.reduce((sum, val) => sum + val, 0) / 20;
            const squaredDiffs = window.map(val => Math.pow(val - sma, 2));
            const variance = squaredDiffs.reduce((sum, val) => sum + val, 0) / 20;
            const stdDev = Math.sqrt(variance);
            
            item.BollingerUpper = sma + (2 * stdDev);
            item.BollingerMiddle = sma;
            item.BollingerLower = sma - (2 * stdDev);
        }
        
        // ローソク足パターン検出（基本的なもの）
        if (index > 0) {
            const prev = sortedData[index - 1];
            const curr = item;
            
            // 陽線/陰線
            const prevChange = prev.Price - (prev.Open || prev.Price * 0.99);
            const currChange = curr.Price - (curr.Open || curr.Price * 0.99);
            
            item.Bullish = currChange > 0;
            
            // 反転パターン（簡易版）
            item.Reversal = (prevChange < 0 && currChange > 0) || (prevChange > 0 && currChange < 0);
        }
    });
    
    return sortedData;
}

// 最新の分析結果を表示
function renderLatestAnalysis(latestData) {
    const analysisDiv = document.getElementById('latest-analysis');
    
    // 指標のシグナル計算
    const rsiSignal = getRsiSignal(latestData.rsi);
    const macdSignal = latestData.macd > latestData.signal ? '買い' : '売り';
    
    // 総合シグナル計算
    const overallSignal = calculateOverallSignal(latestData);
    const signalClass = getSignalClass(overallSignal);
    
    // HTML生成
    analysisDiv.innerHTML = `
        <div class="text-center mb-3">
            <h3 class="mb-0">¥${latestData.price.toLocaleString()}</h3>
            <small class="text-muted">${latestData.date}</small>
        </div>
        
        <div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="mb-0">市場シグナル</h5>
            <span class="badge bg-${signalClass}">${overallSignal}</span>
        </div>
        
        <div class="row mb-3">
            <div class="col-6">
                <div class="card">
                    <div class="card-body p-2 text-center">
                        <div class="small text-muted">RSI</div>
                        <div class="indicator-value ${latestData.rsi > 70 ? 'rsi-overbought' : (latestData.rsi < 30 ? 'rsi-oversold' : 'rsi-neutral')}">
                            ${latestData.rsi.toFixed(1)}
                        </div>
                        <span class="badge ${getRsiBadgeClass(latestData.rsi)}">${rsiSignal}</span>
                    </div>
                </div>
            </div>
            <div class="col-6">
                <div class="card">
                    <div class="card-body p-2 text-center">
                        <div class="small text-muted">MACD</div>
                        <div class="indicator-value">
                            ${latestData.macd.toFixed(1)}
                        </div>
                        <span class="badge ${getMacdBadgeClass(latestData.macd, latestData.signal)}">${macdSignal}</span>
                    </div>
                </div>
            </div>
        </div>
        
        <p class="mb-1">${getMarketSummary(latestData)}</p>
    `;
}

// チャート描画関数
function renderCharts(chartData) {
    if (!chartData || chartData.length === 0) {
        console.error('チャートデータが空です');
        return;
    }

    // 日付を新しい順にソート
    const sortedData = [...chartData].sort((a, b) => new Date(a.date) - new Date(b.date));
    
    // データの準備
    const dates = sortedData.map(d => d.date);
    const prices = sortedData.map(d => d.Price);
    const rsiValues = sortedData.map(d => d.RSI);
    const macdValues = sortedData.map(d => d.MACD);
    const signalValues = sortedData.map(d => d.Signal);
    
    // 既存のチャートを破棄
    if (priceChart) {
        priceChart.destroy();
    }
    if (indicatorChart) {
        indicatorChart.destroy();
    }
    
    // チャートコンテナの高さを設定
    document.getElementById('price-chart').setAttribute('height', '300');
    document.getElementById('price-chart').style.cssText = 'height:300px !important; max-height:300px !important;';
    
    document.getElementById('indicator-chart').setAttribute('height', '200');
    document.getElementById('indicator-chart').style.cssText = 'height:200px !important; max-height:200px !important;';
    
    // 価格チャート
    const priceCtx = document.getElementById('price-chart').getContext('2d');
    priceChart = new Chart(priceCtx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: '日経平均',
                data: prices,
                borderColor: 'rgba(75, 192, 192, 1)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                pointHoverRadius: 5,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                },
                labels: {
                    font: {
                        size: window.innerWidth < 768 ? 10 : 12
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45,
                        autoSkip: true,
                        maxTicksLimit: window.innerWidth < 768 ? 6 : 12,
                        font: {
                            size: window.innerWidth < 768 ? 10 : 12
                        }
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return '¥' + value.toLocaleString();
                        },
                        font: {
                            size: window.innerWidth < 768 ? 10 : 12
                        }
                    }
                }
            }
        }
    });
    
    // 指標チャート
    const indicatorCtx = document.getElementById('indicator-chart').getContext('2d');
    indicatorChart = new Chart(indicatorCtx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'RSI',
                    data: rsiValues,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    yAxisID: 'y-rsi',
                    tension: 0.4,
                    pointRadius: 0,
                    borderWidth: 2
                },
                {
                    label: 'MACD',
                    data: macdValues,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    yAxisID: 'y-macd',
                    tension: 0.4,
                    pointRadius: 0,
                    borderWidth: 2
                },
                {
                    label: 'Signal',
                    data: signalValues,
                    borderColor: 'rgba(255, 159, 64, 1)',
                    backgroundColor: 'rgba(255, 159, 64, 0.2)',
                    yAxisID: 'y-macd',
                    tension: 0.4,
                    pointRadius: 0,
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                labels: {
                    font: {
                        size: window.innerWidth < 768 ? 10 : 12
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45,
                        autoSkip: true,
                        maxTicksLimit: window.innerWidth < 768 ? 6 : 12,
                        font: {
                            size: window.innerWidth < 768 ? 10 : 12
                        }
                    },
                    grid: {
                        display: false
                    }
                },
                'y-rsi': {
                    position: 'left',
                    beginAtZero: false,
                    min: 0,
                    max: 100,
                    grid: {
                        color: 'rgba(255, 99, 132, 0.2)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value;
                        },
                        font: {
                            size: window.innerWidth < 768 ? 10 : 12
                        }
                    }
                },
                'y-macd': {
                    position: 'right',
                    beginAtZero: false,
                    grid: {
                        color: 'rgba(54, 162, 235, 0.2)'
                    }
                }
            }
        }
    });
}

// RSIのシグナルを取得
function getRsiSignal(rsi) {
    if (rsi > 70) return '売り';
    if (rsi < 30) return '買い';
    return '中立';
}

// RSIのバッジクラスを取得
function getRsiBadgeClass(rsi) {
    if (rsi > 70) return 'bg-danger';
    if (rsi < 30) return 'bg-success';
    return 'bg-secondary';
}

// MACDのバッジクラスを取得
function getMacdBadgeClass(macd, signal) {
    return macd > signal ? 'bg-success' : 'bg-danger';
}

// 総合シグナルを計算
function calculateOverallSignal(data) {
    let buySignals = 0;
    let sellSignals = 0;
    
    // RSI
    if (data.rsi < 30) buySignals += 1;
    else if (data.rsi > 70) sellSignals += 1;
    
    // MACD
    if (data.macd > data.signal) buySignals += 1;
    else sellSignals += 1;
    
    // 総合判定
    if (buySignals > sellSignals + 1) return '強い買い';
    if (buySignals > sellSignals) return '弱い買い';
    if (sellSignals > buySignals + 1) return '強い売り';
    if (sellSignals > buySignals) return '弱い売り';
    return '中立';
}

// シグナルに応じたクラスを取得
function getSignalClass(signal) {
    if (signal.includes('買い')) return 'success';
    if (signal.includes('売り')) return 'danger';
    return 'warning';
}

// 市場サマリーテキストを生成
function getMarketSummary(data) {
    const signal = calculateOverallSignal(data);
    
    if (signal === '強い買い') 
        return '短期的な買い場の可能性が高いです。RSIが売られすぎの水準にあり、MACDも買いシグナルを示しています。';
    
    if (signal === '弱い買い') 
        return '弱気ながらも買いサインが出ています。慎重に様子を見ながら買い増しの検討が可能です。';
    
    if (signal === '強い売り') 
        return '短期的な売り圧力が強まっています。利益確定や一部売却の検討をお勧めします。';
    
    if (signal === '弱い売り') 
        return '弱気ながらも売りサインが出ています。新規買い増しは控え目にすることをお勧めします。';
    
    return '明確な方向性が見られません。様子見が推奨されます。';
}

// トースト通知を表示
function showToast(title, message, type = 'info') {
    // トースト表示用のHTMLがなければ追加
    if (!document.getElementById('toast-container')) {
        const toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed bottom-0 end-0 p-3';
        toastContainer.style.zIndex = '11';
        document.body.appendChild(toastContainer);
    }
    
    const toastId = 'toast-' + new Date().getTime();
    const toastHTML = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-${type} text-white">
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    document.getElementById('toast-container').innerHTML += toastHTML;
    
    // Bootstrap 5のToastを初期化して表示
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 5000
    });
    toast.show();
    
    // 一定時間後に削除
    setTimeout(() => {
        toastElement.remove();
    }, 5500);
}

// AI分析を取得する関数
async function fetchAIAnalysis(period, basicAnalysis = null) {
    try {
        const timestamp = new Date().getTime();
        document.getElementById('ai-analysis').innerHTML = 
            '<div class="text-center my-4"><div class="spinner-border text-primary" role="status"></div><p class="mt-2">AIによる高度な市場分析を実行中...</p></div>';
        
        console.log(`AI分析データを取得中: 期間=${period}`);
        
        const response = await fetch(`/api/nikkei/ai-analysis?period=${period}&_t=${timestamp}`);
        console.log("AI分析レスポンスステータス:", response.status);
        
        const data = await response.json();
        console.log("AI分析データ:", data);
        
        if (data.error) {
            throw new Error(data.error || "不明なエラー");
        }
        
        if (data.sample) {
            console.warn("注意: AI分析のサンプルデータを表示しています");
        }
        
        if (data.analysis) {
            // 基本分析結果が提供されている場合は整合性を調整
            if (basicAnalysis) {
                updateBasicAnalysisWithAIInsights(basicAnalysis, data.analysis);
            }
            
            renderAIAnalysis(data.analysis);
        } else {
            throw new Error("AI分析データがありません");
        }
    } catch (error) {
        console.error('AI分析取得エラー:', error);
        document.getElementById('ai-analysis').innerHTML = 
            `<div class="alert alert-danger">
                <h5>AI分析の取得中にエラーが発生しました</h5>
                <p>${error.message}</p>
                <p>再試行するには「高度分析を更新」ボタンをクリックしてください。</p>
            </div>`;
    }
}

// AI分析の洞察を基本分析に統合
function updateBasicAnalysisWithAIInsights(basicAnalysis, aiAnalysis) {
    // すでに表示された基本分析を更新
    const analysisDiv = document.getElementById('latest-analysis');
    const currentHTML = analysisDiv.innerHTML;
    
    // AI分析からの重要な洞察を抽出
    const aiRecommendation = aiAnalysis.recommendation?.action || '判断中';
    const aiConfidence = aiAnalysis.recommendation?.confidence || '低';
    const aiExplanation = aiAnalysis.recommendation?.explanation || '';
    
    // 現在の総合シグナルとAI推奨の整合性を確認
    const basicSignal = calculateOverallSignal(basicAnalysis);
    let combinedSignal, combinedClass;
    
    // 基本シグナルとAI推奨を統合
    if (aiRecommendation === '買い' && basicSignal.includes('買い')) {
        combinedSignal = '強い買い';
        combinedClass = 'success';
    } else if (aiRecommendation === '売り' && basicSignal.includes('売り')) {
        combinedSignal = '強い売り';
        combinedClass = 'danger';
    } else if (aiRecommendation === '買い' || basicSignal.includes('買い')) {
        combinedSignal = '弱い買い';
        combinedClass = 'success';
    } else if (aiRecommendation === '売り' || basicSignal.includes('売り')) {
        combinedSignal = '弱い売り';
        combinedClass = 'danger';
    } else {
        combinedSignal = '中立';
        combinedClass = 'warning';
    }
    
    // 整合性のあるメッセージを表示（コメントでAI見解も表示）
    const updatedHTML = currentHTML.replace(
        /<div class="d-flex justify-content-between align-items-center mb-3">[\s\S]*?<\/div>/,
        `<div class="d-flex justify-content-between align-items-center mb-3">
            <h5 class="mb-0">市場シグナル</h5>
            <span class="badge bg-${combinedClass}">${combinedSignal}</span>
        </div>`
    );
    
    // 更新されたサマリーを追加
    const updatedSummaryHTML = updatedHTML.replace(
        /<p class="mb-1">.*?<\/p>/,
        `<p class="mb-1">${getMarketSummary(basicAnalysis)}</p>
         <p class="text-muted small">AI見解: ${aiExplanation}</p>`
    );
    
    // HTMLを更新
    analysisDiv.innerHTML = updatedSummaryHTML;
}

// AI分析結果を表示する関数
function renderAIAnalysis(analysis) {
    const analysisDiv = document.getElementById('ai-analysis');
    
    // モバイル向けにテンプレートを調整
    const isMobile = window.innerWidth < 768;
    
    // 推奨アクションに基づくスタイル設定
    let actionClass, actionIcon;
    switch(analysis.recommendation?.action) {
        case '買い':
            actionClass = 'text-success';
            actionIcon = '↑';
            break;
        case '売り':
            actionClass = 'text-danger';
            actionIcon = '↓';
            break;
        default:
            actionClass = 'text-warning';
            actionIcon = '→';
    }
    
    // 信頼度レベルの表示
    let confidenceStars = '';
    if (analysis.recommendation?.confidence === '高') {
        confidenceStars = '★★★';
    } else if (analysis.recommendation?.confidence === '中') {
        confidenceStars = '★★☆';
    } else {
        confidenceStars = '★☆☆';
    }
    
    // 市場状況に応じたバッジクラス
    let marketPhaseClass = 'bg-secondary';
    if (analysis.market_condition?.market_phase?.includes('強気')) {
        marketPhaseClass = 'bg-success';
    } else if (analysis.market_condition?.market_phase?.includes('弱気')) {
        marketPhaseClass = 'bg-danger';
    }
    
    // 各指標の方向性アイコン
    const getTrendIcon = (value, threshold1, threshold2) => {
        if (value > threshold2) return '↑↑';
        if (value > threshold1) return '↑';
        if (value < -threshold2) return '↓↓';
        if (value < -threshold1) return '↓';
        return '→';
    };
    
    // テンプレートを構築
    analysisDiv.innerHTML = `
        <div class="row">
            <div class="col-md-8">
                <div class="card mb-4">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">AI分析結果</h5>
                        <span class="badge bg-primary">${analysis.date}</span>
                    </div>
                    <div class="card-body">
                        <!-- モバイル向けにレイアウト調整 -->
                        <div class="${isMobile ? '' : 'd-flex justify-content-between'}">
                            <div class="${isMobile ? 'mb-3' : ''}">
                                <h2 class="mb-0">¥${analysis.price.toLocaleString()}</h2>
                                <small class="text-muted">最新価格</small>
                            </div>
                            <div class="${isMobile ? 'mb-3' : ''}">
                                <h4 class="mb-0">
                                    <span class="badge ${getBadgeClass(analysis.recommendation.action)}">
                                        ${analysis.recommendation.action}
                                    </span>
                                </h4>
                                <small class="text-muted">推奨アクション</small>
                            </div>
                            <div>
                                <h4 class="mb-0">
                                    <span class="badge bg-info">
                                        信頼度: ${analysis.recommendation.confidence}
                                    </span>
                                </h4>
                                <small class="text-muted">AI信頼性</small>
                            </div>
                        </div>
                        
                        <!-- 分析根拠を表示する折りたたみセクション -->
                        <div class="mt-3">
                            <a class="btn btn-sm btn-outline-secondary" data-bs-toggle="collapse" href="#aiReasoningDetail" role="button" aria-expanded="false">
                                分析根拠を表示 ▼
                            </a>
                            <div class="collapse mt-3" id="aiReasoningDetail">
                                <div class="card card-body bg-light">
                                    <h6 class="card-title">AI分析の根拠</h6>
                                    <p class="mb-2">本分析では以下の要素から総合的に判断しています：</p>
                                    <ul class="small">
                                        <li><strong>テクニカル指標の重み付け：</strong> RSI(30%)、MACD(25%)、ボリンジャーバンド(15%)、移動平均線(20%)、その他(10%)</li>
                                        <li><strong>過去パターン分析：</strong> 類似チャートパターンの検出と過去の結果の分析</li>
                                        <li><strong>トレンド強度：</strong> ${analysis.market_condition?.trend_strength || '中程度'} (トレンド方向への確信度に影響)</li>
                                        <li><strong>ボラティリティ状況：</strong> ${analysis.market_condition?.volatility_state || '普通'} (予測の信頼区間に影響)</li>
                                    </ul>
                                    
                                    <h6 class="mt-3">主要判断要因</h6>
                                    <div class="table-responsive">
                                        <table class="table table-sm table-bordered">
                                            <thead class="table-light">
                                                <tr>
                                                    <th>要因</th>
                                                    <th>値</th>
                                                    <th>判断への影響</th>
                                                    <th>重要度</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                <tr>
                                                    <td>RSI水準</td>
                                                    <td>${analysis.indicators?.rsi?.toFixed(1) || '50'}</td>
                                                    <td>${analysis.indicators?.rsi < 30 ? '強い買いシグナル' : 
                                                          (analysis.indicators?.rsi > 70 ? '強い売りシグナル' : '中立')}</td>
                                                    <td>
                                                        <div class="progress" style="height: 8px;">
                                                            <div class="progress-bar bg-primary" role="progressbar" style="width: 30%;" 
                                                                aria-valuenow="30" aria-valuemin="0" aria-valuemax="100"></div>
                                                        </div>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td>MACDシグナル</td>
                                                    <td>${analysis.indicators?.macd?.toFixed(1) || '0'} / ${analysis.indicators?.macd_signal?.toFixed(1) || '0'}</td>
                                                    <td>${analysis.indicators?.macd > analysis.indicators?.macd_signal ? '買いシグナル' : '売りシグナル'}</td>
                                                    <td>
                                                        <div class="progress" style="height: 8px;">
                                                            <div class="progress-bar bg-primary" role="progressbar" style="width: 25%;" 
                                                                aria-valuenow="25" aria-valuemin="0" aria-valuemax="100"></div>
                                                        </div>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td>トレンド方向</td>
                                                    <td>${analysis.predictions?.short_term?.direction || '横ばい'}</td>
                                                    <td>${analysis.predictions?.short_term?.direction === '上昇' ? '買い要因' : 
                                                          (analysis.predictions?.short_term?.direction === '下降' ? '売り要因' : '中立要因')}</td>
                                                    <td>
                                                        <div class="progress" style="height: 8px;">
                                                            <div class="progress-bar bg-primary" role="progressbar" style="width: 20%;" 
                                                                aria-valuenow="20" aria-valuemin="0" aria-valuemax="100"></div>
                                                        </div>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td>ボリンジャーバンド</td>
                                                    <td>${analysis.price > analysis.indicators?.bollinger?.upper ? '上限超え' : 
                                                          (analysis.price < analysis.indicators?.bollinger?.lower ? '下限超え' : 'バンド内')}</td>
                                                    <td>${analysis.price > analysis.indicators?.bollinger?.upper ? '売り要因' : 
                                                          (analysis.price < analysis.indicators?.bollinger?.lower ? '買い要因' : '中立')}</td>
                                                    <td>
                                                        <div class="progress" style="height: 8px;">
                                                            <div class="progress-bar bg-primary" role="progressbar" style="width: 15%;" 
                                                                aria-valuenow="15" aria-valuemin="0" aria-valuemax="100"></div>
                                                        </div>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td>過去類似パターン</td>
                                                    <td>${analysis.predictions?.short_term?.confidence > 0.7 ? '高い類似性' : 
                                                          (analysis.predictions?.short_term?.confidence > 0.5 ? '中程度の類似性' : '低い類似性')}</td>
                                                    <td>${analysis.predictions?.short_term?.direction === '上昇' ? '買い要因' : 
                                                          (analysis.predictions?.short_term?.direction === '下降' ? '売り要因' : '中立要因')}</td>
                                                    <td>
                                                        <div class="progress" style="height: 8px;">
                                                            <div class="progress-bar bg-primary" role="progressbar" style="width: 10%;" 
                                                                aria-valuenow="10" aria-valuemin="0" aria-valuemax="100"></div>
                                                        </div>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                    
                                    <h6 class="mt-3">信頼度の根拠</h6>
                                    <p class="small">
                                        信頼度は以下の要素から算出されています：<br>
                                        - 各指標の一致度: ${Math.round((analysis.predictions?.short_term?.confidence || 0.5) * 100)}%<br>
                                        - 市場のボラティリティ: ${analysis.market_condition?.volatility_state || '普通'}<br>
                                        - トレンド強度: ${analysis.market_condition?.trend_strength || '中程度'}<br>
                                        - 過去類似パターンの精度: ${Math.round((analysis.predictions?.short_term?.confidence || 0.5) * 80)}%
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <div class="card mb-3">
                            <div class="card-body">
                                <h5 class="card-title">短期予測 (7日)</h5>
                                <p class="mb-1">方向性: <strong>${analysis.predictions?.short_term?.direction || '---'}</strong></p>
                                <p class="mb-1">予測変化率: <strong>${analysis.predictions?.short_term?.prediction?.toFixed(2) || '---'}%</strong></p>
                                <p>信頼度: ${(analysis.predictions?.short_term?.confidence * 100)?.toFixed(0) || '---'}%</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card mb-3">
                            <div class="card-body">
                                <h5 class="card-title">中期予測 (30日)</h5>
                                <p class="mb-1">方向性: <strong>${analysis.predictions?.medium_term?.direction || '---'}</strong></p>
                                <p class="mb-1">予測変化率: <strong>${analysis.predictions?.medium_term?.prediction?.toFixed(2) || '---'}%</strong></p>
                                <p>信頼度: ${(analysis.predictions?.medium_term?.confidence * 100)?.toFixed(0) || '---'}%</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="card mb-3">
                    <div class="card-header">市場状況</div>
                    <div class="card-body">
                        <div class="mb-2">
                            <span class="badge ${marketPhaseClass}">${analysis.market_condition?.market_phase || '---'}</span>
                            <span class="badge bg-info">トレンド強度: ${analysis.market_condition?.trend_strength || '---'}</span>
                            <span class="badge bg-secondary">ボラティリティ: ${analysis.market_condition?.volatility_state || '---'}</span>
                        </div>
                        <p>市場センチメント: <strong>${analysis.market_condition?.market_sentiment || '---'}</strong></p>
                        <p>現在価格: <strong>¥${analysis.price?.toLocaleString() || '---'}</strong></p>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card mb-3">
                    <div class="card-header">主要指標</div>
                    <div class="card-body">
                        <table class="table table-sm">
                            <tr>
                                <td>RSI</td>
                                <td><strong>${analysis.indicators?.rsi?.toFixed(1) || '---'}</strong></td>
                                <td>${analysis.indicators?.rsi < 30 ? '📉 売られすぎ' : (analysis.indicators?.rsi > 70 ? '📈 買われすぎ' : '→ 中立')}</td>
                            </tr>
                            <tr>
                                <td>MACD</td>
                                <td><strong>${analysis.indicators?.macd?.toFixed(1) || '---'}</strong></td>
                                <td>${analysis.indicators?.macd > analysis.indicators?.macd_signal ? '📈 買い' : '📉 売り'}</td>
                            </tr>
                            <tr>
                                <td>ボリンジャー</td>
                                <td>${analysis.price > analysis.indicators?.bollinger?.upper ? '上限超え' : 
                                     (analysis.price < analysis.indicators?.bollinger?.lower ? '下限超え' : 'バンド内')}</td>
                                <td>${analysis.price > analysis.indicators?.bollinger?.upper ? '📉 売り' : 
                                     (analysis.price < analysis.indicators?.bollinger?.lower ? '📈 買い' : '→ 中立')}</td>
                            </tr>
                            <tr>
                                <td>ADX</td>
                                <td><strong>${analysis.indicators?.adx?.toFixed(1) || '---'}</strong></td>
                                <td>${analysis.indicators?.adx > 25 ? '📊 トレンド強' : '📐 レンジ相場'}</td>
                            </tr>
                        </table>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">サポート・レジスタンス</div>
                    <div class="card-body">
                        <div id="key-levels">
                            ${analysis.market_condition?.key_levels?.map(level => `
                                <div class="mb-2">
                                    <span class="badge ${level.type === 'サポート' ? 'bg-success' : 'bg-danger'}">${level.type}</span>
                                    <strong>¥${level.price.toLocaleString()}</strong>
                                    <small>(強度: ${level.strength})</small>
                                </div>
                            `).join('') || '主要レベルなし'}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// ウィンドウサイズ変更時にチャートを再描画
window.addEventListener('resize', function() {
    if (priceChart) {
        priceChart.resize();
    }
    if (indicatorChart) {
        indicatorChart.resize();
    }
    if (advancedChart) {
        advancedChart.resize();
    }
});

// 推奨アクションに基づいてバッジクラスを返す関数
function getBadgeClass(action) {
    switch(action) {
        case '買い':
        case '強い買い':
            return 'bg-success';
        case '売り':
        case '強い売り':
            return 'bg-danger';
        case '様子見':
            return 'bg-warning';
        default:
            return 'bg-secondary';
    }
}

// RSIの値に基づいてバッジクラスを返す関数
function getRsiBadgeClass(rsi) {
    if (rsi > 70) return 'bg-danger';
    if (rsi < 30) return 'bg-success';
    return 'bg-secondary';
}

// MACDの値に基づいてバッジクラスを返す関数
function getMacdBadgeClass(macd, signal) {
    if (macd > signal) return 'bg-success';
    return 'bg-danger';
} 