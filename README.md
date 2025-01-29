# Scalping & DCA Trading Bot - README

## 📌 Overview
This bot is an advanced **scalping and Dollar Cost Averaging (DCA) trading system**, designed to execute trades based on technical indicators, volume confirmation, and fallback conditions. It operates on a **score-based system**, evaluating trade signals before executing buy/sell orders.

## 🚀 Features
- **Scalping & DCA Strategy**: Executes trades based on a calculated entry score.
- **Trailing Profit & Stop-Loss**: Supports dynamic trailing profit levels and stop-loss mechanisms.
- **Technical Indicators**: Uses MACD, RSI, Bollinger Bands, VWAP, ATR, and Stochastic indicators.
- **Volume Confirmation**: Ensures strong buy/sell signals.
- **Fallback Conditions**: Allows trades when volume confirmation is weak.
- **Failover Support**: Can pause trading based on external signals.
- **Portfolio Management**: Retrieves available balance before executing orders.
- **Logging & Alerts**: Detailed logs and push notifications for trade execution.

## 📦 Prerequisites
- **Python 3.x**
- Install required dependencies:
  ```bash
  pip install pandas numpy requests tabulate logging
  ```
See requirements.txt for all the required libraries.

- API access to **Coinbase or other exchanges**.
- JSON configuration file for trade parameters.

## 🔧 Configuration
The bot relies on **configuration parameters** stored in JSON files:

- **`trade_config.json`**: Defines trade parameters (BUY_THRESHOLD, SCALP_TARGET, etc.).
- **`score_weights.json`**: Weights assigned to different indicators.
- **`state.json`**: Stores the bot's state between runs.

### Example `trade_config.json`:
```json
{
  "BUY_THRESHOLD": 0.4,
  "SCALP_TARGET": 1.02,
  "STOP_LOSS": 0.98,
  "ENABLE_TRAILING_PROFIT": true,
  "ENABLE_DCA": true,
  "MAX_TRADES_PER_DAY": 5
}
```

## 🛠 Installation & Execution
1. Clone the repository:
   ```bash
   git clone https://github.com/msolomos/scalping-bots
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the bot:
   ```bash
   python trading_bot.py
   ```
4. To **reset the bot state**:
   ```bash
   python trading_bot.py --reset
   ```


## 📊 Technical Indicators Used
| Indicator       | Purpose |
|----------------|---------|
| **MACD**       | Measures trend momentum |
| **RSI**        | Detects overbought/oversold conditions |
| **VWAP**       | Price volume confirmation |
| **Bollinger Bands** | Identifies volatility levels |
| **ATR**        | Measures volatility for dynamic thresholds |
| **Stochastic** | Confirms momentum strength |


## 🏦 DCA Strategy
- If price **drops below a threshold**, it executes a **second buy order** to lower the average price.
- If the price continues to fall, a **third buy order** is placed.
- The **break-even price** is dynamically calculated.
- Sells all positions when the price reaches the desired **trailing profit** or scalp target.

## 📡 Logging & Alerts
- Logs all trade decisions and calculations.
- Sends **push notifications** for important trade events.
- Detailed logging of indicators, scores, and executed trades.

## 📌 Failover & Safety Mechanisms
- **Failover Mode**: If an external bot suggests a "Pause", this bot will **skip execution**.
- **Stop-Loss Protection**: Ensures losses are minimized.
- **Cooldown Management**: Implements a cooldown after each sale to prevent immediate rebuying.




# Trading Bot Execution Flow

## Overview
This document outlines the operational flow and logic of the trading bot from the moment it is executed until it completes its trading cycle.

## 1. **Initialization & Setup**
- The script starts by loading configuration settings, including trading parameters, API keys, and bot state.
- It checks if there is a cooldown period active (to avoid consecutive trades).
- The bot verifies whether it has received any **urgent sell/buy signals** from an external macro (Excel or another system).
- If the bot is set to **paused mode**, it exits early without executing trades.
- If **failover bot** integration is enabled, it checks whether the external decision allows trading.

## 2. **Fetching Market Data**
- The bot retrieves live candlestick data from multiple sources (Coinbase, Binance, etc.).
- It ensures that the data is structured correctly and converts timestamps into a `DatetimeIndex`.
- If there is insufficient data, it will attempt alternative data sources.

## 3. **Technical Indicator Calculation**
- The script computes various indicators, including:
  - Moving Averages (MA)
  - Moving Average Convergence Divergence (MACD)
  - Relative Strength Index (RSI)
  - Bollinger Bands
  - Volume Weighted Average Price (VWAP)
  - Average True Range (ATR)
  - Stochastic Oscillator & Stochastic RSI
  - Directional Movement Index (ADX)
- The bot applies resampling logic if necessary to ensure smooth indicator calculations.

## 4. **Scoring System & Buy Signal Evaluation**
- A weighted scoring system is applied to indicators, assigning a positive or negative score based on predefined thresholds.
- If the overall **score** exceeds the **BUY_THRESHOLD**, the bot checks for **volume confirmation**.
- If **volume confirmation fails**, the bot evaluates **fallback conditions** (ATR, Stochastic RSI).
- If **fallback conditions** are met, the bot proceeds with a buy order.

## 5. **Order Execution: Buying Process**
- Before placing an order, the bot:
  - Checks available portfolio balance.
  - Ensures that the required amount to buy is available.
  - Logs the trade reasoning (indicators & scores).
  - Sends an email notification via SendGrid.
- If the buy order is successful:
  - The trade amount and entry price are recorded.
  - The highest price reached post-entry is tracked for trailing sell logic.

## 6. **Trailing Profit & Stop-Loss Mechanism**
- The bot monitors price movement after entering a position.
- If price exceeds a predefined **scalp target**, the **trailing profit mechanism** is activated.
- If price falls below a dynamically calculated stop-loss, the bot **forces an exit**.
- For positions that include **DCA (Dollar Cost Averaging)**:
  - Second and third entries are triggered dynamically if the price drops beyond set thresholds.
  - A new break-even price is calculated.
  - If price reaches a trailing sell condition, all positions are exited.

## 7. **Profit Calculation & Exit Strategy**
- The bot dynamically adjusts trailing profit thresholds based on market volatility (ATR-based adjustment).
- When the trailing condition is met, a **sell order** is executed.
- Profit/Loss, including fees, is logged, and push notifications are sent.
- After exiting a trade, the bot **enters cooldown mode** to prevent immediate re-entry.

## 8. **Bot Iteration & Loop Termination**
- If the daily profit target or maximum trade count is reached, the bot stops executing further trades.
- The bot logs execution time and awaits the next scheduled run (via cronjob).

---

### Summary
The bot follows a structured and automated decision-making process that:
1. Analyzes the market through multiple technical indicators.
2. Uses a weighted score system for trade validation.
3. Implements DCA strategies for risk management.
4. Uses trailing profits and stop-loss mechanisms for optimized exits.
5. Ensures safe trading with volume confirmation and fallback logic.

The entire execution process is designed for **efficiency, risk mitigation, and dynamic market adaptation**.








## 📩 Contact & Support
For questions, issues, or contributions, reach out via **[GitHub Issues](https://github.com/msolomos/salping-bots/issues)**.

---
This bot is continuously evolving. 🚀 Stay tuned for updates!

