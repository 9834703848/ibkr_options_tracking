from flask import Flask, render_template
import sqlite3
from ibkr_script import run_ibkr_script
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import STATE_RUNNING

app = Flask(__name__)

# Initialize the scheduler
scheduler = BackgroundScheduler()

# Function to fetch data and update the database
def fetch_data():
    run_ibkr_script()  # This calls the main function from ibkr_script.py

# Start the scheduler only if it is not already running
if scheduler.state != STATE_RUNNING:
    scheduler.add_job(func=fetch_data, trigger="interval", minutes=1)  # Adjust interval as needed
    scheduler.start()

# Route to view the fetched data
@app.route('/')
def index():
    # Connect to the SQLite database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Fetch all executed orders from the database
    cursor.execute('SELECT * FROM executed_orders ORDER BY expiry_date')
    rows = cursor.fetchall()
    conn.close()

    # Group data by expiry date
    data_by_expiry = {}
    for row in rows:
        expiry_date = row[9]  # Expiry date column
        if expiry_date not in data_by_expiry:
            data_by_expiry[expiry_date] = []
        data_by_expiry[expiry_date].append(row)

    # Print data for debugging (optional)
    # print(data_by_expiry)

    # Render the template with the grouped data
    return render_template('index.html', data=data_by_expiry)

# Teardown function to shut down the scheduler only if it's running
@app.teardown_appcontext
def shutdown_scheduler(exception=None):
    if scheduler.running:
        scheduler.shutdown()

if __name__ == '__main__':
    app.run(debug=True)
