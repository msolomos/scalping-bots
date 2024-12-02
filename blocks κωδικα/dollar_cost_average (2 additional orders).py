### block Κωδικα για 2 συμπληρωματικές αγορές ...σε συνεχόμενη πτώση

# DOLLAR COST AVERAGE STRATEGY
# Υπολογισμός της τιμής ενεργοποίησης δεύτερης αγοράς
second_buy_trigger_price = active_trade * (1 - MAX_DROP_PERCENTAGE)

# Έλεγχος αν η τιμή έχει πέσει αρκετά για δεύτερη αγορά
if not second_trade_price and current_price <= second_buy_trigger_price:
    logging.info(f"Price dropped below threshold ({second_buy_trigger_price:.{current_decimals}f}). Executing second buy.")

    # Εκτέλεση της εντολής αγοράς
    second_trade_amount = trade_amount  # Ίδια ποσότητα με την αρχική
    order_successful, execution_price, fees = place_order("buy", second_trade_amount, current_price)

    if order_successful and execution_price:
        second_trade_price = execution_price

        # Υπολογισμός νέας μέσης τιμής
        second_total_cost = (trade_amount * active_trade) + (second_trade_amount * second_trade_price)
        second_total_amount = trade_amount + second_trade_amount
        average_trade_price = second_total_cost / second_total_amount

        logging.info(f"Second buy executed successfully at {second_trade_price:.{current_decimals}f}. "
                     f"New average price: {average_trade_price:.{current_decimals}f}.")

        # Αποθήκευση κατάστασης μετά την αγορά
        save_state()

    else:
        logging.error(f"Failed to execute second buy order at price: {current_price:.{current_decimals}f}.")


# Λογική για πώληση μετά τη 2η αγορά
if second_trade_price:  # Εξασφαλίζουμε ότι υπάρχει 2η αγορά πριν υπολογίσουμε
    
    # Υπολογισμός του συνολικού κόστους με fees
    second_total_fees = (trade_amount * active_trade + second_trade_amount * second_trade_price) * FEES_PERCENTAGE
    second_break_even_price = (trade_amount * active_trade + second_trade_amount * second_trade_price + second_total_fees) / (trade_amount + second_trade_amount)
    remaining_to_break_even = max(0, second_break_even_price - current_price)
    logging.info(f"Total fees: {second_total_fees:.{current_decimals}f}, Break-even price: {second_break_even_price:.{current_decimals}f}, Remaining to break-even: {remaining_to_break_even:.{current_decimals}f}")

    # Έλεγχος για πώληση μόνο αν η τρέχουσα τιμή καλύπτει το κόστος + fees
    if current_price >= second_break_even_price:
        logging.info(f"Current price ({current_price:.{current_decimals}f}) reached break-even price ({second_break_even_price:.{current_decimals}f}). Selling all positions.")

        # Υπολογισμός συνολικής ποσότητας προς πώληση
        total_amount_to_sell = trade_amount + second_trade_amount

        # Εκτέλεση εντολής πώλησης
        order_successful, execution_price, fees = place_order("sell", total_amount_to_sell, current_price)

        if order_successful and execution_price:
            # Υπολογισμός καθαρού κέρδους
            profit_loss = (execution_price * total_amount_to_sell) - (trade_amount * active_trade + second_trade_amount * second_trade_price + second_total_fees)
            daily_profit += profit_loss

            logging.info(f"Sell order executed for total amount {total_amount_to_sell}. "
                         f"Profit/Loss: {profit_loss:.{current_decimals}f}, Fees: {fees}")

            # Καθαρισμός μεταβλητών μετά την πώληση
            active_trade = None
            trade_amount = 0
            second_trade_price = None
            second_trade_amount = 0
            average_trade_price = None
            highest_price = None
            trailing_profit_active = False
            current_trades += 1

            send_push_notification(f"ALERT: Dollar Cost Average Sale was executed for {CRYPTO_NAME} bot.")

            # Χρονική αναμονή μετά την πώληση για αποφυγή άμεσης αγοράς
            save_cooldown_state(custom_duration=1800)  # DCA strategy: 30 min cooldown

            # Αποθήκευση της νέας κατάστασης
            save_state()
            return






