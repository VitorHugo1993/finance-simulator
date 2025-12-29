import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Any, List

DB_FILE = "budget_data.db"

def init_database():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Main settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Net worth table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS net_worth (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            savings_accounts TEXT,
            investment_account REAL DEFAULT 0,
            other_assets REAL DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Income table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_salary REAL DEFAULT 0,
            partner_salary REAL DEFAULT 0,
            salary_months INTEGER DEFAULT 14,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Fixed expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fixed_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Variable expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS variable_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Savings contributions (one-time)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS savings_contributions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            account TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Savings recurring monthly
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS savings_recurring_monthly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            account TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Investment contributions (one-time)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS investment_contributions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Investment recurring monthly
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS investment_recurring_monthly (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            category TEXT,
            name TEXT,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            account TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def migrate_from_json():
    """Migrate data from JSON file to database if it exists"""
    json_file = "budget_data.json"
    if not os.path.exists(json_file):
        return False
    
    try:
        with open(json_file, 'r') as f:
            json_data = json.load(f)
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check if database already has data
        cursor.execute("SELECT COUNT(*) FROM income")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return False  # Already migrated
        
        # Migrate net worth
        savings_accounts = json.dumps(json_data.get("net_worth", {}).get("savings_accounts", []))
        cursor.execute('''
            INSERT INTO net_worth (savings_accounts, investment_account, other_assets)
            VALUES (?, ?, ?)
        ''', (
            savings_accounts,
            json_data.get("net_worth", {}).get("investment_account", 0),
            json_data.get("net_worth", {}).get("other_assets", 0)
        ))
        
        # Migrate income
        income = json_data.get("income", {})
        cursor.execute('''
            INSERT INTO income (user_salary, partner_salary, salary_months)
            VALUES (?, ?, ?)
        ''', (
            income.get("user_salary", 0),
            income.get("partner_salary", 0),
            income.get("salary_months", 14)
        ))
        
        # Migrate fixed expenses
        for exp in json_data.get("fixed_expenses", []):
            cursor.execute('''
                INSERT INTO fixed_expenses (name, amount)
                VALUES (?, ?)
            ''', (exp.get("name"), exp.get("amount")))
        
        # Migrate variable expenses
        for exp in json_data.get("variable_expenses", []):
            cursor.execute('''
                INSERT INTO variable_expenses (name, amount, date)
                VALUES (?, ?, ?)
            ''', (exp.get("name"), exp.get("amount"), exp.get("date")))
        
        # Migrate savings contributions
        for contrib in json_data.get("savings_contributions", []):
            cursor.execute('''
                INSERT INTO savings_contributions (amount, date, account)
                VALUES (?, ?, ?)
            ''', (contrib.get("amount"), contrib.get("date"), contrib.get("account")))
        
        # Migrate savings recurring monthly
        for contrib in json_data.get("savings_recurring_monthly", []):
            cursor.execute('''
                INSERT INTO savings_recurring_monthly (amount, account)
                VALUES (?, ?)
            ''', (contrib.get("amount"), contrib.get("account")))
        
        # Migrate investment contributions
        for contrib in json_data.get("investment_contributions", []):
            cursor.execute('''
                INSERT INTO investment_contributions (amount, date)
                VALUES (?, ?)
            ''', (contrib.get("amount"), contrib.get("date")))
        
        # Migrate investment recurring monthly
        for contrib in json_data.get("investment_recurring_monthly", []):
            cursor.execute('''
                INSERT INTO investment_recurring_monthly (amount)
                VALUES (?)
            ''', (contrib.get("amount"),))
        
        # Migrate transactions
        for trans in json_data.get("transactions", []):
            cursor.execute('''
                INSERT INTO transactions (type, category, name, amount, date, account)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                trans.get("type"),
                trans.get("category"),
                trans.get("name"),
                trans.get("amount"),
                trans.get("date"),
                trans.get("account")
            ))
        
        conn.commit()
        conn.close()
        
        # Rename JSON file as backup
        backup_file = json_file + ".backup"
        os.rename(json_file, backup_file)
        
        return True
    except Exception as e:
        print(f"Migration error: {e}")
        return False

def load_data() -> Dict[str, Any]:
    """Load all data from database"""
    init_database()
    migrate_from_json()  # Migrate if JSON exists
    
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    data = {
        "net_worth": {
            "current": 0,
            "savings_accounts": [],
            "investment_account": 0,
            "other_assets": 0
        },
        "income": {
            "user_salary": 0,
            "partner_salary": 0,
            "salary_months": 14
        },
        "fixed_expenses": [],
        "variable_expenses": [],
        "savings_contributions": [],
        "savings_recurring_monthly": [],
        "investment_contributions": [],
        "investment_recurring_monthly": [],
        "transactions": []
    }
    
    # Load net worth
    cursor.execute("SELECT * FROM net_worth ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        data["net_worth"]["savings_accounts"] = json.loads(row["savings_accounts"] or "[]")
        data["net_worth"]["investment_account"] = row["investment_account"] or 0
        data["net_worth"]["other_assets"] = row["other_assets"] or 0
    
    # Load income
    cursor.execute("SELECT * FROM income ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    if row:
        data["income"]["user_salary"] = row["user_salary"] or 0
        data["income"]["partner_salary"] = row["partner_salary"] or 0
        data["income"]["salary_months"] = row["salary_months"] or 14
    
    # Load fixed expenses
    cursor.execute("SELECT name, amount FROM fixed_expenses")
    for row in cursor.fetchall():
        data["fixed_expenses"].append({"name": row["name"], "amount": row["amount"]})
    
    # Load variable expenses
    cursor.execute("SELECT name, amount, date FROM variable_expenses")
    for row in cursor.fetchall():
        data["variable_expenses"].append({
            "name": row["name"],
            "amount": row["amount"],
            "date": row["date"]
        })
    
    # Load savings contributions
    cursor.execute("SELECT amount, date, account FROM savings_contributions")
    for row in cursor.fetchall():
        contrib = {"amount": row["amount"], "date": row["date"]}
        if row["account"]:
            contrib["account"] = row["account"]
        data["savings_contributions"].append(contrib)
    
    # Load savings recurring monthly
    cursor.execute("SELECT amount, account FROM savings_recurring_monthly")
    for row in cursor.fetchall():
        contrib = {"amount": row["amount"]}
        if row["account"]:
            contrib["account"] = row["account"]
        data["savings_recurring_monthly"].append(contrib)
    
    # Load investment contributions
    cursor.execute("SELECT amount, date FROM investment_contributions")
    for row in cursor.fetchall():
        data["investment_contributions"].append({
            "amount": row["amount"],
            "date": row["date"]
        })
    
    # Load investment recurring monthly
    cursor.execute("SELECT amount FROM investment_recurring_monthly")
    for row in cursor.fetchall():
        data["investment_recurring_monthly"].append({"amount": row["amount"]})
    
    # Load transactions
    cursor.execute("SELECT type, category, name, amount, date, account FROM transactions")
    for row in cursor.fetchall():
        trans = {
            "type": row["type"],
            "amount": row["amount"],
            "date": row["date"]
        }
        if row["category"]:
            trans["category"] = row["category"]
        if row["name"]:
            trans["name"] = row["name"]
        if row["account"]:
            trans["account"] = row["account"]
        data["transactions"].append(trans)
    
    conn.close()
    return data

def save_data(data: Dict[str, Any]):
    """Save all data to database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Clear existing data (we'll replace it)
    cursor.execute("DELETE FROM net_worth")
    cursor.execute("DELETE FROM income")
    cursor.execute("DELETE FROM fixed_expenses")
    cursor.execute("DELETE FROM variable_expenses")
    cursor.execute("DELETE FROM savings_contributions")
    cursor.execute("DELETE FROM savings_recurring_monthly")
    cursor.execute("DELETE FROM investment_contributions")
    cursor.execute("DELETE FROM investment_recurring_monthly")
    cursor.execute("DELETE FROM transactions")
    
    # Save net worth
    savings_accounts_json = json.dumps(data["net_worth"].get("savings_accounts", []))
    cursor.execute('''
        INSERT INTO net_worth (savings_accounts, investment_account, other_assets)
        VALUES (?, ?, ?)
    ''', (
        savings_accounts_json,
        data["net_worth"].get("investment_account", 0),
        data["net_worth"].get("other_assets", 0)
    ))
    
    # Save income
    income = data.get("income", {})
    cursor.execute('''
        INSERT INTO income (user_salary, partner_salary, salary_months)
        VALUES (?, ?, ?)
    ''', (
        income.get("user_salary", 0),
        income.get("partner_salary", 0),
        income.get("salary_months", 14)
    ))
    
    # Save fixed expenses
    for exp in data.get("fixed_expenses", []):
        cursor.execute('''
            INSERT INTO fixed_expenses (name, amount)
            VALUES (?, ?)
        ''', (exp.get("name"), exp.get("amount")))
    
    # Save variable expenses
    for exp in data.get("variable_expenses", []):
        cursor.execute('''
            INSERT INTO variable_expenses (name, amount, date)
            VALUES (?, ?, ?)
        ''', (exp.get("name"), exp.get("amount"), exp.get("date")))
    
    # Save savings contributions
    for contrib in data.get("savings_contributions", []):
        cursor.execute('''
            INSERT INTO savings_contributions (amount, date, account)
            VALUES (?, ?, ?)
        ''', (
            contrib.get("amount"),
            contrib.get("date"),
            contrib.get("account")
        ))
    
    # Save savings recurring monthly
    for contrib in data.get("savings_recurring_monthly", []):
        cursor.execute('''
            INSERT INTO savings_recurring_monthly (amount, account)
            VALUES (?, ?)
        ''', (
            contrib.get("amount"),
            contrib.get("account")
        ))
    
    # Save investment contributions
    for contrib in data.get("investment_contributions", []):
        cursor.execute('''
            INSERT INTO investment_contributions (amount, date)
            VALUES (?, ?)
        ''', (contrib.get("amount"), contrib.get("date")))
    
    # Save investment recurring monthly
    for contrib in data.get("investment_recurring_monthly", []):
        cursor.execute('''
            INSERT INTO investment_recurring_monthly (amount)
            VALUES (?)
        ''', (contrib.get("amount"),))
    
    # Save transactions
    for trans in data.get("transactions", []):
        cursor.execute('''
            INSERT INTO transactions (type, category, name, amount, date, account)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            trans.get("type"),
            trans.get("category"),
            trans.get("name"),
            trans.get("amount"),
            trans.get("date"),
            trans.get("account")
        ))
    
    conn.commit()
    conn.close()


