import os
import json
import pandas as pd
from datetime import datetime
from database import SessionLocal, User, Trip, Expense, ExpenseRequest, Base, engine

DATA_DIR = "data"
FOLDERS_FILE = os.path.join(DATA_DIR, "folders.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
REQUESTS_FILE = os.path.join(DATA_DIR, "expense_requests.json")

def migrate_to_db():
    print("Starting database migration...")
    db = SessionLocal()
    
    # 1. Users
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users_data = json.load(f)
            for username, data in users_data.items():
                existing = db.query(User).filter(User.username == username).first()
                if not existing:
                    new_user = User(
                        username=username,
                        password_hash=data.get('password_hash', ''),
                        role=data.get('role', 'user'),
                        approved=data.get('approved', False),
                        created_at=data.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    )
                    db.add(new_user)
        db.commit()
        print(f"Migrated Users.")
        # Rename file to prevent double migration
        os.rename(USERS_FILE, USERS_FILE + ".migrated")

    # 2. Trips (Folders)
    if os.path.exists(FOLDERS_FILE):
        with open(FOLDERS_FILE, "r", encoding="utf-8") as f:
            folders_data = json.load(f)
            for trip_id, data in folders_data.items():
                existing = db.query(Trip).filter(Trip.id == trip_id).first()
                if not existing:
                    new_trip = Trip(
                        id=trip_id,
                        name=data.get('name', 'Unknown'),
                        password=data.get('password', ''),
                        budget=data.get('budget', 0),
                        start_date=data.get('start_date'),
                        end_date=data.get('end_date'),
                        created_at=data.get('created_at', datetime.now().strftime("%Y-%m-%d"))
                    )
                    db.add(new_trip)
                    
                    # Also migrate CSV for this trip
                    csv_path = os.path.join(DATA_DIR, f"expenses_default.csv" if trip_id == "default_trip" else f"expenses_{trip_id}.csv")
                    if os.path.exists(csv_path):
                        df = pd.read_csv(csv_path)
                        for _, row in df.iterrows():
                            # Generate ID if missing
                            exp_id = str(row['ID']) if 'ID' in row and pd.notna(row['ID']) else str(uuid.uuid4())
                            # Handle Date
                            d_val = row['Date']
                            if isinstance(d_val, str):
                                try: d_val = datetime.strptime(d_val[:10], "%Y-%m-%d")
                                except: d_val = datetime.now()
                            elif pd.isna(d_val): d_val = datetime.now()
                            
                            new_exp = Expense(
                                id=exp_id,
                                trip_id=trip_id,
                                user=row.get('User', '알수없음') if 'User' in row else '알수없음',
                                date=d_val,
                                category=row.get('Category', '기타 (Others)'),
                                item=row.get('Item', '내용없음'),
                                amount=float(row.get('Amount', 0.0)),
                                currency=row.get('Currency', 'KRW') if 'Currency' in row else 'KRW',
                                original_amount=float(row.get('Original Amount', row.get('Amount',0.0))) if 'Original Amount' in row else float(row.get('Amount', 0.0)),
                                exchange_rate=float(row.get('Exchange Rate', 1.0)) if 'Exchange Rate' in row else 1.0,
                                image_path=None
                            )
                            db.add(new_exp)
                        os.rename(csv_path, csv_path + ".migrated")
        db.commit()
        print("Migrated Trips and Expenses.")
        os.rename(FOLDERS_FILE, FOLDERS_FILE + ".migrated")

    # 3. Requests
    if os.path.exists(REQUESTS_FILE):
        with open(REQUESTS_FILE, "r", encoding="utf-8") as f:
            req_data = json.load(f)
            for req in req_data:
                new_req = ExpenseRequest(
                    type=req.get('type', 'edit'),
                    trip_id=req.get('trip_id', ''),
                    expense_id=req.get('expense_id', ''),
                    item_name=req.get('item_name', ''),
                    request_user=req.get('request_user', ''),
                    reason=req.get('reason', ''),
                    new_data=req.get('new_data', {})
                )
                db.add(new_req)
        db.commit()
        print("Migrated Expense Requests.")
        os.rename(REQUESTS_FILE, REQUESTS_FILE + ".migrated")

    db.close()
    print("Migration complete!")

if __name__ == "__main__":
    import uuid
    Base.metadata.create_all(bind=engine)
    migrate_to_db()
