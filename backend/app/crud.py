import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from . import models, schemas, security


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_receipt(db: Session, receipt: schemas.ReceiptCreate, user_id: int, user_email: str):
    db_receipt = models.Receipt(
        seller_name=receipt.seller_name,
        category=receipt.category,
        receipt_date=receipt.receipt_date,
        total_amount=receipt.total_amount,
        tax_amount=receipt.tax_amount,
        owner_id=user_id,
        owner_email=user_email
    )
    db.add(db_receipt)
    db.commit()
    db.refresh(db_receipt)
    for item_data in receipt.items:
        db_item = models.Item(**item_data.dict(), receipt_id=db_receipt.id)
        db.add(db_item)
    db.commit()
    db.refresh(db_receipt)
    return db_receipt

def get_receipts_by_user(db: Session, user_id: int, limit: int = 20):
    return db.query(models.Receipt).filter(models.Receipt.owner_id == user_id).order_by(models.Receipt.upload_date.desc()).limit(limit).all()

def get_all_receipts_by_user(db: Session, user_id: int):
    return db.query(models.Receipt).filter(models.Receipt.owner_id == user_id).order_by(models.Receipt.upload_date.desc()).all()

def get_receipt_by_id(db: Session, receipt_id: int):
    return db.query(models.Receipt).filter(models.Receipt.id == receipt_id).first()

def delete_receipt(db: Session, receipt_id: int):
    db_receipt = get_receipt_by_id(db, receipt_id=receipt_id)
    if db_receipt:
        db.delete(db_receipt)
        db.commit()
        return True
    return False

def get_kpi_data(db: Session, user_id: int, start_date: datetime.date = None, end_date: datetime.date = None):
    query = db.query(
        func.sum(models.Receipt.total_amount),
        func.sum(models.Receipt.tax_amount),
        func.count(models.Receipt.id)
    ).filter(models.Receipt.owner_id == user_id)

    if start_date and end_date:
        query = query.filter(and_(models.Receipt.receipt_date >= start_date, models.Receipt.receipt_date <= end_date))

    total_spend, total_tax, total_bills = query.first()
    return {
        "total_spend": total_spend or 0.0,
        "total_tax": total_tax or 0.0,
        "total_bills": total_bills or 0
    }

def get_spending_over_time(db: Session, user_id: int, start_date: datetime.date = None, end_date: datetime.date = None):
    query = db.query(
        func.to_char(models.Receipt.receipt_date, "YYYY-MM").label("label"),
        func.sum(models.Receipt.total_amount).label("value"),
    ).filter(models.Receipt.owner_id == user_id)
    
    if start_date and end_date:
        query = query.filter(and_(models.Receipt.receipt_date >= start_date, models.Receipt.receipt_date <= end_date))

    return query.group_by("label").order_by("label").all()

def get_spending_by_category(db: Session, user_id: int, start_date: datetime.date = None, end_date: datetime.date = None):
    query = db.query(
        models.Receipt.category.label("label"),
        func.sum(models.Receipt.total_amount).label("value"),
    ).filter(models.Receipt.owner_id == user_id)

    if start_date and end_date:
        query = query.filter(and_(models.Receipt.receipt_date >= start_date, models.Receipt.receipt_date <= end_date))
        
    return query.group_by("label").all()

def get_top_items(db: Session, user_id: int, start_date: datetime.date = None, end_date: datetime.date = None, limit: int = 10):
    query = (
        db.query(
            models.Item.item_name.label("label"),
            func.sum(models.Item.subtotal).label("value"),
        )
        .join(models.Receipt)
        .filter(models.Receipt.owner_id == user_id)
    )

    if start_date and end_date:
        query = query.filter(and_(models.Receipt.receipt_date >= start_date, models.Receipt.receipt_date <= end_date))

    return (
        query.group_by(models.Item.item_name)
        .order_by(func.sum(models.Item.subtotal).desc())
        .limit(limit)
        .all()
    )

def get_all_users(db: Session):
    return db.query(models.User).all()

def get_all_receipts(db: Session):
    return db.query(models.Receipt).order_by(models.Receipt.upload_date.desc()).all()

def delete_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False

def get_top_items(db: Session, user_id: int, start_date: datetime.date = None, end_date: datetime.date = None, limit: int = 10):
    """Calculates the top spending by item for a user, optionally filtered by date."""
    query = (
        db.query(
            models.Item.item_name.label("label"),
            func.sum(models.Item.subtotal).label("value"),
        )
        .join(models.Receipt)
        .filter(models.Receipt.owner_id == user_id)
    )

    if start_date and end_date:
        query = query.filter(and_(models.Receipt.receipt_date >= start_date, models.Receipt.receipt_date <= end_date))

    return (
        query.group_by(models.Item.item_name)
        .order_by(func.sum(models.Item.subtotal).desc())
        .limit(limit)
        .all()
    )