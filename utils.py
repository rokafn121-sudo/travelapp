import pandas as pd
import hashlib
import yfinance as yf
from datetime import datetime, timedelta
from database import SessionLocal, User, Trip, Expense, ExpenseRequest

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(str.encode(password)).hexdigest()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def load_users():
    """Load users metadata as dict for app compatibility."""
    db = next(get_db())
    users = db.query(User).all()
    if not users:
        # Create default admin user if no users
        default_user = User(
            username="admin",
            password_hash=hash_password("0713"),
            role="admin",
            approved=True,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.add(default_user)
        db.commit()
        users = [default_user]
        
    user_dict = {}
    for u in users:
        user_dict[u.username] = {
            "password_hash": u.password_hash,
            "role": u.role,
            "approved": u.approved,
            "created_at": u.created_at
        }
    return user_dict

def save_users(users_dict):
    """Save/update users metadata to db."""
    db = next(get_db())
    for username, data in users_dict.items():
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            existing.password_hash = data['password_hash']
            existing.role = data['role']
            existing.approved = data['approved']
        else:
            new_u = User(username=username, password_hash=data['password_hash'], role=data['role'], approved=data['approved'], created_at=data.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            db.add(new_u)
    db.commit()

def register_user(username, password):
    """Register a new user (pending approval). Returns (success, message)."""
    db = next(get_db())
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        return False, "이미 존재하는 사용자명입니다."
    
    new_user = User(
        username=username,
        password_hash=hash_password(password),
        role="user",
        approved=False,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    db.add(new_user)
    db.commit()
    return True, "회원가입 신청이 완료되었습니다. 관리자 승인을 기다려주세요."

def verify_user(username, password):
    """Verify login credentials. Returns (user_data, message)."""
    db = next(get_db())
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None, "존재하지 않는 사용자입니다."
    
    if user.password_hash != hash_password(password):
        return None, "비밀번호가 올바르지 않습니다."
        
    if not user.approved:
        return None, "관리자 승인 대기 중입니다."
        
    return {"username": user.username, "role": user.role}, "로그인 성공"

def approve_user(username):
    """Approve a pending user."""
    db = next(get_db())
    user = db.query(User).filter(User.username == username).first()
    if user:
        user.approved = True
        db.commit()
        return True
    return False

def delete_user(username):
    """Delete a user."""
    db = next(get_db())
    user = db.query(User).filter(User.username == username).first()
    if user and user.role != "admin": # Prevent deleting main admin
        db.delete(user)
        db.commit()
        return True
    return False

def load_folders():
    """Load folders metadata as dict for app compatibility."""
    db = next(get_db())
    trips = db.query(Trip).all()
    folder_dict = {}
    for t in trips:
        folder_dict[t.id] = {
            "name": t.name,
            "password": t.password,
            "budget": t.budget,
            "start_date": t.start_date,
            "end_date": t.end_date,
            "category_budgets": t.category_budgets if t.category_budgets else {},
            "created_at": t.created_at
        }
    return folder_dict

def save_folders(folders_dict):
    """Sync dict to db."""
    db = next(get_db())
    # Delete trips that are no longer in the dict
    existing_ids = [t.id for t in db.query(Trip).all()]
    for tid in existing_ids:
        if tid not in folders_dict:
            db.query(Trip).filter(Trip.id == tid).delete(synchronize_session=False)
            db.query(Expense).filter(Expense.trip_id == tid).delete(synchronize_session=False)

    for trip_id, data in folders_dict.items():
        existing = db.query(Trip).filter(Trip.id == trip_id).first()
        if existing:
            existing.name = data['name']
            existing.password = data['password']
            existing.budget = data['budget']
            existing.start_date = data.get('start_date')
            existing.end_date = data.get('end_date')
            existing.category_budgets = data.get('category_budgets', {})
        else:
            new_trip = Trip(
                id=trip_id,
                name=data['name'],
                password=data['password'],
                budget=data['budget'],
                start_date=data.get('start_date'),
                end_date=data.get('end_date'),
                category_budgets=data.get('category_budgets', {}),
                created_at=data.get('created_at', datetime.now().strftime("%Y-%m-%d"))
            )
            db.add(new_trip)
    db.commit()

def load_data(trip_id=None):
    """
    Loads data from the DB for a specific trip into DataFrame.
    """
    if not trip_id:
        return pd.DataFrame(columns=["ID", "Date", "Category", "Item", "Amount", "Currency", "Original Amount", "Exchange Rate", "User", "image_path"])
        
    db = next(get_db())
    expenses = db.query(Expense).filter(Expense.trip_id == trip_id).all()
    
    data_list = []
    for e in expenses:
        data_list.append({
            "ID": e.id,
            "Date": e.date,
            "Category": e.category,
            "Item": e.item,
            "Amount": e.amount,
            "Currency": e.currency,
            "Original Amount": e.original_amount,
            "Exchange Rate": e.exchange_rate,
            "User": e.user,
            "image_path": e.image_path
        })
        
    if data_list:
        df = pd.DataFrame(data_list)
        df['Date'] = pd.to_datetime(df['Date'])
        return df
    else:
        return pd.DataFrame(columns=["ID", "Date", "Category", "Item", "Amount", "Currency", "Original Amount", "Exchange Rate", "User", "image_path"])

def save_data(df, trip_id):
    """
    Saves the DataFrame to DB for a specific trip.
    We mirror the DF to the Database exactly.
    """
    if not trip_id:
        return
        
    db = next(get_db())
    # clear existing rows for trip
    db.query(Expense).filter(Expense.trip_id == trip_id).delete(synchronize_session=False)
    
    for _, row in df.iterrows():
        new_exp = Expense(
            id=str(row['ID']),
            trip_id=trip_id,
            user=row.get('User', '알수없음'),
            date=row['Date'],
            category=row['Category'],
            item=row['Item'],
            amount=row['Amount'],
            currency=row['Currency'],
            original_amount=row['Original Amount'],
            exchange_rate=row['Exchange Rate'],
            image_path=str(row['image_path']) if 'image_path' in row and pd.notna(row['image_path']) else None
        )
        db.add(new_exp)
    db.commit()

def calculate_metrics(df, total_budget):
    """Calculates total spent and remaining budget."""
    if df.empty:
        return 0, total_budget
    total_spent = df["Amount"].sum()
    remaining = total_budget - total_spent
    return total_spent, remaining

def get_exchange_rate(currency_code, target_date=None):
    """Get exchange rate for currency_code to KRW."""
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
            start_date = target_date.strftime("%Y-%m-%d")
            end_date = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        else:
            data = yf.download(ticker, period="1d", progress=False)
            
        if not data.empty:
            rate = data['Close'].iloc[-1].item()
            return rate
        else:
             data = yf.download(ticker, period="5d", progress=False)
             if not data.empty:
                 return data['Close'].iloc[-1].item()
             return 1.0
    except Exception as e:
        print(f"Error fetching rate: {e}")
        return 1.0

def load_expense_requests():
    """Load pending expense requests from DB as list of dicts."""
    db = next(get_db())
    reqs = db.query(ExpenseRequest).all()
    res = []
    for r in reqs:
        res.append({
            "db_id": r.id,
            "type": r.type,
            "trip_id": r.trip_id,
            "expense_id": r.expense_id,
            "item_name": r.item_name,
            "request_user": r.request_user,
            "reason": r.reason,
            "new_data": r.new_data
        })
    return res

def save_expense_requests(requests_list):
    """Sync list of dicts to DB requests."""
    db = next(get_db())
    # Easiest way to sync is to wipe and recreate
    db.query(ExpenseRequest).delete(synchronize_session=False)
    for r in requests_list:
        new_req = ExpenseRequest(
            type=r['type'],
            trip_id=r['trip_id'],
            expense_id=r['expense_id'],
            item_name=r['item_name'],
            request_user=r['request_user'],
            reason=r.get('reason'),
            new_data=r.get('new_data')
        )
        db.add(new_req)
    db.commit()
