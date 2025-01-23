from tabulate import tabulate
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
import pushover
import csv

###################################################################################################################################################################################################################################
# Αρχικές μεταβλητές - πρέπει να οριστούν

# 1. Crypto asset to scalping - coinbase
CRYPTO_SYMBOL = "AVAX-EUR"
CRYPTO_NAME = "AVAX"
CRYPTO_FULLNAME = "AVAX"     #AVALANCHE-2
CRYPTO_CURRENCY = "EUR"

# 2. Ειδική περίπτωση URL απο Binance
BINANCE_PAIR = "AVAXEUR"
BINANCE_INTERVAL = "5m"

# 3. Scalping variables
SCALP_TARGET = 1.01
TRADE_AMOUNT = 50  # Μονάδα κρυπτονομίσματος
DYNAMIC_TRADE_ENABLED = False    # Δυναμικός υπολογισμός επένδυσης σύμφωνα με το ημερήσιο κέρδος / ζημιά


# 4. Τεχνικοί Δείκτες
short_ma_period = 5  # 5 περιόδων
long_ma_period = 20  # 20 περιόδων
RSI_THRESHOLD = 30
ADX_THRESHOLD = 25
STOCHASTIC_OVERSOLD_THRESHOLD = 40
BUY_THRESHOLD = 0.5     # Όριο για εκτέλεση αγοράς - ας πούμε ότι απαιτείται score >= 0.5 για να προχωρήσει η αγορά
GRANULARITY = 300
GRANULARITY_TEXT = "FIVE_MINUTE"
ENABLE_TABULATE_INDICATORS = False      # αποτελέσματα δεικτών σε γραμμογραφημένη μορφή
ENABLE_GEORGE_SAYS = False              # Εμφάνιση τεχνικών δεικτών μετά το buy
ENABLE_FAILOVER_BOT = False             # Ενεργοποιεί απόφαση απο εξωτερικό bot.

# 5. Ρυθμίσεις και ενεργοποίηση Score History
ENABLE_SCORE_HISTORY = False             # Ενεργοποίηση Score History
MAX_SCORE_HISTORY = 3                   # Ορισμός της σταθεράς για το μέγιστο μέγεθος του score_history - πόσες τιμές θα αποθηκεύονται στο αρχείο
POSITIVE_THRESHOLD = 2                  # Πλήθος των θετικών τιμών που απαιτούνται

# 6. Risk Management
ENABLE_STOP_LOSS = False
STOP_LOSS = 0.95
ENABLE_DYNAMIC_STOP_LOSS = False   # Ενεργοποίηση δυναμικού stop-loss
ATR_MULTIPLIER = 3

# Συντηρητικοί traders τείνουν να επιλέγουν έναν χαμηλότερο συντελεστή, γύρω στο 1.5 έως 2, ώστε να κλείνουν τις θέσεις τους πιο κοντά στην τρέχουσα τιμή για να μειώνουν τις απώλειες.
# Πιο επιθετικοί traders προτιμούν υψηλότερο atr_multiplier, όπως 2.5 ή 3, δίνοντας μεγαλύτερο χώρο στο περιθώριο τιμών και στο bot να αποφεύγει την απότομη πώληση σε βραχυπρόθεσμες διακυμάνσεις.
# Για το Ethereum, το 2 ή 2.5 αποτελεί συνήθη επιλογή, καθώς προσφέρει ισορροπία μεταξύ αποφυγής μικρών διακυμάνσεων και μείωσης κινδύνου από μεγαλύτερες πτώσεις.

ENABLE_TRAILING_PROFIT = True
ENABLE_DYNAMIC_TRAILING_PROFIT = True   # True για δυναμικό trailing profit, False για στατικό
STATIC_TRAILING_PROFIT_THRESHOLD = 0.01 # 1% στατικό trailing profit
ENABLE_ADDITIONAL_CHECKS = False  # Αλλαγή σε False αν θέλεις να απενεργοποιήσεις τους πρόσθετους ελέγχους
EXTRA_PROFIT_MARGIN = 20  # Μεταβλητή για μαξιλαράκι ζημίας για trailing profit

DAILY_PROFIT_TARGET = 500
MAX_TRADES_PER_DAY = 100  # Μέγιστος αριθμός συναλλαγών ανά ημέρα

# 7. Μεταβλητές βραδυνού reset
MINIMUM_PROFIT_THRESHOLD = 15
FEES_PERCENTAGE = 0.0025  # Εκτιμώμενο ποσοστό fees (0.25%)
COOLDOWN_DURATION = 3600  # Χρόνος σε δευτερόλεπτα πριν το re-buy

# Στατική μεταβλητή για έλεγχο πώλησης όταν το trailing profit είναι ενεργό
SELL_ON_TRAILING = False  # ή False ανάλογα με την επιθυμητή συμπεριφορά


# 8. Παράμετροι Αποστολής E-mail
ENABLE_EMAIL_NOTIFICATIONS = True
ENABLE_PUSH_NOTIFICATIONS = True

# 9. MOCK DATA - Στατική μεταβλητή για ενεργοποίηση του demo mode
ENABLE_DEMO_MODE = False  # Ορισμός σε True για demo mode, False για live mode


# 10. DOLLAR COST AVERAGE STRATEGY
MAX_DROP_PERCENTAGE = 0.05       # 5% price drop
ENABLE_DYNAMIC_MAX_DROP_PERCENTAGE = True   ## Δυναμικό κατώφλι buy back αγοράς σε πτώση
ATR_FACTOR = 5  # Ευαισθησία στη μεταβλητότητα (ATR)
ADX_THRESHOLD = 20  # Όριο ADX για ισχυρή τάση                                         

TRAILING_PROFIT_SECOND_PERCENTAGE = 0.005   # 0.5% (προσαρμόστε το αν χρειάζεται)
TRAILING_PROFIT_THIRD_PERCENTAGE = 0.005

# 11. Λειτουργία Γραφήματος και back testing
ENABLE_SAVE_TO_CSV = False


# 12. Debugging 
ENABLE_FULL_RESPONSE_DATA = False   # Full API Response για συνάρτηση fetch_data()
LEVEL_LOGGING = "INFO"              # Μεταβλητή με επίπεδο καταγραφής



###################################################################################################################################################################################################################################

# Αρχικοποίηση μεταβλητών
start_bot = True

daily_profit = 0
current_trades = 0
active_trade = None
highest_price = 0
trailing_profit_active = False


# Βασική διαδρομή του έργου
if os.name == 'nt':  # Windows
    BASE_DIR = os.getenv('BASE_DIR', r'Z:\bots\scalping-bot')
else:  # Όλα τα υπόλοιπα λειτουργικά συστήματα (Linux, macOS)
    BASE_DIR = os.getenv('BASE_DIR', '/opt/python/scalping-bot')


# Decimal Configuration for each bot
decimal_config_path = f"{BASE_DIR}/decimal_config.json"


# Διαδρομή για αρχείο Lock
LOCK_FILE_PATH = f"{BASE_DIR}/"


# Διαδρομή για το αρχείο βαρύτητας
weights_file = f"{BASE_DIR}/indicator_weights.json"


# Api Keys file path
json_path = f"{BASE_DIR}/api_keys.json"


# Logs file path
logs_file_path = f"{BASE_DIR}/{CRYPTO_FULLNAME}/{CRYPTO_NAME}_bot.log"


# Διαδρομή για το cooldownfile
cooldown_file = f"{BASE_DIR}/{CRYPTO_FULLNAME}/cooldown_state.json"


# Διαδρομή για το state file
state_file = f"{BASE_DIR}/{CRYPTO_FULLNAME}/state.json"


# Διαδρομή για το pause flag
pause_file = f"{BASE_DIR}/{CRYPTO_FULLNAME}/pause.flag"


# Διαδρομή για το αρχείο .csv
csv_file_path = f"{BASE_DIR}/{CRYPTO_FULLNAME}/crypto_scores.csv"





# Load decimal configuration from external JSON file
with open(decimal_config_path, "r") as f:
    DECIMAL_CONFIG = json.load(f)

# Get decimals for the current cryptocurrency
if CRYPTO_NAME not in DECIMAL_CONFIG:
    logging.warning(f"Crypto name '{CRYPTO_NAME}' not found in decimal_config.json. Using default decimals: 2")
current_decimals = DECIMAL_CONFIG.get(CRYPTO_NAME, {}).get("decimals", 2)  # Default to 2 decimals



# Convert the string to a logging level
logging_level = getattr(logging, LEVEL_LOGGING.upper(), logging.INFO)


# Configure logging to both file and console
logging.basicConfig(
    level=logging_level,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(logs_file_path),  # Log to file
        logging.StreamHandler(),  # Log to console
    ],
)




# Function to load keys from the JSON file
def load_keys():
    try:
        with open(json_path, "r") as file:
            keys = json.load(file)
            # Βασικά κλειδιά
            key_name = keys.get("key_name")
            key_secret = keys.get("key_secret")
            SENDGRID_API_KEY = keys.get("SENDGRID_API_KEY")
            PUSHOVER_TOKEN = keys.get("PUSHOVER_TOKEN")
            PUSHOVER_USER = keys.get("PUSHOVER_USER")
            # Νέες μεταβλητές
            portfolio_uuid = keys.get("portfolio_uuid")
            EMAIL_SENDER = keys.get("EMAIL_SENDER")
            EMAIL_RECIPIENT = keys.get("EMAIL_RECIPIENT")

            # Έλεγχος αν λείπουν υποχρεωτικές μεταβλητές
            if not all([key_name, key_secret, SENDGRID_API_KEY, PUSHOVER_TOKEN, PUSHOVER_USER]):
                raise ValueError("One or more required keys are missing in the JSON file.")
            if not all([portfolio_uuid, EMAIL_SENDER, EMAIL_RECIPIENT]):
                raise ValueError("Portfolio UUID, Email Sender, or Email Recipient is missing in the JSON file.")

            return key_name, key_secret, SENDGRID_API_KEY, PUSHOVER_TOKEN, PUSHOVER_USER, portfolio_uuid, EMAIL_SENDER, EMAIL_RECIPIENT
    except FileNotFoundError:
        raise FileNotFoundError(f"The specified JSON file '{json_path}' was not found.")
    except json.JSONDecodeError:
        raise ValueError(f"The JSON file '{json_path}' is not properly formatted.")







# Συνάρτηση για να φορτώσει τους δείκτες βαρύτητας απο εξωτερικό αρχείο
def load_weights(crypto_symbol):
    # Έλεγχος αν το αρχείο υπάρχει
    if not os.path.exists(weights_file):
        logging.info(f"The weights file was not found at the specified path: {weights_file}")
        return None

    # Ανάγνωση του αρχείου JSON από το καθορισμένο path
    with open(weights_file, "r") as file:
        weights_data = json.load(file)

    # Επιστροφή των βαρύτητων για το συγκεκριμένο νόμισμα
    return weights_data.get(crypto_symbol, None)




# Έλεγχος για την ύπαρξη του flag
if os.path.exists(pause_file):
    print("Script paused due to reset process.")
    sys.exit()



# Φόρτωση όλων των μεταβλητών από το JSON αρχείο
key_name, key_secret, SENDGRID_API_KEY, PUSHOVER_TOKEN, PUSHOVER_USER, portfolio_uuid, EMAIL_SENDER, EMAIL_RECIPIENT = load_keys()






###############################################################################################################################

# Συνάρτηση που διαβάζει την απόφαση απο το failover-decision-bot
def load_decision():
    try:
        with open("/opt/python/failover-decision-bot/failover_result.json", "r") as f:
            decision_data = json.load(f)
            return decision_data.get("decision")
    except (FileNotFoundError, json.JSONDecodeError):
        logging.error("Failed to load decision from JSON file.")
        return "hold"  # Default to "hold" if there's an error




def is_bot_running():
    """Checks if the bot is already running by looking for the lock file."""
    return os.path.exists(LOCK_FILE_PATH)

def create_lock_file():
    """Creates a lock file to indicate the bot is running."""
    with open(LOCK_FILE_PATH, 'w') as f:
        f.write("Running")

def remove_lock_file():
    """Removes the lock file to indicate the bot has stopped."""
    if os.path.exists(LOCK_FILE_PATH):
        os.remove(LOCK_FILE_PATH)
        
        

###############################################################################################################################  














def check_sell_signal():
    # Define the path to the `sell_signal.txt` file for this specific bot
    signal_file = os.path.join(os.getcwd(), f"/opt/python/scalping-bot/{CRYPTO_FULLNAME}/sell_signal.txt")
    
    # Check if the `sell_signal.txt` file exists
    if os.path.exists(signal_file):
        sell_open_position()  # Execute the sale
        os.remove(signal_file)  # Delete the file after execution
        logging.info("Sell signal executed and `sell_signal.txt` file deleted.")
        return True  # Return True to stop the bot execution for this round
    else:
        logging.info("No external sell signal found.")
        return False  # Return False if no sell signal is found





def check_buy_signal():
    """
    Ελέγχει αν υπάρχει σήμα αγοράς και το εκτελεί αν βρεθεί το αρχείο `buy_signal.txt`.
    """
    # Define the path to the `buy_signal.txt` file for this specific bot
    signal_file = os.path.join(os.getcwd(), f"/opt/python/scalping-bot/{CRYPTO_FULLNAME}/buy_signal.txt")

    # Check if the `buy_signal.txt` file exists
    if os.path.exists(signal_file):
        success, message = buy_open_position()  # Execute the buy

        if success:
            os.remove(signal_file)  # Delete the file after successful execution
            logging.info(f"Buy signal executed successfully: {message}. `buy_signal.txt` file deleted.")
            return True  # Return True to stop the bot execution for this round
        else:
            logging.error(f"Buy signal execution failed: {message}. `buy_signal.txt` file remains.")
            return True  # Return True to stop the bot execution for this round

    else:
        logging.info("No external buy signal found.")
        return False  # Return False if no buy signal is found




def check_sell_all_signal():
    # Ορισμός του μονοπατιού για το αρχείο `sell_all_signal.txt` για αυτό το bot
    signal_file = os.path.join(os.getcwd(), f"/opt/python/scalping-bot/{CRYPTO_FULLNAME}/sell_all_signal.txt")
    
    # Έλεγχος αν υπάρχει το αρχείο `sell_all_signal.txt`
    if os.path.exists(signal_file):
        sell_all_positions()  # Εκτέλεση πώλησης όλων των θέσεων
        os.remove(signal_file)  # Διαγραφή του αρχείου μετά την εκτέλεση
        logging.info("Sell all signal executed and `sell_all_signal.txt` file deleted.")
        return True  # Επιστρέφει True για να σταματήσει η εκτέλεση του bot για αυτόν τον κύκλο
    else:
        logging.info("No external sell all signal found.")
        return False  # Επιστρέφει False αν δεν βρεθεί το αρχείο







# Ειδοποίηση μέσω Pushover
def send_push_notification(message, Logfile=True):
    """
    Στέλνει push notification μέσω Pushover.
    
    Args:
        message (str): Το μήνυμα που θα σταλεί.
        Logfile (bool): Αν είναι True, εμφανίζει τα logs. Αν είναι False, δεν εμφανίζει τίποτα.
    """
    # Έλεγχος αν η αποστολή push notifications είναι ενεργοποιημένη
    if not ENABLE_PUSH_NOTIFICATIONS:
        if Logfile:
            logging.info("Push notifications are paused. Notification was not sent.")
        return  # Επιστροφή χωρίς να σταλεί push notification
    
    try:
        # Αποστολή push notification μέσω Pushover
        po = pushover.Client(user_key=PUSHOVER_USER, api_token=PUSHOVER_TOKEN)
        po.send_message(message, title="Scalping Alert")
        
        if Logfile:
            logging.info("Push notification sent successfully!")
    except Exception as e:
        if Logfile:
            logging.error(f"Error sending Push notification: {e}")




