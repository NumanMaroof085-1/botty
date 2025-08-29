# executor.py
from binance_client import get_binance_client
from strategy import generate_signal
import risk_management
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
    quantity = risk_management.calculate_position_size1()
    
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

# Main loop
if __name__ == "__main__":
    print("Starting Smart Channel Breakout Bot...")
    print("Bot configured with dynamic position sizing")
    print("Symbol:", SYMBOL)
    print("Timeframe:", TIMEFRAME)
    print("Channel Length:", LENGTH)
    print("-" * 50)

    trade = execute_trade('SELL')
    print(get_open_position())
    
    # while True:
    #     try:
    #         execute_strategy()
    #         time.sleep(30)  # Check every 30 seconds
    #     except KeyboardInterrupt:
    #         print("\nBot stopped by user")
    #         break
    #     except Exception as e:
    #         print(f"Unexpected error in main loop: {e}")
    #         time.sleep(60)
