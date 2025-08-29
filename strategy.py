# strategy.py
import pandas as pd
from binance_client import fetch_klines

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


# Example usage for testing (this part would not be in the final file)
if __name__ == "__main__":
    df = fetch_klines(symbol='BTCUSDT', interval='1m', limit=10)
    sample_df = pd.DataFrame(df.tail())
    
    print("Sample data:")
    for i, row in sample_df.iterrows():
        print(f"Bar {i}: High={row['high']}, Low={row['low']}, Close={row['close']}")
    
    # Test with length=1
    signal = generate_signal(sample_df, length=1)
    print(f"\nGenerated signal: {signal}")
    
    # Let's also see what the bounds were
    sample_df['upBound'] = sample_df['high'].rolling(window=1).max().shift(1)
    sample_df['downBound'] = sample_df['low'].rolling(window=1).min().shift(1)
    print(f"\nCalculated bounds:")
    print(sample_df[['high', 'low','close', 'upBound', 'downBound']])