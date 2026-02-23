from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models
from database import engine, get_db

# 서버가 켜질 때 DB 테이블 자동 생성
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MeetU API")

# CORS 설정 (프론트엔드 연결 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "MeetU API 서버가 정상적으로 실행 중입니다! 🚀"}

@app.post("/users/")
def create_user(oauth_provider: str = "email", db: Session = Depends(get_db)):
    new_user = models.User(oauth_provider=oauth_provider)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "message": "유저 생성 완료 💗",
        "user_id": new_user.id,
        "is_verified": new_user.is_verified
    }