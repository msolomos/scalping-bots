from flask import Flask, jsonify, request, render_template
import json
import os
import re
import logging




app = Flask(__name__)



# Διαδρομή του log αρχείου
log_file_path = "/opt/python/scalping-bot/webhook.log"

# Δημιουργία του φακέλου, αν δεν υπάρχει
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

# Δημιουργία του log αρχείου, αν δεν υπάρχει
if not os.path.exists(log_file_path):
    open(log_file_path, 'a').close()

# Δημιουργία custom logger
logger = logging.getLogger("webhook_logger")
logger.setLevel(logging.INFO)

# Ρύθμιση File Handler
file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)

# Ρύθμιση Formatter
formatter = logging.Formatter("%(asctime)s - %(message)s")
file_handler.setFormatter(formatter)

# Προσθήκη Handler στον Logger
logger.addHandler(file_handler)


# Paths to JSON files and Euro pairs for each cryptocurrency
crypto_info = {
    'AVAX': {'path': '/opt/python/scalping-bot/AVAX/state.json', 'euro_pair': 'AVAX-EUR'},
    'SOLANA': {'path': '/opt/python/scalping-bot/SOLANA/state.json', 'euro_pair': 'SOL-EUR'},
    'LITECOIN': {'path': '/opt/python/scalping-bot/LITECOIN/state.json', 'euro_pair': 'LTC-EUR'},
    'ETHEREUM': {'path': '/opt/python/scalping-bot/ETHEREUM/state.json', 'euro_pair': 'ETH-EUR'},
    'BITCOIN': {'path': '/opt/python/scalping-bot/BITCOIN/state.json', 'euro_pair': 'BTC-EUR'},
    'XRP': {'path': '/opt/python/scalping-bot/XRP/state.json', 'euro_pair': 'XRP-EUR'},
    'CARDANO': {'path': '/opt/python/scalping-bot/CARDANO/state.json', 'euro_pair': 'ADA-EUR'},
    'POLKADOT': {'path': '/opt/python/scalping-bot/POLKADOT/state.json', 'euro_pair': 'DOT-EUR'},
    'DOGECOIN': {'path': '/opt/python/scalping-bot/DOGECOIN/state.json', 'euro_pair': 'DOGE-EUR'},      #new bot
    'POLYGON': {'path': '/opt/python/scalping-bot/POLYGON/state.json', 'euro_pair': 'MATIC-EUR'},       #new bot
    'STELLAR': {'path': '/opt/python/scalping-bot/STELLAR/state.json', 'euro_pair': 'XLM-EUR'}          #new bot
}



# Paths to the Python scripts for each bot
crypto_path_files = {
    'AVAX': {'path': '/opt/python/scalping-bot/AVAX/scalper_avax.py'},
    'SOLANA': {'path': '/opt/python/scalping-bot/SOLANA/scalper_solana.py'},
    'LITECOIN': {'path': '/opt/python/scalping-bot/LITECOIN/scalper_litecoin.py'},
    'ETHEREUM': {'path': '/opt/python/scalping-bot/ETHEREUM/scalper_ethereum.py'},
    'BITCOIN': {'path': '/opt/python/scalping-bot/BITCOIN/scalper_bitcoin.py'},
    'XRP': {'path': '/opt/python/scalping-bot/XRP/scalper_xrp.py'},
    'CARDANO': {'path': '/opt/python/scalping-bot/CARDANO/scalper_ada.py'},
    'POLKADOT': {'path': '/opt/python/scalping-bot/POLKADOT/scalper_dot.py'},
    'DOGECOIN': {'path': '/opt/python/scalping-bot/DOGECOIN/scalper_dogecoin.py'},      #new bot
    'POLYGON': {'path': '/opt/python/scalping-bot/POLYGON/scalper_polygon.py'},          #new bot
    'STELLAR': {'path': '/opt/python/scalping-bot/STELLAR/scalper_stellar.py'}          #new bot
}


