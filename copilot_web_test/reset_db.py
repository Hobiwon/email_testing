from webapp.database import Base, engine
# Import all the models, so that Base has them registered
from webapp.models import User, Email, UserActivity

def reset_database():
    print("Dropping all tables...")
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    print("Creating all tables...")
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database has been reset.")

if __name__ == '__main__':
    # This allows the script to be run from the command line
    reset_database()
