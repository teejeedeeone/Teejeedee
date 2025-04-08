import ccxt
import pandas as pd
import numpy as np
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pybit.unified_trading import HTTP
import time
import os
import subprocess
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# ======================== Configuration ========================
# Constants
TRADE_FILE = "active_trade.json"
TRADE_STATE_FILE = "trade_state.txt"  # <-- ADD THIS LINE
ALERT_PATH = os.path.expanduser("alert.mp3")
SCAN_INTERVAL = 0  # 15 minutes in seconds


# Email Configuration
sender = "dahmadu071@gmail.com"
recipients = ["teejeedeeone@gmail.com"]
password = "oase wivf hvqn lyhr"

# Bybit API Configuration
session = HTTP(
    api_key="lJu52hbBTbPkg2VXZ2",
    api_secret="e43RV6YDZsn24Q9mucr0i4xbU7YytdL2HtuV",
    demo=True
)

# Initialize the exchange
exchange = ccxt.bybit()

# Symbol mapping
symbol_mapping = {
    'BTC/USDT:USDT': 'BTCUSDT',
    'XRP/USDT:USDT': 'XRPUSDT'
}
symbols = list(symbol_mapping.keys())
symbol_mapping_inv = {v: k for k, v in symbol_mapping.items()}  # <-- ADD THIS LINE

# Trading Parameters
TRADE_AMOUNT_USDT = 50
STOP_LOSS_PERCENT = 2
TAKE_PROFIT_PERCENT = 20

# Indicator Parameters
timeframe_15m = '15m'
timeframe_1h = '1h'
limit = 500
ema_fast_length = 38
ema_slow_length = 62
ema_trend_length = 200
H_BANDWIDTH = 8.0
MULTIPLIER = 3.0
REPAINT = True

# ======================== Core Functions ========================

def calculate_atr(df, length=14):
    """Calculate ATR for a given dataframe"""
    df['prev_close'] = df['close'].shift(1)
    df['hl'] = df['high'] - df['low']
    df['hc'] = abs(df['high'] - df['prev_close'])
    df['lc'] = abs(df['low'] - df['prev_close'])
    df['tr'] = df[['hl', 'hc', 'lc']].max(axis=1)
    df['atr'] = df['tr'].rolling(window=length).mean()
    return df

def get_atr_levels(symbol, timeframe='15m', length=14):
    """Get current ATR and projected levels"""
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=length+1)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df = calculate_atr(df, length)
    
    last_close = df['close'].iloc[-2]  # Last fully closed candle
    last_atr = df['atr'].iloc[-2]      # Last fully closed ATR
    
    return {
        'upper': last_close + (2 * last_atr),
        'lower': last_close - (2 * last_atr),
        'atr': last_atr
    }



def play_alert():
    """Play alert sound for network issues"""
    if os.path.exists(ALERT_PATH):
        subprocess.Popen(["mpv", "--no-video", ALERT_PATH])
        print("Alert played")
    else:
        print(f"Alert file not found at {ALERT_PATH}")

def save_active_trade(symbol, entry_price, sl_price, tp_price, side):
    """Save trade details to file"""
    trade_data = {
        'symbol': symbol,
        'entry_price': entry_price,
        'sl_price': sl_price,
        'tp_price': tp_price,
        'side': side,
        'opened_at': pd.Timestamp.now().isoformat()
    }
    with open(TRADE_FILE, 'w') as f:
        json.dump(trade_data, f)

def clear_active_trade():
    """Remove trade record file"""
    if os.path.exists(TRADE_FILE):
        os.remove(TRADE_FILE)




def initialize_trade_state():
    """Create file with 'ENTRY' if it doesn't exist"""
    if not os.path.exists(TRADE_STATE_FILE):
        with open(TRADE_STATE_FILE, 'w') as f:
            f.write("ENTRY")

def get_trade_state():
    """Read the current trade state"""
    try:
        with open(TRADE_STATE_FILE, 'r') as f:
            return f.read().strip().upper()
    except:
        return "ENTRY"  # Default to ENTRY if error occurs

