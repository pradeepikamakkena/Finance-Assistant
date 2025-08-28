from app.database import SessionLocal
from app.models import User, Receipt, Item # Import all three models

print("Connecting to the database to clear all tables...")
db = SessionLocal()
try:
    num_items_deleted = db.query(Item).delete()
    print(f"Deleted {num_items_deleted} item(s).")

    num_receipts_deleted = db.query(Receipt).delete()
    print(f"Deleted {num_receipts_deleted} receipt(s).")

    num_users_deleted = db.query(User).delete()
    print(f"Deleted {num_users_deleted} user(s).")

    db.commit()
    print("Successfully cleared all tables.")
except Exception as e:
    print(f"An error occurred: {e}")
    db.rollback()
finally:
    db.close()