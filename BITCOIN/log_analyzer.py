import re
import os
from datetime import datetime

def find_log_file():
    """Find the first .log file in the current directory."""
    for file in os.listdir():
        if file.endswith(".log"):
            return file
    raise FileNotFoundError("No .log file found in the current directory.")

def parse_logs(log_file_path):
    with open(log_file_path, "r") as file:
        logs = file.readlines()

    transactions = []
    current_transaction = None
    tracking_prices = False
    max_price = float('-inf')
    min_price = float('inf')

    for i, line in enumerate(logs):
        # Detect buy entry
        if "Initiating a buy at" in line:
            buy_time = extract_timestamp(line)
            buy_price = float(re.search(r"buy at (\d+\.\d+)", line).group(1))
            current_transaction = {
                "buy_time": buy_time,
                "buy_price": buy_price,
                "sell_time": None,
                "sell_price": None,
                "fees": 0.0,
                "net_profit": None,
                "quantity": None,
                "max_price": None,
                "min_price": None,
                "sell_reason": "Unknown reason",  # Default value
            }
            tracking_prices = True
            max_price = float('-inf')
            min_price = float('inf')

        # Detect buy completion
        if "Order placed successfully at price" in line and current_transaction:
            buy_details = re.search(r"price: (\d+\.\d+) with fees: (\d+\.\d+)", line)
            if buy_details:
                current_transaction["buy_price"] = float(buy_details.group(1))
                current_transaction["fees"] += float(buy_details.group(2))

        # Track price between buy and sell
        if tracking_prices and "Fetched" in line:
            fetched_price = re.search(r"price: (\d+\.\d+)", line)
            if fetched_price:
                price = float(fetched_price.group(1))
                max_price = max(max_price, price)
                min_price = min(min_price, price)

        # Detect sell entry
        if "Sold" in line:
            sell_time = extract_timestamp(line)
            sell_details = re.search(r"Sold (\d+\.\d+) of [A-Z]+ at (\d+\.\d+) with net profit: (-?\d+\.\d+)", line)
            if sell_details:
                current_transaction["sell_time"] = sell_time
                current_transaction["quantity"] = float(sell_details.group(1))
                current_transaction["sell_price"] = float(sell_details.group(2))
                current_transaction["net_profit"] = float(sell_details.group(3))
                current_transaction["max_price"] = max_price
                current_transaction["min_price"] = min_price

                # Look for the reason for the sell
                for j in range(i - 10, i):  # Check up to 10 lines before the sell entry
                    if j >= 0 and "Immediate Sell was executed" in logs[j]:
                        current_transaction["sell_reason"] = "Manual sell (macro call)"
                        break
                    elif j >= 0 and "Immediate Sell" in logs[j]:
                        current_transaction["sell_reason"] = "Immediate Sell"
                        break
                    elif j >= 0 and "Trailing profit activated" in logs[j]:
                        current_transaction["sell_reason"] = "Trailing Profit"
                        break
                    elif j >= 0 and "Stop-loss triggered" in logs[j]:
                        current_transaction["sell_reason"] = "Stop-loss"
                        break
                    elif j >= 0 and "Reset" in logs[j]:
                        current_transaction["sell_reason"] = "Reset"
                        break

                transactions.append(current_transaction)
                current_transaction = None
                tracking_prices = False
            else:
                print(f"Warning: Could not parse sell details from line: {line}")

    return transactions

def extract_timestamp(log_line):
    raw_timestamp = datetime.strptime(log_line[:23], "%Y-%m-%d %H:%M:%S,%f")
    return raw_timestamp.strftime("%d-%m-%Y %H:%M")

def analyze_transactions(transactions):
    for tx in transactions:
        result = "Positive" if tx['net_profit'] > 0 else "Loss"
        net_profit_display = f"""
**************************
  Net Profit: {tx['net_profit']} EUR
  Result: {result}
**************************
"""
        print("Transaction Summary:")
        print(f"  Buy Time: {tx['buy_time']}")
        print(f"  Buy Price: {tx['buy_price']} EUR")
        print(f"  Sell Time: {tx['sell_time']}")
        print(f"  Sell Price: {tx['sell_price']} EUR")
        print(f"  Quantity: {tx['quantity']}")
        print(f"  Fees: {tx['fees']} EUR")
        print(net_profit_display)
        print(f"  Max Price During Trade: {tx['max_price']} EUR")
        print(f"  Min Price During Trade: {tx['min_price']} EUR")
        print(f"  Reason for Sell: {tx['sell_reason']}")
        print("-" * 50)

# Main execution
if __name__ == "__main__":
    try:
        log_file = find_log_file()
        print(f"Found log file: {log_file}")
        transactions = parse_logs(log_file)
        analyze_transactions(transactions)
    except FileNotFoundError as e:
        print(e)
