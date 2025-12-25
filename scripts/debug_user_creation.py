import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from infra.db import SessionLocal, engine
from modules.accounts.model import Account
from core.security import get_password_hash

def debug():
    print("--- Database Debug ---")
    print(f"URL: {engine.url}")
    
    try:
        with engine.connect() as conn:
            print("✅ Connection successful")
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
            tables = [row[0] for row in result]
            print(f"Tables found: {tables}")
            
            if "accounts" in tables:
                cols = conn.execute(text("PRAGMA table_info(accounts);"))
                columns = [row[1] for row in cols]
                print(f"Columns in 'accounts': {columns}")
                if "hashed_password" not in columns:
                    print("❌ MISSING 'hashed_password' column!")
            else:
                print("❌ MISSING 'accounts' table!")

    except Exception as e:
        print(f"❌ Connection/Schema Error: {e}")
        return

    print("\n--- Attempting User Creation (Direct ORM) ---")
    db = SessionLocal()
    try:
        email = "debug_test@example.com"
        password = "password"
        full_name = "Debug User"
        
        # Check existing
        exists = db.query(Account).filter(Account.email == email).first()
        if exists:
            print(f"User {email} already exists. Deleting for cleanup...")
            db.delete(exists)
            db.commit()
        
        print("Hashing password...")
        hashed = get_password_hash(password)
        print(f"Hashed: {hashed[:10]}...")
        
        print("Creating account object...")
        user = Account(email=email, full_name=full_name, hashed_password=hashed)
        db.add(user)
        print("Committing to DB...")
        db.commit()
        print("✅ User created successfully via ORM")
        
    except Exception as e:
        print(f"❌ ORM Creation Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug()
