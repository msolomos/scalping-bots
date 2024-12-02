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

###################################################################################################################################################################################################################################
# Αρχικές μεταβλητές - πρέπει να οριστούν

# 1. Crypto asset to scalping - coinbase
CRYPTO_SYMBOL = "SOL-EUR"
CRYPTO_NAME = "SOL"
CRYPTO_FULLNAME = "SOLANA"

# 2. Ειδική περίπτωση URL απο Binance
BINANCE_PAIR = "SOLEUR"
BINANCE_INTERVAL = "5m"


# 3. Scalping variables
SCALP_TARGET = 1.01  # 5% κέρδος
TRADE_AMOUNT = 12  # Μονάδα κρυπτονομίσματος

# 4. Τεχνικοί Δείκτες
short_ma_period = 5  # 5 περιόδων
long_ma_period = 20  # 20 περιόδων
RSI_THRESHOLD = 50

ADX_THRESHOLD = 25
STOCHASTIC_OVERSOLD_THRESHOLD = 40

GRANULARITY = 300
GRANULARITY_TEXT = "FIVE_MINUTE"


# 5. Risk Management
STOP_LOSS = 0.95  # 5% κάτω από την τιμή αγοράς
ATR_MULTIPLIER = 1.5

# Συντηρητικοί traders τείνουν να επιλέγουν έναν χαμηλότερο συντελεστή, γύρω στο 1.5 έως 2, ώστε να κλείνουν τις θέσεις τους πιο κοντά στην τρέχουσα τιμή για να μειώνουν τις απώλειες.
# Πιο επιθετικοί traders προτιμούν υψηλότερο atr_multiplier, όπως 2.5 ή 3, δίνοντας μεγαλύτερο χώρο στο περιθώριο τιμών και στο bot να αποφεύγει την απότομη πώληση σε βραχυπρόθεσμες διακυμάνσεις.

ENABLE_TRAILING_PROFIT = True
TRAILING_PROFIT_THRESHOLD = 0.01
ENABLE_ADDITIONAL_CHECKS = True  # Αλλαγή σε False αν θέλεις να απενεργοποιήσεις τους πρόσθετους ελέγχους

DAILY_PROFIT_TARGET = 40  # Μεγιστος ημερήσιος στοχος
MAX_TRADES_PER_DAY = 50  # Μέγιστος αριθμός συναλλαγών ανά ημέρα


# 6. Μεταβλητές βραδυνού reset
MINIMUM_PROFIT_THRESHOLD = 5  # Ελάχιστο επιθυμητό κέρδος σε ευρώ για βραδυνό reset
FEES_PERCENTAGE = 0.0025  # Εκτιμώμενο ποσοστό fees (0.25%)
COOLDOWN_DURATION = 3600  # Χρόνος σε δευτερόλεπτα πριν το re-buy


###################################################################################################################################################################################################################################

# Αρχικοποίηση μεταβλητών
start_bot = True

daily_profit = 0
current_trades = 0
active_trade = None
highest_price = 0
trailing_profit_active = False


# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(
            f"/opt/python/scalping-bot/{CRYPTO_FULLNAME}/{CRYPTO_NAME}_bot.log"
        ),  # Log to file
        logging.StreamHandler(),  # Log to console
    ],
)



# Συνάρτηση για να φορτώσει τα κλειδιά από το αρχείο JSON
def load_keys(json_path="/opt/python/scalping-bot/api_keys.json"):
    try:
        with open(json_path, "r") as file:
            keys = json.load(file)
            key_name = keys.get("key_name")
            key_secret = keys.get("key_secret")
            SENDGRID_API_KEY = keys.get("SENDGRID_API_KEY")

            if not key_name or not key_secret or not SENDGRID_API_KEY:
                raise ValueError("Key name / secret or sendgrid key is missing in the JSON file.")

            return key_name, key_secret, SENDGRID_API_KEY
    except FileNotFoundError:
        raise FileNotFoundError(f"The specified JSON file '{json_path}' was not found.")
    except json.JSONDecodeError:
        raise ValueError(f"The JSON file '{json_path}' is not properly formatted.")



# Φόρτωση των κλειδιών
key_name, key_secret, SENDGRID_API_KEY = load_keys()



# Διαδρομή για το cooldownfile
cooldown_file = f"/opt/python/scalping-bot/{CRYPTO_FULLNAME}/cooldown_state.json"


# Διαδρομή για το state file
state_file = f"/opt/python/scalping-bot/{CRYPTO_FULLNAME}/state.json"


# Διαδρομή για το pause flag
pause_file = f"/opt/python/scalping-bot/{CRYPTO_FULLNAME}/pause.flag"


# Έλεγχος για την ύπαρξη του flag
if os.path.exists(pause_file):
    print("Script paused due to reset process.")
    sys.exit()




