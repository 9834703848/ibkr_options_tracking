from ib_insync import *
import asyncio
import nest_asyncio
from datetime import datetime, timedelta, date
import sqlite3

nest_asyncio.apply()  # Applies nest_asyncio to avoid event loop issues in certain environments

# Database connection and initialization
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Create tables if they do not exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS executed_orders (
            unique_id TEXT PRIMARY KEY,
            symbol TEXT,
            sec_type TEXT,
            position REAL,
            average_cost REAL,
            market_price REAL,
            unrealized_pnl REAL,
            realized_pnl REAL,
            order_date TEXT,
            expiry_date TEXT,
            call_put TEXT,
            strike REAL
        )
    ''')
    conn.commit()
    conn.close()

# Function to check if an order exists in the database
def check_order_exists(unique_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM executed_orders WHERE unique_id = ?', (unique_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

# Function to save or update data in the database
def save_or_update_order(unique_id, data):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Check if the order already exists
    if check_order_exists(unique_id):
        # Update the existing order with the latest P&L and other parameters
        cursor.execute('''
            UPDATE executed_orders
            SET symbol = ?, sec_type = ?, position = ?, average_cost = ?, market_price = ?, 
                unrealized_pnl = ?, realized_pnl = ?, order_date = ?, expiry_date = ?, call_put = ?, strike = ?
            WHERE unique_id = ?
        ''', (*data, unique_id))
    else:
        # Insert new order data with today's date if it's not in the database
        cursor.execute('''
            INSERT INTO executed_orders (unique_id, symbol, sec_type, position, average_cost, 
                                         market_price, unrealized_pnl, realized_pnl, 
                                         order_date, expiry_date, call_put, strike)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (unique_id, *data))
    conn.commit()
    conn.close()

# Define the main async function to run the script
async def main():
    # Initialize the database
    init_db()

    # Initialize IB instance
    ib = IB()

    # Connect to the IBKR paper trading platform
    await ib.connectAsync('127.0.0.1', 4002, clientId=12) #ib.connectAsync('127.0.0.1', 7497, clientId=10)
    # try:
    #     , timeout=60)  # Adjust clientId and timeout if needed
    #     print("Connected to IBKR successfully.")
    # except TimeoutError:
    #     print("Failed to connect to IBKR. Please check your TWS/Gateway settings and ensure it is running.")
    #     return

    # Fetch the current portfolio positions to get P&L
    portfolio = ib.portfolio()

    # Check if portfolio has positions
    if not portfolio:
        print("No positions found.")
        return
    trades = ib.reqExecutions()
    for item in portfolio:
        contract = item.contract
        position = item.position
        avg_cost = item.averageCost
        unrealized_pnl = item.unrealizedPNL
        realized_pnl = item.realizedPNL
        market_price = item.marketPrice

        # Generate a unique identifier for each item in the portfolio
        unique_id = f"{contract.symbol}_{contract.secType}_{contract.conId}"  # Unique ID for each contract
        related_trades = [trade for trade in trades if trade.contract.conId == contract.conId]
        if related_trades:
        # Fetch contract details to get expiry date, option type (Call/Put), and strike price for options
            details = await ib.reqContractDetailsAsync(contract)
            expiry_date = details[0].contract.lastTradeDateOrContractMonth if details and contract.secType == 'OPT' else 'N/A'
            call_put = contract.right if contract.secType == 'OPT' else 'N/A'
            strike = contract.strike if contract.secType == 'OPT' else 'N/A'

            # Set order_date to today's date if the order does not exist
            order_date = date.today().strftime('%Y-%m-%d') if check_order_exists(unique_id) else None

            # Save or update the order in the database
            save_or_update_order(unique_id, (contract.symbol, contract.secType, position, avg_cost,
                                            market_price, unrealized_pnl, realized_pnl, 
                                            order_date , expiry_date, call_put, strike))

    # Disconnect from the IBKR paper trading platform
    ib.disconnect()

# This function will be called by the Flask app to run the main IB function
def run_ibkr_script():
    asyncio.run(main())
