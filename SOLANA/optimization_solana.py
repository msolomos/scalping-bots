import logging
import pandas as pd
import numpy as np
from itertools import product
import requests

# Crypto asset to scalping
CRYPTO_SYMBOL = 'SOL-EUR'
CRYPTO_NAME = 'SOL'
CRYPTO_FULLNAME = 'SOLANA'
GRANULARITY = 3600  # hourly granularity

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

# Simulated trading function (replace with your actual trading logic)
def simulate_trading(scalp_target, stop_loss, short_ma, long_ma, rsi_threshold, adx_threshold, stochastic_oversold_threshold, data):
    logging.info(f"Testing with SCALP_TARGET={scalp_target}, STOP_LOSS={stop_loss}, "
                 f"Short MA={short_ma}, Long MA={long_ma}, RSI Threshold={rsi_threshold}, "
                 f"ADX Threshold={adx_threshold}, Stochastic Oversold Threshold={stochastic_oversold_threshold}")

    # Moving Averages
    data['short_ma'] = data['close'].rolling(window=short_ma).mean()
    data['long_ma'] = data['close'].rolling(window=long_ma).mean()

    # MACD calculation
    data['macd'] = data['close'].ewm(span=12, adjust=False).mean() - data['close'].ewm(span=26, adjust=False).mean()
    data['signal'] = data['macd'].ewm(span=9, adjust=False).mean()

    # RSI calculation
    delta = data['close'].diff(1)
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    data['rsi'] = 100 - (100 / (1 + (gain.rolling(window=14).mean() / loss.rolling(window=14).mean())))

    # ADX calculation
    data['plus_dm'] = np.where(data['high'].diff() > data['low'].diff(), data['high'].diff(), 0)
    data['minus_dm'] = np.where(data['low'].diff() > data['high'].diff(), data['low'].diff(), 0)
    data['tr'] = data[['high', 'low', 'close']].max(axis=1) - data[['high', 'low', 'close']].min(axis=1)
    data['atr'] = data['tr'].rolling(window=14).mean()
    data['plus_di'] = 100 * (data['plus_dm'].rolling(window=14).sum() / data['atr'])
    data['minus_di'] = 100 * (data['minus_dm'].rolling(window=14).sum() / data['atr'])
    data['dx'] = (abs(data['plus_di'] - data['minus_di']) / (data['plus_di'] + data['minus_di'])) * 100
    data['adx'] = data['dx'].rolling(window=14).mean()

    # Stochastic Oscillator calculation
    data['low_14'] = data['low'].rolling(window=14).min()
    data['high_14'] = data['high'].rolling(window=14).max()
    data['stochastic'] = 100 * ((data['close'] - data['low_14']) / (data['high_14'] - data['low_14']))

    # Simulated trading logic
    profit = 0
    position = None
    entry_price = 0

    for index, row in data.iterrows():
        # Buy condition (MA crossover + MACD + RSI + ADX + Stochastic)
        if (row['short_ma'] > row['long_ma'] and row['macd'] > row['signal'] and 
            row['rsi'] < rsi_threshold and row['adx'] > adx_threshold and 
            row['stochastic'] < stochastic_oversold_threshold and position is None):
            entry_price = row['close']
            position = "buy"
            logging.debug(f"Buying at {entry_price}")

        # Sell condition (Scalp target reached or stop-loss)
        elif position == "buy":
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
    scalp_target, stop_loss, short_ma, long_ma, rsi_threshold, adx_threshold, stochastic_oversold_threshold = params
    profit = simulate_trading(scalp_target, stop_loss, short_ma, long_ma, rsi_threshold, adx_threshold, stochastic_oversold_threshold, data)
    return profit

# Fetch historical data
def fetch_historical_data():
    url = f"https://api.exchange.coinbase.com/products/{CRYPTO_SYMBOL}/candles?granularity={GRANULARITY}"
    response = requests.get(url)
    candles = response.json()
    df = pd.DataFrame(candles, columns=['time', 'low', 'high', 'open', 'close', 'volume'])
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

data = fetch_historical_data()

# Parameter ranges for grid search
scalp_target_range = [1.01, 1.02, 1.03, 1.04, 1.05]
stop_loss_range = [0.95, 0.96, 0.97, 0.98, 0.99]
short_ma_range = [5, 10, 15]
long_ma_range = [20, 30, 50]
rsi_range = [30, 40, 50]
adx_range = [20, 25, 30]  # ADX threshold
stochastic_range = [20, 30, 40]  # Stochastic oversold threshold

# Grid search over all parameter combinations
best_params = None
best_profit = float('-inf')
for params in product(scalp_target_range, stop_loss_range, short_ma_range, long_ma_range, rsi_range, adx_range, stochastic_range):
    profit = objective(params, data)
    if profit > best_profit:
        best_profit = profit
        best_params = params

print(f"Best parameters: {best_params}, Best Profit: {best_profit}")