# Συνάρτηση για την αποστολή email
def sendgrid_email(quantity, transaction_type, price, daily_profit):   
    
    # Μήνυμα για αγορά ή πώληση
    transaction = "Αγορά" if transaction_type == 'buy' else "Πώληση"
    
    # Τρέχουσα ημερομηνία και ώρα
    current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Δημιουργία του περιεχομένου του email
    html_content = f"""
        Πραγματοποιήθηκε <strong>{transaction} {CRYPTO_SYMBOL}</strong>.<br>
        Τεμάχια: {quantity}<br>
        Αξία: {round(price, 2)} €<br>
        Ημερομηνία: {current_time}<br>
    """
    
    # Προσθήκη του Daily Profit μόνο αν το transaction δεν είναι 'buy'
    if transaction_type == 'sell':
        html_content += f"Daily Profit: {round(daily_profit, 2)} €<br>"
    
    message = Mail(
        from_email='info@f2d.gr',
        to_emails='info@f2d.gr',
        subject=f'Scalping bot - {transaction} {CRYPTO_SYMBOL}',
        html_content=html_content
    )

    try:
        # Αποστολή του email μέσω SendGrid API
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        sg.send(message)
        logging.info("Email sent successfully!")
    except Exception as e:
        # Χρήση logging για αποτυχία αποστολής
        logging.warning(f"Error sending email: {e}")



def reset_bot_state():
    global daily_profit, total_profit, current_trades, active_trade, trade_amount, highest_price, trailing_profit_active

    logging.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    logging.info("Resetting bot state...")

    # Δημιουργία του pause flag
    pause_file = f"/opt/python/scalping-bot/{CRYPTO_FULLNAME}/pause.flag"
    open(pause_file, 'w').close()
    logging.info("Pause flag created. Normal operation is paused.")
    
    order_successful = False
    execution_price = None
    if execution_price is None:
        execution_price = 0

    

    try:
        load_state()

        # Αν υπάρχει ενεργή συναλλαγή, επιχειρούμε να πουλήσουμε αν η τρέχουσα τιμή είναι υψηλότερη από την τιμή αγοράς
        if active_trade:
            logging.info(f"Attempting to sell active trade of {active_trade}")
            current_price = get_crypto_price()
            if current_price is None:
                logging.error("Failed to fetch current price. Skipping trade execution.")
                return

            # Υπολογισμός κέρδους πριν αφαιρεθούν τα fees
            potential_profit = (current_price - active_trade) * trade_amount

            # Εκτίμηση των fees για τη συναλλαγή
            estimated_fees = current_price * trade_amount * FEES_PERCENTAGE
            logging.info(f"Estimated fees for the trade: {round(estimated_fees, 2)}")

            # Υπολογισμός καθαρού κέρδους μετά την αφαίρεση των εκτιμώμενων fees
            net_profit = potential_profit - estimated_fees

            # Πώληση μόνο αν το κέρδος μετά την αφαίρεση των εκτιμώμενων fees υπερβαίνει το κατώφλι
            if current_price > active_trade and net_profit >= MINIMUM_PROFIT_THRESHOLD:
                order_successful, execution_price = place_order("sell", trade_amount, current_price)
                
                if order_successful and execution_price:              
                    logging.info(f"Sold {trade_amount} of {CRYPTO_NAME} at {round(execution_price, 2)} with net profit: {round(net_profit, 2)}")
                    sendgrid_email(trade_amount, "sell", execution_price, daily_profit)
                    
                    # Ανανεώνουμε το συνολικό κέρδος με το τρέχον ημερήσιο κέρδος πριν το reset
                    total_profit += net_profit + daily_profit

                    # Reset των μεταβλητών στο state.json μόνο αν εκτελέστηκε η πώληση
                    daily_profit = 0
                    current_trades = 0
                    active_trade = None
                    trade_amount = 0
                    highest_price = None
                    trailing_profit_active = False

                    # Χρονική αναμονή μετά την πώληση για αποφυγή άμεσης αγοράς
                    
                    save_state()
                    # Αποθήκευση του χρόνου τελευταίου reset για να ενεργοποιηθεί το cooldown
                    save_cooldown_state()
                    logging.info("Cooldown initiated to prevent immediate re-buy.")

                    logging.info("Bot state reset completed.")
                else:
                    logging.info(f"Failed to execute sell order at {current_price}. No state reset performed.")
            else:
                logging.info(f"No sale executed. Current price ({current_price}) is not higher than the active trade price ({active_trade}) or net profit ({net_profit}) is below threshold ({MINIMUM_PROFIT_THRESHOLD}).")
                logging.info("No state reset performed as the active trade remains open.")
                

        else:
            logging.info(f"No active trade found. Updating total profit and resetting daily profit and current trades.")
            # Ανανεώνουμε το συνολικό κέρδος με το τρέχον ημερήσιο κέρδος πριν το reset
            total_profit += daily_profit
            daily_profit = 0
            current_trades = 0
            # Αποθήκευση της νέας κατάστασης
            save_state()
            logging.info("Bot state reset completed.")

    finally:
        # Διαγραφή του pause flag στο τέλος της διαδικασίας
        if os.path.exists(pause_file):
            os.remove(pause_file)
        logging.info("Pause flag removed. Resuming normal operation.")