# Ορισμός των paths των log αρχείων
BOT_PATHS = {
    "AVAX": "/opt/python/scalping-bot/AVAX/AVAX_bot.log",
    "BTC": "/opt/python/scalping-bot/BITCOIN/BTC_bot.log",
    "ADA": "/opt/python/scalping-bot/CARDANO/ADA_bot.log",
    "ETH": "/opt/python/scalping-bot/ETHEREUM/ETH_bot.log",
    "LTC": "/opt/python/scalping-bot/LITECOIN/LTC_bot.log",
    "DOT": "/opt/python/scalping-bot/POLKADOT/DOT_bot.log",
    "SOL": "/opt/python/scalping-bot/SOLANA/SOL_bot.log",
    "XRP": "/opt/python/scalping-bot/XRP/XRP_bot.log",
    "DOGE": "/opt/python/scalping-bot/DOGECOIN/DOGE_bot.log",
    "MATIC": "/opt/python/scalping-bot/POLYGON/MATIC_bot.log",
}



# Define the static variables to read and update
static_vars = [
    'SCALP_TARGET', 'BUY_THRESHOLD', 'RSI_THRESHOLD', 'ENABLE_STOP_LOSS', 'STOP_LOSS', 'ENABLE_TRAILING_PROFIT',
    'STATIC_TRAILING_PROFIT_THRESHOLD', 'MINIMUM_PROFIT_THRESHOLD', 'SELL_ON_TRAILING', 'DAILY_PROFIT_TARGET'
]





@app.route('/api/crypto-info', methods=['GET'])
def get_crypto_info():
    data = []
    for name, info in crypto_info.items():
        path = info['path']
        euro_pair = info['euro_pair']
        if os.path.exists(path):
            with open(path, 'r') as file:
                file_data = json.load(file)
                data.append({
                    "name": name,
                    "start_bot": file_data.get("start_bot", None),  # Αν δεν υπάρχει το κλειδί, αφήνει κενό
                    "manual_third_buy": file_data.get("manual_third_buy", None),  # Προσθήκη manual_third_buy
                    "active_trade": file_data.get("active_trade"),
                    "trade_amount": file_data.get("trade_amount"),
                    "second_trade_price": file_data.get("second_trade_price"),
                    "second_trade_amount": file_data.get("second_trade_amount"),
                    "third_trade_price": file_data.get("third_trade_price"),
                    "third_trade_amount": file_data.get("third_trade_amount"),                       
                    "euro_pair": euro_pair
                })
        else:
            # Αν το αρχείο δεν υπάρχει, προσθέτουμε κενές τιμές
            data.append({
                "name": name,
                "start_bot": None,
                "manual_third_buy": None,  # Προσθήκη manual_third_buy
                "active_trade": None,
                "trade_amount": None,
                "second_trade_price": None,
                "second_trade_amount": None,
                "third_trade_price": None,
                "third_trade_amount": None,                
                "euro_pair": euro_pair
            })
    return jsonify(data)


# Νέο endpoint για πώληση της ανοιχτής θέσης ενός συγκεκριμένου bot
@app.route('/api/sell_position', methods=['POST'])
def sell_position():
    data = request.json
    bot_name = data.get("name")  # Λαμβάνει το όνομα του bot, π.χ., "AVAX"
    
    # Ελέγχει αν το bot υπάρχει στο crypto_info dictionary
    if bot_name in crypto_info:
        # Λήψη του μονοπατιού του bot από το dictionary
        bot_folder = os.path.dirname(crypto_info[bot_name]['path'])
        signal_file = os.path.join(bot_folder, "sell_signal.txt")
        
        # Δημιουργία του αρχείου σήματος πώλησης
        with open(signal_file, "w") as f:
            f.write("SELL")
        
        return jsonify({"status": "success", "message": f"Πώληση για το bot {bot_name} ζητήθηκε επιτυχώς."})
    else:
        return jsonify({"status": "error", "message": f"Το bot '{bot_name}' δεν βρέθηκε."}), 404
        
        
        


