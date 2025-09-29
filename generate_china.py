import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pandas_datareader import data as web
from datetime import datetime

# -------------------------------
# 1. Define Tickers and Invert List
# -------------------------------

tickers = {
    "FXI.US": "FXI.US",         # China Large-Cap
    "MCHI.US": "MCHI.US",       # MSCI China
    "KWEB.US": "KWEB.US",       # China Internet
    "ASHR.US": "ASHR.US",       # A-shares
    "AIA.US": "AIA.US",         # Asia ex-Japan
    "EEM.US": "EEM.US",         # Emerging Markets
    "CPER.US": "CPER.US",       # Copper
    "BNO.US": "BNO.US",         # Brent Oil
    "SLX.US": "SLX.US",         # Steel
    "WOOD.US": "WOOD.US",       # Timber
    "XME.US": "XME.US",         # Metals & Mining
    "XLI.US": "XLI.US",         # Industrials
    "IYT.US": "IYT.US",         # Transportation
    "CNYB.US": "CNYB.US",       # China Bonds
    "DBC.US": "DBC.US",         # Broad Commodities
    "SEA.US": "SEA.US",         # Shipping
    "VAW.US": "VAW.US",         # Materials
    "VWO.US": "VWO.US",         # EM via Vanguard
    "EWT.US": "EWT.US",         # Taiwan
    "KORU.US": "KORU.US",       # Korea
}

invert_list = ['CNYB.US']  # You can add others if they appear on Stooq

# -------------------------------
# 2. Download Data via Stooq
# -------------------------------

start = "1995-01-01"
end = datetime.today().strftime("%Y-%m-%d")

df_all = pd.DataFrame()

for name, ticker in tickers.items():
    try:
        df = web.DataReader(ticker, "stooq", start=start, end=end)
        df = df[::-1]  # reverse Stooq data (comes in descending order)
        df_all[name] = df["Close"]
    except Exception as e:
        print(f"Failed to load {name}: {e}")

df_all = df_all.dropna(axis=1, thresh=int(len(df_all) * 0.75))


# -------------------------------
# 3. Compute Z-Scores
# -------------------------------

n_day = 200
n_smooth = 30

z_scores = pd.DataFrame(index=df_all.index)

for col in df_all.columns:
    price = df_all[col]
    ma = price.rolling(n_day).mean()
    std = price.rolling(n_day).std()
    z = (price - ma) / std

    if col in invert_list:
        z = -z

    z_scores[col] = z

# -------------------------------
# 4. Composite Score
# -------------------------------
# -----------------------------------
# Define bucket mapping
# -----------------------------------
bucket_map = {
    "China_Equities": ["FXI.US", "MCHI.US", "KWEB.US", "ASHR.US"],
    "Regional_Equities": ["AIA.US", "EEM.US", "VWO.US", "EWT.US", "KORU.US"],
    "Commodities": ["CPER.US", "BNO.US", "SLX.US", "WOOD.US", "XME.US", "DBC.US", "VAW.US"],
    "Industrials_Trade": ["XLI.US", "IYT.US", "SEA.US"],
    "Rates_Bonds": ["CNYB.US"]
}

# -----------------------------------
# Step 1: Average z-scores within each bucket
# -----------------------------------
bucket_scores = pd.DataFrame(index=z_scores.index)

for bucket, tickers_in_bucket in bucket_map.items():
    valid = [t for t in tickers_in_bucket if t in z_scores.columns]
    bucket_scores[bucket] = z_scores[valid].mean(axis=1)

# -----------------------------------
# Step 2: Equal-weight across buckets
# -----------------------------------
z_scores["China_Growth_Score"] = bucket_scores.mean(axis=1)
z_scores["China_Growth_Score_Smoothed"] = z_scores["China_Growth_Score"].rolling(n_smooth).mean()


# -------------------------------
# 5. Plotting
# -------------------------------

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=z_scores.index,
    y=z_scores["China_Growth_Score"],
    mode="lines",
    name="China Growth Score",
    line=dict(width=1),
    opacity=0.5
))

fig.add_trace(go.Scatter(
    x=z_scores.index,
    y=z_scores["China_Growth_Score_Smoothed"],
    mode="lines",
    name=f"Smoothed ({n_smooth}d)",
    line=dict(width=2)
))

n_high = z_scores["China_Growth_Score"].quantile(.8)
n_low = z_scores["China_Growth_Score"].quantile(.2)

fig.add_hline(y=n_high, line_dash="dash", line_color="green", annotation_text="Growth-On", annotation_position="top right")
fig.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Neutral", annotation_position="top right")
fig.add_hline(y=n_low, line_dash="dash", line_color="red", annotation_text="Growth-Off", annotation_position="bottom right")

fig.update_layout(
    title=f"Composite China Growth Regime Indicator ({n_day}d Z-Score)",
    xaxis_title="Date",
    yaxis_title="Z-Score",
    height=600,
    width=1000,
    template="plotly_white"
)

fig.show()
