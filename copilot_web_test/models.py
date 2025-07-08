from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Sequence
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from database import Base
import datetime
import uuid
from flask_login import UserMixin

class User(Base, UserMixin):
    __tablename__ = 'users'
    # Define a sequence for the primary key
    id_seq = Sequence('user_id_seq', start=1, increment=1)
    id = Column(Integer, id_seq, primary_key=True, server_default=id_seq.next_value())
    username = Column(String(150), unique=True, nullable=False)
    password = Column(String(256), nullable=False)
    emails = relationship('Email', back_populates='user', lazy=True)
    activities = relationship('UserActivity', backref='user', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Email(Base):
    __tablename__ = 'emails'
    unique_email_id = Column(String(255), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    sender_name = Column(String(255))
    sender_email = Column(String(255))
    title = Column(String(255))
    body = Column(Text)
    email_type = Column(String(50))
    date_sent = Column(DateTime)
    references = Column(Text) # For storing hyperlinked references

    user = relationship("User", back_populates="emails")


class UserActivity(Base):
    __tablename__ = 'user_activity'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id'))
    token = Column(String(36), nullable=False)
    activity = Column(String(200))
    details = Column(Text)  # To store JSON details about the activity
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
