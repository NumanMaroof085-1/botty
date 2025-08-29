# # config.py
# API_KEY = "4qyhITJxVsN6yLVXXRqvKtRmGyFtdVqPf0Jbw2OvqfLFN1A4sfquZkIGlrcz6Ibf"
# API_SECRET = "n721Ma3bci2fhmUW4x80GuI78D9b7rxZARH6Q0JYAH5PsU3CLQ4NT3ON8BsROvIQ"
# SYMBOL = "BTCUSDT"
# TIMEFRAME = "1m"

import os
print("API Key:", os.environ.get('BINANCE_TESTNET_API_KEY'))
print("Secret Key:", os.environ.get('BINANCE_TESTNET_SECRET_KEY'))

# config.py
# # Trading Strategy Parameters
# SYMBOL = "BTCUSDT"
# TIMEFRAME = "1m"
# CHANNEL_LENGTH = 1

# # Risk Management Parameters
# RISC_AMOUNT_USDT = 200

# # Bot Operation Parameters
# CHECK_INTERVAL_SECONDS = 30