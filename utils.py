import pandas as pd
import os
import json
import hashlib
import yfinance as yf
from datetime import datetime, timedelta

DATA_DIR = "data"
DATA_DIR = "data"
FOLDERS_FILE = os.path.join(DATA_DIR, "folders.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(str.encode(password)).hexdigest()

def load_users():
    """Load users metadata."""
    if not os.path.exists(USERS_FILE):
        # Create default admin user if file doesn't exist
        default_users = {
            "admin": {
                "password_hash": hash_password("0713"),
                "role": "admin",
                "approved": True,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        save_users(default_users)
        return default_users
        
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}

def save_users(users):
    """Save users metadata."""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def register_user(username, password):
    """Register a new user (pending approval). Returns (success, message)."""
    users = load_users()
    if username in users:
        return False, "이미 존재하는 사용자명입니다."
    
    users[username] = {
        "password_hash": hash_password(password),
        "role": "user",
        "approved": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_users(users)
    return True, "회원가입 신청이 완료되었습니다. 관리자 승인을 기다려주세요."

def verify_user(username, password):
    """Verify login credentials. Returns (user_data, message)."""
    users = load_users()
    if username not in users:
        return None, "존재하지 않는 사용자입니다."
    
    user = users[username]
    if user["password_hash"] != hash_password(password):
        return None, "비밀번호가 올바르지 않습니다."
        
    if not user["approved"]:
        return None, "관리자 승인 대기 중입니다."
        
    return user, "로그인 성공"

def approve_user(username):
    """Approve a pending user."""
    users = load_users()
    if username in users:
        users[username]["approved"] = True
        save_users(users)
        return True
    return False

def delete_user(username):
    """Delete a user."""
    users = load_users()
    if username in users and users[username]["role"] != "admin": # Prevent deleting main admin
        del users[username]
        save_users(users)
        return True
    return False

def load_folders():
    """Load folders metadata."""
    if os.path.exists(FOLDERS_FILE):
        try:
            with open(FOLDERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading folders: {e}")
            return {}
    return {}

def save_folders(folders):
    """Save folders metadata."""
    with open(FOLDERS_FILE, "w", encoding="utf-8") as f:
        json.dump(folders, f, ensure_ascii=False, indent=4)

def get_expense_file_path(trip_id):
    """Get the CSV file path for a specific trip."""
    # Handle default migration where file was moved but id is 'default_trip'
    if trip_id == "default_trip":
        return os.path.join(DATA_DIR, "expenses_default.csv")
    return os.path.join(DATA_DIR, f"expenses_{trip_id}.csv")

def load_data(trip_id=None):
    """
    Loads data from the CSV file for a specific trip.
    """
    if not trip_id:
        return pd.DataFrame(columns=["Date", "Category", "Item", "Amount", "Currency", "Original Amount", "Exchange Rate"])
        
    file_path = get_expense_file_path(trip_id)
    
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        # Ensure 'Date' column is datetime
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
        
        # Add missing columns if they don't exist (for migration)
        if 'Currency' not in df.columns:
            df['Currency'] = 'KRW'
        if 'Original Amount' not in df.columns:
            df['Original Amount'] = df['Amount']
        if 'Exchange Rate' not in df.columns:
            df['Exchange Rate'] = 1.0
            
        return df
    else:
        return pd.DataFrame(columns=["Date", "Category", "Item", "Amount", "Currency", "Original Amount", "Exchange Rate"])

def save_data(df, trip_id):
    """
    Saves the DataFrame to a CSV file for a specific trip.
    """
    if not trip_id:
        return
        
    file_path = get_expense_file_path(trip_id)
    df.to_csv(file_path, index=False)

def calculate_metrics(df, total_budget):
    """
    Calculates total spent and remaining budget.
    Input df should have 'Amount' in base currency (KRW).
    """
    if df.empty:
        return 0, total_budget
    
    total_spent = df["Amount"].sum()
    remaining = total_budget - total_spent
    return total_spent, remaining

def get_exchange_rate(currency_code, target_date=None):
    """
    Get exchange rate for currency_code to KRW.
    If target_date is None, use today.
    """
    if currency_code == "KRW":
        return 1.0
    
    ticker_map = {
        "USD": "KRW=X",
        "EUR": "EURKRW=X",
        "JPY": "JPYKRW=X"
    }
    
    ticker = ticker_map.get(currency_code)
    if not ticker:
        return 1.0
        
    try:
        if target_date:
            # yfinance expects date string YYYY-MM-DD
            # We need end date as +1 day for download
            start_date = target_date.strftime("%Y-%m-%d")
            end_date = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        else:
            data = yf.download(ticker, period="1d", progress=False)
            
        if not data.empty:
            # Use 'Close' price
            rate = data['Close'].iloc[-1].item()
            return rate
        else:
            # If no data (e.g., weekend), try fetching last 5 days
             data = yf.download(ticker, period="5d", progress=False)
             if not data.empty:
                 return data['Close'].iloc[-1].item()
             return 1.0
    except Exception as e:
        print(f"Error fetching rate: {e}")
        return 1.0
