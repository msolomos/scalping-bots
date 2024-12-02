import re
import os
from datetime import datetime
import ast

class BotLogAnalyzer:
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

    def __init__(self, bot_name):
        self.bot_name = bot_name.upper()
        self.log_file_path = self.BOT_PATHS.get(self.bot_name)
        if not self.log_file_path:
            raise ValueError(f"Bot '{self.bot_name}' not found in paths.")
        self.transactions = []

    def parse_logs(self):
        """Parse the log file and populate transactions."""
        if not os.path.exists(self.log_file_path):
            print(f"Log file not found: {self.log_file_path}")
            return

        with open(self.log_file_path, "r") as file:
            logs = file.readlines()

        current_transaction = None

        for line in logs:
            # Detect JSON response with "side"
            if "Order placed successfully" in line and "side" in line:
                try:
                    json_start = line.index("{")
                    json_data = ast.literal_eval(line[json_start:])
                    side = json_data["success_response"]["side"]
                    product_id = json_data["success_response"]["product_id"]
                    base_size = float(json_data["order_configuration"]["market_market_ioc"]["base_size"])
                    timestamp = self.extract_timestamp(line)

                    if side == "BUY":
                        # Initialize a new transaction
                        current_transaction = {
                            "buy_time": timestamp,
                            "buy_price": None,
                            "sell_time": None,
                            "sell_price": None,
                            "fees": 0.0,
                            "quantity": base_size,
                            "product_id": product_id,
                            "net_profit": None,
                        }
                    elif side == "SELL" and current_transaction:
                        # Finalize the transaction
                        current_transaction["sell_time"] = timestamp
                        current_transaction["quantity"] = base_size
                        self.transactions.append(current_transaction)
                        current_transaction = None

                except Exception as e:
                    print(f"Error parsing JSON response: {line.strip()} - {e}")

            # Detect executed price and fees for BUY
            if "Order executed at price" in line and current_transaction and current_transaction["buy_price"] is None:
                executed_price = re.search(r"price: (\d+\.\d+), fees: (\d+\.\d+)", line)
                if executed_price:
                    current_transaction["buy_price"] = float(executed_price.group(1))
                    current_transaction["fees"] += float(executed_price.group(2))

            # Detect executed price and fees for SELL
            if "Order executed at price" in line:
                last_transaction = next((tx for tx in reversed(self.transactions) if tx["sell_price"] is None), None)
                if last_transaction:
                    executed_price = re.search(r"price: (\d+\.\d+), fees: (\d+\.\d+)", line)
                    if executed_price:
                        last_transaction["sell_price"] = float(executed_price.group(1))
                        last_transaction["fees"] += float(executed_price.group(2))

            # Detect net profit from "Saved state"
            if "Saved state" in line:
                saved_details = re.search(r"daily_profit=(-?\d+\.\d+)", line)
                if saved_details:
                    daily_profit = float(saved_details.group(1))
                    last_transaction = next((tx for tx in reversed(self.transactions) if tx["net_profit"] is None), None)
                    if last_transaction:
                        last_transaction["net_profit"] = daily_profit

    def extract_timestamp(self, log_line):
        """Extract timestamp from a log line."""
        raw_timestamp = datetime.strptime(log_line[:23], "%Y-%m-%d %H:%M:%S,%f")
        return raw_timestamp.strftime("%d-%m-%Y %H:%M")

    def analyze_transactions(self):
        """Analyze and display all parsed transactions."""
        print(f"Analyzing transactions for: {self.bot_name}")
        for tx in self.transactions:
            # Check if the transaction is completed (SELL exists)
            is_completed = tx['sell_price'] is not None
            result = (
                "Positive" if tx['net_profit'] and tx['net_profit'] > 0 else "Loss" if tx['net_profit'] else "Active"
            )
            print("Transaction Summary:")
            print(f"  Product: {tx['product_id']}")
            print(f"  Buy Time: {tx['buy_time']}")
            print(f"  Buy Price: {tx['buy_price']} EUR")

            # Add blank line between Buy Price and Sell Time
            print()
            print(f"  Sell Time: {tx['sell_time'] if tx['sell_time'] else 'Not yet'}")
            print(f"  Sell Price: {tx['sell_price'] if tx['sell_price'] else 'Not yet'} EUR")
            print(f"  Quantity: {tx['quantity']}")
            print(f"  Fees: {tx['fees']} EUR")

            # Add a blank line before the result
            print()
            if is_completed:
                print(f"  Net Profit: {tx['net_profit']} EUR")
                print(f"  Result: {result}")
            else:
                print(f"  Result: Active")
            print("-" * 50)

# Main execution
if __name__ == "__main__":
    bot_name = input("Enter the bot name (e.g., BTC, ETH, LTC): ").strip()
    try:
        analyzer = BotLogAnalyzer(bot_name)
        analyzer.parse_logs()
        analyzer.analyze_transactions()
    except ValueError as e:
        print(e)
