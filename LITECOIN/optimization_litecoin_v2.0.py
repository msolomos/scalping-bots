import logging
import pandas as pd
import numpy as np
from itertools import product
import requests


# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')


symbol = 'LTC-EUR'
granularity=300


# Default User-Agent
default_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0'
}


# Simulated trading function (replace with your actual trading logic)
def simulate_trading(scalp_target, stop_loss, short_ma, long_ma, rsi_threshold, trailing_profit, granularity, data):
    logging.info(f"Testing with SCALP_TARGET={scalp_target}, STOP_LOSS={stop_loss}, Short MA={short_ma}, "
                 f"Long MA={long_ma}, RSI Threshold={rsi_threshold}, Trailing Profit={trailing_profit}, Granularity={granularity}")

    # Moving Averages
    data['short_ma'] = data['close'].rolling(window=short_ma).mean()
    data['long_ma'] = data['close'].rolling(window=long_ma).mean()

    # MACD and RSI calculations (placeholder logic, replace with your actual methods)
    data['macd'] = data['close'].ewm(span=12, adjust=False).mean() - data['close'].ewm(span=26, adjust=False).mean()
    data['signal'] = data['macd'].ewm(span=9, adjust=False).mean()
    delta = data['close'].diff(1)
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    data['rsi'] = 100 - (100 / (1 + (gain.rolling(window=14).mean() / loss.rolling(window=14).mean())))

    # Simulated trading logic
    profit = 0
    position = None  # Track if we have a position
    entry_price = 0
    highest_price = 0

    for index, row in data.iterrows():
        # Buy condition (MA crossover + MACD + RSI)
        if row['short_ma'] > row['long_ma'] and row['macd'] > row['signal'] and row['rsi'] < rsi_threshold and position is None:
            entry_price = row['close']
            position = "buy"
            highest_price = entry_price
            logging.debug(f"Buying at {entry_price}")

        # Sell condition (Scalp target reached, stop-loss, or trailing profit)
        elif position == "buy":
            highest_price = max(highest_price, row['close'])

            if row['close'] >= entry_price * scalp_target:
                profit += (row['close'] - entry_price)
                position = None
                logging.debug(f"Selling at {row['close']} for profit, total profit={profit}")
            elif row['close'] <= entry_price * stop_loss:
                profit -= (entry_price - row['close'])
                position = None
                logging.debug(f"Stop-loss triggered at {row['close']}, total profit={profit}")
            elif row['close'] <= highest_price * (1 - trailing_profit):
                profit += (highest_price - row['close'])
                position = None
                logging.debug(f"Trailing profit activated at {row['close']}, total profit={profit}")

    return profit


# Objective function to test each parameter combination
def objective(params, data):
    scalp_target, stop_loss, short_ma, long_ma, rsi_threshold, trailing_profit, granularity = params
    profit = simulate_trading(scalp_target, stop_loss, short_ma, long_ma, rsi_threshold, trailing_profit, granularity, data)
    return profit


# Historical data fetching
def fetch_historical_data(granularity):
    url = f"https://api.exchange.coinbase.com/products/{symbol}/candles?granularity={granularity}"
    
    # Send request with default User-Agent
    response = requests.get(url, headers=default_headers)
    candles = response.json()

    # Convert to pandas DataFrame
    df = pd.DataFrame(candles, columns=['time', 'low', 'high', 'open', 'close', 'volume'])
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

# Replace the random data with this function:
data = fetch_historical_data(granularity)                                           


# Parameter ranges for grid search
scalp_target_range = [1.01, 1.02, 1.03, 1.04, 1.05]  # Test different scalp targets
stop_loss_range = [0.95, 0.96, 0.97, 0.98, 0.99]  # Test different stop-loss values
short_ma_range = [5, 10, 15]  # Short moving average
long_ma_range = [20, 30, 50]  # Long moving average
rsi_range = [30, 40, 50]  # RSI threshold
trailing_profit_range = [0.01, 0.02, 0.03, 0.04, 0.05]  # Trailing profit percentages
granularity_range = [60, 300, 900, 3600]  # Different granularities (e.g., 5min, 15min, 1hr)

# Grid search over all parameter combinations
best_params = None
best_profit = float('-inf')
for params in product(scalp_target_range, stop_loss_range, short_ma_range, long_ma_range, rsi_range, trailing_profit_range, granularity_range):
    profit = objective(params, data)
    if profit > best_profit:
        best_profit = profit
        best_params = params

# Print best results with names of each parameter
print(f"Best parameters: SCALP_TARGET={best_params[0]}, STOP_LOSS={best_params[1]}, Short MA={best_params[2]}, "
      f"Long MA={best_params[3]}, RSI Threshold={best_params[4]}, Trailing Profit={best_params[5]}, Granularity={best_params[6]}")
print(f"Best Profit: {best_profit}")