# Νέο endpoint για αγορά θέσης για συγκεκριμένο bot
@app.route('/api/buy_position', methods=['POST'])
def buy_position():
    data = request.json
    bot_name = data.get("name")  # Λαμβάνει το όνομα του bot, π.χ., "AVAX"
    
    # Ελέγχει αν το bot υπάρχει στο crypto_info dictionary
    if bot_name in crypto_info:
        # Λήψη του μονοπατιού του bot από το dictionary
        bot_folder = os.path.dirname(crypto_info[bot_name]['path'])
        signal_file = os.path.join(bot_folder, "buy_signal.txt")
        
        # Δημιουργία του αρχείου σήματος αγοράς
        with open(signal_file, "w") as f:
            f.write("BUY")
        
        return jsonify({"status": "success", "message": f"Αγορά για το bot {bot_name} ζητήθηκε επιτυχώς."})
    else:
        return jsonify({"status": "error", "message": f"Το bot '{bot_name}' δεν βρέθηκε."}), 404
        
        
        

# Νέο endpoint για πώληση όλων των θέσεων ενός συγκεκριμένου bot
@app.route('/api/sell_all_positions', methods=['POST'])
def sell_all_positions():
    data = request.json
    if not data:
        logging.error("No JSON data received.")
        return jsonify({"status": "error", "message": "Invalid or missing JSON data."}), 400    
    
    
    bot_name = data.get("name")  # Λαμβάνει το όνομα του bot, π.χ., "AVAX"
    if not bot_name:
        logging.error("Missing 'name' in JSON data.")
        return jsonify({"status": "error", "message": "Missing 'name' in JSON data."}), 400    
    
    
    # Ελέγχει αν το bot υπάρχει στο crypto_info dictionary
    if bot_name in crypto_info:
        # Λήψη δεδομένων για το bot
        bot_info_path = crypto_info[bot_name]['path']
        
        # Φόρτωση του αρχείου JSON με τις θέσεις
        try:
            with open(bot_info_path, "r") as f:
                bot_data = json.load(f)
        except FileNotFoundError:
            return jsonify({"status": "error", "message": f"The data file for bot '{bot_name}' was not found."}), 404
        except json.JSONDecodeError:
            return jsonify({"status": "error", "message": f"The data file for bot '{bot_name}' is not valid."}), 500
        
        # Υπολογισμός συνολικής ποσότητας προς πώληση
        total_amount_to_sell = bot_data.get("trade_amount", 0) + \
                               bot_data.get("second_trade_amount", 0) + \
                               bot_data.get("third_trade_amount", 0)
        
        if total_amount_to_sell > 0:
            # Δημιουργία του αρχείου σήματος πώλησης
            bot_folder = os.path.dirname(bot_info_path)
            signal_file = os.path.join(bot_folder, "sell_all_signal.txt")
            
            with open(signal_file, "w") as f:
                f.write("SELL_ALL")
            
            return jsonify({
                "status": "success",
                "message": f"Sell all positions for bot '{bot_name}' was successfully requested.",
                "total_amount_to_sell": total_amount_to_sell
            })
        else:
            return jsonify({"status": "error", "message": f"Bot '{bot_name}' has no active positions to sell."}), 400
    else:
        return jsonify({"status": "error", "message": f"Bot '{bot_name}' not found."}), 404
        
        


