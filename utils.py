import pandas as pd
import hashlib
import yfinance as yf
from datetime import datetime, timedelta
import uuid
from database import get_db

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(str.encode(password)).hexdigest()

def load_users():
    """Load users from Firestore"""
    db = get_db()
    if not db: return {}
    
    users_ref = db.collection('users')
    docs = users_ref.stream()
    
    user_dict = {}
    for doc in docs:
        user_dict[doc.id] = doc.to_dict()
        
    if not user_dict:
        # Create default admin user if no users
        admin_data = {
            "password_hash": hash_password("0713"),
            "role": "admin",
            "approved": True,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        users_ref.document("admin").set(admin_data)
        user_dict["admin"] = admin_data
        
    return user_dict

def save_users(users_dict):
    """Save/update users to Firestore."""
    db = get_db()
    if not db: return
    batch = db.batch()
    users_ref = db.collection('users')
    for username, data in users_dict.items():
        doc_ref = users_ref.document(username)
        batch.set(doc_ref, data, merge=True)
    batch.commit()

def register_user(username, password):
    """Register a new user to Firestore."""
    db = get_db()
    if not db: return False, "데이터베이스 연결 오류"
    
    doc_ref = db.collection('users').document(username)
    if doc_ref.get().exists:
        return False, "이미 존재하는 사용자명입니다."
    
    doc_ref.set({
        "password_hash": hash_password(password),
        "role": "user",
        "approved": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    return True, "회원가입 신청이 완료되었습니다. 관리자 승인을 기다려주세요."

def verify_user(username, password):
    """Verify login credentials using Firestore."""
    db = get_db()
    if not db: return None, "데이터베이스 연결 오류"
    
    # 안전장치: DB가 아예 비어있어서 admin조차 생성되지 않았을 경우 자동 생성
    users_ref = db.collection('users')
    if username == "admin" and not users_ref.document("admin").get().exists:
        # admin 강제 생성
        admin_data = {
            "password_hash": hash_password("0713"),
            "role": "admin",
            "approved": True,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        users_ref.document("admin").set(admin_data)

    doc_ref = users_ref.document(username)
    doc = doc_ref.get()
    
    if not doc.exists:
        return None, "존재하지 않는 사용자입니다."
    
    data = doc.to_dict()
    if data.get("password_hash") != hash_password(password):
        return None, "비밀번호가 올바르지 않습니다."
        
    if not data.get("approved"):
        return None, "관리자 승인 대기 중입니다."
        
    return {"username": username, "role": data.get("role")}, "로그인 성공"

def approve_user(username):
    db = get_db()
    if not db: return False
    doc_ref = db.collection('users').document(username)
    if doc_ref.get().exists:
        doc_ref.update({"approved": True})
        return True
    return False

def delete_user(username):
    db = get_db()
    if not db: return False
    doc_ref = db.collection('users').document(username)
    doc = doc_ref.get()
    if doc.exists and doc.to_dict().get("role") != "admin": # Prevent deleting admin
        doc_ref.delete()
        return True
    return False

def load_folders():
    """Load trips from Firestore."""
    db = get_db()
    if not db: return {}
    trips_ref = db.collection('trips')
    docs = trips_ref.stream()
    folder_dict = {}
    for doc in docs:
        folder_dict[doc.id] = doc.to_dict()
    return folder_dict

def save_folders(folders_dict):
    """Sync trips to Firestore."""
    db = get_db()
    if not db: return
    
    trips_ref = db.collection('trips')
    existing_docs = [doc.id for doc in trips_ref.stream()]
    
    # Delete removed ones
    for tid in existing_docs:
        if tid not in folders_dict:
            trips_ref.document(tid).delete()

    # Update or add
    batch = db.batch()
    for trip_id, data in folders_dict.items():
        doc_ref = trips_ref.document(trip_id)
        batch.set(doc_ref, data, merge=True)
    batch.commit()

def load_data(trip_id=None):
    """Load expenses for a trip from Firestore into DataFrame."""
    empty_df = pd.DataFrame(columns=["ID", "Date", "Category", "Item", "Amount", "Currency", "Original Amount", "Exchange Rate", "User", "image_path"])
    if not trip_id: return empty_df
        
    db = get_db()
    if not db: return empty_df
        
    expenses_ref = db.collection('expenses').where('trip_id', '==', trip_id)
    docs = expenses_ref.stream()
    
    data_list = []
    for doc in docs:
        d = doc.to_dict()
        data_list.append({
            "ID": d.get("id"),
            "Date": d.get("date"),
            "Category": d.get("category"),
            "Item": d.get("item"),
            "Amount": d.get("amount"),
            "Currency": d.get("currency"),
            "Original Amount": d.get("original_amount"),
            "Exchange Rate": d.get("exchange_rate"),
            "User": d.get("user", "알수없음"),
            "image_path": d.get("image_path")
        })
        
    if data_list:
        df = pd.DataFrame(data_list)
        # Convert Firebase datetime back to Pandas timestamp
        df['Date'] = pd.to_datetime(df['Date'], utc=True).dt.tz_convert(None)
        return df
    else:
        return empty_df

def save_data(df, trip_id):
    """Save DataFrame to Firestore."""
    if not trip_id: return
    db = get_db()
    if not db: return
    
    # 1. Clear existing for this trip
    expenses_ref = db.collection('expenses')
    docs = expenses_ref.where('trip_id', '==', trip_id).stream()
    batch = db.batch()
    for doc in docs:
        batch.delete(doc.reference)
    # Commit deletes
    batch.commit()
    
    # 2. Insert new from DF
    batch = db.batch()
    count = 0
    for _, row in df.iterrows():
        doc_id = str(row['ID'])
        doc_ref = expenses_ref.document(doc_id)
        
        # Ensure primitive Python types for Firebase
        dt = row['Date']
        if isinstance(dt, pd.Timestamp):
            dt = dt.to_pydatetime()
            
        data = {
            "id": doc_id,
            "trip_id": trip_id,
            "user": str(row.get('User', '알수없음')),
            "date": dt,
            "category": str(row['Category']),
            "item": str(row['Item']),
            "amount": float(row['Amount']),
            "currency": str(row['Currency']),
            "original_amount": float(row['Original Amount']),
            "exchange_rate": float(row['Exchange Rate']),
            "image_path": str(row['image_path']) if 'image_path' in row and pd.notna(row['image_path']) else None
        }
        batch.set(doc_ref, data)
        count += 1
        
        # Firestore batch limit is 500
        if count == 400:
            batch.commit()
            batch = db.batch()
            count = 0
            
    if count > 0:
        batch.commit()

def calculate_metrics(df, total_budget):
    if df.empty:
        return 0, total_budget
    total_spent = df["Amount"].sum()
    remaining = total_budget - total_spent
    return total_spent, remaining

def get_exchange_rate(currency_code, target_date=None):
    if currency_code == "KRW": return 1.0
    
    ticker_map = {
        "USD": "KRW=X",
        "EUR": "EURKRW=X",
        "JPY": "JPYKRW=X"
    }
    
    ticker = ticker_map.get(currency_code)
    if not ticker: return 1.0
        
    try:
        if target_date:
            start_date = target_date.strftime("%Y-%m-%d")
            end_date = (target_date + timedelta(days=1)).strftime("%Y-%m-%d")
            data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        else:
            data = yf.download(ticker, period="1d", progress=False)
            
        if not data.empty:
            return float(data['Close'].iloc[-1].item())
        else:
             data = yf.download(ticker, period="5d", progress=False)
             if not data.empty:
                 return float(data['Close'].iloc[-1].item())
             return 1.0
    except Exception as e:
        print(f"Error fetching rate: {e}")
        return 1.0

def load_expense_requests():
    """Load pending expense requests from Firestore."""
    db = get_db()
    if not db: return []
    reqs_ref = db.collection('expense_requests')
    docs = reqs_ref.stream()
    res = []
    for doc in docs:
        d = doc.to_dict()
        res.append({
            "type": d.get("type"),
            "trip_id": d.get("trip_id"),
            "expense_id": d.get("expense_id"),
            "item_name": d.get("item_name"),
            "request_user": d.get("request_user"),
            "reason": d.get("reason"),
            "new_data": d.get("new_data")
        })
    return res

def save_expense_requests(requests_list):
    """Sync list to Firestore requests."""
    db = get_db()
    if not db: return
    reqs_ref = db.collection('expense_requests')
    
    batch = db.batch()
    docs = reqs_ref.stream()
    for doc in docs:
        batch.delete(doc.reference)
    batch.commit()
    
    batch = db.batch()
    for r in requests_list:
        doc_ref = reqs_ref.document(str(uuid.uuid4()))
        batch.set(doc_ref, r)
    batch.commit()
