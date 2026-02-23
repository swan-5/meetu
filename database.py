from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite 데이터베이스 파일 경로 (이 폴더 안에 meetu.db 파일이 자동 생성됩니다)
SQLALCHEMY_DATABASE_URL = "sqlite:///./meetu.db"

# DB 엔진 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 세션(연결 상태)을 만들어주는 도구
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 모든 모델의 뼈대가 되는 Base 클래스
Base = declarative_base()

# 요청이 올 때마다 DB를 열고 닫아주는 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()