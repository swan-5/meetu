from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base  # database.py에서 Base를 가져옴

# --- Enums (상태값 정의) ---
class AuthProvider(str, enum.Enum):
    KAKAO = "kakao"
    GOOGLE = "google"
    EMAIL = "email"

class VerifyStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class MatchStatus(str, enum.Enum):
    SEARCHING = "searching"
    MATCHED = "matched"
    FAILED = "failed"
    EXPIRED = "expired"

class ReportType(str, enum.Enum):
    MANNER = "manner_review"
    REPORT = "report"

# --- DB 테이블 모델 ---
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    oauth_provider = Column(Enum(AuthProvider), default=AuthProvider.EMAIL)
    oauth_id = Column(String, unique=True, index=True, nullable=True)
    student_card_url = Column(String, nullable=True)
    is_verified = Column(Enum(VerifyStatus), default=VerifyStatus.PENDING)
    role = Column(Enum(UserRole), default=UserRole.USER)
    points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("Profile", back_populates="user", uselist=False)
    preference = relationship("Preference", back_populates="user", uselist=False)

class Profile(Base):
    __tablename__ = "profiles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    nickname = Column(String, unique=True, index=True)
    university = Column(String, index=True)
    major = Column(String)
    age = Column(Integer)
    height = Column(Integer, nullable=True)
    mbti = Column(String, nullable=True)
    hobbies = Column(String, nullable=True)
    charms = Column(String, nullable=True)
    profile_image_url = Column(String, nullable=True)

    user = relationship("User", back_populates="profile")

class Preference(Base):
    __tablename__ = "preferences"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    pref_age_min = Column(Integer, nullable=True)
    pref_age_max = Column(Integer, nullable=True)
    pref_univ_group = Column(String, nullable=True)
    avoid_traits = Column(String, nullable=True)
    core_values = Column(String, nullable=True)
    tags = Column(JSON, nullable=True)

    user = relationship("User", back_populates="preference")

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    user_a_id = Column(Integer, ForeignKey("users.id"))
    user_b_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(Enum(MatchStatus), default=MatchStatus.SEARCHING)
    open_chat_url = Column(String, nullable=True)
    meet_place = Column(String, nullable=True)
    meet_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_a = relationship("User", foreign_keys=[user_a_id])
    user_b = relationship("User", foreign_keys=[user_b_id])

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"))
    reported_user_id = Column(Integer, ForeignKey("users.id"))
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)
    report_type = Column(Enum(ReportType))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)