import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_SERVICE_NAME = os.environ.get('DB_SERVICE_NAME') or 'XEPDB1'
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_PORT = os.environ.get('DB_PORT') or '1521'
    
    SQLALCHEMY_DATABASE_URI = f'oracle+oracledb://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/?service_name={DB_SERVICE_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
