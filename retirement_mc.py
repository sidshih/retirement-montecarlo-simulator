import streamlit as st
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="退休蒙地卡羅模擬器", layout="wide")
st.title("📊 ETF 退休蒙地卡羅模擬器（進階版）")

# === 使用者輸入 ===
st.sidebar.header("參數設定")

# 預設值
default_tickers = "VTI,VXUS,BND"
default_weights = "0.6,0.2,0.2"

# 範例按鈕
if st.sidebar.button("載入範例組合 (VTI 60%, VXUS 20%, BND 20%)"):
    st.session_state["tickers_input"] = default_tickers
    st.session_state["weights_input"] = default_weights

# ETF 輸入
tickers = st.sidebar.text_input(
    "輸入ETF代號 (用逗號分隔)", 
    st.session_state.get("tickers_input", default_tickers)
).split(",")

# 投資比例輸入
weights_str = st.sidebar.text_input(
    "輸入各ETF投資比例 (逗號分隔，總和=1)", 
    st.session_state.get("weights_input", default_weights)
)

try:
    weights = [float(w.strip()) for w in weights_str.split(",") if w.strip() != ""]
except ValueError:
    st.error("⚠️ 投資比例必須是數字，請重新輸入，例如: 0.6,0.2,0.2")
    st.stop()

if len(weights) != len(tickers):
    st.error(f"⚠️ ETF 數量 ({len(tickers)}) 與 比例數量 ({len(weights)}) 不一致")
    st.stop()

if abs(sum(weights) - 1.0) > 1e-6:
    st.error("⚠️ 投資比例總和必須等於 1")
    st.stop()

# 其他參數
years = st.sidebar.number_input("退休年數", 10, 60, 30)
initial_assets = st.sidebar.number_input("初始資產 (美元)", 10000, 10000000, 1000000, step=10000)
annual_spending = st.sidebar.number_input("每年花費 (美元)", 1000, 200000, 40000, step=1000)
inflation = st.sidebar.number_input("年通膨率 (%)", 0.0, 10.0, 2.0) / 100
withdraw_rate = st.sidebar.slider("固定比例提領率 (%)", 1.0, 10.0, 4.0, step=0.5) / 100
n_sims = st.sidebar.slider("模擬次數", 1000, 20000, 5000, step=1000)

# === 下載ETF歷史數據 ===
try:
    data = yf.download(tickers, start="2005-01-01", end="2025-01-01")
except Exception as e:
    st.error(f"⚠️ 下載 ETF 數據時發生錯誤：{e}")
    st.stop()

# 檢查下載的數據是否為空
if data.empty:
    st.error("⚠️ 無法下載 ETF 數據，請檢查代號是否正確。")
    st.stop()

# 統一處理 "Adj Close" 欄位
# yfinance 在下載單一股票時，回傳的 DataFrame 結構與多個股票不同
if isinstance(data.columns, pd.MultiIndex):
    # 下載多個 ETF，欄位是多層索引
    data = data["Adj Close"]
else:
    # 下載單一 ETF，欄位是單層索引
    if "Adj Close" in data.columns:
        # 使用雙層方括號 [[...]] 確保結果仍然是 DataFrame
        data = data[["Adj Close"]]
    else:
        st.error("⚠️ 歷史數據中找不到 'Adj Close' 欄位。")
        st.stop()

data = data.dropna()
returns = data.pct_change().dropna()

# 確保在只有一個 ETF 的情況下，weights 也是一個 NumPy 陣列
weights_array = np.array(weights)

portfolio_returns = (returns @ weights_array)

# === 蒙地卡羅模擬函數 ===
def run_simulation(strategy="fixed"):
    results = []
    paths = []
    for sim in range(n_sims):
        assets = initial_assets
        yearly_assets = [assets]
        for y in range(years):
            yearly_return = (1 + np.random.choice(portfolio_returns)) ** 12 - 1
            assets *= (1 + yearly_return)
            if strategy == "fixed":
                spend = annual_spending * ((1 + inflation) ** y)
            elif strategy == "percent":
                spend = assets * withdraw_rate
            assets -= spend
            if assets <= 0:
                assets = 0
                yearly_assets.append(assets)
                break
            yearly_assets.append(assets)
        results.append(assets)
        paths.append(yearly_assets)
    return results, paths

# === 模擬兩種策略 ===
results_fixed, paths_fixed = run_simulation("fixed")
results_percent, paths_percent = run_simulation("percent")

# === 成功率 ===
success_rate_fixed = np.mean([r > 0 for r in results_fixed]) * 100
success_rate_percent = np.mean([r > 0 for r in results_percent]) * 100

st.subheader("📈 成功率比較")
st.write(f"固定金額提領（考慮通膨） ➜ **{success_rate_fixed:.2f}%**")
st.write(f"固定比例提領（{withdraw_rate*100:.1f}% rule） ➜ **{success_rate_percent:.2f}%**")

# === 資產分布圖 ===
fig, ax = plt.subplots()
ax.hist(results_fixed, bins=50, alpha=0.5, label="固定金額提領")
ax.hist(results_percent, bins=50, alpha=0.5, label="固定比例提領")
ax.axvline(np.median(results_fixed), color="blue", linestyle="--", label=f"固定金額中位數: {np.median(results_fixed):,.0f}")
ax.axvline(np.median(results_percent), color="red", linestyle="--", label=f"比例提領中位數: {np.median(results_percent):,.0f}")
ax.set_title("模擬最終資產分布")
ax.set_xlabel("最終資產 (美元)")
ax.set_ylabel("次數")
ax.legend()
st.pyplot(fig)

# === 資產曲線模擬圖 ===
fig2, ax2 = plt.subplots()
for path in paths_fixed[:30]:
    ax2.plot(path, color="blue", alpha=0.2)
for path in paths_percent[:30]:
    ax2.plot(path, color="red", alpha=0.2)
ax2.set_title("部分模擬資產走勢 (藍=固定金額, 紅=比例提領)")
ax2.set_xlabel("年份")
ax2.set_ylabel("資產 (美元)")
st.pyplot(fig2)

# === 下載模擬結果 CSV ===
st.subheader("📥 下載模擬結果")
df_results = pd.DataFrame({
    "固定金額提領": results_fixed,
    "比例提領": results_percent
})
csv = df_results.to_csv(index=False).encode("utf-8")
st.download_button(
    label="下載模擬結果 CSV",
    data=csv,
    file_name="retirement_simulation_results.csv",
    mime="text/csv",
)