# Endpoint to enable manual third buy for a specific bot
@app.route('/api/manual_third_buy', methods=['POST'])
def manual_third_buy():
    data = request.json
    bot_name = data.get("name")

    if bot_name in crypto_info:
        state_file_path = crypto_info[bot_name]['path']

        try:
            with open(state_file_path, 'r+') as f:
                state = json.load(f)
                state['manual_third_buy'] = True  # Set to enable manual third buy

                # Write changes back to the file
                f.seek(0)
                json.dump(state, f, indent=4)
                f.truncate()
            
            # Logging for success
            app.logger.info(f"Manual third buy enabled for bot {bot_name}.")

            return jsonify({"status": "success", "message": f"Manual third buy enabled for bot {bot_name}."})
        
        except Exception as e:
            # Logging for error
            app.logger.error(f"Error updating state file for bot {bot_name}: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500

    else:
        # Logging for bot not found
        app.logger.warning(f"Bot '{bot_name}' not found.")
        return jsonify({"status": "error", "message": f"Bot '{bot_name}' not found."}), 404




# Νέο endpoint για ακύρωση σήματος πώλησης
@app.route('/api/cancel_sell_signal', methods=['POST'])
def cancel_sell_signal():
    data = request.json
    bot_name = data.get("name")  # Λαμβάνει το όνομα του bot, π.χ., "AVAX"
    
    # Ελέγχει αν το bot υπάρχει στο crypto_info dictionary
    if bot_name in crypto_info:
        # Λήψη του μονοπατιού του bot από το dictionary
        bot_folder = os.path.dirname(crypto_info[bot_name]['path'])
        signal_file = os.path.join(bot_folder, "sell_signal.txt")
        
        # Διαγραφή του αρχείου σήματος πώλησης, αν υπάρχει
        if os.path.exists(signal_file):
            os.remove(signal_file)
            return jsonify({"status": "success", "message": f"Το σήμα πώλησης για το bot {bot_name} ακυρώθηκε επιτυχώς."})
        else:
            return jsonify({"status": "warning", "message": f"Δεν υπάρχει σήμα πώλησης για το bot {bot_name}."})
    else:
        return jsonify({"status": "error", "message": f"Το bot '{bot_name}' δεν βρέθηκε."}), 404





# Endpoint to start a specific bot
@app.route('/api/start_bot', methods=['POST'])
def start_bot():
    data = request.json
    bot_name = data.get("name")

    if bot_name in crypto_info:
        state_file_path = crypto_info[bot_name]['path']

        try:
            with open(state_file_path, 'r+') as f:
                state = json.load(f)
                state['start_bot'] = True  # Set to start the bot

                # Write changes back to the file
                f.seek(0)
                json.dump(state, f, indent=4)
                f.truncate()
                
            return jsonify({"status": "success", "message": f"Bot {bot_name} started successfully."})
        
        except Exception as e:
            print(f"Error updating state file for bot {bot_name}: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500

    else:
        return jsonify({"status": "error", "message": f"Bot '{bot_name}' not found."}), 404
        

        


# Endpoint to pause a specific bot
@app.route('/api/pause_bot', methods=['POST'])
def pause_bot():
    data = request.json
    bot_name = data.get("name")  # Name of the bot to pause, e.g., "AVAX"
    
    # Log the bot_name received
    print(f"Received bot name for pausing: {bot_name}")

    # Check if the bot name exists in the dictionary
    if bot_name in crypto_info:
        state_file_path = crypto_info[bot_name]['path']  # Access the path key within the dictionary

        # Check if the state file exists before proceeding
        if not os.path.exists(state_file_path):
            return jsonify({"status": "error", "message": f"State file for bot '{bot_name}' not found."}), 500

        # Load the current state, update start_bot to False (or add it if missing), and save
        try:
            with open(state_file_path, 'r+') as f:
                state = json.load(f)
                
                # Check if start_bot exists; if not, add it
                if "start_bot" not in state:
                    print(f"'start_bot' key not found in {bot_name}'s state file. Adding it.")
                
                state['start_bot'] = False  # Update to pause the bot

                # Write changes back to the file
                f.seek(0)
                json.dump(state, f, indent=4)
                f.truncate()
                
            return jsonify({"status": "success", "message": f"Bot {bot_name} paused successfully."})
        
        except Exception as e:
            # Log the exact error message to understand the issue
            print(f"Error updating state file for bot {bot_name}: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500

    else:
        return jsonify({"status": "error", "message": f"Bot '{bot_name}' not found."}), 404




# Helper function to read variables from a Python script
def read_static_variables(script_path):
    variables = {}
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = ''.join([next(f) for _ in range(100)])
            for var in static_vars:
                match = re.search(rf'^{var}\s*=\s*(.+)', script_content, re.MULTILINE)
                if match:
                    try:
                        variables[var] = eval(match.group(1))
                    except Exception as e:
                        variables[var] = None  # Αν δεν μπορεί να αξιολογήσει τη μεταβλητή
                        print(f"Error parsing variable {var} in {script_path}: {str(e)}")
                else:
                    variables[var] = None
    except Exception as e:
        print(f"Error reading {script_path}: {str(e)}")
    return variables





# Endpoint to get static variables for a specific bot
@app.route('/api/get_static_variables', methods=['GET'])
def get_static_variables():
    bot_name = request.args.get("name")
    if bot_name in crypto_path_files:
        script_path = crypto_path_files[bot_name]['path']
        variables = read_static_variables(script_path)
        return jsonify(variables)
    else:
        return jsonify({"status": "error", "message": f"Bot '{bot_name}' not found."}), 404




# Endpoint to update static variables for a specific bot
@app.route('/api/update_static_variables', methods=['POST'])
def update_static_variables():
    data = request.json
    bot_name = data.get("name")
    new_values = data.get("values", {})

    if bot_name in crypto_info:
        state_file_path = crypto_info[bot_name]['path']
        try:
            # Φόρτωση του αρχείου state.json
            with open(state_file_path, 'r+') as f:
                state_data = json.load(f)

                # Ενημέρωση των τιμών των στατικών μεταβλητών
                for var, new_value in new_values.items():
                    state_data[var] = new_value

                # Εγγραφή των αλλαγών στο αρχείο
                f.seek(0)
                json.dump(state_data, f, indent=4)
                f.truncate()

            return jsonify({"status": "success", "message": f"Bot {bot_name} variables updated successfully."})

        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    else:
        return jsonify({"status": "error", "message": f"Bot '{bot_name}' not found."}), 404


@app.route('/crypto-data')
def crypto_data():
    return render_template('crypto_info.html')  # Το όνομα του αρχείου HTML που έσωσες στον φάκελο templates




@app.route("/logs", methods=["GET"])
def log_viewer():
    # Λήψη του επιλεγμένου log από το dropdown
    selected_log_key = request.args.get("logfile")
    log_content = None

    if selected_log_key and selected_log_key in BOT_PATHS:
        log_path = BOT_PATHS[selected_log_key]
        # Ανάγνωση του αρχείου log αν υπάρχει
        if os.path.exists(log_path):
            with open(log_path, "r") as file:
                lines = file.readlines()

            # Διαχωρισμός σε sessions με βάση το διαχωριστικό
            sessions = []
            current_session = []

            for line in reversed(lines):  # Ξεκινάμε από το τέλος
                line = line.strip()  # Αφαίρεση περιττών κενών
                if "Total Score for this round:" in line:  # Αν περιέχει το μοτίβο
                    # Εντοπίζουμε το score και το χρωματίζουμε
                    prefix, score = line.split("Total Score for this round:")
                    score = score.strip()  # Παίρνουμε μόνο το score
                    line = f'{prefix}Total Score for this round: <span class="highlight">{score}</span>'
                current_session.append(line)
                if "INFO >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" in line:
                    sessions.append(current_session[::-1])  # Αντιστρέφουμε το session για να διατηρήσει τη σωστή σειρά
                    current_session = []

            if current_session:  # Αν υπάρχει υπόλοιπο session
                sessions.append(current_session[::-1])

            # Τα sessions είναι έτοιμα και το πιο πρόσφατο είναι πρώτο
            log_content = "\n".join(["\n".join(session) for session in sessions])

    return render_template(
        "log_viewer.html",
        logs=BOT_PATHS.keys(),  # Μόνο τα keys για το dropdown
        selected_log=selected_log_key,
        log_content=log_content,
    )



@app.route('/webhook', methods=['POST'])
def webhook():
    # Ελέγχει αν είναι POST request
    if request.method == 'POST':
        data = request.get_json()  # Ανάγνωση JSON δεδομένων από το request
        logger.info(f"Webhook received: {data}")
        return 'Webhook received', 200
    else:
        return 'Invalid request method', 400




if __name__ == '__main__':
    app.run(threaded=True, debug=False, host='0.0.0.0', port=5015)