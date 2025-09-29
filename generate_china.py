import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.offline as pyo
from pandas_datareader import data as web
from datetime import datetime

# Define tickers for China Growth indicator
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

invert_list = ['CNYB.US']

# Download data via Stooq
start = "1995-01-01"
end = datetime.today().strftime("%Y-%m-%d")

df_all = pd.DataFrame()

for name, ticker in tickers.items():
    try:
        df = web.DataReader(ticker, "stooq", start=start, end=end)
        df = df[::-1]  # reverse Stooq data (comes in descending order)
        df_all[name] = df["Close"]
        print(f"Successfully loaded {name}")
    except Exception as e:
        print(f"Failed to load {name}: {e}")

df_all = df_all.dropna(axis=1, thresh=int(len(df_all) * 0.75))
print(f"Combined data shape: {df_all.shape}")

# Compute Z-Scores
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

# Define bucket mapping
bucket_map = {
    "China_Equities": ["FXI.US", "MCHI.US", "KWEB.US", "ASHR.US"],
    "Regional_Equities": ["AIA.US", "EEM.US", "VWO.US", "EWT.US", "KORU.US"],
    "Commodities": ["CPER.US", "BNO.US", "SLX.US", "WOOD.US", "XME.US", "DBC.US", "VAW.US"],
    "Industrials_Trade": ["XLI.US", "IYT.US", "SEA.US"],
    "Rates_Bonds": ["CNYB.US"]
}

# Step 1: Average z-scores within each bucket
bucket_scores = pd.DataFrame(index=z_scores.index)

for bucket, tickers_in_bucket in bucket_map.items():
    valid = [t for t in tickers_in_bucket if t in z_scores.columns]
    if valid:  # Only create bucket if we have valid tickers
        bucket_scores[bucket] = z_scores[valid].mean(axis=1)

# Step 2: Equal-weight across buckets
z_scores["China_Growth_Score"] = bucket_scores.mean(axis=1)
z_scores["China_Growth_Score_Smoothed"] = z_scores["China_Growth_Score"].rolling(n_smooth).mean()

# Get current regime and thresholds
current_score = z_scores["China_Growth_Score_Smoothed"].iloc[-1]
n_high = z_scores["China_Growth_Score"].quantile(.8)
n_low = z_scores["China_Growth_Score"].quantile(.2)

if current_score > n_high:
    current_regime = "GROWTH-ON"
elif current_score < n_low:
    current_regime = "GROWTH-OFF" 
else:
    current_regime = "NEUTRAL"

print(f"Current China Growth Regime: {current_regime} (Score: {current_score:.2f})")

# Create the figure
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=z_scores.index,
    y=z_scores["China_Growth_Score"],
    mode="lines",
    name="Raw Score",
    line=dict(width=1, color='lightcoral'),
    opacity=0.6
))

fig.add_trace(go.Scatter(
    x=z_scores.index,
    y=z_scores["China_Growth_Score_Smoothed"],
    mode="lines",
    name="Smoothed (30d)",
    line=dict(width=3, color='darkred')
))

fig.add_hline(y=n_high, line_dash="dash", line_color="green", 
              annotation_text="Growth-On", annotation_position="top right")
fig.add_hline(y=0, line_dash="dash", line_color="gray", 
              annotation_text="Neutral", annotation_position="top right")
fig.add_hline(y=n_low, line_dash="dash", line_color="red", 
              annotation_text="Growth-Off", annotation_position="bottom right")

# Get last updated timestamp
last_updated = datetime.now().strftime('%Y-%m-%d %H:%M UTC')

fig.update_layout(
    title={
        'text': "China Growth Regime Dashboard",
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 24}
    },
    xaxis_title="Date",
    yaxis_title="Z-Score",
    height=600,
    template="plotly_white",
    hovermode='x unified',
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

# Add "Last Updated" annotation
fig.add_annotation(
    text=f"Last Updated: {last_updated}",
    xref="paper", yref="paper",
    x=1, y=-0.1,
    xanchor='right', yanchor='top',
    showarrow=False,
    font=dict(size=12, color="gray")
)

# Create config to hide plotly toolbar
config = {
    'displayModeBar': False,
    'responsive': True
}

# Save as HTML file
output_filename = "china_growth.html"
pyo.plot(fig, filename=output_filename, auto_open=False, config=config)

print(f"Chart saved as '{output_filename}'")

# Create summary data
summary_data = {
    'current_regime': current_regime,
    'current_score': round(current_score, 3),
    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'thresholds': {
        'growth_on': round(n_high, 3),
        'growth_off': round(n_low, 3)
    }
}

import json
with open('china_growth_data.json', 'w') as f:
    json.dump(summary_data, f, indent=2)

print("China Growth data summary saved")
