from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config import Config

username = Config.DB_USER
password = Config.DB_PASSWORD
oracle_host = Config.DB_HOST
oracle_port = Config.DB_PORT
oracle_service_name = Config.DB_SERVICE_NAME

# Construct the database URL using the settings
database_url = f'oracle+oracledb://{username}:{password}@{oracle_host}:{oracle_port}/?service_name={oracle_service_name}'

engine = create_engine(database_url)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    from .models import User, Email, UserActivity
    Base.metadata.create_all(bind=engine)
