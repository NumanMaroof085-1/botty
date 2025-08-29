# main.py
from executor import execute_strategy
import time

print("Starting Channel Breakout Bot...")
while True:
    execute_strategy()
    time.sleep(5)  #Check every 30 seconds
    