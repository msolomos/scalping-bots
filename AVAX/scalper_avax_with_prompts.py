from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from cryptography.hazmat.primitives import serialization
import http.client
import json
import time
import logging
import secrets
import pandas as pd
import numpy as np
import jwt
import requests
import random
import os
import sys
import re



################################################################################################################################

# Αρχικές μεταβλητές - πρέπει να οριστούν --setup

# Crypto asset to scalping
CRYPTO_SYMBOL = 'BTC-USD'
CRYPTO_NAME = 'BTC'
CRYPTO_FULLNAME = 'BITCOIN'

# Scalping variables
SCALP_TARGET = 1.03  # 5% κέρδος
TRADE_AMOUNT = 0.01  # Μονάδα κρυπτονομίσματος

# Technical indicators
short_ma_period = 5  # 5 περιόδων
long_ma_period = 20  # 20 περιόδων
RSI_THRESHOLD = 50  # Βελτιστοποιημένο RSI όριο
GRANULARITY = 300
GRANULARITY_TEXT = "FIVE_MINUTE"

# Ορισμός της μεταβλητής ENABLE_ADDITIONAL_CHECKS
ENABLE_ADDITIONAL_CHECKS = False

# Risk Management
STOP_LOSS = 0.98  # 3% κάτω από την τιμή αγοράς

TRAILING_PROFIT_THRESHOLD = 0.05  # Το αφήνουμε όπως είναι
DAILY_PROFIT_TARGET = 60.0  # Αφήνουμε το ημερήσιο στόχο
MAX_TRADES_PER_DAY = 100  # Μέγιστος αριθμός συναλλαγών ανά ημέρα
start_bot = True

# Tracking variables
daily_profit = 0
current_trades = 0
active_trade = None
highest_price = 0
trailing_profit_active = False


################################################################################################################################


# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(
            f"crypto_bot.log"
        ),  # Log to file
        logging.StreamHandler(),  # Log to console
    ],
)


# Path to the state file
state_file = f"bot_state.json"


# Your Coinbase API details (you need to define these)
key_name = "organizations/a935a9c0-1188-4df6-b289-3bc9c82328d8/apiKeys/cad2e31e-0159-4731-97d6-a43373845768"
key_secret = "-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIElQWMXqYUmD9J9ajFEUxYBqCxkDsLXfAgoKY87BynQaoAoGCCqGSM49\nAwEHoUQDQgAEe/nIxWZ27+bnVyIljVripEhfi5B59QgVcWNDqfiGn3PAvGGPqqK/\nGS95NnY0jDImKumL3AF4fcXOh+MaAebSaw==\n-----END EC PRIVATE KEY-----\n"




# Συνάρτηση για την αποστολή email
def sendgrid_email(quantity, transaction_type, price):
    SENDGRID_API_KEY = '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'
    
    # Μήνυμα για αγορά ή πώληση
    transaction = "Αγορά" if transaction_type == 'buy' else "Πώληση"
    
    # Τρέχουσα ημερομηνία και ώρα
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Δημιουργία του περιεχομένου του email
    message = Mail(
        from_email='info@f2d.gr',
        to_emails='info@f2d.gr',
        subject=f'Scalping bot - {transaction} {CRYPTO_SYMBOL}',
        html_content=f"""
        Πραγματοποιήθηκε <strong>{transaction} {CRYPTO_SYMBOL}</strong>.<br>
        Τεμάχια: {quantity}<br>
        Αξία: {price} €<br>
        Ημερομηνία: {current_time}<br>
        """
    )

    try:
        # Αποστολή του email μέσω SendGrid API
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        logging.info("Email sent successfully!")
    except Exception as e:
        # Χρήση logging για αποτυχία αποστολής
        logging.warning(f"Error sending email: {e}")



def update_python_script(variable_name, new_value, is_string=False):
    # Το path του αρχείου Python (το script που εκτελείται)
    script_path = '/opt/python/scalping-bot/AVAX/scalper_avax_with_prompts.py'
    
    # Διαβάζουμε το περιεχόμενο του script με UTF-8 κωδικοποίηση
    with open(script_path, 'r', encoding='utf-8') as file:
        script_content = file.read()

    # Δημιουργούμε regex για να βρούμε τη γραμμή της μεταβλητής
    if is_string:
        pattern = rf"{variable_name}\s*=\s*['\"].*['\"]"
        replacement = f"{variable_name} = '{new_value}'"
    else:
        if isinstance(new_value, bool):  # Έλεγχος αν είναι boolean
            new_value_str = 'True' if new_value else 'False'
            pattern = rf"{variable_name}\s*=\s*(True|False)"
            replacement = f"{variable_name} = {new_value_str}"
        else:
            pattern = rf"{variable_name}\s*=\s*\d*\.?\d+"
            replacement = f"{variable_name} = {new_value}"

    # Αντικατάσταση της τιμής της μεταβλητής στο περιεχόμενο
    updated_content = re.sub(pattern, replacement, script_content)

    # Γράφουμε το ενημερωμένο περιεχόμενο πίσω στο αρχείο με UTF-8 κωδικοποίηση
    with open(script_path, 'w', encoding='utf-8') as file:
        file.write(updated_content)
    
    print(f"Updated {variable_name} to {new_value} in the Python script.")