def set_trade_state(state):

    """Enhanced with email notifications"""
    old_state = get_trade_state()
    if old_state != state:
        send_email(
            subject=f"🔄 Trade State Changed to {state}",
            body=f"Trading is now {'PAUSED' if state == 'MANAGE' else 'ACTIVE'}"
        )
    """Update the trade state (ENTRY/MANAGE)"""
    valid_states = ["ENTRY", "MANAGE"]
    if state.upper() in valid_states:
        with open(TRADE_STATE_FILE, 'w') as f:
            f.write(state.upper())
    else:
        print(f"Invalid state: {state}. Must be 'ENTRY' or 'MANAGE'")





def get_active_trade():
    """Check for existing active trade"""
    if os.path.exists(TRADE_FILE):
        try:
            with open(TRADE_FILE, 'r') as f:
                trade_data = json.load(f)
            
            # Verify the trade still exists
            position = get_open_position(symbol_mapping.get(trade_data['symbol']))
            if position:
                return trade_data
            else:
                clear_active_trade()
        except Exception as e:
            print(f"Error loading trade data: {e}")
            clear_active_trade()
    return None

def send_email(subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipients, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")

def gauss(x, h):
    """Gaussian window function for band calculation"""
    return np.exp(-(x ** 2) / (h ** 2 * 2))

def calculate_nwe(src, h, mult, repaint):
    """Calculate Nadaraya-Watson Envelope"""
    n = len(src)
    out = np.zeros(n)
    mae = np.zeros(n)
    upper = np.zeros(n)
    lower = np.zeros(n)
    
    if not repaint:
        coefs = np.array([gauss(i, h) for i in range(n)])
        den = np.sum(coefs)
        
        for i in range(n):
            out[i] = np.sum(src * coefs) / den
        
        mae = pd.Series(np.abs(src - out)).rolling(499).mean().values * mult
        upper = out + mae
        lower = out - mae
    else:
        nwe = []
        sae = 0.0
        
        for i in range(n):
            sum_val = 0.0
            sumw = 0.0
            for j in range(n):
                w = gauss(i - j, h)
                sum_val += src[j] * w
                sumw += w
            y2 = sum_val / sumw
            nwe.append(y2)
            sae += np.abs(src[i] - y2)
        
        sae = (sae / n) * mult
        
        for i in range(n):
            upper[i] = nwe[i] + sae
            lower[i] = nwe[i] - sae
            out[i] = nwe[i]
    
    return out, upper, lower

def get_market_price(symbol):
    """Fetch current market price from Bybit"""
    try:
        ticker = session.get_tickers(category="linear", symbol=symbol)
        if ticker["retCode"] == 0 and ticker["result"]["list"]:
            return float(ticker["result"]["list"][0]["lastPrice"])
        raise Exception("No price data returned")
    except Exception as e:
        raise Exception(f"Failed to fetch market price: {str(e)}")

def get_lot_size_rules(symbol):
    """Get trading rules for symbol"""
    try:
        instrument_info = session.get_instruments_info(category="linear", symbol=symbol)
        if instrument_info["retCode"] == 0 and instrument_info["result"]["list"]:
            return instrument_info["result"]["list"][0]["lotSizeFilter"]
        raise Exception("No instrument info returned")
    except Exception as e:
        raise Exception(f"Failed to fetch lot size rules: {str(e)}")

def adjust_quantity_to_lot_size(quantity, lot_size_rules):
    """Adjust quantity to comply with exchange rules"""
    try:
        min_order_qty = float(lot_size_rules["minOrderQty"])
        max_order_qty = float(lot_size_rules["maxOrderQty"])
        qty_step = float(lot_size_rules["qtyStep"])

        quantity = max(min_order_qty, min(quantity, max_order_qty))
        quantity = round(quantity / qty_step) * qty_step
        return max(quantity, min_order_qty)
    except Exception as e:
        raise Exception(f"Failed to adjust quantity: {str(e)}")

def get_open_position(symbol):
    """Check for existing position"""
    try:
        positions = session.get_positions(category="linear", symbol=symbol)
        if positions["retCode"] == 0 and positions["result"]["list"]:
            for position in positions["result"]["list"]:
                if position["symbol"] == symbol and float(position["size"]) > 0:
                    return position
        return None
    except Exception as e:
        raise Exception(f"Failed to check positions: {str(e)}")

def update_stop_loss(symbol, new_sl_price):
    """Update stop-loss for open position"""
    try:
        response = session.set_trading_stop(
            category="linear",
            symbol=symbol,
            stopLoss=str(new_sl_price)
        )
        if response["retCode"] == 0:
            print(f"Stop-loss updated to {new_sl_price} USDT")
            return True
        print(f"Failed to update stop-loss: {response['retMsg']}")
        return False
    except Exception as e:
        print(f"Failed to update stop-loss: {e}")
        return False

def close_position(symbol, side):
    """Close position and place limit re-entry order"""
    try:
        position = get_open_position(symbol)
        if not position:
            print("No open position to close")
            return False

        close_side = "Sell" if side == "Buy" else "Buy"
        response = session.place_order(
            category="linear",
            symbol=symbol,
            side=close_side,
            orderType="Market",
            qty=position["size"],
            reduceOnly=True
        )

        if response["retCode"] == 0:
            print(f"Position closed successfully")
            set_trade_state("MANAGE")
            
            # Get current price and ATR levels
            current_price = get_market_price(symbol)
            ccxt_symbol = symbol_mapping_inv[symbol]
            atr_levels = get_atr_levels(ccxt_symbol)
            
            # Place limit re-entry order
            if side == "Buy":
                limit_price = round(atr_levels['upper'], 4)
                limit_side = "Buy"
                print(f"Placing limit buy at {limit_price:.4f} (2xATR above exit)")
            else:
                limit_price = round(atr_levels['lower'], 4)
                limit_side = "Sell"
                print(f"Placing limit sell at {limit_price:.4f} (2xATR below exit)")
            
            # Calculate quantity (same as original trade)
            raw_quantity = TRADE_AMOUNT_USDT / current_price
            lot_size_rules = get_lot_size_rules(symbol)
            adjusted_quantity = adjust_quantity_to_lot_size(raw_quantity, lot_size_rules)
            
            # Place limit order
            limit_response = session.place_order(
                category="linear",
                symbol=symbol,
                side=limit_side,
                orderType="Limit",
                qty=str(adjusted_quantity),
                price=str(limit_price),
                timeInForce="GTC"  # Good Till Cancelled
            )
            
            if limit_response["retCode"] == 0:
                send_email(
                    subject=f"♻️ {symbol} Limit Order Placed",
                    body=f"Placed {limit_side} limit at {limit_price:.4f}\n"
                         f"ATR: {atr_levels['atr']:.4f}\n"
                         f"Qty: {adjusted_quantity:.4f}\n"
                         f"Original Exit: {current_price:.4f}"
                )
            else:
                print(f"Failed to place limit order: {limit_response['retMsg']}")
            
            return True
            
        print(f"Failed to close position: {response['retMsg']}")
        return False
    except Exception as e:
        print(f"Error closing position: {e}")
        return False

def execute_trade(signal_symbol, signal_type):

    """Execute trade based on signal"""
    if get_trade_state() == "MANAGE":
        print(f"Trade blocked - Currently in MANAGE state for {signal_symbol}")
        return
    bybit_symbol = symbol_mapping.get(signal_symbol)
    if not bybit_symbol:
        print(f"No Bybit symbol mapping for {signal_symbol}")
        return

    try:
        side = "Buy" if signal_type == "BUY" else "Sell"
        market_price = get_market_price(bybit_symbol)
        print(f"{bybit_symbol} price: {market_price} USDT")

        # Calculate position size
        raw_quantity = TRADE_AMOUNT_USDT / market_price
        lot_size_rules = get_lot_size_rules(bybit_symbol)
        adjusted_quantity = adjust_quantity_to_lot_size(raw_quantity, lot_size_rules)

        # Calculate SL/TP prices
        if side == "Buy":
            sl_price = round(market_price * (1 - STOP_LOSS_PERCENT / 100), 4)
            tp_price = round(market_price * (1 + TAKE_PROFIT_PERCENT / 100), 4)
        else:
            sl_price = round(market_price * (1 + STOP_LOSS_PERCENT / 100), 4)
            tp_price = round(market_price * (1 - TAKE_PROFIT_PERCENT / 100), 4)

        print(f"Placing {side} order: {adjusted_quantity} contracts")
        print(f"SL: {sl_price} | TP: {tp_price}")

        # Place order
        response = session.place_order(
            category="linear",
            symbol=bybit_symbol,
            side=side,
            orderType="Market",
            qty=str(adjusted_quantity),
            takeProfit=str(tp_price),
            stopLoss=str(sl_price)
        )

        if response["retCode"] == 0:
            print(f"Order executed successfully")
            save_active_trade(signal_symbol, market_price, sl_price, tp_price, side)
            send_email(
                subject=f"✅ {side} {bybit_symbol} Executed",
                body=f"{side} {bybit_symbol} at {market_price}\n"
                     f"Quantity: {adjusted_quantity}\n"
                     f"SL: {sl_price} | TP: {tp_price}"
            )
            monitor_trade(signal_symbol, market_price, sl_price, tp_price, side)
        else:
            print(f"Order failed: {response['retMsg']}")
            send_email(
                subject=f"❌ {side} {bybit_symbol} Failed",
                body=f"Failed to execute {side} order\n"
                     f"Error: {response['retMsg']}"
            )

    except Exception as e:
        print(f"Trade execution error: {str(e)}")
        send_email(
            subject=f"⚠️ {bybit_symbol} Trade Error",
            body=f"Error executing {side} order\n"
                 f"Error: {str(e)}"
        )

def monitor_trade(symbol, entry_price, sl_price, tp_price, side):
    """Monitor open trade with persistence"""
    max_retries = 3
    retry_delay = 10
    
    while True:
        try:
            # Verify position exists
            position = None
            for attempt in range(max_retries):
                try:
                    position = get_open_position(symbol_mapping.get(symbol))
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    print(f"Network error (attempt {attempt+1}): {e}")
                    play_alert()
                    time.sleep(retry_delay)
            
            if not position:
                print(f"\nPosition closed")
                send_email(f"🏁 {symbol} Closed", "Position closed")
                clear_active_trade()
                return

            # Get current market data
            current_price = None
            for attempt in range(max_retries):
                try:
                    current_price = get_market_price(symbol_mapping.get(symbol))
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    print(f"Network error getting price (attempt {attempt+1}): {str(e)}")
                    play_alert()
                    time.sleep(retry_delay)

            # Fetch OHLCV data
            df = None
            for attempt in range(max_retries):
                try:
                    ohlcv = exchange.fetch_ohlcv(symbol, timeframe_15m, limit=limit)
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    print(f"Network error fetching OHLCV (attempt {attempt+1}): {str(e)}")
                    play_alert()
                    time.sleep(retry_delay)

            # Calculate indicators
            src = df['close'].values
            out, upper, lower = calculate_nwe(src, H_BANDWIDTH, MULTIPLIER, REPAINT)
            
            # Get last candle data
            last_candle = df.iloc[-2]
            last_close = last_candle['close']
            last_open = last_candle['open']
            last_high = last_candle['high']
            last_low = last_candle['low']
            last_upper = upper[-2]
            last_lower = lower[-2]
            
            # Calculate PnL
            if side == "Buy":
                pnl_percent = ((current_price - entry_price) / entry_price) * 100
                # New precise band touch detection
                touched_band = ((last_close >= last_upper) or (last_high >= last_upper)) and not ((last_close > last_upper) and (last_open > last_upper))
                # New crossover detection
                crossover_occurred = (df['close'].shift(1).iloc[-2] < df['upper'].shift(1).iloc[-2]) and (last_close > last_upper)
            else:
                pnl_percent = ((entry_price - current_price) / entry_price) * 100
                # New precise band touch detection
                touched_band = ((last_close <= last_lower) or (last_low <= last_lower)) and not ((last_close < last_lower) and (last_open < last_lower))
                # New crossunder detection
                crossunder_occurred = (df['close'].shift(1).iloc[-2] > df['lower'].shift(1).iloc[-2]) and (last_close < last_lower)

            print(f"Current PnL: {pnl_percent:.2f}%", end="\r")

            # Exit condition checks
            exit_reason = None
            
            # Force Close Conditions (using new precise detection)
            if (side == "Buy" and crossover_occurred) or (side == "Sell" and crossunder_occurred):
                exit_reason = f"Force close ({'crossover' if side == 'Buy' else 'crossunder'})"
            
            # Take Profit Conditions
            elif pnl_percent >= 5 and touched_band:
                exit_reason = "Take profit (≥5% + band touch)"
            
            # Band-touched Exit Conditions
            elif touched_band and pnl_percent < 5:
                if pnl_percent > 0:
                    new_sl = entry_price * 1.001 if side == "Buy" else entry_price * 0.999
                    try:
                        if update_stop_loss(symbol_mapping.get(symbol), new_sl):
                            print(f"\nTrailing SL to 0.1% profit")
                            send_email(
                                subject=f"🔄 {symbol} Trailing SL",
                                body=f"Adjusted SL to {new_sl}\nCurrent PnL: {pnl_percent:.2f}%"
                            )
                    except Exception as e:
                        print(f"Error updating SL: {str(e)}")
                        play_alert()
                else:
                    exit_reason = "Closed at loss (band touch)"
            
            # Original SL/TP
            elif (side == "Buy" and current_price <= sl_price) or (side == "Sell" and current_price >= sl_price):
                exit_reason = "Stop-loss triggered"
            elif (side == "Buy" and current_price >= tp_price) or (side == "Sell" and current_price <= tp_price):
                exit_reason = "Take-profit triggered"

            # Handle exits
            if exit_reason:
                print(f"\n{exit_reason}")
                try:
                    if close_position(symbol_mapping.get(symbol), side):
                        send_email(
                            subject=f"🏁 {symbol} Position Closed",
                            body=f"{exit_reason}\nEntry: {entry_price}\nExit: {current_price}\nPnL: {pnl_percent:.2f}%"
                        )
                        clear_active_trade()
                        return
                except Exception as e:
                    print(f"Error closing position: {str(e)}")
                    play_alert()

            time.sleep(15)  # Normal monitoring interval

        except Exception as e:
            print(f"\nCritical monitoring error: {str(e)}")
            play_alert()
            send_email(
                subject=f"🛑 {symbol} Monitoring Error",
                body=f"Critical error:\n{str(e)}\n\nStill managing position."
            )
            time.sleep(0)  # Longer delay after critical errors



def check_conservative_entry(symbol):
    """Check for trading signals"""
    try:
        print(f"\nChecking {symbol}...")
        
        # Fetch OHLCV data
        ohlcv_15m = exchange.fetch_ohlcv(symbol, timeframe_15m, limit=limit)
        df_15m = pd.DataFrame(ohlcv_15m, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_15m['timestamp'] = pd.to_datetime(df_15m['timestamp'], unit='ms')
        df_15m.set_index('timestamp', inplace=True)

        ohlcv_1h = exchange.fetch_ohlcv(symbol, timeframe_1h, limit=limit)
        df_1h = pd.DataFrame(ohlcv_1h, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_1h['timestamp'] = pd.to_datetime(df_1h['timestamp'], unit='ms')
        df_1h.set_index('timestamp', inplace=True)

        # Calculate EMAs
        df_15m['EMA_Fast'] = df_15m['close'].ewm(span=ema_fast_length, adjust=False).mean()
        df_15m['EMA_Slow'] = df_15m['close'].ewm(span=ema_slow_length, adjust=False).mean()
        df_15m['EMA_Trend'] = df_15m['close'].ewm(span=ema_trend_length, adjust=False).mean()
        df_1h['EMA_Trend'] = df_1h['close'].ewm(span=ema_trend_length, adjust=False).mean()
        df_15m['EMA_Trend_1h'] = df_1h['EMA_Trend'].resample('15min').ffill()

        # Generate signals
        df_15m['Signal'] = 0
        df_15m.loc[
            (df_15m['EMA_Fast'] > df_15m['EMA_Slow']) &
            (df_15m['EMA_Fast'].shift(1) <= df_15m['EMA_Slow'].shift(1)) &
            (df_15m['close'] > df_15m['EMA_Trend']) &
            (df_15m['close'] > df_15m['EMA_Trend_1h']),
            'Signal'] = 1  # Buy signal
        
        df_15m.loc[
            (df_15m['EMA_Fast'] < df_15m['EMA_Slow']) &
            (df_15m['EMA_Fast'].shift(1) >= df_15m['EMA_Slow'].shift(1)) &
            (df_15m['close'] < df_15m['EMA_Trend']) &
            (df_15m['close'] < df_15m['EMA_Trend_1h']),
            'Signal'] = -1  # Sell signal

        # Conservative entry conditions
        df_15m['Entry_Up'] = (
            (df_15m['EMA_Fast'] > df_15m['EMA_Slow']) & 
            (df_15m['close'].shift(1) < df_15m['EMA_Fast'].shift(1)) & 
            (df_15m['close'] > df_15m['EMA_Fast'])
        )
        
        df_15m['Entry_Down'] = (
            (df_15m['EMA_Fast'] < df_15m['EMA_Slow']) & 
            (df_15m['close'].shift(1) > df_15m['EMA_Fast'].shift(1)) & 
            (df_15m['close'] < df_15m['EMA_Fast'])
        )
        
        df_15m['Entry_Up_Filtered'] = df_15m['Entry_Up'] & (
            (df_15m['close'] > df_15m['EMA_Trend']) & 
            (df_15m['close'] > df_15m['EMA_Trend_1h'])
        )
        
        df_15m['Entry_Down_Filtered'] = df_15m['Entry_Down'] & (
            (df_15m['close'] < df_15m['EMA_Trend']) & 
            (df_15m['close'] < df_15m['EMA_Trend_1h'])
        )

        # Track first conservative entry after signal
        df_15m['First_Up_Arrow'] = False
        df_15m['First_Down_Arrow'] = False
        last_signal = 0
        
        for i in range(1, len(df_15m)):
            if df_15m['Signal'].iloc[i] == 1:
                last_signal = 1
            elif df_15m['Signal'].iloc[i] == -1:
                last_signal = -1

            if last_signal == 1 and df_15m['Entry_Up_Filtered'].iloc[i]:
                df_15m.at[df_15m.index[i], 'First_Up_Arrow'] = True
                last_signal = 0
            elif last_signal == -1 and df_15m['Entry_Down_Filtered'].iloc[i]:
                df_15m.at[df_15m.index[i], 'First_Down_Arrow'] = True
                last_signal = 0

        # Check most recent closed candle
        last_candle = df_15m.iloc[-2]
        
        if last_candle['First_Up_Arrow']:
            print(f"{symbol}: ✅ BUY Signal")
            send_email(
                subject=f"🚀 BUY {symbol}",
                body=f"BUY signal detected for {symbol}\n"
                     f"Price: {last_candle['close']}\n"
                     f"Fast EMA: {last_candle['EMA_Fast']:.2f}\n"
                     f"Slow EMA: {last_candle['EMA_Slow']:.2f}"
            )
            execute_trade(symbol, "BUY")
            
        elif last_candle['First_Down_Arrow']:
            print(f"{symbol}: ❌ SELL Signal")
            send_email(
                subject=f"🔻 SELL {symbol}",
                body=f"SELL signal detected for {symbol}\n"
                     f"Price: {last_candle['close']}\n"
                     f"Fast EMA: {last_candle['EMA_Fast']:.2f}\n"
                     f"Slow EMA: {last_candle['EMA_Slow']:.2f}"
            )
            execute_trade(symbol, "SELL")
            
        else:
            print(f"{symbol}: No signal")

    except Exception as e:
        print(f"Error checking {symbol}: {str(e)}")
        send_email(
            subject=f"⚠️ {symbol} Signal Error",
            body=f"Error checking signals for {symbol}\nError: {str(e)}"
        )

# ======================== Main Execution ========================
if __name__ == "__main__":
    print("Starting Trading Bot")
    initialize_trade_state()  # <-- ADD THIS LINE
    
    # Check for existing trade
    active_trade = get_active_trade()
    if active_trade:
        print(f"\nResuming trade: {active_trade['symbol']}")
        monitor_trade(
            symbol=active_trade['symbol'],
            entry_price=active_trade['entry_price'],
            sl_price=active_trade['sl_price'],
            tp_price=active_trade['tp_price'],
            side=active_trade['side']
        )
    
    # Main trading loop
    try:
        while True:
            scan_start = time.time()
            print(f"\n=== New Scan at {pd.Timestamp.now()} ===")
            current_state = get_trade_state()
            print(f"Current Trade State: {current_state}")


            if current_state == "ENTRY":  # <-- MODIFIED THIS LINE
                for symbol in symbols:
                    check_conservative_entry(symbol)
            else:
                print("Skipping signal checks - MANAGE state active")
            elapsed = time.time() - scan_start
            sleep_time = max(0, SCAN_INTERVAL - elapsed)
            time.sleep(sleep_time)  # <-- Add this critical line
    # ... rest of existing loop ...
            
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        send_email("🛑 Bot Crashed", f"Error:\n{str(e)}")