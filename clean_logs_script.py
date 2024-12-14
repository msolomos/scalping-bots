import datetime
import os

def clean_old_logs(log_file_paths):
    # Current date and time
    now = datetime.datetime.now()
    # Time threshold for 96 hours ago
    time_threshold = now - datetime.timedelta(hours=96)

    for log_file_path in log_file_paths:
        # Check if the file exists
        if not os.path.exists(log_file_path):
            print(f"The file {log_file_path} was not found.")
            continue  # Proceed to the next file
        
        # List to keep recent log lines
        recent_logs = []

        try:
            with open(log_file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    # Extract the date and time from the log line
                    try:
                        log_time = datetime.datetime.strptime(line[:23], "%Y-%m-%d %H:%M:%S,%f")
                        # Check if it's within the last 96 hours
                        if log_time >= time_threshold:
                            recent_logs.append(line)
                    except ValueError:
                        # If the line doesn't contain a date, skip it
                        recent_logs.append(line)

            # Write only recent logs back to the file
            with open(log_file_path, 'w', encoding='utf-8') as file:
                file.writelines(recent_logs)
            print(f"The file {log_file_path} was successfully cleaned.")

        except UnicodeDecodeError as e:
            print(f"UnicodeDecodeError for file {log_file_path}: {e}")
        except Exception as e:
            print(f"An error occurred while processing {log_file_path}: {e}")

# List with log file paths
log_files = [
    "/opt/python/scalping-bot/AVAX/AVAX_bot.log",
    "/opt/python/scalping-bot/BITCOIN/BTC_bot.log",
    "/opt/python/scalping-bot/CARDANO/ADA_bot.log",
    "/opt/python/scalping-bot/ETHEREUM/ETH_bot.log",
    "/opt/python/scalping-bot/LITECOIN/LTC_bot.log",
    "/opt/python/scalping-bot/POLKADOT/DOT_bot.log",
    "/opt/python/scalping-bot/SOLANA/SOL_bot.log",
    "/opt/python/scalping-bot/XRP/XRP_bot.log",
    "/opt/python/scalping-bot/DOGECOIN/DOGE_bot.log",   #new bot
    "/opt/python/scalping-bot/POLYGON/MATIC_bot.log",   #new bot
    "/opt/python/scalping-bot/STELLAR/XLM_bot.log",   #new bot
    "/opt/python/failover-decision-bot/trading_decisions.log",
    "/opt/python/short-selling-bot/logging.log"
]


# Example of calling the function
clean_old_logs(log_files)