def get_float_input(prompt, variable_name, current_value):
    while True:
        user_input = input(f"{prompt} (Press ENTER to keep current value: {current_value}): ")
        if user_input == '':
            return current_value  # Επιστροφή της προηγούμενης τιμής αν ο χρήστης πατήσει ENTER
        try:
            value = float(user_input)
            update_python_script(variable_name, value)
            return value
        except ValueError:
            print("Invalid input. Please enter a valid number.")

def get_int_input(prompt, variable_name, current_value):
    while True:
        user_input = input(f"{prompt} (Press ENTER to keep current value: {current_value}): ")
        if user_input == '':
            return current_value  # Επιστροφή της προηγούμενης τιμής αν ο χρήστης πατήσει ENTER
        try:
            value = int(user_input)
            update_python_script(variable_name, value)
            return value
        except ValueError:
            print("Invalid input. Please enter a valid number.")

def get_yes_no_input(prompt, variable_name, current_value):
    while True:
        user_input = input(f"{prompt} (Current: {'yes' if current_value else 'no'}, press ENTER to keep current): ").strip().lower()
        if user_input == '':
            return current_value  # Επιστροφή της προηγούμενης τιμής αν ο χρήστης πατήσει ENTER
        if user_input in ['yes', 'no']:
            value = user_input == 'yes'
            update_python_script(variable_name, value)
            return value
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")


def setup_bot():
    global CRYPTO_SYMBOL, CRYPTO_NAME, CRYPTO_FULLNAME, SCALP_TARGET, TRADE_AMOUNT, STOP_LOSS, DAILY_PROFIT_TARGET
    global ENABLE_ADDITIONAL_CHECKS, short_ma_period, long_ma_period, RSI_THRESHOLD, GRANULARITY, GRANULARITY_TEXT
    global TRAILING_PROFIT_THRESHOLD, MAX_TRADES_PER_DAY

    # Εμφάνιση τίτλου κατά την εκκίνηση
    print("Scalping bot v1.0 - Gerasimos Solomos")
    print("=" * 40)

    # Prompt questions for variables in English
    CRYPTO_NAME = input(f"Which cryptocurrency do you want to scalp (Current: {CRYPTO_NAME}, e.g., AVAX): ").upper()
    if CRYPTO_NAME:
        update_python_script('CRYPTO_NAME', CRYPTO_NAME, is_string=True)

    CRYPTO_SYMBOL = input(f"Set the trading symbol for {CRYPTO_NAME} (Current: {CRYPTO_SYMBOL}, e.g., AVAX-EUR): ").upper()
    if CRYPTO_SYMBOL:
        update_python_script('CRYPTO_SYMBOL', CRYPTO_SYMBOL, is_string=True)

    CRYPTO_FULLNAME = input(f"Set the full name of {CRYPTO_NAME} (Current: {CRYPTO_FULLNAME}, e.g., AVALANCHE-2): ").upper()
    if CRYPTO_FULLNAME:
        update_python_script('CRYPTO_FULLNAME', CRYPTO_FULLNAME, is_string=True)

    # Αριθμητικά δεδομένα με έλεγχο εισαγωγής και δυνατότητα διατήρησης της τρέχουσας τιμής
    SCALP_TARGET = get_float_input("What is the scalping target (e.g., 1.05 for 5% profit)", 'SCALP_TARGET', SCALP_TARGET)
    TRADE_AMOUNT = get_float_input("How many units do you want to trade per transaction (e.g., 40)", 'TRADE_AMOUNT', TRADE_AMOUNT)
    STOP_LOSS = get_float_input("What is the stop-loss limit (e.g., 0.98 for 2% below)", 'STOP_LOSS', STOP_LOSS)
    DAILY_PROFIT_TARGET = get_float_input("What is your daily profit target (e.g., 60)", 'DAILY_PROFIT_TARGET', DAILY_PROFIT_TARGET)

    # Προσθήκη τίτλου για το setup των τεχνικών δεικτών
    print("\nTechnical Indicators Setup")
    print("=" * 40)

    # Ναι/Όχι εισαγωγή με έλεγχο και δυνατότητα διατήρησης της τρέχουσας τιμής
    ENABLE_ADDITIONAL_CHECKS = get_yes_no_input("Enable additional checks for technical indicators? (yes/no)", 'ENABLE_ADDITIONAL_CHECKS', ENABLE_ADDITIONAL_CHECKS)

    # Τεχνικοί δείκτες με έλεγχο αριθμητικής εισαγωγής και δυνατότητα διατήρησης της τρέχουσας τιμής
    short_ma_period = get_int_input("Enter the short moving average period (e.g., 5)", 'short_ma_period', short_ma_period)
    long_ma_period = get_int_input("Enter the long moving average period (e.g., 20)", 'long_ma_period', long_ma_period)
    RSI_THRESHOLD = get_int_input("Enter the RSI threshold (e.g., 50)", 'RSI_THRESHOLD', RSI_THRESHOLD)
    GRANULARITY = get_int_input("Enter the granularity in seconds (e.g., 300 for 5 minutes)", 'GRANULARITY', GRANULARITY)

    GRANULARITY_TEXT = input(f"Enter the granularity text (Current: {GRANULARITY_TEXT}, e.g., FIVE_MINUTE): ").upper()
    if GRANULARITY_TEXT:
        update_python_script('GRANULARITY_TEXT', GRANULARITY_TEXT, is_string=True)

    # Αριθμητικά δεδομένα με έλεγχο εισαγωγής
    TRAILING_PROFIT_THRESHOLD = get_float_input("Enter the trailing profit threshold (e.g., 0.05 for 5%)", 'TRAILING_PROFIT_THRESHOLD', TRAILING_PROFIT_THRESHOLD)
    MAX_TRADES_PER_DAY = get_int_input("What is the maximum number of trades per day (e.g., 100)", 'MAX_TRADES_PER_DAY', MAX_TRADES_PER_DAY)

    # Εμφάνιση των επιλογών στον χρήστη
    logging.info(f"""
    Your selected options:
    Cryptocurrency: {CRYPTO_NAME}
    Symbol: {CRYPTO_SYMBOL}
    Full Name: {CRYPTO_FULLNAME}
    Scalping Target: {SCALP_TARGET}
    Trade Amount Per Transaction: {TRADE_AMOUNT}
    Stop-Loss Limit: {STOP_LOSS}
    Daily Profit Target: {DAILY_PROFIT_TARGET}
    Enable Additional Checks: {ENABLE_ADDITIONAL_CHECKS}
    Short Moving Average Period: {short_ma_period}
    Long Moving Average Period: {long_ma_period}
    RSI Threshold: {RSI_THRESHOLD}
    Granularity: {GRANULARITY} seconds ({GRANULARITY_TEXT})
    Trailing Profit Threshold: {TRAILING_PROFIT_THRESHOLD}
    Max Trades Per Day: {MAX_TRADES_PER_DAY}
    """)






