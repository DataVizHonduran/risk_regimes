# Risk Regime Dashboards

Interactive dashboards that track market risk regimes using multi-asset z-score analysis.

## Live Dashboards
- **US Risk Regime:** [https://datavizhonduran.github.io/risk_regimes/us_regime.html](https://datavizhonduran.github.io/risk_regimes/us_regime.html)
- **China Growth Regime:** [https://datavizhonduran.github.io/risk_regimes/china_growth.html](https://datavizhonduran.github.io/risk_regimes/china_growth.html)

## Features
- Real-time risk regime indicators (Risk-On/Risk-Off/Neutral for US, Growth-On/Growth-Off/Neutral for China)
- Multi-asset z-score analysis across different asset classes
- Daily automatic updates via GitHub Actions at 6 AM EST
- Interactive Plotly visualizations

## Data Sources
- **US Regime:** Uses ETF proxies for equities, bonds, commodities, and volatility
- **China Growth:** Uses China-focused ETFs, commodities, and Asia-Pacific regional indicators

## Technical Details
- Built with Python, Pandas, and Plotly
- Data sourced from Stooq via pandas-datareader
- Automated deployment using GitHub Actions
- Hosted on GitHub Pages

## Repository Structure
- `generate_us.py` - US risk regime analysis script
- `generate_china.py` - China growth regime analysis script
- `.github/workflows/update-dashboard.yml` - Automated update workflow
