import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Uploads directory for receipts/photos
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

DB_PATH = os.path.join(DATA_DIR, "travel_db.sqlite")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    username = Column(String, primary_key=True, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    approved = Column(Boolean, default=False)
    created_at = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

class Trip(Base):
    __tablename__ = "trips"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    password = Column(String, nullable=False)
    budget = Column(Integer, default=0)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    category_budgets = Column(JSON, nullable=True) # {"식사": 500000, "쇼핑": 100000...}
    created_at = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d"))

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(String, primary_key=True, index=True)
    trip_id = Column(String, index=True)
    user = Column(String, default="알수없음")
    date = Column(DateTime, nullable=False)
    category = Column(String, nullable=False)
    item = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="KRW")
    original_amount = Column(Float, nullable=False)
    exchange_rate = Column(Float, default=1.0)
    image_path = Column(String, nullable=True)  # Path to uploaded photo/receipt

class ExpenseRequest(Base):
    __tablename__ = "expense_requests"
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String, nullable=False) # 'edit' or 'delete'
    trip_id = Column(String, nullable=False)
    expense_id = Column(String, nullable=False)
    item_name = Column(String, nullable=False)
    request_user = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    new_data = Column(JSON, nullable=True)  # Stores edit JSON details

Base.metadata.create_all(bind=engine)

# Dependency helper
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
