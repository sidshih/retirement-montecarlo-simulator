import streamlit as st
import yfinance as yf
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="退休蒙地卡羅模擬器", layout="wide")
st.title("📊 ETF 退休蒙地卡羅模擬器（進階版）")

# === 使用者輸入 ===
st.sidebar.header("參數設定")
tickers = st.sidebar.text_input("輸入ETF代號 (用逗號分隔)", "VTI,VXUS,BND").split(",")
weights = st.sidebar.text_input("輸入各ETF投資比例 (逗號分隔，總和=1)", "0.6,0.2,0.2")
weights = [float(w) for w in weights]
years = st.sidebar.number_input("退休年數", 10, 60, 30)
initial_assets = st.sidebar.number_input("初始資產 (美元)", 10000, 10000000, 1000000, step=10000)
annual_spending = st.sidebar.number_input("每年花費 (美元)", 1000, 200000, 40000, step=1000)
inflation = st.sidebar.number_input("年通膨率 (%)", 0.0, 10.0, 2.0) / 100
withdraw_rate = st.sidebar.slider("固定比例提領率 (%)", 1.0, 10.0, 4.0, step=0.5) / 100
n_sims = st.sidebar.slider("模擬次數", 1000, 20000, 5000, step=1000)

# === 下載ETF歷史數據 ===
data = yf.download(tickers, start="2005-01-01", end="2025-01-01")["Adj Close"].dropna()
returns = data.pct_change().dropna()
portfolio_returns = (returns @ np.array(weights))

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
