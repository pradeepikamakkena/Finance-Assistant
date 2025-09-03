import datetime
from sqlalchemy import create_engine, Column, Integer, String, Numeric, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship

DATABASE_URL = "postgresql://postgres:financeapp1234598@db.iucsbzevwqvnsrduxrno.supabase.co:5432/postgres"

engine = create_engine(DATABASE_URL)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False) 

    receipts = relationship("Receipt", back_populates="owner")

class Receipt(Base):
    __tablename__ = 'receipts'
    id = Column(Integer, primary_key=True, index=True)
    seller_name = Column(String, index=True)
    category = Column(String, index=True)
    receipt_date = Column(DateTime)
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
    total_amount = Column(Numeric(10, 2))
    tax_amount = Column(Numeric(10, 2))
    
    owner_id = Column(Integer, ForeignKey('users.id'))
    owner_email = Column(String)
    
    owner = relationship("User", back_populates="receipts")
    
    items = relationship("Item", back_populates="receipt", cascade="all, delete-orphan")

class Item(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String)
    quantity = Column(Integer)
    rate = Column(Numeric(10, 2))
    subtotal = Column(Numeric(10, 2))
    
    receipt_id = Column(Integer, ForeignKey('receipts.id'))
    
    receipt = relationship("Receipt", back_populates="items")