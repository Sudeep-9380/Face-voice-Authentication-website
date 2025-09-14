# database.py - Database setup and management utilities
from app import app, db, User, LoginHistory
from werkzeug.security import generate_password_hash
import os

def create_tables():
    """Create all database tables"""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

def create_admin_user():
    """Create a default admin user"""
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: username=admin, password=admin123")
        else:
            print("Admin user already exists")

def reset_database():
    """Reset the entire database (WARNING: This will delete all data)"""
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database reset completed!")

def backup_database():
    """Create a backup of the database"""
    import shutil
    import datetime
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"biometric_auth_backup_{timestamp}.db"
    
    if os.path.exists('biometric_auth.db'):
        shutil.copy2('biometric_auth.db', backup_name)
        print(f"Database backed up to: {backup_name}")
    else:
        print("No database file found to backup")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python database.py [create|admin|reset|backup]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'create':
        create_tables()
    elif command == 'admin':
        create_admin_user()
    elif command == 'reset':
        confirm = input("This will delete ALL data. Type 'yes' to continue: ")
        if confirm.lower() == 'yes':
            reset_database()
        else:
            print("Operation cancelled")
    elif command == 'backup':
        backup_database()
    else:
        print("Invalid command. Use: create, admin, reset, or backup")