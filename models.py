from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    login_id = Column(String, unique=True)
    password = Column(String)
    is_verified = Column(String, default="pending") 
    student_card_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    profile = relationship("Profile", back_populates="user", uselist=False)

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    nickname = Column(String)
    university = Column(String)
    major = Column(String)
    age = Column(Integer)
    height = Column(Integer)
    mbti = Column(String, nullable=True)
    ideal_type = Column(String, nullable=True)
    pref_mbti = Column(String, nullable=True)
    pref_age = Column(String, nullable=True)
    must_have = Column(String, nullable=True)
    description = Column(String, nullable=True)
    meeting_type = Column(String, default="1:1")
    user = relationship("User", back_populates="profile")