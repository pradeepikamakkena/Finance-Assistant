import sys
from app.database import SessionLocal
from app.models import User

def make_user_admin(email: str):
    """Finds a user by email and sets their is_admin flag to True."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"Error: User with email '{email}' not found.")
            return

        user.is_admin = True
        db.commit()
        print(f"Success! User '{email}' has been granted admin privileges.")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_admin.py <user_email>")
    else:
        user_email = sys.argv[1]
        make_user_admin(user_email)