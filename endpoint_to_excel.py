from flask import Flask, jsonify, request, render_template
import json
import os
import re




app = Flask(__name__)

# Paths to JSON files and Euro pairs for each cryptocurrency
crypto_info = {
    'AVAX': {'path': '/opt/python/scalping-bot/AVAX/state.json', 'euro_pair': 'AVAX-EUR'},
    'SOLANA': {'path': '/opt/python/scalping-bot/SOLANA/state.json', 'euro_pair': 'SOL-EUR'},
    'LITECOIN': {'path': '/opt/python/scalping-bot/LITECOIN/state.json', 'euro_pair': 'LTC-EUR'},
    'ETHEREUM': {'path': '/opt/python/scalping-bot/ETHEREUM/state.json', 'euro_pair': 'ETH-EUR'},
    'BITCOIN': {'path': '/opt/python/scalping-bot/BITCOIN/state.json', 'euro_pair': 'BTC-EUR'},
    'XRP': {'path': '/opt/python/scalping-bot/XRP/state.json', 'euro_pair': 'XRP-EUR'},
    'CARDANO': {'path': '/opt/python/scalping-bot/CARDANO/state.json', 'euro_pair': 'ADA-EUR'},
    'POLKADOT': {'path': '/opt/python/scalping-bot/POLKADOT/state.json', 'euro_pair': 'DOT-EUR'}
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
    'POLKADOT': {'path': '/opt/python/scalping-bot/POLKADOT/scalper_dot.py'}
}

# Define the static variables to read and update
static_vars = [
    'SCALP_TARGET', 'BUY_THRESHOLD', 'RSI_THRESHOLD', 'ENABLE_STOP_LOSS', 'STOP_LOSS', 'ENABLE_TRAILING_PROFIT',
    'TRAILING_PROFIT_THRESHOLD', 'MINIMUM_PROFIT_THRESHOLD', 'DAILY_PROFIT_TARGET'
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
                    "active_trade": file_data.get("active_trade"),
                    "trade_amount": file_data.get("trade_amount"),
                    "euro_pair": euro_pair
                })
        else:
            # Αν το αρχείο δεν υπάρχει, προσθέτουμε κενές τιμές
            data.append({
                "name": name,
                "start_bot": None,
                "active_trade": None,
                "trade_amount": None,
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
        with open(script_path, 'r') as f:
            # Διαβάζουμε μόνο τις πρώτες 75 γραμμές
            script_content = ''.join([next(f) for _ in range(75)])
            for var in static_vars:
                match = re.search(rf'^{var}\s*=\s*(.+)', script_content, re.MULTILINE)
                if match:
                    variables[var] = eval(match.group(1))
                else:
                    variables[var] = None  # Variable not found
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





if __name__ == '__main__':
    app.run(threaded=True, debug=False, host='0.0.0.0', port=5015)