#------------------------------------------------------------------------------------------------------------------------------------------------------
# block για 3ή αγορά εφόσον η πτώση συνεχιστει

# Υπολογισμός της τιμής ενεργοποίησης τρίτης αγοράς
third_buy_trigger_price = second_trade_price * (1 - THIRD_MAX_DROP_PERCENTAGE)

# Έλεγχος αν η τιμή έχει πέσει αρκετά για τρίτη αγορά
if not third_trade_price and current_price <= third_buy_trigger_price:
    logging.info(f"Price dropped below third-buy threshold ({third_buy_trigger_price:.{current_decimals}f}). Executing third buy.")

    # Εκτέλεση της εντολής αγοράς
    third_trade_amount = trade_amount  # Ίδια ποσότητα με τις προηγούμενες
    order_successful, execution_price, fees = place_order("buy", third_trade_amount, current_price)

    if order_successful and execution_price:
        third_trade_price = execution_price

        # Υπολογισμός νέας μέσης τιμής
        total_cost = (trade_amount * active_trade) + (second_trade_amount * second_trade_price) + (third_trade_amount * third_trade_price)
        total_amount = trade_amount + second_trade_amount + third_trade_amount
        average_trade_price = total_cost / total_amount

        logging.info(f"Third buy executed successfully at {third_trade_price:.{current_decimals}f}. "
                     f"New average price: {average_trade_price:.{current_decimals}f}.")

        # Αποθήκευση κατάστασης μετά την τρίτη αγορά
        save_state()

    else:
        logging.error(f"Failed to execute third buy order at price: {current_price:.{current_decimals}f}.")


# Υπολογισμός και έλεγχος για πώληση
if third_trade_price:  # Εξασφαλίζουμε ότι υπάρχει 3η αγορά πριν υπολογίσουμε
    
    # Υπολογισμός του συνολικού κόστους με fees
    third_total_fees = (trade_amount * active_trade + second_trade_amount * second_trade_price + third_trade_amount * third_trade_price) * FEES_PERCENTAGE
    third_break_even_price = (trade_amount * active_trade + second_trade_amount * second_trade_price + third_trade_amount * third_trade_price + third_total_fees) / (trade_amount + second_trade_amount + third_trade_amount)
    logging.info(f"Total fees: {third_total_fees:.{current_decimals}f}, Break-even price: {third_break_even_price:.{current_decimals}f}")

    # Έλεγχος για πώληση μόνο αν η τρέχουσα τιμή καλύπτει το κόστος + fees
    if current_price >= third_break_even_price:
        logging.info(f"Current price ({current_price:.{current_decimals}f}) reached break-even price ({third_break_even_price:.{current_decimals}f}). Selling all positions.")

        # Υπολογισμός συνολικής ποσότητας προς πώληση
        total_amount_to_sell = trade_amount + second_trade_amount + third_trade_amount

        # Εκτέλεση εντολής πώλησης
        order_successful, execution_price, fees = place_order("sell", total_amount_to_sell, current_price)

        if order_successful and execution_price:
            # Υπολογισμός καθαρού κέρδους
            profit_loss = (execution_price * total_amount_to_sell) - (trade_amount * active_trade + second_trade_amount * second_trade_price + third_trade_amount * third_trade_price + third_total_fees)
            daily_profit += profit_loss

            logging.info(f"Sell order executed for total amount {total_amount_to_sell}. "
                         f"Profit/Loss: {profit_loss:.{current_decimals}f}, Fees: {fees}")

            # Καθαρισμός μεταβλητών μετά την πώληση
            active_trade = None
            trade_amount = 0
            second_trade_price = None
            second_trade_amount = 0
            third_trade_price = None
            third_trade_amount = 0
            average_trade_price = None
            highest_price = None
            trailing_profit_active = False
            current_trades += 1

            send_push_notification(f"ALERT: Dollar Cost Average Sale (after third buy) was executed for {CRYPTO_NAME} bot.")

            # Χρονική αναμονή μετά την πώληση για αποφυγή άμεσης αγοράς
            save_cooldown_state(custom_duration=1800)  # DCA strategy: 30 min cooldown

            # Αποθήκευση της νέας κατάστασης
            save_state()
            return
