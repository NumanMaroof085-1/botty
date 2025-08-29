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

calculate_position_size1()

# risk_management.py
# This module is no longer needed for fixed quantity trading
# Keeping it empty for compatibility
def calculate_position_size():
    """
    Fixed quantity trading - no calculations needed
    """
    return 0.01  # Same as FIXED_QUANTITY in executor.py