# Load the state from the file
def load_state():
    global daily_profit, total_profit, current_trades, active_trade, trade_amount, highest_price, trailing_profit_active
    try:
        with open(state_file, "r") as f:
            state = json.load(f)
            daily_profit = state.get("daily_profit", 0)
            total_profit = state.get("total_profit", 0)  # Load the total_profit
            current_trades = state.get("current_trades", 0)
            active_trade = state.get("active_trade", None)
            trade_amount = state.get("trade_amount", 0)
            highest_price = state.get("highest_price", None)
            trailing_profit_active = state.get("trailing_profit_active", False)
            logging.info(
                f"Loaded state: daily_profit={round(daily_profit, 2)}, total_profit={round(total_profit, 2)}, "
                f"current_trades={current_trades}, active_trade={active_trade}, trade_amount={trade_amount}, "
                f"highest_price={highest_price}, trailing_profit_active={trailing_profit_active}"
            )
    except FileNotFoundError:
        daily_profit = 0
        total_profit = 0  # Initialize total_profit if the state file is not found
        current_trades = 0
        active_trade = None
        trade_amount = 0
        highest_price = None
        trailing_profit_active = False
        save_state()  # Initialize the state file if it doesn't exist
        logging.info(
            f"State file not found. Initialized new state: daily_profit={daily_profit}, total_profit={total_profit}, "
            f"current_trades={current_trades}, active_trade={active_trade}, trade_amount={trade_amount}, "
            f"highest_price={highest_price}, trailing_profit_active={trailing_profit_active}"
        )



def save_cooldown_state():
    """Αποθηκεύει τον χρόνο τελευταίου reset στο αρχείο cooldown"""
    with open(cooldown_file, 'w') as f:
        json.dump({"last_reset_time": time.time()}, f)


def load_cooldown_state():
    """Φορτώνει τον χρόνο τελευταίου reset από το αρχείο"""
    if os.path.exists(cooldown_file):
        with open(cooldown_file, 'r') as f:
            data = json.load(f)
        return data.get("last_reset_time", 0)
    return 0


def check_cooldown():
    """Ελέγχει αν έχει λήξει το cooldown και επιστρέφει τον υπόλοιπο χρόνο"""
    last_reset_time = load_cooldown_state()
    current_time = time.time()
    remaining_time = COOLDOWN_DURATION - (current_time - last_reset_time)
    return remaining_time <= 0, max(0, int(remaining_time))