# Συνάρτηση για την αποστολή email
def sendgrid_email(quantity, transaction_type, price, net_profit, final_score, reasoning):   
    # Έλεγχος αν η αποστολή email είναι ενεργοποιημένη
    if not ENABLE_EMAIL_NOTIFICATIONS:
        logging.info("Email sending is paused. Email was not sent.")
        return  # Επιστροφή χωρίς να σταλεί email
    
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
        Βαθμολογία: {final_score}<br>
        Αιτιολόγηση: {reasoning}<br>
    """
    
    # Προσθήκη του Net Profit μόνο αν το transaction δεν είναι 'buy'
    if transaction_type == 'sell':
        html_content += f"Net Profit: {round(net_profit, 2)} €<br>"
    
    # Έλεγχος αν η μεταβλητή ENABLE_DEMO_MODE είναι True για προσθήκη του loud out box
    if ENABLE_DEMO_MODE:
        html_content += """
            <div style="border: 2px solid red; padding: 10px; margin-top: 20px;">
                <strong>DEMO MODE:</strong> Αυτή είναι μια προσομοίωση. Καμία πραγματική συναλλαγή δεν έχει εκτελεστεί.
            </div>
        """

    message = Mail(
        from_email=EMAIL_SENDER,
        to_emails=EMAIL_RECIPIENT,
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






# Load the state from the file
def load_state():
    global daily_profit, total_profit, current_trades, active_trade, trade_amount, highest_price, trailing_profit_active, start_bot, score_history
    global second_trade_price, second_trade_amount, average_trade_price  # Νέες μεταβλητές
    global highest_price_second_position, trailing_profit_second_position_active  # Νέες μεταβλητές για τη δεύτερη θέση
    global third_trade_price, third_trade_amount, highest_price_third_position, trailing_profit_third_position_active  # Μεταβλητές για την τρίτη θέση
    global manual_second_buy, manual_third_buy  # Νέες μεταβλητές

    try:
        with open(state_file, "r") as f:
            state = json.load(f)
            daily_profit = state.get("daily_profit", 0)
            total_profit = state.get("total_profit", 0)
            current_trades = state.get("current_trades", 0)
            active_trade = state.get("active_trade", None)
            trade_amount = state.get("trade_amount", 0)
            highest_price = state.get("highest_price", None)
            trailing_profit_active = state.get("trailing_profit_active", False)
            start_bot = state.get("start_bot", True)  # Load the start_bot status
            score_history = state.get("score_history", [])  # Load the score history
            
            # Φόρτωση μεταβλητών για τη δεύτερη θέση
            second_trade_price = state.get("second_trade_price", None)
            second_trade_amount = state.get("second_trade_amount", 0)
            average_trade_price = state.get("average_trade_price", None)
            highest_price_second_position = state.get("highest_price_second_position", None)
            trailing_profit_second_position_active = state.get("trailing_profit_second_position_active", False)

            # Φόρτωση μεταβλητών για την τρίτη θέση
            third_trade_price = state.get("third_trade_price", None)
            third_trade_amount = state.get("third_trade_amount", 0)
            highest_price_third_position = state.get("highest_price_third_position", None)
            trailing_profit_third_position_active = state.get("trailing_profit_third_position_active", False)
            
            # Νέες μεταβλητές
            manual_second_buy = state.get("manual_second_buy", False)
            manual_third_buy = state.get("manual_third_buy", False)
            

            logging.info(
                f"Loaded state 1/3: daily_profit={daily_profit:.2f}, total_profit={total_profit:.2f}, "
                f"active_trade={active_trade:.{current_decimals}f}, trade_amount={trade_amount}"
            )
            logging.info(
                f"Loaded state 2/3: current_trades={current_trades}, highest_price={highest_price:.{current_decimals}f}, "
                f"trailing_active={trailing_profit_active}, start_bot={start_bot}, score_history={score_history}, manual_second_buy={manual_second_buy}, manual_third_buy={manual_third_buy}"
            )
            logging.info(
                f"Loaded state 3/3: second_trade_price={second_trade_price}, second_trade_amount={second_trade_amount}, "
                f"average_trade_price={average_trade_price}, highest_price_second_position={highest_price_second_position}, "
                f"trailing_profit_second_position_active={trailing_profit_second_position_active}"
            )
            logging.info(
                f"Loaded state 4/4: third_trade_price={third_trade_price}, third_trade_amount={third_trade_amount}, "
                f"highest_price_third_position={highest_price_third_position}, "
                f"trailing_profit_third_position_active={trailing_profit_third_position_active}"
            )

    except FileNotFoundError:
        
        # Initialize defaults if state file is not found
        daily_profit = 0
        total_profit = 0
        current_trades = 0
        active_trade = None
        trade_amount = 0
        highest_price = None
        trailing_profit_active = False
        start_bot = True  # Default to True if no state file
        score_history = []  # Initialize score history as an empty list

        # Αρχικοποίηση μεταβλητών για τη δεύτερη θέση
        second_trade_price = None
        second_trade_amount = 0
        average_trade_price = None
        highest_price_second_position = None
        trailing_profit_second_position_active = False

        # Αρχικοποίηση μεταβλητών για την τρίτη θέση
        third_trade_price = None
        third_trade_amount = 0
        highest_price_third_position = None
        trailing_profit_third_position_active = False
        
        # Default value for new variables
        manual_second_buy = False        
        manual_third_buy = False

        save_state()  # Create the state file
        logging.info(
            f"State file not found. Initialized new state: daily_profit={daily_profit}, total_profit={total_profit}, "
            f"current_trades={current_trades}, active_trade={active_trade}, trade_amount={trade_amount}, "
            f"highest_price={highest_price}, trailing_profit_active={trailing_profit_active}, start_bot={start_bot}, manual_second_buy={manual_second_buy}, manual_third_buy={manual_third_buy}, "
            f"score_history={score_history}, second_trade_price={second_trade_price}, second_trade_amount={second_trade_amount}, "
            f"average_trade_price={average_trade_price}, highest_price_second_position={highest_price_second_position}, "
            f"trailing_profit_second_position_active={trailing_profit_second_position_active}, "
            f"third_trade_price={third_trade_price}, third_trade_amount={third_trade_amount}, "
            f"highest_price_third_position={highest_price_third_position}, "
            f"trailing_profit_third_position_active={trailing_profit_third_position_active}"
        )
        

# Save the state to the file
def save_state(log_info=True):  # Προσθέτουμε το όρισμα log_info
    state = {
        "daily_profit": round(daily_profit, 2) if daily_profit is not None else 0,
        "total_profit": round(total_profit, 2) if total_profit is not None else 0,
        "current_trades": current_trades,
        "active_trade": round(active_trade, current_decimals) if active_trade is not None else 0,
        "trade_amount": trade_amount,
        "highest_price": round(highest_price, current_decimals) if highest_price is not None else 0,
        "trailing_profit_active": trailing_profit_active,
        "start_bot": start_bot,  # Save the start_bot status
        "score_history": [round(score, 2) for score in score_history],  # Round each score in score_history

        # Μεταβλητές για τη δεύτερη θέση
        "second_trade_price": round(second_trade_price, current_decimals) if second_trade_price is not None else 0,
        "second_trade_amount": second_trade_amount,
        "average_trade_price": round(average_trade_price, current_decimals) if average_trade_price is not None else 0,
        "highest_price_second_position": round(highest_price_second_position, current_decimals) if highest_price_second_position is not None else 0,
        "trailing_profit_second_position_active": trailing_profit_second_position_active,

        # Μεταβλητές για την τρίτη θέση
        "third_trade_price": round(third_trade_price, current_decimals) if third_trade_price is not None else 0,
        "third_trade_amount": third_trade_amount,
        "highest_price_third_position": round(highest_price_third_position, current_decimals) if highest_price_third_position is not None else 0,
        "trailing_profit_third_position_active": trailing_profit_third_position_active,
        
        # Νέα μεταβλητή για χειροκίνητη αγορά δεύτερης θέσης
        "manual_second_buy": manual_second_buy,
        "manual_third_buy": manual_third_buy
        
    }

    # Save state to a file
    with open(state_file, "w") as f:
        json.dump(state, f)

    # Log the saved state dynamically with decimals if log_info is True
    if log_info:
        logging.info(
            f"Saved state: daily_profit={state['daily_profit']:.2f}, total_profit={state['total_profit']:.2f}, "
            f"current_trades={current_trades}, active_trade={state['active_trade']:.{current_decimals}f}, trade_amount={trade_amount}, "
            f"highest_price={state['highest_price']:.{current_decimals}f}, trailing_profit_active={trailing_profit_active}, start_bot={start_bot}, "
            f"score_history={[round(score, 2) for score in score_history]}, "
            f"second_trade_price={state['second_trade_price']:.{current_decimals}f}, second_trade_amount={second_trade_amount}, "
            f"average_trade_price={state['average_trade_price']:.{current_decimals}f}, highest_price_second_position={state['highest_price_second_position']:.{current_decimals}f}, "
            f"trailing_profit_second_position_active={state['trailing_profit_second_position_active']}, "
            f"third_trade_price={state['third_trade_price']:.{current_decimals}f}, third_trade_amount={third_trade_amount}, "
            f"highest_price_third_position={state['highest_price_third_position']:.{current_decimals}f}, "
            f"trailing_profit_third_position_active={state['trailing_profit_third_position_active']}, "
            f"manual_second_buy={state['manual_second_buy']}, manual_third_buy={state['manual_third_buy']}"
        )
        




# Συνάρτηση που αποθηκεύει τον χρόνο τελευταίου reset στο αρχείο cooldown
def save_cooldown_state(custom_duration=None):
    cooldown_time = time.time() if not custom_duration else time.time() - (COOLDOWN_DURATION - custom_duration)
    with open(cooldown_file, 'w') as f:
        json.dump({"last_reset_time": cooldown_time}, f)



# Συνάρτηση που φορτώνει τον χρόνο τελευταίου reset από το αρχείο
def load_cooldown_state():
    if os.path.exists(cooldown_file):
        with open(cooldown_file, 'r') as f:
            data = json.load(f)
        return data.get("last_reset_time", 0)
    return 0


# Συνάρτηση που ελέγχει αν έχει λήξει το cooldown και επιστρέφει τον υπόλοιπο χρόνο
def check_cooldown():    
    last_reset_time = load_cooldown_state()
    current_time = time.time()
    remaining_time = COOLDOWN_DURATION - (current_time - last_reset_time)
    return remaining_time <= 0, max(0, int(remaining_time))








def save_to_csv(csv_file_path, CRYPTO_NAME, current_price, score, scores):
    """
    Αποθηκεύει δεδομένα σε αρχείο CSV, προσθέτοντας μια νέα γραμμή κάθε φορά.

    Args:
        csv_file_path (str): Το όνομα ή η διαδρομή του αρχείου CSV.
        CRYPTO_NAME (str): Το όνομα του crypto/bot.
        current_price (float): Η τρέχουσα τιμή.
        score (float): Η συνολική βαθμολογία.
        scores (dict): Οι βαθμολογίες των τεχνικών δεικτών.

    Returns:
        None
    """
    
    # Στρογγυλοποίηση του score στα 2 δεκαδικά ψηφία
    score = round(score, 2)    
    
    
    # Δημιουργία της νέας εγγραφής
    new_entry = {
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "bot_name": CRYPTO_NAME,
        "macd_score": scores.get("macd", 0),
        "rsi_score": scores.get("rsi", 0),
        "bollinger_score": scores.get("bollinger", 0),
        "vwap_score": scores.get("vwap", 0),
        "current_price": current_price,
        "score": score
    }

    # Έλεγχος αν υπάρχει το αρχείο
    file_exists = os.path.exists(csv_file_path)

    # Γράψιμο της εγγραφής
    with open(csv_file_path, mode="a", newline='', encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=new_entry.keys())
        
        # Αν το αρχείο δεν υπάρχει, γράφουμε κεφαλίδες
        if not file_exists:
            writer.writeheader()
        
        # Προσθήκη της νέας γραμμής
        writer.writerow(new_entry)

    # Καταγραφή της επιτυχούς αποθήκευσης
    logging.info(f"File {csv_file_path} found. Appending new data.")





# Συνάρτηση για πώληση όλων των ανοιχτών θέσεων απο macro excel
def sell_all_positions():
    global active_trade, trade_amount, second_trade_price, second_trade_amount
    global third_trade_price, third_trade_amount, daily_profit, current_trades
    global highest_price, highest_price_second_position, highest_price_third_position
    global trailing_profit_active, trailing_profit_second_position_active, trailing_profit_third_position_active
    
    logging.info("Sell All Positions was executed through macro call.")
    
    load_state()
    
    current_price = get_crypto_price()
    if current_price is None:
        logging.error("Failed to fetch current price. Skipping trade execution.")
        return
    
    # Υπολογισμός συνολικής ποσότητας προς πώληση
    total_amount_to_sell = trade_amount + second_trade_amount + third_trade_amount

    if total_amount_to_sell == 0:
        logging.info("No active positions to sell. Skipping execution.")
        return

    # Υπολογισμός καθαρών κερδών για όλες τις θέσεις
    potential_profit = (current_price - active_trade) * trade_amount if active_trade else 0
    potential_profit += (current_price - second_trade_price) * second_trade_amount if second_trade_price else 0
    potential_profit += (current_price - third_trade_price) * third_trade_amount if third_trade_price else 0

    # Εκτίμηση των fees για τη συναλλαγή
    estimated_fees = current_price * total_amount_to_sell * FEES_PERCENTAGE
    logging.info(f"Estimated fees for the trade: {estimated_fees:.{current_decimals}f}")

    # Υπολογισμός καθαρού κέρδους μετά την αφαίρεση των fees
    net_profit = potential_profit - estimated_fees

    # Εκτέλεση της εντολής πώλησης
    order_successful, execution_price, fees = place_order("sell", total_amount_to_sell, current_price)
    if order_successful and execution_price:
        logging.info(f"Sold total {total_amount_to_sell} of {CRYPTO_NAME} at {execution_price:.{current_decimals}f} "
                     f"with net profit: {net_profit:.{current_decimals}f}")
        
        # Ανανεώνουμε το κέρδος με το κέρδος της συναλλαγής
        daily_profit += net_profit
        
        sendgrid_email(total_amount_to_sell, "sell", execution_price, net_profit, "N/A", "Macro Call")

        # Reset όλων των μεταβλητών στο state.json μόνο αν εκτελέστηκε η πώληση
        current_trades += 1
        active_trade = None
        trade_amount = 0
        second_trade_price = None
        second_trade_amount = 0
        third_trade_price = None
        third_trade_amount = 0
        highest_price = None
        highest_price_second_position = None
        highest_price_third_position = None
        trailing_profit_active = False
        trailing_profit_second_position_active = False
        trailing_profit_third_position_active = False

        # Αποθήκευση του χρόνου τελευταίου reset για να ενεργοποιηθεί το cooldown
        save_state()
        save_cooldown_state(custom_duration=2700)  # macro call 45 minutes

    else:
        logging.info(f"Failed to execute sell all order at {current_price}. No state reset performed.")



# Συνάρτηση για πώληση της θέσης απο macro excel
def sell_open_position():
    global active_trade, trade_amount, daily_profit, current_trades, highest_price, trailing_profit_active
    logging.info("Immediate Sell was executed through macro call.")
    
    load_state()
    
    current_price = get_crypto_price()
    if current_price is None:
        logging.error("Failed to fetch current price. Skipping trade execution.")
        return
    
    # Υπολογισμός κέρδους πριν αφαιρεθούν τα fees
    potential_profit = (current_price - active_trade) * trade_amount

    # Εκτίμηση των fees για τη συναλλαγή
    estimated_fees = current_price * trade_amount * FEES_PERCENTAGE
    logging.info(f"Estimated fees for the trade: {estimated_fees:.{current_decimals}f}")

    # Υπολογισμός καθαρού κέρδους μετά την αφαίρεση των εκτιμώμενων fees
    net_profit = potential_profit - estimated_fees    

    order_successful, execution_price, fees = place_order("sell", trade_amount, current_price)
    if order_successful and execution_price:              
        logging.info(f"Sold {trade_amount} of {CRYPTO_NAME} at {execution_price:.{current_decimals}f} with net profit: {net_profit:.{current_decimals}f}")
                           
        # Ανανεώνουμε το κέρδος με το κέρδος της συναλλαγής
        daily_profit += net_profit
        
        sendgrid_email(trade_amount, "sell", execution_price, net_profit, "N/A", "Macro Call")

        # Reset των μεταβλητών στο state.json μόνο αν εκτελέστηκε η πώληση
        current_trades += 1
        active_trade = None
        trade_amount = 0
        highest_price = None
        trailing_profit_active = False

        # Αποθήκευση του χρόνου τελευταίου reset για να ενεργοποιηθεί το cooldown
        save_state()

        # Χρονική αναμονή μετά την πώληση για αποφυγή άμεσης αγοράς
        save_cooldown_state(custom_duration=2700)       # macro call 45 minutes  

    else:
        logging.info(f"Failed to execute sell order at {current_price}. No state reset performed.")




def buy_open_position():
    """
    Εκτελεί αγορά με βάση τη στατική ποσότητα TRADE_AMOUNT.
    """
    global active_trade, trade_amount, daily_profit, current_trades, highest_price, trailing_profit_active, TRADE_AMOUNT
    logging.info("Immediate Buy was executed through macro call.")

    load_state()

    current_price = get_crypto_price()
    if current_price is None:
        logging.error("Failed to fetch current price. Skipping trade execution.")
        return

    # Λήψη διαθέσιμου υπολοίπου
    portfolio_summary = get_portfolio_balance(portfolio_uuid)
    
    if "error" not in portfolio_summary:
        available_cash = portfolio_summary['total_cash_equivalent_balance']
        
        # Υπολογισμός ποσού που απαιτείται για την αγορά
        amount_needed_to_buy = TRADE_AMOUNT * current_price
        logging.info(f"Available cash in portfolio: {available_cash:.2f} EUR, Amount needed: {amount_needed_to_buy:.2f} EUR ")

        if amount_needed_to_buy <= available_cash:
            logging.info(f"Sufficient funds available ({available_cash:.2f} EUR). Executing Buy Order.")
            

            # Εκτίμηση των fees για τη συναλλαγή
            estimated_fees = current_price * TRADE_AMOUNT * FEES_PERCENTAGE
            logging.info(f"Estimated fees for the trade: {estimated_fees:.{current_decimals}f}")

            # Εκτέλεση της αγοράς
            order_successful, execution_price, fees = place_order("buy", TRADE_AMOUNT, current_price)
            
            if order_successful and execution_price:
                logging.info(f"Bought {TRADE_AMOUNT} of {CRYPTO_NAME} at {execution_price:.{current_decimals}f}.")

                # Ενημέρωση των μεταβλητών μετά την αγορά
                active_trade = execution_price
                trade_amount = TRADE_AMOUNT
                daily_profit -= fees
                highest_price = execution_price  # Ενημέρωση για trailing profit logic
                current_trades += 1

                sendgrid_email(TRADE_AMOUNT, "buy", execution_price, "N/A", "N/A", "Macro Call")

                # Χρονική αναμονή μετά την αγορά για αποφυγή άμεσης πώλησης
                save_cooldown_state(custom_duration=2700)  # macro call 45 minutes
                
                # Αποθήκευση της κατάστασης
                save_state()
                
                return True, "Order placed successfully."

        else:
            logging.warning(f"Insufficient funds. Needed: {amount_needed_to_buy:.2f} EUR, Available: {available_cash:.2f} EUR")
            send_push_notification(
                f"ALERT: Insufficient funds for {CRYPTO_NAME} bot. Needed: {amount_needed_to_buy:.2f} EUR, Available: {available_cash:.2f} EUR. This alert originates from the macro buy definition. Please ensure sufficient funds as this message will appear every 2 minutes.",
                Logfile=False
            )
            return False, "Insufficient funds."
            
    else:
        logging.error(f"Failed to retrieve portfolio balance. No buy action taken.")
        logging.error(f"Error details: {portfolio_summary['message']}")
        return False, "Portfolio balance retrieval failed."




def reset_bot_state():
    global daily_profit, total_profit, current_trades, active_trade, trade_amount, highest_price, trailing_profit_active, score_history

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

            # Έλεγχος για το αν πρέπει να εκτελεστεί πώληση
            if SELL_ON_TRAILING or (not SELL_ON_TRAILING and not trailing_profit_active):
                current_price = get_crypto_price()
                if current_price is None:
                    logging.error("Failed to fetch current price. Skipping trade execution.")
                    return

                # Υπολογισμός κέρδους πριν αφαιρεθούν τα fees
                potential_profit = (current_price - active_trade) * trade_amount

                # Εκτίμηση των fees για τη συναλλαγή
                estimated_fees = current_price * trade_amount * FEES_PERCENTAGE
                logging.info(f"Estimated fees for the trade: {estimated_fees:.{current_decimals}f}")

                # Υπολογισμός καθαρού κέρδους μετά την αφαίρεση των εκτιμώμενων fees
                net_profit = potential_profit - estimated_fees

                # Πώληση μόνο αν το κέρδος μετά την αφαίρεση των εκτιμώμενων fees υπερβαίνει το κατώφλι
                if current_price > active_trade and net_profit >= MINIMUM_PROFIT_THRESHOLD:
                    order_successful, execution_price, fees = place_order("sell", trade_amount, current_price)
                    
                    if order_successful and execution_price:              
                        logging.info(f"Sold {trade_amount} of {CRYPTO_NAME} at {execution_price:.{current_decimals}f} with net profit: {net_profit:.{current_decimals}f}")
                                           
                        # Ανανεώνουμε το συνολικό κέρδος με το τρέχον ημερήσιο κέρδος πριν το reset
                        total_profit += net_profit + daily_profit
                        
                        sendgrid_email(trade_amount, "sell", execution_price, net_profit, "N/A", "Night Reset")

                        # Reset των μεταβλητών στο state.json μόνο αν εκτελέστηκε η πώληση
                        daily_profit = 0
                        current_trades = 0
                        active_trade = None
                        trade_amount = 0
                        highest_price = None
                        trailing_profit_active = False
                        score_history = []  # Reset του score_history

                        # Αποθήκευση του χρόνου τελευταίου reset για να ενεργοποιηθεί το cooldown
                        save_state()
                        
                        # Χρονική αναμονή μετά την πώληση για αποφυγή άμεσης αγοράς
                        save_cooldown_state(custom_duration=3600)       #night reset - 1 hour
                        logging.info("Cooldown initiated to prevent immediate re-buy.")

                        logging.info("Bot state reset completed.")
                    else:
                        logging.info(f"Failed to execute sell order at {current_price}. No state reset performed.")
                else:
                    logging.info(f"No sale executed. Current price {current_price} is not higher than the active trade price {active_trade} or net profit {net_profit:.{current_decimals}f} is below threshold {MINIMUM_PROFIT_THRESHOLD}.")
                    logging.info("Conditions not met for sale. Proceeding with zeroing of trades and daily reset.")
                                       
                    # Ανανεώνουμε το συνολικό κέρδος με το τρέχον ημερήσιο κέρδος πριν το reset
                    total_profit += daily_profit
                    
                    # Μηδενισμός των μεταβλητών παρά το ότι δεν έγινε πώληση                    
                    daily_profit = 0
                    current_trades = 0
                    score_history = []  # Reset του score_history
                    
                    # Αποθήκευση της κατάστασης                    
                    save_state()
                    logging.info("Zeroing of trades and daily reset completed successfully.")
                    
                    
            else:
                logging.info("Trailing profit is active; no sale executed due to SELL_ON_TRAILING setting.")

                # Ανανεώνουμε το συνολικό κέρδος με το τρέχον ημερήσιο κέρδος πριν το reset
                total_profit += daily_profit
                daily_profit = 0
                current_trades = 0
                score_history = []  # Reset του score_history
                
                # Αποθήκευση της νέας κατάστασης
                save_state()
                logging.info("Bot state reset completed.")

        else:
            logging.info(f"No active trade found. Resetting daily profit and current trades, updating total profit.")
            
            # Ανανεώνουμε το συνολικό κέρδος με το τρέχον ημερήσιο κέρδος πριν το reset
            total_profit += daily_profit
            daily_profit = 0
            current_trades = 0
            start_bot = True
            score_history = []  # Reset του score_history
            
            # Αποθήκευση της νέας κατάστασης
            save_state()
            logging.info("Bot state reset completed.")

    finally:
        # Διαγραφή του pause flag στο τέλος της διαδικασίας
        if os.path.exists(pause_file):
            os.remove(pause_file)
        logging.info("Pause flag removed. Resuming normal operation.")









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




# Συνάρτηση που ανακτά τις λεπτομέρειες της παραγγελίας
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

    
    attempt = 0  # Μετρητής προσπαθειών
    max_attempts = 3  # Μέγιστος αριθμός προσπαθειών

    while attempt < max_attempts:
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
                # Αν η απάντηση δεν είναι επιτυχής, λογότυπος σφάλματος
                logging.error(f"Failed to retrieve order details. Status: {response.status_code}, Data: {response.text}")

        except Exception as e:
            # Λογότυπος για σφάλμα που προκύπτει από την αίτηση
            logging.error(f"Error fetching order details: {e}")

        attempt += 1
        if attempt < max_attempts:
            # Καθυστέρηση πριν την επόμενη προσπάθεια
            time.sleep(5)

    # Αν αποτύχουν όλες οι προσπάθειες, επιστροφή λάθους
    logging.error(f"Failed to retrieve order details after {max_attempts} attempts. Status: {response.status_code}, Data: {response.text}")
    return {
        "error": response.status_code,
        "message": response.text
    }






def get_portfolio_balance(portfolio_uuid):
    """
    Επιστρέφει το όνομα του χαρτοφυλακίου και το συνολικό υπόλοιπο σε μετρητά από το Coinbase API.

    :param portfolio_uuid: Το μοναδικό ID του χαρτοφυλακίου.
    :return: Ένα λεξικό με το όνομα και το συνολικό υπόλοιπο σε μετρητά.
    """
    # Ρυθμίσεις για το API
    request_host = "api.coinbase.com"
    portfolio_details_path = f"/api/v3/brokerage/portfolios/{portfolio_uuid}"
    uri = f"GET {request_host}{portfolio_details_path}"

    # Δημιουργία JWT token
    jwt_token = build_jwt(uri)

    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
    }

    # Σύνδεση και αίτημα στο API
    conn = http.client.HTTPSConnection(request_host)

    try:
        conn.request("GET", portfolio_details_path, headers=headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")

        logging.debug(f"Response Status Code: {res.status}")
        logging.debug(f"Response Data: {data}")

        if res.status == 200:
            portfolio_details = json.loads(data)
            breakdown = portfolio_details.get("breakdown", {})
            portfolio_info = breakdown.get("portfolio", {})
            portfolio_balances = breakdown.get("portfolio_balances", {})
            
            # Εξαγωγή του ονόματος και του υπολοίπου
            portfolio_name = portfolio_info.get("name", "Unknown Portfolio")
            total_cash_balance = float(portfolio_balances.get("total_cash_equivalent_balance", {}).get("value", 0))

            return {
                "portfolio_name": portfolio_name,
                "total_cash_equivalent_balance": total_cash_balance
            }
        else:
            logging.error(f"Failed to retrieve portfolio balance. Status: {res.status}, Data: {data}")
            return {
                "error": res.status,
                "message": data
            }

    except Exception as e:
        logging.error(f"Error fetching portfolio balance: {e}")
        return {
            "error": "exception",
            "message": str(e)
        }
    finally:
        conn.close()










# Τοποθέτηση εντολών αγοράς/πώλησης με δυνατότητα demo mode
def place_order(side, size, price):
    global start_bot
    # Έλεγχος για demo mode
    if ENABLE_DEMO_MODE:
        # Mock response data για demo mode
        logging.info("Demo mode active: Using mock data instead of live order.")
        
        # Mock order_id, average_filled_price και fees
        mock_order_id = "demo_" + secrets.token_hex(5)
        mock_average_filled_price = price  # Τιμή εκτέλεσης παρόμοια με την τιμή παραγγελίας
        mock_total_fees = mock_average_filled_price * size * FEES_PERCENTAGE  # Παράδειγμα χρέωσης για mock data
        
        # Mock response as if order was placed and executed successfully
        logging.info(f"Mock order placed successfully with order_id: {mock_order_id}")
        logging.info(f"Order executed at mock price: {mock_average_filled_price:.{current_decimals}f}, mock fees: {mock_total_fees:.{current_decimals}f}")
        
        # Προσομοίωση καθυστέρησης για ομοιότητα με την πραγματική λειτουργία
        time.sleep(1)
        
        # Επιστροφή των mock τιμών
        return True, mock_average_filled_price, mock_total_fees


    # Αρχικός κώδικας της συνάρτησης place_order χωρίς αλλαγές
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
                        logging.info(f"Order executed at price: {average_filled_price:.{current_decimals}f} {CRYPTO_CURRENCY}, fees: {total_fees:.{current_decimals}f} {CRYPTO_CURRENCY}")
                        return True, average_filled_price, total_fees  # Επιστρέφουμε και τα fees
                    else:
                        # Fallback logic when no execution price is found
                        logging.warning("Order placed but no execution price found.")
                        
                        # Fallback: Treat the sale as successful using the provided price
                        logging.warning(f"Using fallback for order execution at price: {price}")
                        total_fees = price * size * FEES_PERCENTAGE
                                                
                        # Εξαγωγή των λεπτομερειών λάθους αν υπάρχει
                        error_details = response_data.get("message", response_data)
                        
                        # Αποστολή Push notification
                        send_push_notification(f"ALERT: Usign fallback for order execution  for {CRYPTO_NAME} bot. Details: {error_details}")
                        
                        return True, price, total_fees


                else:
                    logging.warning("Order placed but no order_id returned.")
                    return True, None, None
            else:
                # Εξαγωγή των λεπτομερειών λάθους αν υπάρχει
                error_message = response_data.get("error", "Unknown error")
                error_details = response_data.get("message", response_data)

                logging.error(
                    f"Failed to place order. Status: {res.status}, Error: {error_message}, Details: {error_details}"
                )
                
                # Send push notification
                send_push_notification(
                    f"ALERT: Failed to place order for {CRYPTO_NAME} bot.\nError Details:\n{error_details}",
                    Logfile=False
)
                
                # Διακοπή bot και αποθήκευση κατάστασης
                start_bot = False
                save_state()  # Εκτελείται πριν το return για να αποθηκευτεί η κατάσταση
                
                return False, None, None
        else:
            logging.error(f"HTTP error occurred. Status: {res.status}, Data: {data}")
            return False, None, None

    except Exception as e:
        logging.error(f"Error making request: {e}")
        return False, None, None
    finally:
        conn.close()



#--------------------------------------------------------------------------------------------------------------------------------------------
# ΥΠΟΛΟΓΙΣΜΟΣ ΤΕΧΝΙΚΏΝ ΔΕΙΚΤΩΝ

# Συνάρτηση για Υπολογισμό του Κινητού Μέσου Όρου (MA) με Δυνατότητα Resampling
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





# Συνάρτηση για Υπολογισμό του MACD (Moving Average Convergence Divergence) με Δυνατότητα Resampling
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




# Συνάρτηση για Υπολογισμό του Δείκτη Σχετικής Ισχύος (RSI) με Δυνατότητα Resampling
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




# Συνάρτηση για Υπολογισμό του Δείκτη Μέσης Κατευθυντικότητας (ADX) και του Μέσου Αληθινού Εύρους (ATR)
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



# Συνάρτηση για Υπολογισμό του Στοχαστικού Ταλαντωτή (Stochastic Oscillator)
def calculate_stochastic(df, k_period=14, d_period=3):
    df['low_k'] = df['low'].rolling(window=k_period).min()
    df['high_k'] = df['high'].rolling(window=k_period).max()
    
    df['%K'] = 100 * ((df['close'] - df['low_k']) / (df['high_k'] - df['low_k']))
    df['%D'] = df['%K'].rolling(window=d_period).mean()
    
    # Αφαιρούμε τις προσωρινές στήλες
    df.drop(['low_k', 'high_k'], axis=1, inplace=True)
    
    return df['%K'], df['%D']
    
    
    
def calculate_stochastic_rsi(df, period=14):
    """
    Υπολογίζει το Stochastic RSI για ένα DataFrame.
    
    Args:
        df: DataFrame με τιμές 'close'.
        period: Περίοδος για τον υπολογισμό (default 14).
    
    Returns:
        pd.Series: Τιμές του Stochastic RSI.
    """
    # Υπολογισμός RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rsi = 100 - (100 / (1 + gain / loss))
    
    # Υπολογισμός Stochastic RSI
    lowest_rsi = rsi.rolling(window=period).min()
    highest_rsi = rsi.rolling(window=period).max()
    stoch_rsi = (rsi - lowest_rsi) / (highest_rsi - lowest_rsi)
    
    return stoch_rsi
    



# Συνάρτηση για Έλεγχο Επιβεβαίωσης Όγκου μέσω Κινούμενου Μέσου Όρου
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

        logging.info(f"Latest volume: {current_volume}, MAV ({window} periods): {avg_volume:.{current_decimals}f}")
        #logging.info(f"Moving average volume ({window} periods): {avg_volume:.{current_decimals}f}")
        #logging.info(f"Volume confirmation: {'Yes' if volume_confirmation else 'No'}")

        return volume_confirmation, current_volume, avg_volume
    else:
        logging.info("There is not enough data to calculate the moving average volume.")
        return False, None, None



# Συνάρτηση για Υπολογισμό των Bollinger Bands
def calculate_bollinger_bands(df, period=20, num_std_dev=2):
    df['SMA'] = df['close'].rolling(window=period).mean()
    df['STD'] = df['close'].rolling(window=period).std()
    df['Bollinger_Upper'] = df['SMA'] + (df['STD'] * num_std_dev)
    df['Bollinger_Lower'] = df['SMA'] - (df['STD'] * num_std_dev)
    
    # Επιστρέφουμε τις στήλες με τις μπάντες
    return df['Bollinger_Upper'], df['Bollinger_Lower']



# Συνάρτηση για Υπολογισμό του Δείκτη VWAP (Volume Weighted Average Price)
def calculate_vwap(df):
    # Υπολογισμός του VWAP
    df['Typical_Price'] = (df['high'] + df['low'] + df['close']) / 3
    df['VWAP'] = (df['Typical_Price'] * df['volume']).cumsum() / df['volume'].cumsum()
    
    return df['VWAP']





# Συνάρτηση για Έλεγχο Επαρκών Δεδομένων για Υπολογισμό Τεχνικών Δεικτών
def calculate_indicators(df, source_url, short_ma_period, long_ma_period):
    # Έλεγχος αν υπάρχουν αρκετά δεδομένα για τον υπολογισμό των δεικτών
    if len(df) < max(short_ma_period, long_ma_period, 26):  # Μακρύτερη περίοδος για MACD είναι 26
        #logging.warning(f"Not enough data to calculate indicators from {source_url}. Data length: {len(df)}")
        return False  # Επιστρέφει False για να δηλώσει ότι δεν υπάρχουν αρκετά δεδομένα
    return True  # Επιστρέφει True αν υπάρχουν αρκετά δεδομένα





def fallback_conditions(df, atr_threshold=1.5, stochastic_threshold=20, stoch_rsi_threshold=0.2):
    """
    Συνδυαστική λογική για fallback συνθήκες: επιβεβαίωση τάσης, δυναμικής και μεταβλητότητας.
    
    Args:
        df: DataFrame με δεδομένα αγοράς (high, low, close).
        atr_threshold: Πολλαπλασιαστής για ATR (π.χ. 1.5 = αυξημένη μεταβλητότητα).
        stochastic_threshold: Κατώφλι για Stochastic (%K) (π.χ. κάτω από 20 = υπερπουλημένη αγορά).
        stoch_rsi_threshold: Κατώφλι για Stochastic RSI (π.χ. κάτω από 0.2 = υπερπουλημένο RSI).
    
    Returns:
        Boolean: True αν όλες οι συνδυαστικές συνθήκες πληρούνται (να προχωρήσει σε αγορά), αλλιώς False.
    """
    # Υπολογισμός δεικτών
    macd_signal, macd_histogram = calculate_macd(df)  # MACD
    _, atr = calculate_adx(df)  # ATR μέσω ADX υπολογισμού
    k_percent, _ = calculate_stochastic(df)  # Stochastic Oscillator
    stoch_rsi = calculate_stochastic_rsi(df)  # Stochastic RSI
    vwap = calculate_vwap(df)  # VWAP

    # Τρέχοντα δεδομένα
    current_atr = atr.iloc[-1]  # Τρέχον ATR
    mean_atr = atr.mean()  # Μέσο ATR
    current_k = k_percent.iloc[-1]  # Τρέχον %K
    current_stoch_rsi = stoch_rsi.iloc[-1]  # Τρέχον Stochastic RSI
    current_vwap = vwap.iloc[-1]  # Τρέχον VWAP
    current_price = df['close'].iloc[-1]  # Τρέχουσα τιμή

    # 1. Επιβεβαίωση Τάσης (Trend Condition)
    trend_condition = (current_price > current_vwap) and (macd_histogram.iloc[-1] > 0)

    # 2. Επιβεβαίωση Δυναμικής (Momentum Condition)
    momentum_condition = (current_k < stochastic_threshold) or (current_stoch_rsi < stoch_rsi_threshold)

    # 3. Επιβεβαίωση Μεταβλητότητας (Volatility Condition)
    volatility_condition = current_atr > (atr_threshold * mean_atr)

    # Logging για debugging
    logging.info(f"Trend Condition: Price > VWAP = {current_price > current_vwap}, MACD Histogram > 0 = {macd_histogram.iloc[-1] > 0}, Condition = {trend_condition}")
    logging.info(f"Momentum Condition: %K = {current_k:.2f}, StochRSI = {current_stoch_rsi:.2f}, Condition = {momentum_condition}")
    logging.info(f"Volatility Condition: Current ATR = {current_atr:.2f}, Mean ATR = {mean_atr:.2f}, Condition = {volatility_condition}")



    #---------------------------------------------------------------------------------------------
    #Χαλάρωση της λογικής (weighted):
    # # Τελική απόφαση (όλες οι συνθήκες πρέπει να πληρούνται)
    # if trend_condition and momentum_condition and volatility_condition:
        # return True
    # else:
        # return False
    #---------------------------------------------------------------------------------------------


    # Αντί για αυστηρό AND, χρησιμοποιούμε weighting:    
    
    # logging πριν την προσθεση
    logging.debug(f">>>> Trend Condition: {trend_condition}, Momentum Condition: {momentum_condition}, Volatility Condition: {volatility_condition}")

    total_conditions = int(trend_condition) + int(momentum_condition) + int(volatility_condition)
    
    # Logging πριν το IF και μετά την προσθεση
    logging.debug(f">>>> Total conditions calculated: {total_conditions}")
    
    if total_conditions >= 2:  # Πρέπει να πληρούνται τουλάχιστον 2 συνθήκες
        return True
    else:
        return False







# Ανάκτηση δεδομένων candlestick από 3 διαφορετικές διαδρομές με χρήση try-except
def fetch_data():
    logging.debug(f"Fetching data for {CRYPTO_SYMBOL} with granularity: {GRANULARITY}")

    urls = [
        f"https://api.coinbase.com/api/v3/brokerage/market/products/{CRYPTO_SYMBOL}/candles?granularity={GRANULARITY_TEXT}",
        f"https://api.exchange.coinbase.com/products/{CRYPTO_SYMBOL}/candles?granularity={GRANULARITY}",
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
                    response_body = res.read().decode("utf-8")
                    logging.debug(f"Response body: {response_body}")
                    attempts += 1
                    time.sleep(delay_between_retries)
                    continue

                data = res.read().decode("utf-8")
                if ENABLE_FULL_RESPONSE_DATA:
                    logging.debug(f"Raw response from {url}: {data}")

                try:
                    response_json = json.loads(data)
                    if ENABLE_FULL_RESPONSE_DATA:
                        logging.debug(f"Parsed JSON data structure from {url}: {response_json}")
                except json.JSONDecodeError:
                    logging.error(f"Failed to parse JSON from {url}. Response body: {data}")
                    break

                # Διαχείριση δεδομένων JSON για το Coinbase Brokerage API
                if "api.coinbase.com" in url and "candles" in response_json:
                    candles = response_json["candles"]

                    # Έλεγχος για τα πεδία "start"
                    if all("start" in candle for candle in candles):
                        df = pd.DataFrame(candles, columns=["start", "low", "high", "open", "close", "volume"])
                        df.rename(columns={"start": "time"}, inplace=True)
                        # Μετατροπή της στήλης "time" σε datetime χρησιμοποιώντας τη μονάδα "s" (δευτερόλεπτα)
                        df["time"] = pd.to_datetime(df["time"].astype(int), unit="s", errors="coerce")
                    else:
                        df = pd.DataFrame(candles, columns=["time", "low", "high", "open", "close", "volume"])
                        df["time"] = pd.to_datetime(df["time"], unit="s", errors="coerce")

                    # Έλεγχος αν υπάρχει έγκυρη χρονοσήμανση. Δημιουργία χρονοσήμανσης εάν λείπει ή δεν είναι έγκυρη
                    if df["time"].isnull().all():
                        logging.warning("No valid timedata for Coinbase Brokerage API; generating DatetimeIndex with regular intervals.")
                        start_time = pd.Timestamp.now() - pd.Timedelta(minutes=GRANULARITY * len(df))
                        df["time"] = pd.date_range(start=start_time, periods=len(df), freq=f"{GRANULARITY}T")
                    else:
                        logging.info(f"Valid timedata found for Coinbase Brokerage API.")

                # Ειδική περίπτωση για το Binance API
                # Διαχείριση δεδομένων JSON για το Binance API
                elif "binance" in url:
                    candles = response_json
                    if len(candles[0]) == 12:
                        df = pd.DataFrame(candles, columns=[
                            "time", "open", "high", "low", "close", "volume", 
                            "close_time", "quote_asset_volume", "number_of_trades", 
                            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
                        ])
                    else:
                        df = pd.DataFrame(candles, columns=["time", "open", "high", "low", "close", "volume"])
                    
                    df["time"] = pd.to_datetime(df["time"], unit="ms", errors="coerce")

                    # Έλεγχος αν υπάρχει έγκυρη χρονοσήμανση
                    if df["time"].isnull().all():
                        logging.warning("No valid timedata for Binance API; generating DatetimeIndex with regular intervals.")
                        start_time = pd.Timestamp.now() - pd.Timedelta(minutes=GRANULARITY * len(df))
                        df["time"] = pd.date_range(start=start_time, periods=len(df), freq=f"{GRANULARITY}T")
                    else:
                        logging.info(f"Valid timedata found for Binance API.")
                    
                    

                # Γενική περίπτωση για άλλες APIs
                else:
                    candles = response_json
                    df = pd.DataFrame(candles, columns=["time", "low", "high", "open", "close", "volume"])
                    df["time"] = pd.to_datetime(df["time"], unit="s", errors="coerce")
                    

                    # Έλεγχος αν υπάρχει έγκυρη χρονοσήμανση
                    if df["time"].isnull().all():
                        logging.warning("No valid timedata for general API; generating DatetimeIndex with regular intervals.")
                        start_time = pd.Timestamp.now() - pd.Timedelta(minutes=GRANULARITY * len(df))
                        df["time"] = pd.date_range(start=start_time, periods=len(df), freq=f"{GRANULARITY}T")
                    else:
                        logging.info(f"Valid timedata found for general API.")                    
                    
                    

                # Logging για να διαγνωστεί η δομή και οι τύποι δεδομένων
                if ENABLE_FULL_RESPONSE_DATA:
                    logging.debug(f"Data structure from {url}: \n{df.head()}")
                    logging.debug(f"Data types from {url}: \n{df.dtypes}")

                # Μετατροπή όλων των στηλών σε αριθμητικές τιμές για να αποφευχθούν σφάλματα τύπου
                for column in ["open", "high", "low", "close", "volume"]:
                    df[column] = pd.to_numeric(df[column], errors="coerce")

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


#--------------------------------------------------------------------------------------------------------------------------------------------






# # MOCK UP API - ΓΙΑ ΔΟΚΙΜΕΣ - Απλή έκδοση χωρίς ελέγχους ή retries
# def get_crypto_price():
    # public_base_url = "http://localhost:5015"  # Δικό σου API URL
    # response = requests.get(f"{public_base_url}/price")
    # return float(response.json().get('price'))  # Επιστροφή της τιμής ως float





# Νέα συνάρτηση για την ισοτιμία δολλαρίου
def get_exchange_rate():
    primary_url = "https://api.frankfurter.app/latest?symbols=USD"
    backup_url = "https://v6.exchangerate-api.com/v6/d19c5232df02126152e43f60/pair/EUR/USD"
    timeout_seconds = 5  # Maximum waiting time for the primary API

    try:
        # Test primary API
        response = requests.get(primary_url, timeout=timeout_seconds)
        response.raise_for_status()
        data = response.json()
        exchange_rate = data['rates']['USD']
        return exchange_rate
    except (requests.exceptions.Timeout, requests.exceptions.RequestException):
        logging.warning("The primary API for the exchange rate delayed or failed. Trying the backup API...")

        try:
            # Test backup API
            response = requests.get(backup_url, timeout=timeout_seconds)
            response.raise_for_status()
            data = response.json()
            exchange_rate = data['conversion_rate']
            return exchange_rate
        except requests.exceptions.RequestException as e:
            logging.warning(f"Error retrieving from the backup API as well: {e}")

    # Return None if both APIs fail
    return None





# Νέα έκδοση της συνάρτησης get_crypto_price για χρήση με public endpoint (χωρίς authentication)
def get_crypto_price(retries=3, delay=5):
    # Mock-up mode
    if ENABLE_DEMO_MODE:
        mock_price = 96.01  # Παράδειγμα mock τιμής
        logging.debug(f"Demo mode active: Returning mock price {mock_price} for {CRYPTO_NAME}.")
        return mock_price
    
    
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
            current_rate = get_exchange_rate()
            
            logline_price = f"Fetched {CRYPTO_NAME} price: {price:.{current_decimals}f} {CRYPTO_CURRENCY}"         # δημιουργία Logline
            if current_rate is not None:
                price_in_usd = price * current_rate
                logline_price += f", equivalent to {price_in_usd:.{current_decimals}f} USD."      # προσθήκη στο logline
                
            logging.info(logline_price)                                     # εμφάνιση Logline στα logs    
            
            return price

        except requests.exceptions.RequestException as e:
            logging.error(
                f"Error fetching {CRYPTO_NAME} price: {e}. Attempt {attempt + 1} of {retries}"
            )
            time.sleep(delay)  # Καθυστέρηση πριν την επόμενη προσπάθεια

    # Αν αποτύχουν όλες οι προσπάθειες
    logging.error(f"Failed to fetch {CRYPTO_NAME} price after {retries} attempts.")
    return None





def execute_buy_action(
    df,
    portfolio_uuid,
    TRADE_AMOUNT,
    current_price,
    macd_last,
    signal_last,
    rsi_last,
    bollinger_upper_last,
    bollinger_lower_last,
    vwap_last,
    score,
    current_decimals
):
    global active_trade, trade_amount, highest_price, daily_profit, current_trades

    # Εξαγωγή του υπολοίπου του χαρτοφυλακίου
    portfolio_summary = get_portfolio_balance(portfolio_uuid)

    if "error" not in portfolio_summary:
        available_cash = portfolio_summary['total_cash_equivalent_balance']

        amount_needed_to_buy = TRADE_AMOUNT * current_price
        logging.info(f"Available cash in portfolio: {available_cash:.2f} EUR, Amount needed: {amount_needed_to_buy:.2f} EUR ")

        # Έλεγχος αν το ποσό της αγοράς επαρκεί
        if amount_needed_to_buy <= available_cash:
            logging.info(f"Sufficient funds available ({available_cash:.2f} EUR). Executing Buy Order.")
            order_successful, execution_price, fees = place_order("buy", TRADE_AMOUNT, current_price)

            if order_successful and execution_price:
                # Ενημέρωση μεταβλητών
                active_trade = execution_price
                trade_amount = TRADE_AMOUNT
                highest_price = execution_price
                daily_profit -= fees
                current_trades += 1

                logging.info(f"Order placed successfully at price: {execution_price:.{current_decimals}f} with fees: {fees:.{current_decimals}f}")

                # Δημιουργία reasoning και final_score για email
                reasoning = (
                    f"Indicators: MACD={round(macd_last, 3)}, Signal={round(signal_last, 3)}, "
                    f"RSI={round(rsi_last, 3)}, Bollinger Upper={round(bollinger_upper_last, 3)}, "
                    f"Bollinger Lower={round(bollinger_lower_last, 3)}, "
                    f"VWAP={round(vwap_last, 3)}")
                final_score = f"Trade signal score is positive: {round(score, 3)}."

                # Αποστολή email
                sendgrid_email(trade_amount, "buy", execution_price, fees, final_score, reasoning)

                # Αποθήκευση του state μετά την ενημέρωση
                save_state()
                
                return True, "Order placed successfully."
            else:
                logging.info(f"Order placement failed. No buy action taken.")
                return False, "Order placement failed."
        else:
            logging.warning(f"Insufficient funds. Needed: {amount_needed_to_buy:.2f} EUR, Available: {available_cash:.2f} EUR")
            send_push_notification(
                f"ALERT: Insufficient funds for {CRYPTO_NAME} bot. Needed: {amount_needed_to_buy:.2f} EUR, Available: {available_cash:.2f} EUR. This alert originates from the fallback_conditions block. Please ensure sufficient funds as this message will appear every 2 minutes.",
                Logfile=False
            )
            return False, "Insufficient funds."
            
    else:
        logging.error(f"Failed to retrieve portfolio balance. No buy action taken.")
        logging.error(f"Error details: {portfolio_summary['message']}")
        return False, "Portfolio balance retrieval failed."





# Main trading logic (updated)
def execute_scalping_trade(CRYPTO_SYMBOL):
    global daily_profit, current_trades, highest_price, active_trade, trade_amount, start_bot, trailing_profit_active
    global second_trade_price, second_trade_amount, average_trade_price  # Υφιστάμενες global μεταβλητές για τη 2η αγορά
    global highest_price_second_position, trailing_profit_second_position_active  # Προσθήκη μεταβλητών για τη 2η θέση
    global third_trade_price, third_trade_amount, highest_price_third_position, trailing_profit_third_position_active  # Νέες global μεταβλητές για την 3η αγορά
    global manual_second_buy, manual_third_buy


    
    logging.info(f"Executing trade logic for {CRYPTO_SYMBOL}")
    if not active_trade:        
        logging.info(f"Analyzing technical indicators: MACD for momentum, RSI for overbought/oversold levels, Bollinger Bands for volatility, and VWAP for price-volume trends.")

    

    logging.debug(f"Scalp target: {SCALP_TARGET}, "
                 f"Trailing threshold: {f'{STATIC_TRAILING_PROFIT_THRESHOLD}, Sell on trailing: {SELL_ON_TRAILING}' if ENABLE_TRAILING_PROFIT else 'Disabled'}, "
                 f"Stop-loss: {f'{STOP_LOSS}, Dynamic Stop-loss: {ENABLE_DYNAMIC_STOP_LOSS}' if ENABLE_STOP_LOSS else 'Disabled'}, "
                 f"Minimum Profit Threshold: {MINIMUM_PROFIT_THRESHOLD}")

    
        
    
    
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



        #------------------------------------------------------------------------------------------------------------------ 
        
        # ΔΥΝΑΜΙΚΟ TRADE_AMOUNT - Υπολογισμός προσαρμοσμένου TRADE_AMOUNT
        if DYNAMIC_TRADE_ENABLED:
            
            if trade_amount == 0:
                trade_amount = 500  # Εξασφάλιση ότι χρησιμοποιείται η αρχική τιμή            
            
                #logging.info(f"Initial trade amount: {trade_amount}")    
                PROFIT_OR_LOSS_CRYPTO = daily_profit / current_price  # Μετατροπή κέρδους/ζημίας σε αριθμό κρυπτονομισμάτων
                trade_amount = trade_amount + PROFIT_OR_LOSS_CRYPTO
                    
                logging.info(f"Dynamic trade Enabled. New Trade Amount: {trade_amount:.{current_decimals}f} {CRYPTO_SYMBOL}")        
         
        #------------------------------------------------------------------------------------------------------------------


        # Αν υπάρχει ανοιχτή θέση, έλεγχος για πώληση
        if active_trade:
            # Πρώτο μέρος: Πληροφορίες για την πρώτη αγορά
            log_message = f"Active trade at {active_trade:.{current_decimals}f} {CRYPTO_CURRENCY}."

            # Δεύτερο μέρος: Αν υπάρχει δεύτερη αγορά, προσθέτουμε πληροφορίες
            if second_trade_price:
                log_message += f" Second trade at {second_trade_price:.{current_decimals}f} with {second_trade_amount} {CRYPTO_NAME}."
                
                
            # Τρίτο μέρος: Αν υπάρχει τρίτη αγορά, προσθέτουμε πληροφορίες
            if third_trade_price:
                log_message += f" Third trade at {third_trade_price:.{current_decimals}f} with {third_trade_amount} {CRYPTO_NAME}."                

            # Τέταρτο μέρος: Προσθήκη του "Checking for sell opportunity." στο τέλος
            log_message += " Checking sell opportunity."

            # Καταγραφή του τελικού μηνύματος
            logging.info(log_message)






            # Αρχικοποίηση του highest_price αν είναι None
            if highest_price is None:
                highest_price = active_trade
                logging.info(f"Initialized highest_price to {highest_price}")
                save_state()  # Αποθήκευση του ενημερωμένου highest_price

            # Ενημέρωση του highest_price μόνο αν η τρέχουσα τιμή είναι μεγαλύτερη
            if current_price > highest_price:
                highest_price = current_price
                logging.info(f"Updated highest_price to {highest_price}")
                save_state(log_info=False)  # Αποθήκευση του ενημερωμένου highest_price χωρίς Logging.info

            logging.info(f"Current Price: {current_price:.{current_decimals}f} {CRYPTO_CURRENCY}, Highest Price: {highest_price} {CRYPTO_CURRENCY}.")



            df, source_url = fetch_data()
            if df is None:
                logging.error(f"Failed to fetch data from {source_url}")
                return

                    
            # Πριν από τον υπολογισμό δεικτών
            df['high'] = pd.to_numeric(df['high'], errors='coerce')
            df['low'] = pd.to_numeric(df['low'], errors='coerce')
            df['close'] = pd.to_numeric(df['close'], errors='coerce')


##########################################################################################################################################################################

            # Υπολογισμός των δεικτών
            macd, signal = calculate_macd(df)
            rsi = calculate_rsi(df)
            bollinger_upper, bollinger_lower = calculate_bollinger_bands(df)
            vwap = calculate_vwap(df)

            # Λήψη των τελευταίων τιμών για κάθε δείκτη
            macd_last = float(macd.iloc[-1]) if isinstance(macd.iloc[-1], (float, int, str)) else macd
            signal_last = float(signal.iloc[-1]) if isinstance(signal.iloc[-1], (float, int, str)) else signal
            rsi_last = float(rsi.iloc[-1]) if isinstance(rsi.iloc[-1], (float, int, str)) else rsi
            bollinger_upper_last = float(bollinger_upper.iloc[-1]) if isinstance(bollinger_upper.iloc[-1], (float, int, str)) else bollinger_upper
            bollinger_lower_last = float(bollinger_lower.iloc[-1]) if isinstance(bollinger_lower.iloc[-1], (float, int, str)) else bollinger_lower
            vwap_last = float(vwap.iloc[-1]) if isinstance(vwap.iloc[-1], (float, int, str)) else vwap



            if ENABLE_GEORGE_SAYS:
                # Logging για έλεγχο τύπων και τιμών
                logging.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                logging.info("George said: Evaluate indicators for feedback after opening a position")

                logging.info(
                    f"Indicators: MACD={macd_last:.{current_decimals}f}, Signal={signal_last:.{current_decimals}f}, "
                    f"RSI={rsi_last:.{current_decimals}f}, Bollinger Upper={bollinger_upper_last:.{current_decimals}f}, "
                    f"Bollinger Lower={bollinger_lower_last:.{current_decimals}f}, Current Price={current_price:.{current_decimals}f}, "
                    f"VWAP={vwap_last:.{current_decimals}f}"
                )
            
            
            



            # Βάρη για κάθε δείκτη - ΦΟΡΤΏΝΟΝΤΑΙ ΑΠΟ ΕΞΩΤΕΡΙΚΟ ΑΡΧΕΙΟ JSON
            weights = load_weights(CRYPTO_NAME)
            
            
            

            try:
                # Αρχικοποίηση βαθμολογίας και βαθμολογιών δεικτών
                score = 0
                scores = {}

                # Υπολογισμός MACD
                scores['macd'] = weights['macd'] * (1 if macd_last > signal_last else -1)
                score += scores['macd']
                #logging.info(f"MACD Score: {scores['macd']}")

                # Υπολογισμός RSI            
                scores['rsi'] = weights['rsi'] * (1 if rsi_last < RSI_THRESHOLD else -1)
                score += scores['rsi']
                #logging.info(f"RSI Score: {scores['rsi']}")

                # Υπολογισμός Bollinger Bands
                if current_price <= bollinger_lower_last:
                    scores['bollinger'] = weights['bollinger'] * 1
                elif current_price >= bollinger_upper_last:
                    scores['bollinger'] = weights['bollinger'] * -1
                else:
                    scores['bollinger'] = 0
                score += scores['bollinger']
                #logging.info(f"Bollinger Score: {scores['bollinger']}")

                # Υπολογισμός VWAP
                scores['vwap'] = weights['vwap'] * (1 if current_price > vwap_last else -1)
                score += scores['vwap']



                if ENABLE_TABULATE_INDICATORS:
                    # Δημιουργία πίνακα με τα αποτελέσματα
                    table_data = [
                        ["MACD", macd_last, "MACD > Signal" if macd_last > signal_last else "MACD < Signal", weights['macd'], scores['macd']],
                        ["RSI", rsi_last, "RSI > 30" if rsi_last > RSI_THRESHOLD else "RSI < 30", weights['rsi'], scores['rsi']],
                        ["Bollinger", current_price, "Current Price < Bollinger Lower" if current_price <= bollinger_lower_last
                            else "Current Price > Bollinger Upper" if current_price >= bollinger_upper_last
                            else "Inside Bands", weights['bollinger'], scores['bollinger']],
                        ["VWAP", current_price, "Current Price > VWAP" if current_price > vwap_last else "Current Price < VWAP",
                         weights['vwap'], scores['vwap']],
                        ["Total Score", "", "", "", round(score, 3)]
                    ]

                    # Format table
                    table = tabulate(table_data, headers=["Indicator", "Value", "Condition", "Weight", "Score"], tablefmt="pretty")

                    # Log table
                    logging.info("\n" + table)

                    # Logging της συνολικής βαθμολογίας
                    logging.info(f"Total Score: {score:.{current_decimals}f}")

                
                if ENABLE_GEORGE_SAYS:
                    logging.info(f"Trade signal score is ({score:.{current_decimals}f}) while buy threshold is ({BUY_THRESHOLD}).")
                    logging.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")


            except TypeError as e:
                logging.error(f"TypeError occurred during score calculation: {e}")
                logging.error(f"Values - MACD Last: {macd_last}, Signal Last: {signal_last}, "
                              f"RSI Last: {rsi_last}, Bollinger Upper: {bollinger_upper_last}, "
                              f"Bollinger Lower: {bollinger_lower_last}, VWAP: {vwap_last}")
                return False, None            



##########################################################################################################################################################################
         
            # Logging πριν το statement
            logging.debug(f"ENABLE_DYNAMIC_MAX_DROP_PERCENTAGE: {ENABLE_DYNAMIC_MAX_DROP_PERCENTAGE}")
            logging.debug(f"Second_trade_price: {second_trade_price}")

            #--------------------------------------------------------------------------------------------------------------------------------------------------------------
            # Dynamic MAX_DROP_PERCENTAGE
            if ENABLE_DYNAMIC_MAX_DROP_PERCENTAGE and not third_trade_price:  # Υπολογισμός μόνο αν δεν υπάρχει 3η αγορά
                dynamic_adjustment = 0
                
                # Call the calculate_adx function, which should return both adx and atr
                adx, atr = calculate_adx(df)
                atr_value = atr.iloc[-1]
                adx_value = adx.iloc[-1]
                atr_percentage = atr_value / current_price

                if atr_value <= 0 or adx_value <= 0 or current_price <= 0:
                    logging.warning("Invalid market data for ADX or ATR. Skipping dynamic adjustment.")
                    return                

                if adx_value < ADX_THRESHOLD:
                    DYNAMIC_MAX_DROP_PERCENTAGE = MAX_DROP_PERCENTAGE
                else:
                    dynamic_adjustment = ATR_FACTOR * atr_percentage
                    DYNAMIC_MAX_DROP_PERCENTAGE = MAX_DROP_PERCENTAGE + dynamic_adjustment

                logging.info("Dynamic MAX_DROP_PERCENTAGE enabled.")
                logging.info(f"ADX Value: {adx_value:.2f}, ATR Value: {atr_value:.2f}, ATR Percentage: {atr_percentage:.4f}")            
                logging.info(f"Dynamic Adjustment: {dynamic_adjustment:.4f}, Dynamic Threshold: {DYNAMIC_MAX_DROP_PERCENTAGE:.4f}")

                if not second_trade_price:
                    second_buy_trigger_price = active_trade * (1 - DYNAMIC_MAX_DROP_PERCENTAGE)
                    logging.info(f"Second Buy Trigger Price with Dynamic Threshold: {second_buy_trigger_price:.2f} {CRYPTO_CURRENCY}")
                elif not third_trade_price and second_trade_price:
                    third_buy_trigger_price = second_trade_price * (1 - DYNAMIC_MAX_DROP_PERCENTAGE)
                    logging.info(f"Third Buy Trigger Price with Dynamic Threshold: {third_buy_trigger_price:.2f} {CRYPTO_CURRENCY}")
            else:
                logging.info("Dynamic MAX_DROP_PERCENTAGE skipped. All positions filled.")

            



            #----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # DOLLAR COST AVERAGE STRATEGY
            logging.debug(f"Manual second buy state is: {manual_second_buy}")
            
            # AΓΟΡΑ ΔΕΥΤΕΡΗΣ ΘΕΣΗΣ - Έλεγχος αν η τιμή έχει πέσει αρκετά για δεύτερη αγορά ----------------------------------------------------------------------------------------------------------------------------------------
            if not second_trade_price and (current_price <= second_buy_trigger_price or manual_second_buy):
                if manual_second_buy:
                    logging.info(f"Manual trigger activated for second buy. Executing second buy at current price {current_price:.{current_decimals}f} {CRYPTO_CURRENCY}.")
                else:
                    logging.info(f"Price {current_price} {CRYPTO_CURRENCY} dropped below threshold {second_buy_trigger_price:.{current_decimals}f} {CRYPTO_CURRENCY}. Executing second buy.")

                # Εκτέλεση της εντολής αγοράς
                second_trade_amount = trade_amount  # Ίδια ποσότητα με την αρχική
                order_successful, execution_price, fees = place_order("buy", second_trade_amount, current_price)

                if order_successful and execution_price:
                    second_trade_price = execution_price

                    # Υπολογισμός νέας μέσης τιμής
                    second_total_cost = (trade_amount * active_trade) + (second_trade_amount * second_trade_price)
                    second_total_amount = trade_amount + second_trade_amount
                    average_trade_price = second_total_cost / second_total_amount
                    
                    # Προσθήκη των fees στο daily_profit                
                    daily_profit -= fees  # Αφαιρούμε τα fees από το daily_profit για ακριβή υπολογισμό του κόστους                    


                    # Ειδοποίηση με διαφορετικό μήνυμα ανάλογα με το manual second buy
                    if manual_second_buy:
                        send_push_notification(f"ALERT: Manual second buy executed successfully at {second_trade_price:.{current_decimals}f} for {CRYPTO_NAME} bot.")
                        
                        logging.info(f"Manual second buy executed successfully at {second_trade_price:.{current_decimals}f}. "
                                     f"New average price: {average_trade_price:.{current_decimals}f}.")                        
                        
                    else:
                        send_push_notification(f"ALERT: Second buy executed automatically at {second_trade_price:.{current_decimals}f} for {CRYPTO_NAME} bot.")
                        
                        logging.info(f"Second buy executed automatically at {second_trade_price:.{current_decimals}f}. "
                                     f"New average price: {average_trade_price:.{current_decimals}f}.") 


                    
                    # Αποθήκευση κατάστασης μετά την αγορά
                    manual_second_buy = False       # Επαναφορά του flag
                    save_state()
                    
                    return

                else:
                    logging.error(f"Failed to execute second buy order at price: {current_price:.{current_decimals}f}.")
                    second_trade_amount = 0
                    save_state(log_info=False)
                    return
                    




            # ΠΩΛΗΣΗ ΔΕΥΤΕΡΗΣ ΘΕΣΗΣ - Λογική για πώληση μετά τη 2η αγορά ----------------------------------------------------------------------------------------------------------------------------------------------------------
            if second_trade_price:  # Εξασφαλίζουμε ότι υπάρχει 2η αγορά πριν υπολογίσουμε

                # Υπολογισμός του συνολικού κόστους με fees
                second_total_fees = (trade_amount * active_trade + second_trade_amount * second_trade_price) * FEES_PERCENTAGE
                second_break_even_price = (trade_amount * active_trade + second_trade_amount * second_trade_price + second_total_fees) / (trade_amount + second_trade_amount)
                remaining_to_break_even = max(0, second_break_even_price - current_price)
                logging.info(f"[Second Position] Break-even sell price: {second_break_even_price:.{current_decimals}f} {CRYPTO_CURRENCY}.")
                
                

                # Έλεγχος για πώληση μόνο αν η τρέχουσα τιμή καλύπτει το κόστος + fees
                if current_price >= second_break_even_price:
                    logging.info(f"[Second Position] Current price {current_price:.{current_decimals}f} {CRYPTO_CURRENCY} reached sell price {second_break_even_price:.{current_decimals}f} {CRYPTO_CURRENCY}.")


                    # Ενεργοποίηση trailing profit για τη δεύτερη θέση μόνο αν δεν είναι ήδη ενεργό
                    if not trailing_profit_second_position_active:
                        trailing_profit_second_position_active = True
                        highest_price_second_position = current_price  # Αρχικοποίηση της μέγιστης τιμής
                        logging.info(f"[Second Position] Trailing profit activated for second position and initialized highest price to {highest_price_second_position:.{current_decimals}f}.")
                        save_state(log_info=False)  #χωρίς Logging.info



                    # Ενημέρωση της μέγιστης τιμής για το trailing profit αυτού του block
                    if current_price > highest_price_second_position:
                        highest_price_second_position = current_price
                        logging.info(f"[Second Position] Initialized highest_price to {highest_price_second_position:.{current_decimals}f}")
                        save_state(log_info=False)  #χωρίς Logging.info
                        
                        
                       
                        
                
                # ===== Νέο Block: Έλεγχος Trailing Sell Εκτός Break-even Check =====
                if trailing_profit_second_position_active:
                
                    
                    # Υπολογισμός ποσοστού δυναμικά βάσει των θέσεων
                    TRAILING_PROFIT_SECOND_PERCENTAGE = round((active_trade - second_trade_price) / active_trade, 3)
                    logging.info(f"[Second Position] Trailing profit recalculated to {TRAILING_PROFIT_SECOND_PERCENTAGE}")
                    
                    # Υπολογισμός του trailing sell price για τη δεύτερη θέση                   
                    trailing_sell_price_second_position = max(
                        second_break_even_price,
                        highest_price_second_position * (1 - TRAILING_PROFIT_SECOND_PERCENTAGE)
                    )                   
                    
                    logging.debug(f"[Second Position] Trailing sell price: {trailing_sell_price_second_position:.8f}, Highest price: {highest_price_second_position:.8f}")


                    # Έλεγχος αν η τρέχουσα τιμή έχει πέσει κάτω από το trailing sell price
                    logging.debug(f"DEBUG: Current Price: {current_price:.8f}, Trailing Sell Price: {trailing_sell_price_second_position:.8f}")
                    logging.debug(f"DEBUG: Highest Price: {highest_price_second_position}, Trailing Sell Price: {trailing_sell_price_second_position}")

                    if current_price <= trailing_sell_price_second_position:

                        logging.info(f"[Second Position] Current price {current_price:.{current_decimals}f} {CRYPTO_CURRENCY} "
                                     f"dropped below trailing sell price {trailing_sell_price_second_position:.{current_decimals}f} {CRYPTO_CURRENCY}. "
                                     "Evaluating break-even condition before executing sell.")                        

                        
                        # Έλεγχος αν η τιμή έχει φτάσει στο break-even price πριν την πώληση
                        if current_price >= second_break_even_price:

                            logging.info(f"[Second Position] Current price {current_price:.{current_decimals}f} {CRYPTO_CURRENCY} "
                                         f"dropped below trailing sell price {trailing_sell_price_second_position:.{current_decimals}f} {CRYPTO_CURRENCY} "
                                         f"and is above break-even price {second_break_even_price:.{current_decimals}f} {CRYPTO_CURRENCY}. Selling all positions.")    


                            # Ελέγχουμε αν η 3η θέση υπάρχει και αν ναι, πουλάμε όλες τις θέσεις
                            if third_trade_price:  # Υπάρχει 3η θέση
                                logging.info(f"[Second Position] 3rd position exists, selling all positions.")


                                # Καλούμε τη συνάρτηση sell_all_positions() για να πουλήσουμε όλες τις θέσεις
                                sell_all_positions()

                            
                            else:                                
                        
                                # Αν δεν υπάρχει 3η θέση, πουλάμε μόνο τη 1η και 2η
                                logging.info(f"[Second Position] 3rd position does not exist, selling only 1st and 2nd positions.")                        
                        
                                # Υπολογισμός συνολικής ποσότητας προς πώληση
                                total_amount_to_sell = trade_amount + second_trade_amount

                                # Εκτέλεση εντολής πώλησης
                                order_successful, execution_price, fees = place_order("sell", total_amount_to_sell, current_price)

                                if order_successful:
                                    # Υπολογισμός καθαρού κέρδους
                                    profit_loss = (execution_price * total_amount_to_sell) - (trade_amount * active_trade + second_trade_amount * second_trade_price + second_total_fees)
                                    daily_profit += profit_loss

                                    logging.info(f"The sale was completed for total amount of {total_amount_to_sell} {CRYPTO_NAME}. "
                                                 f"Profit/Loss: {profit_loss:.{current_decimals}f} {CRYPTO_CURRENCY}, Fees: {fees:.{current_decimals}f}")

                                    # Καθαρισμός μεταβλητών μετά την πώληση
                                    active_trade = None
                                    trade_amount = 0
                                    second_trade_price = None
                                    second_trade_amount = 0
                                    average_trade_price = None
                                    highest_price = None
                                    highest_price_second_position = None
                                    trailing_profit_second_position_active = False
                                    current_trades += 1

                                    send_push_notification(f"ALERT: Trailing Profit Sale for second position executed for {CRYPTO_NAME} bot.")
                                    
                                    sendgrid_email(total_amount_to_sell, "sell", execution_price, profit_loss, "N/A", "DCA Strategy")

                                    # Αποθήκευση της νέας κατάστασης
                                    save_state()

                                    # Χρονική αναμονή μετά την πώληση για αποφυγή άμεσης αγοράς
                                    save_cooldown_state(custom_duration=1800)  # DCA strategy: 30 min cooldown
                                    
                                    return


                        else:
                            logging.info(f"[Second Position] Current price {current_price:.{current_decimals}f} "
                                         f"dropped below trailing sell price ({trailing_sell_price_second_position:.{current_decimals}f}) "
                                         f"but is below break-even price ({second_break_even_price:.{current_decimals}f}). No sell action taken.")                            
                                             
                    
                    elif current_price > trailing_sell_price_second_position:
                        logging.info(f"[Second Position] Current price {current_price:.{current_decimals}f} "
                                     f"has not dropped below trailing sell price ({trailing_sell_price_second_position:.{current_decimals}f}). "
                                     "No sell action taken. Waiting for price to meet criteria.")                        





            # ΑΓΟΡΑΣ ΤΡΙΤΗΣ ΘΕΣΗΣ - Έλεγχος για 3η αγορά του crypto ---------------------------------------------------------------------------------------------------------------------------------------------------------------
            logging.debug(f"Manual third buy state is: {manual_third_buy}")
            if not third_trade_price and second_trade_price and (current_price <= third_buy_trigger_price or manual_third_buy):
                if manual_third_buy:
                    logging.info(f"Manual trigger activated for third buy. Executing third buy at current price {current_price:.{current_decimals}f} {CRYPTO_CURRENCY}.")
                else:
                    logging.info(f"Price {current_price} {CRYPTO_CURRENCY} dropped below threshold {third_buy_trigger_price:.{current_decimals}f} {CRYPTO_CURRENCY}. Executing third buy.")


                # Έκτελεση της εντολής αγοράς για την 3η θέση
                third_trade_amount = trade_amount  # Ίδια ποσότητα με την αρχική
                order_successful, execution_price, fees = place_order("buy", third_trade_amount, current_price)

                if order_successful and execution_price:
                    third_trade_price = execution_price

                    # Υπολογισμός νέας μέσης τιμής
                    third_total_cost = (trade_amount * active_trade) + (second_trade_amount * second_trade_price) + (third_trade_amount * third_trade_price)
                    third_total_amount = trade_amount + second_trade_amount + third_trade_amount
                    average_trade_price = third_total_cost / third_total_amount

                    # Προσθήκη των fees στο daily_profit
                    daily_profit -= fees

                    # Ειδοποίηση με διαφορετικό μήνυμα ανάλογα με το manual τρίτο buy
                    if manual_third_buy:
                        send_push_notification(f"ALERT: Manual third buy executed successfully at {third_trade_price:.{current_decimals}f} for {CRYPTO_NAME} bot.")
                        
                        logging.info(f"Manual third buy executed successfully at {third_trade_price:.{current_decimals}f}. "
                                     f"New average price: {average_trade_price:.{current_decimals}f}.")                        
                        
                    else:
                        send_push_notification(f"ALERT: Third buy executed automatically at {third_trade_price:.{current_decimals}f} for {CRYPTO_NAME} bot.")
                        
                        logging.info(f"Third buy executed automatically at {third_trade_price:.{current_decimals}f}. "
                                     f"New average price: {average_trade_price:.{current_decimals}f}.")

                    # Αποθήκευση κατάστασης μετά την αγορά
                    manual_third_buy = False       # Επαναφορά του flag
                    save_state()
                    return

                else:
                    logging.error(f"Failed to execute third buy order at price: {current_price:.{current_decimals}f}.")
                    third_trade_amount = 0
                    save_state(log_info=False)
                    return





            # ΠΩΛΗΣΗ ΤΡΙΤΗΣ ΘΕΣΗΣ - Λογική για πώληση μετά τη 3η αγορά ------------------------------------------------------------------------------------------------------------------------------------------------------------
            if third_trade_price:  # Εξασφαλίζουμε ότι υπάρχει 3η αγορά πριν υπολογίσουμε

                # Υπολογισμός του συνολικού κόστου με fees
                third_total_fees = (trade_amount * active_trade + second_trade_amount * second_trade_price + third_trade_amount * third_trade_price) * FEES_PERCENTAGE
                third_break_even_price = (trade_amount * active_trade + second_trade_amount * second_trade_price + third_trade_amount * third_trade_price + third_total_fees) / (trade_amount + second_trade_amount + third_trade_amount)
                remaining_to_break_even = max(0, third_break_even_price - current_price)
                logging.info(f"[Third Position] Break-even sell price: {third_break_even_price:.{current_decimals}f} {CRYPTO_CURRENCY}.")

                # Έλεγχος για πώληση μόνο αν η τρέχουσα τιμή καλύπτει το κόστο + fees
                if current_price >= third_break_even_price:
                    logging.info(f"[Third Position] Current price {current_price:.{current_decimals}f} {CRYPTO_CURRENCY} reached sell price {third_break_even_price:.{current_decimals}f} {CRYPTO_CURRENCY}.")

                    # Ενεργοποίηση trailing profit για τη τρίτη θέση μόνο αν δεν είναι ήδη ενεργό
                    if not trailing_profit_third_position_active:
                        trailing_profit_third_position_active = True
                        highest_price_third_position = current_price  # Έναρξη της μέγιστης τιμής
                        logging.info(f"[Third Position] Trailing profit activated for third position and initialized highest price to {highest_price_third_position:.{current_decimals}f}.")
                        save_state(log_info=False)

                    # Ενημέρωση της μέγιστης τιμής για το trailing profit αυτού του block
                    if current_price > highest_price_third_position:
                        highest_price_third_position = current_price
                        logging.info(f"[Third Position] Initialized highest_price to {highest_price_third_position:.{current_decimals}f}")
                        save_state(log_info=False)
                        


                        
                # ===== Νέο Block: Έλεγχος Trailing Sell, για 3ή αγορά, εκτός Break-even Check =====
                if trailing_profit_third_position_active:                       
                  
                    TRAILING_PROFIT_THIRD_PERCENTAGE = 0.02  # 2% σταθερό ποσοστό για την 3η θέση
                    
                    
                    trailing_sell_price_third_position = max(
                        third_break_even_price,
                        highest_price_third_position * (1 - TRAILING_PROFIT_THIRD_PERCENTAGE)
                    )           
                    
                    logging.debug(f"[Third Position] Trailing sell price updated to {trailing_sell_price_third_position:.{current_decimals}f} {CRYPTO_CURRENCY}.")


                    # Έλεγχος αν η τρέχουσα τιμή έχει πέσει κάτω από το trailing sell price
                    logging.debug(f"DEBUG: Current Price: {current_price:.8f}, Trailing Sell Price: {trailing_sell_price_third_position:.8f}")
                    logging.debug(f"DEBUG: Highest Price: {highest_price_third_position}, Trailing Sell Price: {trailing_sell_price_third_position}")
                                        
                    if current_price <= trailing_sell_price_third_position:
                        
                        logging.info(f"[Third Position] Current price {current_price:.{current_decimals}f} {CRYPTO_CURRENCY} "
                                     f"dropped below trailing sell price {trailing_sell_price_third_position:.{current_decimals}f} {CRYPTO_CURRENCY}. "
                                     "Evaluating break-even condition before executing sell.")                    

                        if current_price >= third_break_even_price:
                            
                            logging.info(f"[Third Position] Current price {current_price:.{current_decimals}f} {CRYPTO_CURRENCY} "
                                         f"dropped below trailing sell price {trailing_sell_price_third_position:.{current_decimals}f} {CRYPTO_CURRENCY} "
                                         f"and is above break-even price {third_break_even_price:.{current_decimals}f} {CRYPTO_CURRENCY}. Selling all positions.")

                            
                        
                            # Υπολογισμός συνολικής ποσότητας προς πώληση
                            total_amount_to_sell = trade_amount + second_trade_amount + third_trade_amount

                            # Έκτελεση εντολής πωλήσης
                            order_successful, execution_price, fees = place_order("sell", total_amount_to_sell, current_price)

                            if order_successful:
                                # Υπολογισμός καθαρού κέρδους
                                profit_loss = (execution_price * total_amount_to_sell) - (trade_amount * active_trade + second_trade_amount * second_trade_price + third_trade_amount * third_trade_price + third_total_fees)
                                daily_profit += profit_loss
                                            
                                logging.info(f"The sale was completed for total amount of {total_amount_to_sell} {CRYPTO_NAME}. "
                                             f"Profit/Loss: {profit_loss:.{current_decimals}f} {CRYPTO_CURRENCY}, Fees: {fees:.{current_decimals}f}")                                         
                                                                                     

                                # Καθαρισμός μεταβλητών μετά τη πώληση
                                active_trade = None
                                trade_amount = 0
                                second_trade_price = None
                                second_trade_amount = 0
                                third_trade_price = None
                                third_trade_amount = 0
                                average_trade_price = None
                                highest_price = None
                                highest_price_second_position = None
                                highest_price_third_position = None
                                trailing_profit_second_position_active = False
                                trailing_profit_third_position_active = False
                                current_trades += 1

                                send_push_notification(
                                    f"ALERT: Trailing Profit Sale for third position was executed for {CRYPTO_NAME} bot at {execution_price:.{current_decimals}f} {CRYPTO_CURRENCY}. "
                                    f"The net profit after calculating and subtracting the fees is {profit_loss:.2f} {CRYPTO_CURRENCY}."
                                )

                                sendgrid_email(total_amount_to_sell, "sell", execution_price, profit_loss, "N/A", "DCA Strategy")

                                # Αποθήκευση της νέας κατάστασης
                                save_state()

                                # Χρονική αναμονή μετά τη πώληση για αποφυγή άμεσης αγοράς
                                save_cooldown_state(custom_duration=1800)  # DCA strategy: 30 min cooldown

                                return


                        else:
                            logging.info(
                                f"[Third Position] Current price {current_price:.{current_decimals}f} {CRYPTO_CURRENCY} "
                                                                                                                                                          
                                f"is below break-even price {third_break_even_price:.{current_decimals}f} {CRYPTO_CURRENCY}."
                            )
                            logging.info("No sell action taken.")


                    else:
                        logging.info(f"[Third Position] Current price {current_price:.{current_decimals}f} {CRYPTO_CURRENCY} has not dropped below trailing sell price {trailing_sell_price_third_position:.{current_decimals}f} {CRYPTO_CURRENCY}.")




            
            # STOP LOSS MANAGEMENT - Έλεγχος για την ενεργοποίηση του stop-loss----------------------------------------------------------------------------------------------------------------------------------------------------
            if ENABLE_STOP_LOSS:
                # Υπολογισμός της τιμής του δυναμικού stop-loss βάσει του ATR
                if ENABLE_DYNAMIC_STOP_LOSS:
                    # Call the calculate_adx function, which should return both adx and atr
                    adx, atr = calculate_adx(df)
                    # Λήψη της τελευταίας τιμής για χρήση στον υπολογισμό του dynamic stop loss
                    atr_value = atr.iloc[-1]
                    
                    
                    stop_loss_price = active_trade - (atr_value * ATR_MULTIPLIER)
                    logging.info(f"Dynamic stop-loss set at: {stop_loss_price:.{current_decimals}f} (ATR Multiplier: {ATR_MULTIPLIER})")
                else:
                    stop_loss_price = active_trade * STOP_LOSS  # Εφαρμογή του ποσοστιαίου ορίου
                    logging.info(f"Static stop-loss set at: {stop_loss_price:.{current_decimals}f}")

                # Έλεγχος αν η τρέχουσα τιμή ενεργοποιεί το stop-loss
                if current_price <= stop_loss_price:
                    logging.info(f"Stop-loss triggered. Attempting to sell at current price: {current_price}")
                    order_successful, execution_price, fees = place_order("sell", trade_amount, current_price)

                    if order_successful and execution_price:
                        # Υπολογισμός του κέρδους ή της ζημίας και ενημέρωση των μεταβλητών
                        profit_loss = (execution_price - active_trade) * trade_amount - fees
                        daily_profit += profit_loss
                        logging.info(f"Sell order executed at {execution_price}. Profit/Loss: {profit_loss:.{current_decimals}f}, Fees: {fees}")

                        # Αποστολή ειδοποίησης μέσω email
                        sendgrid_email(trade_amount, "sell", execution_price, profit_loss, "N/A", "Stop-Loss")

                        # Επαναφορά των μεταβλητών της συναλλαγής
                        active_trade = None
                        trade_amount = 0
                        highest_price = None
                        current_trades += 1
                        save_state()  # Αποθήκευση της τρέχουσας κατάστασης
                        
                        
                        # Χρονική αναμονή μετά την πώληση για αποφυγή άμεσης αγοράς
                        save_cooldown_state(custom_duration=3600)        #stop-loss  1 hour                

                        return  # Σταματάει η εκτέλεση εδώ αν γίνει πώληση λόγω stop-loss
                    else:
                        logging.warning(f"Failed to execute sell order for stop-loss at {current_price}")





            # ΠΩΛΗΣΗ 1ης ΘΕΣΗΣ ΜΕ TRAILING ΕΝΕΡΓΟ - Υπολογισμός του scalp target price --------------------------------------------------------------------------------------------------------------------------------------------
            scalp_target_price = active_trade * SCALP_TARGET
            if ENABLE_TRAILING_PROFIT:
                try:
                    # Έλεγχος αν το trailing profit είναι ενεργό ή αν πρέπει να ενεργοποιηθεί
                    if not trailing_profit_active and current_price >= scalp_target_price:
                        logging.info(f"Scalp target reached. Trailing profit activated.")
                        trailing_profit_active = True
                        save_state(log_info=False)  #χωρίς Logging.info
                                                                                                                        

                    if trailing_profit_active:
                        if ENABLE_DYNAMIC_TRAILING_PROFIT:
                            if second_trade_price in [None, 0] and third_trade_price in [None, 0]:
                                # Δυναμικός υπολογισμός για την active_trade (1η θέση)
                                atr_period_21 = calculate_adx(df, period=21)[1]  # ATR για μεγαλύτερο period
                                last_atr_value = atr_period_21.iloc[-1]  # Παίρνουμε την τελευταία τιμή του ATR
                                logging.info(f"ATR (Period 21): {last_atr_value:.6f}")

                                # Υπολογισμός δυναμικού threshold
                                TRAILING_PROFIT_THRESHOLD = last_atr_value * ATR_MULTIPLIER / current_price
                                logging.info(f"Dynamic trailing profit enabled. Threshold: {TRAILING_PROFIT_THRESHOLD:.4f}")

                            elif third_trade_price in [None, 0]:
                                # Δυναμικός υπολογισμός για τη second_trade_price (2η θέση)
                                atr_period_21 = calculate_adx(df, period=21)[1]  # ATR για μεγαλύτερο period
                                last_atr_value = atr_period_21.iloc[-1]  # Παίρνουμε την τελευταία τιμή του ATR
                                logging.info(f"ATR (Period 21): {last_atr_value:.6f}")

                                # Υπολογισμός δυναμικού threshold
                                TRAILING_PROFIT_THRESHOLD = last_atr_value * ATR_MULTIPLIER / current_price
                                logging.info(f"Dynamic trailing profit enabled. Threshold: {TRAILING_PROFIT_THRESHOLD:.4f}")
                                

                            else:
                                # Λογική για την 1η θέση: Υπολογισμός με ποσοστό (1η - 2η θέση)
                                TRAILING_PROFIT_THRESHOLD = (active_trade - second_trade_price) / active_trade
                                logging.info(f"Dynamic (ATR) trailing profit disabled. Threshold for active_trade: {TRAILING_PROFIT_THRESHOLD:.4f}")

                        else:
                            # Χρήση στατικού threshold
                            TRAILING_PROFIT_THRESHOLD = STATIC_TRAILING_PROFIT_THRESHOLD
                            logging.info(f"Static trailing profit enabled. Threshold: {TRAILING_PROFIT_THRESHOLD:.4f}")
                      
                        
                        
                        # Ενημέρωση του trailing sell price
                        trailing_sell_price = highest_price * (1 - TRAILING_PROFIT_THRESHOLD)
                        trailing_sell_price = max(trailing_sell_price, active_trade + EXTRA_PROFIT_MARGIN)
                        
                        logging.info(f"Adjusted trailing sell price is {trailing_sell_price:.{current_decimals}f} {CRYPTO_CURRENCY}.")

                        # Έλεγχος αν πρέπει να πουλήσουμε λόγω trailing profit
                        if current_price <= trailing_sell_price:
                            
                            logging.info(f"Trailing profit triggered. Selling at {current_price} {CRYPTO_CURRENCY}.")
                            
                            # Ελέγχουμε αν η 3η θέση υπάρχει και αν ναι, πουλάμε όλες τις θέσεις
                            if third_trade_price or second_trade_price:  # Υπάρχει 2ή ή 3η θέση
                                
                                logging.info(f"There are more positions, selling all positions.")

                                # Καλούμε τη συνάρτηση sell_all_positions() για να πουλήσουμε όλες τις θέσεις
                                sell_all_positions()
                            
                            else:                        
                                # Δεν υπάρχουν αλλές θεσεις - πουλάμε κανονικά μόνο την 1ή                            
                                order_successful, execution_price, fees = place_order("sell", trade_amount, current_price)

                                if order_successful and execution_price:
                                    
                                    # Ενημέρωση daily_profit λαμβάνοντας υπόψη και τα fees
                                    profit_trailing = (execution_price - active_trade) * trade_amount - fees
                                    logging.info(f"The sale was completed with a net profit of {profit_trailing:.2f} {CRYPTO_CURRENCY}.")
                                    
                                    daily_profit += profit_trailing
                                    
                                    # Αποστολή ειδοποιήσεων για την πώληση
                                    sendgrid_email(trade_amount, "sell", execution_price, profit_trailing, "N/A", "Trailing Profit")                            
                                    send_push_notification(
                                        f"ALERT: Trailing Profit Sale was executed for {CRYPTO_NAME} bot at {execution_price} {CRYPTO_CURRENCY}. "
                                        f"The net profit after calculating and subtracting the fees is {profit_trailing:.2f} {CRYPTO_CURRENCY}."
                                    )
                                    
                                    # Ενημέρωση μεταβλητών
                                    active_trade = None
                                    trade_amount = 0
                                    highest_price = None
                                    trailing_profit_active = False
                                    current_trades += 1
                                    save_state()
                                    
                                    
                                    # Χρονική αναμονή μετά την πώληση για αποφυγή άμεσης αγοράς
                                    save_cooldown_state(custom_duration=3600)       #trailing profit 1 hour                     
                                    
                                    
                                    return  # Σταματάμε εδώ αν έγινε πώληση λόγω trailing profit
                                
                                
                                else:
                                    logging.info(f"Failed to execute sell order for trailing profit at {current_price}")           
                                           
                        
                        else:
                            logging.info(f"Trailing profit active. Current price {current_price} has not dropped below trailing sell price {trailing_sell_price:.{current_decimals}f}.")


                    else:
                        # Αν το trailing profit δεν είναι ενεργό και η τιμή δεν έχει φτάσει το scalp target
                        logging.info(f"Waiting for price to reach scalp target at {scalp_target_price:.{current_decimals}f} {CRYPTO_CURRENCY}.")



                except Exception as e:
                    logging.error(f"An error occurred in the trailing profit logic: {e}")
                    send_push_notification(f"ERROR: An issue occurred in the trailing profit logic: {e}")




            # ΠΩΛΗΣΗ 1ης ΘΕΣΗΣ ME TRAILING ΑΠΕΝΕΡΓΟΠΟΙΗΜΕΝΟ -----------------------------------------------------------------------------------------------------------------------------------------------------------------------
            else:
                #logging.info("Trailing profit is disabled.")
                # Υπολογισμός κέρδους πριν αφαιρεθούν τα fees
                potential_profit = (current_price - active_trade) * trade_amount

                # Εκτίμηση των fees για τη συναλλαγή
                estimated_fees = current_price * trade_amount * FEES_PERCENTAGE
                
                if not trailing_profit_second_position_active:
                    logging.info(f"Estimated fees for the trade: {estimated_fees:.{current_decimals}f}")

                # Υπολογισμός καθαρού κέρδους μετά την αφαίρεση των εκτιμώμενων fees
                scalp_profit = potential_profit - estimated_fees

                # Πώληση μόνο αν η τιμή έχει φτάσει το scalp target και το καθαρό κέρδος υπερβαίνει το κατώφλι
                if current_price >= scalp_target_price and scalp_profit >= MINIMUM_PROFIT_THRESHOLD:
                    logging.info(f"Selling at {current_price} for profit (scalp target met and sufficient profit)")
                    

                    # Ελέγχουμε αν υπάρχει 2ή ή 3ή θεση και αν ναι, πουλάμε όλες τις θέσεις
                    if third_trade_price or second_trade_price:  # Υπάρχει 2ή ή 3η θέση
                        logging.info(f"There are more positions, selling all positions.")
                        
                        # Καλούμε τη συνάρτηση sell_all_positions() για να πουλήσουμε όλες τις θέσεις
                        sell_all_positions()

                    else:
                        # Δεν υπάρχουν αλλές θεσεις - πουλάμε κανονικά μόνο την 1ή                
                        order_successful, execution_price, fees = place_order("sell", trade_amount, current_price)

                        if order_successful and execution_price:
                            
                            # Ενημέρωση daily_profit λαμβάνοντας υπόψη τα fees
                            daily_profit += scalp_profit
                            
                            sendgrid_email(trade_amount, "sell", execution_price, scalp_profit, "N/A", "Scalp Target")
                            
                            active_trade = None
                            trade_amount = 0
                            highest_price = None
                            current_trades += 1
                            save_state()
                            
                            # Χρονική αναμονή μετά την πώληση για αποφυγή άμεσης αγοράς
                            save_cooldown_state(custom_duration=3600)       #scalp target 1 hour

                            logging.info("Cooldown initiated to prevent immediate re-buy.")
                            
                            
                            return  # Σταματάει η εκτέλεση εδώ αν γίνει πώληση λόγω scalp target
                        else:
                            logging.info(f"Failed to execute sell order for scalp target at {execution_price}")

                            

                # Δεν πουλάμε ακόμη, συνεχίζουμε να παρακολουθούμε
                logging.info(f"Current price {current_price} has not reached scalp target price {scalp_target_price:.{current_decimals}f} or minimum profit threshold not met.")


            # Καμία πώληση δεν έγινε
            logging.info(f"No sell action taken. Current price {current_price} {CRYPTO_CURRENCY} did not meet any sell criteria.")


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
        macd_last = float(macd.iloc[-1]) if isinstance(macd.iloc[-1], (float, int, str)) else macd
        signal_last = float(signal.iloc[-1]) if isinstance(signal.iloc[-1], (float, int, str)) else signal
        rsi_last = float(rsi.iloc[-1]) if isinstance(rsi.iloc[-1], (float, int, str)) else rsi
        bollinger_upper_last = float(bollinger_upper.iloc[-1]) if isinstance(bollinger_upper.iloc[-1], (float, int, str)) else bollinger_upper
        bollinger_lower_last = float(bollinger_lower.iloc[-1]) if isinstance(bollinger_lower.iloc[-1], (float, int, str)) else bollinger_lower
        vwap_last = float(vwap.iloc[-1]) if isinstance(vwap.iloc[-1], (float, int, str)) else vwap

                                                                  
                                
                
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
                            f"Additional check passed: MA_Short={ma_short_long_period:.{current_decimals}f}, "
                            f"MA_Long={ma_long_long_period:.{current_decimals}f}, MACD={macd_long.iloc[-1]:.{current_decimals}f}, "
                            f"Signal={signal_long.iloc[-1]:.{current_decimals}f}, RSI={rsi_long:.{current_decimals}f}"
                        )

            except Exception as e:
                logging.error(f"Exception occurred during additional checks: {type(e).__name__}: {e}")
                logging.info(
                    "Αποτυχία κατά τον υπολογισμό των δεικτών. Παρακαλούμε ελέγξτε την πηγή των δεδομένων "
                    "και βεβαιωθείτε ότι περιέχουν έγκυρες χρονικές πληροφορίες και επαρκή δεδομένα για επεξεργασία."
                )

                
        # ---------------------------------------




        # Logging για έλεγχο τύπων και τιμών
        logging.info(
            f"Indicators: MACD={macd_last:.{current_decimals}f}, Signal={signal_last:.{current_decimals}f}, "
            f"RSI={rsi_last:.{current_decimals}f}, Bollinger Upper={bollinger_upper_last:.{current_decimals}f}, "
            f"Bollinger Lower={bollinger_lower_last:.{current_decimals}f}, Current Price={current_price:.{current_decimals}f}, "
            f"VWAP={vwap_last:.{current_decimals}f}"
        )





        # ---------------------------------------
        # Σύστημα βαθμολογίας με βάρη
        
        # Βάρη για κάθε δείκτη - ΦΟΡΤΏΝΟΝΤΑΙ ΑΠΟ ΕΞΩΤΕΡΙΚΟ ΑΡΧΕΙΟ JSON
        weights = load_weights(CRYPTO_NAME)
        
        
        

        try:
            # Αρχικοποίηση βαθμολογίας και βαθμολογιών δεικτών
            score = 0
            scores = {}


            #-------------------------------------------------------------------------------------------------------
            # Υπολογισμός MACD
            if macd_last > signal_last:
                if macd_last > 0:
                    # Θετικό MACD, bullish σήμα (πλήρης θετική βαθμολογία)
                    raw_score = 1  # Απόλυτη βαθμολογία πριν την εφαρμογή βαρών
                else:
                    # MACD > Signal αλλά αρνητικό (αδύναμη ανοδική κίνηση)
                    raw_score = 0.3  # Περιορισμένη θετική βαθμολογία
            else:
                # MACD < Signal, bearish σήμα
                raw_score = -1  # Απόλυτη βαθμολογία πριν την εφαρμογή βαρών

            # Εφαρμογή του βάρους στο τελικό σκορ
            scores['macd'] = weights['macd'] * raw_score

            # Προσθήκη στο συνολικό σκορ
            score += scores['macd']

            # logging.info(f"MACD Score: {scores['macd']}")  # Προαιρετικό logging
            #-------------------------------------------------------------------------------------------------------

            
            # Υπολογισμός RSI
            if rsi_last < 20:
                raw_score = 1.5  # Πολύ ισχυρό bullish σήμα (βαθιά υπερπουλημένη ζώνη)
            elif 20 <= rsi_last < 30:
                raw_score = 1  # Ισχυρό bullish σήμα
            elif 30 <= rsi_last < 40:
                raw_score = 0.5  # Αδύναμο bullish σήμα
            elif 40 <= rsi_last <= 60:
                if rsi_last < 50:
                    raw_score = 0.1  # Ελαφρύ bullish bias
                else:
                    raw_score = -0.1  # Ελαφρύ bearish bias
            elif 60 < rsi_last <= 70:
                raw_score = -0.5  # Αδύναμο bearish σήμα
            elif 70 < rsi_last <= 80:
                raw_score = -0.3  # Ασθενές bearish σήμα
            else:  # rsi_last > 80
                raw_score = -0.5  # Πολύ ισχυρό bearish σήμα (βαθιά υπεραγορασμένη ζώνη)

            # Εφαρμογή βάρους στο σκορ RSI
            scores['rsi'] = weights['rsi'] * raw_score

            # Προσθήκη στο συνολικό σκορ
            score += scores['rsi']

            # Προαιρετικό Logging
            logging.info(f"RSI Last: {rsi_last:.2f}, Raw Score: {raw_score:.2f}, Weighted Score: {scores['rsi']:.2f}")


            
            #-------------------------------------------------------------------------------------------------------


            # Υπολογισμός Bollinger Bands
            mid_band = (bollinger_lower_last + bollinger_upper_last) / 2
            band_width = bollinger_upper_last - bollinger_lower_last

            if current_price <= bollinger_lower_last:
                if current_price < bollinger_lower_last * 0.98:
                    raw_score = 1.5  # Πολύ κάτω από την κάτω μπάντα (ισχυρό bullish)
                else:
                    raw_score = 1  # Κάτω από την κάτω μπάντα
            elif current_price >= bollinger_upper_last:
                if current_price > bollinger_upper_last * 1.02:
                    raw_score = -0.5  # Πολύ πάνω από την άνω μπάντα (ισχυρό bearish)
                else:
                    raw_score = -0.3  # Λίγο πάνω από την άνω μπάντα (ασθενές bearish)
            elif abs(current_price - mid_band) <= band_width * 0.1:
                raw_score = 0  # Κοντά στη μεσαία γραμμή (ουδέτερη ζώνη)
            elif current_price < mid_band:
                raw_score = 0.5  # Κοντά στην κάτω μπάντα (ασθενές bullish)
            else:
                raw_score = -0.5  # Κοντά στην άνω μπάντα (ασθενές bearish)

            # Εφαρμογή βάρους στο σκορ Bollinger Bands
            scores['bollinger'] = weights['bollinger'] * raw_score

            # Προσθήκη στο συνολικό σκορ
            score += scores['bollinger']

            # logging.info(f"Bollinger Score: {scores['bollinger']}")


            #-------------------------------------------------------------------------------------------------------


            # Υπολογισμός ποσοστιαίας απόκλισης από το VWAP
            vwap_diff = abs(current_price - vwap_last) / vwap_last  

            if current_price > vwap_last:
                if vwap_diff > 0.05:  # Τιμή >5% πάνω από το VWAP
                    raw_score = 0.3  # Πολύ μικρό bullish σήμα λόγω υπερεκτεταμένης τιμής
                elif vwap_diff > 0.03:  # Τιμή 3-5% πάνω από το VWAP
                    raw_score = 0.5  # Ασθενές bullish σήμα
                else:  # Τιμή <3% πάνω από το VWAP
                    raw_score = 1  # Ισχυρό bullish σήμα
            elif current_price < vwap_last:
                if vwap_diff > 0.05:  # Τιμή >5% κάτω από το VWAP
                    raw_score = -0.3  # Πολύ μικρό bearish σήμα
                elif vwap_diff > 0.03:  # Τιμή 3-5% κάτω από το VWAP
                    raw_score = -0.5  # Ασθενές bearish σήμα
                else:  # Τιμή <3% κάτω από το VWAP
                    raw_score = -1  # Ισχυρό bearish σήμα
            else:
                raw_score = 0  # Πολύ κοντά στο VWAP, ουδέτερη ζώνη

            # Εφαρμογή βάρους στο σκορ VWAP
            scores['vwap'] = weights['vwap'] * raw_score

            # Προσθήκη στο συνολικό σκορ
            score += scores['vwap']
            

            #-------------------------------------------------------------------------------------------------------
          
            
            score = round(score, 2)         
                      
            logging.info(f"Current Price: {current_price}, VWAP: {vwap_last:.2f}, VWAP Diff: {vwap_diff:.2f}, Raw Score: {raw_score}")

           

            # Στρογγυλοποίηση όλων των τιμών στο Score Analysis
            rounded_scores = {key: round(value, 2) for key, value in scores.items()}                      
            
            
            # Συγκεντρωτικό logging
            logging.info(f"Score Analysis: {rounded_scores}, Total Score: {score:.2f}")
            logging.debug(f"Score history before append: {[round(score, 2) for score in score_history]}")



            #-------------------------------------------------------------------------------------------------------      


            # Αποθήκευση τιμών και σκορ σε excel
            if ENABLE_SAVE_TO_CSV:
                save_to_csv(csv_file_path, CRYPTO_NAME, current_price, score, scores)



            
            #Αναλυτικό μήνυμα για το συνολικό score και το score history.
            if ENABLE_SCORE_HISTORY:
                logging.info(f"Total Score for this round: {score:.2f}. Score History is activated.")
            
            
                # Προσθήκη νέου score στο score_history
                score_history.append(score)

                # Διατήρηση μόνο των τελευταίων MAX_SCORE_HISTORY τιμών
                if len(score_history) > MAX_SCORE_HISTORY:
                    score_history.pop(0)              

            
            else:
                logging.info(f"Total Score for this round: {score:.2f}")
            
            
      

              
            if ENABLE_TABULATE_INDICATORS:
                # Δημιουργία πίνακα με τα αποτελέσματα
                table_data = [
                    ["MACD", macd_last, "MACD > Signal" if macd_last > signal_last else "MACD < Signal", weights['macd'], scores['macd']],
                    ["RSI", rsi_last, "RSI > 30" if rsi_last > RSI_THRESHOLD else "RSI < 30", weights['rsi'], scores['rsi']],
                    ["Bollinger", current_price, "Current Price < Bollinger Lower" if current_price <= bollinger_lower_last
                        else "Current Price > Bollinger Upper" if current_price >= bollinger_upper_last
                        else "Inside Bands", weights['bollinger'], scores['bollinger']],
                    ["VWAP", current_price, "Current Price > VWAP" if current_price > vwap_last else "Current Price < VWAP",
                     weights['vwap'], scores['vwap']],
                    ["Total Score", "", "", "", round(score, 3)]
                ]

                # Format table
                table = tabulate(table_data, headers=["Indicator", "Value", "Condition", "Weight", "Score"], tablefmt="pretty")

                # Log table
                logging.info("\n" + table)

                # Logging της συνολικής βαθμολογίας
                logging.info(f"Total Score: {score:.{current_decimals}f}")




        except TypeError as e:
            logging.error(f"TypeError occurred during score calculation: {e}")
            logging.error(f"Values - MACD Last: {macd_last}, Signal Last: {signal_last}, "
                          f"RSI Last: {rsi_last}, Bollinger Upper: {bollinger_upper_last}, "
                          f"Bollinger Lower: {bollinger_lower_last}, VWAP: {vwap_last}")
            return False, None



        # ---------------------------------------

        # ---------------------------------------
        
        # Αγοραστικό σήμα #############################################################################################################################################################################################
        # Πρώτος έλεγχος για βασικούς δείκτες
        
        # attention: score_history is loaded from json file while scripts starts...
        
        # Logging του score_history για έλεγχο των τιμών
        logging.debug(f"Score history for decision: {[round(score, 2) for score in score_history]}")

        
        if ENABLE_SCORE_HISTORY:        
            if len(score_history) == MAX_SCORE_HISTORY and sum(score >= BUY_THRESHOLD for score in score_history) >= POSITIVE_THRESHOLD:
                
                # Εξαγωγή του υπολοίπου του χαρτοφυλακίου
                portfolio_summary = get_portfolio_balance(portfolio_uuid)  # Υποθέτουμε ότι έχεις το portfolio_uuid
                if "error" not in portfolio_summary:
                    available_cash = portfolio_summary['total_cash_equivalent_balance']

                    amount_needed_to_buy = TRADE_AMOUNT * current_price
                    logging.info(f"Available cash in portfolio: {available_cash:.2f} EUR, Amount needed: {amount_needed_to_buy:.2f} EUR ")

                    # Έλεγχος αν το ποσό της αγοράς επαρκεί
                    if amount_needed_to_buy <= available_cash:
                        logging.info(f"Sufficient funds available ({available_cash:.2f} EUR). Executing Buy Order.")
                        order_successful, execution_price, fees = place_order("buy", TRADE_AMOUNT, current_price)

                        if order_successful and execution_price:
                            active_trade = execution_price  # Ενημέρωση της ανοιχτής θέσης με την τιμή εκτέλεσης
                            trade_amount = TRADE_AMOUNT  # Καταχώρηση του ποσού συναλλαγής
                            logging.info(f"Order placed successfully at price: {execution_price:.{current_decimals}f} with fees: {fees:.{current_decimals}f}")
                            
                            # Προσθήκη των fees στο daily_profit                
                            daily_profit -= fees  # Αφαιρούμε τα fees από το daily_profit για ακριβή υπολογισμό του κόστους
                                          
                            # Δημιουργία του reasoning ως string για χρήση στην κλήση της sendgrid
                            reasoning = (
                                f"Indicators: MACD={round(macd_last, 3)}, Signal={round(signal_last, 3)}, "
                                f"RSI={round(rsi_last, 3)}, Bollinger Upper={round(bollinger_upper_last, 3)}, "
                                f"Bollinger Lower={round(bollinger_lower_last, 3)}, "
                                f"VWAP={round(vwap_last, 3)}")
                            
                            # Δημιουργία του final_score ως string για χρήση στην κλήση της sendgrid
                            final_score = f"Trade signal score is positive: {round(score, 3)}."
                            
                            # Κλήση της συνάρτησης για αποστολή email πριν μηδενιστούν οι τιμές
                            sendgrid_email(trade_amount, "buy", execution_price, fees, final_score, reasoning)
                            
                            highest_price = execution_price
                            current_trades += 1
                            save_state()  # Αποθήκευση της κατάστασης μετά την αγορά
                        else:
                            logging.info(f"Order placement failed. No buy action taken.")
                    else:
                        logging.warning(f"Insufficient funds. Needed: {amount_needed_to_buy:.2f} EUR, Available: {available_cash:.2f} EUR")
                        send_push_notification(
                            f"ALERT: Insufficient funds for {CRYPTO_NAME} bot. Needed: {amount_needed_to_buy:.2f} EUR, Available: {available_cash:.2f} EUR. This alert originates from the score history block. Please ensure sufficient funds as this message will appear every 2 minutes.",
                            Logfile=False
                        )                        
                        return
                        
                else:
                    logging.error(f"Failed to retrieve portfolio balance. No buy action taken.")
                    logging.error(f"Error details: {portfolio_summary['message']}")
            else:
                logging.info(f"Trade Score history {[round(score, 2) for score in score_history]} was below the buy threshold ({BUY_THRESHOLD})")
                logging.info(f"Score not consistently above threshold; No action taken.")
                save_state()  # Αποθήκευση της κατάστασης
                

        else:
            if score >= BUY_THRESHOLD:
                logging.info(f"Trade signal score is positive: {score:.2f}. Proceeding to volume confirmation check before initiating a buy at {current_price}.")
                logging.info(f"Checking Volume Confirmation...")
                
                # Ενημέρωση για θετική τιμή σε silent mode
                #send_push_notification(f"ALERT: Positive score detected: {score:.2f} for {CRYPTO_NAME} bot. Proceeding to volume confirmation check before initiating a buy at {current_price}.", Logfile=False)

                # Έλεγχος επιβεβαίωσης όγκου πριν την αγορά
                volume_confirmation, current_volume, avg_volume = calculate_volume_confirmation(df, window=30)
                
                
                if not volume_confirmation:
                    logging.info(f"Volume confirmation failed. Current Volume: {current_volume}, Average Volume: {avg_volume:.2f}")
                    logging.info(f"Checking fallback conditions ATR and Stochastic")

                    # Κλήση της fallback συνάρτησης
                    if fallback_conditions(df):
                        logging.info("Fallback conditions met. Proceeding with buy action despite failed volume confirmation.")
                        
                        # Κλήση execute_buy_action αν οι fallback συνθήκες πληρούνται
                        success, reason = execute_buy_action(
                            df=df,
                            portfolio_uuid=portfolio_uuid,
                            TRADE_AMOUNT=TRADE_AMOUNT,
                            current_price=current_price,
                            macd_last=macd_last,
                            signal_last=signal_last,
                            rsi_last=rsi_last,
                            bollinger_upper_last=bollinger_upper_last,
                            bollinger_lower_last=bollinger_lower_last,
                            vwap_last=vwap_last,
                            score=score,
                            current_decimals=current_decimals
                        )
                        
                        
                        if success:
                            logging.info("Buy action completed via fallback conditions.")
                            
                            # Send push notification
                            send_push_notification(
                                f"Buy action executed under fallback conditions for the {CRYPTO_NAME} bot. "
                                f"The decision was made following positive confirmation from ATR and Stochastic indicators, "
                                f"despite a lack of volume confirmation. "
                                f"This strategic move aligns with the fallback logic to seize potential opportunities in the market."
                            )

                        else:
                            logging.warning(f"Buy action failed via fallback conditions. Reason: {reason}")
                        return  # Τερματισμός της εκτέλεσης
                    
                    else:
                        logging.info("Fallback conditions not met. Buy action skipped.")
                        return  # Τερματισμός της εκτέλεσης

                logging.info(f"Volume confirmation passed. Current Volume: {current_volume}, Average Volume: {avg_volume:.2f}")
                
                # Εξαγωγή του υπολοίπου του χαρτοφυλακίου
                portfolio_summary = get_portfolio_balance(portfolio_uuid)  # Υποθέτουμε ότι έχεις το portfolio_uuid
                if "error" not in portfolio_summary:
                    available_cash = portfolio_summary['total_cash_equivalent_balance']                    
                    
                    amount_needed_to_buy = TRADE_AMOUNT * current_price
                    logging.info(f"Available cash in portfolio: {available_cash:.2f} EUR, Amount needed: {amount_needed_to_buy:.2f} EUR ")

                    # Έλεγχος αν το ποσό της αγοράς επαρκεί
                    if amount_needed_to_buy <= available_cash:
                        logging.info(f"Sufficient funds available. Executing Buy Order.")
                        order_successful, execution_price, fees = place_order("buy", TRADE_AMOUNT, current_price)

                        if order_successful and execution_price:
                            active_trade = execution_price  # Ενημέρωση της ανοιχτής θέσης με την τιμή εκτέλεσης
                            trade_amount = TRADE_AMOUNT  # Καταχώρηση του ποσού συναλλαγής
                            logging.info(f"Order placed successfully at price: {execution_price:.{current_decimals}f} with fees: {fees:.{current_decimals}f}")

                            # Προσθήκη των fees στο daily_profit                
                            daily_profit -= fees  # Αφαιρούμε τα fees από το daily_profit για ακριβή υπολογισμό του κόστους

                            # Δημιουργία του reasoning ως string για χρήση στην κλήση της sendgrid
                            reasoning = (
                                f"Indicators: MACD={round(macd_last, 3)}, Signal={round(signal_last, 3)}, "
                                f"RSI={round(rsi_last, 3)}, Bollinger Upper={round(bollinger_upper_last, 3)}, "
                                f"Bollinger Lower={round(bollinger_lower_last, 3)}, "
                                f"VWAP={round(vwap_last, 3)}")
                            
                            # Δημιουργία του final_score ως string για χρήση στην κλήση της sendgrid
                            final_score = f"Trade signal score is positive: {round(score, 3)}."
                            
                            # Κλήση της συνάρτησης για αποστολή email πριν μηδενιστούν οι τιμές
                            sendgrid_email(trade_amount, "buy", execution_price, fees, final_score, reasoning)

                            highest_price = execution_price
                            current_trades += 1
                            save_state()  # Αποθήκευση της κατάστασης μετά την αγορά
                        else:
                            logging.info(f"Order placement failed. No buy action taken.")
                    else:
                        logging.warning(f"Insufficient funds. Needed: {amount_needed_to_buy:.2f} EUR, Available: {available_cash:.2f} EUR")
                        send_push_notification(
                            f"ALERT: Insufficient funds for {CRYPTO_NAME} bot. Needed: {amount_needed_to_buy:.2f} EUR, Available: {available_cash:.2f} EUR. This alert originates from the volume confirmation block. Please ensure sufficient funds as this message will appear every 2 minutes.",
                            Logfile=False
                        )
                        return
                        
                else:
                    logging.error(f"Failed to retrieve portfolio balance. No buy action taken.")
                    logging.error(f"Error details: {portfolio_summary['message']}")
            else:
                logging.info(f"Trade signal score ({score:.2f}) was below the buy threshold ({BUY_THRESHOLD}). No action taken.")



        # Έλεγχος αν επιτεύχθηκε το καθημερινό κέρδος ή το όριο συναλλαγών
        if daily_profit >= DAILY_PROFIT_TARGET or current_trades >= MAX_TRADES_PER_DAY:
            logging.info(
                f"Daily profit target reached: {daily_profit:.2f} or maximum trades executed."
            )
            
            logging.info(f"The bot has been stopped. Push notification has been sent.")
            
            # Αποστολή Push Notification #####################################
            send_push_notification(f"Alert: The bot has been stopped. Daily profit target reached ({DAILY_PROFIT_TARGET} {CRYPTO_CURRENCY}) for {CRYPTO_NAME} bot.")
                       
            start_bot = False
            save_state(log_info=False)  # Αποθήκευση κατάστασης όταν σταματάει το bot

    except Exception as e:
        logging.error(f"Exception occurred in execute_scalping_trade: {type(e).__name__}: {e}")
        return
        
        
        # ---------------------------------------


# Main loop (updated to load state)
def run_bot():
    logging.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    logging.info(f"Starting {CRYPTO_FULLNAME} ({CRYPTO_NAME}) bot...")
    
    iteration_start = time.time()    
    

    # Check for URGENT SELL ALL signal (macro call via excel)
    if check_sell_all_signal():
        logging.info("Bot execution stopped for this round due to sell ALL signal.")
        return  # Stop bot execution for this round


    # Check for URGENT sell signal at the beginning (macro call via excel)
    if check_sell_signal():
        logging.info("Bot execution stopped for this round due to sell signal.")
        return  # Stop bot execution for this round
        

    # Check for URGENT buy signal at the beginning (macro call via excel)
    if check_buy_signal():
        logging.info("Bot execution stopped for this round due to buy signal.")
        return  # Stop bot execution for this round        
   
   
    # Check if the bot is allowed to run
    load_state()  # Load the state to check start_bot status
 
 
    #------------------------------------------------------------------------------------------------------------------
    
    if ENABLE_FAILOVER_BOT:
        # Φόρτωση της απόφασης από το JSON file    
        decision = load_decision()
        logging.info(f"Decision from failover bot: {decision}")
        
        # Check decision from failover bot
        if decision != "Buy" and active_trade == 0:  
            current_price = get_crypto_price()
            
            logging.info("Scalping bot is paused because the decision is not 'Buy' and there are no active trades. Exiting this round.")
            logging.info("Bot execution completed.")
            return
        
    #------------------------------------------------------------------------------------------------------------------     
    
    
    if not start_bot:

        current_price = get_crypto_price()
        if current_price is None:
            logging.error("Failed to fetch current price. Skipping trade execution.")

        logging.info("Bot is paused. Exiting this round.")        
        return  # Stop the bot from executing this round if start_bot is False    
    
  
    execute_scalping_trade(CRYPTO_SYMBOL) 
    
    # Μετά την ολοκλήρωση του iteration
    iteration_end = time.time()
    logging.info(f"Bot execution completed in {iteration_end - iteration_start:.2f} seconds.")    
    


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