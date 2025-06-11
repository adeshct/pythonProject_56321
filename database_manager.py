# database_manager.py

import sqlite3
from datetime import datetime
import logging

DATABASE_NAME = 'trades.db'

def connect_db():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_NAME)
    return conn

def create_trades_table():
    """Creates the 'trades' table if it doesn't already exist."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exchange TEXT NOT NULL DEFAULT 'NFO',
            tradingsymbol TEXT NOT NULL,
            underlying TEXT NOT NULL DEFAULT 'BANKNIFTY',
            strategy TEXT NOT NULL DEFAULT 'default',
            direction TEXT NOT NULL DEFAULT 'LONG',
            isFutures boolean NOT NULL DEFAULT 0,
            isOptions boolean NOT NULL DEFAULT 1,
            optionType TEXT NOT NULL DEFAULT 'CE',
            placeMarketOrder boolean NOT NULL DEFAULT 1,
            requestedEntryPrice REAL NOT NULL DEFAULT 0.0,
            entryPrice REAL NOT NULL DEFAULT 0.0,
            slPercentage REAL NOT NULL DEFAULT 0.0,
            quantity INTEGER NOT NULL,
            initialSL REAL NOT NULL DEFAULT 0.0,
            SLPrice REAL NOT NULL DEFAULT 0.0,
            targetPrice REAL NOT NULL DEFAULT 0.0,
            tradeState TEXT NOT NULL DEFAULT 'OPEN',
            timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            pnl REAL NOT NULL DEFAULT 0.0,
            exitPrice REAL DEFAULT 0.0,
            pnlPercentage REAL NOT NULL DEFAULT 0.0,
            exitTimestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            intradaysquareofftimestamp TEXT,
            exitReason TEXT DEFAULT 'NA',
            exitOrderId TEXT DEFAULT 'NA'
        )
    ''')
    conn.commit()
    conn.close()

    logging.info(f"Table 'trades' created or already exists in {DATABASE_NAME}")
    print(f"Table 'trades' created or already exists in {DATABASE_NAME}")

def insert_trade(exchange='NFO', tradingsymbol=None, underlying='BANKNIFTY', strategy='default',
                 direction='LONG', isFutures=False, isOptions=True, optionType='CE',
                 placeMarketOrder=True, requestedEntryPrice=0.0, entryPrice=0.0,
                 slPercentage=0.0, quantity=0, initialSL=0.0, SLPrice=0.0,
                 targetPrice=0.0, tradeState='OPEN', pnl=0.0, exitPrice=0.0,
                 pnlPercentage=0.0, intradaysquareofftimestamp=None,
                 exitReason='NA', exitOrderId='NA'):
    """Inserts a new trade record into the 'trades' table."""
    conn = connect_db()
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat() # Get current timestamp in ISO format
    exitTimestamp = 'NA'
    try:
        cursor.execute('''
            INSERT INTO trades (timestamp, exchange, tradingsymbol, underlying, strategy, direction, isFutures, isOptions, optionType, placeMarketOrder, requestedEntryPrice, entryPrice, slPercentage, quantity, initialSL, SLPrice, targetPrice, tradeState, pnl, exitPrice, pnlPercentage, intradaysquareofftimestamp, exitTimestamp, exitReason, exitOrderId)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, exchange, tradingsymbol, underlying, strategy, direction, isFutures, isOptions, optionType, placeMarketOrder, requestedEntryPrice, entryPrice, slPercentage, quantity, initialSL, SLPrice, targetPrice, tradeState, pnl, exitPrice, pnlPercentage, intradaysquareofftimestamp, exitTimestamp, exitReason, exitOrderId))
        conn.commit()
        logging.info(f"Trade recorded: {exchange}, {tradingsymbol}, {entryPrice}, {quantity}")
        return cursor.lastrowid # Return the ID of the newly inserted row
    except sqlite3.Error as e:
        logging.error(f"Error inserting trade: {e}")
        conn.rollback() # Rollback changes if an error occurs
        return None
    finally:
        conn.close()

def fetch_all_trades():
    """Fetches all trade records from the 'trades' table."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trades ORDER BY timestamp DESC')
    trades = cursor.fetchall()
    conn.close()
    return trades