# Save the state to the file
def save_state():
    state = {
        "daily_profit": round(daily_profit, 2) if daily_profit is not None else 0,
        "total_profit": round(total_profit, 2) if total_profit is not None else 0,  # Save the total_profit
        "current_trades": current_trades,
        "active_trade": round(active_trade, 2) if active_trade is not None else 0,
        "trade_amount": trade_amount,
        "highest_price": round(highest_price, 2) if highest_price is not None else 0,
        "trailing_profit_active": trailing_profit_active
    }
    with open(state_file, "w") as f:
        json.dump(state, f)
    logging.info(
        f"Saved state: daily_profit={state['daily_profit']}, total_profit={state['total_profit']}, "
        f"current_trades={current_trades}, active_trade={state['active_trade']}, trade_amount={trade_amount}, "
        f"highest_price={state['highest_price']}, trailing_profit_active={trailing_profit_active}"
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








def get_order_details(order_id, jwt_token):
    """
    Ανακτά πληροφορίες για μια παραγγελία από το Coinbase API χρησιμοποιώντας το endpoint για ιστορικές παραγγελίες.
    
    :param order_id: Το ID της παραγγελίας.
    :param jwt_token: Το JWT token για την επικύρωση της αίτησης.
    :return: Ένα λεξικό με την τελική τιμή εκτέλεσης (average_filled_price).
    """
    request_host = "api.coinbase.com"
    order_details_path = f"/api/v3/brokerage/orders/historical/{order_id}"
    url = f"https://{request_host}{order_details_path}"

    uri = f"GET {request_host}{order_details_path}"
    jwt_token = build_jwt(uri)  # Δημιουργία νέου JWT token

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            order_details = response.json().get('order', {})

            # Logging για το πλήρες αντικείμενο της παραγγελίας
            logging.debug(f"Full order details: {order_details}")

            # Εξαγωγή των σημαντικών τιμών
            executed_value = float(order_details.get("filled_value", 0))
            filled_size = float(order_details.get("filled_size", 0))
            average_filled_price = float(order_details.get("average_filled_price", 0))
            total_fees = float(order_details.get("total_fees", 0))
            status = order_details.get("status", "unknown")

            # Logging της κατάστασης της παραγγελίας
            logging.debug(f"Order status: {status}")

            return {
                "order_id": order_id,
                "executed_value": executed_value,
                "filled_size": filled_size,
                "average_filled_price": average_filled_price,
                "total_fees": total_fees,
                "status": status
            }
        else:
            logging.error(f"Failed to retrieve order details. Status: {response.status_code}, Data: {response.text}")
            return {
                "error": response.status_code,
                "message": response.text
            }

    except Exception as e:
        logging.error(f"Error fetching order details: {e}")
        return {
            "error": "exception",
            "message": str(e)
        }




# Τοποθέτηση εντολών αγοράς/πώλησης με επιπλέον logging
def place_order(side, size, price):
    logging.debug(f"Placing {side.upper()} order for {size} {CRYPTO_NAME} at price {price}")
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

        # Έλεγχος αν το status είναι 200 και η απάντηση επιτυχημένη
        if res.status == 200:
            if response_data.get("success", False):
                logging.info(f"Order placed successfully: {response_data}")

                time.sleep(5)
                # Αποθήκευση του order_id για ανάκτηση λεπτομερειών
                order_id = response_data.get("success_response", {}).get("order_id")
                
                if order_id:
                    # Ανάκτηση των λεπτομερειών της παραγγελίας
                    order_details = get_order_details(order_id, jwt_token)
                    
                    # Προσθήκη logging για να δούμε τι επιστρέφει το get_order_details
                    logging.debug(f"Order details retrieved: {order_details}")                    
                    
                    average_filled_price = order_details.get("average_filled_price")
                    total_fees = order_details.get("total_fees")

                    if average_filled_price:
                        logging.info(f"Order executed at price: {round(average_filled_price, 2)}, fees: {round(total_fees, 2)}")
                        return True, average_filled_price
                    else:
                        logging.warning("Order placed but no execution price found.")
                        return True, None
                else:
                    logging.warning("Order placed but no order_id returned.")
                    return True, None
            else:
                # Εξαγωγή των λεπτομερειών λάθους αν υπάρχει
                error_message = response_data.get("error", "Unknown error")
                error_details = response_data.get("message", response_data)

                logging.error(
                    f"Failed to place order. Status: {res.status}, Error: {error_message}, Details: {error_details}"
                )
                return False, None
        else:
            logging.error(f"HTTP error occurred. Status: {res.status}, Data: {data}")
            return False, None

    except Exception as e:
        logging.error(f"Error making request: {e}")
        return False, None
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
                df = df.copy()  # Δημιουργούμε αντίγραφο του DataFrame για να μην αλλάξουμε το πρωτότυπο
                df.index = pd.to_datetime(df.index)  # Μετατροπή του index σε DatetimeIndex

            df = df.resample(timeframe).last()  # Χρησιμοποιεί το τελευταίο διαθέσιμο κλείσιμο για το timeframe
        # ---------------------------------------

        # Μετατροπή των τιμών σε αριθμητικές (αν δεν είναι ήδη)
        df['close'] = pd.to_numeric(df['close'], errors='coerce')

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
                df.index = pd.to_datetime(df.index)  # Μετατροπή του index σε DatetimeIndex
                logging.info(f"Index type after conversion: {type(df.index)}")

            df = df.resample(timeframe).last()  # Χρησιμοποιεί το τελευταίο διαθέσιμο κλείσιμο για το timeframe
            logging.info(f"Resampled data: {df.index.min()} to {df.index.max()}")  # Έλεγχος resampling
        # ---------------------------------------

        # Μετατροπή των τιμών σε αριθμητικές (αν δεν είναι ήδη)
        df['close'] = pd.to_numeric(df['close'], errors='coerce')

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
                df.index = pd.to_datetime(df.index)  # Μετατροπή του index σε DatetimeIndex
                logging.info(f"Index type after conversion: {type(df.index)}")

            df = df.resample(timeframe).last()  # Χρησιμοποιεί το τελευταίο διαθέσιμο κλείσιμο για το timeframe
            logging.info(f"Resampled data: {df.index.min()} to {df.index.max()}")  # Έλεγχος resampling
        # ---------------------------------------

        # Μετατροπή των τιμών σε αριθμητικές (αν δεν είναι ήδη)
        if df['close'].dtype != 'float64' and df['close'].dtype != 'int64':
            df['close'] = pd.to_numeric(df['close'], errors='coerce')

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




def calculate_adx(df, period=14):
    # Υπολογισμός του +DM και -DM
    df['up_move'] = df['high'] - df['high'].shift(1)
    df['down_move'] = df['low'].shift(1) - df['low']
    df['plus_dm'] = np.where((df['up_move'] > df['down_move']) & (df['up_move'] > 0), df['up_move'], 0)
    df['minus_dm'] = np.where((df['down_move'] > df['up_move']) & (df['down_move'] > 0), df['down_move'], 0)
    
    # Υπολογισμός του TR (True Range)
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = abs(df['high'] - df['close'].shift(1))
    df['tr3'] = abs(df['low'] - df['close'].shift(1))
    df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    
    # Υπολογισμός του ATR
    df['atr'] = df['true_range'].rolling(window=period).mean()
    
    # Υπολογισμός των Directional Indicators
    df['plus_di'] = 100 * (df['plus_dm'].rolling(window=period).mean() / df['atr'])
    df['minus_di'] = 100 * (df['minus_dm'].rolling(window=period).mean() / df['atr'])
    
    # Υπολογισμός του DX και του ADX
    df['dx'] = 100 * (abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di']))
    df['adx'] = df['dx'].rolling(window=period).mean()
    
    # Αποθήκευση του ADX και του ATR πριν από τον καθαρισμό
    adx = df['adx'].copy()
    atr = df['atr'].copy()
    
    # Καθαρισμός των προσωρινών στηλών
    df.drop(['up_move', 'down_move', 'plus_dm', 'minus_dm', 'tr1', 'tr2', 'tr3', 'true_range',
             'atr', 'plus_di', 'minus_di', 'dx', 'adx'], axis=1, inplace=True)
    
    return adx, atr




def calculate_stochastic(df, k_period=14, d_period=3):
    df['low_k'] = df['low'].rolling(window=k_period).min()
    df['high_k'] = df['high'].rolling(window=k_period).max()
    
    df['%K'] = 100 * ((df['close'] - df['low_k']) / (df['high_k'] - df['low_k']))
    df['%D'] = df['%K'].rolling(window=d_period).mean()
    
    # Αφαιρούμε τις προσωρινές στήλες
    df.drop(['low_k', 'high_k'], axis=1, inplace=True)
    
    return df['%K'], df['%D']





def calculate_volume_confirmation(df, window=20):
    """
    Calculates the average volume over a given time period (window) and
    returns an indicator if the current volume exceeds the average.

    :param df: DataFrame containing the data with a 'volume' column
    :param window: The number of periods for the moving average
    :return: True if the current volume is above the average, otherwise False
    """
    if 'volume' not in df.columns:
        logging.info("The 'volume' column does not exist in the DataFrame.")
        return
    
    # Convert the volume column to numeric format
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    
    # Remove rows with invalid values (NaN)
    df = df.dropna(subset=['volume'])

    # Calculate the moving average of the volume
    df['volume_avg'] = df['volume'].rolling(window=window).mean()

    # Check if the last volume is above the moving average
    if not df.empty and 'volume_avg' in df.columns:
        current_volume = df['volume'].iloc[-1]
        
        avg_volume = df['volume_avg'].iloc[-1]
        
        volume_confirmation = current_volume > avg_volume

        logging.info(f"Latest volume: {current_volume}, MAV ({window} periods): {round(avg_volume, 2)}")
        #logging.info(f"Moving average volume ({window} periods): {round(avg_volume, 2)}")
        #logging.info(f"Volume confirmation: {'Yes' if volume_confirmation else 'No'}")

        return volume_confirmation, current_volume, avg_volume
    else:
        logging.info("There is not enough data to calculate the moving average volume.")
        return False, None, None




def calculate_bollinger_bands(df, period=20, num_std_dev=2):
    df['SMA'] = df['close'].rolling(window=period).mean()
    df['STD'] = df['close'].rolling(window=period).std()
    df['Bollinger_Upper'] = df['SMA'] + (df['STD'] * num_std_dev)
    df['Bollinger_Lower'] = df['SMA'] - (df['STD'] * num_std_dev)
    
    # Επιστρέφουμε τις στήλες με τις μπάντες
    return df['Bollinger_Upper'], df['Bollinger_Lower']



def calculate_vwap(df):
    # Υπολογισμός του VWAP
    df['Typical_Price'] = (df['high'] + df['low'] + df['close']) / 3
    df['VWAP'] = (df['Typical_Price'] * df['volume']).cumsum() / df['volume'].cumsum()
    
    return df['VWAP']








def calculate_indicators(df, source_url, short_ma_period, long_ma_period):
    # Έλεγχος αν υπάρχουν αρκετά δεδομένα για τον υπολογισμό των δεικτών
    if len(df) < max(short_ma_period, long_ma_period, 26):  # Μακρύτερη περίοδος για MACD είναι 26
        #logging.warning(f"Not enough data to calculate indicators from {source_url}. Data length: {len(df)}")
        return False  # Επιστρέφει False για να δηλώσει ότι δεν υπάρχουν αρκετά δεδομένα
    return True  # Επιστρέφει True αν υπάρχουν αρκετά δεδομένα





# Fetch candlestick data from 3 different routes with try catch
def fetch_data():
    logging.debug(f"Fetching data for {CRYPTO_SYMBOL} with granularity: {GRANULARITY}")

    urls = [
        f"https://api.coinbase.com/api/v3/brokerage/market/products/{CRYPTO_SYMBOL}/candles?granularity={GRANULARITY_TEXT}",
        f"https://api.exchange.coinbase.com/products/{CRYPTO_SYMBOL}/candles?granularity={GRANULARITY}",
        #f"https://api.coingecko.com/api/v3/coins/{CRYPTO_FULLNAME.lower()}/ohlc?days=1&vs_currency=eur",
        f"https://api.binance.com/api/v3/klines?symbol={BINANCE_PAIR}&interval={BINANCE_INTERVAL}",
    ]

    random.shuffle(urls)
    max_retries = 2
    delay_between_retries = 10
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0"

    for url in urls:
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
                    response_json = json.loads(data)
                    logging.debug(f"Parsed data structure: {response_json}")
                except json.JSONDecodeError:
                    logging.error(f"Failed to parse JSON from {url}. Response body: {data}")
                    break

                # Ειδικός έλεγχος για το Coinbase API URL
                if "api.coinbase.com" in url and "candles" in response_json:
                    candles = response_json["candles"]
                else:
                    candles = response_json

                if not candles or len(candles) == 0:
                    logging.warning(f"No valid data fetched from {url}. Trying next URL.")
                    break

                # Διαχείριση των δεδομένων στο DataFrame για Coinbase
                if "api.coinbase.com" in url:
                    df = pd.DataFrame(candles, columns=["time", "low", "high", "open", "close", "volume"])
                    df["time"] = pd.to_datetime(df["time"], unit="s")

                # Ειδική περίπτωση για το CoinGecko: η API επιστρέφει μόνο 5 στήλες (time, open, high, low, close)
                elif "coingecko" in url:
                    df = pd.DataFrame(candles, columns=["time", "open", "high", "low", "close"])
                    df["time"] = pd.to_datetime(df["time"], unit="ms")

                # Ειδική περίπτωση για το Binance, όπου μπορεί να επιστρέφει 12 στήλες αντί για 6
                elif "binance" in url:
                    if len(candles[0]) == 12:
                        df = pd.DataFrame(candles, columns=[
                            "time", "open", "high", "low", "close", "volume", 
                            "close_time", "quote_asset_volume", "number_of_trades", 
                            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
                        ])
                    else:
                        df = pd.DataFrame(candles, columns=["time", "open", "high", "low", "close", "volume"])
                    
                    df["time"] = pd.to_datetime(df["time"], unit="ms")

                # Γενική περίπτωση για άλλες APIs, όπως Kraken
                else:
                    df = pd.DataFrame(candles, columns=["time", "low", "high", "open", "close", "volume"])
                    df["time"] = pd.to_datetime(df["time"], unit="s")

                # Υπολογισμός δεικτών
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
    global daily_profit, current_trades, highest_price, active_trade, trade_amount, start_bot, trailing_profit_active

    
    logging.info(f"Executing trade logic for {CRYPTO_SYMBOL}")
    logging.info(f"Scalp target: {SCALP_TARGET}, Daily profit target: {DAILY_PROFIT_TARGET}, Trailing threshold: {TRAILING_PROFIT_THRESHOLD}, Stop-loss: {STOP_LOSS}")

    
    order_successful = False
    execution_price = None
    
    
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
        logging.debug(f"Current Price: {current_price}, Highest_price: {highest_price}")

        # Αν υπάρχει ανοιχτή θέση, έλεγχος για πώληση
        if active_trade:
            logging.info(f"Active trade exists at {round(active_trade, 2)}. Checking for sell opportunity.")

            # Αρχικοποίηση του highest_price αν είναι None
            if highest_price is None:
                highest_price = active_trade
                logging.info(f"Initialized highest_price to {highest_price}")
                save_state()  # Αποθήκευση του ενημερωμένου highest_price

            # Ενημέρωση του highest_price μόνο αν η τρέχουσα τιμή είναι μεγαλύτερη
            if current_price > highest_price:
                highest_price = current_price
                logging.info(f"Updated highest_price to {highest_price}")
                save_state()  # Αποθήκευση του ενημερωμένου highest_price

            logging.info(f"Current Price: {current_price}, Highest Price: {highest_price}")



            df, source_url = fetch_data()
            if df is None:
                logging.error(f"Failed to fetch data from {source_url}")
                return

                    
            # Πριν από τον υπολογισμό δεικτών
            df['high'] = pd.to_numeric(df['high'], errors='coerce')
            df['low'] = pd.to_numeric(df['low'], errors='coerce')
            df['close'] = pd.to_numeric(df['close'], errors='coerce')



            # Call the calculate_adx function, which should return both adx and atr
            adx, atr = calculate_adx(df)

            # Λήψη της τελευταίας τιμής
            atr_value = atr.iloc[-1]
                     
            
            # Υπολογισμός της τιμής του δυναμικού stop-loss βάσει του ATR
            stop_loss_price = active_trade - (atr_value * ATR_MULTIPLIER)
            

            logging.info(f"Setting dynamic stop-loss at: {round(stop_loss_price, 2)} (ATR Multiplier: {ATR_MULTIPLIER})")

            # Check if the current price triggers the stop-loss
            if current_price <= stop_loss_price:
                logging.info(f"Dynamic stop-loss triggered. Selling at price {current_price}")
                order_successful, execution_price = place_order("sell", trade_amount, current_price)

                if order_successful and execution_price:
                    daily_profit -= (active_trade - current_price) * trade_amount
                    sendgrid_email(trade_amount, "sell", current_price, daily_profit)
                    active_trade = None
                    trade_amount = 0
                    highest_price = None
                    current_trades += 1
                    save_state()
                    return  # Σταματάει η εκτέλεση εδώ αν γίνει πώληση λόγω stop-loss
                else:
                    logging.info(f"Failed to execute sell order for stop-loss at {current_price}")




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
                    logging.info(f"Trailing sell price is {round(trailing_sell_price, 2)}")

                    # Έλεγχος αν πρέπει να πουλήσουμε λόγω trailing profit
                    if current_price <= trailing_sell_price:
                        logging.info(f"Trailing profit triggered. Selling at {current_price}")
                        order_successful, execution_price = place_order("sell", trade_amount, current_price)

                        if order_successful and execution_price:
                            daily_profit += (current_price - active_trade) * trade_amount
                            sendgrid_email(trade_amount, "sell", current_price, daily_profit)
                            active_trade = None
                            trade_amount = 0
                            highest_price = None
                            trailing_profit_active = False
                            current_trades += 1
                            save_state()
                            return  # Σταματάμε εδώ αν έγινε πώληση λόγω trailing profit
                        else:
                            logging.info(f"Failed to execute sell order for trailing profit at {current_price}")
                    else:
                        logging.info(f"Trailing profit active. Current price {current_price} has not dropped below trailing sell price {round(trailing_sell_price, 2)}.")

                else:
                    # Αν το trailing profit δεν είναι ενεργό και η τιμή δεν έχει φτάσει το scalp target
                    logging.info(f"Waiting for price to reach scalp target at {round(scalp_target_price, 2)}")


            else:
                # Αν το trailing profit δεν είναι ενεργοποιημένο, πουλάμε στο scalp target
                if current_price >= scalp_target_price:
                    logging.info(f"Selling at {current_price} for profit (scalp target)")
                    order_successful, execution_price = place_order("sell", trade_amount, current_price)

                    if order_successful and execution_price:
                        daily_profit += (current_price - active_trade) * trade_amount
                        sendgrid_email(trade_amount, "sell", current_price, daily_profit)
                        active_trade = None
                        trade_amount = 0
                        highest_price = None
                        current_trades += 1
                        save_state()
                        return  # Σταματάει η εκτέλεση εδώ αν γίνει πώληση λόγω scalp target
                    else:
                        logging.info(f"Failed to execute sell order for scalp target at {current_price}")

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
 

        
        # Πριν από τον υπολογισμό δεικτών
        df['high'] = pd.to_numeric(df['high'], errors='coerce')
        df['low'] = pd.to_numeric(df['low'], errors='coerce')
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
  
        
        # Υπολογισμός των δεικτών
        macd, signal = calculate_macd(df)
        rsi = calculate_rsi(df)
        bollinger_upper, bollinger_lower = calculate_bollinger_bands(df)
        vwap = calculate_vwap(df)

        # Λήψη των τελευταίων τιμών για κάθε δείκτη
        macd_last = macd.iloc[-1] if isinstance(macd, pd.Series) else macd
        signal_last = signal.iloc[-1] if isinstance(signal, pd.Series) else signal
        rsi_last = rsi.iloc[-1] if isinstance(rsi, pd.Series) else rsi
        bollinger_upper_last = bollinger_upper.iloc[-1] if isinstance(bollinger_upper, pd.Series) else bollinger_upper
        bollinger_lower_last = bollinger_lower.iloc[-1] if isinstance(bollinger_lower, pd.Series) else bollinger_lower
        vwap_last = vwap.iloc[-1] if isinstance(vwap, pd.Series) else vwap

        # Logging για έλεγχο τύπων και τιμών
        logging.info(
            f"Indicators: MACD={round(macd_last, 3)}, Signal={round(signal_last, 3)}, "
            f"RSI={round(rsi_last, 3)}, Bollinger Upper={round(bollinger_upper_last, 3)}, "
            f"Bollinger Lower={round(bollinger_lower_last, 3)}, Current Price={round(current_price, 3)}, "
            f"VWAP={round(vwap_last, 3)}"
        )

        # Βάρη για κάθε δείκτη (επιβεβαίωση ότι είναι `float`)
        weights = {
            'macd': float(0.3),
            'rsi': float(0.3),
            'bollinger': float(0.2),
            'vwap': float(0.2)
        }

        # Logging των τύπων των βαρών
        #logging.info(f"Weight Types - MACD: {type(weights['macd'])}, RSI: {type(weights['rsi'])}, "
        #             f"Bollinger: {type(weights['bollinger'])}, VWAP: {type(weights['vwap'])}")

        # Αρχικοποίηση βαθμολογίας και βαθμολογιών δεικτών
        score = 0
        scores = {}

        # Λογική για MACD - θετικό αν το MACD είναι πάνω από τη γραμμή signal
        scores['macd'] = weights['macd'] * (1 if macd_last > signal_last else -1)
        score += scores['macd']

        # Λογική για RSI - θετικό αν το RSI είναι κάτω από το 50 (υποδεικνύει δυνατότητα ανόδου)

        scores['rsi'] = weights['rsi'] * (1 if rsi_last < RSI_THRESHOLD else -1)
        score += scores['rsi']

        # Λογική για Bollinger Bands - θετικό αν η τιμή βρίσκεται κοντά στην κατώτερη μπάντα
        if current_price <= bollinger_lower_last:
            scores['bollinger'] = weights['bollinger'] * 1
        elif current_price >= bollinger_upper_last:
            scores['bollinger'] = weights['bollinger'] * -1
        else:
            scores['bollinger'] = 0
        score += scores['bollinger']

        # Λογική για VWAP - θετικό αν η τιμή είναι πάνω από το VWAP (δείχνει ανοδική πίεση)
        scores['vwap'] = weights['vwap'] * (1 if current_price > vwap_last else -1)
        score += scores['vwap']

        # Logging των βαθμολογιών των δεικτών και της τελικής βαθμολογίας
        logging.info(
            f"Score breakdown: MACD Score={scores['macd']}, RSI Score={scores['rsi']}, "
            f"Bollinger Score={scores['bollinger']}, VWAP Score={scores['vwap']}, "
            f"Total Score={round(score, 3)}"
        )


        
        # Όριο για εκτέλεση αγοράς - ας πούμε ότι απαιτείται score >= 0.5 για να προχωρήσει η αγορά
        buy_threshold = 0.5
            
                
        # Εμφάνιση του εύρους δεδομένων πριν το resample
        # logging.info(f"Data available for SOL-EUR: {df.index.min()} to {df.index.max()}")

        # ---------------------------------------
        # Μετατροπή της στήλης 'time' σε DatetimeIndex, αν υπάρχει
        if "time" in df.columns:
            # Προσπαθούμε να μετατρέψουμε τη στήλη σε datetime
            df["time"] = pd.to_datetime(df["time"], errors="coerce")
            
            if df["time"].isna().all():
                # Δημιουργούμε DatetimeIndex αν όλη η στήλη είναι NaT
                logging.warning("No valid 'time' data; generating DatetimeIndex with regular intervals.")
                df["time"] = pd.date_range(start="2024-10-01", periods=len(df), freq="T")
            
            df = df.dropna(subset=["time"])
            df.set_index("time", inplace=True)
            #logging.info(f"Index converted to DatetimeIndex: {df.index}")
        else:
            # Χρήση DatetimeIndex αν λείπει η στήλη 'time'
            if isinstance(df.index, pd.RangeIndex):
                logging.warning("No valid datetime index. Creating a DatetimeIndex.")
                df.index = pd.date_range(start="2024-10-01", periods=len(df), freq="T")
                logging.info(f"New index created: {df.index}")
            else:
                logging.error("No 'time' column or valid index for resampling.")
                return
        # ---------------------------------------

        # ---------------------------------------
        # Συμπληρωματικός Έλεγχος για επιβεβαίωση δεικτών (προαιρετικός)
        if ENABLE_ADDITIONAL_CHECKS:
            try:
                # Resampling data σε ωριαίο χρονικό διάστημα
                df_resampled = df.resample("1H").last().dropna()  # Αφαιρούμε τυχόν κενές γραμμές μετά το resampling

                # Ελέγχουμε αν υπάρχουν αρκετά δεδομένα για υπολογισμό των δεικτών
                if len(df_resampled) < max(short_ma_period, long_ma_period, 14):
                    logging.warning(
                        f"Not enough resampled data for calculating indicators. Data length: {len(df_resampled)}"
                    )
                    logging.info("Continuing without additional confirmation checks.")
                else:
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
                            f"Additional check failed: MA_Short_Long={ma_short_long_period}, "
                            f"MA_Long_Long={ma_long_long_period}, MACD_Long={macd_long.iloc[-1]}, "
                            f"Signal_Long={signal_long.iloc[-1]}, RSI_Long={rsi_long}"
                        )
                        logging.info(
                            "Indicators are not consistent across multiple timeframes. No buy action will be taken."
                        )
                    else:
                        logging.info(
                            f"Additional check passed: MA_Short={round(ma_short_long_period, 3)}, "
                            f"MA_Long={round(ma_long_long_period, 2)}, MACD={round(macd_long.iloc[-1], 3)}, "
                            f"Signal={round(signal_long.iloc[-1], 3)}, RSI={round(rsi_long, 3)}"
                        )

            except Exception as e:
                logging.error(f"Exception occurred during additional checks: {type(e).__name__}: {e}")
                logging.info(
                    "Αποτυχία κατά τον υπολογισμό των δεικτών. Παρακαλούμε ελέγξτε την πηγή των δεδομένων "
                    "και βεβαιωθείτε ότι περιέχουν έγκυρες χρονικές πληροφορίες και επαρκή δεδομένα για επεξεργασία."
                )

                
        # ---------------------------------------
       
        # Αγοραστικό σήμα
        # Πρώτος έλεγχος για βασικούς δείκτες
                
        if score >= buy_threshold:
            logging.info(f"Trade signal score is positive: {round(score, 3)}. Initiating a buy at {current_price}.")            
            order_successful, execution_price = place_order("buy", TRADE_AMOUNT, current_price)
            
            if order_successful and execution_price:
                active_trade = execution_price  # Ενημέρωση της ανοιχτής θέσης με την τιμή εκτέλεσης
                trade_amount = TRADE_AMOUNT  # Καταχώρηση του ποσού συναλλαγής
                logging.info(f"Order placed successfully at price: {execution_price}")
                
                # Κλήση της sendgrid_email πριν μηδενιστούν οι τιμές
                sendgrid_email(trade_amount, "buy", execution_price, daily_profit=0) 
                
                highest_price = execution_price
                current_trades += 1
                save_state()  # Αποθήκευση της κατάστασης μετά την αγορά
            else:
                logging.info(f"Order placement failed. No buy action taken.")

        else:
            logging.info(f"Trade signal score did not meet the buy threshold: {round(score, 3)}. No action taken.")


        # Έλεγχος αν επιτεύχθηκε το καθημερινό κέρδος ή το όριο συναλλαγών
        if daily_profit >= DAILY_PROFIT_TARGET or current_trades >= MAX_TRADES_PER_DAY:
            logging.info(
                f"Daily profit target reached: {round(daily_profit, 2)} or maximum trades executed."
            )
            start_bot = False
            #save_state()  # Αποθήκευση κατάστασης όταν σταματάει το bot

    except Exception as e:
        logging.error(f"Exception occurred in execute_scalping_trade: {type(e).__name__}: {e}")
        return


# Main loop (updated to load state)
def run_bot():
    logging.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    logging.info("Starting bot...")
    load_state()  # Load the previous state
    execute_scalping_trade(CRYPTO_SYMBOL)
    # save_state()  # Save the state after each execution
    logging.info("Bot execution completed.")



# Τροποποίηση της κύριας συνάρτησης για να ελέγχει το cooldown και να εμφανίζει το χρόνο που απομένει
if __name__ == "__main__":
    if "--reset" in sys.argv:
        reset_bot_state()  # Εκτέλεση της συνάρτησης reset
    else:
        is_cooldown_over, remaining_time = check_cooldown()  # Έλεγχος αν έχει λήξει το cooldown
        
        if is_cooldown_over:
            run_bot()  # Εκτέλεση του bot
        else:
            remaining_minutes = remaining_time // 60  # Μετατροπή σε λεπτά
            logging.info(f"Bot is in cooldown. Remaining time: {remaining_minutes} minutes.")