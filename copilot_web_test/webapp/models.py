from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Sequence
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from .database import Base
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
    comments = relationship('Comment', back_populates='user', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Email(Base):
    __tablename__ = 'emails'
    unique_email_id = Column(String(255), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    sender_name = Column(String(255))
    sender_email = Column(String(255))
    title = Column(String(255))
    body = Column(Text)
    email_type = Column(String(50), index=True)
    date_sent = Column(DateTime, index=True)
    references = Column(Text) # For storing hyperlinked references
    comments = relationship('Comment', back_populates='email', lazy=True)

    user = relationship("User", back_populates="emails")

    __table_args__ = (
        {'extend_existing': True},
    )

class UserActivity(Base):
    __tablename__ = 'user_activity'
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    token = Column(String(36), nullable=False, index=True)
    activity = Column(String(200))
    details = Column(Text)  # To store JSON details about the activity

class Comment(Base):
    __tablename__ = 'comments'
    id_seq = Sequence('comment_id_seq', start=1, increment=1)
    id = Column(Integer, id_seq, primary_key=True, server_default=id_seq.next_value())
    body = Column(Text, nullable=False)
    timestamp = Column(DateTime, index=True, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    email_id = Column(String(255), ForeignKey('emails.unique_email_id'), index=True)
    parent_id = Column(Integer, ForeignKey('comments.id'), index=True)

    user = relationship('User', back_populates='comments')
    email = relationship('Email', back_populates='comments')
    parent = relationship('Comment', remote_side=[id], backref='replies')

    def __repr__(self):
        return f'<Comment {self.id}>'

    __table_args__ = (
        {'extend_existing': True},
    )
