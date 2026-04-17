import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.offline as pyo
import yfinance as yf
from datetime import datetime

# Keys are display names (kept with .US suffix so bucket_map is unchanged)
# Values are Yahoo Finance tickers (no .US suffix)
tickers = {
    "FXI.US": "FXI",
    "MCHI.US": "MCHI",
    "KWEB.US": "KWEB",
    "ASHR.US": "ASHR",
    "AIA.US": "AIA",
    "EEM.US": "EEM",
    "CPER.US": "CPER",
    "BNO.US": "BNO",
    "SLX.US": "SLX",
    "WOOD.US": "WOOD",
    "XME.US": "XME",
    "XLI.US": "XLI",
    "IYT.US": "IYT",
    "CNYB.US": "CNYB",
    "DBC.US": "DBC",
    "SEA.US": "SEA",
    "VAW.US": "VAW",
    "VWO.US": "VWO",
    "EWT.US": "EWT",
    "KORU.US": "KORU",
}

invert_list = ['CNYB.US']

start = "1995-01-01"
end = datetime.today().strftime("%Y-%m-%d")

# Download all at once via yfinance
yf_symbols = list(tickers.values())
raw = yf.download(yf_symbols, start=start, end=end, auto_adjust=True, progress=False)["Close"]

df_all = pd.DataFrame()
for col_name, yf_ticker in tickers.items():
    if yf_ticker in raw.columns and not raw[yf_ticker].dropna().empty:
        df_all[col_name] = raw[yf_ticker]
        print(f"Successfully loaded {col_name}")
    else:
        print(f"Failed to load {col_name}: no data")

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
