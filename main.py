# binance_client.py
from binance.client import Client
import pandas as pd
import os

def get_binance_client():
    """
    Creates and returns an authenticated Binance Client instance connected to the TESTNET.
    Reads API keys from environment variables.
    """
    api_key = "D7jUfM1q8pzN8403xK6NiRKdJKifJXWUB1SeodY1R4H8LcEIABUtJxUwNvJ1100I"
    api_secret = "odgBguZ8VUIkF6ahADOVpfOgPWBtwS3psjGeIkmvu7pwtnPA0yR46Puo2ztCCI52"

    if not api_key or not api_secret:
        raise ValueError("Could not find Binance API keys in environment variables. "
                         "Please set 'BINANCE_TESTNET_API_KEY' and 'BINANCE_TESTNET_SECRET_KEY'.")

    # The 'testnet=True' flag is crucial to point to the testnet environment
    return Client(api_key, api_secret, testnet=True)

def fetch_klines(symbol, interval, limit=500):
    """
    Fetches historical kline (OHLCV) data from Binance and returns a cleaned pandas DataFrame.

    Args:
        symbol (str): The trading symbol (e.g., 'BTCUSDT')
        interval (str): The kline interval (e.g., '1m', '5m', '1h')
        limit (int): The number of candles to fetch (max 1000)

    Returns:
        pd.DataFrame: DataFrame with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    """
    client = get_binance_client()

    # Fetch the raw klines data from Binance
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)

    # Define the column names for the DataFrame
    columns = [
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ]

    # Create the DataFrame
    df = pd.DataFrame(klines, columns=columns)

    # Convert relevant columns to numeric types
    numeric_columns = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col])

    # Convert timestamp to a readable datetime format
    # Correct conversion to match chart timezone
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms').dt.tz_localize('UTC').dt.tz_convert('Asia/Karachi')

    # Return only the essential columns for trading analysis
    return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

# strategy.py
def generate_signal(dataframe, length=1):
    """
    Analyzes the dataframe to generate signals based on the Channel Breakout strategy.
    We emulate stop orders by checking if the price broke the channel in the previous candle.

    Args:
        dataframe (pd.DataFrame): DataFrame containing OHLCV data.
        length (int): The lookback period for the highest high and lowest low channel.

    Returns:
        str: "BUY", "SELL", or "HOLD"
    """
    df = dataframe.copy()
    # print(df)
    # 1. Calculate the channel boundaries for the PREVIOUS 'length' bars
    # The channel for current candle is the highest/high of bars from [-length-1] to [-2]
    # We use .shift(1) to make sure we don't include the current candle in the calculation
    df['upBound'] = df['high'].rolling(window=length).max().shift(1)
    df['downBound'] = df['low'].rolling(window=length).min().shift(1)
    
    # 2. Check for breakouts on the most recent completed candle (previous candle)
    # We use .iloc[-1] for the previous candle since we want to act on completed data
    try:
        last_candle = df.iloc[-1]
        prev_high = last_candle['upBound']
        prev_low = last_candle['downBound']
        
        # Handle NaN values (not enough data)
        if pd.isna(prev_high) or pd.isna(prev_low):
            return "HOLD"
        
    except IndexError:
        # Not enough data to calculate
        return "not enough data: HOLD"
    # 3. Define breakout conditions
    # A BUY signal is triggered if the previous candle's HIGH broke above the channel top
    buy_signal_triggered = last_candle['high'] > prev_high
    # A SELL signal is triggered if the previous candle's LOW broke below the channel bottom
    sell_signal_triggered = last_candle['low'] < prev_low

    # 4. Generate the signal
    if buy_signal_triggered:
        return "BUY"
    elif sell_signal_triggered:
        return "SELL"
    else:
        return "HOLD"

# risk_management.py
from binance_client import get_binance_client

def get_account_balance():
    """Gets your current USDT balance."""
    client = get_binance_client()
    account = client.get_account()
    for balance in account['balances']:
        if balance['asset'] == 'USDT':
            return float(balance['free']) + float(balance['locked'])
    return 0.0

