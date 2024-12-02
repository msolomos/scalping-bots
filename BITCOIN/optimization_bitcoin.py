import logging
import pandas as pd
import numpy as np
from itertools import product
import requests


# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

# Simulated trading function (replace with your actual trading logic)
def simulate_trading(scalp_target, stop_loss, short_ma, long_ma, rsi_threshold, data):
    logging.info(f"Testing with SCALP_TARGET={scalp_target}, STOP_LOSS={stop_loss}, "
                 f"Short MA={short_ma}, Long MA={long_ma}, RSI Threshold={rsi_threshold}")

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

    for index, row in data.iterrows():
        # Buy condition (MA crossover + MACD + RSI)
        if row['short_ma'] > row['long_ma'] and row['macd'] > row['signal'] and row['rsi'] < rsi_threshold and position is None:
            logging.debug(f"Buy condition met at {row['close']} (short MA: {row['short_ma']}, long MA: {row['long_ma']}, MACD: {row['macd']}, signal: {row['signal']}, RSI: {row['rsi']})")
            entry_price = row['close']
            position = "buy"
            logging.debug(f"Buying at {entry_price}")

        # Sell condition (Scalp target reached or stop-loss)
        elif position == "buy":
            logging.debug(f"Current price: {row['close']}, scalp target: {entry_price * scalp_target}, stop loss: {entry_price * stop_loss}")
            if row['close'] >= entry_price * scalp_target:
                profit += (row['close'] - entry_price)
                position = None
                logging.debug(f"Selling at {row['close']} for profit, total profit={profit}")
            elif row['close'] <= entry_price * stop_loss:
                profit -= (entry_price - row['close'])
                position = None
                logging.debug(f"Stop-loss triggered at {row['close']}, total profit={profit}")

    return profit

# Objective function to test each parameter combination
def objective(params, data):
    scalp_target, stop_loss, short_ma, long_ma, rsi_threshold = params
    profit = simulate_trading(scalp_target, stop_loss, short_ma, long_ma, rsi_threshold, data)
    return profit


############# RANDOM ΔΕΔΟΜΕΝΑ ####################################################
# # Historical data simulation (replace with real historical data)
# data = pd.DataFrame({
    # 'close': np.random.normal(2150, 50, 1000),  # Randomly generated data; replace with actual historical prices
# })



################################ ΔΟΚΙΜΗ ΜΕ ΠΡΑΓΜΑΤΙΚΑ ΙΣΤΟΡΙΚΑ ΔΕΔΟΜΕΝΑ#########################################
def fetch_historical_data(symbol='BTC-EUR', granularity=3600):  # Example for BTC-USD with hourly granularity
    url = f"https://api.exchange.coinbase.com/products/{symbol}/candles?granularity={granularity}"
    response = requests.get(url)
    candles = response.json()

    # Convert to pandas DataFrame
    df = pd.DataFrame(candles, columns=['time', 'low', 'high', 'open', 'close', 'volume'])
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

# Replace the random data with this function:
data = fetch_historical_data('BTC-USD')



# Parameter ranges for grid search
scalp_target_range = [1.01, 1.02, 1.03, 1.04, 1.05]  # Test different scalp targets - scalp_target_range: [1%, 2%, 3%, 4%, 5%]
stop_loss_range = [0.95, 0.96, 0.97, 0.98, 0.99]  # Test different stop-loss values - stop_loss_range: [-5%, -4%, -3%, -2%, -1%]
short_ma_range = [5, 10, 15]  # Short moving average
long_ma_range = [20, 30, 50]  # Long moving average
rsi_range = [30, 40, 50]  # RSI threshold

# Grid search over all parameter combinations
best_params = None
best_profit = float('-inf')
for params in product(scalp_target_range, stop_loss_range, short_ma_range, long_ma_range, rsi_range):
    profit = objective(params, data)
    if profit > best_profit:
        best_profit = profit
        best_params = params

print(f"Best parameters: {best_params}, Best Profit: {best_profit}")