# Συνάρτηση για reset bot καθε μερα  --reset
def reset_bot_state():
    global daily_profit, current_trades, active_trade, TRADE_AMOUNT, highest_price, trailing_profit_active

    logging.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    logging.info("Resetting bot state...")

    # Αν υπάρχει ενεργή συναλλαγή, εκτελούμε πώληση
    if active_trade:
        logging.info(f"Selling active trade at {active_trade}")
        current_price = get_crypto_price()
        if current_price is None:
            logging.error("Failed to fetch current price. Skipping trade execution.")
            return

        place_order("sell", TRADE_AMOUNT, current_price)
        sendgrid_email(TRADE_AMOUNT, "sell", current_price)
        logging.info(f"Sold {TRADE_AMOUNT} of {CRYPTO_SYMBOL} at {current_price}")
        
    # Επαναφορά των τιμών στο state.json
    daily_profit = 0
    current_trades = 0
    active_trade = None
    TRADE_AMOUNT = 0.01
    highest_price = None
    trailing_profit_active = False

    # Αποθήκευση της νέας κατάστασης
    save_state()
    logging.info("Bot state reset completed.")





# Load the state from the file
def load_state():
    global daily_profit, current_trades, active_trade, TRADE_AMOUNT, highest_price, trailing_profit_active
    try:
        with open(state_file, "r") as f:
            state = json.load(f)
            daily_profit = state.get("daily_profit", 0)
            current_trades = state.get("current_trades", 0)
            active_trade = state.get("active_trade", None)
            TRADE_AMOUNT = state.get("TRADE_AMOUNT", 0)
            highest_price = state.get("highest_price", None)  # Φόρτωση του highest_price
            trailing_profit_active = state.get('trailing_profit_active', False)
            logging.info(
                f"Loaded state: daily_profit={round(daily_profit, 2)}, current_trades={current_trades}, active_trade={active_trade}, TRADE_AMOUNT={TRADE_AMOUNT}, highest_price={highest_price}"
            )
    except FileNotFoundError:
        daily_profit = 0
        current_trades = 0
        active_trade = None
        TRADE_AMOUNT = 0.01
        highest_price = None  # Αρχικοποίηση του highest_price αν δεν υπάρχει
        save_state()  # Αρχικοποίηση του αρχείου αν δεν υπάρχει
        logging.info(
            f"State file not found. Initialized new state: daily_profit={daily_profit}, current_trades={current_trades}, active_trade={active_trade}, TRADE_AMOUNT={TRADE_AMOUNT}, highest_price={highest_price}, trailing_profit_active={trailing_profit_active}"
        )



