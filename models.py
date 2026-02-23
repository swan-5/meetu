from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from database import Base
import datetime

# 방 참여자 연결 테이블 (다대다 관계)
room_members = Table(
    "room_members",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("room_id", Integer, ForeignKey("rooms.id"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    login_id = Column(String, unique=True)
    password = Column(String)
    is_verified = Column(String, default="pending") 
    student_card_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    profile = relationship("Profile", back_populates="user", uselist=False)
    # 참여 중인 방들
    rooms = relationship("Room", secondary=room_members, back_populates="members")

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    nickname = Column(String)
    university = Column(String)
    major = Column(String)
    age = Column(Integer)
    height = Column(Integer)
    gender = Column(String) # 성별 추가
    mbti = Column(String, nullable=True)
    ideal_type = Column(String, nullable=True)
    pref_mbti = Column(String, nullable=True)
    pref_age = Column(String, nullable=True)
    must_have = Column(String, nullable=True)
    description = Column(String, nullable=True)
    meeting_type = Column(String, default="1:1")
    exit_count = Column(Integer, default=0)
    
    user = relationship("User", back_populates="profile")

class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    capacity = Column(Integer)
    creator_id = Column(Integer)
    status = Column(String, default="open")
    creator_id = Column(Integer)
    members = relationship("User", secondary=room_members, back_populates="rooms")