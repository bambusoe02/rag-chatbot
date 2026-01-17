"""Database initialization script."""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.database import init_db, SessionLocal
from backend.db_models import User
from backend.auth import get_password_hash


def initialize_database():
    """Initialize database tables and create admin user."""
    print("=" * 50)
    print("Initializing Database...")
    print("=" * 50)
    
    # Create tables
    try:
        init_db()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"⚠️ Warning: {e}")
    
    # Create data directories
    os.makedirs("./data/uploads", exist_ok=True)
    os.makedirs("./data/chroma_db", exist_ok=True)
    os.makedirs("./data/chat_history", exist_ok=True)
    os.makedirs("./data/feedback", exist_ok=True)
    os.makedirs("./data/analytics", exist_ok=True)
    print("✅ Data directories created")
    
    # Create admin user
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                full_name="Administrator",
                role="admin",
                is_active=True
            )
            db.add(admin)
            db.commit()
            print("✅ Admin user created")
            print("   Username: admin")
            print("   Password: admin123")
            print("   ⚠️  CHANGE THIS IMMEDIATELY IN PRODUCTION!")
        else:
            print("ℹ️  Admin user already exists")
    except Exception as e:
        print(f"⚠️ Warning: {e}")
    finally:
        db.close()
    
    print("=" * 50)
    print("✅ Database initialization complete!")
    print("=" * 50)


if __name__ == "__main__":
    initialize_database()