# Save the state to the file
def save_state():
    state = {
        "daily_profit": daily_profit,
        "current_trades": current_trades,
        "active_trade": active_trade,
        "TRADE_AMOUNT": TRADE_AMOUNT,
        "highest_price": highest_price,  # Αποθήκευση του highest_price
        "trailing_profit_active": trailing_profit_active
    }
    with open(state_file, "w") as f:
        json.dump(state, f)
    logging.info(
        f"Saved state: daily_profit={round(daily_profit, 2)}, current_trades={current_trades}, active_trade={active_trade}, TRADE_AMOUNT={TRADE_AMOUNT}, highest_price={highest_price}, trailing={trailing_profit_active}"
    )



# Συνάρτηση για τη δημιουργία JWT token
def build_jwt(uri):
    # logging.debug(f"Building JWT token for URI: {uri}")
    private_key_bytes = key_secret.encode("utf-8")
    private_key = serialization.load_pem_private_key(private_key_bytes, password=None)

    # JWT payload
    jwt_payload = {
        "sub": key_name,
        "iss": "cdp",
        "nbf": int(time.time()),
        "exp": int(time.time()) + 120,  # Expire in 120 seconds
        "uri": uri,
    }

    # Generate JWT token using ES256
    jwt_token = jwt.encode(
        jwt_payload,
        private_key,
        algorithm="ES256",
        headers={"kid": key_name, "nonce": secrets.token_hex()},
    )
    # logging.debug(f"JWT token generated successfully: {jwt_token}")
    return jwt_token


