from ib_insync import *
import asyncio
import nest_asyncio
from datetime import datetime, timedelta

nest_asyncio.apply()  # Applies nest_asyncio to avoid event loop issues in certain environments

# Define the main async function to run the script
async def main():
    # Initialize IB instance
    ib = IB()

    # Asynchronously connect to the IBKR paper trading platform
    await ib.connectAsync('127.0.0.1', 4002, clientId=8) 
    # try:
    #     # Asynchronously connect to the IBKR paper trading platform
    #     await ib.connectAsync('127.0.0.1', 4002, clientId=8, timeout=60)  # Adjust clientId and timeout if needed
    #     print("Connected to IBKR successfully.")
    # except TimeoutError:
    #     print("Failed to connect to IBKR. Please check your TWS/Gateway settings and ensure it is running.")
 # Adjust clientId if needed to ensure uniqueness

    # Fetch the current portfolio positions to get P&L
    portfolio = ib.portfolio()
    print('dfjsdjf')
    # Attempt to fetch historical executions with an extended time filter
    start_date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d %H:%M:%S')  # 1 year ago
    execution_filter = ExecutionFilter(time=start_date)  # Set filter to a broader range
    trades = ib.reqExecutions(execution_filter)  # Attempt to retrieve historical executions
    print(trades)
    # Check if portfolio has positions
    if not portfolio:
        print("No positions found.")
    else:
        print("Current Portfolio Positions with P&L, Order Date, and Expiry Date:")
        for item in portfolio:
            contract = item.contract
            position = item.position
            avg_cost = item.averageCost
            unrealized_pnl = item.unrealizedPNL
            realized_pnl = item.realizedPNL
            market_price = item.marketPrice

            # Find corresponding trade executions to get order placing date
            related_trades = [trade for trade in trades if trade.contract.conId == contract.conId]
            if related_trades:
                # Access the execution time directly from the related trade (Fill) object
                order_date = related_trades[0].time.strftime('%Y-%m-%d %H:%M:%S') if related_trades[0].time else 'N/A'
            else:
                order_date = 'N/A'  # If historical executions aren't returned correctly, fallback to N/A

            # Fetch contract details to get expiry date for options
            details = await ib.reqContractDetailsAsync(contract)
            if details and contract.secType == 'OPT':
                expiry_date = details[0].contract.lastTradeDateOrContractMonth
            else:
                expiry_date = 'N/A'

            # Display details including P&L, Order Date, and Expiry Date
            print(f'Symbol: {contract.symbol}, '
                  f'Security Type: {contract.secType}, '
                  f'Position: {position}, '
                  f'Average Cost: {avg_cost}, '
                  f'Current Market Price: {market_price}, '
                  f'Unrealized P&L: {unrealized_pnl}, '
                  f'Realized P&L: {realized_pnl}, '
                  f'Order Date: {order_date}, '
                  f'Expiry Date: {expiry_date}')

    # Disconnect from the IBKR paper trading platform
    ib.disconnect()

# Run the main async function using asyncio.run()
if __name__ == "__main__":
    asyncio.run(main())