def fetch_trades_by_symbol(symbol):
    """Fetches trade records for a specific symbol."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trades WHERE symbol = ? ORDER BY timestamp DESC', (symbol,))
    trades = cursor.fetchall()
    conn.close()
    return trades

def update_trade(trade_id, **kwargs):
    """
    Updates an existing trade record in the 'trades' table based on its ID.
    Only provided keyword arguments will be updated.
    
    Args:
        trade_id (int): The ID of the trade record to update.
        **kwargs: Keyword arguments for the columns to update (e.g., symbol='AAPL', price=150.0).
                  The keys should match the column names in your database table.
    """
    conn = connect_db()
    cursor = conn.cursor()
    set_clauses = []
    params = []

    # Map kwargs to actual column names for update
    # We explicitly check for None to allow updating a field to a valid zero/False value if needed.
    # However, if you want to allow updating a field *to* NULL, you would need to adjust this.
    # For SQLite, boolean values are stored as 0 (False) and 1 (True).
    
    # Iterate over all possible columns that can be updated
    updatable_columns = {
        'exchange', 'tradingsymbol', 'underlying', 'strategy', 'direction',
        'isFutures', 'isOptions', 'optionType', 'placeMarketOrder',
        'requestedEntryPrice', 'entryPrice', 'slPercentage', 'quantity',
        'initialSL', 'SLPrice', 'targetPrice', 'tradeState', 'pnl',
        'exitPrice', 'pnlPercentage', 'exitTimestamp',
        'intradaysquareofftimestamp', 'exitReason', 'exitOrderId'
    }

    # Automatically set `timestamp` or `exitTimestamp` to current time if updated,
    # or allow explicit update if desired.
    # For this function, we'll allow explicit update or let the user handle it.
    
    for key, value in kwargs.items():
        if key in updatable_columns:
            # Handle boolean types for SQLite
            if key in ['isFutures', 'isOptions', 'placeMarketOrder']:
                value = 1 if value else 0 # Convert Python bool to SQLite int
            set_clauses.append(f"{key} = ?")
            params.append(value)
        else:
            logging.info(f"Warning: '{key}' is not a valid updatable column.")

    if not set_clauses:
        logging.info("No valid parameters provided for update.")
        conn.close()
        return False

    update_query = f"UPDATE trades SET {', '.join(set_clauses)} WHERE id = ?"
    params.append(trade_id) # Add the trade_id for the WHERE clause

    try:
        cursor.execute(update_query, tuple(params))
        conn.commit()
        if cursor.rowcount > 0:
            logging.info(f"Trade with ID {trade_id} updated successfully.")
            return True
        else:
            logging.info(f"No trade found with ID {trade_id} or no changes made.")
            return False
    except sqlite3.Error as e:
        logging.error(f"Error updating trade: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    create_trades_table()

    # --- Example Usage for the new Update Function ---
    print("\n--- Inserting example trades for update test ---")
    trade1_id = insert_trade(tradingsymbol="BANKNIFTY24JULFUT", quantity=50, entryPrice=52000.0, strategy="TrendFollow")
    trade2_id = insert_trade(tradingsymbol="NIFTY24JULC19500", quantity=75, entryPrice=250.0, optionType="CE", strategy="OptionBuy")
    trade3_id = insert_trade(tradingsymbol="BANKNIFTY24JULP51000", quantity=25, entryPrice=180.0, optionType="PE", strategy="Hedge")

    print("\n--- Current trades ---")
    all_trades = fetch_all_trades()
    for trade in all_trades:
        print((trade))

    print("\n--- Updating trade with ID", trade1_id, "(BANKNIFTY Futures) ---")
    # Update entryPrice, SLPrice, and tradeState
    update_trade(trade1_id, entryPrice=52050.0, SLPrice=51950.0, tradeState="IN_PROGRESS")

    print("\n--- Updating trade with ID", trade2_id, "(NIFTY CE) - changing pnl and exitPrice ---")
    # Mark as closed, update PnL and exit price
    update_trade(trade2_id, pnl=1500.0, exitPrice=270.0, tradeState="CLOSED", exitReason="Target Hit", exitTimestamp=datetime.now().isoformat())

    print("\n--- Attempting to update a non-existent trade ---")
    update_trade(9999, quantity=100) # Should show "No trade found"

    print("\n--- Trades after updates ---")
    all_trades_after_update = fetch_all_trades()
    for trade in all_trades_after_update:
        print((trade))
