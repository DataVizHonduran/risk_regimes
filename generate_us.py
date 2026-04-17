import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objects as go
import plotly.offline as pyo

tickers = {
    "SPX": "SPY",
    "DAX": "EWG",
    "NIKKEI": "EWJ",
    "EMEQ": "EEM",
    "HYG": "HYG",
    "LQD": "LQD",
    "TLT": "TLT",
    "VIX": "VIXY",
    "DBC": "DBC",
    "GLD": "GLD",
    "USO": "USO",
    "CPER": "CPER",
    "VNQ": "VNQ",
    "UUP": "UUP"
}

invert_list = ["VIX", "TLT", "GLD", "UUP"]
start = datetime.datetime(2002, 1, 1)
end = datetime.datetime.today()

# Download all tickers at once
yf_tickers = list(tickers.values())
raw = yf.download(yf_tickers, start=start, end=end, auto_adjust=True, progress=False)["Close"]

# Build per-name series
data = {}
name_to_yf = {name: ticker for name, ticker in tickers.items()}
for name, ticker in name_to_yf.items():
    if ticker in raw.columns and not raw[ticker].dropna().empty:
        data[name] = raw[ticker].dropna()
        print(f"Successfully loaded {name} ({ticker})")
    else:
        print(f"Failed to load {name} ({ticker}): no data")

# Combine and drop missing
df_all = pd.concat(data.values(), axis=1)
df_all.columns = data.keys()
df_all.dropna(inplace=True)
print(f"Combined data shape: {df_all.shape}")

# Calculate z-scores of distance from moving average
z_scores = pd.DataFrame(index=df_all.index)
n_day = 100
n_smooth = 20

for col in df_all.columns:
    price = df_all[col]
    ma_period = price.rolling(n_day).mean()
    std = price.rolling(90).std()
    
    z = (price - ma_period) / std
    
    # Invert for assets where lower value = more risk-on
    if col in invert_list:
        z = -z
    
    z_scores[col] = z

# Composite Risk Regime Score
z_scores["Risk_Regime_Score"] = z_scores.median(axis=1)
z_scores["Risk_Regime_Score_Smoothed"] = z_scores["Risk_Regime_Score"].rolling(n_smooth).mean()

# Get current regime
current_score = z_scores["Risk_Regime_Score_Smoothed"].iloc[-1]
if current_score > 1:
    current_regime = "RISK-ON"
elif current_score < -1:
    current_regime = "RISK-OFF" 
else:
    current_regime = "NEUTRAL"

print(f"Current Risk Regime: {current_regime} (Score: {current_score:.2f})")

# Create single figure (no subplots)
fig = go.Figure()

# Main risk regime chart
fig.add_trace(go.Scatter(
    x=z_scores.index,
    y=z_scores["Risk_Regime_Score"],
    mode="lines",
    name="Raw Score",
    line=dict(width=1, color='lightblue'),
    opacity=0.6
))

# Smoothed regime score
fig.add_trace(go.Scatter(
    x=z_scores.index,
    y=z_scores["Risk_Regime_Score_Smoothed"],
    mode="lines",
    name="Smoothed (20d)",
    line=dict(width=3, color='darkblue')
))

# Add threshold lines
fig.add_hline(y=1, line_dash="dash", line_color="green", 
              annotation_text="Risk-On", annotation_position="top right")
fig.add_hline(y=0, line_dash="dash", line_color="gray", 
              annotation_text="Neutral", annotation_position="top right")
fig.add_hline(y=-1, line_dash="dash", line_color="red", 
              annotation_text="Risk-Off", annotation_position="bottom right")

# Get last updated timestamp
last_updated = datetime.datetime.now().strftime('%Y-%m-%d %H:%M UTC')

# Update layout
fig.update_layout(
    title={
        'text': "Risk Regime Dashboard",
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

# Save as standalone HTML file for GitHub Pages
output_filename = "us_regime.html"
pyo.plot(fig, filename=output_filename, auto_open=False, config=config)

print(f"Chart saved as '{output_filename}'")
print("US Risk Regime dashboard will be available on GitHub Pages!")

# Also create summary data
summary_data = {
    'current_regime': current_regime,
    'current_score': round(current_score, 3),
    'last_updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'recent_scores': z_scores["Risk_Regime_Score_Smoothed"].iloc[-30:].round(3).tolist()
}

import json
with open('us_regime_data.json', 'w') as f:
    json.dump(summary_data, f, indent=2)

print("US regime data summary saved as 'us_regime_data.json'")