# Τοποθέτηση εντολών αγοράς/πώλησης με επιπλέον logging
def place_order(side, size, price):
    logging.debug(f"Placing {side.upper()} order for {size} at price {price}")
    request_host = "api.coinbase.com"
    place_order_path = "/api/v3/brokerage/orders"

    # Order data
    order_data = {
        "client_order_id": secrets.token_hex(10),
        "product_id": CRYPTO_SYMBOL,
        "side": "BUY" if side == "buy" else "SELL",
        "order_configuration": {
            "market_market_ioc": {
                "base_size": str(size),
            }
        },
    }

    body = json.dumps(order_data)
    logging.debug(f"Order data: {body}")

    uri = f"POST {request_host}{place_order_path}"
    jwt_token = build_jwt(uri)
    # logging.debug(f"Generated JWT Token: {jwt_token}")

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
    }

    conn = http.client.HTTPSConnection(request_host)
    try:
        conn.request("POST", place_order_path, body, headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")

        logging.debug(f"Response Status Code: {res.status}")
        logging.debug(f"Response Data: {data}")

        response_data = json.loads(data)
        if res.status == 200 and response_data.get("success", False):
            logging.info(f"Order placed successfully: {response_data}")
            return response_data
        else:
            error_message = response_data.get("error_response", "Unknown error")
            logging.error(
                f"Failed to place order. Status: {res.status}, Error: {error_message}"
            )
            return None
    except Exception as e:
        logging.error(f"Error making request: {e}")
        return None
    finally:
        conn.close()


# Technical indicators (MA, MACD, RSI)
def calculate_ma(df, period, timeframe=None):
    try:
        # ---------------------------------------
        # Έλεγχος αν το DataFrame έχει DatetimeIndex για να μπορεί να χρησιμοποιηθεί το resample
        if timeframe is not None:
            if not isinstance(
                df.index, (pd.DatetimeIndex, pd.TimedeltaIndex, pd.PeriodIndex)
            ):
                df = (
                    df.copy()
                )  # Δημιουργούμε αντίγραφο του DataFrame για να μην αλλάξουμε το πρωτότυπο
                df.index = pd.to_datetime(
                    df.index
                )  # Μετατροπή του index σε DatetimeIndex

            df = df.resample(
                timeframe
            ).last()  # Χρησιμοποιεί το τελευταίο διαθέσιμο κλείσιμο για το timeframe
        # ---------------------------------------

        ma = df["close"].rolling(window=period).mean()

        return ma
    except Exception as e:
        logging.error(f"Error calculating MA: {e}")
        return None


def calculate_macd(df, timeframe=None):
    try:
        # ---------------------------------------
        # Έλεγχος αν το DataFrame έχει DatetimeIndex για να μπορεί να χρησιμοποιηθεί το resample
        if timeframe is not None:
            if not isinstance(
                df.index, (pd.DatetimeIndex, pd.TimedeltaIndex, pd.PeriodIndex)
            ):
                logging.warning(f"Index type before conversion: {type(df.index)}")
                df = df.copy()
                df.index = pd.to_datetime(
                    df.index
                )  # Μετατροπή του index σε DatetimeIndex
                logging.info(f"Index type after conversion: {type(df.index)}")

            df = df.resample(
                timeframe
            ).last()  # Χρησιμοποιεί το τελευταίο διαθέσιμο κλείσιμο για το timeframe
            logging.info(
                f"Resampled data: {df.index.min()} to {df.index.max()}"
            )  # Έλεγχος resampling
        # ---------------------------------------

        short_ema = df["close"].ewm(span=12, adjust=False).mean()
        long_ema = df["close"].ewm(span=26, adjust=False).mean()
        macd = short_ema - long_ema
        signal = macd.ewm(span=9, adjust=False).mean()

        return macd, signal
    except Exception as e:
        logging.error(f"Error calculating MACD: {e}")
        return None, None


def calculate_rsi(df, period=14, timeframe=None):
    try:
        # ---------------------------------------
        # Έλεγχος αν το DataFrame έχει DatetimeIndex για να μπορεί να χρησιμοποιηθεί το resample
        if timeframe is not None:
            if not isinstance(
                df.index, (pd.DatetimeIndex, pd.TimedeltaIndex, pd.PeriodIndex)
            ):
                logging.warning(f"Index type before conversion: {type(df.index)}")
                df = df.copy()
                df.index = pd.to_datetime(
                    df.index
                )  # Μετατροπή του index σε DatetimeIndex
                logging.info(f"Index type after conversion: {type(df.index)}")

            df = df.resample(
                timeframe
            ).last()  # Χρησιμοποιεί το τελευταίο διαθέσιμο κλείσιμο για το timeframe
            logging.info(
                f"Resampled data: {df.index.min()} to {df.index.max()}"
            )  # Έλεγχος resampling
        # ---------------------------------------

        delta = df["close"].diff(1)
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi
    except Exception as e:
        logging.error(f"Error calculating RSI: {e}")
        return None



def calculate_indicators(df, source_url, short_ma_period, long_ma_period):
    # Έλεγχος αν υπάρχουν αρκετά δεδομένα για τον υπολογισμό των δεικτών
    if len(df) < max(short_ma_period, long_ma_period, 26):  # Μακρύτερη περίοδος για MACD είναι 26
        #logging.warning(f"Not enough data to calculate indicators from {source_url}. Data length: {len(df)}")
        return False  # Επιστρέφει False για να δηλώσει ότι δεν υπάρχουν αρκετά δεδομένα
    return True  # Επιστρέφει True αν υπάρχουν αρκετά δεδομένα





def fetch_data():
    logging.debug(f"Fetching data for {CRYPTO_SYMBOL} with granularity: {GRANULARITY}")

                                                                                               
    urls = [
        f"https://api.coinbase.com/api/v3/brokerage/market/products/{CRYPTO_SYMBOL}/candles?granularity={GRANULARITY_TEXT}",
        f"https://api.exchange.coinbase.com/products/{CRYPTO_SYMBOL}/candles?granularity={GRANULARITY}",
        f"https://api.coingecko.com/api/v3/coins/{CRYPTO_FULLNAME.lower()}/ohlc?days=1&vs_currency=eur",
    ]

     # Ανακάτεμα των URLs τυχαία                                             
    random.shuffle(urls)

    max_retries = 2
    delay_between_retries = 10
    
    # Standard Mozilla User-Agent string
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0"

    for url in urls:  # Δοκιμάζουμε διαφορετικά URLs
        attempts = 0
        conn = None

        while attempts < max_retries:
            try:
                logging.debug(f"Attempt {attempts + 1} to fetch data from {url}")
                conn = http.client.HTTPSConnection(url.split("/")[2])
                path = "/" + "/".join(url.split("/")[3:])

                headers = {
                    "User-Agent": user_agent
                }

                conn.request("GET", path, headers=headers)
                res = conn.getresponse()

                if res.status != 200:
                    # Καταγράφουμε το status, headers, και το response body για debugging
                    logging.error(f"Failed to fetch data from {url}: HTTP {res.status}")
                    logging.debug(f"Response headers: {res.getheaders()}")
                    response_body = res.read().decode("utf-8")
                    logging.debug(f"Response body: {response_body}")
                    
                    attempts += 1
                    time.sleep(delay_between_retries)
                    continue

                data = res.read().decode("utf-8")
                logging.debug(f"Raw response from {url}: {data}")

                try:
                    candles = json.loads(data)
                except json.JSONDecodeError:
                    logging.error(f"Failed to parse JSON from {url}. Response body: {data}")
                    break

                if not candles or len(candles) == 0:
                    logging.warning(f"No valid data fetched from {url}. Trying next URL.")
                    break  # Προχωράμε στο επόμενο URL

                if "coingecko" in url:
                    df = pd.DataFrame(candles, columns=["time", "open", "high", "low", "close"])
                    df["time"] = pd.to_datetime(df["time"], unit="ms")
                else:
                    df = pd.DataFrame(candles, columns=["time", "low", "high", "open", "close", "volume"])
                    df["time"] = pd.to_datetime(df["time"], unit="s")

                                                                                    
                if calculate_indicators(df, url, short_ma_period, long_ma_period):
                    return df, url

                                                                                                            
                logging.warning(f"Not enough data from {url}. Data length: {len(df)}. Trying next URL...")
                break

            except Exception as e:
                logging.error(f"Error fetching data from {url} (Attempt {attempts + 1}): {e}")
                attempts += 1
                time.sleep(delay_between_retries)

            finally:
                if conn:
                    conn.close()

    logging.error("Failed to fetch sufficient data from all sources")
    return None, None






# # MOCK UP API - ΓΙΑ ΔΟΚΙΜΕΣ - Απλή έκδοση χωρίς ελέγχους ή retries
# def get_crypto_price():
    # public_base_url = "http://localhost:5015"  # Δικό σου API URL
    # response = requests.get(f"{public_base_url}/price")
    # return float(response.json().get('price'))  # Επιστροφή της τιμής ως float










# Νέα έκδοση της συνάρτησης get_crypto_price για χρήση με public endpoint (χωρίς authentication)
def get_crypto_price(retries=3, delay=5):
    method = "GET"
    # Δημόσιο endpoint για crypto
    request_path = f"/products/{CRYPTO_SYMBOL}/ticker"
    public_base_url = "https://api.exchange.coinbase.com"

    for attempt in range(retries):
        try:
            # Δημιουργία του πλήρους URL (χωρίς authentication)
            # logging.debug(f"Making request to {public_base_url}{request_path}")
            response = requests.get(f"{public_base_url}{request_path}")
            # logging.debug(f"Response Status Code: {response.status_code}")
            # logging.debug(f"Response Headers: {response.headers}")
            # logging.debug(f"Response Text: {response.text}")

            # Έλεγχος status code
            if response.status_code != 200:
                logging.error(
                    f"Failed to fetch {CRYPTO_NAME} price. Status code: {response.status_code}. Attempt {attempt + 1} of {retries}"
                )
                time.sleep(delay)  # Καθυστέρηση πριν την επόμενη προσπάθεια
                continue

            # Ανάλυση του JSON
            data = response.json()
            if "price" not in data:
                logging.error(
                    f"'price' key missing in API response: {data}. Attempt {attempt + 1} of {retries}"
                )
                time.sleep(delay)  # Καθυστέρηση πριν την επόμενη προσπάθεια
                continue

            # Απόκτηση της τιμής
            price = float(data["price"])
            logging.info(f"Fetched {CRYPTO_NAME} price: {price}")
            return price

        except requests.exceptions.RequestException as e:
            logging.error(
                f"Error fetching {CRYPTO_NAME} price: {e}. Attempt {attempt + 1} of {retries}"
            )
            time.sleep(delay)  # Καθυστέρηση πριν την επόμενη προσπάθεια

    # Αν αποτύχουν όλες οι προσπάθειες
    logging.error(f"Failed to fetch {CRYPTO_NAME} price after {retries} attempts.")
    return None


# Main trading logic (updated)
def execute_scalping_trade(CRYPTO_SYMBOL):
    global daily_profit, current_trades, highest_price, active_trade, TRADE_AMOUNT, start_bot, trailing_profit_active

    logging.info(f"Executing trade logic for {CRYPTO_SYMBOL}")

    if not start_bot:
        logging.info("Bot is stopped.")
        return

    try:
        # Λήψη της τρέχουσας τιμής του κρυπτονομίσματος
        current_price = get_crypto_price()

        if current_price is None:
            logging.error("Failed to fetch current price. Skipping trade execution.")
            return

        logging.debug(f"Current price for {CRYPTO_SYMBOL}: {current_price}")
        logging.debug(f"Current Price: {current_price}, Highest Price: {highest_price}")

        # Αν υπάρχει ανοιχτή θέση, έλεγχος για πώληση
        if active_trade:
            logging.info(f"Active trade exists at {active_trade}. Checking for sell opportunity.")

            # Αρχικοποίηση του highest_price αν είναι None
            if highest_price is None:
                highest_price = active_trade
                logging.info(f"Initialized highest_price to {highest_price}")

            # Ενημέρωση του highest_price μόνο αν η τρέχουσα τιμή είναι μεγαλύτερη
            if current_price > highest_price:
                highest_price = current_price
                logging.info(f"Updated highest_price to {highest_price}")
                save_state()  # Αποθήκευση του ενημερωμένου highest_price

            logging.info(f"Current Price: {current_price}, Highest Price: {highest_price}")

            # Έλεγχος stop-loss πρώτα
            stop_loss_price = active_trade * STOP_LOSS
            if current_price <= stop_loss_price:
                logging.info(f"Stop-loss triggered. Selling at {current_price}")
                place_order("sell", TRADE_AMOUNT, current_price)
                sendgrid_email(TRADE_AMOUNT, "sell", current_price)
                daily_profit -= (active_trade - current_price) * TRADE_AMOUNT
                active_trade = None
                TRADE_AMOUNT = 0.01
                highest_price = None
                current_trades += 1
                save_state()
                return  # Σταματάει η εκτέλεση εδώ αν γίνει πώληση λόγω stop-loss

            # Υπολογισμός του scalp target price
            scalp_target_price = active_trade * SCALP_TARGET

            if ENABLE_TRAILING_PROFIT:
                # Έλεγχος αν το trailing profit είναι ενεργό ή αν πρέπει να ενεργοποιηθεί
                if not trailing_profit_active and current_price >= scalp_target_price:
                    logging.info(f"Scalp target reached. Trailing profit activated.")
                    trailing_profit_active = True
                    save_state()
                                                                                                                    
                if trailing_profit_active:
                    # Ενημέρωση του trailing sell price
                    trailing_sell_price = highest_price * (1 - TRAILING_PROFIT_THRESHOLD)
                    logging.info(f"Trailing sell price is {trailing_sell_price}")

                    # Έλεγχος αν πρέπει να πουλήσουμε λόγω trailing profit
                    if current_price <= trailing_sell_price:
                        logging.info(f"Trailing profit triggered. Selling at {current_price}")
                        place_order("sell", TRADE_AMOUNT, current_price)
                        sendgrid_email(TRADE_AMOUNT, "sell", current_price)
                        daily_profit += (current_price - active_trade) * TRADE_AMOUNT
                        active_trade = None
                        TRADE_AMOUNT = 0.01
                        highest_price = None
                        trailing_profit_active = False
                        current_trades += 1
                        save_state()
                        return  # Σταματάμε εδώ αν έγινε πώληση λόγω trailing profit
                    else:
                        logging.info(f"Trailing profit active. Current price {current_price} has not dropped below trailing sell price {trailing_sell_price}.")

                else:
                    # Αν το trailing profit δεν είναι ενεργό και η τιμή δεν έχει φτάσει το scalp target
                    logging.info(f"Waiting for price to reach scalp target at {scalp_target_price}")


            else:
                # Αν το trailing profit δεν είναι ενεργοποιημένο, πουλάμε στο scalp target
                if current_price >= scalp_target_price:
                    logging.info(f"Selling at {current_price} for profit (scalp target)")
                    place_order("sell", TRADE_AMOUNT, current_price)
                    sendgrid_email(TRADE_AMOUNT, "sell", current_price)
                    daily_profit += (current_price - active_trade) * TRADE_AMOUNT
                    active_trade = None
                    TRADE_AMOUNT = 0.01
                    highest_price = None
                    current_trades += 1
                    save_state()
                    return  # Σταματάει η εκτέλεση εδώ αν γίνει πώληση λόγω scalp target

                # Δεν πουλάμε ακόμη, συνεχίζουμε να παρακολουθούμε
                logging.info(f"Current price {current_price} has not reached scalp target price {scalp_target_price}.")

            # Καμία πώληση δεν έγινε
            logging.info(f"No sell action taken. Current price {current_price} did not meet any sell criteria.")

            return  # Δεν κάνουμε νέα αγορά αν υπάρχει ανοιχτή θέση





        
        
        
        
        ##########################################################################################################################################
        ################### ΓΙΑ ΑΓΟΡΑ####################################################

        # Μεταφέραμε την κλήση fetch_data() εδώ, πριν τον έλεγχο για την αγορά  (ήταν στην αρχή της συνάρτησης αμέσως μετα το try)
        df, source_url = fetch_data()
        if df is None:
            logging.error(f"Failed to fetch data from {source_url}")
            return


        # # Έλεγχος αν υπάρχουν αρκετά δεδομένα για τον υπολογισμό των δεικτών
        # if len(df) < max(short_ma_period, long_ma_period, 26):  # Μακρύτερη περίοδος για MACD είναι 26
            # logging.warning(f"Not enough data to calculate indicators. Data length: {len(df)}")
            # return

        # Calculate indicators (για αγορά)
        ma_short = calculate_ma(df, short_ma_period).iloc[-1]
        ma_long = calculate_ma(df, long_ma_period).iloc[-1]
        macd, signal = calculate_macd(df)
        rsi = calculate_rsi(df).iloc[-1]

        logging.info(
            f"Indicators: MA_Short={round(ma_short,3)}, MA_Long={round(ma_long,3)}, MACD={round(macd.iloc[-1],3)}, Signal={round(signal.iloc[-1],3)}, RSI={round(rsi,3)}, Current Price={current_price}"
        )
        # Εμφάνιση του εύρους δεδομένων πριν το resample
        # logging.info(f"Data available for SOL-EUR: {df.index.min()} to {df.index.max()}")

        # ---------------------------------------
        # Μετατροπή της στήλης 'time' σε DatetimeIndex, αν υπάρχει
        if "time" in df.columns:
            df["time"] = pd.to_datetime(
                df["time"]
            )  # Μετατροπή της στήλης 'time' σε datetime format
            df.set_index(
                "time", inplace=True
            )  # Ορισμός της στήλης 'time' ως DatetimeIndex
            # logging.info(f"Index converted to DatetimeIndex: {df.index}")
        else:
            # Αν δεν υπάρχει στήλη 'time', δημιουργούμε DatetimeIndex από RangeIndex
            if isinstance(df.index, pd.RangeIndex):
                logging.warning("No valid datetime index. Creating a DatetimeIndex.")
                df.index = pd.date_range(
                    start="2024-10-01", periods=len(df), freq="T"
                )  # Προσαρμόστε το freq ανάλογα
                logging.info(f"New index created: {df.index}")
            else:
                logging.error("No 'time' column or valid index for resampling.")
                return  # Σταματάμε την εκτέλεση, αν δεν υπάρχουν χρονικές πληροφορίες
        # ---------------------------------------

        # ---------------------------------------
        # Συμπληρωματικός Έλεγχος για επιβεβαίωση δεικτών (προαιρετικός)
        if ENABLE_ADDITIONAL_CHECKS:
            # Resampling data σε ωριαίο χρονικό διάστημα
            df_resampled = df.resample(
                "1H"
            ).last()  # Χρησιμοποιεί το τελευταίο διαθέσιμο κλείσιμο κάθε ώρας
            # logging.info(f"Resampled data: {df_resampled.index.min()} to {df_resampled.index.max()}, length: {len(df_resampled)}")

            # Ελέγχουμε αν υπάρχουν αρκετά δεδομένα για υπολογισμό των δεικτών
            if len(df_resampled) < max(
                short_ma_period, long_ma_period, 14
            ):  # Ανάλογα με τις περιόδους που χρησιμοποιείς
                logging.warning(
                    f"Not enough resampled data for calculating indicators. Data length: {len(df_resampled)}"
                )
                return

            # Υπολογισμός τεχνικών δεικτών
            ma_short_long_period = calculate_ma(df_resampled, short_ma_period).iloc[-1]
            ma_long_long_period = calculate_ma(df_resampled, long_ma_period).iloc[-1]
            macd_long, signal_long = calculate_macd(df_resampled)
            rsi_long = calculate_rsi(df_resampled).iloc[-1]

            # Επιβεβαίωση ότι οι δείκτες συμφωνούν και σε ωριαία χρονικά διαστήματα
            if (
                pd.isna(ma_short_long_period)
                or pd.isna(ma_long_long_period)
                or pd.isna(rsi_long)
            ):
                logging.warning(
                    f"Additional check failed: MA_Short_Long={ma_short_long_period}, MA_Long_Long={ma_long_long_period}, MACD_Long={macd_long.iloc[-1]}, Signal_Long={signal_long.iloc[-1]}, RSI_Long={rsi_long}"
                )
                logging.info(
                    f"Indicators are not consistent across multiple timeframes. No buy action will be taken."
                )
                return
            else:
                logging.info(
                    f"Additional check passed: MA_Short_Long={round(ma_short_long_period, 3)}, MA_Long_Long={round(ma_long_long_period, 3)}, MACD_Long={round(macd_long.iloc[-1], 3)}, Signal_Long={round(signal_long.iloc[-1], 3)}, RSI_Long={round(rsi_long, 3)}"
                )
        # ---------------------------------------

        # Αγοραστικό σήμα
        if (ma_short > ma_long and macd.iloc[-1] > signal.iloc[-1] and rsi < RSI_THRESHOLD):
        #if (ma_short > ma_long or rsi < RSI_THRESHOLD):
            logging.info(f"All technical indicators are positive. Initiating a buy at {current_price}.")
            place_order("buy", TRADE_AMOUNT, current_price)      
            active_trade = current_price  # Ενημέρωση της ανοιχτής θέσης
            #TRADE_AMOUNT = TRADE_AMOUNT  # Καταχώρηση του ποσού συναλλαγής
            
            # Κλήση της sendgrid_email πριν μηδενιστούν οι τιμές
            sendgrid_email(TRADE_AMOUNT, "buy", current_price) 
            
            highest_price = current_price
            current_trades += 1
            save_state()  # Αποθήκευση της κατάστασης μετά την αγορά
        else:
            # logging.info(f"Indicators: MA_Short={round(ma_short,3)}, MA_Long={round(ma_long,3)}, MACD={round(macd.iloc[-1],3)}, Signal={round(signal.iloc[-1],3)}, RSI={round(rsi,3)}, Current Price={current_price}")
            logging.info(
                f"Not all technical indicators are favorable. No buy action will be taken at this time."
            )

        # Έλεγχος αν επιτεύχθηκε το καθημερινό κέρδος ή το όριο συναλλαγών
        if daily_profit >= DAILY_PROFIT_TARGET or current_trades >= MAX_TRADES_PER_DAY:
            logging.info(
                f"Daily profit target reached: {daily_profit}$ or maximum trades executed"
            )
            start_bot = False
            #save_state()  # Αποθήκευση κατάστασης όταν σταματάει το bot

    except Exception as e:
        logging.error(f"Exception occurred in execute_scalping_trade: {e}")
        return


# Main loop (updated to load state)
def run_bot():
    logging.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    logging.info("Starting bot...")
    load_state()  # Load the previous state
    execute_scalping_trade(CRYPTO_SYMBOL)
    # save_state()  # Save the state after each execution
    logging.info("Bot execution completed.")



if __name__ == "__main__":
    if "--setup" in sys.argv:
        setup_bot()  # Κλήση της συνάρτησης setup για την εισαγωγή μεταβλητών
    elif "--reset" in sys.argv:
        reset_bot_state()  # Κλήση της συνάρτησης reset
    else:
        run_bot()  # Εκτέλεση του bot κανονικά
