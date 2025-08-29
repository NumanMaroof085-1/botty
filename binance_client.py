# binance_client.py
from binance.client import Client
import pandas as pd
import os

def get_binance_client():
    """
    Creates and returns an authenticated Binance Client instance connected to the TESTNET.
    Reads API keys from environment variables.
    """
    api_key = os.environ.get('BINANCE_TESTNET_API_KEY')
    api_secret = os.environ.get('BINANCE_TESTNET_SECRET_KEY')

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


# Example usage and test function
if __name__ == "__main__":
    # Test the connection and data fetch
    try:
        print("Testing connection to Binance Testnet...")
        client = get_binance_client()
        # A simple API call to test connectivity
        server_time = client.get_server_time()
        print(f"✓ Connection successful. Server time: {server_time['serverTime']}")

        print("\nFetching recent BTCUSDT 1m klines...")
        # Fetch data for the strategy
        df = fetch_klines(symbol='BTCUSDT', interval='1m', limit=10)
        print(f"✓ Successfully fetched {len(df)} candles.")
        print("\nLatest candles:")
        print(df.tail(9))

        # Quick check of account balance (optional)
        print("\nChecking USDT balance...")
        account_info = client.get_account()
        for balance in account_info['balances']:
            if balance['asset'] == 'USDT':
                print(f"USDT Balance: {balance['free']}")
                break

    except Exception as e:
        print(f"✗ An error occurred: {e}")