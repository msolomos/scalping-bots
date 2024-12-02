from flask import Flask, render_template, jsonify
import json
import os
import logging
import requests

# Import static variables from scalper.py
from scalper_ethereum import (
    SCALP_TARGET, STOP_LOSS, TRADE_AMOUNT, short_ma_period, long_ma_period, 
    RSI_THRESHOLD, TRAILING_PROFIT_THRESHOLD, DAILY_PROFIT_TARGET, MAX_TRADES_PER_DAY
)

app = Flask(__name__)


# Απενεργοποίηση της χρήσης του root logger από το Flask
log = logging.getLogger('werkzeug')  # Ο logger που χρησιμοποιεί το Flask για τα requests
log.disabled = True  # Απενεργοποίηση του werkzeug logger

# Δημιουργία νέου console-only logger για το Flask
console_handler = logging.StreamHandler()  # Καταγραφή στην κονσόλα
console_handler.setLevel(logging.INFO)  # Επίπεδο logging (info, debug, warning, error)
formatter = logging.Formatter('%(asctime)s - %(message)s')
console_handler.setFormatter(formatter)

# Καθαρίζουμε τους υπάρχοντες handlers και προσθέτουμε μόνο τον console handler
app.logger.handlers = [console_handler]
app.logger.setLevel(logging.INFO)



# Path to the state file and log file
state_file = "/opt/python/scalping-bot/state.json"
log_file = "/opt/python/scalping-bot/scalping_bot.log"



# Συνάρτηση για να ανακτήσουμε την τιμή του Ethereum από το Coinbase API
def get_eth_price():
    url = "https://api.coinbase.com/v2/prices/ETH-EUR/spot"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        eth_price = data['data']['amount']
        return eth_price
    else:
        return None   




@app.route('/')
def dashboard():
    # Load the state variables
    state_data = load_state()
    
    return render_template('dashboard.html', state_data=state_data)

@app.route('/get_variables')
def get_variables():
    # Return the imported static variables from scalper.py
    static_variables = {
        'SCALP_TARGET': SCALP_TARGET,
        'STOP_LOSS': STOP_LOSS,
        'TRADE_AMOUNT': TRADE_AMOUNT,
        'short_ma_period': short_ma_period,
        'long_ma_period': long_ma_period,
        'RSI_THRESHOLD': RSI_THRESHOLD,
        'TRAILING_PROFIT_THRESHOLD': TRAILING_PROFIT_THRESHOLD,
        'DAILY_PROFIT_TARGET': DAILY_PROFIT_TARGET,
        'MAX_TRADES_PER_DAY': MAX_TRADES_PER_DAY
    }
    return jsonify(static_variables)

@app.route('/get_logs')
def get_logs():
    # Επιστροφή των τελευταίων 20 γραμμών με trim στο μήκος κάθε γραμμής
    max_length = 100  # Καθορισμός του μέγιστου μήκους γραμμής
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            logs = f.readlines()
        last_logs = []
        for line in logs[-20:]:
            trimmed_line = line[:max_length].strip()  # Κόψιμο της γραμμής στο max_length
            if len(line) > max_length:
                trimmed_line += " (trimmed)"  # Προσθήκη του μηνύματος (trimmed) αν έχει κοπεί
            last_logs.append(trimmed_line)
        return jsonify(last_logs)
    else:
        return jsonify([])




def load_state():
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            state_data = json.load(f)
        return state_data
    return {}
    

@app.route('/get_state_file_data')
def get_state_file_data():
    state_data = load_state()
    
    # Στρογγυλοποίηση της μεταβλητής daily_profit σε 2 δεκαδικά
    if 'daily_profit' in state_data:
        state_data['daily_profit'] = round(state_data['daily_profit'], 2)
    
    return jsonify(state_data)


# Νέο route για την τιμή του Ethereum
@app.route('/api/eth_price')
def api_eth_price():
    eth_price = get_eth_price()
    if eth_price:
        return jsonify({"eth_price": eth_price})
    else:
        return jsonify({"error": "Unable to fetch ETH price"}), 500
 

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5015)

