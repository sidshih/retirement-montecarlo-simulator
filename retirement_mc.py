import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

st.title("📊 ETF 退休蒙地卡羅模擬器")

# === 使用者輸入 ===
st.sidebar.header("參數設定")
tickers = st.sidebar.text_input("輸入ETF代號 (用逗號分隔)", "VTI,VXUS,BND").split(",")
weights = st.sidebar.text_input("輸入各ETF投資比例 (逗號分隔，總和=1)", "0.6,0.2,0.2")
weights = [float(w) for w in weights]
years = st.sidebar.number_input("退休年數", 10, 60, 30)
initial_assets = st.sidebar.number_input("初始資產 (美元)", 10000, 10000000, 1000000, step=10000)
annual_spending = st.sidebar.number_input("每年花費 (美元)", 1000, 200000, 40000, step=1000)
inflation = st.sidebar.number_input("年通膨率 (%)", 0.0, 10.0, 2.0) / 100
n_sims = st.sidebar.slider("模擬次數", 1000, 20000, 5000, step=1000)

# === 下載ETF歷史數據 ===
data = yf.download(tickers, start="2005-01-01", end="2025-01-01")["Adj Close"].dropna()
returns = data.pct_change().dropna()
portfolio_returns = (returns @ np.array(weights))

# === 蒙地卡羅模擬 ===
def run_simulation():
    results = []
    for sim in range(n_sims):
        assets = initial_assets
        for y in range(years):
            # 隨機抽樣一個年化報酬率 (bootstrap)
            yearly_return = (1 + np.random.choice(portfolio_returns)) ** 12 - 1
            assets *= (1 + yearly_return)
            # 花費（考慮通膨）
            spend = annual_spending * ((1 + inflation) ** y)
            assets -= spend
            if assets <= 0:
                assets = 0
                break
        results.append(assets)
    return results

results = run_simulation()

# === 結果顯示 ===
success_rate = np.mean([r > 0 for r in results]) * 100
st.subheader(f"✅ 成功率: {success_rate:.2f}%")

fig, ax = plt.subplots()
ax.hist(results, bins=50, alpha=0.7)
ax.axvline(np.median(results), color="red", linestyle="--", label=f"中位數: {np.median(results):,.0f}")
ax.set_title("模擬最終資產分布")
ax.set_xlabel("最終資產 (美元)")
ax.set_ylabel("出現次數")
ax.legend()
st.pyplot(fig)
