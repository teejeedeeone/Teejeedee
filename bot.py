from pybit.unified_trading import HTTP
import math
import time

# Hardcoded API key and secret
API_KEY = "lJu52hbBTbPkg2VXZ2"
API_SECRET = "e43RV6YDZsn24Q9mucr0i4xbU7YytdL2HtuV"

# Initialize the session
session = HTTP(
    api_key=API_KEY,
    api_secret=API_SECRET,
    demo=True  # Use testnet environment
)

def get_market_price(symbol):
    """Fetch the current market price of the symbol."""
    ticker = session.get_tickers(category="linear", symbol=symbol)
    if ticker["retCode"] == 0 and ticker["result"]["list"]:
        return float(ticker["result"]["list"][0]["lastPrice"])
    else:
        raise Exception("Failed to fetch market price")

def get_lot_size_rules(symbol):
    """Fetch the lot size rules for the symbol."""
    instrument_info = session.get_instruments_info(category="linear", symbol=symbol)
    if instrument_info["retCode"] == 0 and instrument_info["result"]["list"]:
        return instrument_info["result"]["list"][0]["lotSizeFilter"]
    else:
        raise Exception("Failed to fetch lot size rules")

def adjust_quantity_to_lot_size(quantity, lot_size_rules):
    """Adjust the quantity to comply with lot size rules."""
    min_order_qty = float(lot_size_rules["minOrderQty"])
    max_order_qty = float(lot_size_rules["maxOrderQty"])
    qty_step = float(lot_size_rules["qtyStep"])

    # Ensure quantity is within min and max limits
    quantity = max(min_order_qty, min(quantity, max_order_qty))

    # Round quantity to the nearest multiple of qtyStep
    quantity = round(quantity / qty_step) * qty_step

    # Ensure the quantity is not less than the minimum order size
    quantity = max(quantity, min_order_qty)

    return quantity

def get_open_position(symbol):
    """Fetch the open position for the symbol."""
    positions = session.get_positions(category="linear", symbol=symbol)
    if positions["retCode"] == 0 and positions["result"]["list"]:
        for position in positions["result"]["list"]:
            if position["symbol"] == symbol and float(position["size"]) > 0:
                return position
    return None

def update_stop_loss(symbol, new_sl_price):
    """Update the stop-loss price for the open position."""
    try:
        response = session.set_trading_stop(
            category="linear",
            symbol=symbol,
            stopLoss=str(new_sl_price)
        )
        if response["retCode"] == 0:
            print(f"Stop-loss updated to {new_sl_price} USDT")
        else:
            print(f"Failed to update stop-loss: {response['retMsg']}")
    except Exception as e:
        print(f"Failed to update stop-loss: {e}")

def place_order_with_usdt(symbol, usdt_amount, sl_percent=2, tp_percent=4.5):
    """Place a market order using USDT value with stop-loss and take-profit."""
    try:
        # Step 1: Get the current market price
        market_price = get_market_price(symbol)
        print(f"Current market price of {symbol}: {market_price} USDT")

        # Step 2: Calculate the raw quantity of the asset to buy
        raw_quantity = usdt_amount / market_price
        print(f"Raw quantity to buy: {raw_quantity}")

        # Step 3: Fetch lot size rules and adjust quantity
        lot_size_rules = get_lot_size_rules(symbol)
        adjusted_quantity = adjust_quantity_to_lot_size(raw_quantity, lot_size_rules)
        print(f"Adjusted quantity to buy: {adjusted_quantity}")

        # Step 4: Calculate the actual USDT value being used
        actual_usdt_value = adjusted_quantity * market_price
        print(f"Actual USDT value being used: {actual_usdt_value} USDT")

        # Step 5: Calculate stop-loss and take-profit prices
        sl_price = market_price * (1 - sl_percent / 100)  # Stop-loss price
        tp_price = market_price * (1 + tp_percent / 100)  # Take-profit price
        print(f"Stop-loss price: {sl_price} USDT")
        print(f"Take-profit price: {tp_price} USDT")

        # Step 6: Place the market order with SL and TP
        response = session.place_order(
            category="linear",
            symbol=symbol,
            side="Buy",
            orderType="Market",
            qty=adjusted_quantity,
            takeProfit=str(tp_price),  # Take-profit price
            stopLoss=str(sl_price)    # Stop-loss price
        )
        print("Order placed successfully:")
        print(response)

        # Step 7: Monitor the trade and print profit/loss
        monitor_trade(symbol, market_price, sl_price, tp_price)
    except Exception as e:
        print(f"Failed to place order: {e}")

def monitor_trade(symbol, entry_price, sl_price, tp_price):
    """Monitor the trade and print profit/loss."""
    try:
        print("Monitoring trade...")
        trail_stop_loss = False  # Flag to indicate if trailing stop-loss is active

        while True:
            # Fetch the current market price
            current_price = get_market_price(symbol)
            #print(f"Current price: {current_price} USDT")

            # Calculate the current profit/loss percentage
            profit_percent = ((current_price - entry_price) / entry_price) * 100
            #print(f"Current profit/loss: {profit_percent:.2f}%")
            print(f"Current profit/loss: {profit_percent * 10:.2f}%")


            # Check if the trade is still open
            open_position = get_open_position(symbol)
            if not open_position:
                print("Trade is no longer open. Exiting trade monitoring.")
                break

            # Check if SL or TP is hit
            if current_price <= sl_price or current_price >= tp_price:
                print("Stop-loss or take-profit hit. Exiting trade monitoring.")
                break

            # Check if profit reaches 0.3% and trail stop-loss to 0.1% profit
            if profit_percent >= 0.3 and not trail_stop_loss:
                new_sl_price = entry_price * (1 + 0.1 / 100)  # 0.1% above entry price
                update_stop_loss(symbol, new_sl_price)
                sl_price = new_sl_price  # Update the stop-loss price
                trail_stop_loss = True  # Activate trailing stop-loss
                print(f"Trailing stop-loss activated at {new_sl_price} USDT")

            # Wait for a few seconds before checking again
            time.sleep(0)  # Adjust the interval as needed
    except Exception as e:
        print(f"Failed to monitor trade: {e}")

# Place an order using 50 USDT with 2% SL and 4.5% TP
place_order_with_usdt("TRUMPUSDT", 40, sl_percent=2, tp_percent=4.5)
