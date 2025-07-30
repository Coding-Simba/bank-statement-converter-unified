"""Test database and create a test user."""

from models.database import init_db, get_db
from models.database import User
from utils.auth import get_password_hash

def test_database():
    # Initialize database
    init_db()
    
    # Get a database session
    db = next(get_db())
    
    try:
        # Check if test user exists
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        
        if not test_user:
            # Create test user
            test_user = User(
                email="test@example.com",
                password_hash=get_password_hash("testpassword"),
                full_name="Test User",
                account_type="free"
            )
            db.add(test_user)
            db.commit()
            print("Test user created successfully!")
        else:
            print("Test user already exists!")
            
        # Test query
        users_count = db.query(User).count()
        print(f"Total users in database: {users_count}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_database()