def calculate_position_size1():
    """
    Calculates position size scaled to account capital.
    Uses 0.01 BTC for $10,000 capital as the baseline.
    """
    account_balance = get_account_balance()
    
    # Base calculation: 0.01 BTC per $10,000 capital
    base_capital = 1000000
    base_position = 8
    
    if account_balance <= 0:
        return base_position  # Default fallback
    
    # Scale position size proportionally to account balance
    scale_factor = account_balance / base_capital
    position_size = base_position * scale_factor
    
    # Apply LOT_SIZE filter (round to 6 decimal places for BTC)
    position_size = round(position_size, 5)
    
    # Ensure minimum position size of 0.0001 BTC
    position_size = max(position_size, 0.0001)
    
    print(f"Account Balance: ${account_balance:.2f}, Position Size: {position_size:.5f} BTC")
    return position_size

# Keeping it empty for compatibility
def calculate_position_size():
    """
    Fixed quantity trading - no calculations needed
    """
    return 0.01  # Same as FIXED_QUANTITY in executor.py

# executor.py
import time

# Configuration
SYMBOL = 'BTCUSDT'
TIMEFRAME = '1m'
LENGTH = 1

def get_open_position():
    """
    Checks if we currently hold a BTC position.
    Returns position size and side.
    """
    client = get_binance_client()
    try:
        account = client.get_account()
        for balance in account['balances']:
            if balance['asset'] == 'BTC':
                btc_balance = float(balance['free']) + float(balance['locked'])
                if btc_balance >= 0.0001:  # Detect any significant BTC position
                    return btc_balance, 'LONG'
        return 0, 'NONE'
    except Exception as e:
        print(f"Error checking position: {e}")
        return 0, 'NONE'

def cancel_all_orders(symbol):
    """Cancels all open orders for a given symbol."""
    client = get_binance_client()
    try:
        open_orders = client.get_open_orders(symbol=symbol)
        for order in open_orders:
            result = client.cancel_order(symbol=symbol, orderId=order['orderId'])
            print(f"Cancelled order {order['orderId']}")
        if open_orders:
            print(f"Cancelled {len(open_orders)} open orders for {symbol}")
    except Exception as e:
        print(f"Error cancelling orders: {e}")

def close_position(quantity, side):
    """
    Closes the current position with a market order.
    """
    client = get_binance_client()
    try:
        if side == 'LONG':
            # Round quantity to 6 decimals for BTC
            quantity = round(quantity, 6)
            order = client.order_market_sell(
                symbol=SYMBOL,
                quantity=quantity
            )
            print(f"✓ Closed LONG position: Sold {quantity} BTC")
            return True
        return False
    except Exception as e:
        print(f"✗ Error closing position: {e}")
        return False

def execute_trade(signal):
    """
    Executes a market trade.
    """
    client = get_binance_client()
    
    # Get dynamically calculated position size
    quantity = calculate_position_size1()
    
    try:
        if signal == "BUY":
            order = client.order_market_buy(
                symbol=SYMBOL,
                quantity=quantity
            )
            print(f"✓ Market BUY executed: {quantity} BTC")
            return True
        elif signal == "SELL":
            try:
                pos_size , _ = get_open_position()
                if pos_size > 0:
                    close = close_position(pos_size,side='LONG')
                    print(f"✓ Long position exit: {pos_size} BTC")
                    return True
                else:
                    print("No long position to exit!!")
            except Exception as e:
                print(f"✗ Error closing long: {e}")
        else:
            return False
    except Exception as e:
        print(f"✗ Trade execution failed: {e}")
        return False

def execute_strategy():
    """
    Main strategy execution function.
    """
    print(f"\n--- Checking at {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    # 1. Check for existing position
    position_size, current_side = get_open_position()
    has_position = position_size > 0
    
    # 2. Get market data and generate signal
    from binance_client import fetch_klines
    try:
        data = fetch_klines(SYMBOL, TIMEFRAME, limit=100)
        signal = generate_signal(data, LENGTH)
    except Exception as e:
        print(f"✗ Error fetching data: {e}")
        return
    
    print(f"Signal: {signal}, Position: {has_position}, Size: {position_size:.6f} BTC")
    
    # 3. Manage existing position
    if has_position:
        if signal == "SELL":
            print("Closing position due to SELL signal")
            cancel_all_orders(SYMBOL)
            if close_position(position_size, current_side):
                print("Waiting for position closure...")
                time.sleep(2)  # Brief pause for order to process
            return
        else:
            print("Holding existing position")
            return
    
    # 4. Enter new trade if no position and valid signal
    if signal in ['BUY']:
        print(f"Entering new {signal} trade")
        cancel_all_orders(SYMBOL)
        execute_trade(signal)

print("Starting Channel Breakout Bot...")
while True:
    execute_strategy()
    time.sleep(5)  #Check every 5 seconds

